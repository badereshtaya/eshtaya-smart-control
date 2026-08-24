/* Eshtaya Smart Control v2.3 Template Manager shell integration. */
const ESC_V23_DOMAIN="eshtaya_smart_control";
const esc23Can=(panel,permission)=>Boolean(panel._access?.permissions?.includes(permission));
const esc23Txt=(panel,en,ar)=>panel._lang==="ar"?ar:en;

customElements.whenDefined("eshtaya-smart-control-panel").then(()=>queueMicrotask(()=>{
  const Panel=customElements.get("eshtaya-smart-control-panel");
  if(!Panel||Panel.prototype.__eshtayaV23Applied)return;
  const p=Panel.prototype;p.__eshtayaV23Applied=true;
  const baseLoad=p._load,baseBody=p._body,baseDashboard=p._dashboardV21||p._dashboard,baseWire=p._wireChild,baseDocs=p._docs,baseCss=p._css;

  p._load=async function(){
    const wanted=this._view;
    await baseLoad.call(this);
    if(esc23Can(this,"template.view")){
      try{this._templateOverview=await this._hass.callWS({type:`${ESC_V23_DOMAIN}/template/snapshot`});}catch(_){this._templateOverview=null;}
      if(wanted==="template")this._view="template";
    }
    this._render();
  };

  p._nav=function(){
    const items=[
      ["dashboard","mdi:view-dashboard-outline",this._t("dashboard"),"dashboard.view"],
      ["entity","mdi:account-eye-outline",this._t("entity"),"entity.view"],
      ["tuya","mdi:cloud-cog-outline",this._t("tuya"),"tuya.view"],
      ["multi","mdi:home-switch-outline",this._t("multi"),"multi.view"],
      ["template","mdi:swap-horizontal-bold",esc23Txt(this,"Template Manager","الكيانات الدائمة"),"template.view"],
      ["docs","mdi:book-open-page-variant-outline",this._t("docs"),"docs.view"],
      ["system","mdi:heart-pulse",this._t("system"),"system.view"],
      ["access","mdi:account-key-outline",esc23Txt(this,"Access Control","الصلاحيات"),"access.manage"],
    ].filter(x=>esc23Can(this,x[3]));
    return `<nav>${items.map(([v,i,l])=>`<button data-view="${v}" class="${this._view===v?"active":""}">${this._icon(i)}<span>${l}</span></button>`).join("")}</nav>`;
  };

  p._body=function(){
    if(this._view==="template"){
      if(!esc23Can(this,"template.view"))return this._noAccess?.()||"";
      return this._tool("mdi:swap-horizontal-bold",esc23Txt(this,"Template Manager","إدارة الكيانات الدائمة"),esc23Txt(this,"Create permanent Light/Fan entities from Tuya switches, edit mappings and recover missing sources.","إنشاء كيانات Light/Fan دائمة من مفاتيح Tuya وتعديل الربط واستعادة المصادر المفقودة."),`<eshtaya-template-manager-panel></eshtaya-template-manager-panel>`);
    }
    return baseBody.call(this);
  };

  p._dashboardV21=function(){
    const html=baseDashboard.call(this);
    if(!esc23Can(this,"template.view"))return html;
    const s=this._templateOverview||{};
    const card=this._module("template","mdi:swap-horizontal-bold",esc23Txt(this,"Template Manager","الكيانات الدائمة"),esc23Txt(this,"Permanent Tuya-backed Light/Fan entities with automatic legacy migration and source recovery.","كيانات Light/Fan دائمة مرتبطة بتويا مع نقل تلقائي للطريقة القديمة واستعادة المصادر."),`${s.managed_count??0} ${esc23Txt(this,"managed","مدار")}`,"cyan");
    return `${html}<section class="moduleGrid v23TemplateModule">${card}</section>`;
  };

  p._docs=function(){
    const html=baseDocs.call(this);
    if(this._doc)return html;
    return `${html}<section class="docGrid v23Docs"><button class="docCard" data-doc="TEMPLATE_MANAGER"><span>14</span><div class="docIcon">${this._icon("mdi:swap-horizontal-bold")}</div><b>${esc23Txt(this,"Template Manager","إدارة الكيانات الدائمة")}</b><small>TEMPLATE_MANAGER.md</small></button></section>`;
  };

  p._wireChild=function(){
    baseWire.call(this);
    const child=this.shadowRoot?.querySelector("eshtaya-template-manager-panel");
    if(child&&this._hass){child.hass=this._hass;try{child.language=this._lang;}catch(_){}}
  };

  p._css=function(){return `${baseCss.call(this)}.v23TemplateModule{margin-top:12px}.v23TemplateModule .module{grid-column:span 4}.v23Docs{margin-top:12px}@media(max-width:900px){.v23TemplateModule .module{grid-column:1/-1}}`;};
}));
