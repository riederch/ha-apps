// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * Local EMS Energy Flow – independently implemented circular power-flow card.
 * The round topology is familiar from Home Assistant's Energy Distribution
 * and Power Flow Card Plus, but has no imported code or runtime dependency
 * on another dashboard card.
 */
import { buildFlowModel, formatWatts } from "./flow-model.mjs";
// Both Local EMS cards are shipped through the same Lovelace JS resource.
import "./local-ems-peak-gauge-card.mjs";

const TRANSLATIONS = {
  de: {
    title: "Energiefluss",
    solar: "Solar",
    grid: "Netz",
    home: "Haus",
    battery: "Batterie",
    on_grid: "Netzbetrieb",
    eps: "EPS / Inselbetrieb",
    grid_lost: "Netzausfall",
    suspect: "Netzstatus unsicher",
    recovering: "Netz stabilisiert sich",
    unknown: "Netzstatus unbekannt",
    unconfigured: "Netzüberwachung nicht konfiguriert",
    missing: "Local EMS Energiefluss-Entität nicht gefunden.",
    noSources: "Keine aktuellen Leistungsquellen zugeordnet: im Energy-Dashboard oder Local EMS konfigurieren.",
    import: "Bezug",
    export: "Einspeisung",
    discharge: "Entladen",
    charge: "Laden",
    production: "Erzeugung",
    idle: "",
    sourceEnergy: "Energy-Dashboard",
    sourceEms: "Local EMS",
    inverter: "Wechselrichter",
    invalid: "Messwert nicht verfügbar",
  },
  en: {
    title: "Energy flow",
    solar: "Solar",
    grid: "Grid",
    home: "Home",
    battery: "Battery",
    on_grid: "Grid connected",
    eps: "EPS / islanded",
    grid_lost: "Grid outage",
    suspect: "Grid state uncertain",
    recovering: "Grid recovering",
    unknown: "Grid state unknown",
    unconfigured: "Grid status not configured",
    missing: "Local EMS energy-flow entity was not found.",
    noSources: "No live power sources configured. Set up Energy Dashboard or Local EMS.",
    import: "Import",
    export: "Export",
    discharge: "Discharging",
    charge: "Charging",
    production: "Producing",
    idle: "",
    sourceEnergy: "Energy Dashboard",
    sourceEms: "Local EMS",
    inverter: "Inverter",
    invalid: "Measurement unavailable",
  },
};

const PATHS = {
  grid: "M16 50 H84",
  gridReverse: "M84 50 H16",
  solar: "M50 24 V40 Q50 47 60 47 H84",
  battery: "M50 76 V60 Q50 53 60 53 H84",
  batteryReverse: "M84 53 H60 Q50 53 50 60 V76",
  // Direct routes on the left side, joining the respective source nodes.
  // Solar -> grid and grid -> battery are only animated where conservative
  // energy-balance inference confirms a minimum transfer.
  solarGrid: "M50 24 V40 Q50 47 40 47 H16",
  gridBattery: "M16 50 H40 Q50 53 50 60 V74",
};

