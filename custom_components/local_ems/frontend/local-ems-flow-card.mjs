// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * Local EMS wrapper for original Power Flow Card Plus v0.4.0-beta.1 (MIT).
 *
 * PFCP supplies the complete upstream renderer, UI styles, power-flow
 * allocator, animations, interactions and optional UI editor. This wrapper
 * only translates existing HA Energy/EMS sources, handles a stable local
 * Lovelace card type, and shields the original card from entity name clashes.
 * See vendor/LICENSE-PFCP and THIRD_PARTY_NOTICES.md.
 */
import { buildUpstreamBridge, LOCAL_CARD_TYPE, UPSTREAM_ELEMENT,
  UPSTREAM_CARD_TYPE } from "./pfcp-adapter.mjs?v=0.5.0b6";
import "./local-ems-peak-gauge-card.mjs";

const VENDOR_MODULE = "./vendor/power-flow-card-plus-v0.4.0-beta.1.mjs?v=0.5.0b6";
let vendorPromise;

async function loadVendor() {
  if (!vendorPromise) vendorPromise = import(VENDOR_MODULE);
  await vendorPromise;
  if (!customElements.get(UPSTREAM_ELEMENT)) {
    throw new Error("Local EMS: bundled Power Flow Card Plus element was not registered");
  }
  return customElements.get(UPSTREAM_ELEMENT);
}

export class LocalEMSFlowCard extends HTMLElement {
  constructor() {
    super();
    this._config = {};
    this._hass = null;
    this._connection = null;
    this._prefs = null;
    this._prefsRequested = false;
    this._vendorReady = false;
    this._original = null;
    this._configSignature = null;
    this._sourceMap = {};
    this._message = null;
    this._error = null;
    this._onMoreInfo = (event) => {
      const requested = event.detail?.entityId;
      const actual = this._sourceMap[requested];
      if (actual && actual !== requested) {
        event.stopPropagation();
        this.dispatchEvent(new CustomEvent("hass-more-info", {
          bubbles: true, composed: true, detail: { entityId: actual },
        }));
      }
    };
    this.addEventListener("hass-more-info", this._onMoreInfo);
  }

  connectedCallback() {
    void this._ensureVendor();
  }

  disconnectedCallback() {
    // Keep the nested Lit card alive when Lovelace temporarily detaches it.
  }

  async _ensureVendor() {
    if (this._vendorReady || this._error) return;
    try {
      await loadVendor();
      this._vendorReady = true;
      this._refresh();
    } catch (error) {
      this._error = error;
      console.error("Local EMS: loading bundled Power Flow Card Plus failed", error);
      this._showMessage("Local EMS: Power Flow Card Plus konnte nicht geladen werden.");
    }
  }

  setConfig(config) {
    if (!config || typeof config !== "object" || Array.isArray(config)) {
      throw new Error("Local EMS Flow: invalid card configuration");
    }
    if (config.entity && (typeof config.entity !== "string" ||
        !config.entity.startsWith("sensor."))) {
      throw new Error("Local EMS Flow: entity must be a sensor ID");
    }
    if (config.source_mode && !["energy", "ems"].includes(config.source_mode)) {
      throw new Error("Local EMS Flow: source_mode must be energy or ems");
    }
    if (config.invert_battery_power !== undefined &&
        typeof config.invert_battery_power !== "boolean") {
      throw new Error("Local EMS Flow: invert_battery_power must be true or false");
    }
    if (config.entities && config.invert_battery_power !== undefined) {
      throw new Error(
        "Local EMS Flow: with manual entities, use entities.battery.invert_state"
      );
    }
    this._config = { ...config };
    this._configSignature = null;
    this._refresh();
  }

  set hass(hass) {
    if (this._connection !== hass?.connection) {
      this._connection = hass?.connection ?? null;
      this._prefs = null;
      this._prefsRequested = false;
    }
    this._hass = hass;
    if (!this._prefsRequested && !this._config.entities &&
        typeof hass?.callWS === "function") {
      void this._fetchEnergyPreferences(hass);
    }
    this._refresh();
  }

