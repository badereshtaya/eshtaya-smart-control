/* Eshtaya Smart Control v2.4.1 hotfixes.
 *
 * 1) Tuya account fields must never be erased by routine Home Assistant state
 *    updates. The shell rewires child components whenever `hass` changes and the
 *    historical Tuya language setter re-rendered unconditionally. Preserve draft
 *    form values/focus across any legitimate render and skip no-op language renders.
 * 2) Documentation lives in the packaged integration docs directory, not under
 *    the frontend static directory. Load it through the existing permission-aware
 *    WebSocket endpoint instead of a broken static fetch path.
 */

const ESC_V241_DOMAIN = "eshtaya_smart_control";

function escV241Error(err) {
  return err?.message || err?.body?.message || String(err || "Unknown error");
}

customElements.whenDefined("eshtaya-tuya-control").then(() => {
  const Tuya = customElements.get("eshtaya-tuya-control");
  if (!Tuya || Tuya.prototype.__eshtayaV241Applied) return;

  const p = Tuya.prototype;
  p.__eshtayaV241Applied = true;

  const baseRender = p._render;

  // The parent shell assigns the same language on every Home Assistant update.
  // Re-render only when the effective child language really changed.
  Object.defineProperty(p, "language", {
    configurable: true,
    get() {
      return this._language;
    },
    set(value) {
      const next = value || "";
      if (this._language === next) return;
      this._language = next;
      this._render();
    },
  });

  p._render = function () {
    const previous = {};
    let focusKey = null;
    let selectionStart = null;
    let selectionEnd = null;

    if (this.shadowRoot) {
      for (const field of this.shadowRoot.querySelectorAll("[data-c]")) {
        previous[field.dataset.c] = field.value;
      }

      const active = this.shadowRoot.activeElement;
      if (active?.matches?.("[data-c]")) {
        focusKey = active.dataset.c;
        if (typeof active.selectionStart === "number") {
          selectionStart = active.selectionStart;
          selectionEnd = active.selectionEnd;
        }
      }
    }

    const result = baseRender.call(this);

    if (this.shadowRoot) {
      for (const [key, value] of Object.entries(previous)) {
        const field = this.shadowRoot.querySelector(`[data-c="${key}"]`);
        if (field) field.value = value;
      }

      if (focusKey) {
        const active = this.shadowRoot.querySelector(`[data-c="${focusKey}"]`);
        if (active) {
          active.focus();
          if (
            selectionStart !== null &&
            selectionEnd !== null &&
            typeof active.setSelectionRange === "function"
          ) {
            try {
              active.setSelectionRange(selectionStart, selectionEnd);
            } catch (_) {
              // Select elements and some input types do not support caret ranges.
            }
          }
        }
      }
    }

    return result;
  };
});

customElements.whenDefined("eshtaya-smart-control-panel").then(() =>
  queueMicrotask(() =>
    queueMicrotask(() => {
      const Panel = customElements.get("eshtaya-smart-control-panel");
      if (!Panel || Panel.prototype.__eshtayaV241DocsApplied) return;

      const p = Panel.prototype;
      p.__eshtayaV241DocsApplied = true;

      p._openDoc = async function (slug) {
        const requestedSlug = String(slug || "").trim().toUpperCase();
        if (!requestedSlug || !this._hass) return;

        this._doc = requestedSlug;
        this._docText = "";
        this._render();

        try {
          const result = await this._hass.callWS({
            type: `${ESC_V241_DOMAIN}/documentation/get`,
            slug: requestedSlug,
            language: this._lang,
          });
          const content = typeof result?.content === "string" ? result.content : "";
          if (!content.trim()) throw new Error("Documentation response is empty");

          // Ignore a late response if the user already left this document.
          if (this._doc !== requestedSlug) return;
          this._docText = content;
        } catch (err) {
          if (this._doc !== requestedSlug) return;
          this._docText = `# ${this._t("docLoadError")}\n\n${escV241Error(err)}`;
        }

        if (this._doc === requestedSlug) this._render();
      };
    })
  )
);