// Percent-based paths keep the same power-flow topology on phones, tablets,
// and widescreen dashboards. SVG vector-effect keeps lines a consistent width.
const CSS = [
  ":host{display:block;width:100%;min-width:0;box-sizing:border-box;--ems-bubble-diameter:80px;--ems-solar:var(--warning-color,#eba526);",
  "--ems-grid:var(--info-color,#3395cc);",
  "--ems-home:var(--success-color,#36aca0);",
  "--ems-battery:#bb6baf;}",
  "ha-card{padding:18px 12px 15px;overflow:hidden;width:100%;box-sizing:border-box;}",
  ".header{display:flex;align-items:center;justify-content:space-between;gap:12px;",
  "padding:0 8px 12px;}",
  ".title{color:var(--primary-text-color);font-size:1.14rem;font-weight:600;}",
  ".status{border-radius:15px;background:var(--secondary-background-color);",
  "font-size:.73rem;line-height:1.3;padding:6px 9px;color:var(--secondary-text-color);",
  "display:inline-flex;align-items:center;gap:6px;max-width:57%;}",
  ".status::before{content:'';display:inline-block;border-radius:50%;width:7px;height:7px;",
  "flex:none;background:currentColor;}",
  ".status[data-state='on_grid']{color:var(--success-color,#39a178);}",
  ".status[data-state='eps'],.status[data-state='grid_lost']{color:var(--error-color,#e25959);}",
  ".status[data-state='suspect'],.status[data-state='recovering']{color:var(--warning-color,#c99d30);}",
  ".canvas{height:324px;min-width:0;position:relative;isolation:isolate;}",
  ".lines{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;",
  "overflow:visible;z-index:0;}",
  ".track,.dots{fill:none;vector-effect:non-scaling-stroke;stroke-linecap:round;}",
  ".track{stroke:var(--divider-color,rgba(145,150,158,.3));stroke-width:2;}",
  ".track[data-visible='false']{visibility:hidden;}",
  ".dots{stroke-width:5;stroke-dasharray:1 20;animation:power-dots 1.4s linear infinite;}",
  ".dots[data-active='false']{visibility:hidden;animation:none;}",
  "#solar-dots,#solar-grid-dots{stroke:var(--ems-solar);}",
  "#grid-dots,#grid-battery-dots{stroke:var(--ems-grid);}",
  "#battery-dots{stroke:var(--ems-battery);}",
  "@keyframes power-dots{from{stroke-dashoffset:0;}to{stroke-dashoffset:-84;}}",
  ".node{position:absolute;transform:translate(-50%,-50%);",
  "width:var(--ems-bubble-diameter);height:var(--ems-bubble-diameter);",
  "aspect-ratio:1;box-sizing:border-box;flex:none;",
  "border:none;background:transparent;padding:0;cursor:pointer;color:var(--primary-text-color);",
  "display:flex;align-items:center;justify-content:center;font:inherit;z-index:1;}",
  ".node:focus-visible{outline:2px solid var(--primary-color);outline-offset:6px;",
  "border-radius:50%;}",
  ".disc{box-sizing:border-box;width:100%;height:100%;aspect-ratio:1;",
  "border:3px solid var(--ring);border-radius:50%;",
  "background:var(--card-background-color,var(--ha-card-background,#fff));",
  "display:flex;flex-direction:column;align-items:center;justify-content:center;",
  "gap:2px;padding:9px 5px;box-shadow:0 2px 9px rgba(0,0,0,.07);}",
  ".disc ha-icon{--mdc-icon-size:23px;color:var(--ring);}",
  ".disc .power{font-size:.97rem;font-weight:700;white-space:nowrap;line-height:1.2;}",
  ".disc .detail{font-size:.68rem;color:var(--secondary-text-color);white-space:nowrap;",
  "max-width:100%;overflow:hidden;text-overflow:ellipsis;line-height:1.25;}",
  ".node .name{position:absolute;left:50%;transform:translateX(-50%);",
  "top:calc(100% + 6px);font-size:.8rem;color:var(--secondary-text-color);",
  "white-space:nowrap;font-weight:500;pointer-events:none;}",
  ".solar .name{top:auto;bottom:calc(100% + 5px);}",
  ".solar{--ring:var(--ems-solar);left:50%;top:24%;}",
  ".grid{--ring:var(--ems-grid);left:max(42px,16%);top:50%;}",
  ".home{--ring:var(--ems-home);left:min(calc(100% - 42px),84%);top:50%;}",
  ".battery{--ring:var(--ems-battery);left:50%;top:74%;}",
  ".node[data-active='false'] .disc{border-color:var(--divider-color,#a1a1a1);}",
  ".node[data-active='false'] .disc ha-icon{color:var(--secondary-text-color);}",
  ".node[data-outage='true']{--ring:var(--error-color,#e05c5c);}",
  ".node[data-outage='true'] .disc{border-width:4px;}",
  ".node:disabled{cursor:default;}",
  ".footer{display:flex;flex-wrap:wrap;justify-content:space-between;",
  "gap:5px 12px;border-top:1px solid var(--divider-color);",
  "margin:7px 6px 0;padding:10px 2px 0;",
  "color:var(--secondary-text-color);font-size:.72rem;}",
  ".note{color:var(--secondary-text-color);font-size:.76rem;text-align:center;",
  "margin:7px 8px 0;line-height:1.4;}",
  ".note:empty{display:none;}",
  "@media(max-width:400px){ha-card{padding:14px 8px;}.canvas{height:310px;}",
  ".node{width:var(--ems-bubble-diameter);height:var(--ems-bubble-diameter);}",
  ".disc .power{font-size:.85rem;}.disc .detail{font-size:.59rem;}",
  ".disc ha-icon{--mdc-icon-size:21px;}.header{gap:7px;}",
  ".status{font-size:.69rem;}}",
  "@media(prefers-reduced-motion:reduce){.dots{animation:none;",
  "stroke-dasharray:none;stroke-width:2.5;}}",
].join("");

