/* Eshtaya Smart Control v2.2 shell extensions.
 * Adds resilient shell loading and Home Assistant Core access management.
 */

const ESC_DOMAIN_V22 = "eshtaya_smart_control";

function escV22Text(panel, en, ar) {
  return panel._lang === "ar" ? ar : en;
}

function escV22Error(err) {
  return err?.message || err?.body?.message || String(err || "Unknown error");
}

function escV22Timeout(promise, ms, label) {
  let timer;
  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error(`${label} timed out`)), ms);
  });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
}

function escV22Permission(panel, name) {
  return Boolean(panel._access?.permissions?.includes(name));
}

customElements.whenDefined("eshtaya-smart-control-panel").then(() => {
  // v2.1 registers its prototype patch from another whenDefined callback.
  // Queue one extra microtask so this layer always becomes the final shell adapter.
  queueMicrotask(() => {
    const Panel = customElements.get("eshtaya-smart-control-panel");
    if (!Panel || Panel.prototype.__eshtayaV22Applied) return;
    const p = Panel.prototype;
    p.__eshtayaV22Applied = true;

    const baseAccessPage = p._accessPage;
    const baseClick = p._click;
    const baseCss = p._css;

    p._scheduleShellRecovery = function(err) {
      const text = escV22Error(err).toLowerCase();
      if (text.includes("unauthorized") || text.includes("permission") || text.includes("forbidden")) return;
      clearTimeout(this.__escShellRetry);
      this.__escShellRetryAttempt = (this.__escShellRetryAttempt || 0) + 1;
      const delay = Math.min(30000, 1200 * Math.pow(1.8, Math.min(this.__escShellRetryAttempt, 7)));
      this.__escShellRetry = setTimeout(() => {
        if (this.isConnected && this._hass) this._load();
      }, delay);
    };

    p._load = async function() {
      if (!this._hass || this._loading) return;
      this._loading = true;
      const generation = (this.__escShellGeneration || 0) + 1;
      this.__escShellGeneration = generation;
      try {
        const access = await escV22Timeout(
          this._hass.callWS({type: `${ESC_DOMAIN_V22}/access/current`}),
          12000,
          "Access profile"
        );
        if (generation !== this.__escShellGeneration) return;
        this._access = access;
        this.__escShellRetryAttempt = 0;
        clearTimeout(this.__escShellRetry);

        const allowed = view => {
          const map = {
            dashboard: "dashboard.view", entity: "entity.view", tuya: "tuya.view",
            multi: "multi.view", docs: "docs.view", system: "system.view", access: "access.manage"
          };
          return map[view] ? access.permissions?.includes(map[view]) : false;
        };
        if (!allowed(this._view)) {
          this._view = ["dashboard","entity","tuya","multi","docs","system","access"].find(allowed) || "none";
        }

        const jobs = [];
        if (escV22Permission(this, "dashboard.view")) {
          jobs.push(
            escV22Timeout(this._hass.callWS({type: `${ESC_DOMAIN_V22}/overview`}), 20000, "Overview")
              .then(value => { if (generation === this.__escShellGeneration) this._overview = value; })
              .catch(err => { if (generation === this.__escShellGeneration) this._overviewError = escV22Error(err); })
          );
        } else {
          this._overview = null;
        }
        if (escV22Permission(this, "access.manage")) {
          jobs.push(
            escV22Timeout(this._hass.callWS({type: `${ESC_DOMAIN_V22}/access/snapshot`}), 15000, "Eshtaya access")
              .then(value => { if (generation === this.__escShellGeneration) this._accessAdmin = value; })
              .catch(err => { if (generation === this.__escShellGeneration) this._accessAdminError = escV22Error(err); })
          );
        } else {
          this._accessAdmin = null;
        }
        if (access.is_admin) {
          jobs.push(
            escV22Timeout(this._hass.callWS({type: `${ESC_DOMAIN_V22}/ha_access/snapshot`}), 15000, "Home Assistant access")
              .then(value => { if (generation === this.__escShellGeneration) this._haAccess = value; })
              .catch(err => { if (generation === this.__escShellGeneration) this._haAccessError = escV22Error(err); })
          );
        } else {
          this._haAccess = null;
        }
        await Promise.allSettled(jobs);
        this._error = "";
      } catch (err) {
        if (generation !== this.__escShellGeneration) return;
        this._error = escV22Error(err);
        this._scheduleShellRecovery(err);
      } finally {
        if (generation === this.__escShellGeneration) {
          this._loading = false;
          this._render();
        }
      }
    };

    p._haAccessSection = function() {
      if (!this._access?.is_admin) {
        return `<section class="haAccessCard"><div class="haAccessHead"><div><span>HOME ASSISTANT CORE</span><h2>${escV22Text(this,"Home Assistant system access","صلاحيات نظام Home Assistant")}</h2></div><span class="haCoreBadge">CORE</span></div><p>${escV22Text(this,"Only a real Home Assistant administrator can change Core-wide user access. Eshtaya roles cannot elevate a non-admin into this section.","فقط مدير Home Assistant الحقيقي يستطيع تعديل صلاحيات النظام. دور Eshtaya وحده لا يرفع مستخدماً عادياً لصلاحيات مدير النظام.")}</p></section>`;
      }
      const snap = this._haAccess;
      if (!snap) {
        return `<section class="haAccessCard"><div class="loading">${this._icon("mdi:loading","spin")} ${escV22Text(this,"Loading Home Assistant system access...","جاري تحميل صلاحيات Home Assistant الفعلية...")}</div>${this._haAccessError?`<div class="accessError">${this._esc(this._haAccessError)}</div>`:""}</section>`;
      }
      const users = snap.users || [];
      const roleLabel = id => ({administrator:escV22Text(this,"Administrator","مدير"),user:escV22Text(this,"User","مستخدم"),read_only:escV22Text(this,"Read Only","قراءة فقط"),owner:escV22Text(this,"Owner","المالك")}[id] || id);
      const rows = users.map(user => {
        const locked = user.is_owner || user.system_generated;
        const roleOptions = ["administrator","user","read_only"].map(role => `<option value="${role}" ${user.ha_role===role?"selected":""}>${roleLabel(role)}</option>`).join("");
        return `<article class="haUserRow" data-ha-user="${this._esc(user.id)}"><div class="haUserIdentity"><div class="haAvatar">${this._icon(user.is_owner?"mdi:crown-outline":user.is_admin?"mdi:shield-account-outline":"mdi:account-outline")}</div><div><b>${this._esc(user.name)}</b><small>${user.is_owner?roleLabel("owner"):roleLabel(user.ha_role)}${user.system_generated?` · ${escV22Text(this,"System user","مستخدم نظام")}`:""}</small></div></div><label><span>${escV22Text(this,"System role","دور النظام")}</span><select data-ha-role ${locked?"disabled":""}>${user.is_owner?`<option value="owner" selected>${roleLabel("owner")}</option>`:roleOptions}</select></label><label class="haCheck"><input type="checkbox" data-ha-active ${user.is_active?"checked":""} ${locked?"disabled":""}><span>${escV22Text(this,"Active account","الحساب فعال")}</span></label><label class="haCheck"><input type="checkbox" data-ha-local ${user.local_only?"checked":""} ${user.system_generated?"disabled":""}><span>${escV22Text(this,"Local network only","دخول محلي فقط")}</span></label><button class="primary" data-ha-save="${this._esc(user.id)}" ${locked?"disabled":""}>${this._icon("mdi:content-save-outline")} ${escV22Text(this,"Apply to Home Assistant","تطبيق على Home Assistant")}</button></article>`;
      }).join("");
      return `<section class="haAccessCard"><div class="haAccessHead"><div><span>HOME ASSISTANT CORE · BACKEND ENFORCED</span><h2>${escV22Text(this,"Home Assistant system access","صلاحيات نظام Home Assistant")}</h2><p>${escV22Text(this,"These controls modify the real Home Assistant user groups, not only this integration. Changes affect the whole Home Assistant instance according to Core authorization.","هذه الإعدادات تعدّل مجموعات المستخدم الحقيقية داخل Home Assistant، وليست فقط صلاحيات الإضافة. التغيير ينعكس على النظام كله حسب محرك صلاحيات Core.")}</p></div><span class="haCoreBadge">CORE</span></div><div class="haRoleLegend"><div><b>${roleLabel("administrator")}</b><span>${escV22Text(this,"Full Home Assistant administration.","إدارة Home Assistant كاملة.")}</span></div><div><b>${roleLabel("user")}</b><span>${escV22Text(this,"Normal Core user; administrator-only configuration remains blocked.","مستخدم عادي؛ إعدادات المدير في Core تبقى ممنوعة.")}</span></div><div><b>${roleLabel("read_only")}</b><span>${escV22Text(this,"Core-enforced read-only entity access.","قراءة فقط للكيانات ومطبقة من Core.")}</span></div></div><div class="haWarning">${this._icon("mdi:shield-alert-outline")}<div><b>${escV22Text(this,"Important Core limitation","حد مهم في Home Assistant")}</b><span>${escV22Text(this,"Home Assistant 2026 still does not expose supported custom Core roles, explicit deny rules, or per-service ACL to HACS integrations. This panel therefore uses only supported Core groups and keeps Eshtaya permissions as a separate additional layer.","Home Assistant 2026 لا يوفر لـ HACS API مدعوماً لإنشاء أدوار Core مخصصة أو Deny Rules أو صلاحيات لكل Service. لذلك هذا القسم يستخدم مجموعات Core المدعومة فقط، وتبقى صلاحيات Eshtaya طبقة إضافية منفصلة.")}</span></div></div><div class="haUsers">${rows}</div></section>`;
    };

    p._accessPage = function() {
      const integration = typeof baseAccessPage === "function" ? baseAccessPage.call(this) : "";
      return `${this._haAccessSection()}${integration}`;
    };

    p._saveHaAccess = async function(userId, button) {
      const row = button?.closest?.("[data-ha-user]");
      if (!row || !this._hass) return;
      const role = row.querySelector("[data-ha-role]")?.value;
      const active = Boolean(row.querySelector("[data-ha-active]")?.checked);
      const localOnly = Boolean(row.querySelector("[data-ha-local]")?.checked);
      button.disabled = true;
      try {
        await this._hass.callWS({
          type: `${ESC_DOMAIN_V22}/ha_access/update_user`,
          user_id: userId,
          role,
          is_active: active,
          local_only: localOnly,
        });
        this._haAccess = await this._hass.callWS({type: `${ESC_DOMAIN_V22}/ha_access/snapshot`});
        this._toast = escV22Text(this,"Home Assistant access updated","تم تحديث صلاحيات Home Assistant الفعلية");
      } catch (err) {
        this._toast = `${escV22Text(this,"System access update failed","فشل تحديث صلاحيات النظام")}: ${escV22Error(err)}`;
      } finally {
        this._render();
        setTimeout(() => { this._toast = ""; this._render(); }, 3500);
      }
    };

    p._click = function(e) {
      const haSave = e.target.closest?.("[data-ha-save]");
      if (haSave) {
        this._saveHaAccess(haSave.dataset.haSave, haSave);
        return;
      }
      return baseClick?.call(this, e);
    };

    p._css = function() {
      return `${baseCss.call(this)}
      .haAccessCard{border:1px solid var(--divider-color);background:var(--card-background-color);border-radius:22px;padding:20px;margin-bottom:14px}.haAccessHead{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}.haAccessHead>div>span{font-size:9px;letter-spacing:1.2px;font-weight:900;color:var(--primary-color)}.haAccessHead h2{margin:5px 0 6px;font-size:21px}.haAccessHead p,.haAccessCard>p{color:var(--secondary-text-color);font-size:11px;line-height:1.7;max-width:1000px}.haCoreBadge{font-size:9px;font-weight:950;padding:7px 9px;border-radius:999px;background:color-mix(in srgb,var(--primary-color) 12%,var(--secondary-background-color));color:var(--primary-color);border:1px solid color-mix(in srgb,var(--primary-color) 28%,var(--divider-color))}.haRoleLegend{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:14px 0}.haRoleLegend>div{border:1px solid var(--divider-color);background:var(--secondary-background-color);border-radius:13px;padding:11px;display:grid;gap:4px}.haRoleLegend b{font-size:11px}.haRoleLegend span{font-size:9px;color:var(--secondary-text-color);line-height:1.5}.haWarning{display:grid;grid-template-columns:auto 1fr;gap:10px;padding:12px;border-radius:13px;background:color-mix(in srgb,#f5a623 10%,var(--secondary-background-color));border:1px solid color-mix(in srgb,#f5a623 35%,var(--divider-color));margin-bottom:12px}.haWarning ha-icon{color:#f5a623}.haWarning div{display:grid;gap:3px}.haWarning b{font-size:11px}.haWarning span{font-size:9.5px;color:var(--secondary-text-color);line-height:1.6}.haUsers{display:grid;gap:8px}.haUserRow{display:grid;grid-template-columns:minmax(220px,1.3fr) minmax(150px,.75fr) minmax(130px,.55fr) minmax(150px,.65fr) auto;align-items:center;gap:10px;border:1px solid var(--divider-color);background:var(--secondary-background-color);border-radius:14px;padding:11px}.haUserIdentity{display:flex;align-items:center;gap:9px;min-width:0}.haAvatar{width:38px;height:38px;border-radius:11px;display:grid;place-items:center;background:var(--card-background-color);color:var(--primary-color)}.haUserIdentity>div:last-child{display:grid;min-width:0}.haUserIdentity b{font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.haUserIdentity small{font-size:9px;color:var(--secondary-text-color)}.haUserRow label{display:grid;gap:4px}.haUserRow label>span{font-size:8.5px;color:var(--secondary-text-color);font-weight:800}.haUserRow select{width:100%;border:1px solid var(--divider-color);background:var(--card-background-color);color:var(--primary-text-color);border-radius:9px;padding:8px}.haCheck{grid-template-columns:auto 1fr!important;align-items:center}.haCheck input{accent-color:var(--primary-color)}.haUserRow button{white-space:nowrap}.accessError{padding:10px;border-radius:10px;background:color-mix(in srgb,var(--error-color) 8%,var(--secondary-background-color));color:var(--error-color);margin-top:10px}@media(max-width:1050px){.haUserRow{grid-template-columns:1fr 1fr}.haUserIdentity{grid-column:1/-1}.haUserRow button{width:100%}}@media(max-width:700px){.haRoleLegend{grid-template-columns:1fr}.haUserRow{grid-template-columns:1fr}.haUserIdentity{grid-column:auto}.haAccessHead{align-items:center}}
      `;
    };

    if (!this?.__dummy) {
      // no-op: keeps module side-effect only and makes lint/static parsers happy.
    }
  });
});
