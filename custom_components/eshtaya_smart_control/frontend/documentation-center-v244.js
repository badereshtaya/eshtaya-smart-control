/* Eshtaya Smart Control v2.4.4 — resilient Documentation Center. */

const ESC_DOC244_DOMAIN = "eshtaya_smart_control";
const ESC_DOC244_PAGES = [
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

function escDoc244Text(panel, en, ar) {
  return panel._lang === "ar" ? ar : en;
}

function escDoc244Error(err) {
  return err?.message || err?.body?.message || String(err || "Unknown error");
}

function escDoc244Timeout(promise, ms = 18000) {
  let timer;
  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error("Documentation request timed out")), ms);
  });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
}

function escDoc244Inline(panel, text) {
  let value = panel._esc(String(text ?? ""));
  value = value.replace(/`([^`]+)`/g, "<code>$1</code>");
  value = value.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  value = value.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  return value;
}

function escDoc244RenderMarkdown(panel, markdown) {
  const source = String(markdown ?? "").replace(/\r\n?/g, "\n");
  if (!source.trim()) return "";

  const blocks = source.split(/```/);
  const rendered = [];
  for (let blockIndex = 0; blockIndex < blocks.length; blockIndex += 1) {
    const block = blocks[blockIndex];
    if (blockIndex % 2 === 1) {
      const lines = block.replace(/^\n/, "").split("\n");
      if (lines.length && /^[a-zA-Z0-9_+.-]+$/.test(lines[0].trim())) lines.shift();
      rendered.push(`<pre><code>${panel._esc(lines.join("\n").trimEnd())}</code></pre>`);
      continue;
    }

    const lines = block.split("\n");
    let paragraph = [];
    let listType = "";
    let listItems = [];

    const flushParagraph = () => {
      if (!paragraph.length) return;
      rendered.push(`<p>${paragraph.map(line => escDoc244Inline(panel, line)).join("<br>")}</p>`);
      paragraph = [];
    };
    const flushList = () => {
      if (!listItems.length) return;
      rendered.push(`<${listType}>${listItems.map(item => `<li>${escDoc244Inline(panel, item)}</li>`).join("")}</${listType}>`);
      listItems = [];
      listType = "";
    };

    for (const rawLine of lines) {
      const line = rawLine.trimEnd();
      const trimmed = line.trim();
      if (!trimmed) {
        flushParagraph();
        flushList();
        continue;
      }

      const heading = /^(#{1,3})\s+(.+)$/.exec(trimmed);
      if (heading) {
        flushParagraph();
        flushList();
        const level = heading[1].length;
        rendered.push(`<h${level}>${escDoc244Inline(panel, heading[2])}</h${level}>`);
        continue;
      }

      const bullet = /^[-*]\s+(.+)$/.exec(trimmed);
      const numbered = /^\d+[.)]\s+(.+)$/.exec(trimmed);
      if (bullet || numbered) {
        flushParagraph();
        const nextType = bullet ? "ul" : "ol";
        if (listType && listType !== nextType) flushList();
        listType = nextType;
        listItems.push((bullet || numbered)[1]);
        continue;
      }

      if (/^---+$/.test(trimmed)) {
        flushParagraph();
        flushList();
        rendered.push("<hr>");
        continue;
      }

      flushList();
      paragraph.push(line);
    }
    flushParagraph();
    flushList();
  }

  return rendered.join("") || `<pre class="doc244-raw">${panel._esc(source)}</pre>`;
}

