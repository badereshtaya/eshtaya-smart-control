/* Runtime resilience layer for Eshtaya Smart Control v2.2.
 *
 * The embedded panels used to perform a single first-load attempt. A transient
 * WebSocket disconnect, integration startup race, or browser reconnect could
 * therefore leave Entity, Tuya, or Multi-Way mounted forever without data.
 * This layer adds bounded request timeouts, automatic retry/backoff, reconnect
 * recovery and stale-request protection without duplicating backend logic.
 */

const ESC_RETRY = Symbol("escRetryState");

function retryState(el) {
  if (!el[ESC_RETRY]) el[ESC_RETRY] = {attempt: 0, timer: null, generation: 0, lastError: ""};
  return el[ESC_RETRY];
}

function errorText(err) {
  return err?.message || err?.body?.message || String(err || "Unknown error");
}

function isAuthorizationError(err) {
  const text = errorText(err).toLowerCase();
  return text.includes("unauthorized") || text.includes("permission") || text.includes("not allowed") || text.includes("forbidden");
}

function withTimeout(promise, ms = 20000, label = "request") {
  let timer;
  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error(`${label} timed out after ${Math.round(ms / 1000)}s`)), ms);
  });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
}

function clearRetry(el) {
  const state = retryState(el);
  if (state.timer) clearTimeout(state.timer);
  state.timer = null;
}

function scheduleRetry(el, fn, err, {min = 1200, max = 30000} = {}) {
  const state = retryState(el);
  state.lastError = errorText(err);
  if (isAuthorizationError(err) || !el.isConnected) return;
  clearRetry(el);
  const delay = Math.min(max, Math.round(min * Math.pow(1.8, Math.min(state.attempt, 7))));
  state.attempt += 1;
  state.timer = setTimeout(() => {
    state.timer = null;
    if (el.isConnected && el._hass) fn.call(el);
  }, delay);
}

function markSuccess(el) {
  const state = retryState(el);
  state.attempt = 0;
  state.lastError = "";
  clearRetry(el);
}

function installReconnectHooks(el, reload) {
  if (el.__escReconnectInstalled) return;
  el.__escReconnectInstalled = true;
  const recover = () => {
    const state = retryState(el);
    state.generation += 1;
    state.attempt = 0;
    clearRetry(el);
    if (el.isConnected && el._hass) reload.call(el);
  };
  el.__escRecover = recover;
  window.addEventListener("online", recover);
  window.addEventListener("focus", () => {
    const state = retryState(el);
    if (state.lastError && el.isConnected) recover();
  });
}

// Entity & Alexa -----------------------------------------------------------
customElements.whenDefined("eshtaya-entity-manager-panel").then(() => {
  const C = customElements.get("eshtaya-entity-manager-panel");
  if (!C || C.prototype.__escV22Resilient) return;
  const p = C.prototype;
  p.__escV22Resilient = true;

  p._load = async function(includeFile = false) {
    if (!this._hass) return;
    const state = retryState(this);
    if (this.__escLoadPromise) return this.__escLoadPromise;
    const generation = ++state.generation;
    this._ensureV12State?.();
    this._loading = true;
    this._render();
    installReconnectHooks(this, () => this._load(includeFile || this._tab === "file"));

    this.__escLoadPromise = (async () => {
      try {
        const data = await withTimeout(
          this._hass.callWS({type: "eshtaya_smart_control/entity/get", include_file: !!includeFile}),
          20000,
          "Entity Control"
        );
        if (generation !== retryState(this).generation) return;
        this._data = data;
        this._loaded = true;
        this._loadError = "";
        const valid = new Set((this._data?.entities || []).map(e => e.entity_id));
        if (this._selectedEntities) {
          for (const id of [...this._selectedEntities]) if (!valid.has(id)) this._selectedEntities.delete(id);
        }
        markSuccess(this);
      } catch (err) {
        if (generation !== retryState(this).generation) return;
        this._loadError = errorText(err);
        this._loaded = false;
        scheduleRetry(this, () => this._load(includeFile || this._tab === "file"), err);
        this._toast?.(`${this._loadError} · auto retry`, true);
      } finally {
        if (generation === retryState(this).generation) {
          this._loading = false;
          this._render();
        }
      }
    })().finally(() => { this.__escLoadPromise = null; });
    return this.__escLoadPromise;
  };
});

