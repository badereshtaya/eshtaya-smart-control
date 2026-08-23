import "./eshtaya-entity-manager-panel.js";

const DOMAIN = "eshtaya_smart_control/entity";
const panelClass = customElements.get("eshtaya-entity-manager-panel");

if (panelClass) {
  const baseLoad = panelClass.prototype._load;
  const baseOpenMoreInfo = panelClass.prototype._openMoreInfo;

  panelClass.prototype._ensureV12State = function () {
    this._selectedEntities ??= new Set();
    this._areaFilter ??= "__all";
    this._platformFilter ??= "__all";
    this._availabilityFilter ??= "all";
    this._sortMode ??= "name";
    this._density ??= "comfortable";
    this._pendingRulesImport ??= null;
    this._rulesImportPreview ??= null;
  };

  panelClass.prototype._load = async function (includeFile = false) {
    this._ensureV12State();
    await baseLoad.call(this, includeFile);
    const valid = new Set((this._data?.entities || []).map((e) => e.entity_id));
    for (const id of [...this._selectedEntities]) if (!valid.has(id)) this._selectedEntities.delete(id);
  };

  panelClass.prototype._callAndReload = async function (message, success, includeFile = false) {
    if (!this._hass) return;
    this._loading = true;
    this._render();
    try {
      await this._hass.callWS(message);
      this._loading = false;
      await this._load(includeFile || this._tab === "file");
      this._toast(success);
    } catch (err) {
      this._loading = false;
      this._render();
      this._toast(this._errorText(err), true);
    }
  };

  panelClass.prototype._filteredEntities = function () {
    this._ensureV12State();
    if (!this._data?.entities) return [];
    const term = (this._search || "").trim().toLocaleLowerCase();
    const list = this._data.entities.filter((entity) => {
      if (this._domain !== "__all" && entity.domain !== this._domain) return false;
      if (this._areaFilter !== "__all" && (entity.area_name || "") !== this._areaFilter) return false;
      if (this._platformFilter !== "__all" && (entity.platform || "") !== this._platformFilter) return false;
      if (this._availabilityFilter === "available" && !entity.available) return false;
      if (this._availabilityFilter === "unavailable" && entity.available) return false;
      if (this._status === "included" && entity.excluded) return false;
      if (this._status === "excluded" && !entity.excluded) return false;
      if (this._status === "overrides" && entity.rule === "inherit") return false;
      if (!term) return true;
      const haystack = `${entity.entity_id} ${entity.name || ""} ${entity.device_name || ""} ${entity.area_name || ""} ${entity.platform || ""}`.toLocaleLowerCase();
      return haystack.includes(term);
    });

    const collator = new Intl.Collator(this._lang(), { numeric: true, sensitivity: "base" });
    return list.sort((a, b) => {
      if (this._sortMode === "entity_id") return collator.compare(a.entity_id, b.entity_id);
      if (this._sortMode === "domain") return collator.compare(`${a.domain} ${a.name}`, `${b.domain} ${b.name}`);
      if (this._sortMode === "area") return collator.compare(`${a.area_name || "~"} ${a.name}`, `${b.area_name || "~"} ${b.name}`);
      return collator.compare(a.name || a.entity_id, b.name || b.entity_id);
    });
  };

  panelClass.prototype._styles = function () {
    return `
      :host{display:block;width:100%;min-height:100%;box-sizing:border-box;color:var(--primary-text-color);background:var(--primary-background-color)}
      *{box-sizing:border-box} button,input,select{font:inherit}
      .app{width:100%;min-height:100vh;padding:22px clamp(12px,2.4vw,34px) 88px;background:linear-gradient(180deg,color-mix(in srgb,var(--primary-color) 5%,var(--primary-background-color)) 0,var(--primary-background-color) 220px);font-family:var(--paper-font-body1_-_font-family,Roboto,Arial,sans-serif)}
      .shell{width:min(1880px,100%);margin:0 auto}
      .hero{display:flex;justify-content:space-between;gap:18px;align-items:flex-start;margin-bottom:16px}
      .eyebrow{font-size:10px;letter-spacing:.14em;text-transform:uppercase;font-weight:800;color:var(--primary-color);margin-bottom:7px}
      h1{font-size:clamp(26px,2.6vw,38px);line-height:1.1;letter-spacing:-.025em;margin:0}.hero p{margin:7px 0 0;color:var(--secondary-text-color);font-size:13px}
      .heroRight{display:flex;align-items:center;gap:8px;flex-wrap:wrap;justify-content:flex-end}.syncPill{display:flex;align-items:center;gap:7px;padding:8px 11px;border:1px solid var(--divider-color);border-radius:999px;background:var(--card-background-color);font-size:11px;font-weight:800}.syncDot{width:8px;height:8px;border-radius:50%}.syncPill.ok .syncDot{background:var(--success-color,#43a047)}.syncPill.bad .syncDot{background:var(--error-color,#e53935)}
      .btn{border:1px solid var(--divider-color);background:var(--card-background-color);color:var(--primary-text-color);padding:9px 13px;border-radius:11px;cursor:pointer;font-weight:700;transition:.15s ease}.btn:hover{border-color:color-mix(in srgb,var(--primary-color) 55%,var(--divider-color));transform:translateY(-1px)}.btn.primary{background:var(--primary-color);border-color:var(--primary-color);color:var(--text-primary-color,#fff)}.btn.danger{color:var(--error-color,#e53935);background:color-mix(in srgb,var(--error-color,#e53935) 8%,var(--card-background-color))}.btn.small{padding:7px 9px;font-size:11px}.btn:disabled{opacity:.45;cursor:not-allowed;transform:none}
      .stats{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin-bottom:14px}.stat{min-width:0;background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:15px;padding:13px 14px;display:flex;gap:11px;align-items:center}.statIcon{width:36px;height:36px;border-radius:10px;display:grid;place-items:center;background:color-mix(in srgb,var(--primary-color) 10%,var(--secondary-background-color));color:var(--primary-color);font-weight:900}.statLabel{font-size:10.5px;color:var(--secondary-text-color);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.statValue{font-size:20px;font-weight:900;margin-top:2px}
      .tabs{display:flex;gap:5px;padding:5px;border:1px solid var(--divider-color);border-radius:14px;background:var(--card-background-color);position:sticky;top:6px;z-index:10;overflow:auto;margin-bottom:12px;box-shadow:0 4px 18px rgba(0,0,0,.05)}.tab{border:0;background:transparent;color:var(--secondary-text-color);padding:9px 13px;border-radius:10px;cursor:pointer;font-weight:800;white-space:nowrap}.tab.active{background:color-mix(in srgb,var(--primary-color) 12%,var(--card-background-color));color:var(--primary-color)}
      .toolbarCard{border:1px solid var(--divider-color);background:var(--card-background-color);border-radius:15px;padding:11px;margin-bottom:10px}.toolbar{display:grid;grid-template-columns:minmax(220px,1.5fr) repeat(5,minmax(130px,.55fr)) auto;gap:8px;align-items:center}.search,.select,.textInput,.renameInput{width:100%;border:1px solid var(--divider-color);background:var(--secondary-background-color);color:var(--primary-text-color);border-radius:10px;padding:9px 10px;outline:none}.search:focus,.select:focus,.textInput:focus,.renameInput:focus{border-color:var(--primary-color);box-shadow:0 0 0 2px color-mix(in srgb,var(--primary-color) 13%,transparent)}
      .domainScroller{display:flex;gap:6px;overflow:auto;padding:9px 1px 1px;scrollbar-width:thin}.chip{border:1px solid var(--divider-color);background:var(--secondary-background-color);color:var(--secondary-text-color);border-radius:999px;padding:6px 10px;font-size:11px;font-weight:800;cursor:pointer;white-space:nowrap}.chip.active{color:var(--primary-color);border-color:color-mix(in srgb,var(--primary-color) 45%,var(--divider-color));background:color-mix(in srgb,var(--primary-color) 10%,var(--secondary-background-color))}
      .resultsLine{display:flex;justify-content:space-between;align-items:center;gap:8px;margin:7px 2px 9px;color:var(--secondary-text-color);font-size:11px}.textBtn{border:0;background:none;color:var(--primary-color);cursor:pointer;font-weight:800;padding:4px}
      .entityHeader,.entityRow{display:grid;grid-template-columns:34px minmax(220px,1.25fr) minmax(170px,.8fr) minmax(250px,1fr) minmax(280px,1.05fr);gap:10px;align-items:center}.entityHeader{padding:5px 11px;color:var(--secondary-text-color);font-size:10px;font-weight:800;text-transform:uppercase}.list{display:flex;flex-direction:column;gap:6px}.entityRow{background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:13px;padding:10px 11px;transition:.15s ease}.entityRow:hover{border-color:color-mix(in srgb,var(--primary-color) 28%,var(--divider-color));box-shadow:0 3px 12px rgba(0,0,0,.04)}.entityRow.selected{background:color-mix(in srgb,var(--primary-color) 5%,var(--card-background-color));border-color:color-mix(in srgb,var(--primary-color) 40%,var(--divider-color))}.entityRow.compact{padding-top:7px;padding-bottom:7px}.check{width:17px;height:17px;accent-color:var(--primary-color);cursor:pointer}
      .entityMain{min-width:0;display:flex;gap:10px;align-items:center}.statusDot{width:9px;height:9px;border-radius:50%;flex:0 0 auto}.statusDot.included{background:var(--success-color,#43a047)}.statusDot.excluded{background:var(--error-color,#e53935)}.name{font-size:13px;font-weight:850;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.eid{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:10px;color:var(--secondary-text-color);margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.subline{font-size:10.5px;color:var(--secondary-text-color);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.stateBadge{display:inline-flex;width:max-content;max-width:100%;font-size:9.5px;font-weight:800;padding:3px 7px;border-radius:999px;border:1px solid var(--divider-color);margin-top:4px}.stateBadge.offline{color:var(--error-color,#e53935);border-color:color-mix(in srgb,var(--error-color,#e53935) 35%,var(--divider-color))}
      .seg{display:grid;grid-template-columns:repeat(3,1fr);padding:3px;border:1px solid var(--divider-color);background:var(--secondary-background-color);border-radius:10px;gap:2px}.seg button{border:0;background:transparent;color:var(--secondary-text-color);border-radius:7px;padding:7px 5px;font-size:10px;font-weight:850;cursor:pointer;white-space:nowrap}.seg button.active.auto{background:var(--card-background-color);color:var(--primary-text-color)}.seg button.active.allow{background:color-mix(in srgb,var(--success-color,#43a047) 13%,var(--card-background-color));color:var(--success-color,#43a047)}.seg button.active.exclude{background:color-mix(in srgb,var(--error-color,#e53935) 12%,var(--card-background-color));color:var(--error-color,#e53935)}.reason{font-size:9.5px;color:var(--secondary-text-color);margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
      .renameWrap{display:grid;grid-template-columns:minmax(100px,1fr) 34px 34px;gap:5px}.iconBtn{width:34px;height:34px;border:1px solid var(--divider-color);border-radius:9px;background:var(--secondary-background-color);color:var(--primary-text-color);cursor:pointer;font-weight:900}.iconBtn:hover{color:var(--primary-color);border-color:var(--primary-color)}.iconBtn:disabled{opacity:.4;cursor:not-allowed}
      .selectionBar{position:fixed;left:50%;bottom:18px;transform:translateX(-50%);z-index:40;width:min(720px,calc(100% - 24px));display:flex;align-items:center;justify-content:space-between;gap:10px;padding:9px 11px;border:1px solid color-mix(in srgb,var(--primary-color) 35%,var(--divider-color));border-radius:15px;background:color-mix(in srgb,var(--card-background-color) 96%,transparent);backdrop-filter:blur(14px);box-shadow:0 12px 34px rgba(0,0,0,.18)}.selectionActions{display:flex;gap:6px;flex-wrap:wrap}.selectedCount{font-weight:900;font-size:12px}
      .sectionCard{background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:15px;padding:15px;margin-bottom:10px}.sectionTitle{font-size:16px;font-weight:900;margin-bottom:4px}.sectionDesc{color:var(--secondary-text-color);font-size:11px;line-height:1.5;margin-bottom:13px}.domainGrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:7px}.domainRule{display:flex;align-items:center;justify-content:space-between;gap:9px;padding:9px 10px;border:1px solid var(--divider-color);border-radius:11px;background:var(--secondary-background-color)}.domainName{font:800 11px ui-monospace,SFMono-Regular,Consolas,monospace}.domainStats{font-size:9.5px;color:var(--secondary-text-color);margin-top:2px}.switch{position:relative;width:39px;height:22px;display:inline-block}.switch input{display:none}.slider{position:absolute;inset:0;border-radius:999px;background:var(--disabled-text-color);cursor:pointer}.slider:before{content:"";position:absolute;width:16px;height:16px;left:3px;top:3px;background:white;border-radius:50%;transition:.18s}.switch input:checked + .slider{background:var(--primary-color)}.switch input:checked + .slider:before{transform:translateX(17px)}[dir="rtl"] .switch input:checked + .slider:before{transform:translateX(-17px)}
      .formGrid,.yamlMeta{display:grid;grid-template-columns:1fr 1fr;gap:9px}.field label{display:block;font-size:10.5px;font-weight:850;margin-bottom:5px}.fieldHint{font-size:9.5px;color:var(--secondary-text-color);margin-top:4px}.metaBox{padding:9px;border:1px solid var(--divider-color);border-radius:10px;background:var(--secondary-background-color);min-width:0}.metaBox .label{font-size:9.5px;color:var(--secondary-text-color);margin-bottom:3px}.metaBox code{font-size:10.5px;word-break:break-all}.yamlBox{margin:0;padding:12px;min-height:280px;max-height:55vh;overflow:auto;background:var(--code-editor-background-color,#111827);color:var(--code-editor-text-color,#e5e7eb);border:1px solid var(--divider-color);border-radius:11px;font:11px/1.55 ui-monospace,SFMono-Regular,Consolas,monospace;direction:ltr;text-align:left}
      .deviceGrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:9px}.deviceCard{background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:14px;padding:12px}.deviceHead{display:flex;justify-content:space-between;align-items:flex-start;gap:8px;margin-bottom:8px}.deviceTitle{font-size:13px;font-weight:900}.deviceArea{font-size:10px;color:var(--secondary-text-color);margin-top:2px}.badge{display:inline-flex;padding:4px 7px;border:1px solid var(--divider-color);border-radius:999px;font-size:9.5px;color:var(--secondary-text-color)}.miniEntity{padding:8px 0;border-top:1px solid var(--divider-color);display:flex;justify-content:space-between;gap:8px;align-items:center}.miniEntity:first-of-type{border-top:0}
      .empty{padding:40px 14px;text-align:center;border:1px dashed var(--divider-color);border-radius:14px;background:var(--card-background-color);color:var(--secondary-text-color);font-size:12px}.notice{padding:11px 12px;border:1px solid var(--divider-color);border-radius:11px;background:var(--secondary-background-color);font-size:11px;line-height:1.55}.notice.warn{border-color:color-mix(in srgb,var(--warning-color,#f9a825) 40%,var(--divider-color))}.notice.bad{border-color:color-mix(in srgb,var(--error-color,#e53935) 40%,var(--divider-color))}
      .modalBackdrop{position:fixed;inset:0;background:rgba(0,0,0,.5);display:grid;place-items:center;padding:16px;z-index:60}.modal{width:min(560px,100%);background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:16px;padding:16px;box-shadow:0 20px 60px rgba(0,0,0,.25)}.modalHead{display:flex;justify-content:space-between;gap:10px;align-items:center;margin-bottom:12px}.modalTitle{font-size:16px;font-weight:900}.modalActions{display:flex;justify-content:flex-end;gap:7px;margin-top:14px}
      .toast{position:fixed;inset-inline-end:18px;bottom:20px;z-index:80;opacity:0;transform:translateY(15px);transition:.18s;background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:10px;padding:9px 12px;box-shadow:0 9px 30px rgba(0,0,0,.18);font-size:11px}.toast.show{opacity:1;transform:none}.toast.ok{border-color:color-mix(in srgb,var(--success-color,#43a047) 42%,var(--divider-color))}.toast.error{border-color:color-mix(in srgb,var(--error-color,#e53935) 48%,var(--divider-color));color:var(--error-color,#e53935)}.busy{position:fixed;inset:0;z-index:70;background:rgba(0,0,0,.18);display:grid;place-items:center}.busyInner{display:flex;gap:9px;align-items:center;background:rgba(20,20,20,.82);color:#fff;padding:10px 13px;border-radius:12px;font-size:11px;font-weight:800}.spinner{width:19px;height:19px;border-radius:50%;border:2px solid rgba(255,255,255,.35);border-top-color:#fff;animation:spin .7s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}
      @media(max-width:1280px){.toolbar{grid-template-columns:minmax(220px,1.4fr) repeat(3,minmax(125px,.6fr))}.toolbar .optionalWide{display:none}.entityHeader,.entityRow{grid-template-columns:32px minmax(220px,1.2fr) minmax(200px,.8fr) minmax(235px,1fr)}.contextCol{display:none}.stats{grid-template-columns:repeat(3,1fr)}}
      @media(max-width:820px){.app{padding:12px 9px 88px}.hero{flex-direction:column}.heroRight{justify-content:flex-start}.stats{grid-template-columns:1fr 1fr}.toolbar{grid-template-columns:1fr 1fr}.toolbar .searchWrap{grid-column:1/-1}.entityHeader{display:none}.entityRow{grid-template-columns:28px minmax(0,1fr);gap:8px}.entityRow>.alexaCol,.entityRow>.renameCol{grid-column:2}.renameWrap{grid-template-columns:1fr 34px 34px}.selectionBar{bottom:10px;align-items:flex-start;flex-direction:column}.selectionActions{width:100%}.selectionActions .btn{flex:1}.formGrid,.yamlMeta{grid-template-columns:1fr}.deviceGrid{grid-template-columns:1fr}}
      @media(max-width:460px){.stats{grid-template-columns:1fr 1fr}.stat:nth-child(5){grid-column:1/-1}.toolbar{grid-template-columns:1fr}.toolbar .searchWrap{grid-column:auto}.heroRight{width:100%}.heroRight .btn{flex:1}.syncPill{width:100%;justify-content:center}}
    `;
  };

  panelClass.prototype._statCard = function (icon, label, value, cls = "") {
    return `<div class="stat ${cls}"><div class="statIcon">${icon}</div><div style="min-width:0"><div class="statLabel">${this._esc(label)}</div><div class="statValue">${Number(value || 0).toLocaleString()}</div></div></div>`;
  };

  panelClass.prototype._render = function () {
    this._ensureV12State();
    if (!this.shadowRoot) return;
    const ar = this._lang() === "ar";
    const data = this._data;
    const stats = data?.stats || { total: 0, included: 0, excluded: 0, overrides: 0, unavailable: 0 };
    const syncOk = data?.file?.sync?.ok !== false;
    this.shadowRoot.innerHTML = `
      <style>${this._styles()}</style>
      <div class="app" dir="${ar ? "rtl" : "ltr"}"><div class="shell">
        <header class="hero">
          <div><div class="eyebrow">ESHTAYA SMART · ENTITY CONTROL</div><h1>${ar ? "مدير الكيانات و Alexa" : "Entity & Alexa Manager"}</h1><p>${ar ? "إدارة الأسماء، الظهور في Alexa، القواعد والنسخ الاحتياطية من لوحة واحدة." : "Names, Alexa visibility, rules and backups in one focused workspace."}</p></div>
          <div class="heroRight">
            <div class="syncPill ${syncOk ? "ok" : "bad"}"><span class="syncDot"></span>${syncOk ? (ar ? "ملفا Alexa متزامنان" : "Alexa files synced") : (ar ? "الملفان غير متزامنين" : "Files out of sync")}</div>
            ${!syncOk ? `<button class="btn danger small" data-action="repair-sync">${ar ? "إصلاح المزامنة" : "Repair sync"}</button>` : ""}
            <button class="btn" data-action="refresh">↻ ${ar ? "تحديث" : "Refresh"}</button>
            <button class="btn primary" data-action="bulk">⚡ ${ar ? "تعديل بالكلمة" : "Keyword bulk edit"}</button>
          </div>
        </header>
        <section class="stats">
          ${this._statCard("◫", ar ? "إجمالي الكيانات" : "Total", stats.total)}
          ${this._statCard("✓", ar ? "ظاهرة في Alexa" : "Exposed", stats.included)}
          ${this._statCard("⊘", ar ? "مخفية" : "Hidden", stats.excluded)}
          ${this._statCard("⚙", ar ? "Overrides" : "Overrides", stats.overrides)}
          ${this._statCard("!", ar ? "غير متوفرة" : "Unavailable", stats.unavailable)}
        </section>
        <nav class="tabs">
          ${this._tabButton("entities", "☷", ar ? "الكيانات" : "Entities")}
          ${this._tabButton("devices", "▦", ar ? "الأجهزة" : "Devices")}
          ${this._tabButton("rules", "⚙", ar ? "القواعد" : "Rules")}
          ${this._tabButton("file", "YAML", ar ? "الملفات والنسخ" : "Files & backup")}
        </nav>
        <main>${!data ? `<div class="empty">${ar ? "جاري التحميل..." : "Loading..."}</div>` : this._renderTab()}</main>
        ${this._renderSelectionBar()}
        ${this._renderBulkModal()}
        <div class="toast"></div>
      </div>${this._loading ? `<div class="busy"><div class="busyInner"><div class="spinner"></div>${ar ? "جاري الحفظ..." : "Saving..."}</div></div>` : ""}</div>`;
  };

  panelClass.prototype._renderToolbar = function () {
    this._ensureV12State();
    const ar = this._lang() === "ar";
    const entities = this._data?.entities || [];
    const domains = this._data?.domains || [];
    const areas = [...new Set(entities.map((e) => e.area_name).filter(Boolean))].sort();
    const platforms = [...new Set(entities.map((e) => e.platform).filter(Boolean))].sort();
    const filtered = this._filteredEntities();
    const selectedVisible = filtered.filter((e) => this._selectedEntities.has(e.entity_id)).length;
    return `
      <div class="toolbarCard">
        <div class="toolbar">
          <div class="searchWrap"><input class="search" data-role="search" value="${this._esc(this._search || "")}" placeholder="${ar ? "ابحث بالاسم، Entity ID، الجهاز أو المنطقة..." : "Search name, entity ID, device or area..."}"></div>
          <select class="select" data-role="status">${this._option("all", ar ? "كل حالات Alexa" : "All Alexa states", this._status)}${this._option("included", ar ? "الظاهرة فقط" : "Exposed only", this._status)}${this._option("excluded", ar ? "المخفية فقط" : "Hidden only", this._status)}${this._option("overrides", ar ? "Overrides فقط" : "Overrides only", this._status)}</select>
          <select class="select" data-role="area"><option value="__all">${ar ? "كل المناطق" : "All areas"}</option>${areas.map((a)=>`<option value="${this._esc(a)}" ${a===this._areaFilter?"selected":""}>${this._esc(a)}</option>`).join("")}</select>
          <select class="select" data-role="platform"><option value="__all">${ar ? "كل التكاملات" : "All integrations"}</option>${platforms.map((p)=>`<option value="${this._esc(p)}" ${p===this._platformFilter?"selected":""}>${this._esc(p)}</option>`).join("")}</select>
          <select class="select optionalWide" data-role="availability">${this._option("all", ar ? "كل التوفر" : "Any availability", this._availabilityFilter)}${this._option("available", ar ? "متوفر" : "Available", this._availabilityFilter)}${this._option("unavailable", ar ? "غير متوفر" : "Unavailable", this._availabilityFilter)}</select>
          <select class="select optionalWide" data-role="sort">${this._option("name", ar ? "ترتيب: الاسم" : "Sort: name", this._sortMode)}${this._option("entity_id", "Entity ID", this._sortMode)}${this._option("domain", ar ? "النوع" : "Domain", this._sortMode)}${this._option("area", ar ? "المنطقة" : "Area", this._sortMode)}</select>
          <button class="btn small" data-action="toggle-density">${this._density === "compact" ? (ar ? "عرض مريح" : "Comfortable") : (ar ? "عرض مضغوط" : "Compact")}</button>
        </div>
        <div class="domainScroller">
          <button class="chip ${this._domain === "__all" ? "active" : ""}" data-domain-filter="__all">${ar ? "الكل" : "All"} · ${this._data?.stats?.total || 0}</button>
          ${domains.map((d)=>`<button class="chip ${this._domain===d.domain?"active":""}" data-domain-filter="${this._esc(d.domain)}">${this._esc(d.domain)} · ${d.count}</button>`).join("")}
        </div>
        <div class="resultsLine"><span>${filtered.length} ${ar ? "نتيجة" : "results"}${this._selectedEntities.size ? ` · ${this._selectedEntities.size} ${ar ? "محدد" : "selected"}` : ""}</span><span><button class="textBtn" data-action="select-visible">${ar ? "تحديد النتائج الظاهرة" : "Select visible"}</button>${selectedVisible ? ` · <button class="textBtn" data-action="clear-selection">${ar ? "إلغاء التحديد" : "Clear selection"}</button>` : ""} · <button class="textBtn" data-action="clear-filters">${ar ? "مسح الفلاتر" : "Clear filters"}</button></span></div>
      </div>`;
  };

  panelClass.prototype._renderEntities = function () {
    const ar = this._lang() === "ar";
    const entities = this._filteredEntities();
    return `${this._renderToolbar()}<div class="entityHeader"><div></div><div>${ar ? "الكيان" : "Entity"}</div><div class="contextCol">${ar ? "السياق" : "Context"}</div><div>${ar ? "Alexa" : "Alexa"}</div><div>${ar ? "الاسم" : "Name"}</div></div><div class="list">${entities.length ? entities.map((e)=>this._entityRow(e)).join("") : `<div class="empty">${ar ? "لا توجد نتائج مطابقة." : "No matching entities."}</div>`}</div>`;
  };

  panelClass.prototype._entityRow = function (e) {
    const ar = this._lang() === "ar";
    const selected = this._selectedEntities.has(e.entity_id);
    const stateText = e.available ? String(e.state ?? "") : (ar ? "غير متوفر" : "Unavailable");
    return `<div class="entityRow ${selected ? "selected" : ""} ${this._density === "compact" ? "compact" : ""}" data-eid="${this._esc(e.entity_id)}">
      <div><input class="check" type="checkbox" data-select-eid="${this._esc(e.entity_id)}" ${selected ? "checked" : ""}></div>
      <div class="entityMain"><span class="statusDot ${e.excluded ? "excluded" : "included"}"></span><div style="min-width:0;flex:1"><div class="name">${this._esc(e.name)}</div><div class="eid">${this._esc(e.entity_id)}</div><span class="stateBadge ${e.available ? "" : "offline"}">${this._esc(stateText)}</span></div><button class="iconBtn" data-action="more-info" data-eid="${this._esc(e.entity_id)}">↗</button></div>
      <div class="contextCol"><div class="subline">${this._esc(e.device_name || (ar ? "بدون جهاز" : "No device"))}</div><div class="subline">${this._esc(e.area_name || (ar ? "بدون منطقة" : "No area"))}</div><div class="subline">${this._esc(e.platform || "—")} · ${this._esc(e.domain)}</div></div>
      <div class="alexaCol"><div class="seg"><button data-action="direct-rule" data-eid="${this._esc(e.entity_id)}" data-mode="inherit" class="${e.rule === "inherit" ? "active auto" : ""}">${ar ? "تلقائي" : "Auto"}</button><button data-action="direct-rule" data-eid="${this._esc(e.entity_id)}" data-mode="allow" class="${e.rule === "allow" ? "active allow" : ""}">${ar ? "إظهار" : "Show"}</button><button data-action="direct-rule" data-eid="${this._esc(e.entity_id)}" data-mode="exclude" class="${e.rule === "exclude" ? "active exclude" : ""}">${ar ? "إخفاء" : "Hide"}</button></div><div class="reason" title="${this._esc(e.reason)}">${this._esc(e.reason)}</div></div>
      <div class="renameCol"><div class="renameWrap"><input class="renameInput" data-rename-eid="${this._esc(e.entity_id)}" value="${this._esc(e.name)}" ${e.can_rename ? "" : "disabled"}><button class="iconBtn" data-action="rename-save" data-eid="${this._esc(e.entity_id)}" ${e.can_rename ? "" : "disabled"} title="${ar ? "حفظ الاسم" : "Save name"}">✓</button><button class="iconBtn" data-action="rename-reset" data-eid="${this._esc(e.entity_id)}" ${e.can_rename ? "" : "disabled"} title="${ar ? "إرجاع الاسم" : "Reset name"}">↺</button></div></div>
    </div>`;
  };

  panelClass.prototype._renderSelectionBar = function () {
    this._ensureV12State();
    if (!this._selectedEntities.size) return "";
    const ar = this._lang() === "ar";
    return `<div class="selectionBar"><div class="selectedCount">${this._selectedEntities.size} ${ar ? "كيان محدد" : "entities selected"}</div><div class="selectionActions"><button class="btn small" data-action="selected-rule" data-mode="inherit">${ar ? "تلقائي" : "Auto"}</button><button class="btn small primary" data-action="selected-rule" data-mode="allow">${ar ? "إظهار في Alexa" : "Show in Alexa"}</button><button class="btn small danger" data-action="selected-rule" data-mode="exclude">${ar ? "إخفاء من Alexa" : "Hide from Alexa"}</button><button class="btn small" data-action="clear-selection">${ar ? "إلغاء" : "Clear"}</button></div></div>`;
  };

  panelClass.prototype._renderDevices = function () {
    const ar = this._lang() === "ar";
    const entities = this._filteredEntities();
    const groups = new Map();
    for (const e of entities) {
      const key = e.device_id || `__${e.area_name || "none"}__${e.domain}`;
      if (!groups.has(key)) groups.set(key, { name: e.device_name || (ar ? "بدون جهاز" : "No device"), area: e.area_name || (ar ? "بدون منطقة" : "No area"), entities: [] });
      groups.get(key).entities.push(e);
    }
    const sorted = [...groups.values()].sort((a,b)=>a.name.localeCompare(b.name));
    return `${this._renderToolbar()}<div class="deviceGrid">${sorted.length ? sorted.map((g)=>`<section class="deviceCard"><div class="deviceHead"><div><div class="deviceTitle">${this._esc(g.name)}</div><div class="deviceArea">${this._esc(g.area)}</div></div><span class="badge">${g.entities.length} ${ar ? "كيان" : "entities"}</span></div>${g.entities.map((e)=>`<div class="miniEntity"><div style="min-width:0"><div class="name">${this._esc(e.name)}</div><div class="eid">${this._esc(e.entity_id)}</div></div><div class="seg" style="width:170px"><button data-action="direct-rule" data-eid="${this._esc(e.entity_id)}" data-mode="inherit" class="${e.rule==="inherit"?"active auto":""}">${ar?"تلقائي":"Auto"}</button><button data-action="direct-rule" data-eid="${this._esc(e.entity_id)}" data-mode="allow" class="${e.rule==="allow"?"active allow":""}">${ar?"إظهار":"Show"}</button><button data-action="direct-rule" data-eid="${this._esc(e.entity_id)}" data-mode="exclude" class="${e.rule==="exclude"?"active exclude":""}">${ar?"إخفاء":"Hide"}</button></div></div>`).join("")}</section>`).join("") : `<div class="empty">${ar ? "لا توجد نتائج." : "No results."}</div>`}</div>`;
  };

  panelClass.prototype._renderRules = function () {
    const ar = this._lang() === "ar";
    const settings = this._data?.settings || {};
    const domains = this._data?.domains || [];
    const orphanIds = this._data?.maintenance?.orphan_rules || [];
    return `<section class="sectionCard"><div class="sectionTitle">${ar ? "قواعد الـDomains" : "Domain rules"}</div><div class="sectionDesc">${ar ? "إيقاف Domain يخفي كياناته تلقائيًا، مع بقاء Force Allow أعلى أولوية." : "Disabling a domain hides its entities automatically; Force Allow still has higher priority."}</div><div class="domainGrid">${domains.map((d)=>`<div class="domainRule"><div><div class="domainName">${this._esc(d.domain)}</div><div class="domainStats">${d.count} ${ar?"كيان":"entities"} · ${d.excluded} ${ar?"مخفي":"hidden"}</div></div><label class="switch"><input type="checkbox" data-domain-toggle="${this._esc(d.domain)}" ${d.enabled?"checked":""}><span class="slider"></span></label></div>`).join("")}</div></section>
      <section class="sectionCard"><div class="sectionTitle">${ar ? "الاستثناء التلقائي" : "Automatic exclusions"}</div><div class="sectionDesc">${ar ? "هذه القواعد تطبق فقط عندما تكون حالة الكيان Auto." : "These rules apply only while an entity uses Auto."}</div><div class="formGrid"><div class="field"><label>Entity categories</label><input class="textInput" data-setting="categories" value="${this._esc((settings.exclude_entity_category||[]).join(", "))}"><div class="fieldHint">diagnostic, config</div></div><div class="field"><label>${ar?"الكلمات المستثناة":"Excluded keywords"}</label><input class="textInput" data-setting="keywords" value="${this._esc((settings.exclude_name_keywords||[]).join(", "))}"><div class="fieldHint">backlight, child_lock, browser_mod</div></div></div><div style="margin-top:12px"><button class="btn primary" data-action="save-defaults">${ar?"حفظ القواعد":"Save rules"}</button></div></section>
      <section class="sectionCard"><div class="sectionTitle">${ar ? "تنظيف القواعد القديمة" : "Rule maintenance"}</div><div class="sectionDesc">${ar ? "القواعد اليتيمة هي Overrides لكيانات لم تعد موجودة في Home Assistant. لا نحذفها تلقائيًا حتى لا نخسر Rule أثناء تعطل Integration مؤقتًا." : "Orphan rules are overrides for entities that are no longer loaded. They are not removed automatically to protect against temporary integration outages."}</div>${orphanIds.length ? `<div class="notice warn"><b>${orphanIds.length} ${ar?"قاعدة يتيمة":"orphan rules"}</b><div style="margin-top:6px;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:9.5px;max-height:120px;overflow:auto">${orphanIds.slice(0,50).map((x)=>this._esc(x)).join("<br>")}${orphanIds.length>50?"<br>…":""}</div></div><div style="margin-top:10px"><button class="btn danger" data-action="cleanup-orphans">${ar?"حذف القواعد اليتيمة":"Remove orphan rules"}</button></div>` : `<div class="notice">✓ ${ar?"لا توجد قواعد يتيمة.":"No orphan rules found."}</div>`}</section>`;
  };

  panelClass.prototype._renderFile = function () {
    const ar = this._lang() === "ar";
    const file = this._data?.file || {};
    const sync = file.sync || {};
    const content = file.content;
    const preview = this._rulesImportPreview;
    return `<section class="sectionCard"><div class="deviceHead"><div><div class="sectionTitle">hidden_entities.yaml</div><div class="sectionDesc">${ar ? "الملفان يُكتبان بنفس المحتوى تلقائيًا. إذا اختلفا يظهر تنبيه مزامنة أعلى الصفحة." : "Both files are written with identical content automatically. A sync warning appears if they ever differ."}</div></div><div style="display:flex;gap:7px"><button class="btn" data-action="load-file">${ar?"عرض المحتوى":"Load content"}</button><button class="btn primary" data-action="regenerate">${ar?"إعادة التوليد":"Regenerate"}</button></div></div><div class="yamlMeta"><div class="metaBox"><div class="label">Primary · ${sync.primary?.exists?"✓":"✕"}</div><code>${this._esc(file.path || "/config/hidden_entities.yaml")}</code></div><div class="metaBox"><div class="label">Public · ${sync.public?.exists?"✓":"✕"}</div><code>${this._esc(file.public_path || "/config/www/hidden_entities.yaml")}</code></div></div>${sync.ok===false?`<div class="notice bad">${ar?"النسختان غير متطابقتين. استخدم إصلاح المزامنة لإعادة توليدهما من القواعد الحالية.":"The two copies differ. Repair sync will regenerate both from the current rules."} <button class="btn small danger" data-action="repair-sync" style="margin-inline-start:8px">${ar?"إصلاح":"Repair"}</button></div>`:""}${content===undefined?"":`<pre class="yamlBox" style="margin-top:10px">${this._esc(content || "[]")}</pre>`}</section>
      <section class="sectionCard"><div class="sectionTitle">${ar ? "استيراد / تصدير قواعد Alexa" : "Import / export Alexa rules"}</div><div class="sectionDesc">${ar ? "ارفع alexa_rules.json لاسترجاع Domains وForce Allow وForce Exclude وقواعد Auto-exclude. يتم حفظ Backup للقواعد الحالية قبل الاستبدال." : "Upload alexa_rules.json to restore domains, entity overrides and automatic exclusions. Current rules are backed up before replacement."}</div><div class="formGrid"><div class="field"><label>${ar?"ملف القواعد":"Rules file"}</label><input class="textInput" type="file" accept=".json,application/json" data-rules-import-file><div class="fieldHint">alexa_rules.json</div></div><div class="field"><label>${ar?"آخر Backup قبل الاستيراد":"Last pre-import backup"}</label><div class="metaBox"><code>${this._esc(file.rules_backup_path || "/config/eshtaya_entity_manager_rules_backup.json")}</code></div></div></div>${preview?`<div class="yamlMeta" style="margin-top:10px"><div class="metaBox"><div class="label">${ar?"الملف":"File"}</div><code>${this._esc(preview.name)}</code></div><div class="metaBox"><div class="label">Domains</div><code>${preview.domains}</code></div><div class="metaBox"><div class="label">Force Allow</div><code>${preview.allow}</code></div><div class="metaBox"><div class="label">Force Exclude</div><code>${preview.exclude}</code></div></div>`:""}<div style="display:flex;gap:7px;flex-wrap:wrap;margin-top:12px"><button class="btn primary" data-action="import-rules" ${this._pendingRulesImport?"":"disabled"}>${ar?"استيراد واستبدال القواعد":"Import and replace rules"}</button><button class="btn" data-action="export-rules">${ar?"تنزيل alexa_rules.json":"Download alexa_rules.json"}</button></div></section>`;
  };

  panelClass.prototype._renderBulkModal = function () {
    if (!this._bulkOpen) return "";
    const ar = this._lang() === "ar";
    const domains = this._data?.domains || [];
    return `<div class="modalBackdrop" data-action="bulk-backdrop"><div class="modal"><div class="modalHead"><div class="modalTitle">${ar?"تعديل جماعي حسب كلمة":"Keyword bulk edit"}</div><button class="iconBtn" data-action="bulk-close">×</button></div><div class="field"><label>${ar?"الكلمة المفتاحية":"Keyword"}</label><input class="textInput" data-bulk="keyword"></div><div class="field" style="margin-top:9px"><label>${ar?"البحث في":"Search in"}</label><select class="select" data-bulk="where">${this._option("name",ar?"الاسم":"Name","both")}${this._option("id","Entity ID","both")}${this._option("both",ar?"الاسم + Entity ID":"Name + Entity ID","both")}</select></div><div class="field" style="margin-top:9px"><label>${ar?"الحالة الجديدة":"New rule"}</label><select class="select" data-bulk="mode">${this._option("allow",ar?"إظهار إجباري":"Force show","exclude")}${this._option("exclude",ar?"إخفاء إجباري":"Force hide","exclude")}${this._option("inherit",ar?"تلقائي":"Auto","exclude")}</select></div><div class="field" style="margin-top:9px"><label>Domain</label><select class="select" data-bulk="domain"><option value="">${ar?"كل الأنواع":"All domains"}</option>${domains.map((d)=>`<option value="${this._esc(d.domain)}" ${this._domain===d.domain?"selected":""}>${this._esc(d.domain)}</option>`).join("")}</select></div><div class="modalActions"><button class="btn" data-action="bulk-close">${ar?"إلغاء":"Cancel"}</button><button class="btn primary" data-action="bulk-apply">${ar?"تطبيق":"Apply"}</button></div></div></div>`;
  };

  panelClass.prototype._onChange = async function (ev) {
    this._ensureV12State();
    const target = ev.target;
    if (target.matches("[data-rules-import-file]")) {
      const file = target.files?.[0]; if (!file) return;
      try {
        const parsed = JSON.parse(await file.text());
        if (!parsed || typeof parsed !== "object" || Array.isArray(parsed) || (!parsed.domains && !parsed.entities && !parsed.defaults)) throw new Error("Not a valid alexa_rules.json");
        let allow=0, exclude=0; Object.values(parsed.entities||{}).forEach((v)=>{if(v?.enabled===true)allow++; if(v?.enabled===false)exclude++;});
        this._pendingRulesImport=parsed; this._rulesImportPreview={name:file.name,domains:Object.keys(parsed.domains||{}).length,allow,exclude}; this._render();
      } catch(err){this._pendingRulesImport=null;this._rulesImportPreview=null;this._render();this._toast(this._errorText(err),true);} return;
    }
    if (target.matches("[data-select-eid]")) { const id=target.dataset.selectEid; target.checked?this._selectedEntities.add(id):this._selectedEntities.delete(id); this._render(); return; }
    if (target.matches("[data-role='status']")) { this._status=target.value; this._render(); return; }
    if (target.matches("[data-role='area']")) { this._areaFilter=target.value; this._render(); return; }
    if (target.matches("[data-role='platform']")) { this._platformFilter=target.value; this._render(); return; }
    if (target.matches("[data-role='availability']")) { this._availabilityFilter=target.value; this._render(); return; }
    if (target.matches("[data-role='sort']")) { this._sortMode=target.value; this._render(); return; }
    if (target.matches("[data-domain-toggle]")) { await this._callAndReload({type:`${DOMAIN}/set_domain`,domain:target.dataset.domainToggle,enabled:target.checked},this._lang()==="ar"?"تم تحديث الـDomain":"Domain updated"); return; }
  };

  panelClass.prototype._onInput = function (ev) {
    const target=ev.target;
    if(target.matches("[data-role='search']")){const caret=target.selectionStart;this._search=target.value;this._render();const n=this.shadowRoot.querySelector("[data-role='search']");if(n){n.focus();try{n.setSelectionRange(caret,caret)}catch(_){}}}
  };

  panelClass.prototype._rename = async function (entityId, reset) {
    const input=this.shadowRoot.querySelector(`[data-rename-eid="${CSS.escape(entityId)}"]`); const name=reset?null:(input?.value||"").trim();
    await this._callAndReload({type:`${DOMAIN}/rename`,entity_id:entityId,name},reset?(this._lang()==="ar"?"تم إرجاع الاسم":"Name reset"):(this._lang()==="ar"?"تم حفظ الاسم":"Name saved"));
  };

  panelClass.prototype._saveDefaults = async function () {
    const categories=(this.shadowRoot.querySelector("[data-setting='categories']")?.value||"").split(",").map(x=>x.trim()).filter(Boolean);
    const keywords=(this.shadowRoot.querySelector("[data-setting='keywords']")?.value||"").split(",").map(x=>x.trim()).filter(Boolean);
    await this._callAndReload({type:`${DOMAIN}/set_defaults`,categories,keywords},this._lang()==="ar"?"تم حفظ القواعد":"Rules saved");
  };

  panelClass.prototype._bulkApply = async function () {
    const keyword=(this.shadowRoot.querySelector("[data-bulk='keyword']")?.value||"").trim(); if(!keyword)return;
    const where=this.shadowRoot.querySelector("[data-bulk='where']")?.value||"both"; const mode=this.shadowRoot.querySelector("[data-bulk='mode']")?.value||"exclude"; const domain=this.shadowRoot.querySelector("[data-bulk='domain']")?.value||null;
    this._loading=true;this._render();try{const r=await this._hass.callWS({type:`${DOMAIN}/bulk_rule`,keyword,where,mode,domain});this._bulkOpen=false;this._loading=false;await this._load(this._tab==="file");this._toast(`${r.changed||0} ${this._lang()==="ar"?"كيان تم تعديله":"entities updated"}`);}catch(err){this._loading=false;this._render();this._toast(this._errorText(err),true);}
  };

  panelClass.prototype._onClick = async function (ev) {
    this._ensureV12State();
    const target=ev.target.closest("[data-action],[data-tab],[data-domain-filter]"); if(!target)return;
    const ar=this._lang()==="ar";
    if(target.dataset.tab){this._tab=target.dataset.tab; if(this._tab==="file"&&this._data?.file?.content===undefined) await this._load(true); else this._render(); return;}
    if(target.dataset.domainFilter!==undefined){this._domain=target.dataset.domainFilter;this._render();return;}
    const action=target.dataset.action;
    if(action==="refresh") return this._load(this._tab==="file");
    if(action==="bulk"){this._bulkOpen=true;this._render();return;}
    if(action==="bulk-close"){this._bulkOpen=false;this._render();return;}
    if(action==="bulk-backdrop"&&ev.target===target){this._bulkOpen=false;this._render();return;}
    if(action==="bulk-apply") return this._bulkApply();
    if(action==="more-info") return baseOpenMoreInfo.call(this,target.dataset.eid);
    if(action==="rename-save") return this._rename(target.dataset.eid,false);
    if(action==="rename-reset") return this._rename(target.dataset.eid,true);
    if(action==="direct-rule") return this._callAndReload({type:`${DOMAIN}/set_entity_rule`,entity_id:target.dataset.eid,mode:target.dataset.mode},ar?"تم تحديث حالة Alexa":"Alexa rule updated");
    if(action==="toggle-density"){this._density=this._density==="compact"?"comfortable":"compact";this._render();return;}
    if(action==="select-visible"){this._filteredEntities().forEach(e=>this._selectedEntities.add(e.entity_id));this._render();return;}
    if(action==="clear-selection"){this._selectedEntities.clear();this._render();return;}
    if(action==="clear-filters"){this._search="";this._status="all";this._domain="__all";this._areaFilter="__all";this._platformFilter="__all";this._availabilityFilter="all";this._render();return;}
    if(action==="selected-rule"){
      const ids=[...this._selectedEntities]; if(!ids.length)return; this._loading=true;this._render();
      try{const r=await this._hass.callWS({type:`${DOMAIN}/set_many_rules`,entity_ids:ids,mode:target.dataset.mode});this._selectedEntities.clear();this._loading=false;await this._load(this._tab==="file");this._toast(`${r.changed||0} ${ar?"كيان تم تعديله":"entities updated"}`);}catch(err){this._loading=false;this._render();this._toast(this._errorText(err),true);} return;
    }
    if(action==="save-defaults") return this._saveDefaults();
    if(action==="regenerate") return this._callAndReload({type:`${DOMAIN}/regenerate`},ar?"تم إعادة توليد الملفين":"Files regenerated",true);
    if(action==="load-file") return this._load(true);
    if(action==="repair-sync") return this._callAndReload({type:`${DOMAIN}/repair_sync`},ar?"تم إصلاح مزامنة الملفين":"File sync repaired",true);
    if(action==="cleanup-orphans"){
      const count=this._data?.maintenance?.orphan_count||0; if(!count)return;
      if(!confirm(ar?`سيتم حذف ${count} Rule لكيانات غير موجودة حاليًا. هل تريد المتابعة؟`:`Remove ${count} rules for entities that are not currently loaded?`))return;
      return this._callAndReload({type:`${DOMAIN}/cleanup_orphans`},ar?"تم تنظيف القواعد اليتيمة":"Orphan rules removed");
    }
    if(action==="import-rules"){
      if(!this._pendingRulesImport)return; if(!confirm(ar?"سيتم استبدال القواعد الحالية بعد حفظ Backup. متابعة؟":"Current rules will be replaced after a backup is saved. Continue?"))return;
      this._loading=true;this._render();try{const r=await this._hass.callWS({type:`${DOMAIN}/import_rules`,rules:this._pendingRulesImport});this._pendingRulesImport=null;this._rulesImportPreview=null;this._loading=false;await this._load(true);this._toast(ar?`تم الاستيراد: ${r.force_exclude} مخفي، ${r.force_allow} ظاهر إجباريًا`:`Imported: ${r.force_exclude} hidden, ${r.force_allow} force-shown`);}catch(err){this._loading=false;this._render();this._toast(this._errorText(err),true);}return;
    }
    if(action==="export-rules"){
      try{const rules=await this._hass.callWS({type:`${DOMAIN}/export_rules`});const blob=new Blob([JSON.stringify(rules,null,2)+"\n"],{type:"application/json"});const url=URL.createObjectURL(blob);const a=document.createElement("a");a.href=url;a.download="alexa_rules.json";a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);this._toast(ar?"تم تجهيز النسخة الاحتياطية":"Backup downloaded");}catch(err){this._toast(this._errorText(err),true);}return;
    }
  };
}
