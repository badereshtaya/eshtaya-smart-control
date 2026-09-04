/* Eshtaya Smart Control v2.4.4 — frontend regression recovery.
 *
 * v2.4.3 used Element.insertAdjacentHTML() on a ShadowRoot. ShadowRoot extends
 * DocumentFragment, not Element, so browsers can throw before Template Manager
 * reaches its WebSocket scan. The base markup is already written at that point,
 * leaving the visible counters at their default zero values.
 *
 * This layer restores safe ShadowRoot insertion, makes Template Manager data
 * loading independent from enhancement rendering, suppresses no-op language
 * renders, exposes generated-YAML scan errors, and preserves the Template Manager
 * view across shell reconnects.
 */

const ESC_V244_DOMAIN = "eshtaya_smart_control";

function escV244Error(err) {
  return err?.message || err?.body?.message || String(err || "Unknown error");
}

function installShadowRootInsertAdjacentHtml() {
  if (typeof ShadowRoot === "undefined") return;
  if (typeof ShadowRoot.prototype.insertAdjacentHTML === "function") return;

  Object.defineProperty(ShadowRoot.prototype, "insertAdjacentHTML", {
    configurable: true,
    writable: true,
    value(position, html) {
      if (position !== "beforeend" && position !== "afterbegin") {
        throw new DOMException(
          "ShadowRoot compatibility insertion supports afterbegin/beforeend only",
          "NotSupportedError",
        );
      }
      const template = document.createElement("template");
      template.innerHTML = String(html ?? "");
      const fragment = template.content.cloneNode(true);
      if (position === "afterbegin") {
        this.insertBefore(fragment, this.firstChild);
      } else {
        this.appendChild(fragment);
      }
    },
  });
}

installShadowRootInsertAdjacentHtml();

customElements.whenDefined("eshtaya-template-manager-panel").then(() =>
  queueMicrotask(() => {
    const Panel = customElements.get("eshtaya-template-manager-panel");
    if (!Panel || Panel.prototype.__eshtayaV244RecoveryApplied) return;
    const p = Panel.prototype;
    p.__eshtayaV244RecoveryApplied = true;
    const enhancedRender = p._render;

    Object.defineProperty(p, "language", {
      configurable: true,
      get() {
        return this._language;
      },
      set(value) {
        const next = value || "";
        if (this._language === next) return;
        this._language = next;
        try {
          this._render();
        } catch (err) {
          console.error("Eshtaya Template Manager language render failed", err);
        }
      },
    });

    p._render = function () {
      const result = enhancedRender.call(this);
      if (!this.shadowRoot) return result;

      // "Managed" now means all definitions known to the manager, including a
      // mapping whose source is currently Missing. Missing remains separately
      // visible in its own counter/tab.
      const managedStat = this.shadowRoot.querySelector(".stats article:first-child b");
      if (managedStat && Number.isFinite(Number(this._data?.defined_count))) {
        managedStat.textContent = String(Number(this._data.defined_count));
      }

      const diagnostics = this._data?.generated_scan;
      const failures = Array.isArray(diagnostics?.files)
        ? diagnostics.files.filter(file => file?.exists && file?.ok === false)
        : [];
      if (failures.length) {
        const wrap = this.shadowRoot.querySelector(".wrap");
        if (wrap && !wrap.querySelector(".esc-v244-scan-error")) {
          const banner = document.createElement("div");
          banner.className = "error esc-v244-scan-error";
          banner.style.cssText = "padding:12px 14px;display:grid;gap:5px";
          const title = document.createElement("b");
          title.textContent = this.t(
            "One or more generated Template YAML files could not be parsed. Existing mappings were preserved.",
            "تعذر قراءة ملف أو أكثر من ملفات Template YAML. تم الحفاظ على الربط السابق ولم يتم حذفه.",
          );
          banner.appendChild(title);
          for (const failure of failures) {
            const line = document.createElement("code");
            line.textContent = `${failure.file}: ${failure.error || "scan failed"}`;
            banner.appendChild(line);
          }
          wrap.prepend(banner);
        }
      }
      return result;
    };

    p._load = async function (scan = false) {
      if (!this._hass || this._busy) return;
      this._busy = true;

      const safeRender = () => {
        try {
          this._render();
          this.__escV244RenderError = "";
        } catch (err) {
          this.__escV244RenderError = escV244Error(err);
          console.error("Eshtaya Template Manager render failed", err);
        }
      };

      // A renderer problem must never block the backend scan again.
      safeRender();
      try {
        this._data = await this._call(
          {type: `${ESC_V244_DOMAIN}/template/${scan ? "scan" : "snapshot"}`},
          25000,
        );
        this._error = "";
      } catch (err) {
        this._error = escV244Error(err);
      } finally {
        this._busy = false;
        safeRender();
      }
    };
  }),
);

customElements.whenDefined("eshtaya-smart-control-panel").then(() =>
  queueMicrotask(() =>
    queueMicrotask(() => {
      const Panel = customElements.get("eshtaya-smart-control-panel");
      if (!Panel || Panel.prototype.__eshtayaV244ViewRecoveryApplied) return;
      const p = Panel.prototype;
      p.__eshtayaV244ViewRecoveryApplied = true;
      const baseLoad = p._load;

      p._load = async function (...args) {
        const requestedView = this._view;
        const result = await baseLoad.apply(this, args);
        if (
          requestedView === "template" &&
          this._access?.permissions?.includes("template.view") &&
          this._view !== "template"
        ) {
          this._view = "template";
          this._render();
        }
        return result;
      };
    }),
  ),
);
