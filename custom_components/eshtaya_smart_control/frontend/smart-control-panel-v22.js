import "./tuya-control.js";
import "./entity/eshtaya-entity-manager-panel-loader.js";
import "./multiway/panel.js";

const DOMAIN = "eshtaya_smart_control";
const STATIC = "/eshtaya_smart_control_static";
const VERSION = "2.2.0";

const VIEW_PERMISSION = {
  dashboard: "dashboard.view", entity: "entity.view", tuya: "tuya.view",
  multi: "multi.view", docs: "docs.view", system: "system.view", access: "access.manage",
};

const DOCS = [
  ["GETTING_STARTED","mdi:rocket-launch-outline","Getting Started","البدء والتثبيت"],
  ["DASHBOARD","mdi:view-dashboard-outline","Dashboard","لوحة التحكم"],
  ["ENTITY_CONTROL","mdi:account-eye-outline","Entity & Alexa Control","إدارة الكيانات وأليكسا"],
  ["TUYA_CONTROL","mdi:cloud-cog-outline","Tuya Control","إدارة تويا"],
  ["MULTIWAY","mdi:electric-switch","Multi-Way","التحكم متعدد النقاط"],
  ["SMART_GROUPS","mdi:lightbulb-group-outline","Smart Groups","المجموعات الذكية"],
  ["COMMISSIONING","mdi:tools","Commissioning","التجهيز والـCommissioning"],
  ["SYSTEM_CENTER","mdi:heart-pulse","System Center","مركز النظام"],
  ["ACCESS_CONTROL","mdi:account-key-outline","Home Assistant Access Control","صلاحيات Home Assistant"],
  ["MIGRATION","mdi:swap-horizontal-bold","Migration","الهجرة"],
  ["ARCHITECTURE","mdi:sitemap-outline","Architecture","البنية التقنية"],
  ["SECURITY_BACKUP","mdi:shield-lock-outline","Security & Backup","الأمان والنسخ الاحتياطي"],
  ["TROUBLESHOOTING","mdi:lifebuoy","Troubleshooting","حل المشاكل"],
];

const PERMISSION_LABELS = {
  "dashboard.view":["Dashboard","لوحة التحكم"], "entity.view":["Entity: View","الكيانات: مشاهدة"],
  "entity.manage":["Entity: Manage","الكيانات: إدارة"], "tuya.view":["Tuya: View","تويا: مشاهدة"],
  "tuya.control":["Tuya: Control","تويا: تحكم"], "tuya.configure":["Tuya: Configure","تويا: إعداد الحساب"],
  "multi.view":["Multi-Way: View","Multi-Way: مشاهدة"], "multi.control":["Multi-Way: Control","Multi-Way: تحكم"],
  "multi.manage":["Multi-Way: Manage","Multi-Way: إدارة"], "docs.view":["Documentation","التوثيق"],
  "system.view":["System: View","النظام: مشاهدة"], "system.actions":["System: Actions","النظام: إجراءات"],
  "system.reports":["System: Reports","النظام: تقارير"], "access.manage":["Eshtaya Access","إدارة صلاحيات Eshtaya"],
};

function readType(type="") {
  return /(?:\/status|\/list|\/get|\/activity|\/diagnostics|\/details|\/shadow_props|\/bulk_details|\/repair\/missing|\/ha_groups|\/export|\/report|\/snapshot|config\/.+\/list)$/.test(type)
    || ["eshtaya_smart_control/overview","eshtaya_smart_control/access/current","eshtaya_smart_control/documentation/get","eshtaya_smart_control/migration_report","eshtaya_smart_control/system_report"].includes(type);
}
function timeoutFor(type="") { return type.includes("/tuya/") ? 38000 : 18000; }
function sleep(ms){ return new Promise(r=>setTimeout(r,ms)); }

async function safeWS(hass, payload, opts={}) {
  const timeout = opts.timeout ?? timeoutFor(payload?.type || "");
  const retries = opts.retries ?? (readType(payload?.type || "") ? 1 : 0);
  let last;
  for(let attempt=0; attempt<=retries; attempt++){
    let timer;
    try{
      const result = await Promise.race([
        hass.callWS(payload),
        new Promise((_,reject)=>{ timer=setTimeout(()=>reject(new Error(`WebSocket timeout: ${payload?.type || "request"}`)), timeout); }),
      ]);
      clearTimeout(timer);
      return result;
    }catch(err){
      clearTimeout(timer); last=err;
      if(attempt<retries) await sleep(250*(attempt+1));
    }
  }
  throw last;
}

function resilientHass(raw) {
  if(!raw) return raw;
  return new Proxy(raw, {
    get(target, prop, receiver){
      if(prop === "callWS") return (payload)=>safeWS(target,payload);
      const value=Reflect.get(target,prop,receiver);
      return typeof value === "function" ? value.bind(target) : value;
    }
  });
}

function hardenMultiWayPanel(){
  const C=customElements.get("eshtaya-multiway-panel");
  if(!C || C.prototype.__escV22Stable) return;
  const p=C.prototype; p.__escV22Stable=true;

  p._bootstrap = async function(){
    this.__escBooting=true;
    const results=await Promise.allSettled([this._loadCatalog(),this._loadNativeGroups(),this._refresh(true)]);
    const rejected=results.filter(x=>x.status==="rejected");
    if(rejected.length) this.__escLoadError=rejected.map(x=>x.reason?.message||String(x.reason)).join(" · ");
    try{
      this._unsubscribe=await this._hass.connection.subscribeEvents(()=>{
        clearTimeout(this.__escEventTimer);
        this.__escEventTimer=setTimeout(()=>this._refresh(false),300);
      },`${DOMAIN}/multiway_event`);
    }catch(_){ /* manual refresh remains available */ }
    this._loading=false; this.__escBooting=false; this._render();
  };

  p._refresh = async function(includeActivity=false){
    if(!this._hass) return;
    if(this.__escRefreshPromise){ this.__escRefreshPending=this.__escRefreshPending||includeActivity; return this.__escRefreshPromise; }
    const run=async()=>{
      const core=await Promise.allSettled([
        this._hass.callWS({type:`${DOMAIN}/multiway/list`}),
        this._hass.callWS({type:`${DOMAIN}/multiway/smart/list`}),
        this._hass.callWS({type:`${DOMAIN}/multiway/repair/missing`}),
      ]);
      const errors=[];
      if(core[0].status==="fulfilled") this._data=core[0].value; else errors.push(core[0].reason);
      if(core[1].status==="fulfilled") this._smart=core[1].value; else errors.push(core[1].reason);
      if(core[2].status==="fulfilled") this._missing=core[2].value?.missing||[]; else errors.push(core[2].reason);
      if(includeActivity || this._tab==="activity"){
        const extra=await Promise.allSettled([
          this._hass.callWS({type:`${DOMAIN}/multiway/activity`,limit:200}),
          this._hass.callWS({type:`${DOMAIN}/multiway/smart/diagnostics`}),
        ]);
        if(extra[0].status==="fulfilled") this._activity=extra[0].value?.activity||[]; else errors.push(extra[0].reason);
        if(extra[1].status==="fulfilled") this._smartActivity=extra[1].value?.activity||[]; else errors.push(extra[1].reason);
      }
      this.__escLoadError=errors.length ? errors.map(x=>x?.message||String(x)).join(" · ") : "";
      if(!this._loading&&!this._editing&&!this._smartEditing&&!this._testResult&&!this._settingsDirty) this._render();
    };
    this.__escRefreshPromise=run().finally(()=>{
      this.__escRefreshPromise=null;
      if(this.__escRefreshPending){ const again=this.__escRefreshPending; this.__escRefreshPending=false; setTimeout(()=>this._refresh(!!again),120); }
    });
    return this.__escRefreshPromise;
  };
}
hardenMultiWayPanel();