// Tuya ---------------------------------------------------------------------
customElements.whenDefined("eshtaya-tuya-control").then(() => {
  const C = customElements.get("eshtaya-tuya-control");
  if (!C || C.prototype.__escV22Resilient) return;
  const p = C.prototype;
  p.__escV22Resilient = true;
  const baseRender = p._render;

  p._render = function() {
    baseRender.call(this);
    if (!this._loadError || !this.shadowRoot) return;
    const wrap = this.shadowRoot.querySelector(".wrap");
    if (!wrap || wrap.querySelector(".esc-recovery")) return;
    const banner = document.createElement("div");
    banner.className = "esc-recovery";
    banner.style.cssText = "margin:0 0 12px;padding:11px 13px;border:1px solid var(--error-color,#e53935);border-radius:12px;background:color-mix(in srgb,var(--error-color,#e53935) 8%,var(--card-background-color));font-size:12px;line-height:1.5";
    banner.textContent = `${this._ar ? "تعذر تحميل بيانات تويا مؤقتاً. تتم إعادة المحاولة تلقائياً: " : "Tuya data could not be loaded temporarily. Automatic retry is active: "}${this._loadError}`;
    wrap.prepend(banner);
  };

  p._loadStatus = async function() {
    if (!this._hass) return;
    if (this.__escStatusPromise) return this.__escStatusPromise;
    const state = retryState(this);
    const generation = ++state.generation;
    installReconnectHooks(this, this._loadStatus);
    this._loading = true;
    this._render();
    this.__escStatusPromise = (async () => {
      try {
        const status = await withTimeout(
          this._hass.callWS({type: "eshtaya_smart_control/tuya/status"}),
          15000,
          "Tuya status"
        );
        if (generation !== retryState(this).generation) return;
        this._status = status;
        this._loadError = "";
        markSuccess(this);
        if (status?.configured) await this._loadDevices(false, true);
      } catch (err) {
        if (generation !== retryState(this).generation) return;
        this._loadError = errorText(err);
        scheduleRetry(this, this._loadStatus, err);
      } finally {
        if (generation === retryState(this).generation) {
          this._loading = false;
          this._render();
        }
      }
    })().finally(() => { this.__escStatusPromise = null; });
    return this.__escStatusPromise;
  };

  p._loadDevices = async function(force = false, fromStatus = false) {
    if (!this._hass) return;
    if (this.__escDevicesPromise) return this.__escDevicesPromise;
    const state = retryState(this);
    const generation = fromStatus ? state.generation : ++state.generation;
    this._loading = true;
    this._render();
    this.__escDevicesPromise = (async () => {
      try {
        const result = await withTimeout(
          this._hass.callWS({type: "eshtaya_smart_control/tuya/list_devices", force: !!force}),
          force ? 45000 : 30000,
          "Tuya devices"
        );
        if (generation !== retryState(this).generation) return;
        this._devices = result?.devices || [];
        this._loadError = "";
        markSuccess(this);
      } catch (err) {
        if (generation !== retryState(this).generation) return;
        this._loadError = errorText(err);
        scheduleRetry(this, () => this._loadDevices(false), err, {min: 1800, max: 45000});
      } finally {
        if (generation === retryState(this).generation) {
          this._loading = false;
          this._render();
        }
      }
    })().finally(() => { this.__escDevicesPromise = null; });
    return this.__escDevicesPromise;
  };
});

// Multi-Way / Smart Groups -------------------------------------------------
customElements.whenDefined("eshtaya-multiway-panel").then(() => {
  const C = customElements.get("eshtaya-multiway-panel");
  if (!C || C.prototype.__escV22Resilient) return;
  const p = C.prototype;
  p.__escV22Resilient = true;
  const baseRender = p._render;

  p._render = function() {
    baseRender.call(this);
    if (!this._loadError || !this.shadowRoot) return;
    const main = this.shadowRoot.querySelector("main") || this.shadowRoot.firstElementChild;
    if (!main || main.querySelector(".esc-recovery")) return;
    const banner = document.createElement("div");
    banner.className = "esc-recovery";
    banner.style.cssText = "margin:12px 16px;padding:11px 13px;border:1px solid var(--error-color,#e53935);border-radius:12px;background:color-mix(in srgb,var(--error-color,#e53935) 8%,var(--card-background-color));font-size:12px";
    banner.textContent = `${this.lang === "ar" ? "تعذر تحميل جزء من بيانات الجروبات مؤقتاً. النظام يعيد المحاولة تلقائياً: " : "Part of the group data failed to load. Automatic recovery is active: "}${this._loadError}`;
    main.prepend(banner);
  };

  p._bootstrap = async function() {
    if (!this._hass) return;
    if (this.__escBootstrapPromise) return this.__escBootstrapPromise;
    const state = retryState(this);
    const generation = ++state.generation;
    installReconnectHooks(this, this._bootstrap);
    this._loading = true;
    this._render();

    this.__escBootstrapPromise = (async () => {
      const jobs = [
        ["catalog", () => withTimeout(this._loadCatalog(), 20000, "Entity catalog")],
        ["native groups", () => withTimeout(this._loadNativeGroups(), 20000, "Native groups")],
        ["group runtime", () => withTimeout(this._refresh(true), 30000, "Multi-Way runtime")],
      ];
      const failures = [];
      for (const [name, job] of jobs) {
        try { await job(); }
        catch (err) { failures.push(`${name}: ${errorText(err)}`); }
      }
      if (generation !== retryState(this).generation) return;

      if (failures.length) {
        const err = new Error(failures.join(" | "));
        this._loadError = err.message;
        scheduleRetry(this, this._bootstrap, err, {min: 1500, max: 30000});
      } else {
        this._loadError = "";
        markSuccess(this);
      }

      if (!this._unsubscribe) {
        try {
          this._unsubscribe = await this._hass.connection.subscribeEvents(
            () => this._refresh(false),
            "eshtaya_smart_control/multiway_event"
          );
        } catch (_) {
          // Reconnect recovery and manual refresh remain available.
        }
      }
    })().catch(err => {
      if (generation !== retryState(this).generation) return;
      this._loadError = errorText(err);
      scheduleRetry(this, this._bootstrap, err);
    }).finally(() => {
      if (generation === retryState(this).generation) {
        this._loading = false;
        this._render();
      }
    }).finally(() => { this.__escBootstrapPromise = null; });

    return this.__escBootstrapPromise;
  };
});