const TEMPLATE = [
  "<style>", CSS, "</style>",
  "<ha-card>",
  '<div class="header"><div class="title" id="title"></div>',
  '<div class="status" id="status" role="status" data-state="unknown"></div></div>',
  '<div class="canvas" role="group" aria-label="Energy power flow">',
  '<svg class="lines" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">',
  '<path class="track" id="grid-track" d="M16 50 H84"></path>',
  '<path class="track" id="solar-track" d="M50 24 V40 Q50 47 60 47 H84"></path>',
  '<path class="track" id="battery-track" d="M50 76 V60 Q50 53 60 53 H84"></path>',
  '<path class="track" id="solar-grid-track" d="M50 24 V40 Q50 47 40 47 H16"></path>',
  '<path class="track" id="grid-battery-track" d="M16 50 H40 Q50 53 50 60 V74"></path>',
  '<path class="dots" id="grid-dots" data-active="false"></path>',
  '<path class="dots" id="solar-dots" data-active="false"></path>',
  '<path class="dots" id="battery-dots" data-active="false"></path>',
  '<path class="dots" id="solar-grid-dots" data-active="false"></path>',
  '<path class="dots" id="grid-battery-dots" data-active="false"></path>',
  "</svg>",
  '<button type="button" class="node solar" data-node="solar">',
  '<span class="name" data-name="solar"></span><span class="disc">',
  '<ha-icon data-icon="solar" icon="mdi:solar-power"></ha-icon>',
  '<span class="power" data-power="solar">—</span>',
  '<span class="detail" data-detail="solar"></span></span></button>',
  '<button type="button" class="node grid" data-node="grid">',
  '<span class="name" data-name="grid"></span><span class="disc">',
  '<ha-icon data-icon="grid" icon="mdi:transmission-tower"></ha-icon>',
  '<span class="power" data-power="grid">—</span>',
  '<span class="detail" data-detail="grid"></span></span></button>',
  '<button type="button" class="node home" data-node="home">',
  '<span class="name" data-name="home"></span><span class="disc">',
  '<ha-icon data-icon="home" icon="mdi:home-lightning-bolt"></ha-icon>',
  '<span class="power" data-power="home">—</span>',
  '<span class="detail" data-detail="home"></span></span></button>',
  '<button type="button" class="node battery" data-node="battery">',
  '<span class="name" data-name="battery"></span><span class="disc">',
  '<ha-icon data-icon="battery" icon="mdi:battery"></ha-icon>',
  '<span class="power" data-power="battery">—</span>',
  '<span class="detail" data-detail="battery"></span></span></button>',
  "</div>",
  '<div class="footer"><span id="data-source"></span><span id="inverter"></span></div>',
  '<div class="note" id="note"></div>',
  "</ha-card>",
].join("");

function secondsPerFlow(watts, minRate = 0.75, maxRate = 6, expected = 2000) {
  if (!Number.isFinite(watts) || !Number.isFinite(expected) || expected <= 0) {
    return maxRate;
  }
  const minimum = Number.isFinite(minRate) && minRate > 0 ? minRate : 0.75;
  const maximum = Number.isFinite(maxRate) && maxRate >= minimum ? maxRate : 6;
  const proportion = Math.max(0, Math.min(1, Math.abs(watts) / expected));
  return maximum - proportion * (maximum - minimum);
}

export class LocalEMSFlowCard extends HTMLElement {
  constructor() {
    super();
    this._root = this.attachShadow({ mode: "open" });
    this._root.innerHTML = TEMPLATE;
    this._config = {};
    this._lastModel = null;
    this._prefs = null;
    this._prefsRequested = false;
    this._connection = null;

    this._root.querySelectorAll("[data-node]").forEach((button) => {
      button.addEventListener("click", () => {
        const source = this._lastModel?.sources?.[button.dataset.node];
        if (typeof source !== "string" || !source) return;
        this.dispatchEvent(new CustomEvent("hass-more-info", {
          bubbles: true,
          composed: true,
          detail: { entityId: source },
        }));
      });
    });
  }

