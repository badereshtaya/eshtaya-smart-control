/* Eshtaya Smart Control v2.4.3 — full Managed Template editor. */
const ESC_TM243_DOMAIN = "eshtaya_smart_control";

customElements.whenDefined("eshtaya-template-manager-panel").then(() => queueMicrotask(() => {
  const Panel = customElements.get("eshtaya-template-manager-panel");
  if (!Panel || Panel.prototype.__eshtayaTm243Applied) return;
  const p = Panel.prototype;
  p.__eshtayaTm243Applied = true;

  const baseRow = p._row;
  const baseRender = p._render;
  const baseClick = p._click;
  const baseInput = p._input;
  const baseChange = p._change;

  Object.defineProperty(p, "migrationLocked", {
    configurable: true,
    get() {
      if (this._data && Object.prototype.hasOwnProperty.call(this._data, "mutation_locked")) {
        return Boolean(this._data.mutation_locked);
      }
      const m = this.migration || {};
      return Boolean(m.legacy_found && !m.completed && ["prepared", "restart_required"].includes(String(m.phase || "")));
    },
  });

  p._row = function (x) {
    if (this._tab !== "managed") return baseRow.call(this, x);
    const dis = this.migrationLocked || this._busy ? "disabled" : "";
    const external = Boolean(x.external_managed);
    const source = this.esc(x.source_entity || "—");
    const file = this.esc(String(x.generated_path || "").split(/[\\/]/).pop() || "");
    return `<article class="row managed tm243-managed">
      <div class="id">
        <ha-icon icon="${x.type === "fan" ? "mdi:fan" : "mdi:lightbulb-outline"}"></ha-icon>
        <div>
          <div class="tm243-titleline">
            <b>${this.esc(x.name || x.entity_id)}</b>
            <span class="tm243-badge">${this.esc(String(x.type || "").toUpperCase())}</span>
            ${external ? `<span class="tm243-badge yaml">YAML MANAGED</span>` : `<span class="tm243-badge native">ESHTAYA</span>`}
          </div>
          <code>${this.esc(x.entity_id)}</code>
          <small>${this.t("Source", "المصدر")}: ${source} · ${this.esc(x.source_state || "")}${external && file ? ` · ${file}` : ""}</small>
        </div>
      </div>
      <div class="actions">
        <button class="tm243-edit" data-edit="${this.esc(x.entity_id)}" ${dis}><ha-icon icon="mdi:pencil-outline"></ha-icon>${this.t("Edit all", "تعديل الكل")}</button>
        <button class="danger" data-delete="${this.esc(x.entity_id)}" ${dis}><ha-icon icon="mdi:delete-outline"></ha-icon>${this.t("Delete", "حذف")}</button>
      </div>
    </article>`;
  };

  p._tm243SourceOptions = function () {
    const rows = this._data?.candidates || [];
    const current = this._editor?.source_entity || "";
    const values = new Set(rows.map((row) => String(row.entity_id || "")).filter(Boolean));
    if (current) values.add(current);
    return [...values].sort().map((value) => `<option value="${this.esc(value)}"></option>`).join("");
  };

  p._tm243EditorHtml = function () {
    if (!this._editor && !this._editorLoading) return "";
    if (this._editorLoading) {
      return `<div class="tm243-overlay"><div class="tm243-modal tm243-loading">
        <ha-icon icon="mdi:loading" class="spin"></ha-icon>
        <b>${this.t("Loading complete template definition…", "جاري تحميل تعريف التمبلت الكامل…")}</b>
      </div></div>`;
    }

    const e = this._editor;
    const external = Boolean(e.external_managed);
    const saving = Boolean(this._editorSaving);
    const disabled = saving ? "disabled" : "";
    const advanced = external ? `<section class="tm243-advanced">
      <div class="tm243-section-head">
        <div>
          <b>${this.t("Advanced YAML — full definition", "Advanced YAML — التعريف الكامل")}</b>
          <small>${this.t("Every supported Home Assistant template property can be edited here. The basic fields above remain authoritative for type, name, entity ID, source and unique ID.", "تقدر تعدل هون كل خصائص Template المدعومة في Home Assistant. الحقول الأساسية فوق تظل المرجع للنوع والاسم وEntity ID والمصدر وUnique ID.")}</small>
        </div>
        <span class="tm243-file"><ha-icon icon="mdi:file-code-outline"></ha-icon>${this.esc(e.generated_file || "generated YAML")}</span>
      </div>
      <textarea data-tm243-field="definition_yaml" spellcheck="false" ${disabled}>${this.esc(e.definition_yaml || "")}</textarea>
      <div class="tm243-warning"><ha-icon icon="mdi:shield-check-outline"></ha-icon><span>${this.t("Save validates YAML, checks identity conflicts, creates a backup, writes atomically and reloads Home Assistant templates. If reload fails, the file is rolled back.", "الحفظ يفحص YAML وتعارضات الهوية، ويأخذ Backup، ويكتب الملف بشكل آمن ثم يعمل Reload للـTemplates. إذا فشل الـReload يتم إرجاع الملف تلقائياً.")}</span></div>
    </section>` : `<div class="tm243-native-note"><ha-icon icon="mdi:information-outline"></ha-icon><span>${this.t("This is an Eshtaya-native wrapper, so it has no hidden YAML definition. All functional settings are editable above. Its integration-owned Unique ID is shown read-only to protect entity identity.", "هذا Wrapper داخلي من Eshtaya وما إله YAML مخفي. كل الإعدادات الوظيفية قابلة للتعديل فوق. الـUnique ID المملوك للانتجريشن ظاهر للقراءة فقط لحماية هوية الكيان.")}</span></div>`;

    return `<div class="tm243-overlay" data-tm243-backdrop>
      <div class="tm243-modal" role="dialog" aria-modal="true">
        <header class="tm243-modal-head">
          <div>
            <span>${external ? "GENERATED YAML" : "ESHTAYA NATIVE"}</span>
            <h3>${this.t("Edit managed template", "تعديل التمبلت المدار")}</h3>
            <code>${this.esc(e.managed_entity || "")}</code>
          </div>
          <button class="tm243-icon" data-tm243-cancel ${disabled}><ha-icon icon="mdi:close"></ha-icon></button>
        </header>
        ${this._editorError ? `<div class="tm243-editor-error"><ha-icon icon="mdi:alert-circle-outline"></ha-icon><span>${this.esc(this._editorError)}</span></div>` : ""}
        <section class="tm243-basic">
          <label><span>${this.t("Type", "النوع")}</span><select data-tm243-field="template_type" ${disabled}>
            <option value="light" ${e.template_type === "light" ? "selected" : ""}>Light</option>
            <option value="fan" ${e.template_type === "fan" ? "selected" : ""}>Fan</option>
          </select></label>
          <label><span>${this.t("Name", "الاسم")}</span><input data-tm243-field="name" value="${this.esc(e.name || "")}" ${disabled}></label>
          <label><span>Entity ID</span><input data-tm243-field="entity_id" value="${this.esc(e.entity_id || "")}" ${disabled}></label>
          <label><span>${this.t("Source entity", "الكيان المصدر")}</span><input data-tm243-field="source_entity" list="tm243-sources" value="${this.esc(e.source_entity || "")}" ${disabled}><datalist id="tm243-sources">${this._tm243SourceOptions()}</datalist></label>
          <label class="tm243-wide"><span>Unique ID ${external ? "" : `· ${this.t("read only", "للقراءة فقط")}`}</span><input data-tm243-field="unique_id" value="${this.esc(e.unique_id || "")}" ${external ? disabled : "disabled"}></label>
        </section>
        ${advanced}
        <footer class="tm243-footer">
          <button data-tm243-cancel ${disabled}>${this.t("Cancel", "إلغاء")}</button>
          <button class="tm243-save" data-tm243-save ${disabled}><ha-icon icon="${saving ? "mdi:loading" : "mdi:content-save-check-outline"}" class="${saving ? "spin" : ""}"></ha-icon>${saving ? this.t("Saving…", "جاري الحفظ…") : this.t("Save all changes", "حفظ كل التعديلات")}</button>
        </footer>
      </div>
    </div>`;
  };

  p._tm243Css = function () {
    return `<style>
      .tm243-titleline{display:flex;align-items:center;gap:7px;min-width:0}.tm243-titleline b{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.tm243-badge{font-size:8px;line-height:1;padding:4px 6px;border-radius:999px;border:1px solid var(--divider-color);background:var(--secondary-background-color);color:var(--secondary-text-color);font-weight:900;letter-spacing:.5px}.tm243-badge.yaml{color:var(--primary-color)}.tm243-edit{display:flex;align-items:center;gap:5px}.tm243-edit ha-icon,.actions .danger ha-icon{--mdc-icon-size:16px}.actions .danger{display:flex;align-items:center;gap:5px}
      .tm243-overlay{position:fixed;inset:0;z-index:1000;background:rgba(0,0,0,.48);display:flex;align-items:center;justify-content:center;padding:22px;box-sizing:border-box}.tm243-modal{width:min(980px,96vw);max-height:92vh;overflow:auto;border:1px solid var(--divider-color);border-radius:20px;background:var(--card-background-color);box-shadow:0 22px 70px rgba(0,0,0,.28)}.tm243-loading{width:min(460px,90vw);min-height:150px;display:flex;align-items:center;justify-content:center;gap:12px;padding:25px}.tm243-loading ha-icon{color:var(--primary-color)}
      .tm243-modal-head{position:sticky;top:0;z-index:3;display:flex;justify-content:space-between;align-items:flex-start;gap:16px;padding:18px 20px;border-bottom:1px solid var(--divider-color);background:var(--card-background-color)}.tm243-modal-head span{font-size:9px;letter-spacing:1.2px;font-weight:900;color:var(--primary-color)}.tm243-modal-head h3{margin:4px 0;font-size:21px}.tm243-modal-head code{font-size:10px;color:var(--secondary-text-color)}.tm243-icon{width:38px;height:38px;border:1px solid var(--divider-color);border-radius:10px;background:var(--secondary-background-color);color:var(--primary-text-color);cursor:pointer}
      .tm243-editor-error{margin:14px 18px 0;padding:11px 13px;border-radius:11px;border:1px solid var(--error-color);display:flex;gap:8px;align-items:flex-start;color:var(--error-color);font-size:11px}.tm243-basic{padding:18px;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.tm243-basic label{display:grid;gap:5px}.tm243-basic label span{font-size:9px;font-weight:800;color:var(--secondary-text-color)}.tm243-basic .tm243-wide{grid-column:1/-1}.tm243-basic input,.tm243-basic select{box-sizing:border-box}.tm243-basic input:disabled{opacity:.65}
      .tm243-advanced{margin:0 18px 18px;border:1px solid var(--divider-color);border-radius:15px;overflow:hidden}.tm243-section-head{padding:13px 14px;display:flex;justify-content:space-between;gap:14px;align-items:flex-start;background:var(--secondary-background-color)}.tm243-section-head>div{display:grid;gap:4px}.tm243-section-head b{font-size:12px}.tm243-section-head small{font-size:9px;line-height:1.55;color:var(--secondary-text-color);max-width:680px}.tm243-file{display:flex;gap:5px;align-items:center;white-space:nowrap;font-size:9px;color:var(--primary-color);font-weight:800}.tm243-file ha-icon{--mdc-icon-size:16px}.tm243-advanced textarea{display:block;width:100%;min-height:330px;resize:vertical;box-sizing:border-box;border:0;border-top:1px solid var(--divider-color);border-bottom:1px solid var(--divider-color);border-radius:0;padding:13px;background:var(--card-background-color);color:var(--primary-text-color);font:12px/1.55 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;direction:ltr;text-align:left;tab-size:2}.tm243-warning,.tm243-native-note{display:flex;gap:8px;align-items:flex-start;font-size:9px;line-height:1.55;color:var(--secondary-text-color)}.tm243-warning{padding:10px 12px}.tm243-warning ha-icon,.tm243-native-note ha-icon{--mdc-icon-size:17px;color:var(--primary-color);flex:none}.tm243-native-note{margin:0 18px 18px;padding:12px;border:1px solid var(--divider-color);border-radius:12px;background:var(--secondary-background-color)}
      .tm243-footer{position:sticky;bottom:0;z-index:3;display:flex;justify-content:flex-end;gap:8px;padding:13px 18px;border-top:1px solid var(--divider-color);background:var(--card-background-color)}.tm243-footer button{border:1px solid var(--divider-color);border-radius:10px;padding:10px 14px;background:var(--secondary-background-color);color:var(--primary-text-color);font-weight:900;cursor:pointer}.tm243-footer .tm243-save{display:flex;align-items:center;gap:6px;border-color:var(--primary-color);background:var(--primary-color);color:var(--text-primary-color,#fff)}.tm243-footer button:disabled,.tm243-icon:disabled{opacity:.55;cursor:default}.spin{animation:tm243spin .85s linear infinite}@keyframes tm243spin{to{transform:rotate(360deg)}}
      @media(max-width:720px){.tm243-overlay{padding:8px}.tm243-modal{width:100%;max-height:97vh;border-radius:15px}.tm243-basic{grid-template-columns:1fr}.tm243-basic .tm243-wide{grid-column:auto}.tm243-section-head{display:grid}.tm243-footer{display:grid;grid-template-columns:1fr 1.4fr}.tm243-footer button{justify-content:center}.tm243-managed{grid-template-columns:1fr!important}.tm243-managed .actions{justify-content:flex-end}}
    </style>`;
  };

  p._render = function () {
    baseRender.call(this);
    if (!this.shadowRoot) return;
    this.shadowRoot.insertAdjacentHTML("beforeend", `${this._tm243Css()}${this._tm243EditorHtml()}`);
  };

  p._openEditorV243 = async function (managedEntity) {
    if (!managedEntity || this._busy || this.migrationLocked) return;
    this._editorLoading = managedEntity;
    this._editor = null;
    this._editorError = "";
    this._render();
    try {
      this._editor = await this._call({
        type: `${ESC_TM243_DOMAIN}/template/editor/get`,
        managed_entity: managedEntity,
      }, 30000);
    } catch (err) {
      this._error = err?.message || String(err);
    } finally {
      this._editorLoading = "";
      this._render();
    }
  };

  p._closeEditorV243 = function () {
    if (this._editorSaving) return;
    this._editor = null;
    this._editorLoading = "";
    this._editorError = "";
    this._render();
  };

  p._saveEditorV243 = async function () {
    if (!this._editor || this._editorSaving || this.migrationLocked) return;
    const editor = this._editor;
    this._editorSaving = true;
    this._editorError = "";
    this._render();
    try {
      await this._call({
        type: `${ESC_TM243_DOMAIN}/template/editor/save`,
        managed_entity: editor.managed_entity,
        template_type: editor.template_type,
        name: editor.name || "",
        entity_id: editor.entity_id || "",
        source_entity: editor.source_entity || "",
        unique_id: editor.unique_id || "",
        definition_yaml: editor.definition_yaml || "",
      }, 45000);
      this._editor = null;
      this._editorSaving = false;
      await this._load(true);
      return;
    } catch (err) {
      this._editorError = err?.message || String(err);
    }
    this._editorSaving = false;
    this._render();
  };

  p._click = function (event) {
    const button = event.target.closest("button");
    if (button?.dataset.tm243Cancel !== undefined) {
      this._closeEditorV243();
      return;
    }
    if (button?.dataset.tm243Save !== undefined) {
      this._saveEditorV243();
      return;
    }
    if (button?.dataset.edit) {
      this._openEditorV243(button.dataset.edit);
      return;
    }
    baseClick.call(this, event);
  };

  p._input = function (event) {
    const field = event.target.dataset.tm243Field;
    if (field && this._editor) {
      this._editor[field] = event.target.value;
      return;
    }
    baseInput.call(this, event);
  };

  p._change = function (event) {
    const field = event.target.dataset.tm243Field;
    if (field && this._editor) {
      const previousType = this._editor.template_type;
      this._editor[field] = event.target.value;
      if (field === "template_type" && previousType !== event.target.value) {
        const current = String(this._editor.entity_id || "");
        const tail = current.includes(".") ? current.split(".").slice(1).join(".") : current;
        this._editor.entity_id = `${event.target.value}.${tail}`;
        this._render();
      }
      return;
    }
    baseChange.call(this, event);
  };
}));
