const DOMAIN = "eshtaya_smart_control/entity";

const TEXT = {
  ar: {
    title: "إدارة الكيانات وأليكسا",
    subtitle: "إدارة أسماء كيانات Home Assistant وقواعد ظهورها على أليكسا من مكان واحد",
    entities: "الكيانات",
    devices: "الأجهزة",
    rules: "القواعد",
    file: "ملف أليكسا",
    total: "إجمالي الكيانات",
    included: "ظاهرة على أليكسا",
    excluded: "مخفية عن أليكسا",
    renamed: "أسماء مخصصة",
    search: "ابحث بالاسم أو معرّف الكيان أو الجهاز...",
    allDomains: "كل الأنواع",
    all: "الكل",
    onlyIncluded: "المرحّلة فقط",
    onlyExcluded: "المخفية فقط",
    overrides: "التعديلات فقط",
    state: "الحالة",
    source: "المصدر",
    alexa: "أليكسا",
    rename: "تغيير الاسم",
    save: "حفظ",
    reset: "إرجاع",
    inherit: "تلقائي",
    allow: "ترحيل إجباري",
    exclude: "إخفاء إجباري",
    reason: "السبب",
    unavailable: "غير متوفر",
    noDevice: "بدون جهاز",
    noArea: "بدون منطقة",
    entitiesCount: "كيان",
    bulk: "تعديل جماعي",
    refresh: "تحديث",
    domainRules: "قواعد الأنواع",
    domainRulesDesc: "إيقاف نوع يخفي كل كياناته عن أليكسا إلا إذا تم فرض إظهار كيان محدد.",
    autoRules: "الاستثناء التلقائي",
    autoRulesDesc: "تُطبق فقط على الكيانات التي تستخدم الوضع التلقائي.",
    categories: "تصنيفات الكيانات المستثناة",
    categoriesHint: "مثال: تشخيص أو إعدادات (diagnostic, config)",
    keywords: "الكلمات المستثناة",
    keywordsHint: "تُفحص داخل الاسم ومعرّف الكيان. افصل بينها بفاصلة.",
    saveRules: "حفظ القواعد",
    enabled: "مسموح",
    disabled: "مخفي",
    yamlTitle: "hidden_entities.yaml",
    yamlDesc: "هذا الملف يتم توليده تلقائيًا. أي تعديل يدوي عليه قد يُستبدل عند الحفظ من اللوحة.",
    regenerate: "إعادة توليد الملف",
    copy: "نسخ المحتوى",
    path: "المسار",
    backup: "نسخة الاستيراد الاحتياطية",
    bulkTitle: "تعديل جماعي لحالة الترحيل",
    keyword: "الكلمة المفتاحية",
    where: "مكان البحث",
    nameOnly: "الاسم فقط",
    idOnly: "معرّف الكيان فقط",
    both: "الاسم + معرّف الكيان",
    mode: "الحالة الجديدة",
    currentDomain: "ضمن النوع المحدد حاليًا",
    allDomainsBulk: "كل الأنواع",
    apply: "تطبيق",
    cancel: "إلغاء",
    loading: "جاري التحميل...",
    noResults: "لا توجد كيانات مطابقة للفلاتر الحالية.",
    renameSaved: "تم تغيير الاسم",
    renameReset: "تم إرجاع الاسم للاسم الأصلي",
    ruleSaved: "تم تحديث حالة أليكسا وملف YAML",
    rulesSaved: "تم حفظ القواعد وإعادة توليد الملف",
    regenerated: "تم إعادة توليد hidden_entities.yaml",
    bulkDone: "تم تعديل {count} كيان",
    copied: "تم نسخ الملف",
    error: "حدث خطأ",
    registryOnly: "هذا الكيان غير موجود في Entity Registry ولا يمكن تغيير اسمه من هنا.",
    customName: "اسم مخصص",
    originalName: "الاسم الأصلي",
    domain: "النوع",
    area: "المنطقة",
    device: "الجهاز",
    openEntity: "فتح تفاصيل الكيان",
    hide: "إخفاء",
    show: "إظهار",
    auto: "تلقائي",
    close: "إغلاق",
    fileMissing: "الملف غير موجود بعد.",
    panelHelp: "غيّر الاسم أو حالة Alexa مباشرة؛ لا يوجد زر حفظ عام للكيانات.",
  },
  en: {
    title: "Entity Manager",
    subtitle: "Manage Home Assistant names and Alexa exclusions in one place",
    entities: "Entities",
    devices: "Devices",
    rules: "Rules",
    file: "Alexa file",
    total: "Total entities",
    included: "Exposed to Alexa",
    excluded: "Hidden from Alexa",
    renamed: "Custom names",
    search: "Search name, entity ID or device...",
    allDomains: "All domains",
    all: "All",
    onlyIncluded: "Included only",
    onlyExcluded: "Excluded only",
    overrides: "Overrides only",
    state: "State",
    source: "Source",
    alexa: "أليكسا",
    rename: "Rename",
    save: "Save",
    reset: "Reset",
    inherit: "Automatic",
    allow: "Force allow",
    exclude: "Force exclude",
    reason: "Reason",
    unavailable: "Unavailable",
    noDevice: "No device",
    noArea: "No area",
    entitiesCount: "entities",
    bulk: "Bulk edit",
    refresh: "Refresh",
    domainRules: "Domain rules",
    domainRulesDesc: "Disabling a domain excludes its entities unless an entity is Force Allowed.",
    autoRules: "Automatic exclusions",
    autoRulesDesc: "Applied only to entities using Inherit.",
    categories: "Excluded entity categories",
    categoriesHint: "Example: diagnostic, config",
    keywords: "Excluded keywords",
    keywordsHint: "Matched against display name and Entity ID. Separate with commas.",
    saveRules: "Save rules",
    enabled: "Allowed",
    disabled: "Excluded",
    yamlTitle: "hidden_entities.yaml",
    yamlDesc: "This file is generated automatically. Manual edits may be overwritten by the panel.",
    regenerate: "Regenerate file",
    copy: "Copy content",
    path: "Path",
    backup: "Imported-file backup",
    bulkTitle: "Bulk Alexa visibility edit",
    keyword: "Keyword",
    where: "Search in",
    nameOnly: "Name only",
    idOnly: "Entity ID only",
    both: "Name + Entity ID",
    mode: "New rule",
    currentDomain: "Current selected domain",
    allDomainsBulk: "All domains",
    apply: "Apply",
    cancel: "Cancel",
    loading: "Loading...",
    noResults: "No entities match the current filters.",
    renameSaved: "Entity name updated",
    renameReset: "Entity name reset",
    ruleSaved: "Alexa rule and YAML file updated",
    rulesSaved: "Rules saved and YAML regenerated",
    regenerated: "hidden_entities.yaml regenerated",
    bulkDone: "Updated {count} entities",
    copied: "File copied",
    error: "Error",
    registryOnly: "This entity is not in the Entity Registry and cannot be renamed here.",
    customName: "Custom name",
    originalName: "Original name",
    domain: "Domain",
    area: "Area",
    device: "Device",
    openEntity: "Open entity details",
    hide: "Hide",
    show: "Show",
    auto: "Auto",
    close: "Close",
    fileMissing: "The file does not exist yet.",
    panelHelp: "Names and Alexa rules save immediately; there is no global entity save button.",
  },
};

class EshtayaEntityManagerPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._data = null;
    this._loading = false;
    this._loaded = false;
    this._tab = "entities";
    this._search = "";
    this._status = "all";
    this._domain = "__all";
    this._bulkOpen = false;
    this._toastTimer = null;
  }

  set hass(value) {
    const first = !this._hass;
    this._hass = value;
    if (first && !this._loaded) this._load(false);
  }

  get hass() {
    return this._hass;
  }

  set panel(value) {
    this._panel = value;
  }

  connectedCallback() {
    this._render();
    this.shadowRoot.addEventListener("click", (ev) => this._onClick(ev));
    this.shadowRoot.addEventListener("change", (ev) => this._onChange(ev));
    this.shadowRoot.addEventListener("input", (ev) => this._onInput(ev));
  }

  _lang() {
    const language = window.__ESHTAYA_SMART_LANG__ || this._hass?.locale?.language || this._hass?.language || "en";
    return String(language).toLowerCase().startsWith("ar") ? "ar" : "en";
  }

  _t(key, vars = {}) {
    let value = TEXT[this._lang()][key] || TEXT.en[key] || key;
    Object.entries(vars).forEach(([k, v]) => {
      value = value.replace(`{${k}}`, String(v));
    });
    return value;
  }

  _esc(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  async _load(includeFile = false) {
    if (!this._hass || this._loading) return;
    this._loading = true;
    this._render();
    try {
      this._data = await this._hass.callWS({
        type: `${DOMAIN}/get`,
        include_file: includeFile,
      });
      this._loaded = true;
    } catch (err) {
      const message = this._errorText(err);
      this._loading = false;
      this._render();
      this._toast(message, true);
      return;
    } finally {
      if (this._loading) {
        this._loading = false;
        this._render();
      }
    }
  }

  _errorText(err) {
    return err?.message || err?.body?.message || String(err || this._t("error"));
  }

  _toast(message, error = false) {
    clearTimeout(this._toastTimer);
    let node = this.shadowRoot?.querySelector(".toast");
    if (!node) return;
    node.textContent = message;
    node.className = `toast show ${error ? "error" : "ok"}`;
    this._toastTimer = setTimeout(() => {
      node.className = "toast";
    }, 3200);
  }

  _filteredEntities() {
    if (!this._data?.entities) return [];
    const term = this._search.trim().toLocaleLowerCase();
    return this._data.entities.filter((entity) => {
      if (this._domain !== "__all" && entity.domain !== this._domain) return false;
      if (this._status === "included" && entity.excluded) return false;
      if (this._status === "excluded" && !entity.excluded) return false;
      if (this._status === "overrides" && entity.rule === "inherit") return false;
      if (!term) return true;
      const haystack = `${entity.entity_id} ${entity.name || ""} ${entity.device_name || ""} ${entity.area_name || ""}`.toLocaleLowerCase();
      return haystack.includes(term);
    });
  }

  _render() {
    if (!this.shadowRoot) return;
    const rtl = this._lang() === "ar";
    const data = this._data;
    const stats = data?.stats || { total: 0, included: 0, excluded: 0, renamed: 0 };

    this.shadowRoot.innerHTML = `
      <style>${this._styles()}</style>
      <div class="app" dir="${rtl ? "rtl" : "ltr"}">
        <header class="hero">
          <div class="heroText">
            <div class="eyebrow">ESHTAYA SMART · HOME ASSISTANT</div>
            <h1>${this._t("title")}</h1>
            <p>${this._t("subtitle")}</p>
          </div>
          <div class="heroActions">
            <button class="btn ghost" data-action="refresh">↻ ${this._t("refresh")}</button>
            <button class="btn primary" data-action="bulk">⚡ ${this._t("bulk")}</button>
          </div>
        </header>

        <section class="stats">
          ${this._statCard("◫", this._t("total"), stats.total)}
          ${this._statCard("✓", this._t("included"), stats.included, "good")}
          ${this._statCard("⊘", this._t("excluded"), stats.excluded, "bad")}
          ${this._statCard("Aa", this._t("renamed"), stats.renamed, "accent")}
        </section>

        <nav class="tabs">
          ${this._tabButton("entities", "☷", this._t("entities"))}
          ${this._tabButton("devices", "▦", this._t("devices"))}
          ${this._tabButton("rules", "⚙", this._t("rules"))}
          ${this._tabButton("file", "YAML", this._t("file"))}
        </nav>

        <main>
          ${!data ? this._emptyLoading() : this._renderTab()}
        </main>

        ${this._renderBulkModal()}
        <div class="toast"></div>
        ${this._loading ? `<div class="busy"><div class="spinner"></div><span>${this._t("loading")}</span></div>` : ""}
      </div>
    `;
  }

  _styles() {
    return `
      :host{display:block;width:100%;min-height:100%;box-sizing:border-box;color:var(--primary-text-color);background:var(--primary-background-color)}
      *{box-sizing:border-box}
      .app{width:100%;min-height:100vh;padding:24px clamp(14px,2.6vw,38px) 48px;background:
        radial-gradient(circle at 10% 0%, color-mix(in srgb,var(--primary-color) 12%,transparent), transparent 32%),
        var(--primary-background-color);font-family:var(--paper-font-body1_-_font-family,Roboto,Arial,sans-serif)}
      .hero{display:flex;justify-content:space-between;align-items:flex-end;gap:18px;margin:0 auto 20px;max-width:1800px}
      .eyebrow{font-size:11px;letter-spacing:.14em;color:var(--secondary-text-color);font-weight:700;margin-bottom:8px}
      h1{margin:0;font-size:clamp(27px,3vw,42px);line-height:1.1;letter-spacing:-.02em}
      .hero p{margin:8px 0 0;color:var(--secondary-text-color);font-size:14px}
      .heroActions{display:flex;gap:8px;flex-wrap:wrap}
      .btn{border:1px solid var(--divider-color);background:var(--card-background-color);color:var(--primary-text-color);padding:10px 14px;border-radius:12px;cursor:pointer;font-weight:600;transition:.16s ease;box-shadow:none}
      .btn:hover{transform:translateY(-1px);border-color:color-mix(in srgb,var(--primary-color) 55%,var(--divider-color))}
      .btn:disabled{opacity:.5;cursor:not-allowed;transform:none}
      .btn.primary{background:var(--primary-color);color:var(--text-primary-color,#fff);border-color:var(--primary-color)}
      .btn.danger{background:color-mix(in srgb,var(--error-color,#db4437) 12%,var(--card-background-color));color:var(--error-color,#db4437)}
      .btn.small{padding:8px 10px;border-radius:10px;font-size:12px}
      .stats{max-width:1800px;margin:0 auto 18px;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
      .stat{background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:17px;padding:16px;display:flex;align-items:center;gap:12px;min-height:82px;box-shadow:var(--ha-card-box-shadow,none)}
      .statIcon{width:42px;height:42px;border-radius:12px;background:color-mix(in srgb,var(--secondary-background-color) 85%,var(--primary-color) 15%);display:grid;place-items:center;font-weight:800;color:var(--primary-color)}
      .stat.good .statIcon{color:var(--success-color,#2e7d32)} .stat.bad .statIcon{color:var(--error-color,#db4437)}
      .statLabel{font-size:12px;color:var(--secondary-text-color);margin-bottom:4px}.statValue{font-size:24px;font-weight:800;line-height:1}
      .tabs{max-width:1800px;margin:0 auto 14px;display:flex;gap:6px;padding:5px;background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:15px;overflow:auto;position:sticky;top:8px;z-index:5;box-shadow:var(--ha-card-box-shadow,none)}
      .tab{border:0;background:transparent;color:var(--secondary-text-color);padding:10px 15px;border-radius:11px;cursor:pointer;font-weight:700;white-space:nowrap}
      .tab.active{background:color-mix(in srgb,var(--primary-color) 14%,var(--card-background-color));color:var(--primary-color)}
      main{max-width:1800px;margin:0 auto}
      .toolbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:12px}
      .searchWrap{flex:1;min-width:240px;position:relative}.search{width:100%;padding:12px 14px;border:1px solid var(--divider-color);border-radius:13px;background:var(--card-background-color);color:var(--primary-text-color);outline:none}
      .search:focus,.select:focus,.renameInput:focus,.textInput:focus{border-color:var(--primary-color);box-shadow:0 0 0 2px color-mix(in srgb,var(--primary-color) 16%,transparent)}
      .select,.textInput{padding:11px 12px;border:1px solid var(--divider-color);border-radius:12px;background:var(--card-background-color);color:var(--primary-text-color);outline:none}
      .domainScroller{display:flex;gap:7px;overflow:auto;padding:2px 0 10px;margin-bottom:4px;scrollbar-width:thin}
      .chip{border:1px solid var(--divider-color);background:var(--card-background-color);color:var(--secondary-text-color);border-radius:999px;padding:7px 11px;white-space:nowrap;cursor:pointer;font-size:12px;font-weight:700}
      .chip.active{background:color-mix(in srgb,var(--primary-color) 14%,var(--card-background-color));border-color:color-mix(in srgb,var(--primary-color) 48%,var(--divider-color));color:var(--primary-color)}
      .help{font-size:12px;color:var(--secondary-text-color);margin:0 0 12px}
      .list{display:flex;flex-direction:column;gap:8px}
      .entityRow{display:grid;grid-template-columns:minmax(220px,1.45fr) minmax(120px,.65fr) minmax(180px,.9fr) minmax(300px,1.25fr);gap:12px;align-items:center;padding:12px;background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:15px;box-shadow:var(--ha-card-box-shadow,none)}
      .entityMain{min-width:0;display:flex;align-items:center;gap:11px}.statusDot{width:11px;height:11px;border-radius:50%;flex:0 0 auto}.statusDot.included{background:var(--success-color,#2e7d32);box-shadow:0 0 0 4px color-mix(in srgb,var(--success-color,#2e7d32) 14%,transparent)}.statusDot.excluded{background:var(--error-color,#db4437);box-shadow:0 0 0 4px color-mix(in srgb,var(--error-color,#db4437) 13%,transparent)}
      .name{font-size:14px;font-weight:800;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.eid{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:11px;color:var(--secondary-text-color);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin-top:3px}
      .meta{font-size:12px;color:var(--secondary-text-color);display:flex;flex-direction:column;gap:4px;min-width:0}.metaLine{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
      .ruleWrap{display:flex;flex-direction:column;gap:5px}.ruleSelect{width:100%;padding:9px 10px;border:1px solid var(--divider-color);border-radius:11px;background:var(--secondary-background-color);color:var(--primary-text-color);font-weight:700}.reason{font-size:10.5px;color:var(--secondary-text-color);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
      .renameWrap{display:grid;grid-template-columns:minmax(120px,1fr) auto auto;gap:6px}.renameInput{min-width:0;width:100%;padding:9px 10px;border:1px solid var(--divider-color);border-radius:11px;background:var(--secondary-background-color);color:var(--primary-text-color);outline:none}
      .iconBtn{width:37px;height:37px;border:1px solid var(--divider-color);border-radius:10px;background:var(--secondary-background-color);color:var(--primary-text-color);cursor:pointer;font-weight:800}.iconBtn:hover{border-color:var(--primary-color);color:var(--primary-color)}
      .badge{display:inline-flex;align-items:center;width:max-content;max-width:100%;padding:4px 8px;border:1px solid var(--divider-color);border-radius:999px;font-size:10.5px;color:var(--secondary-text-color)}
      .empty{padding:48px 16px;text-align:center;background:var(--card-background-color);border:1px dashed var(--divider-color);border-radius:16px;color:var(--secondary-text-color)}
      .deviceGrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:12px}.deviceCard{background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:16px;padding:14px;min-width:0}.deviceHead{display:flex;justify-content:space-between;gap:8px;align-items:start;margin-bottom:10px}.deviceTitle{font-weight:800}.deviceArea{font-size:11px;color:var(--secondary-text-color);margin-top:3px}.miniEntity{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;align-items:center;padding:9px 0;border-top:1px solid var(--divider-color)}.miniEntity:first-of-type{border-top:0}.miniRight{display:flex;align-items:center;gap:7px}
      .sectionCard{background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:17px;padding:17px;margin-bottom:12px}.sectionTitle{font-size:17px;font-weight:800;margin-bottom:5px}.sectionDesc{color:var(--secondary-text-color);font-size:12px;margin-bottom:15px}.domainGrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px}.domainRule{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:10px;border:1px solid var(--divider-color);border-radius:12px;background:var(--secondary-background-color)}.domainName{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:12px;font-weight:700}.domainStats{font-size:10.5px;color:var(--secondary-text-color);margin-top:3px}
      .switch{position:relative;width:42px;height:24px;display:inline-block;flex:0 0 auto}.switch input{display:none}.slider{position:absolute;inset:0;border-radius:999px;background:var(--disabled-text-color);cursor:pointer;transition:.2s}.slider:before{content:"";position:absolute;width:18px;height:18px;left:3px;top:3px;border-radius:50%;background:white;transition:.2s}.switch input:checked + .slider{background:var(--primary-color)}.switch input:checked + .slider:before{transform:translateX(18px)}[dir="rtl"] .switch input:checked + .slider:before{transform:translateX(-18px)}
      .formGrid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.field label{display:block;font-size:12px;font-weight:700;margin-bottom:6px}.field .textInput{width:100%}.fieldHint{font-size:10.5px;color:var(--secondary-text-color);margin-top:5px}
      .yamlMeta{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px}.metaBox{padding:10px;border:1px solid var(--divider-color);background:var(--secondary-background-color);border-radius:12px;min-width:0}.metaBox .label{font-size:10px;color:var(--secondary-text-color);margin-bottom:4px}.metaBox code{font-size:11px;word-break:break-all}.yamlBox{margin:0;padding:14px;min-height:300px;max-height:60vh;overflow:auto;background:var(--code-editor-background-color,#111827);color:var(--code-editor-text-color,#e5e7eb);border-radius:13px;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:12px;line-height:1.55;direction:ltr;text-align:left;border:1px solid var(--divider-color)}
      .modalBackdrop{position:fixed;inset:0;background:rgba(0,0,0,.52);display:grid;place-items:center;padding:18px;z-index:50}.modal{width:min(560px,100%);background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:18px;padding:18px;box-shadow:0 18px 60px rgba(0,0,0,.28)}.modalHead{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:14px}.modalTitle{font-weight:800;font-size:18px}.modal .field{margin-bottom:12px}.modalActions{display:flex;justify-content:flex-end;gap:8px;margin-top:16px}
      .toast{position:fixed;inset-inline-end:22px;bottom:24px;transform:translateY(20px);opacity:0;pointer-events:none;background:var(--card-background-color);border:1px solid var(--divider-color);padding:11px 14px;border-radius:12px;box-shadow:0 10px 34px rgba(0,0,0,.2);z-index:70;font-size:13px;transition:.2s}.toast.show{opacity:1;transform:translateY(0)}.toast.ok{border-color:color-mix(in srgb,var(--success-color,#2e7d32) 45%,var(--divider-color))}.toast.error{border-color:color-mix(in srgb,var(--error-color,#db4437) 55%,var(--divider-color));color:var(--error-color,#db4437)}
      .busy{position:fixed;inset:0;background:rgba(0,0,0,.18);display:flex;align-items:center;justify-content:center;gap:10px;z-index:60;color:white;font-weight:700}.spinner{width:24px;height:24px;border-radius:50%;border:3px solid rgba(255,255,255,.35);border-top-color:white;animation:spin .7s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}
      @media(max-width:1100px){.entityRow{grid-template-columns:minmax(220px,1.2fr) minmax(160px,.8fr) minmax(280px,1fr)}.entityRow>.meta:nth-child(2){display:none}}
      @media(max-width:800px){.app{padding:14px 10px 34px}.hero{align-items:flex-start;flex-direction:column}.stats{grid-template-columns:1fr 1fr}.entityRow{grid-template-columns:1fr;gap:9px}.entityRow>.meta:nth-child(2){display:flex}.renameWrap{grid-template-columns:1fr auto auto}.deviceGrid{grid-template-columns:1fr}.formGrid,.yamlMeta{grid-template-columns:1fr}.tabs{top:4px}.stat{min-height:70px;padding:12px}.statValue{font-size:20px}}
      @media(max-width:430px){.stats{grid-template-columns:1fr}.heroActions{width:100%}.heroActions .btn{flex:1}.toolbar>.select{width:100%}.renameWrap{grid-template-columns:1fr 1fr}.renameWrap .renameInput{grid-column:1/-1}}
    `;
  }

  _statCard(icon, label, value, cls = "") {
    return `<div class="stat ${cls}"><div class="statIcon">${icon}</div><div><div class="statLabel">${this._esc(label)}</div><div class="statValue">${Number(value || 0).toLocaleString()}</div></div></div>`;
  }

  _tabButton(tab, icon, label) {
    return `<button class="tab ${this._tab === tab ? "active" : ""}" data-tab="${tab}"><span>${icon}</span>&nbsp; ${this._esc(label)}</button>`;
  }

  _emptyLoading() {
    return `<div class="empty">${this._t("loading")}</div>`;
  }

  _renderTab() {
    if (this._tab === "devices") return this._renderDevices();
    if (this._tab === "rules") return this._renderRules();
    if (this._tab === "file") return this._renderFile();
    return this._renderEntities();
  }

  _renderToolbar() {
    const domains = this._data?.domains || [];
    return `
      <div class="toolbar">
        <div class="searchWrap"><input class="search" data-role="search" value="${this._esc(this._search)}" placeholder="${this._esc(this._t("search"))}"></div>
        <select class="select" data-role="status">
          ${this._option("all", this._t("all"), this._status)}
          ${this._option("included", this._t("onlyIncluded"), this._status)}
          ${this._option("excluded", this._t("onlyExcluded"), this._status)}
          ${this._option("overrides", this._t("overrides"), this._status)}
        </select>
      </div>
      <div class="domainScroller">
        <button class="chip ${this._domain === "__all" ? "active" : ""}" data-domain-filter="__all">${this._t("allDomains")} · ${this._data?.stats?.total || 0}</button>
        ${domains.map((d) => `<button class="chip ${this._domain === d.domain ? "active" : ""}" data-domain-filter="${this._esc(d.domain)}">${this._esc(d.domain)} · ${d.count}</button>`).join("")}
      </div>
      <p class="help">${this._t("panelHelp")}</p>
    `;
  }

  _renderEntities() {
    const entities = this._filteredEntities();
    return `
      ${this._renderToolbar()}
      <div class="list">
        ${entities.length ? entities.map((e) => this._entityRow(e)).join("") : `<div class="empty">${this._t("noResults")}</div>`}
      </div>
    `;
  }

  _entityRow(entity) {
    const alexaClass = entity.excluded ? "excluded" : "included";
    const device = entity.device_name || this._t("noDevice");
    const area = entity.area_name || this._t("noArea");
    const platform = entity.platform || "—";
    return `
      <div class="entityRow" data-eid="${this._esc(entity.entity_id)}">
        <div class="entityMain">
          <span class="statusDot ${alexaClass}" title="${this._esc(entity.reason)}"></span>
          <div style="min-width:0;flex:1">
            <div class="name" title="${this._esc(entity.name)}">${this._esc(entity.name)}</div>
            <div class="eid" title="${this._esc(entity.entity_id)}">${this._esc(entity.entity_id)}</div>
          </div>
          <button class="iconBtn" data-action="more-info" data-eid="${this._esc(entity.entity_id)}" title="${this._esc(this._t("openEntity"))}">↗</button>
        </div>
        <div class="meta">
          <div class="metaLine">${this._t("device")}: <b>${this._esc(device)}</b></div>
          <div class="metaLine">${this._t("area")}: ${this._esc(area)}</div>
          <div class="metaLine">${this._t("source")}: ${this._esc(platform)}</div>
        </div>
        <div class="ruleWrap">
          <select class="ruleSelect" data-rule-eid="${this._esc(entity.entity_id)}">
            ${this._option("inherit", `◌ ${this._t("inherit")}`, entity.rule)}
            ${this._option("allow", `✓ ${this._t("allow")}`, entity.rule)}
            ${this._option("exclude", `⊘ ${this._t("exclude")}`, entity.rule)}
          </select>
          <div class="reason" title="${this._esc(entity.reason)}">${this._t("reason")}: ${this._esc(entity.reason)}</div>
        </div>
        <div>
          <div class="renameWrap">
            <input class="renameInput" data-rename-eid="${this._esc(entity.entity_id)}" value="${this._esc(entity.name)}" ${entity.can_rename ? "" : "disabled"} title="${entity.can_rename ? "" : this._esc(this._t("registryOnly"))}">
            <button class="iconBtn" data-action="rename-save" data-eid="${this._esc(entity.entity_id)}" ${entity.can_rename ? "" : "disabled"} title="${this._esc(this._t("save"))}">✓</button>
            <button class="iconBtn" data-action="rename-reset" data-eid="${this._esc(entity.entity_id)}" ${entity.can_rename ? "" : "disabled"} title="${this._esc(this._t("reset"))}">↺</button>
          </div>
          ${entity.registry_name !== null && entity.registry_name !== undefined ? `<div style="margin-top:6px"><span class="badge">${this._t("customName")}: ${this._esc(entity.registry_name)}</span></div>` : ""}
        </div>
      </div>
    `;
  }

  _option(value, label, current) {
    return `<option value="${this._esc(value)}" ${String(value) === String(current) ? "selected" : ""}>${this._esc(label)}</option>`;
  }

  _renderDevices() {
    const entities = this._filteredEntities();
    const groups = new Map();
    for (const entity of entities) {
      const key = entity.device_id || `__${entity.area_name || "none"}__${entity.domain}`;
      if (!groups.has(key)) groups.set(key, { name: entity.device_name || this._t("noDevice"), area: entity.area_name || this._t("noArea"), entities: [] });
      groups.get(key).entities.push(entity);
    }
    const sorted = [...groups.values()].sort((a, b) => a.name.localeCompare(b.name));
    return `
      ${this._renderToolbar()}
      <div class="deviceGrid">
        ${sorted.length ? sorted.map((g) => `
          <section class="deviceCard">
            <div class="deviceHead"><div><div class="deviceTitle">${this._esc(g.name)}</div><div class="deviceArea">${this._esc(g.area)}</div></div><span class="badge">${g.entities.length} ${this._t("entitiesCount")}</span></div>
            ${g.entities.map((e) => `<div class="miniEntity"><div style="min-width:0"><div class="name">${this._esc(e.name)}</div><div class="eid">${this._esc(e.entity_id)}</div></div><div class="miniRight"><span class="statusDot ${e.excluded ? "excluded" : "included"}"></span><select class="ruleSelect" data-rule-eid="${this._esc(e.entity_id)}">${this._option("inherit", this._t("auto"), e.rule)}${this._option("allow", this._t("show"), e.rule)}${this._option("exclude", this._t("hide"), e.rule)}</select></div></div>`).join("")}
          </section>`).join("") : `<div class="empty">${this._t("noResults")}</div>`}
      </div>
    `;
  }

  _renderRules() {
    const settings = this._data.settings || {};
    const domains = this._data.domains || [];
    return `
      <section class="sectionCard">
        <div class="sectionTitle">${this._t("domainRules")}</div>
        <div class="sectionDesc">${this._t("domainRulesDesc")}</div>
        <div class="domainGrid">
          ${domains.map((d) => `<div class="domainRule"><div><div class="domainName">${this._esc(d.domain)}</div><div class="domainStats">${d.count} ${this._t("entitiesCount")} · ${d.excluded} ${this._t("excluded")}</div></div><label class="switch"><input type="checkbox" data-domain-toggle="${this._esc(d.domain)}" ${d.enabled ? "checked" : ""}><span class="slider"></span></label></div>`).join("")}
        </div>
      </section>
      <section class="sectionCard">
        <div class="sectionTitle">${this._t("autoRules")}</div>
        <div class="sectionDesc">${this._t("autoRulesDesc")}</div>
        <div class="formGrid">
          <div class="field"><label>${this._t("categories")}</label><input class="textInput" data-setting="categories" value="${this._esc((settings.exclude_entity_category || []).join(", "))}"><div class="fieldHint">${this._t("categoriesHint")}</div></div>
          <div class="field"><label>${this._t("keywords")}</label><input class="textInput" data-setting="keywords" value="${this._esc((settings.exclude_name_keywords || []).join(", "))}"><div class="fieldHint">${this._t("keywordsHint")}</div></div>
        </div>
        <div style="margin-top:14px"><button class="btn primary" data-action="save-defaults">${this._t("saveRules")}</button></div>
      </section>
    `;
  }

  _renderFile() {
    const file = this._data.file || {};
    const content = file.content;
    return `
      <section class="sectionCard">
        <div class="deviceHead">
          <div><div class="sectionTitle">${this._t("yamlTitle")}</div><div class="sectionDesc">${this._t("yamlDesc")}</div></div>
          <div class="heroActions"><button class="btn ghost" data-action="copy-file">${this._t("copy")}</button><button class="btn primary" data-action="regenerate">${this._t("regenerate")}</button></div>
        </div>
        <div class="yamlMeta">
          <div class="metaBox"><div class="label">${this._t("path")}</div><code>${this._esc(file.path || "")}</code></div>
          <div class="metaBox"><div class="label">${this._t("backup")}</div><code>${this._esc(file.backup_path || "")}</code></div>
        </div>
        ${content === undefined ? `<div class="empty"><button class="btn primary" data-action="load-file">${this._t("file")}</button></div>` : `<pre class="yamlBox">${this._esc(content || this._t("fileMissing"))}</pre>`}
      </section>
    `;
  }

  _renderBulkModal() {
    if (!this._bulkOpen) return "";
    const domains = this._data?.domains || [];
    return `
      <div class="modalBackdrop" data-action="bulk-backdrop">
        <div class="modal" role="dialog" aria-modal="true">
          <div class="modalHead"><div class="modalTitle">${this._t("bulkTitle")}</div><button class="iconBtn" data-action="bulk-close">×</button></div>
          <div class="field"><label>${this._t("keyword")}</label><input class="textInput" style="width:100%" data-bulk="keyword" autofocus></div>
          <div class="field"><label>${this._t("where")}</label><select class="select" style="width:100%" data-bulk="where">${this._option("name", this._t("nameOnly"), "both")}${this._option("id", this._t("idOnly"), "both")}${this._option("both", this._t("both"), "both")}</select></div>
          <div class="field"><label>${this._t("mode")}</label><select class="select" style="width:100%" data-bulk="mode">${this._option("llow", this._t("allow"), "exclude")}${this._option("exclude", this._t("exclude"), "exclude")}${this._option("inherit", this._t("inherit"), "exclude")}</select></div>
          <div class="field"><label>${this._t("domain")}</label><select class="select" style="width:100%" data-bulk="domain"><option value="">${this._t("allDomainsBulk")}</option>${domains.map((d) => `<option value="${this._esc(d.domain)}" ${this._domain === d.domain ? "selected" : ""}>${this._esc(d.domain)}</option>`).join("")}</select></div>
          <div class="modalActions"><button class="btn ghost" data-action="bulk-close">${this._t("cancel")}</button><button class="btn primary" data-action="bulk-apply">${this._t("apply")}</button></div>
        </div>
      </div>`;
  }

  async _onClick(ev) {
    const target = ev.target.closest("[data-action],[data-tab],[data-domain-filter]");
    if (!target) return;

    if (target.dataset.tab) {
      this._tab = target.dataset.tab;
      if (this._tab === "file" && this._data?.file?.content === undefined) await this._load(true);
      else this._render();
      return;
    }

    if (target.dataset.domainFilter !== undefined) {
      this._domain = target.dataset.domainFilter;
      this._render();
      return;
    }

    const action = target.dataset.action;
    if (action === "refresh") return this._load(this._tab === "file");
    if (action === "bulk") { this._bulkOpen = true; this._render(); return; }
    if (action === "bulk-close") { this._bulkOpen = false; this._render(); return; }
    if (action === "bulk-backdrop" && ev.target === target) { this._bulkOpen = false; this._render(); return; }
    if (action === "more-info") return this._openMoreInfo(target.dataset.eid);
    if (action === "rename-save") return this._rename(target.dataset.eid, false);
    if (action === "rename-reset") return this._rename(target.dataset.eid, true);
    if (action === "save-defaults") return this._saveDefaults();
    if (action === "regenerate") return this._regenerate();
    if (action === "load-file") return this._load(true);
    if (action === "copy-file") return this._copyFile();
    if (action === "bulk-apply") return this._bulkApply();
  }

  async _onChange(ev) {
    const target = ev.target;
    if (target.matches("[data-role='status']")) {
      this._status = target.value;
      this._render();
      return;
    }
    if (target.matches("[data-rule-eid]")) {
      await this._callAndReload({ type: `${DOMAIN}/set_entity_rule`, entity_id: target.dataset.ruleEid, mode: target.value }, this._t("ruleSaved"));
      return;
    }
    if (target.matches("[data-domain-toggle]")) {
      await this._callAndReload({ type: `${DOMAIN}/set_domain`, domain: target.dataset.domainToggle, enabled: target.checked }, this._t("ruleSaved"));
    }
  }

  _onInput(ev) {
    const target = ev.target;
    if (target.matches("[data-role='search']")) {
      const caret = target.selectionStart;
      this._search = target.value;
      this._render();
      const refreshed = this.shadowRoot.querySelector("[data-role='search']");
      if (refreshed) { refreshed.focus(); try { refreshed.setSelectionRange(caret, caret); } catch (_) {} }
    }
  }

  _openMoreInfo(entityId) {
    this.dispatchEvent(new CustomEvent("hass-more-info", { detail: { entityId }, bubbles: true, composed: true }));
  }

  async _rename(entityId, reset) {
    const input = this.shadowRoot.querySelector(`[data-rename-eid="${CSS.escape(entityId)}"]`);
    const name = reset ? null : (input?.value || "").trim();
    await this._callAndReload({ type: `${DOMAIN}/rename`, entity_id: entityId, name }, reset ? this._t("renameReset") : this._t("renameSaved"));
  }

  async _saveDefaults() {
    const categories = (this.shadowRoot.querySelector("[data-setting='categories']")?.value || "").split(",").map((x) => x.trim()).filter(Boolean);
    const keywords = (this.shadowRoot.querySelector("[data-setting='keywords']")?.value || "").split(",").map((x) => x.trim()).filter(Boolean);
    await this._callAndReload({ type: `${DOMAIN}/set_defaults`, categories, keywords }, this._t("rulesSaved"));
  }

  async _regenerate() {
    await this._callAndReload({ type: `${DOMAIN}/regenerate` }, this._t("regenerated"), true);
  }

  async _copyFile() {
    const content = this._data?.file?.content;
    if (content === undefined) {
      await this._load(true);
      return;
    }
    try {
      await navigator.clipboard.writeText(content || "");
      this._toast(this._t("copied"));
    } catch (err) {
      this._toast(this._errorText(err), true);
    }
  }

  async _bulkApply() {
    const keyword = (this.shadowRoot.querySelector("[data-bulk='keyword']")?.value || "").trim();
    const where = this.shadowRoot.querySelector("[data-bulk='where']")?.value || "both";
    const mode = this.shadowRoot.querySelector("[data-bulk='mode']")?.value || "exclude";
    const domain = this.shadowRoot.querySelector("[data-bulk='domain']")?.value || null;
    if (!keyword) return;
    this._loading = true;
    this._render();
    try {
      const result = await this._hass.callWS({ type: `${DOMAIN}/bulk_rule`, keyword, where, mode, domain });
      this._bulkOpen = false;
      this._loading = false;
      await this._load(this._tab === "file");
      this._toast(this._t("bulkDone", { count: result.changed || 0 }));
    } catch (err) {
      this._loading = false;
      this._render();
      this._toast(this._errorText(err), true);
    }
  }

  async _callAndReload(message, success, includeFile = false) {
    if (!this._hass) return;
    this._loading = true;
    this._render();
    try {
      await this._hass.callWs(message);
      this._loading = false;
      await this._load(includeFile || this._tab === "file");
      this._toast(success);
    } catch (err) {
      this._loading = false;
      this._render();
      this._toast(this._errorText(err), true);
    }
  }
}

if (!customElements.get("eshtaya-entity-manager-panel")) {
  customElements.define("eshtaya-entity-manager-panel", EshtayaEntityManagerPanel);
}