  setConfig(config) {
    if (config.entity && (typeof config.entity !== "string" ||
        !config.entity.startsWith("sensor."))) {
      throw new Error("Local EMS Flow: entity must be a sensor ID");
    }
    if (config.source_mode &&
        !["energy", "ems"].includes(config.source_mode)) {
      throw new Error("Local EMS Flow: source_mode must be energy or ems");
    }
    this._config = { ...config };
    this._update();
  }

  set hass(hass) {
    if (this._connection !== hass.connection) {
      this._connection = hass.connection;
      this._prefsRequested = false;
      this._prefs = null;
    }
    this._hass = hass;
    if (!this._prefsRequested && typeof hass.callWS === "function") {
      void this._fetchEnergyPreferences(hass);
    }
    this._update();
  }

  async _fetchEnergyPreferences(hass) {
    // Energy is a native component. This call is read-only and per card
    // instance, never on every fast-changing Home Assistant state event.
    this._prefsRequested = true;
    try {
      this._prefs = await hass.callWS({ type: "energy/get_prefs" });
    } catch (_error) {
      this._prefs = null;
    }
    if (this._hass?.connection === hass.connection) this._update();
  }

  getCardSize() { return 8; }

  getGridOptions() {
    // Sections dashboards use a 12-column grid. Default to the full width;
    // existing explicit grid_options from a saved card still take precedence.
    return { columns: 12, min_columns: 6, max_columns: 12, rows: "auto" };
  }

  static getStubConfig() { return {}; }

  _language() {
    return String(this._hass?.language || "de").startsWith("de") ?
      TRANSLATIONS.de : TRANSLATIONS.en;
  }

  _metadataEntity() {
    const states = this._hass?.states || {};
    if (this._config.entity) return states[this._config.entity] || null;
    return Object.values(states).find((st) => (
      st?.entity_id?.startsWith("sensor.") &&
      st.attributes?.ems_flow_version === 1
    )) || null;
  }

  _text(selector, value) {
    const element = this._root.querySelector(selector);
    if (element) element.textContent = value ?? "";
  }

  _inverterLabel(model) {
    // The backend stores vendor-neutral raw states. For display, prefer
    // Home Assistant's localized label for an ENUM sensor when available.
    const entity = this._hass?.states?.[model.sources?.inverter_state];
    const localize = this._hass?.formatEntityState;
    if (entity && typeof localize === "function") {
      try {
        const value = localize.call(this._hass, entity);
        if (typeof value === "string" && value.trim()) return value;
      } catch (_err) {
        // Unknown or custom enum: use a readable raw state as fallback.
      }
    }
    return model.inverterState ? model.inverterState.replaceAll("_", " ") : "";
  }

  _flow(name, active, path, watts) {
    const element = this._root.getElementById(name + "-dots");
    element.setAttribute("d", path);
    element.dataset.active = active ? "true" : "false";
    if (active) {
      element.style.animationDuration = secondsPerFlow(
        watts, this._config.min_flow_rate, this._config.max_flow_rate,
        this._config.max_expected_power || 2000
      ).toFixed(2) + "s";
    }
  }

  _reset() {
    this._lastModel = null;
    for (const el of this._root.querySelectorAll("[data-power]")) {
      el.textContent = "—";
    }
    for (const el of this._root.querySelectorAll("[data-detail]")) {
      el.textContent = "";
    }
    for (const el of this._root.querySelectorAll(".dots")) {
      el.dataset.active = "false";
    }
    for (const el of this._root.querySelectorAll(".track")) {
      el.dataset.visible = "true";
    }
    this._root.getElementById("status").dataset.state = "unknown";
    this._root.querySelector('[data-icon="grid"]').setAttribute(
      "icon", "mdi:transmission-tower"
    );
    this._text("#inverter", "");
    this._text("#data-source", "");
  }

