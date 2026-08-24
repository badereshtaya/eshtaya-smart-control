const DOMAIN = "eshtaya_smart_control";

const VIEW_PERMISSION = {
  dashboard: "dashboard.view",
  entity: "entity.view",
  tuya: "tuya.view",
  multi: "multi.view",
  template: "template.view",
  docs: "docs.view",
  system: "system.view",
  access: "access.manage",
};

const DOCS_V21 = [
  ["GETTING_STARTED", "mdi:rocket-launch-outline", "Getting Started", "البدء والتثبيت"],
  ["DASHBOARD", "mdi:view-dashboard-outline", "Dashboard", "لوحة التحكم"],
  ["ENTITY_CONTROL", "mdi:account-eye-outline", "Entity & Alexa Control", "إدارة الكيانات وأليكسا"],
  ["TUYA_CONTROL", "mdi:cloud-cog-outline", "Tuya Control", "إدارة تويا"],
  ["MULTIWAY", "mdi:electric-switch", "Multi-Way", "Multi-Way"],
  ["SMART_GROUPS", "mdi:lightbulb-group-outline", "Smart Groups", "المجموعات الذكية"],
  ["COMMISSIONING", "mdi:tools", "Commissioning", "التجهيز والـCommissioning"],
  ["SYSTEM_CENTER", "mdi:heart-pulse", "System Center", "مركز النظام"],
  ["ACCESS_CONTROL", "mdi:account-key-outline", "Access Control", "مركز الصلاحيات"],
  ["MIGRATION", "mdi:swap-horizontal-bold", "Migration", "الهجرة"],
  ["ARCHITECTURE", "mdi:sitemap-outline", "Architecture", "البنية التقنية"],
  ["SECURITY_BACKUP", "mdi:shield-lock-outline", "Security & Backup", "الأمان والنسخ الاحتياطي"],
  ["TROUBLESHOOTING", "mdi:lifebuoy", "Troubleshooting", "حل المشاكل"],
  ["TEMPLATE_MANAGER", "mdi:swap-horizontal-bold", "Template Manager", "إدارة الكيانات الدائمة"],
];

const PERMISSION_LABELS = {
  "dashboard.view": ["Dashboard", "لوحة التحكم"],
  "entity.view": ["Entity: View", "الكيانات: مشاهدة"],
  "entity.manage": ["Entity: Manage", "الكيانات: إدارة"],
  "tuya.view": ["Tuya: View", "تويا: مشاهدة"],
  "tuya.control": ["Tuya: Control", "تويا: تحكم"],
  "tuya.configure": ["Tuya: Configure", "تويا: إعداد الحساب"],
  "multi.view": ["Multi-Way: View", "Multi-Way: مشاهدة"],
  "multi.control": ["Multi-Way: Control", "Multi-Way: تحكم"],
  "multi.manage": ["Multi-Way: Manage", "Multi-Way: إدارة"],
  "template.view": ["Template Manager: View", "الكيانات الدائمة: مشاهدة"],
  "template.manage": ["Template Manager: Manage", "الكيانات الدائمة: إدارة"],
  "docs.view": ["Documentation", "التوثيق"],
  "system.view": ["System: View", "النظام: مشاهدة"],
  "system.actions": ["System: Actions", "النظام: إجراءات"],
  "system.reports": ["System: Reports", "النظام: تقارير"],
  "access.manage": ["Access Control", "إدارة الصلاحيات"],
};

function ar(panel) { return panel._lang === "ar"; }
function txt(panel, en, arabic) { return ar(panel) ? arabic : en; }
function can(panel, permission) {
  return Boolean(panel._access?.permissions?.includes(permission));
}
function moduleAllowed(panel, view) {
  const permission = VIEW_PERMISSION[view];
  if (!permission) return view === "none";
  return can(panel, permission);
}
function firstAllowedView(panel) {
  return ["dashboard", "entity", "tuya", "multi", "template", "docs", "system", "access"].find(v => moduleAllowed(panel, v)) || "none";
}

