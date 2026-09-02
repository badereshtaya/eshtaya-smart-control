/* Eshtaya Smart Control v2.4.2 System Center settings integration. */
const ESC_V242_CAN=(panel,permission)=>Boolean(panel._access?.permissions?.includes(permission));

customElements.whenDefined("eshtaya-smart-control-panel").then(()=>queueMicrotask(()=>{
  const Panel=customElements.get("eshtaya-smart-control-panel");
  if(!Panel||Panel.prototype.__eshtayaV242Applied)return;
  const p=Panel.prototype;p.__eshtayaV242Applied=true;
  const baseSystem=p._systemV21;
  const baseWire=p._wireChild;

  p._systemV21=function(){
    const html=baseSystem.call(this);
    if(!ESC_V242_CAN(this,"system.view"))return html;
    return `${html}<eshtaya-runtime-settings-panel></eshtaya-runtime-settings-panel>`;
  };

  p._wireChild=function(){
    baseWire.call(this);
    const settings=this.shadowRoot?.querySelector("eshtaya-runtime-settings-panel");
    if(settings&&this._hass){
      settings.hass=this._hass;
      settings.language=this._lang;
      settings.manage=ESC_V242_CAN(this,"system.actions");
    }
  };
}));