  _update() {
    if (!this._hass || !this._root) return;
    const t = this._language();
    const locale = this._hass.locale?.language || this._hass.language || "de-AT";
    const showZeroLines = this._config.display_zero_lines !== false;
    this._text("#title", this._config.title || t.title);

    const metadata = this._metadataEntity();
    if (!metadata) {
      this._reset();
      this._text("#status", t.unknown);
      this._text("#note", t.missing);
      return;
    }

    const model = buildFlowModel(
      this._hass.states, metadata.attributes, this._prefs, this._config
    );
    this._lastModel = model;
    this._text("#status", t[model.gridState] || t.unknown);
    this._root.getElementById("status").dataset.state = model.gridState;
    this._text("#note", model.sourcesConfigured ? "" : t.noSources);
    this._text("#data-source", model.sourceMode === "energy" ?
      t.sourceEnergy : t.sourceEms);

    const outage = ["eps", "grid_lost"].includes(model.gridState) ||
      model.gridContact === false;
    const gridNode = this._root.querySelector(".node.grid");
    gridNode.dataset.outage = outage ? "true" : "false";
    this._root.querySelector('[data-icon="grid"]').setAttribute(
      "icon", outage ? "mdi:transmission-tower-off" : "mdi:transmission-tower"
    );

    const inverterLabel = this._inverterLabel(model);
    const data = {
      solar: { watts: model.solarW, detail: model.directions.solar },
      grid: { watts: model.gridW, detail: model.directions.grid },
      home: { watts: model.houseW, detail: null },
      battery: { watts: model.batteryW, detail: model.directions.battery },
    };

    for (const name of Object.keys(data)) {
      const node = this._root.querySelector(".node." + name);
      const item = data[name];
      this._text('[data-name="' + name + '"]', t[name]);
      this._text('[data-power="' + name + '"]', formatWatts(item.watts, locale));
      node.dataset.active = item.watts !== null ? "true" : "false";
      node.disabled = !model.sources?.[name];
      node.title = model.sources?.[name] || t.invalid;
      let detail = item.detail ? (t[item.detail] || "") : "";
      if (name === "battery" && model.batterySoc !== null) {
        const soc = new Intl.NumberFormat(locale, {
          maximumFractionDigits: 0,
        }).format(model.batterySoc) + " %";
        detail = [soc, detail].filter(Boolean).join(" · ");
      }
      if (name === "grid" && model.frequency !== null) {
        detail = new Intl.NumberFormat(locale, {
          minimumFractionDigits: 1, maximumFractionDigits: 2,
        }).format(model.frequency) + " Hz";
      }
      if (name === "home" && inverterLabel) {
        detail = inverterLabel;
      }
      this._text('[data-detail="' + name + '"]', detail);
      const detailEl = this._root.querySelector('[data-detail="' + name + '"]');
      if (detailEl) detailEl.title = detail;
    }

    const moving = {
      solar: model.directions.solar === "production",
      grid: ["import", "export"].includes(model.directions.grid),
      battery: ["discharge", "charge"].includes(model.directions.battery),
      "solar-grid": model.directFlows.solarToGridW >= 5,
      "grid-battery": model.directFlows.gridToBatteryW >= 5,
    };
    for (const name of Object.keys(moving)) {
      this._root.getElementById(name + "-track").dataset.visible =
        showZeroLines || moving[name] ? "true" : "false";
    }
    this._flow("solar", moving.solar, PATHS.solar, model.solarW);
    this._flow(
      "solar-grid", moving["solar-grid"], PATHS.solarGrid,
      model.directFlows.solarToGridW
    );
    this._flow(
      "grid-battery", moving["grid-battery"], PATHS.gridBattery,
      model.directFlows.gridToBatteryW
    );
    this._flow(
      "grid", moving.grid,
      model.directions.grid === "export" ? PATHS.gridReverse : PATHS.grid,
      model.gridW
    );
    this._flow(
      "battery", moving.battery,
      model.directions.battery === "charge" ?
        PATHS.batteryReverse : PATHS.battery,
      model.batteryW
    );
    this._text("#inverter", inverterLabel ?
      t.inverter + ": " + inverterLabel : "");
  }
}

if (typeof customElements !== "undefined" &&
    !customElements.get("local-ems-flow-card")) {
  customElements.define("local-ems-flow-card", LocalEMSFlowCard);
}
if (typeof window !== "undefined") {
  window.customCards = window.customCards || [];
  if (!window.customCards.some((entry) => entry.type === "local-ems-flow-card")) {
    window.customCards.push({
      type: "local-ems-flow-card",
      name: "Local EMS Power Flow",
      description: "Round, animated power flow from Energy Dashboard and Local EMS",
      preview: false,
    });
  }
}