  async _fetchEnergyPreferences(hass) {
    this._prefsRequested = true;
    try {
      const prefs = await hass.callWS({ type: "energy/get_prefs" });
      if (this._hass?.connection === hass.connection) this._prefs = prefs;
    } catch (_) {
      if (this._hass?.connection === hass.connection) this._prefs = null;
    }
    if (this._hass?.connection === hass.connection) this._refresh();
  }

  _metadata() {
    if (this._config.entities) return null;
    const states = this._hass?.states || {};
    if (this._config.entity) return states[this._config.entity] ?? null;
    return Object.values(states).find(st =>
      st?.entity_id?.startsWith("sensor.") &&
      st.attributes?.ems_flow_version === 1
    ) ?? null;
  }

  _showMessage(message) {
    if (this._original) {
      this._original.remove();
      this._original = null;
      this._configSignature = null;
    }
    if (!this._message) {
      this._message = document.createElement("ha-card");
      this._message.style.cssText = "display:block;padding:16px;box-sizing:border-box";
    }
    this._message.textContent = message;
    if (!this._message.isConnected) this.appendChild(this._message);
  }

  _refresh() {
    if (!this._hass) return;
    if (!this._vendorReady) {
      if (!this._error) void this._ensureVendor();
      return;
    }
    const metadata = this._metadata();
    if (!this._config.entities && !metadata) {
      this._showMessage("Local EMS: Energiefluss-Entität nicht gefunden.");
      return;
    }

    const bridge = buildUpstreamBridge(
      this._hass, metadata?.attributes, this._prefs, this._config
    );
    if (!bridge) {
      this._showMessage("Local EMS: Keine Leistungsquellen konfiguriert.");
      return;
    }

    try {
      const signature = JSON.stringify(bridge.config);
      if (!this._original) {
        this._original = document.createElement(UPSTREAM_ELEMENT);
        this._original.style.cssText = "display:block;width:100%;min-width:0";
        this.appendChild(this._original);
      }
      if (this._message?.isConnected) this._message.remove();
      this._sourceMap = bridge.sourceMap;
      if (this._configSignature !== signature) {
        this._original.setConfig(bridge.config);
        this._configSignature = signature;
      }
      this._original.hass = bridge.hass;
    } catch (error) {
      console.error("Local EMS: upstream Power Flow Card Plus rendering error", error);
      this._showMessage("Local EMS: Power-Flow-Karte konnte nicht dargestellt werden.");
    }
  }

  getCardSize() { return this._original?.getCardSize?.() ?? 8; }

  getGridOptions() {
    return { columns: 12, min_columns: 6, max_columns: 12, rows: "auto" };
  }

  static getStubConfig() { return { type: LOCAL_CARD_TYPE }; }

  // The vendored original editor is available when users opt into manually
  // configured PFCP entities (all upstream options, not a partial clone).
  static async getConfigElement() {
    const Original = await loadVendor();
    const editor = await Original.getConfigElement();
    editor.addEventListener("config-changed", (event) => {
      if (event.detail?.config && typeof event.detail.config === "object") {
        event.detail.config = { ...event.detail.config, type: LOCAL_CARD_TYPE };
      }
    });
    return editor;
  }
}

if (typeof customElements !== "undefined" &&
    !customElements.get("local-ems-flow-card")) {
  customElements.define("local-ems-flow-card", LocalEMSFlowCard);
}
if (typeof window !== "undefined") {
  window.customCards = window.customCards || [];
  if (!window.customCards.some(entry => entry.type === "local-ems-flow-card")) {
    window.customCards.push({
      type: "local-ems-flow-card",
      name: "Local EMS Power Flow (Power Flow Card Plus)",
      description: "Original Power Flow Card Plus renderer with Local EMS sources",
      preview: false,
    });
  }
}