customElements.whenDefined("eshtaya-smart-control-panel").then(() => {
  const Panel = customElements.get("eshtaya-smart-control-panel");
  if (!Panel || Panel.prototype.__eshtayaV21Applied) return;
  const p = Panel.prototype;
  p.__eshtayaV21Applied = true;

  const originalCss = p._css;
  const originalClick = p._click;

  p._load = async function () {
    if (!this._hass || this._loading) return;
    this._loading = true;
    try {
      this._access = await this._hass.callWS({type: `${DOMAIN}/access/current`});
      if (!moduleAllowed(this, this._view)) this._view = firstAllowedView(this);
      this._overview = can(this, "dashboard.view")
        ? await this._hass.callWS({type: `${DOMAIN}/overview`})
        : null;
      this._accessAdmin = can(this, "access.manage")
        ? await this._hass.callWS({type: `${DOMAIN}/access/snapshot`})
        : null;
      this._error = "";
    } catch (e) {
      this._error = e?.message || String(e);
    } finally {
      this._loading = false;
      this._render();
    }
  };

  p._nav = function () {
    const items = [
      ["dashboard", "mdi:view-dashboard-outline", this._t("dashboard")],
      ["entity", "mdi:account-eye-outline", this._t("entity")],
      ["tuya", "mdi:cloud-cog-outline", this._t("tuya")],
      ["multi", "mdi:home-switch-outline", this._t("multi")],
      ["template", "mdi:swap-horizontal-bold", txt(this,"Template Manager","الكيانات الدائمة")],
      ["docs", "mdi:book-open-page-variant-outline", this._t("docs")],
      ["system", "mdi:heart-pulse", this._t("system")],
      ["access", "mdi:account-key-outline", txt(this, "Access Control", "الصلاحيات")],
    ].filter(([view]) => moduleAllowed(this, view));
    return `<nav>${items.map(([v,i,l]) => `<button data-view="${v}" class="${this._view===v?"active":""}">${this._icon(i)}<span>${l}</span></button>`).join("")}</nav>`;
  };

  p._body = function () {
    if (this._view === "none") return this._noAccess();
    if (!moduleAllowed(this, this._view)) return this._noAccess();
    if (this._view === "access") return this._accessPage();
    if (this._view === "entity") return this._tool("mdi:account-eye-outline",this._t("entity"),this._t("entityDesc"),`<eshtaya-entity-manager-panel></eshtaya-entity-manager-panel>`);
    if (this._view === "tuya") return this._tool("mdi:cloud-cog-outline",this._t("tuya"),this._t("tuyaDesc"),`<eshtaya-tuya-control></eshtaya-tuya-control>`);
    if (this._view === "multi") return this._tool("mdi:home-switch-outline",this._t("multi"),this._t("multiDesc"),`<eshtaya-multiway-panel></eshtaya-multiway-panel>`);
    if (this._view === "docs") return this._docs();
    if (this._view === "system") return this._systemV21();
    return this._dashboardV21();
  };

  p._noAccess = function () {
    return `<section class="noAccess"><div>${this._icon("mdi:shield-lock-outline")}</div><h1>${txt(this,"No access assigned","لا توجد صلاحيات مخصصة")}</h1><p>${txt(this,"Ask a Home Assistant administrator to assign an Eshtaya Smart Control role to this user.","اطلب من مدير Home Assistant إعطاء هذا المستخدم دوراً في Eshtaya Smart Control.")}</p></section>`;
  };

  p._dashboardV21 = function () {
    const o=this._overview||{},e=o.entity?.stats||{},m=o.multiway||{},s=o.smart_groups||{},t=o.tuya||{},h=o.health||{score:100,state:"excellent"};
    const heroButtons = [
      can(this,"system.view") ? `<button class="primary" data-view="system">${this._icon("mdi:heart-pulse")} ${this._t("system")}</button>` : "",
      can(this,"docs.view") ? `<button class="ghost" data-view="docs">${this._icon("mdi:book-open-page-variant-outline")} ${this._t("docs")}</button>` : "",
    ].join("");
    const metrics=[];
    if(can(this,"entity.view")){metrics.push(["mdi:format-list-bulleted",e.total??0,this._t("entities")],["mdi:alert-circle-outline",e.unavailable??0,this._t("unavailable")],["mdi:account-voice-off-outline",e.excluded??0,this._t("alexaHidden")]);}
    if(can(this,"multi.view")){metrics.push(["mdi:electric-switch",m.groups??0,this._t("groups")],["mdi:lightbulb-group-outline",s.groups??0,this._t("smartGroups")]);}
    if(can(this,"tuya.view")){metrics.push(["mdi:cloud-check-outline",t.configured?this._t("activated"):this._t("notActivated"),this._t("tuyaState")]);}
    const moduleCards=[];
    if(can(this,"entity.view")) moduleCards.push(this._module("entity","mdi:account-eye-outline",this._t("entity"),this._t("entityDesc"),`${e.total??0} ${this._t("entities")}`,"violet"));
    if(can(this,"tuya.view")) moduleCards.push(this._module("tuya","mdi:cloud-cog-outline",this._t("tuya"),this._t("tuyaDesc"),t.configured?this._t("activated"):this._t("notActivated"),"cyan"));
    if(can(this,"multi.view")) moduleCards.push(this._module("multi","mdi:home-switch-outline",this._t("multi"),this._t("multiDesc"),`${m.groups??0} + ${s.groups??0}`,"green"));
    if(can(this,"template.view")) moduleCards.push(this._module("template","mdi:swap-horizontal-bold",txt(this,"Template Manager","الكيانات الدائمة"),txt(this,"Permanent Light/Fan entities backed by physical switches.","كيانات Light/Fan دائمة مرتبطة بالمفاتيح الفعلية."),"","cyan"));
    if(can(this,"docs.view")) moduleCards.push(this._module("docs","mdi:book-open-page-variant-outline",this._t("docs"),this._t("docsDesc"),`${DOCS_V21.length} ${ar(this)?"دليل":"guides"}`,"amber"));
    if(can(this,"system.view")) moduleCards.push(this._module("system","mdi:heart-pulse",this._t("system"),this._t("systemDesc"),`${h.score??100}/100`,"slate"));
    if(can(this,"access.manage")) moduleCards.push(this._module("access","mdi:account-key-outline",txt(this,"Access Control","مركز الصلاحيات"),txt(this,"Manage Home Assistant users, roles, overrides, temporary access and audit history.","إدارة مستخدمي Home Assistant والأدوار والاستثناءات والصلاحيات المؤقتة وسجل التدقيق."),`${this._accessAdmin?.users?.length??0} ${txt(this,"users","مستخدم")}`,"violet"));
    return `<section class="hero"><div class="heroText"><span class="pill">${this._icon("mdi:auto-fix")} ${this._t("smartPlatform")}</span><h1>${this._t("overview")}</h1><p>${this._t("subtitle")}</p><div class="heroButtons">${heroButtons}</div></div><div class="score"><div class="ring" style="--score:${Number(h.score)||0}"><div><strong>${h.score??100}</strong><small>/ 100</small></div></div><b>${this._t("healthScore")}</b><span class="state ${h.state}">${this._t(h.state||"excellent")}</span></div></section>${metrics.length?`<section class="metrics permissionMetrics">${metrics.map(([i,v,l])=>`<article>${this._icon(i)}<div><strong>${v}</strong><small>${l}</small></div></article>`).join("")}</section>`:""}${this._recommendations(o.recommendations||[])}<section class="moduleGrid">${moduleCards.join("")}</section>`;
  };

  p._systemV21 = function () {
    const o=this._overview||{},h=o.health||{},sync=o.entity?.file_sync,m=o.migration||{};
    const actions=[];
    if(can(this,"system.actions")){
      if(can(this,"entity.manage")) actions.push(`<button data-sys="repair_alexa_files">${this._icon("mdi:file-sync-outline")}<span>${this._t("repairAlexa")}</span></button>`);
      if(can(this,"tuya.view")) actions.push(`<button data-sys="refresh_tuya">${this._icon("mdi:cloud-refresh-outline")}<span>${this._t("refreshTuya")}</span></button>`);
      if(can(this,"multi.control")) actions.push(`<button data-sys="sync_groups" data-physical="1">${this._icon("mdi:sync")}<span>${this._t("syncGroups")}</span></button>`);
    }
    if(can(this,"system.reports")) actions.push(`<button data-action="system-report">${this._icon("mdi:file-download-outline")}<span>${this._t("downloadReport")}</span></button>`);
    return `<section class="pageTitle"><div class="pageIcon">${this._icon("mdi:heart-pulse")}</div><div><span>SYSTEM INTELLIGENCE</span><h1>${this._t("system")}</h1><p>${this._t("systemDesc")}</p></div></section><section class="systemGrid"><article class="panel"><div class="panelHead"><h2>${this._t("healthScore")}</h2><strong class="bigScore">${h.score??100}</strong></div><div class="healthBar"><i style="width:${Math.max(0,Math.min(100,Number(h.score)||0))}%"></i></div>${this._recommendations(o.recommendations||[])}</article><article class="panel"><div class="panelHead"><h2>${this._t("quickActions")}</h2>${this._icon("mdi:lightning-bolt-outline")}</div>${actions.length?`<div class="actions">${actions.join("")}</div>`:`<p class="muted">${txt(this,"No system actions are assigned to this role.","لا توجد إجراءات نظام مسموحة لهذا الدور.")}</p>`}</article>${can(this,"entity.view")?`<article class="panel"><div class="panelHead"><h2>${this._t("fileHealth")}</h2><span class="badge ${sync?.ok===false?"warning":"success"}">${sync?.ok===false?this._t("needsRepair"):this._t("synchronized")}</span></div><code>/config/hidden_entities.yaml</code><code>/config/www/hidden_entities.yaml</code></article>`:""}</section>${this._migration(m)}`;
  };

  p._docs = function () {
    if(this._doc) return this._docPage();
    const q=this._docSearch.trim().toLowerCase();
    const docs=DOCS_V21.filter(([slug,_i,en,arabic])=>`${slug} ${en} ${arabic}`.toLowerCase().includes(q));
    return `<section class="pageTitle"><div class="pageIcon">${this._icon("mdi:book-open-page-variant-outline")}</div><div><span>KNOWLEDGE BASE</span><h1>${this._t("documentation")}</h1><p>${this._t("docsDesc")}</p></div></section><div class="docSearch">${this._icon("mdi:magnify")}<input data-doc-search value="${this._esc(this._docSearch)}" placeholder="${this._t("searchDocs")}"></div><section class="docGrid">${docs.map(([slug,icon,en,arabic],i)=>`<button class="docCard" data-doc="${slug}"><span>${i+1}</span><div class="docIcon">${this._icon(icon)}</div><b>${ar(this)?arabic:en}</b><small>${slug}.md</small></button>`).join("")}</section>`;
  };

  p._docPage = function () {
    return `<section class="docPage"><button class="back" data-action="doc-back">${this._icon("mdi:arrow-${ar(this)?"right":"left"}")} ${this._t("back")}</button><article>${this._markdown(this._doc?.content||"")}</article></section>`;
  };

  p._accessPage = function () {
    const snap=this._accessAdmin;if(!snap)return `<section class="panel"><div class="loading">${this._icon("mdi:loading","spin")} ${txt(this,"Loading access data...","جاري تحميل الصلاحيات...")}</div></section>`;
    const users=snap.users||[],roles=snap.roles||{},permissions=snap.permissions||[],audit=snap.audit||[];
    const roleOptions=user=>Object.entries(roles).map(([id,r])=>`<option value="${this._esc(id)}" ${user.assignment?.role===id?"selected":""}>${this._esc(r.name||id)}</option>`).join("");
    const usersHtml=users.map(user=>`<article class="accessUser" data-ac-user="${this._esc(user.id)}"><div class="accessUserHead"><div><b>${this._esc(user.name)}</b><small>${this._esc(user.id)}</small></div><span class="badge ${user.is_admin?"success":""}">${user.is_admin?"HA Admin":txt(this,"Managed user","مستخدم")}</span></div><div class="accessFields"><label>${txt(this,"Role","الدور")}<select data-ac-role ${user.is_admin?"disabled":""}>${roleOptions(user)}</select></label><label>${txt(this,"Expires","ينتهي")}<input data-ac-expiry type="datetime-local" value="${user.assignment?.expires_at?String(user.assignment.expires_at).slice(0,16):""}" ${user.is_admin?"disabled":""}></label></div><details><summary>${txt(this,"Permission overrides","استثناءات الصلاحيات")}</summary><div class="overrideGrid"><div><h4>${txt(this,"Force allow","سماح إضافي")}</h4>${permissions.map(perm=>`<label><input type="checkbox" data-ac-allow="${this._esc(perm)}" ${user.assignment?.allow?.includes(perm)?"checked":""} ${user.is_admin?"disabled":""}> <span>${this._permLabel(perm)}</span></label>`).join("")}</div><div><h4>${txt(this,"Force deny","منع إضافي")}</h4>${permissions.map(perm=>`<label><input type="checkbox" data-ac-deny="${this._esc(perm)}" ${user.assignment?.deny?.includes(perm)?"checked":""} ${user.is_admin?"disabled":""}> <span>${this._permLabel(perm)}</span></label>`).join("")}</div></div></details>${user.is_admin?"":`<button class="primary accessSave" data-ac-save-user="${this._esc(user.id)}">${txt(this,"Save permissions","حفظ الصلاحيات")}</button>`}<div class="effective"><b>${txt(this,"Effective permissions","الصلاحيات الفعلية")}</b><small>${(user.effective_permissions||[]).map(p=>this._permLabel(p)).join(" · ")||txt(this,"No access","لا يوجد وصول")}</small></div></article>`).join("");
    const customRoles=Object.entries(roles).filter(([,r])=>r.custom).map(([id,r])=>`<div class="roleRow"><div><b>${this._esc(r.name)}</b><small>${this._esc(id)} · ${(r.permissions||[]).length} permissions</small></div><button class="iconBtn danger" data-ac-delete-role="${this._esc(id)}">${this._icon("mdi:delete-outline")}</button></div>`).join("")||`<p class="muted">${txt(this,"No custom roles yet.","لا توجد أدوار مخصصة بعد.")}</p>`;
    const permissionChecks=permissions.map(perm=>`<label><input type="checkbox" data-ac-role-perm="${this._esc(perm)}"> <span>${this._permLabel(perm)}</span></label>`).join("");
    const auditHtml=audit.slice(0,40).map(row=>`<tr><td>${this._esc(String(row.timestamp||"").replace("T"," ").slice(0,19))}</td><td>${this._esc(row.actor_name||row.actor_id||"—")}</td><td>${this._esc(row.action||"")}</td><td>${this._esc(row.target||"")}</td></tr>`).join("");
    const html=`<section class="pageTitle"><div class="pageIcon">${this._icon("mdi:account-key-outline")}</div><div><span>ROLE BASED ACCESS CONTROL</span><h1>${txt(this,"Access Control Center","مركز الصلاحيات والمستخدمين")}</h1><p>${txt(this,"Backend-enforced permissions for existing Home Assistant users.","صلاحيات محمية من الـBackend لمستخدمي Home Assistant الحاليين.")}</p></div></section><section class="accessLayout"><div class="accessUsers"><div class="sectionHead"><div><span>USERS</span><h2>${txt(this,"Home Assistant users","مستخدمو Home Assistant")}</h2></div><span class="badge">${users.length}</span></div>${usersHtml}</div><aside><article class="panel accessRole"><div class="panelHead"><h2>${txt(this,"Create custom role","إنشاء دور مخصص")}</h2>${this._icon("mdi:shield-account-outline")}</div><label>ID<input data-ac-role-id placeholder="lighting_operator"></label><label>${txt(this,"Role name","اسم الدور")}<input data-ac-role-name placeholder="Lighting Operator"></label><div class="rolePermissions">${permissionChecks}</div><button class="primary full" data-ac-save-role>${txt(this,"Save role","حفظ الدور")}</button></article><article class="panel"><div class="panelHead"><h2>${txt(this,"Custom roles","الأدوار المخصصة")}</h2></div>${customRoles}</article></aside></section><section class="panel auditPanel"><div class="panelHead"><h2>${txt(this,"Audit log","سجل التدقيق")}</h2>${this._icon("mdi:clipboard-text-clock-outline")}</div><div class="tableWrap"><table><thead><tr><th>${txt(this,"Time","الوقت")}</th><th>${txt(this,"Actor","المنفذ")}</th><th>${txt(this,"Action","الإجراء")}</th><th>${txt(this,"Target","الهدف")}</th></tr></thead><tbody>${auditHtml||`<tr><td colspan="4">${txt(this,"No audit events yet.","لا يوجد سجل بعد.")}</td></tr></tbody></table></div></section>`;
    setTimeout(()=>{this.shadowRoot?.querySelectorAll("[data-ac-user]").forEach(row=>{const id=row.dataset.acUser;const u=users.find(x=>x.id===id);const role=u?.assignment?.role||snap.settings?.default_role||"no_access";const select=row.querySelector("[data-ac-role]");if(select)select.value=role;});},0);
    return html;
  };

  p._permLabel = function (permission) {
    const pair=PERMISSION_LABELS[permission]||[permission,permission];
    return ar(this)?pair[1]:pair[0];
  };

  p._refreshAccessAdmin = async function () {
    this._access=await this._hass.callWS({type:`${DOMAIN}/access/current`});
    this._accessAdmin=can(this,"access.manage")?await this._hass.callWS({type:`${DOMAIN}/access/snapshot`}):null;
    if(can(this,"dashboard.view"))this._overview=await this._hass.callWS({type:`${DOMAIN}/overview`});
    this._render();
  };

  p._saveAccessUser = async function (userId) {
    const row=[...this.shadowRoot.querySelectorAll("[data-ac-user]")].find(x=>x.dataset.acUser===userId);if(!row)return;
    const role=row.querySelector("[data-ac-role]")?.value||"no_access";
    const rawExpiry=row.querySelector("[data-ac-expiry]")?.value||"";
    const allow=[...row.querySelectorAll("[data-ac-allow]:checked")].map(x=>x.dataset.acAllow);
    const deny=[...row.querySelectorAll("[data-ac-deny]:checked")].map(x=>x.dataset.acDeny);
    const expires_at=rawExpiry?new Date(rawExpiry).toISOString():null;
    try{await this._hass.callWS({type:`${DOMAIN}/access/assign_user`,user_id:userId,role,allow,deny,expires_at});this._toast=txt(this,"Permissions saved","تم حفظ الصلاحيات");await this._refreshAccessAdmin();}catch(e){this._toast=`${txt(this,"Save failed","فشل الحفظ")}: ${e?.message||e}`;this._render();}
  };

  p._saveAccessRole = async function () {
    const role_id=this.shadowRoot.querySelector("[data-ac-role-id]")?.value?.trim()||"";
    const name=this.shadowRoot.querySelector("[data-ac-role-name]")?.value?.trim()||"";
    const permissions=[...this.shadowRoot.querySelectorAll("[data-ac-role-perm]:checked")].map(x=>x.dataset.acRolePerm);
    if(!role_id){this._toast=txt(this,"Role ID is required","معرّف الدور مطلوب");this._render();return;}
    try{await this._hass.callWS({type:`${DOMAIN}/access/save_role`,role_id,name,permissions});this._toast=txt(this,"Role saved","تم حفظ الدور");await this._refreshAccessAdmin();}catch(e){this._toast=`${txt(this,"Save failed","فشل الحفظ")}: ${e?.message||e}`;this._render();}
  };

  p._deleteAccessRole = async function (roleId) {
    if(!confirm(txt(this,"Delete this custom role?","حذف هذا الدور المخصص؟")))return;
    try{await this._hass.callWS({type:`${DOMAIN}/access/delete_role`,role_id:roleId});this._toast=txt(this,"Role deleted","تم حذف الدور");await this._refreshAccessAdmin();}catch(e){this._toast=`${txt(this,"Save failed","فشل الحفظ")}: ${e?.message||e}`;this._render();}
  };

  p._click = function (e) {
    const t=e.target.closest("[data-ac-save-user],[data-ac-save-role],[data-ac-delete-role],[data-view],[data-action],[data-sys],[data-doc]");
    if(!t)return;
    if(t.dataset.acSaveUser){this._saveAccessUser(t.dataset.acSaveUser);return;}
    if(t.hasAttribute("data-ac-save-role")){this._saveAccessRole();return;}
    if(t.dataset.acDeleteRole){this._deleteAccessRole(t.dataset.acDeleteRole);return;}
    if(t.dataset.view&&!moduleAllowed(this,t.dataset.view)){this._toast=txt(this,"This role does not have access to that module.","هذا الدور لا يملك صلاحية الدخول إلى هذا القسم.");this._render();return;}
    originalClick.call(this,e);
  };

  p._css = function () {
    return originalCss.call(this)+`.permissionMetrics{grid-template-columns:repeat(auto-fit,minmax(170px,1fr))}.noAccess{min-height:60vh;display:grid;place-items:center;align-content:center;text-align:center;gap:12px}.noAccess>div{width:86px;height:86px;border-radius:26px;background:var(--secondary-background-color);display:grid;place-items:center}.noAccess ha-icon{--mdc-icon-size:45px;color:var(--primary-color)}.noAccess h1{margin:0;font-size:30px}.noAccess p,.muted{color:var(--secondary-text-color);line-height:1.7}.accessLayout{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:14px;align-items:start}.accessUsers{display:grid;gap:10px}.accessUser{border:1px solid var(--divider-color);background:var(--card-background-color);border-radius:20px;padding:17px}.accessUserHead{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.accessUserHead>div{display:grid;gap:4px}.accessUserHead small,.effective small{color:var(--secondary-text-color);font-size:9px;overflow-wrap:anywhere}.accessFields{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:14px}.accessFields label,.accessRole>label{display:grid;gap:6px;font-size:10px;font-weight:800}.accessFields select,.accessFields input,.accessRole input{border:1px solid var(--divider-color);background:var(--secondary-background-color);color:var(--primary-text-color);border-radius:11px;padding:10px;outline:none}.accessUser details{margin-top:12px;border:1px solid var(--divider-color);border-radius:12px;padding:10px}.accessUser summary{cursor:pointer;font-size:10px;font-weight:800}.overrideGrid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:10px}.overrideGrid h4{font-size:9px;margin:0 0 7px;color:var(--secondary-text-color)}.overrideGrid label,.rolePermissions label{display:flex;align-items:flex-start;gap:6px;padding:5px 0;font-size:9px}.accessSave{margin-top:12px}.effective{display:grid;gap:5px;margin-top:12px;padding-top:10px;border-top:1px solid var(--divider-color)}.accessRole{display:grid;gap:10px}.rolePermissions{max-height:330px;overflow:auto;border:1px solid var(--divider-color);border-radius:12px;padding:9px}.roleRow{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:9px 0;border-top:1px solid var(--divider-color)}.roleRow>div{display:grid}.roleRow small{font-size:8px;color:var(--secondary-text-color)}.auditPanel{margin-top:14px}.tableWrap{overflow:auto;margin-top:12px}.tableWrap table{width:100%;border-collapse:collapse;font-size:10px}.tableWrap th,.tableWrap td{text-align:start;padding:9px;border-top:1px solid var(--divider-color);white-space:nowrap}@media(max-width:980px){.accessLayout{grid-template-columns:1fr}.accessLayout aside{display:grid;grid-template-columns:1fr 1fr;gap:10px}}@media(max-width:650px){.accessFields,.overrideGrid,.accessLayout aside{grid-template-columns:1fr}.accessUserHead{align-items:center}.permissionMetrics{grid-template-columns:1fr 1fr}}`;
  };
});