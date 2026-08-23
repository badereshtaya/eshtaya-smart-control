import "./tuya-control.js";
import "./entity/eshtaya-entity-manager-panel-loader.js";
import "./multiway/panel.js";

const DOMAIN = "eshtaya_smart_control";

const TEXT = {
  ar: {
    home: "مركز التحكم", entity: "HomeAssistant Entity Control", tuya: "Tuya Entity Control",
    multi: "Multi-Way & Smart Groups", docs: "مركز التوثيق", system: "مركز النظام",
    title: "Eshtaya Smart Control", subtitle: "منصة Eshtaya Smart الموحدة لإدارة Home Assistant",
    choose: "اختر الأداة التي تريد إدارتها", open: "فتح الأداة", language: "اللغة", auto: "تلقائي",
    refresh: "تحديث", ready: "جاهز", configured: "مُعد", notConfigured: "غير مُعد",
    entities: "كيانات", hidden: "مخفي عن Alexa", groups: "مجموعات", fileHealth: "صحة ملفات Alexa",
    synced: "متزامن", needsSync: "يحتاج مزامنة", modules: "الوحدات", migration: "Migration Center",
    migrationDesc: "نقل آمن وتلقائي من إضافات Eshtaya السابقة مع Backup وValidation وRollback.",
    report: "تنزيل تقرير الهجرة", noMigration: "لا توجد إضافات قديمة تحتاج للهجرة على هذا النظام.",
    migrationDone: "تمت الهجرة بنجاح", migrationRunning: "الهجرة قيد التنفيذ", migrationFailed: "الهجرة تحتاج مراجعة",
    beforeAfter: "المقارنة قبل / بعد", before: "قبل", after: "بعد", status: "الحالة",
    entityRules: "قواعد Entity / Alexa", multiGroups: "Multi-Way Groups", smartGroups: "Smart Groups",
    rollback: "الحماية والاسترجاع", backup: "نسخة الهجرة الاحتياطية", rollbackReady: "Rollback متوفر",
    rollbackUsed: "تم استخدام Rollback", legacyEntries: "Config Entries القديمة", removed: "تمت إزالتها بعد التحقق",
    hacsCleanup: "تنظيف HACS", errors: "الأخطاء", none: "لا يوجد", optional: "إعداد اختياري",
    entityDesc: "إدارة أسماء الكيانات وقواعد Alexa وملفات hidden_entities.yaml من لوحة واحدة.",
    tuyaDesc: "إدارة حساب Tuya Cloud والأجهزة والأسماء الرئيسية والفرعية مباشرة من Home Assistant.",
    multiDesc: "Multi-Way وSmart Groups وAction Groups وCommissioning والصحة والنسخ الاحتياطي.",
    docsDesc: "توثيق عربي وإنجليزي للإعداد والاستخدام والهجرة والأمان.",
    systemDesc: "حالة المنصة والوحدات وملفات Alexa والهجرة والتوافق.",
    recentMigration: "تم تحديث النظام تلقائيًا من الإضافات القديمة", details: "عرض التفاصيل",
    steps: {
      detect: "اكتشاف القديم", backup: "إنشاء Backup", copy: "نسخ الإعدادات", quiesce: "إيقاف المحركات القديمة",
      runtime_start: "تشغيل المحرك الجديد", validate: "التحقق", remove_legacy: "إزالة Config Entries القديمة",
      reconcile: "مزامنة الملكية والحالة", hacs_cleanup: "تنظيف HACS"
    },
    stepStatus: { pending: "بانتظار", running: "يعمل", completed: "مكتمل", failed: "فشل", skipped: "تم تخطيه", rolled_back: "تم التراجع" }
  },
  en: {
    home: "Control Hub", entity: "HomeAssistant Entity Control", tuya: "Tuya Entity Control",
    multi: "Multi-Way & Smart Groups", docs: "Documentation Center", system: "System Center",
    title: "Eshtaya Smart Control", subtitle: "The unified Eshtaya Smart administration platform for Home Assistant",
    choose: "Choose the tool you want to manage", open: "Open tool", language: "Language", auto: "Auto",
    refresh: "Refresh", ready: "Ready", configured: "Configured", notConfigured: "Not configured",
    entities: "entities", hidden: "hidden from Alexa", groups: "groups", fileHealth: "Alexa file health",
    synced: "Synchronized", needsSync: "Needs sync", modules: "Modules", migration: "Migration Center",
    migrationDesc: "Safe automatic migration from legacy Eshtaya integrations with backup, validation and rollback.",
    report: "Download migration report", noMigration: "No legacy Eshtaya integrations require migration on this system.",
    migrationDone: "Migration completed successfully", migrationRunning: "Migration in progress", migrationFailed: "Migration needs attention",
    beforeAfter: "Before / after comparison", before: "Before", after: "After", status: "Status",
    entityRules: "Entity / Alexa rules", multiGroups: "Multi-Way Groups", smartGroups: "Smart Groups",
    rollback: "Protection & rollback", backup: "Migration backup", rollbackReady: "Rollback available",
    rollbackUsed: "Rollback was used", legacyEntries: "Legacy config entries", removed: "Removed after validation",
    hacsCleanup: "HACS cleanup", errors: "Errors", none: "None", optional: "Optional configuration",
    entityDesc: "Manage entity names, Alexa rules and hidden_entities.yaml outputs from one control surface.",
    tuyaDesc: "Manage Tuya Cloud account, devices, primary names and property sub-names directly in Home Assistant.",
    multiDesc: "Multi-Way, Smart Groups, Action Groups, commissioning, health and backups.",
    docsDesc: "Bilingual setup, operation, migration and security documentation.",
    systemDesc: "Platform modules, Alexa file health, migration and compatibility status.",
    recentMigration: "This system was automatically upgraded from legacy integrations", details: "View details",
    steps: {
      detect: "Detect legacy", backup: "Create backup", copy: "Copy configuration", quiesce: "Stop legacy engines",
      runtime_start: "Start new runtime", validate: "Validate", remove_legacy: "Remove legacy config entries",
      reconcile: "Reconcile ownership/state", hacs_cleanup: "Clean HACS"
    },
    stepStatus: { pending: "Pending", running: "Running", completed: "Completed", failed: "Failed", skipped: "Skipped", rolled_back: "Rolled back" }
  }
};

class EshtayaSmartControlPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._overview = null;
    this._view = "home";
    this._error = null;
    this._loading = false;
    this._langMode = localStorage.getItem("eshtayaSmartControlLang") || "auto";
  }

  set hass(value) {
    const first = !this._hass;
    this._hass = value;
    if (first) this._load();
    else this._wireChild();
  }

  connectedCallback() {
    this._render();
    this.shadowRoot.addEventListener("click", (event) => this._click(event));
    this.shadowRoot.addEventListener("change", (event) => this._change(event));
  }

  get _lang() {
    if (this._langMode !== "auto") return this._langMode;
    const lang = String(this._hass?.locale?.language || this._hass?.language || "en");
    return lang.toLowerCase().startsWith("ar") ? "ar" : "en";
  }

  get _tr() { return TEXT[this._lang] || TEXT.en; }
  _t(key) { return this._tr[key] ?? TEXT.en[key] ?? key; }

  async _load() {
    if (!this._hass || this._loading) return;
    this._loading = true;
    try {
      this._overview = await this._hass.callWS({ type: `${DOMAIN}/overview` });
      this._error = null;
    } catch (err) {
      this._error = err?.message || String(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }

  _setGlobalLang() {
    if (this._langMode === "auto") delete window.__ESHTAYA_SMART_LANG__;
    else window.__ESHTAYA_SMART_LANG__ = this._langMode;
  }

  _render() {
    if (!this.shadowRoot) return;
    this._setGlobalLang();
    const ar = this._lang === "ar";
    this.shadowRoot.innerHTML = `
      <style>${this._css()}</style>
      <div class="shell" dir="${ar ? "rtl" : "ltr"}">
        ${this._header()}
        ${this._nav()}
        <main>${this._error ? `<div class="errorBanner">${this._esc(this._error)}</div>` : ""}${this._body()}</main>
      </div>`;
    this._wireChild();
  }

  _header() {
    return `<header>
      <button class="brand" data-view="home" aria-label="Home">
        <span class="brandMark"><span>ES</span></span>
        <span class="brandText"><strong>${this._t("title")}</strong><small>${this._t("subtitle")}</small></span>
      </button>
      <div class="headerActions">
        <span class="version">v${this._overview?.version || "1.2.0"}</span>
        <select data-lang title="${this._t("language")}">
          <option value="auto" ${this._langMode === "auto" ? "selected" : ""}>${this._t("auto")}</option>
          <option value="ar" ${this._langMode === "ar" ? "selected" : ""}>العربية</option>
          <option value="en" ${this._langMode === "en" ? "selected" : ""}>English</option>
        </select>
        <button class="round" data-action="refresh" title="${this._t("refresh")}">${this._loading ? "…" : "↻"}</button>
      </div>
    </header>`;
  }

  _nav() {
    const items = [
      ["home", "⌂", this._t("home")], ["entity", "Aa", this._t("entity")], ["tuya", "T", this._t("tuya")],
      ["multi", "↔", this._t("multi")], ["docs", "?", this._t("docs")], ["system", "⚙", this._t("system")]
    ];
    return `<nav>${items.map(([v, i, label]) => `<button class="${this._view === v ? "active" : ""}" data-view="${v}"><i>${i}</i><span>${label}</span></button>`).join("")}</nav>`;
  }

  _body() {
    if (this._view === "entity") return this._tool("entity", this._t("entity"), this._t("entityDesc"), "<eshtaya-entity-manager-panel></eshtaya-entity-manager-panel>");
    if (this._view === "tuya") return this._tool("tuya", this._t("tuya"), this._t("tuyaDesc"), "<eshtaya-tuya-control></eshtaya-tuya-control>");
    if (this._view === "multi") return this._tool("multi", this._t("multi"), this._t("multiDesc"), "<eshtaya-multiway-panel></eshtaya-multiway-panel>");
    if (this._view === "docs") return this._docs();
    if (this._view === "system") return this._system();
    return this._home();
  }

  _tool(_id, title, desc, element) {
    return `<section class="toolTitle">${this._back()}<div><span class="eyebrow">ESHTAYA SMART TOOL</span><h1>${title}</h1><p>${desc}</p></div></section>${element}`;
  }

  _back() { return `<button class="back" data-view="home">${this._lang === "ar" ? "→" : "←"}</button>`; }

  _home() {
    const o = this._overview || {};
    const e = o.entity?.stats || {};
    const m = o.multiway || {};
    const t = o.tuya || {};
    const migration = o.migration || {};
    const migrationBanner = migration.legacy_found
      ? `<section class="migrationBanner ${migration.completed ? "success" : migration.phase === "rolled_back" || migration.phase === "validation_failed" ? "danger" : "active"}">
          <div class="migIcon">${migration.completed ? "✓" : migration.phase === "rolled_back" ? "↶" : "⇄"}</div>
          <div><strong>${migration.completed ? this._t("recentMigration") : this._migrationHeadline(migration)}</strong><small>${this._migrationSummary(migration)}</small></div>
          <button data-view="system">${this._t("details")} ${this._lang === "ar" ? "←" : "→"}</button>
        </section>` : "";

    return `<section class="hero">
      <div class="heroOrbs"><span></span><span></span><span></span></div>
      <div class="heroCopy"><span class="eyebrow">ESHTAYA SMART · CONTROL PLATFORM</span><h1>${this._t("title")}</h1><p>${this._t("choose")}</p></div>
      <div class="metrics">
        ${this._metric(e.total ?? "—", this._t("entities"), "HA")}
        ${this._metric(e.excluded ?? "—", this._t("hidden"), "Alexa")}
        ${this._metric(m.groups ?? 0, "Multi-Way", "↔")}
        ${this._metric(m.smart_groups ?? 0, "Smart Groups", "SG")}
      </div>
    </section>
    ${migrationBanner}
    <section class="toolCards">
      ${this._card("entity", "Aa", this._t("entity"), this._t("entityDesc"), `${e.total ?? 0} ${this._t("entities")}`, "purple")}
      ${this._card("tuya", "T", this._t("tuya"), this._t("tuyaDesc"), t.configured ? this._t("configured") : this._t("notConfigured"), "blue")}
      ${this._card("multi", "↔", this._t("multi"), this._t("multiDesc"), `${m.groups ?? 0} Multi-Way · ${m.smart_groups ?? 0} Smart`, "green")}
      ${this._card("docs", "?", this._t("docs"), this._t("docsDesc"), this._lang === "ar" ? "عربي · English" : "English · عربي", "amber")}
      ${this._card("system", "⚙", this._t("system"), this._t("systemDesc"), migration.legacy_found ? this._migrationHeadline(migration) : this._t("ready"), "slate")}
    </section>`;
  }

  _metric(value, label, icon) { return `<div class="metric"><span>${icon}</span><strong>${value}</strong><small>${label}</small></div>`; }
  _card(view, icon, title, desc, state, tone) { return `<article class="toolCard ${tone}" data-view="${view}"><div class="toolIcon">${icon}</div><div class="toolState">${state}</div><h2>${title}</h2><p>${desc}</p><button data-view="${view}">${this._t("open")} <span>${this._lang === "ar" ? "←" : "→"}</span></button></article>`; }

  _docs() {
    const ar = this._lang === "ar";
    const items = ar ? [
      ["HomeAssistant Entity Control", "إدارة Entity Registry وAlexa visibility وhidden_entities.yaml مع فلاتر وBulk Actions واستيراد/تصدير القواعد."],
      ["Tuya Entity Control", "إدارة حساب Tuya Cloud لكل Home Assistant، البحث بالأجهزة وتعديل أسماء الأجهزة والمخارج من داخل النظام بدون PHP خارجي."],
      ["Multi-Way & Smart Groups", "محرك Multi-Way الكامل وSmart Groups وAction Groups وCommissioning وHealth وDiagnostics وBackup/Restore."],
      ["Automatic Legacy Migration", "عند أول تشغيل يتم اكتشاف الإضافات القديمة، إنشاء Backup مستقل، نسخ الإعدادات، إيقاف القديم، تشغيل الجديد، التحقق من الأعداد، ثم إزالة Config Entries القديمة فقط بعد النجاح. إذا فشل Cutover يتم Rollback تلقائي."],
      ["Security", "تقارير Migration لا تحتوي Client Secret أو بيانات Tuya أو محتوى Storage الخام. الأسرار تبقى في Config Entry والـbackup الداخلي غير معروض من الواجهة."]
    ] : [
      ["HomeAssistant Entity Control", "Manage Entity Registry names, Alexa visibility and hidden_entities.yaml with filters, bulk actions and rule import/export."],
      ["Tuya Entity Control", "Configure Tuya Cloud per Home Assistant instance, search devices, and edit device/property names without an external PHP page."],
      ["Multi-Way & Smart Groups", "Complete Multi-Way engine, Smart Groups, Action Groups, commissioning, health, diagnostics and backup/restore."],
      ["Automatic Legacy Migration", "On first setup, legacy integrations are detected, backed up, copied, quiesced and replaced only after before/after validation. Failed cutovers automatically roll back."],
      ["Security", "Migration reports exclude Tuya secrets, credentials and raw storage payloads. Secrets remain inside the Home Assistant config entry."]
    ];
    return `<section class="toolTitle">${this._back()}<div><span class="eyebrow">KNOWLEDGE BASE</span><h1>${this._t("docs")}</h1><p>${this._t("docsDesc")}</p></div></section>
      <section class="docsGrid">${items.map((item, i) => `<article><span class="docNo">0${i + 1}</span><h2>${item[0]}</h2><p>${item[1]}</p></article>`).join("")}</section>`;
  }

  _system() {
    const o = this._overview || {};
    const sync = o.entity?.file_sync;
    const migration = o.migration || {};
    return `<section class="toolTitle">${this._back()}<div><span class="eyebrow">SYSTEM OPERATIONS</span><h1>${this._t("system")}</h1><p>${this._t("systemDesc")}</p></div></section>
      <section class="systemTop">
        <article class="panelCard"><div class="panelHead"><h2>${this._t("modules")}</h2><span class="health good">${this._t("ready")}</span></div>
          ${this._moduleRow("HomeAssistant Entity Control", true)}
          ${this._moduleRow("Tuya Entity Control", !!o.tuya?.configured, this._t("optional"))}
          ${this._moduleRow("Multi-Way & Smart Groups", true)}
        </article>
        <article class="panelCard"><div class="panelHead"><h2>${this._t("fileHealth")}</h2><span class="health ${sync?.ok === false ? "warn" : "good"}">${sync?.ok === false ? this._t("needsSync") : this._t("synced")}</span></div>
          <div class="paths"><code>/config/hidden_entities.yaml</code><code>/config/www/hidden_entities.yaml</code></div>
        </article>
      </section>
      ${this._migrationCenter(migration)}`;
  }

  _moduleRow(name, ok, note = "") { return `<div class="moduleRow"><span class="moduleDot ${ok ? "good" : "idle"}"></span><div><strong>${name}</strong>${note ? `<small>${note}</small>` : ""}</div><span>${ok ? "✓" : "○"}</span></div>`; }

  _migrationCenter(m) {
    if (!m || (!m.legacy_found && m.phase !== "rolled_back")) {
      return `<section class="migrationCenter empty"><div class="migrationHeader"><div><span class="eyebrow">AUTOMATIC LEGACY MIGRATION</span><h2>${this._t("migration")}</h2><p>${this._t("migrationDesc")}</p></div></div><div class="emptyState"><span>✓</span><strong>${this._t("noMigration")}</strong></div></section>`;
    }

    const steps = Array.isArray(m.steps) ? m.steps : [];
    const before = m.counts?.before || m.expected || {};
    const after = m.counts?.validated || m.counts?.after_start || {};
    const rollback = m.rollback || {};
    const errors = m.errors || [];
    const headline = this._migrationHeadline(m);
    const tone = m.completed ? "success" : (m.phase === "rolled_back" || m.phase === "validation_failed") ? "danger" : "active";

    return `<section class="migrationCenter ${tone}">
      <div class="migrationHeader">
        <div><span class="eyebrow">AUTOMATIC LEGACY MIGRATION</span><h2>${this._t("migration")}</h2><p>${this._t("migrationDesc")}</p></div>
        <div class="migrationActions"><span class="migrationState">${headline}</span>${m.report_ready ? `<button class="primary" data-action="download-report">⇩ ${this._t("report")}</button>` : ""}</div>
      </div>
      <div class="timeline">${steps.map((step, i) => this._step(step, i)).join("")}</div>
      <div class="migrationGrid">
        <article class="migrationPanel"><h3>${this._t("beforeAfter")}</h3>
          ${this._compareRow(this._t("entityRules"), before.entity_rules, after.entity_rules)}
          ${this._compareRow(this._t("multiGroups"), before.multiway_groups, after.multiway_groups)}
          ${this._compareRow(this._t("smartGroups"), before.smart_groups, after.smart_groups)}
        </article>
        <article class="migrationPanel"><h3>${this._t("rollback")}</h3>
          <div class="kv"><span>${this._t("backup")}</span><code>${this._esc(m.backup_store || rollback.backup_store || "—")}</code></div>
          <div class="kv"><span>${this._t("status")}</span><strong>${rollback.used ? this._t("rollbackUsed") : rollback.available ? this._t("rollbackReady") : "—"}</strong></div>
          <div class="kv"><span>${this._t("legacyEntries")}</span><strong>${m.removed_entries?.length ? `${m.removed_entries.length} · ${this._t("removed")}` : (m.legacy_entries?.length ?? 0)}</strong></div>
        </article>
        <article class="migrationPanel"><h3>${this._t("hacsCleanup")}</h3>${this._hacsRows(m.hacs_cleanup || {})}</article>
        <article class="migrationPanel"><h3>${this._t("errors")}</h3>${errors.length ? `<ul class="errors">${errors.map(e => `<li>${this._esc(e)}</li>`).join("")}</ul>` : `<div class="noErrors">✓ ${this._t("none")}</div>`}</article>
      </div>
    </section>`;
  }

  _step(step, index) {
    const status = step.status || "pending";
    const label = this._tr.steps?.[step.id] || step.id;
    const statusLabel = this._tr.stepStatus?.[status] || status;
    return `<div class="step ${status}"><div class="stepRail"><span>${status === "completed" ? "✓" : status === "failed" ? "!" : status === "rolled_back" ? "↶" : index + 1}</span></div><div class="stepBody"><div><strong>${label}</strong><em>${statusLabel}</em></div>${step.message ? `<small>${this._esc(step.message)}</small>` : ""}</div></div>`;
  }

  _compareRow(label, before, after) {
    const b = before ?? 0, a = after ?? 0;
    const ok = Number(a) >= Number(b);
    return `<div class="compareRow"><strong>${label}</strong><span>${this._t("before")} <b>${b}</b></span><i>→</i><span>${this._t("after")} <b>${a}</b></span><em class="${ok ? "ok" : "bad"}">${ok ? "✓" : "!"}</em></div>`;
  }

  _hacsRows(data) {
    const entries = Object.entries(data || {});
    if (!entries.length) return `<div class="subtle">—</div>`;
    return entries.map(([repo, state]) => `<div class="hacsRow"><span>${this._esc(repo.replace("badereshtaya/hacs-eshtaya-", ""))}</span><strong class="${String(state).startsWith("failed:") ? "bad" : state === "removed" || state === "not_registered" ? "ok" : ""}">${this._esc(state)}</strong></div>`).join("");
  }

  _migrationHeadline(m) {
    if (m.completed) return this._t("migrationDone");
    if (m.phase === "rolled_back" || m.phase === "validation_failed" || m.phase === "cleanup_partial") return this._t("migrationFailed");
    return this._t("migrationRunning");
  }

  _migrationSummary(m) {
    const exp = m.expected || {};
    return `${exp.entity_rules ?? 0} ${this._t("entityRules")} · ${exp.multiway_groups ?? 0} Multi-Way · ${exp.smart_groups ?? 0} Smart Groups`;
  }

  async _downloadReport() {
    if (!this._hass) return;
    try {
      const report = await this._hass.callWS({ type: `${DOMAIN}/migration_report` });
      const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      const stamp = new Date().toISOString().replace(/[:.]/g, "-");
      a.href = url;
      a.download = `eshtaya-smart-control-migration-${stamp}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1500);
    } catch (err) {
      this._error = err?.message || String(err);
      this._render();
    }
  }

  _wireChild() {
    const child = this.shadowRoot?.querySelector("eshtaya-entity-manager-panel,eshtaya-tuya-control,eshtaya-multiway-panel");
    if (child && this._hass) {
      child.hass = this._hass;
      try { child.language = this._lang; } catch (_) {}
    }
  }

  _click(event) {
    const target = event.target.closest("[data-view],[data-action]");
    if (!target) return;
    if (target.dataset.view) {
      this._view = target.dataset.view;
      this._render();
      window.scrollTo?.({ top: 0, behavior: "smooth" });
      return;
    }
    if (target.dataset.action === "refresh") this._load();
    if (target.dataset.action === "download-report") this._downloadReport();
  }

  _change(event) {
    if (!event.target.matches("[data-lang]")) return;
    this._langMode = event.target.value;
    localStorage.setItem("eshtayaSmartControlLang", this._langMode);
    this._render();
  }

  _esc(value) {
    return String(value ?? "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" })[ch]);
  }

  _css() {
    return `
      :host{display:block;width:100%;min-height:100%;color:var(--primary-text-color);background:var(--primary-background-color);font-family:var(--paper-font-body1_-_font-family,Roboto,Arial,sans-serif)}
      *{box-sizing:border-box}button,select{font:inherit}.shell{min-height:100vh;background:radial-gradient(900px 480px at 8% -10%,color-mix(in srgb,var(--primary-color) 18%,transparent),transparent 68%),var(--primary-background-color)}
      header{height:76px;padding:0 clamp(14px,2.5vw,36px);display:flex;align-items:center;justify-content:space-between;gap:18px;position:sticky;top:0;z-index:30;border-bottom:1px solid var(--divider-color);background:color-mix(in srgb,var(--card-background-color) 92%,transparent);backdrop-filter:blur(18px)}
      .brand{display:flex;align-items:center;gap:12px;background:none;border:0;color:inherit;cursor:pointer;text-align:inherit;min-width:0}.brandMark{width:44px;height:44px;border-radius:14px;display:grid;place-items:center;background:linear-gradient(145deg,color-mix(in srgb,var(--primary-color) 85%,white),var(--primary-color));box-shadow:0 10px 28px color-mix(in srgb,var(--primary-color) 28%,transparent);color:white;font-weight:900;letter-spacing:-1px}.brandText{display:grid;gap:3px}.brandText strong{font-size:16px}.brandText small{font-size:11px;color:var(--secondary-text-color);max-width:480px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.headerActions{display:flex;align-items:center;gap:8px}.version{padding:6px 9px;border-radius:999px;background:var(--secondary-background-color);color:var(--secondary-text-color);font-size:11px;font-weight:700}.headerActions select,.round{height:38px;border:1px solid var(--divider-color);background:var(--card-background-color);color:var(--primary-text-color);border-radius:11px}.headerActions select{padding:0 10px}.round{width:38px;cursor:pointer;font-size:19px}
      nav{display:flex;gap:6px;padding:10px clamp(12px,2.5vw,34px);position:sticky;top:76px;z-index:25;background:color-mix(in srgb,var(--primary-background-color) 94%,transparent);backdrop-filter:blur(14px);border-bottom:1px solid var(--divider-color);overflow:auto}nav button{display:flex;align-items:center;gap:7px;border:0;background:transparent;color:var(--secondary-text-color);padding:9px 12px;border-radius:10px;cursor:pointer;white-space:nowrap;font-size:12px;font-weight:700}nav button i{font-style:normal;width:22px;height:22px;border-radius:7px;display:grid;place-items:center;background:var(--secondary-background-color);font-size:11px}nav button.active{background:color-mix(in srgb,var(--primary-color) 12%,var(--card-background-color));color:var(--primary-color)}nav button.active i{background:var(--primary-color);color:white}
      main{width:min(1700px,100%);margin:0 auto;padding:clamp(16px,2.6vw,38px)}.errorBanner{padding:13px 16px;border:1px solid color-mix(in srgb,var(--error-color,#db4437) 40%,transparent);background:color-mix(in srgb,var(--error-color,#db4437) 10%,var(--card-background-color));border-radius:14px;margin-bottom:14px;color:var(--error-color,#db4437);font-size:13px}
      .hero{position:relative;overflow:hidden;border:1px solid var(--divider-color);border-radius:28px;padding:clamp(26px,5vw,62px);min-height:330px;background:linear-gradient(135deg,color-mix(in srgb,var(--card-background-color) 97%,var(--primary-color) 3%),var(--card-background-color));box-shadow:0 18px 60px rgba(0,0,0,.08);display:grid;grid-template-columns:minmax(0,1.3fr) minmax(360px,.7fr);align-items:end;gap:30px}.heroCopy{position:relative;z-index:2}.eyebrow{display:inline-block;font-size:10px;font-weight:900;letter-spacing:1.6px;color:var(--primary-color);text-transform:uppercase}.hero h1{font-size:clamp(38px,6vw,76px);letter-spacing:-3px;line-height:.98;margin:15px 0 14px;max-width:850px}.hero p{font-size:17px;color:var(--secondary-text-color);margin:0}.heroOrbs span{position:absolute;border-radius:999px;filter:blur(1px);opacity:.32}.heroOrbs span:nth-child(1){width:360px;height:360px;background:var(--primary-color);inset:-170px -80px auto auto}.heroOrbs span:nth-child(2){width:190px;height:190px;background:#7c4dff;inset:auto 18% -110px auto}.heroOrbs span:nth-child(3){width:90px;height:90px;background:#00bcd4;inset:35px 35% auto auto}.metrics{position:relative;z-index:2;display:grid;grid-template-columns:1fr 1fr;gap:10px}.metric{min-height:105px;padding:15px;border:1px solid color-mix(in srgb,var(--divider-color) 80%,transparent);border-radius:18px;background:color-mix(in srgb,var(--card-background-color) 78%,transparent);backdrop-filter:blur(14px);display:grid;grid-template-columns:auto 1fr;column-gap:10px;align-content:center}.metric>span{grid-row:1/3;width:34px;height:34px;border-radius:11px;display:grid;place-items:center;background:var(--secondary-background-color);font-size:11px;font-weight:900}.metric strong{font-size:23px}.metric small{color:var(--secondary-text-color);font-size:11px}
      .migrationBanner{margin-top:16px;padding:15px 18px;border-radius:18px;display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:13px;border:1px solid var(--divider-color);background:var(--card-background-color)}.migrationBanner.success{border-color:color-mix(in srgb,#31b46d 35%,var(--divider-color));background:color-mix(in srgb,#31b46d 7%,var(--card-background-color))}.migrationBanner.danger{border-color:color-mix(in srgb,var(--error-color,#db4437) 40%,var(--divider-color));background:color-mix(in srgb,var(--error-color,#db4437) 7%,var(--card-background-color))}.migrationBanner.active{border-color:color-mix(in srgb,var(--primary-color) 38%,var(--divider-color))}.migIcon{width:42px;height:42px;border-radius:14px;display:grid;place-items:center;background:var(--secondary-background-color);font-size:20px;font-weight:900}.migrationBanner div:nth-child(2){display:grid;gap:4px}.migrationBanner small{color:var(--secondary-text-color)}.migrationBanner button{border:0;border-radius:11px;padding:9px 12px;background:var(--primary-color);color:white;cursor:pointer;font-weight:800}
      .toolCards{display:grid;grid-template-columns:repeat(12,1fr);gap:14px;margin-top:18px}.toolCard{grid-column:span 4;min-height:255px;border:1px solid var(--divider-color);border-radius:22px;background:var(--card-background-color);padding:20px;position:relative;overflow:hidden;cursor:pointer;transition:.2s transform,.2s box-shadow}.toolCard:hover{transform:translateY(-2px);box-shadow:0 14px 38px rgba(0,0,0,.09)}.toolCard:nth-child(4),.toolCard:nth-child(5){grid-column:span 6}.toolCard:before{content:"";position:absolute;width:160px;height:160px;border-radius:999px;inset:-80px -50px auto auto;opacity:.12}.toolCard.purple:before{background:#7c4dff}.toolCard.blue:before{background:#2196f3}.toolCard.green:before{background:#31b46d}.toolCard.amber:before{background:#ff9800}.toolCard.slate:before{background:#607d8b}.toolIcon{width:48px;height:48px;border-radius:15px;display:grid;place-items:center;background:var(--secondary-background-color);font-weight:900;font-size:16px}.toolState{position:absolute;top:20px;inset-inline-end:20px;padding:6px 9px;border-radius:999px;background:var(--secondary-background-color);font-size:10px;font-weight:800;color:var(--secondary-text-color)}.toolCard h2{font-size:20px;margin:30px 0 8px}.toolCard p{margin:0;color:var(--secondary-text-color);font-size:13px;line-height:1.65;min-height:64px}.toolCard>button{margin-top:16px;border:0;background:transparent;color:var(--primary-color);padding:0;cursor:pointer;font-weight:900}.toolCard>button span{font-size:18px;margin-inline-start:4px}
      .toolTitle{display:flex;gap:15px;align-items:flex-start;margin-bottom:18px}.toolTitle .back{width:42px;height:42px;border-radius:13px;border:1px solid var(--divider-color);background:var(--card-background-color);color:var(--primary-text-color);cursor:pointer;font-size:20px}.toolTitle h1{font-size:clamp(26px,4vw,42px);margin:5px 0}.toolTitle p{margin:0;color:var(--secondary-text-color)}
      .docsGrid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}.docsGrid article{border:1px solid var(--divider-color);border-radius:20px;background:var(--card-background-color);padding:22px}.docNo{display:inline-grid;place-items:center;width:34px;height:34px;border-radius:11px;background:var(--secondary-background-color);font-size:11px;font-weight:900;color:var(--primary-color)}.docsGrid h2{font-size:18px;margin:18px 0 9px}.docsGrid p{color:var(--secondary-text-color);line-height:1.7;margin:0;font-size:13px}
      .systemTop{display:grid;grid-template-columns:1.15fr .85fr;gap:14px;margin-bottom:14px}.panelCard,.migrationCenter{border:1px solid var(--divider-color);border-radius:22px;background:var(--card-background-color);padding:20px}.panelHead{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:14px}.panelHead h2{margin:0;font-size:17px}.health{padding:5px 8px;border-radius:999px;font-size:10px;font-weight:900}.health.good{background:color-mix(in srgb,#31b46d 13%,transparent);color:#31b46d}.health.warn{background:color-mix(in srgb,#ff9800 14%,transparent);color:#ff9800}.moduleRow{display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:10px;padding:12px 0;border-top:1px solid var(--divider-color)}.moduleDot{width:9px;height:9px;border-radius:50%;background:var(--disabled-text-color)}.moduleDot.good{background:#31b46d;box-shadow:0 0 0 4px color-mix(in srgb,#31b46d 12%,transparent)}.moduleRow div{display:grid;gap:2px}.moduleRow small{font-size:10px;color:var(--secondary-text-color)}.paths{display:grid;gap:9px}.paths code,.kv code{padding:8px 10px;border-radius:10px;background:var(--secondary-background-color);font-size:11px;overflow:auto}
      .migrationCenter{padding:0;overflow:hidden}.migrationCenter.empty{padding:22px}.migrationHeader{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;padding:22px;border-bottom:1px solid var(--divider-color);background:linear-gradient(120deg,color-mix(in srgb,var(--primary-color) 6%,var(--card-background-color)),var(--card-background-color))}.migrationHeader h2{font-size:25px;margin:6px 0}.migrationHeader p{margin:0;color:var(--secondary-text-color);font-size:13px}.migrationActions{display:flex;align-items:center;gap:8px;flex-wrap:wrap;justify-content:flex-end}.migrationState{padding:7px 10px;border-radius:999px;background:var(--secondary-background-color);font-size:11px;font-weight:900}.primary{border:0;border-radius:11px;padding:9px 12px;background:var(--primary-color);color:white;cursor:pointer;font-weight:900;font-size:11px}.emptyState{display:grid;place-items:center;gap:10px;min-height:160px;text-align:center;color:var(--secondary-text-color)}.emptyState span{width:52px;height:52px;border-radius:17px;background:color-mix(in srgb,#31b46d 12%,transparent);color:#31b46d;display:grid;place-items:center;font-size:23px}.timeline{display:grid;grid-template-columns:repeat(9,minmax(130px,1fr));overflow:auto;padding:18px 18px 8px;gap:0}.step{min-width:130px;position:relative}.stepRail{height:34px;position:relative;display:flex;align-items:center}.stepRail:after{content:"";position:absolute;height:2px;background:var(--divider-color);inset-inline-start:30px;inset-inline-end:0;top:16px}.step:last-child .stepRail:after{display:none}.stepRail span{position:relative;z-index:2;width:32px;height:32px;border-radius:50%;display:grid;place-items:center;background:var(--secondary-background-color);border:2px solid var(--divider-color);font-size:10px;font-weight:900}.step.completed .stepRail span{background:#31b46d;color:white;border-color:#31b46d}.step.failed .stepRail span{background:var(--error-color,#db4437);color:white;border-color:var(--error-color,#db4437)}.step.running .stepRail span{border-color:var(--primary-color);color:var(--primary-color);box-shadow:0 0 0 4px color-mix(in srgb,var(--primary-color) 10%,transparent)}.step.rolled_back .stepRail span{background:#ff9800;color:white;border-color:#ff9800}.stepBody{padding:7px 10px 8px 0}.stepBody>div{display:grid;gap:3px}.stepBody strong{font-size:11px}.stepBody em{font-style:normal;font-size:9px;color:var(--secondary-text-color);text-transform:uppercase}.stepBody small{display:block;margin-top:5px;color:var(--secondary-text-color);font-size:9px;line-height:1.45;max-width:145px}
      .migrationGrid{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:18px}.migrationPanel{border:1px solid var(--divider-color);border-radius:16px;padding:16px;background:color-mix(in srgb,var(--secondary-background-color) 32%,var(--card-background-color))}.migrationPanel h3{font-size:14px;margin:0 0 13px}.compareRow{display:grid;grid-template-columns:minmax(150px,1fr) auto 20px auto 24px;align-items:center;gap:8px;padding:9px 0;border-top:1px solid var(--divider-color);font-size:11px}.compareRow>strong{font-size:11px}.compareRow span{color:var(--secondary-text-color)}.compareRow span b{color:var(--primary-text-color);font-size:14px;margin-inline-start:3px}.compareRow i{font-style:normal;color:var(--disabled-text-color)}.compareRow em{font-style:normal;width:22px;height:22px;border-radius:50%;display:grid;place-items:center;font-size:10px;font-weight:900}.compareRow em.ok{background:color-mix(in srgb,#31b46d 13%,transparent);color:#31b46d}.compareRow em.bad{background:color-mix(in srgb,var(--error-color,#db4437) 13%,transparent);color:var(--error-color,#db4437)}.kv,.hacsRow{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:9px 0;border-top:1px solid var(--divider-color);font-size:11px}.kv span,.hacsRow span{color:var(--secondary-text-color)}.hacsRow strong{font-size:10px}.ok{color:#31b46d}.bad{color:var(--error-color,#db4437)}.noErrors{color:#31b46d;font-weight:800;font-size:12px}.errors{padding-inline-start:18px;margin:0;color:var(--error-color,#db4437);font-size:11px;line-height:1.6}.subtle{color:var(--secondary-text-color)}
      @media(max-width:1050px){.hero{grid-template-columns:1fr}.toolCard{grid-column:span 6}.toolCard:nth-child(4),.toolCard:nth-child(5){grid-column:span 6}.systemTop,.migrationGrid{grid-template-columns:1fr}}
      @media(max-width:700px){header{height:66px}.brandText small,.version{display:none}nav{top:66px;padding-inline:8px}nav button span{display:none}nav button{padding:7px}.hero{min-height:0;padding:24px;border-radius:21px}.hero h1{font-size:38px;letter-spacing:-2px}.metrics{grid-template-columns:1fr 1fr}.toolCards{grid-template-columns:1fr}.toolCard,.toolCard:nth-child(4),.toolCard:nth-child(5){grid-column:auto}.migrationBanner{grid-template-columns:auto 1fr}.migrationBanner button{grid-column:1/-1}.docsGrid{grid-template-columns:1fr}.migrationHeader{display:grid}.migrationActions{justify-content:flex-start}.migrationGrid{padding:12px}.compareRow{grid-template-columns:1fr auto auto}.compareRow i,.compareRow em{display:none}.compareRow span{font-size:9px}.brandMark{width:40px;height:40px}.headerActions select{max-width:100px}main{padding:12px}}
    `;
  }
}

if (!customElements.get("eshtaya-smart-control-panel")) {
  customElements.define("eshtaya-smart-control-panel", EshtayaSmartControlPanel);
}