function installDocumentationV244() {
  const Panel = customElements.get("eshtaya-smart-control-panel");
  if (!Panel || Panel.prototype.__eshtayaDocs244Applied) return;
  const p = Panel.prototype;
  p.__eshtayaDocs244Applied = true;

  p._docs = function () {
    if (this._doc) return this._docPage();
    const q = String(this._docSearch || "").trim().toLowerCase();
    const pages = ESC_DOC244_PAGES.filter(([slug, _icon, en, ar]) =>
      `${slug} ${en} ${ar}`.toLowerCase().includes(q),
    );
    return `<section class="pageTitle"><div class="pageIcon">${this._icon("mdi:book-open-page-variant-outline")}</div><div><span>KNOWLEDGE BASE</span><h1>${escDoc244Text(this,"Detailed Documentation","التوثيق التفصيلي")}</h1><p>${escDoc244Text(this,"Complete packaged documentation loaded through the permission-aware backend.","توثيق كامل ومضمّن داخل الإضافة ويتم تحميله من الـbackend مع احترام الصلاحيات.")}</p></div></section>
      <div class="docSearch">${this._icon("mdi:magnify")}<input data-doc-search value="${this._esc(this._docSearch || "")}" placeholder="${escDoc244Text(this,"Search documentation...","ابحث في التوثيق...")}"></div>
      <section class="docGrid">${pages.map(([slug, icon, en, ar], index) => `<button class="docCard" data-doc="${slug}"><span>${String(index + 1).padStart(2,"0")}</span>${this._icon(icon)}<b>${escDoc244Text(this,en,ar)}</b><small>${slug}.md</small></button>`).join("")}</section>`;
  };

  p._docPage = function () {
    let content;
    if (this._docLoading) {
      content = `<div class="loading">${this._icon("mdi:loading", "spin")} ${escDoc244Text(this,"Loading documentation...","جاري تحميل الشرح...")}</div>`;
    } else if (this._docError) {
      content = `<div class="doc244-error">${this._icon("mdi:alert-circle-outline")}<div><b>${escDoc244Text(this,"Documentation could not be loaded","تعذر تحميل التوثيق")}</b><span>${this._esc(this._docError)}</span><button class="ghost" data-doc-retry="${this._esc(this._doc || "")}">${escDoc244Text(this,"Retry","إعادة المحاولة")}</button></div></div>`;
    } else if (String(this._docText || "").trim()) {
      try {
        content = escDoc244RenderMarkdown(this, this._docText);
      } catch (err) {
        content = `<pre class="doc244-raw">${this._esc(this._docText)}</pre>`;
      }
    } else {
      content = `<div class="doc244-error">${this._icon("mdi:file-alert-outline")}<div><b>${escDoc244Text(this,"Documentation response was empty","ملف التوثيق رجع فارغ")}</b><span>${escDoc244Text(this,"Use Retry. If the backend still returns no content, the error will be shown here instead of a blank page.","استخدم إعادة المحاولة. إذا بقي الـbackend لا يرجع محتوى سيظهر الخطأ هنا بدل صفحة فاضية.")}</span></div></div>`;
    }

    return `<section class="docPage"><div class="docToolbar"><button class="ghost" data-action="docs-back">${this._icon(this._lang === "ar" ? "mdi:arrow-right" : "mdi:arrow-left")} ${escDoc244Text(this,"Back to index","العودة إلى الفهرس")}</button><code>${this._esc(this._doc || "")}.md</code></div><article class="markdown">${content}</article></section>`;
  };

  p._openDoc = async function (slug) {
    const requestedSlug = String(slug || "").trim().toUpperCase();
    if (!requestedSlug || !this._hass) return;
    const generation = (this.__escDoc244Generation || 0) + 1;
    this.__escDoc244Generation = generation;
    this._doc = requestedSlug;
    this._docText = "";
    this._docError = "";
    this._docLoading = true;
    this._render();

    try {
      const result = await escDoc244Timeout(
        this._hass.callWS({
          type: `${ESC_DOC244_DOMAIN}/documentation/get`,
          slug: requestedSlug,
          language: this._lang,
        }),
      );
      if (generation !== this.__escDoc244Generation || this._doc !== requestedSlug) return;
      const content = typeof result?.content === "string" ? result.content : "";
      if (!content.trim()) throw new Error("Documentation backend returned empty content");
      this._docText = content;
      this._docError = "";
    } catch (err) {
      if (generation !== this.__escDoc244Generation || this._doc !== requestedSlug) return;
      this._docText = "";
      this._docError = escDoc244Error(err);
    } finally {
      if (generation === this.__escDoc244Generation && this._doc === requestedSlug) {
        this._docLoading = false;
        this._render();
      }
    }
  };

  const baseClick = p._click;
  p._click = function (event) {
    const retry = event.target.closest?.("[data-doc-retry]");
    if (retry) {
      this._openDoc(retry.dataset.docRetry);
      return;
    }
    return baseClick?.call(this, event);
  };

  const baseCss = p._css;
  p._css = function () {
    return `${baseCss.call(this)}
      .doc244-error{display:grid;grid-template-columns:auto 1fr;gap:12px;align-items:start;padding:15px;border:1px solid color-mix(in srgb,var(--error-color) 45%,var(--divider-color));background:color-mix(in srgb,var(--error-color) 7%,var(--card-background-color));border-radius:14px}.doc244-error>ha-icon{color:var(--error-color)}.doc244-error>div{display:grid;gap:7px}.doc244-error b{font-size:13px}.doc244-error span{font-size:10px;color:var(--secondary-text-color);overflow-wrap:anywhere}.doc244-error button{justify-self:start}.doc244-raw{white-space:pre-wrap;overflow:auto}.markdown ul,.markdown ol{padding-inline-start:24px}.markdown hr{border:0;border-top:1px solid var(--divider-color);margin:24px 0}.markdown em{font-style:italic}`;
  };
}

customElements.whenDefined("eshtaya-smart-control-panel").then(() =>
  queueMicrotask(() =>
    queueMicrotask(() =>
      queueMicrotask(() =>
        queueMicrotask(installDocumentationV244),
      ),
    ),
  ),
);
