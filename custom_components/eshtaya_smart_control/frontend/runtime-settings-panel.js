const ESC_SETTINGS_DOMAIN = "eshtaya_smart_control";

class EshtayaRuntimeSettingsPanel extends HTMLElement {
  constructor(){
    super();
    this.attachShadow({mode:"open"});
    this._hass=null;
    this._language="en";
    this._manage=false;
    this._data=null;
    this._busy=false;
    this._error="";
    this._saved="";
  }
  set hass(value){const first=!this._hass;this._hass=value;if(first)this._load();}
  get hass(){return this._hass;}
  set language(value){this._language=value;this._render();}
  set manage(value){this._manage=Boolean(value);this._render();}
  get lang(){return String(this._language||this._hass?.locale?.language||"en").toLowerCase().startsWith("ar")?"ar":"en";}
  connectedCallback(){this._render();this.shadowRoot.addEventListener("click",e=>this._click(e));}
  t(en,ar){return this.lang==="ar"?ar:en;}
  esc(value){return String(value??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));}
  async _load(){
    if(!this._hass||this._busy)return;
    this._busy=true;this._render();
    try{
      this._data=await this._hass.callWS({type:`${ESC_SETTINGS_DOMAIN}/settings/get`});
      this._error="";
    }catch(error){this._error=error?.message||String(error);}
    finally{this._busy=false;this._render();}
  }
  _check(key,label,description){
    const value=Boolean(this._data?.settings?.[key]);
    return `<label class="setting check"><input type="checkbox" data-setting="${key}" ${value?"checked":""} ${!this._manage?"disabled":""}><span><b>${label}</b><small>${description}</small></span></label>`;
  }
  _number(key,label,description,min,max){
    const value=Number(this._data?.settings?.[key]??0);
    return `<label class="setting number"><span><b>${label}</b><small>${description}</small></span><input type="number" data-setting="${key}" value="${value}" min="${min}" max="${max}" ${!this._manage?"disabled":""}></label>`;
  }
  _render(){
    if(!this.shadowRoot)return;
    if(!this._data&&!this._error){
      this.shadowRoot.innerHTML=`<style>${this._css()}</style><section class="panel" dir="${this.lang==="ar"?"rtl":"ltr"}"><div class="loading">${this.t("Loading settings…","جاري تحميل الإعدادات…")}</div></section>`;
      return;
    }
    const s=this._data?.settings||{};
    this.shadowRoot.innerHTML=`<style>${this._css()}</style><section class="panel" dir="${this.lang==="ar"?"rtl":"ltr"}">
      <div class="head"><div><span>RUNTIME SETTINGS</span><h2>${this.t("Startup & Migration Settings","إعدادات بدء التشغيل والماجريشن")}</h2><p>${this.t("These are the live Eshtaya Smart Control config-entry options. Saving reloads only this integration.","هذه إعدادات Eshtaya Smart Control الفعلية. الحفظ يعيد تحميل الانتجريشن فقط.")}</p></div><button data-refresh ${this._busy?"disabled":""}><ha-icon icon="mdi:refresh"></ha-icon>${this.t("Refresh","تحديث")}</button></div>
      ${this._error?`<div class="error">${this.esc(this._error)}</div>`:""}
      ${this._saved?`<div class="saved"><ha-icon icon="mdi:check-circle-outline"></ha-icon>${this.esc(this._saved)}</div>`:""}
      <div class="section"><div class="sectionTitle"><ha-icon icon="mdi:shield-check-outline"></ha-icon><div><b>${this.t("Startup safety","حماية بدء التشغيل")}</b><small>${this.t("Controls the Multi-Way startup barrier and missing-entity Repair protection.","تتحكم بحاجز بدء التشغيل وحماية Repairs من اعتبار الكيانات مفقودة مبكراً.")}</small></div></div>
        <div class="grid">
          ${this._check("startup_wait_home_assistant",this.t("Wait for Home Assistant startup","انتظار اكتمال تشغيل Home Assistant"),this.t("Recommended. Do not activate Multi-Way before HA startup is complete.","موصى به. لا يتم تفعيل Multi-Way قبل اكتمال تشغيل Home Assistant."))}
          ${this._check("startup_wait_referenced_integrations",this.t("Wait for referenced integrations","انتظار الانتجريشنات المالكة للكيانات"),this.t("Wait for Tuya/other owners that are still loading or retrying.","ينتظر Tuya أو أي مالك للكيانات طالما ما زال يحمل أو يعيد المحاولة."))}
          ${this._number("startup_settle_seconds",this.t("Settle window (seconds)","فترة الاستقرار (ثانية)"),this.t("Extra stable time after providers become ready.","فترة استقرار إضافية بعد جاهزية المصادر."),0,120)}
          ${this._number("startup_max_wait_seconds",this.t("Maximum startup wait (seconds)","أقصى انتظار لبدء التشغيل (ثانية)"),this.t("Bounded maximum wait if a provider is broken.","حد أقصى للانتظار إذا كان أحد المصادر معطلاً."),30,900)}
          ${this._number("repair_grace_seconds",this.t("Repair grace (seconds)","مهلة Repair (ثانية)"),this.t("How long a missing entity must remain absent after startup.","مدة بقاء الكيان مفقوداً بعد التشغيل قبل اعتبار المشكلة حقيقية."),0,900)}
          ${this._number("repair_missing_confirmations",this.t("Missing confirmations","عدد تأكيدات الفقدان"),this.t("Repeated checks required before creating a Repair issue.","عدد الفحوص المتكررة المطلوبة قبل إنشاء Repair."),1,10)}
        </div>
      </div>
      <div class="section migration"><div class="sectionTitle"><ha-icon icon="mdi:swap-horizontal-bold"></ha-icon><div><b>${this.t("Legacy migration controls","إعدادات الماجريشن القديمة")}</b><small>${this.t("All legacy migration remains opt-in. Native Home Assistant Group discovery and Take Over are independent of these switches.","كل الماجريشن القديم اختياري. اكتشاف Home Assistant Groups و Take Over يعملان بشكل مستقل تماماً عن هذه الخيارات.")}</small></div></div>
        <div class="grid">
          ${this._check("legacy_migration_enabled",this.t("Enable legacy Eshtaya migration","تفعيل الماجريشن القديم"),this.t("Master switch. Keep off when your old migrations are already complete.","المفتاح الرئيسي. اتركه مغلقاً إذا كانت الماجريشنات القديمة منتهية."))}
          ${this._check("migrate_legacy_entity_manager",this.t("Migrate old Entity Manager","نقل Entity Manager القديم"),this.t("Used only when the master migration switch is enabled.","يعمل فقط عند تفعيل المفتاح الرئيسي للماجريشن."))}
          ${this._check("migrate_legacy_multiway",this.t("Migrate old Multi-Way / Smart Groups","نقل Multi-Way / Smart Groups القديمة"),this.t("Used only when the master migration switch is enabled.","يعمل فقط عند تفعيل المفتاح الرئيسي للماجريشن."))}
          ${this._check("migrate_legacy_template_manager",this.t("Migrate old Template Manager","نقل Template Manager القديم"),this.t("Destructive takeover is optional; generated YAML packages are managed automatically even when this is off.","النقل الكامل اختياري؛ ملفات YAML المولدة يتم إدارتها تلقائياً حتى لو كان هذا الخيار مغلقاً."))}
          ${this._check("legacy_hacs_cleanup",this.t("Legacy HACS cleanup","تنظيف مستودعات HACS القديمة"),this.t("Remove verified retired HACS repositories only after successful migration.","يحذف مستودعات HACS القديمة بعد نجاح الماجريشن والتحقق منه فقط."))}
          ${this._check("legacy_service_aliases",this.t("Legacy service aliases","توافق الخدمات القديمة"),this.t("Keep old eshtaya_* service domains for old automations.","يبقي أسماء خدمات eshtaya_* القديمة للتوافق مع الأوتوميشنات القديمة."))}
        </div>
      </div>
      <div class="foot"><div><ha-icon icon="mdi:information-outline"></ha-icon><span>${this.t("Generated Template Manager package files are adopted as Managed without enabling legacy migration.","ملفات Template Manager المولدة تظهر كـ Managed بدون الحاجة لتفعيل الماجريشن القديم.")}</span></div>${this._manage?`<button class="primary" data-save ${this._busy?"disabled":""}><ha-icon icon="mdi:content-save-outline"></ha-icon>${this.t("Save & reload integration","حفظ وإعادة تحميل الانتجريشن")}</button>`:`<span class="readonly">${this.t("Read-only: System Actions permission is required to change these settings.","للقراءة فقط: يلزم System Actions لتعديل هذه الإعدادات.")}</span>`}</div>
    </section>`;
  }
  async _click(event){
    const button=event.target.closest("button");if(!button)return;
    if(button.dataset.refresh!==undefined){await this._load();return;}
    if(button.dataset.save===undefined||!this._manage||this._busy)return;
    const settings={};
    for(const input of this.shadowRoot.querySelectorAll("[data-setting]")){
      settings[input.dataset.setting]=input.type==="checkbox"?input.checked:Number(input.value);
    }
    this._busy=true;this._error="";this._saved="";this._render();
    try{
      await this._hass.callWS({type:`${ESC_SETTINGS_DOMAIN}/settings/update`,settings});
      this._saved=this.t("Saved. Eshtaya Smart Control is reloading with the new settings.","تم الحفظ. يجري إعادة تحميل Eshtaya Smart Control بالإعدادات الجديدة.");
    }catch(error){this._error=error?.message||String(error);}
    finally{this._busy=false;this._render();}
  }
  _css(){return `:host{display:block;margin-top:14px}.panel{display:grid;gap:14px}.head,.section,.foot,.error,.saved{border:1px solid var(--divider-color);background:var(--card-background-color);border-radius:18px}.head{display:flex;align-items:flex-start;justify-content:space-between;gap:18px;padding:18px}.head span{font-size:9px;letter-spacing:1.2px;color:var(--primary-color);font-weight:900}.head h2{margin:5px 0;font-size:20px}.head p{margin:0;color:var(--secondary-text-color);font-size:11px;line-height:1.65}.head button,.primary{border:1px solid var(--divider-color);border-radius:10px;background:var(--secondary-background-color);color:var(--primary-text-color);padding:9px 12px;display:flex;gap:6px;align-items:center;cursor:pointer;font-weight:800}.section{padding:16px}.sectionTitle{display:flex;gap:10px;align-items:flex-start;margin-bottom:13px}.sectionTitle>ha-icon{color:var(--primary-color)}.sectionTitle div{display:grid;gap:3px}.sectionTitle b{font-size:14px}.sectionTitle small{font-size:10px;color:var(--secondary-text-color);line-height:1.55}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.setting{border:1px solid var(--divider-color);background:var(--secondary-background-color);border-radius:12px;padding:11px;min-height:58px}.setting span{display:grid;gap:3px}.setting b{font-size:11px}.setting small{font-size:9px;color:var(--secondary-text-color);line-height:1.5}.check{display:flex;gap:10px;align-items:flex-start}.check input{margin-top:3px;width:18px;height:18px;accent-color:var(--primary-color)}.number{display:grid;grid-template-columns:minmax(0,1fr) 90px;align-items:center;gap:10px}.number input{height:36px;border:1px solid var(--divider-color);border-radius:8px;background:var(--card-background-color);color:var(--primary-text-color);padding:0 8px}.foot{padding:12px 14px;display:flex;justify-content:space-between;gap:14px;align-items:center}.foot>div{display:flex;align-items:center;gap:7px;color:var(--secondary-text-color);font-size:10px;line-height:1.5}.primary{background:var(--primary-color);color:var(--text-primary-color,#fff);border:0;white-space:nowrap}.error{padding:10px 14px;color:var(--error-color);font-size:11px}.saved{padding:10px 14px;color:var(--success-color,#2e7d32);font-size:11px;display:flex;align-items:center;gap:7px}.readonly{font-size:10px;color:var(--secondary-text-color)}button:disabled,input:disabled{opacity:.55;cursor:not-allowed}.loading{padding:20px;color:var(--secondary-text-color)}@media(max-width:800px){.grid{grid-template-columns:1fr}.head,.foot{flex-direction:column}.number{grid-template-columns:minmax(0,1fr) 88px}.primary{width:100%;justify-content:center}}`;}
}

if(!customElements.get("eshtaya-runtime-settings-panel"))customElements.define("eshtaya-runtime-settings-panel",EshtayaRuntimeSettingsPanel);