class EshtayaSmartControlPanelV22 extends HTMLElement {
  constructor(){
    super(); this.attachShadow({mode:"open"});
    this._hass=null; this._safeHass=null; this._profile=null; this._bootError=""; this._booting=false;
    this._view="dashboard"; this._overview=null; this._overviewError=""; this._overviewLoading=false;
    this._langMode=localStorage.getItem("eshtayaSmartControlLang")||"auto";
    this._doc=null; this._docText=""; this._docSearch=""; this._toast="";
    this._haAccess=null; this._integrationAccess=null; this._accessLoading=false; this._accessError="";
    this._haSelected=""; this._haDraft=null; this._haEntityQ="";
  }
  set hass(v){ const first=!this._hass; this._hass=v; this._safeHass=resilientHass(v); if(first)this._boot(); else this._wireChild(); }
  get hass(){return this._hass;}
  set panel(v){this._panel=v;} set narrow(v){this._narrow=v;}
  connectedCallback(){ this._render(); this.shadowRoot.addEventListener("click",e=>this._click(e)); this.shadowRoot.addEventListener("change",e=>this._change(e)); this.shadowRoot.addEventListener("input",e=>this._input(e)); }
  get _lang(){ if(this._langMode!=="auto")return this._langMode; return String(this._hass?.locale?.language||this._hass?.language||"en").toLowerCase().startsWith("ar")?"ar":"en"; }
  _tr(en,ar){return this._lang==="ar"?ar:en;}
  _can(p){return !!this._profile?.permissions?.includes(p);}
  _allowed(v){const p=VIEW_PERMISSION[v];return p?this._can(p):false;}
  _first(){return ["dashboard","entity","tuya","multi","docs","system","access"].find(v=>this._allowed(v))||"none";}
  _esc(v){return String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));}
  _icon(i){return `<ha-icon icon="${i}"></ha-icon>`;}
  _setLang(){if(this._langMode==="auto")delete window.__ESHTAYA_SMART_LANG__;else window.__ESHTAYA_SMART_LANG__=this._langMode;}

  async _boot(){
    if(!this._hass||this._booting)return; this._booting=true; this._bootError=""; this._render();
    try{
      this._profile=await safeWS(this._hass,{type:`${DOMAIN}/access/current`},{timeout:12000,retries:1});
      if(!this._allowed(this._view))this._view=this._first();
      this._booting=false; this._render();
      this._loadOverview();
      if(this._profile?.is_admin||this._can("access.manage")) this._loadAccess(false);
    }catch(e){this._bootError=e?.message||String(e);this._booting=false;this._render();}
  }
  async _loadOverview(){
    if(!this._can("dashboard.view")||this._overviewLoading)return; this._overviewLoading=true; this._render();
    try{this._overview=await safeWS(this._hass,{type:`${DOMAIN}/overview`},{timeout:15000,retries:1});this._overviewError="";}
    catch(e){this._overviewError=e?.message||String(e);}finally{this._overviewLoading=false;this._render();}
  }
  async _loadAccess(render=true){
    if(this._accessLoading)return; this._accessLoading=true;if(render)this._render();
    const jobs=[]; const keys=[];
    if(this._profile?.is_admin){keys.push("ha");jobs.push(safeWS(this._hass,{type:`${DOMAIN}/ha_access/snapshot`},{timeout:20000,retries:1}));}
    if(this._can("access.manage")){keys.push("integration");jobs.push(safeWS(this._hass,{type:`${DOMAIN}/access/snapshot`},{timeout:18000,retries:1}));}
    const results=await Promise.allSettled(jobs); const errors=[];
    results.forEach((r,i)=>{if(r.status==="fulfilled"){if(keys[i]==="ha")this._haAccess=r.value;else this._integrationAccess=r.value;}else errors.push(r.reason?.message||String(r.reason));});
    this._accessError=errors.join(" · "); this._accessLoading=false; this._ensureHaDraft(); if(render)this._render();
  }

  _render(){
    if(!this.shadowRoot)return;this._setLang();const rtl=this._lang==="ar";
    this.shadowRoot.innerHTML=`<style>${this._css()}</style><div class="app" dir="${rtl?"rtl":"ltr"}">${this._header()}${this._profile?this._nav():""}<main>${this._toast?`<div class="toast">${this._esc(this._toast)}</div>`:""}${this._body()}</main></div>`;this._wireChild();
  }
  _header(){return `<header><button class="brand" data-view="dashboard"><img src="${STATIC}/assets/logo.png?v=${VERSION}"><span><b>Eshtaya Smart Control</b><small>${this._tr("Stable unified Home Assistant control platform","منصة Home Assistant الموحدة والمستقرة")}</small></span></button><div class="top"><span class="version">v${VERSION}</span><select data-lang><option value="auto" ${this._langMode==="auto"?"selected":""}>${this._tr("Auto","تلقائي")}</option><option value="ar" ${this._langMode==="ar"?"selected":""}>العربية</option><option value="en" ${this._langMode==="en"?"selected":""}>English</option></select><button class="iconBtn" data-action="global-refresh">${this._icon("mdi:refresh")}</button></div></header>`;}
  _nav(){const all=[["dashboard","mdi:view-dashboard-outline",this._tr("Dashboard","لوحة التحكم")],["entity","mdi:account-eye-outline",this._tr("Entity & Alexa","الكيانات وأليكسا")],["tuya","mdi:cloud-cog-outline",this._tr("Tuya","تويا")],["multi","mdi:home-switch-outline",this._tr("Groups","الجروبات")],["docs","mdi:book-open-page-variant-outline",this._tr("Documentation","التوثيق")],["system","mdi:heart-pulse",this._tr("System","النظام")],["access","mdi:account-key-outline",this._tr("Access Control","الصلاحيات")]].filter(([v])=>this._allowed(v));return `<nav>${all.map(([v,i,l])=>`<button data-view="${v}" class="${this._view===v?"active":""}>${this._icon(i)}<span>${l}</span></button>`).join("")}</nav>`;}
  _body(){
    if(this._booting)return this._center("mdi:loading",this._tr("Loading secure profile…","جاري تحميل ملف الصلاحيات…"),"");
    if(this._bootError)return this._center("mdi:alert-circle-outline",this._tr("Control Hub could not initialize","تعذر تشغيل مركز التحكم"),this._bootError,true);
    if(!this._profile||this._view==="none")return this._center("mdi:shield-lock-outline",this._tr("No access assigned","لا توجد صلاحيات مخصصة"),this._tr("Ask a Home Assistant administrator to assign access.","اطلب من مدير Home Assistant إعطاء هذا المستخدم صلاحيات."));
    if(!this._allowed(this._view))return this._center("mdi:shield-lock-outline",this._tr("Access denied","غير مسموح"),"");
    if(this._view==="entity")return this._tool("mdi:account-eye-outline",this._tr("Entity & Alexa Control","إدارة الكيانات وأليكسا"),`<eshtaya-entity-manager-panel></eshtaya-entity-manager-panel>`);
    if(this._view==="tuya")return this._tool("mdi:cloud-cog-outline",this._tr("Tuya Cloud Control","إدارة تويا السحابية"),`<eshtaya-tuya-control></eshtaya-tuya-control>`);
    if(this._view==="multi")return this._tool("mdi:home-switch-outline",this._tr("Multi-Way & Smart Groups","Multi-Way والمجموعات الذكية"),`<eshtaya-multiway-panel></eshtaya-multiway-panel>`);
    if(this._view==="docs")return this._docs(); if(this._view==="system")return this._system(); if(this._view==="access")return this._access(); return this._dashboard();
  }
  _center(icon,title,desc,retry=false){return `<section class="center">${this._icon(icon)}<h1>${this._esc(title)}</h1><p>${this._esc(desc)}</p>${retry?`<button class="primary" data-action="retry-boot">${this._tr("Retry","إعادة المحاولة")}</button>`:""}</section>`;}
  _tool(icon,title,body){return `<section class="pageTitle"><div>${this._icon(icon)}</div><span><small>ESHTAYA SMART · v${VERSION}</small><h1>${title}</h1></span></section>${body}`;}

  _dashboard(){
    const o=this._overview||{},h=o.health||{},e=o.entity?.stats||{},m=o.multiway||{},s=o.smart_groups||{},t=o.tuya||{};
    const cards=[];
    if(this._can("entity.view"))cards.push(this._module("entity","mdi:account-eye-outline",this._tr("Entity & Alexa","الكيانات وأليكسا"),`${e.total??"—"}`));
    if(this._can("tuya.view"))cards.push(this._module("tuya","mdi:cloud-cog-outline",this._tr("Tuya Cloud","تويا"),t.configured===true?this._tr("Activated","مفعلة"):t.configured===false?this._tr("Not activated","غير مفعلة"):"—"));
    if(this._can("multi.view"))cards.push(this._module("multi","mdi:home-switch-outline",this._tr("Groups","الجروبات"),`${m.groups??0} + ${s.groups??0}`));
    if(this._can("docs.view"))cards.push(this._module("docs","mdi:book-open-page-variant-outline",this._tr("Documentation","التوثيق"),`${DOCS.length}`));
    if(this._can("system.view"))cards.push(this._module("system","mdi:heart-pulse",this._tr("System Center","مركز النظام"),h.score!=null?`${h.score}/100`:"—"));
    if(this._allowed("access"))cards.push(this._module("access","mdi:account-key-outline",this._tr("Access Control","الصلاحيات"),this._profile?.is_admin?this._tr("Home Assistant + Eshtaya","Home Assistant + Eshtaya"):this._tr("Eshtaya modules","أقسام Eshtaya")));
    return `<section class="hero"><div><span class="pill">${this._icon("mdi:shield-check-outline")} v${VERSION} STABLE CORE</span><h1>${this._tr("One control hub. Independent modules.","مركز واحد، وكل قسم يعمل بشكل مستقل.")}</h1><p>${this._tr("A Tuya cloud timeout no longer blocks Groups or Entity/Alexa. Every module has bounded WebSocket requests and independent recovery.","تعطل أو تأخر Tuya Cloud لم يعد يوقف الجروبات أو الكيانات/Alexa. كل قسم له تحميل واسترجاع مستقل.")}</p></div><div class="score"><strong>${h.score??"—"}</strong><small>${this._tr("Health score","صحة النظام")}</small></div></section>${this._overviewError?`<div class="alert"><span>${this._esc(this._overviewError)}</span><button data-action="overview-retry">${this._tr("Retry overview","إعادة تحميل النظرة العامة")}</button></div>`:""}${this._overviewLoading&&!this._overview?`<div class="thinLoading">${this._tr("Loading overview…","جاري تحميل النظرة العامة…")}</div>`:""}<section class="moduleGrid">${cards.join("")}</section>`;
  }
  _module(view,icon,title,status){return `<article class="module" data-view="${view}"><div>${this._icon(icon)}<span>${this._esc(status)}</span></div><h2>${title}</h2><button data-view="${view}">${this._tr("Open","فتح")} ${this._icon(this._lang==="ar"?"mdi:arrow-left":"mdi:arrow-right")}</button></article>`;}

  _docs(){if(this._doc)return this._docPage();const q=this._docSearch.trim().toLowerCase();const docs=DOCS.filter(([s,_i,en,ar])=>`${s} ${en} ${ar}`.toLowerCase().includes(q));return `${this._tool("mdi:book-open-page-variant-outline",this._tr("Complete Documentation Center","مركز التوثيق الكامل"),"")}<div class="docSearch">${this._icon("mdi:magnify")}<input data-doc-search value="${this._esc(this._docSearch)}" placeholder="${this._tr("Search all guides…","ابحث في كل الأدلة…")}"></div><section class="docGrid">${docs.map(([slug,icon,en,ar],i)=>`<button class="docCard" data-doc="${slug}"><span>${String(i+1).padStart(2,"0")}</span>${this._icon(icon)}<b>${this._lang==="ar"?ar:en}</b><small>${slug}</small></button>`).join("")}</section>`;}
  _docPage(){return `<section class="docPage"><div class="docToolbar"><button class="ghost" data-action="docs-back">${this._icon(this._lang==="ar"?"mdi:arrow-right":"mdi:arrow-left")} ${this._tr("Back","رجوع")}</button><code>${this._esc(this._doc)}</code></div><article class="markdown">${this._docText?this._markdown(this._docText):`<div class="thinLoading">${this._tr("Loading full guide…","جاري تحميل الدليل الكامل…")}</div>`}</article></section>`;}
  async _openDoc(slug){this._doc=slug;this._docText="";this._render();try{const r=await safeWS(this._hass,{type:`${DOMAIN}/documentation/get`,slug,language:this._lang},{timeout:15000,retries:1});this._docText=r.content||"";}catch(e){this._docText=`# ${this._tr("Could not load documentation","تعذر تحميل التوثيق")}\n\n${e?.message||e}\n\n${this._tr("Use Retry/Refresh after checking Home Assistant connectivity.","استخدم التحديث بعد التأكد من اتصال Home Assistant.")}`;}this._render();}
  _markdown(md){let x=this._esc(md);x=x.replace(/```([\s\S]*?)```/g,(_,v)=>`<pre><code>${v.trim()}</code></pre>`).replace(/^#### (.+)$/gm,"<h4>$1</h4>").replace(/^### (.+)$/gm,"<h3>$1</h3>").replace(/^## (.+)$/gm,"<h2>$1</h2>").replace(/^# (.+)$/gm,"<h1>$1</h1>").replace(/\*\*(.+?)\*\*/g,"<strong>$1</strong>").replace(/`([^`]+)`/g,"<code>$1</code>").replace(/^[-*] (.+)$/gm,"<li>$1</li>").replace(/^\d+\. (.+)$/gm,"<li>$1</li>").replace(/\n{2,}/g,"</p><p>").replace(/\n/g,"<br>");return `<p>${x}</p>`;}

  _system(){const o=this._overview||{},h=o.health||{},actions=[];if(this._can("system.actions")){if(this._can("entity.manage"))actions.push(["repair_alexa_files","mdi:file-sync-outline",this._tr("Repair Alexa files","إصلاح ملفات أليكسا")]);if(this._can("tuya.view"))actions.push(["refresh_tuya","mdi:cloud-refresh-outline",this._tr("Refresh Tuya","تحديث تويا")]);if(this._can("multi.control"))actions.push(["sync_groups","mdi:sync",this._tr("Sync groups","مزامنة الجروبات")]);}return `${this._tool("mdi:heart-pulse",this._tr("System Center","مركز النظام"),"")}<section class="systemGrid"><article class="panel"><h2>${this._tr("Health","الصحة")}</h2><strong class="big">${h.score??"—"}</strong><p>${this._overviewError?this._esc(this._overviewError):this._tr("Operational overview is loaded independently from every module.","النظرة العامة تُحمّل بشكل مستقل عن كل قسم.")}</p><button class="ghost" data-action="overview-retry">${this._tr("Refresh health","تحديث الصحة")}</button></article><article class="panel"><h2>${this._tr("Safe actions","إجراءات النظام")}</h2><div class="actionGrid">${actions.map(([a,i,l])=>`<button data-sys="${a}" ${a==="sync_groups"?'data-physical="1"':''}>${this._icon(i)}<span>${l}</span></button>`).join("")}${this._can("system.reports")?`<button data-action="system-report">${this._icon("mdi:file-download-outline")}<span>${this._tr("System report","تقرير النظام")}</span></button>`:""}</div></article></section>`;}
  async _systemAction(action,physical=false){if(physical&&!confirm(this._tr("This can send real commands to devices. Continue?","هذا الإجراء قد يرسل أوامر فعلية للأجهزة. متابعة؟")))return;try{await safeWS(this._hass,{type:`${DOMAIN}/system_action`,action,confirm_physical:!!physical},{timeout:40000,retries:0});this._say(this._tr("Action completed","تم تنفيذ الإجراء"));this._loadOverview();}catch(e){this._say(`${this._tr("Action failed","فشل الإجراء")}: ${e?.message||e}`);}}
  async _download(type,name){try{const data=await safeWS(this._hass,{type:`${DOMAIN}/${type}`},{timeout:25000,retries:1});const b=new Blob([JSON.stringify(data,null,2)],{type:"application/json"});const u=URL.createObjectURL(b),a=document.createElement("a");a.href=u;a.download=`eshtaya-${name}-${new Date().toISOString().replace(/[:.]/g,"-")}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);}catch(e){this._say(e?.message||String(e));}}

  _access(){
    if(this._accessLoading&&!this._haAccess&&!this._integrationAccess)return this._center("mdi:loading",this._tr("Loading access data…","جاري تحميل الصلاحيات…"),"");
    if(!this._haAccess&&!this._integrationAccess&&!this._accessLoading){setTimeout(()=>this._loadAccess(),0);}
    return `${this._tool("mdi:account-key-outline",this._tr("Access Control Center","مركز الصلاحيات"),"")}${this._accessError?`<div class="alert"><span>${this._esc(this._accessError)}</span><button data-action="access-retry">${this._tr("Retry","إعادة المحاولة")}</button></div>`:""}${this._profile?.is_admin?this._haAccessSection():""}${this._can("access.manage")?this._integrationAccessSection():""}`;
  }
  _ensureHaDraft(){
    if(!this._haAccess)return;const users=this._haAccess.users||[];if(!users.length)return;
    if(!users.some(u=>u.id===this._haSelected))this._haSelected=(users.find(u=>!u.is_owner&&!u.system_generated)?.id)||users[0].id;
    const u=users.find(x=>x.id===this._haSelected);if(!u)return;
    if(!this._haDraft||this._haDraft.user_id!==u.id){let mode=u.mode;if(!mode||mode==="restored"){if(u.is_admin)mode="administrator";else if((u.group_ids||[]).includes("system-read-only"))mode="read_only";else mode="standard";}this._haDraft={user_id:u.id,mode,rules:JSON.parse(JSON.stringify(u.rules||{base:"none",domains:{},areas:{},entities:{}}))};this._haDraft.rules.base??="none";this._haDraft.rules.domains??={};this._haDraft.rules.areas??={};this._haDraft.rules.entities??={};}
  }
  _haAccessSection(){
    if(!this._haAccess)return `<section class="panel"><div class="thinLoading">${this._tr("Loading native Home Assistant permissions…","جاري تحميل صلاحيات Home Assistant الأصلية…")}</div></section>`;
    this._ensureHaDraft();const snap=this._haAccess,users=snap.users||[],u=users.find(x=>x.id===this._haSelected),d=this._haDraft||{},rules=d.rules||{};const currentId=this._hass?.user?.id;
    const userList=users.map(x=>`<button class="userPick ${x.id===this._haSelected?"active":""}" data-ha-user="${this._esc(x.id)}"><span><b>${this._esc(x.name)}</b><small>${x.is_owner?"OWNER":x.is_admin?"ADMIN":this._esc(x.mode||x.group_ids?.join(", ")||"USER")}</small></span>${x.managed?this._icon("mdi:shield-key-outline"):""}</button>`).join("");
    if(!u)return "";const immutable=u.is_owner||u.system_generated||u.id===currentId;const restricted=d.mode==="restricted";
    const modeOptions=[["standard",this._tr("Standard User · all entities","مستخدم عادي · كل الكيانات")],["read_only",this._tr("Read Only · all entities","قراءة فقط · كل الكيانات")],["restricted",this._tr("Restricted · custom entity policy","مقيد · سياسة كيانات مخصصة")],["no_entity_access",this._tr("No entity access","بدون وصول للكيانات")]];if(this._profile?.is_owner)modeOptions.push(["administrator",this._tr("Administrator","مدير")]);
    return `<section class="nativeAccess"><div class="sectionHead"><div><span>HOME ASSISTANT NATIVE PERMISSIONS</span><h2>${this._tr("Whole-system entity access","صلاحيات الكيانات على مستوى Home Assistant")}</h2><p>${this._tr("Backend enforced by Home Assistant for entity Read / Control / Edit. Owner is protected and original groups are backed up before the first change.","تُطبق من Backend Home Assistant نفسه على قراءة/تحكم/تعديل الكيانات. الـOwner محمي ويتم حفظ المجموعات الأصلية قبل أول تعديل.")}</p></div><span class="badge success">${snap.compatibility?.custom_restricted_groups?"NATIVE POLICY READY":"BUILT-IN ONLY"}</span></div><div class="haAccessGrid"><aside>${userList}</aside><article class="accessEditor"><div class="editorHead"><div><h3>${this._esc(u.name)}</h3><small>${this._esc((u.group_ids||[]).join(" · "))}</small></div>${u.has_backup?`<button class="ghost" data-ha-restore="${this._esc(u.id)}" ${immutable?"disabled":""}>${this._icon("mdi:backup-restore")} ${this._tr("Restore original","استرجاع الأصلي")}</button>`:""}</div>${immutable?`<div class="notice">${u.is_owner?this._tr("Owner access cannot be modified.","لا يمكن تعديل صلاحيات الـOwner."):this._tr("You cannot change your own access from this panel.","لا يمكنك تعديل صلاحيات حسابك من نفس اللوحة.")}</div>`:`<label class="field">${this._tr("Home Assistant access mode","وضع صلاحيات Home Assistant")}<select data-ha-mode>${modeOptions.map(([v,l])=>`<option value="${v}" ${d.mode===v?"selected":""}>${l}</option>`).join("")}</select></label>${restricted?this._restrictedEditor(rules,snap):""}<button class="primary full" data-ha-save="${this._esc(u.id)}">${this._icon("mdi:shield-check-outline")} ${this._tr("Apply native HA access","تطبيق صلاحيات Home Assistant")}</button>`}<div class="nativeLimit"><b>${this._tr("Core limitation","حدود Home Assistant الحالية")}</b><p>${this._tr("Native custom policies are additive grants and cover entity read/control/edit. Home Assistant does not currently provide general custom deny rules or per-service/dashboard RBAC through its public permission model.","السياسات الأصلية هي صلاحيات سماح تراكمية وتغطي قراءة/تحكم/تعديل الكيانات. Home Assistant لا يوفر حالياً Deny عام أو RBAC مخصص لكل Service/Dashboard ضمن نموذج الصلاحيات العام.")}</p></div></article></div></section>`;
  }
  _restrictedEditor(rules,snap){
    const level=(val,attr)=>`<select ${attr}>${[["none",this._tr("None","بدون")],["read",this._tr("Read","قراءة")],["control",this._tr("Control","تحكم")],["edit",this._tr("Edit","تعديل")]].map(([v,l])=>`<option value="${v}" ${val===v?"selected":""}>${l}</option>`).join("")}</select>`;
    const domains=Object.entries(rules.domains||{}).map(([k,v])=>`<div class="scopeRow"><code>${this._esc(k)}</code>${level(v,`data-ha-domain-level="${this._esc(k)}"`)}<button data-ha-remove-domain="${this._esc(k)}">×</button></div>`).join("");
    const areas=Object.entries(rules.areas||{}).map(([k,v])=>`<div class="scopeRow"><code>${this._esc((snap.areas||[]).find(a=>a.id===k)?.name||k)}</code>${level(v,`data-ha-area-level="${this._esc(k)}"`)}<button data-ha-remove-area="${this._esc(k)}">×</button></div>`).join("");
    const entities=Object.entries(rules.entities||{}).map(([k,v])=>`<div class="scopeRow"><code>${this._esc(k)}</code>${level(v,`data-ha-entity-level="${this._esc(k)}"`)}<button data-ha-remove-entity="${this._esc(k)}">×</button></div>`).join("");
    const availableDomains=(snap.domains||[]).filter(x=>!(x in (rules.domains||{})));const availableAreas=(snap.areas||[]).filter(x=>!(x.id in (rules.areas||{})));
    const q=this._haEntityQ.trim().toLowerCase();const entityMatches=q?(snap.entities||[]).filter(x=>!(x.entity_id in (rules.entities||{}))&&`${x.entity_id} ${x.name}`.toLowerCase().includes(q)).slice(0,12):[];
    return `<div class="restricted"><label class="field">${this._tr("Base access for all entities","الصلاحية الأساسية لكل الكيانات")}${level(rules.base||"none","data-ha-base")}</label><div class="scopeGrid"><section><h4>${this._tr("Domain grants","صلاحيات حسب النوع")}</h4>${domains}<div class="adder"><select data-ha-new-domain><option value="">${this._tr("Choose domain…","اختر النوع…")}</option>${availableDomains.map(x=>`<option value="${this._esc(x)}">${this._esc(x)}</option>`).join("")}</select><button data-ha-add-domain>+</button></div></section><section><h4>${this._tr("Area grants","صلاحيات حسب المنطقة")}</h4>${areas}<div class="adder"><select data-ha-new-area><option value="">${this._tr("Choose area…","اختر المنطقة…")}</option>${availableAreas.map(x=>`<option value="${this._esc(x.id)}">${this._esc(x.name)}</option>`).join("")}</select><button data-ha-add-area>+</button></div></section><section class="entityScope"><h4>${this._tr("Specific entity grants","صلاحيات كيانات محددة")}</h4>${entities}<input data-ha-entity-search value="${this._esc(this._haEntityQ)}" placeholder="${this._tr("Search entity ID or name…","ابحث عن الكيان بالاسم أو ID…")}">${entityMatches.length?`<div class="entityMatches">${entityMatches.map(x=>`<button data-ha-add-entity="${this._esc(x.entity_id)}"><b>${this._esc(x.name)}</b><code>${this._esc(x.entity_id)}</code></button>`).join("")}</div>`:""}</section></div><p class="hint">${this._tr("Specific grants have lookup priority, but Home Assistant merges grants permissively. Do not use a broad Control grant if you need a narrower scope to be Read-only.","الكيان المحدد له أولوية بحث أعلى، لكن Home Assistant يدمج صلاحيات السماح بالأوسع. لا تمنح Control بشكل واسع إذا أردت جزءاً أضيق Read-only.")}</p></div>`;
  }

  _integrationAccessSection(){
    const s=this._integrationAccess;if(!s)return `<section class="panel"><div class="thinLoading">${this._tr("Loading Eshtaya module permissions…","جاري تحميل صلاحيات أقسام Eshtaya…")}</div></section>`;
    const roles=s.roles||{},users=(s.users||[]).filter(u=>!u.is_admin&&!u.system_generated);return `<section class="integrationAccess"><div class="sectionHead"><div><span>ESHTAYA MODULE PERMISSIONS</span><h2>${this._tr("Control Hub module access","صلاحيات أقسام Eshtaya")}</h2><p>${this._tr("This second layer controls Eshtaya screens and actions; it is separate from native Home Assistant entity access above.","هذه طبقة ثانية تتحكم بشاشات وإجراءات Eshtaya وهي منفصلة عن صلاحيات كيانات Home Assistant أعلاه.")}</p></div></div><div class="roleUsers">${users.map(u=>{const role=u.assignment?.role||s.settings?.default_role||"no_access";return `<div class="roleUser" data-int-user="${this._esc(u.id)}"><span><b>${this._esc(u.name)}</b><small>${this._esc((u.effective_permissions||[]).map(p=>this._permLabel(p)).join(" · ")||this._tr("No module access","بدون صلاحية للأقسام"))}</small></span><select data-int-role>${Object.entries(roles).map(([id,r])=>`<option value="${this._esc(id)}" ${role===id?"selected":""}>${this._esc(r.name||id)}</option>`).join("")}</select><button data-int-save="${this._esc(u.id)}">${this._tr("Save","حفظ")}</button></div>`;}).join("")}</div><details class="customRoles"><summary>${this._tr("Create a custom Eshtaya role","إنشاء دور Eshtaya مخصص")}</summary><div class="customRoleForm"><input data-role-id placeholder="lighting_operator"><input data-role-name placeholder="${this._tr("Role name","اسم الدور")}"><div class="permGrid">${(s.permissions||[]).map(p=>`<label><input type="checkbox" data-role-perm="${this._esc(p)}">${this._esc(this._permLabel(p))}</label>`).join("")}</div><button class="primary" data-role-save>${this._tr("Create role","إنشاء الدور")}</button></div></details></section>`;
  }
  _permLabel(p){const x=PERMISSION_LABELS[p]||[p,p];return this._lang==="ar"?x[1]:x[0];}
  async _saveHa(userId){try{await safeWS(this._hass,{type:`${DOMAIN}/ha_access/apply`,user_id:userId,mode:this._haDraft.mode,rules:this._haDraft.rules},{timeout:20000,retries:0});this._say(this._tr("Home Assistant access applied","تم تطبيق صلاحيات Home Assistant"));this._haDraft=null;await this._loadAccess();}catch(e){this._say(`${this._tr("Access update failed","فشل تعديل الصلاحيات")}: ${e?.message||e}`);}}
  async _restoreHa(userId){if(!confirm(this._tr("Restore the original Home Assistant groups captured before Eshtaya changed this user?","استرجاع مجموعات Home Assistant الأصلية المحفوظة قبل تعديل هذا المستخدم؟")))return;try{await safeWS(this._hass,{type:`${DOMAIN}/ha_access/restore`,user_id:userId},{timeout:20000,retries:0});this._say(this._tr("Original access restored","تم استرجاع الصلاحيات الأصلية"));this._haDraft=null;await this._loadAccess();}catch(e){this._say(e?.message||String(e));}}
  async _saveIntegrationUser(userId){const row=[...this.shadowRoot.querySelectorAll("[data-int-user]")].find(x=>x.dataset.intUser===userId);const role=row?.querySelector("[data-int-role]")?.value||"no_access";const old=(this._integrationAccess?.users||[]).find(u=>u.id===userId)?.assignment||{};try{await safeWS(this._hass,{type:`${DOMAIN}/access/assign_user`,user_id:userId,role,allow:old.allow||[],deny:old.deny||[],expires_at:old.expires_at||null},{timeout:15000,retries:0});this._say(this._tr("Eshtaya role saved","تم حفظ دور Eshtaya"));await this._loadAccess();}catch(e){this._say(e?.message||String(e));}}
  async _saveCustomRole(){const id=this.shadowRoot.querySelector("[data-role-id]")?.value?.trim()||"",name=this.shadowRoot.querySelector("[data-role-name]")?.value?.trim()||id,permissions=[...this.shadowRoot.querySelectorAll("[data-role-perm]:checked")].map(x=>x.dataset.rolePerm);if(!id){this._say(this._tr("Role ID is required","معرف الدور مطلوب"));return;}try{await safeWS(this._hass,{type:`${DOMAIN}/access/save_role`,role_id:id,name,permissions},{timeout:15000,retries:0});this._say(this._tr("Custom role created","تم إنشاء الدور"));await this._loadAccess();}catch(e){this._say(e?.message||String(e));}}

  _wireChild(){const child=this.shadowRoot?.querySelector("eshtaya-entity-manager-panel,eshtaya-tuya-control,eshtaya-multiway-panel");if(child&&this._safeHass){child.hass=this._safeHass;try{child.language=this._lang;}catch(_){}}}
  _say(v){this._toast=String(v||"");this._render();clearTimeout(this.__toastTimer);this.__toastTimer=setTimeout(()=>{this._toast="";this._render();},3600);}
  _click(e){const t=e.target.closest("[data-view],[data-action],[data-sys],[data-doc],[data-ha-user],[data-ha-save],[data-ha-restore],[data-ha-add-domain],[data-ha-remove-domain],[data-ha-add-area],[data-ha-remove-area],[data-ha-add-entity],[data-ha-remove-entity],[data-int-save],[data-role-save]");if(!t)return;
    if(t.dataset.view){if(!this._allowed(t.dataset.view)){this._say(this._tr("Access denied","غير مسموح"));return;}this._view=t.dataset.view;this._doc=null;if(this._view==="access")this._loadAccess(false);if(this._view==="system")this._loadOverview();this._render();return;}
    if(t.dataset.doc){this._openDoc(t.dataset.doc);return;} if(t.dataset.sys){this._systemAction(t.dataset.sys,t.dataset.physical==="1");return;}
    if(t.dataset.action==="retry-boot"){this._boot();return;}if(t.dataset.action==="global-refresh"){this._loadOverview();if(this._view==="access")this._loadAccess();const child=this.shadowRoot.querySelector("eshtaya-entity-manager-panel,eshtaya-tuya-control,eshtaya-multiway-panel");child?._load?.(false);child?._loadStatus?.();child?._refresh?.(true);return;}if(t.dataset.action==="overview-retry"){this._loadOverview();return;}if(t.dataset.action==="access-retry"){this._loadAccess();return;}if(t.dataset.action==="docs-back"){this._doc=null;this._docText="";this._render();return;}if(t.dataset.action==="system-report"){this._download("system_report","system-report");return;}
    if(t.dataset.haUser){this._haSelected=t.dataset.haUser;this._haDraft=null;this._haEntityQ="";this._ensureHaDraft();this._render();return;}if(t.dataset.haSave){this._saveHa(t.dataset.haSave);return;}if(t.dataset.haRestore){this._restoreHa(t.dataset.haRestore);return;}
    if(t.hasAttribute("data-ha-add-domain")){const v=this.shadowRoot.querySelector("[data-ha-new-domain]")?.value;if(v){this._haDraft.rules.domains[v]="read";this._render();}return;}if(t.dataset.haRemoveDomain){delete this._haDraft.rules.domains[t.dataset.haRemoveDomain];this._render();return;}if(t.hasAttribute("data-ha-add-area")){const v=this.shadowRoot.querySelector("[data-ha-new-area]")?.value;if(v){this._haDraft.rules.areas[v]="read";this._render();}return;}if(t.dataset.haRemoveArea){delete this._haDraft.rules.areas[t.dataset.haRemoveArea];this._render();return;}if(t.dataset.haAddEntity){this._haDraft.rules.entities[t.dataset.haAddEntity]="read";this._haEntityQ="";this._render();return;}if(t.dataset.haRemoveEntity){delete this._haDraft.rules.entities[t.dataset.haRemoveEntity];this._render();return;}
    if(t.dataset.intSave){this._saveIntegrationUser(t.dataset.intSave);return;}if(t.hasAttribute("data-role-save")){this._saveCustomRole();return;}
  }
  _change(e){const x=e.target;if(x.matches("[data-lang]")){this._langMode=x.value;localStorage.setItem("eshtayaSmartControlLang",x.value);this._doc=null;this._render();return;}if(x.matches("[data-ha-mode]")){this._haDraft.mode=x.value;if(x.value==="restricted"&&!this._haDraft.rules)this._haDraft.rules={base:"none",domains:{},areas:{},entities:{}};this._render();return;}if(x.matches("[data-ha-base]")){this._haDraft.rules.base=x.value;return;}if(x.dataset.haDomainLevel){this._haDraft.rules.domains[x.dataset.haDomainLevel]=x.value;return;}if(x.dataset.haAreaLevel){this._haDraft.rules.areas[x.dataset.haAreaLevel]=x.value;return;}if(x.dataset.haEntityLevel){this._haDraft.rules.entities[x.dataset.haEntityLevel]=x.value;return;}}
  _input(e){const x=e.target;if(x.matches("[data-doc-search]")){this._docSearch=x.value;this._render();const i=this.shadowRoot.querySelector("[data-doc-search]");i?.focus();return;}if(x.matches("[data-ha-entity-search]")){this._haEntityQ=x.value;this._render();const i=this.shadowRoot.querySelector("[data-ha-entity-search]");if(i){i.focus();i.setSelectionRange(i.value.length,i.value.length);}return;}}

  _css(){return `:host{display:block;width:100%;min-height:100%;color:var(--primary-text-color);background:var(--primary-background-color)}*{box-sizing:border-box}button,input,select{font:inherit}.app{min-height:100vh;background:var(--primary-background-color)}header{height:74px;position:sticky;top:0;z-index:50;display:flex;align-items:center;justify-content:space-between;gap:12px;padding:0 clamp(12px,2.5vw,34px);background:color-mix(in srgb,var(--card-background-color) 94%,transparent);border-bottom:1px solid var(--divider-color);backdrop-filter:blur(16px)}.brand{border:0;background:none;color:inherit;display:flex;align-items:center;gap:10px;text-align:inherit;min-width:0;cursor:pointer}.brand img{width:48px;height:48px;object-fit:contain;border-radius:13px}.brand span{display:grid;min-width:0}.brand b{font-size:15px}.brand small{font-size:9px;color:var(--secondary-text-color);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.top{display:flex;gap:7px;align-items:center}.version,.top select,.iconBtn{border:1px solid var(--divider-color);background:var(--secondary-background-color);color:inherit;border-radius:10px;padding:8px}.version{font-size:9px;font-weight:900}.iconBtn{width:38px;height:38px;cursor:pointer}nav{position:sticky;top:74px;z-index:45;display:flex;gap:5px;padding:8px clamp(9px,2.5vw,34px);overflow:auto;background:color-mix(in srgb,var(--card-background-color) 92%,transparent);border-bottom:1px solid var(--divider-color);backdrop-filter:blur(12px)}nav button{border:0;background:none;color:var(--secondary-text-color);border-radius:10px;padding:8px 11px;display:flex;align-items:center;gap:6px;white-space:nowrap;cursor:pointer;font-size:10px;font-weight:800}nav button.active{background:color-mix(in srgb,var(--primary-color) 11%,var(--secondary-background-color));color:var(--primary-color)}nav ha-icon{--mdc-icon-size:18px}main{width:min(1800px,100%);margin:auto;padding:clamp(13px,2.6vw,34px)}.toast{position:fixed;bottom:20px;inset-inline-end:20px;z-index:100;background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:13px;padding:12px 15px;box-shadow:0 15px 45px rgba(0,0,0,.25);max-width:460px}.center{min-height:60vh;display:grid;place-items:center;align-content:center;text-align:center;gap:10px}.center>ha-icon{--mdc-icon-size:50px;color:var(--primary-color)}.center h1{margin:0;font-size:28px}.center p{max-width:650px;color:var(--secondary-text-color);line-height:1.7}.primary,.ghost{border-radius:11px;padding:10px 13px;cursor:pointer;font-weight:800;display:inline-flex;align-items:center;justify-content:center;gap:6px}.primary{border:0;background:var(--primary-color);color:#fff}.ghost{border:1px solid var(--divider-color);background:var(--card-background-color);color:inherit}.full{width:100%}.hero{min-height:330px;border:1px solid var(--divider-color);border-radius:28px;padding:clamp(25px,5vw,58px);display:grid;grid-template-columns:1fr 220px;gap:25px;align-items:center;background:linear-gradient(135deg,color-mix(in srgb,#171827 96%,var(--card-background-color)),color-mix(in srgb,#0c1c29 93%,var(--card-background-color)));color:#fff}.pill{display:inline-flex;gap:6px;align-items:center;font-size:9px;font-weight:900;border:1px solid rgba(255,255,255,.15);border-radius:999px;padding:7px 10px}.hero h1{font-size:clamp(34px,5vw,68px);line-height:1.04;margin:16px 0}.hero p{color:#cbd5e1;line-height:1.7;max-width:850px}.score{display:grid;place-items:center}.score strong{font-size:60px}.score small{color:#cbd5e1}.moduleGrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:11px;margin-top:13px}.module{border:1px solid var(--divider-color);background:var(--card-background-color);border-radius:19px;padding:18px;min-height:180px;cursor:pointer}.module>div{display:flex;justify-content:space-between;align-items:center}.module>div>ha-icon{--mdc-icon-size:29px;color:var(--primary-color)}.module>div>span{font-size:10px;color:var(--secondary-text-color)}.module h2{margin:27px 0;font-size:18px}.module button{border:0;background:none;color:var(--primary-color);padding:0;display:flex;gap:5px;align-items:center;cursor:pointer;font-weight:800}.alert{display:flex;justify-content:space-between;align-items:center;gap:10px;border:1px solid color-mix(in srgb,var(--error-color) 35%,var(--divider-color));background:color-mix(in srgb,var(--error-color) 6%,var(--card-background-color));padding:11px 13px;border-radius:13px;margin:12px 0;font-size:10px}.alert button{border:0;background:none;color:var(--primary-color);font-weight:900;cursor:pointer}.thinLoading{padding:18px;text-align:center;color:var(--secondary-text-color)}.pageTitle{display:flex;gap:13px;align-items:center;margin-bottom:18px}.pageTitle>div{width:54px;height:54px;border-radius:16px;display:grid;place-items:center;background:var(--secondary-background-color)}.pageTitle>div ha-icon{--mdc-icon-size:29px;color:var(--primary-color)}.pageTitle span{display:grid}.pageTitle small{color:var(--secondary-text-color);font-size:9px}.pageTitle h1{margin:3px 0 0;font-size:clamp(27px,4vw,43px)}.docSearch{display:flex;align-items:center;gap:8px;border:1px solid var(--divider-color);background:var(--card-background-color);border-radius:14px;padding:0 12px}.docSearch input{flex:1;border:0;background:none;color:inherit;outline:none;padding:13px 0}.docGrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:10px;margin-top:12px}.docCard{position:relative;border:1px solid var(--divider-color);background:var(--card-background-color);color:inherit;border-radius:17px;padding:18px;text-align:inherit;display:grid;gap:10px;cursor:pointer;min-height:150px}.docCard>span{position:absolute;inset-inline-end:13px;top:13px;color:var(--disabled-text-color);font-size:9px}.docCard>ha-icon{--mdc-icon-size:28px;color:var(--primary-color)}.docCard small{color:var(--secondary-text-color);font-size:8px}.docPage{max-width:1250px;margin:auto}.docToolbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}.markdown{border:1px solid var(--divider-color);background:var(--card-background-color);border-radius:20px;padding:clamp(20px,4vw,46px);font-size:13px;line-height:1.85}.markdown h1{font-size:32px}.markdown h2{font-size:23px;margin-top:35px}.markdown h3{font-size:18px;margin-top:28px}.markdown code{background:var(--secondary-background-color);border-radius:6px;padding:2px 5px}.markdown pre{overflow:auto;padding:12px;background:var(--code-editor-background-color,#111827);border-radius:10px}.markdown li{margin:5px 0}.systemGrid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.panel,.nativeAccess,.integrationAccess{border:1px solid var(--divider-color);background:var(--card-background-color);border-radius:20px;padding:19px;margin-bottom:13px}.panel h2{margin-top:0}.big{font-size:48px;color:var(--primary-color)}.panel p{color:var(--secondary-text-color);line-height:1.6}.actionGrid{display:grid;grid-template-columns:1fr 1fr;gap:8px}.actionGrid button{border:1px solid var(--divider-color);background:var(--secondary-background-color);color:inherit;border-radius:12px;padding:12px;display:flex;align-items:center;gap:7px;cursor:pointer}.sectionHead{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;margin-bottom:15px}.sectionHead span{font-size:9px;letter-spacing:1px;color:var(--secondary-text-color);font-weight:900}.sectionHead h2{margin:5px 0;font-size:20px}.sectionHead p{margin:0;color:var(--secondary-text-color);font-size:10px;line-height:1.6;max-width:900px}.badge{padding:6px 8px;border-radius:999px;background:var(--secondary-background-color);font-size:8px;font-weight:900;white-space:nowrap}.badge.success{color:var(--success-color,#43a047)}.haAccessGrid{display:grid;grid-template-columns:290px minmax(0,1fr);gap:12px}.haAccessGrid aside{display:flex;flex-direction:column;gap:6px;max-height:720px;overflow:auto}.userPick{border:1px solid var(--divider-color);background:var(--secondary-background-color);color:inherit;border-radius:12px;padding:10px;text-align:inherit;display:flex;justify-content:space-between;align-items:center;gap:8px;cursor:pointer}.userPick.active{border-color:var(--primary-color);background:color-mix(in srgb,var(--primary-color) 9%,var(--secondary-background-color))}.userPick span{display:grid;min-width:0}.userPick b{font-size:11px;overflow:hidden;text-overflow:ellipsis}.userPick small{font-size:8px;color:var(--secondary-text-color);overflow:hidden;text-overflow:ellipsis}.accessEditor{border:1px solid var(--divider-color);border-radius:15px;padding:15px;background:var(--secondary-background-color)}.editorHead{display:flex;justify-content:space-between;align-items:start;gap:10px}.editorHead h3{margin:0}.editorHead small{font-size:8px;color:var(--secondary-text-color)}.field{display:grid;gap:6px;margin:13px 0;font-size:10px;font-weight:800}.field select,.adder select,.entityScope input,.roleUser select,.customRoleForm input,.scopeRow select{border:1px solid var(--divider-color);background:var(--card-background-color);color:inherit;border-radius:9px;padding:9px;outline:none}.notice,.nativeLimit,.hint{border:1px solid var(--divider-color);border-radius:11px;padding:10px;margin-top:12px;color:var(--secondary-text-color);font-size:9px;line-height:1.6}.nativeLimit b{color:var(--primary-text-color)}.scopeGrid{display:grid;grid-template-columns:1fr 1fr;gap:10px}.scopeGrid section{border:1px solid var(--divider-color);border-radius:12px;padding:11px;background:var(--card-background-color)}.scopeGrid h4{margin:0 0 9px}.entityScope{grid-column:1/-1}.scopeRow{display:grid;grid-template-columns:minmax(0,1fr) 120px 28px;gap:5px;align-items:center;margin:5px 0}.scopeRow code{font-size:9px;overflow:hidden;text-overflow:ellipsis}.scopeRow button,.adder button{border:1px solid var(--divider-color);background:var(--secondary-background-color);color:inherit;border-radius:8px;cursor:pointer}.adder{display:grid;grid-template-columns:1fr 32px;gap:5px;margin-top:7px}.entityScope input{width:100%;margin-top:7px}.entityMatches{display:grid;gap:4px;margin-top:5px;max-height:220px;overflow:auto}.entityMatches button{border:1px solid var(--divider-color);background:var(--secondary-background-color);color:inherit;border-radius:8px;padding:7px;text-align:inherit;display:grid;cursor:pointer}.entityMatches b{font-size:9px}.entityMatches code{font-size:8px;color:var(--secondary-text-color)}.roleUsers{display:grid;gap:6px}.roleUser{display:grid;grid-template-columns:minmax(0,1fr) 200px 70px;gap:8px;align-items:center;border-top:1px solid var(--divider-color);padding:9px 0}.roleUser span{display:grid;min-width:0}.roleUser b{font-size:11px}.roleUser small{font-size:8px;color:var(--secondary-text-color);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.roleUser button{border:0;background:var(--primary-color);color:#fff;border-radius:8px;padding:9px;cursor:pointer}.customRoles{margin-top:14px;border:1px solid var(--divider-color);border-radius:12px;padding:10px}.customRoles summary{cursor:pointer;font-weight:800;font-size:10px}.customRoleForm{display:grid;gap:8px;margin-top:10px}.permGrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:5px}.permGrid label{font-size:9px;display:flex;gap:5px;align-items:center}@media(max-width:900px){.hero{grid-template-columns:1fr}.score{justify-items:start}.systemGrid,.haAccessGrid{grid-template-columns:1fr}.haAccessGrid aside{max-height:260px}.scopeGrid{grid-template-columns:1fr}.entityScope{grid-column:auto}.brand small{max-width:240px}}@media(max-width:600px){header{height:66px}.brand img{width:40px;height:40px}.brand small{display:none}nav{top:66px}.top .version{display:none}main{padding:11px}.hero{border-radius:20px;padding:24px}.hero h1{font-size:38px}.systemGrid{grid-template-columns:1fr}.actionGrid{grid-template-columns:1fr}.roleUser{grid-template-columns:1fr}.scopeRow{grid-template-columns:minmax(0,1fr) 105px 28px}.sectionHead{display:grid}.docGrid{grid-template-columns:1fr}}`;}
}

if(!customElements.get("eshtaya-smart-control-panel-v22")) customElements.define("eshtaya-smart-control-panel-v22",EshtayaSmartControlPanelV22);
