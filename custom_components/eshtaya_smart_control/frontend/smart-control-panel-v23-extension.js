/* Eshtaya Smart Control v2.3.1 Template Manager shell integration.
 *
 * The canonical v2.1 permission layer now knows template.view/template.manage.
 * Keep this extension focused only on the actual Template Manager page and child
 * wiring so navigation, module cards and docs have one source of truth.
 */
const ESC_V23_DOMAIN="eshtaya_smart_control";
const esc23Can=(panel,permission)=>Boolean(panel._access?.permissions?.includes(permission));
const esc23Txt=(panel,en,ar)=>panel._lang==="ar"?ar:en;

customElements.whenDefined("eshtaya-smart-control-panel").then(()=>queueMicrotask(()=>{
  const Panel=customElements.get("eshtaya-smart-control-panel");
  if(!Panel||Panel.prototype.__eshtayaV23Applied)return;
  const p=Panel.prototype;p.__eshtayaV23Applied=true;
  const baseLoad=p._load,baseBody=p._body,baseWire=p._wireChild,baseCss=p._css;

  p._load=async function(){
    await baseLoad.call(this);
    if(esc23Can(this,"template.view")){
      try{this._templateOverview=await this._hass.callWS({type:`${ESC_V23_DOMAIN}/template/snapshot`});}
      catch(_){this._templateOverview=null;}
    }else{
      this._templateOverview=null;
    }
    this._render();
  };

  p._body=function(){
    if(this._view==="template"){
      if(!esc23Can(this,"template.view"))return this._noAccess?.()||"";
      return this._tool(
        "mdi:swap-horizontal-bold",
        esc23Txt(this,"Template Manager","إدارة الكيانات الدائمة"),
        esc23Txt(this,"Create permanent Light/Fan entities from physical switches, migrate the legacy method safely, edit mappings and recover missing sources.","إنشاء كيانات Light/Fan دائمة من المفاتيح الفعلية، نقل الطريقة القديمة بأمان، تعديل الربط واستعادة المصادر المفقودة."),
        `<eshtaya-template-manager-panel></eshtaya-template-manager-panel>`
      );
    }
    return baseBody.call(this);
  };

  p._wireChild=function(){
    baseWire.call(this);
    const child=this.shadowRoot?.querySelector("eshtaya-template-manager-panel");
    if(child&&this._hass){child.hass=this._hass;try{child.language=this._lang;}catch(_){}}
  };

  p._css=function(){return `${baseCss.call(this)}.v23TemplateModule{margin-top:12px}@media(max-width:900px){.v23TemplateModule .module{grid-column:1/-1}}`;};
}));
