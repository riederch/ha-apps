// SPDX-License-Identifier: GPL-3.0-or-later
/** A standalone energy-flow Lovelace card shipped by the Local EMS integration. */
import { buildFlowModel, formatWatts } from "./flow-model.mjs";

const TEXTS = {
  de: {
    title: "Energiefluss",
    solar: "Photovoltaik",
    grid: "Netz",
    battery: "Batterie",
    home: "Haus",
    loading: "Local EMS wird geladen …",
    missing: "Local EMS Energy flow ist nicht vorhanden. Bitte EMS-Quellen in der Integration zuordnen.",
    notConfigured: "EMS-Energiequellen noch nicht zugeordnet.",
    freq: "Netzfrequenz",
    inverter: "Wechselrichter",
    on_grid: "Netz vorhanden",
    eps: "EPS / Inselbetrieb",
    grid_lost: "Netzausfall",
    suspect: "Netzstatus unsicher",
    recovering: "Netz stabilisiert sich",
    unknown: "Netzstatus unbekannt",
    unconfigured: "Netzüberwachung nicht eingerichtet",
    import: "Netzbezug",
    export: "Einspeisung",
    discharge: "Entladung",
    charge: "Ladung",
    production: "Erzeugung",
    idle: "Keine Leistung",
    notAvailable: "Keine Messwerte",
  },
  en: {
    title: "Energy flow",
    solar: "Solar PV",
    grid: "Grid",
    battery: "Battery",
    home: "Home",
    loading: "Local EMS is loading …",
    missing: "Local EMS Energy flow was not found. Configure EMS energy sources first.",
    notConfigured: "EMS energy sources are not configured yet.",
    freq: "Grid frequency",
    inverter: "Inverter",
    on_grid: "Grid connected",
    eps: "EPS / island mode",
    grid_lost: "Grid outage",
    suspect: "Grid status uncertain",
    recovering: "Grid recovering",
    unknown: "Grid status unknown",
    unconfigured: "Grid status not configured",
    import: "Import",
    export: "Export",
    discharge: "Discharging",
    charge: "Charging",
    production: "Producing",
    idle: "Idle",
    notAvailable: "No live measurement",
  },
};

const STYLES = [
  ":host{display:block;}",
  "ha-card{padding:16px;overflow:hidden;}",
  ".head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:6px;}",
  ".title{font-size:1.15rem;font-weight:600;color:var(--primary-text-color);}",
  ".status{display:inline-flex;align-items:center;gap:6px;padding:5px 9px;border-radius:20px;",
  "font-size:.76rem;line-height:1.3;color:var(--secondary-text-color);",
  "background:var(--secondary-background-color);max-width:62%;text-align:right;}",
  ".dot{height:7px;width:7px;flex-shrink:0;border-radius:100%;background:currentColor;}",
  ".status[data-state='on_grid']{color:var(--success-color,#39986c);}",
  ".status[data-state='eps'],.status[data-state='grid_lost']{color:var(--error-color,#cc4444);}",
  ".status[data-state='suspect'],.status[data-state='recovering']{color:var(--warning-color,#dd9800);}",
  ".canvas{position:relative;width:100%;height:322px;overflow:hidden;}",
  ".links{position:absolute;inset:0;height:100%;width:100%;overflow:visible;pointer-events:none;}",
  ".track{fill:none;stroke:var(--divider-color,rgba(127,127,127,.22));stroke-width:4;stroke-linecap:round;}",
  ".flow{fill:none;stroke-width:4.5;stroke-linecap:round;",
  "stroke-dasharray:2 14;animation:travel 1.3s linear infinite;}",
  ".flow.off{opacity:0;animation:none;}",
  "#flow-solar{stroke:var(--warning-color,#d7a300);}",
  "#flow-grid{stroke:var(--info-color,#349ad7);}",
  "#flow-battery{stroke:var(--success-color,#38a57b);}",
  "@keyframes travel{to{stroke-dashoffset:-32;}}",
  ".node{position:absolute;transform:translate(-50%,-50%);",
  "width:clamp(76px,26%,122px);min-height:80px;",
  "display:flex;flex-direction:column;align-items:center;justify-content:center;",
  "padding:8px 5px;border:1px solid var(--divider-color);",
  "border-radius:15px;background:var(--card-background-color,var(--ha-card-background));",
  "color:var(--primary-text-color);cursor:pointer;font:inherit;line-height:1.25;",
  "box-shadow:0 2px 9px rgba(0,0,0,.04);box-sizing:border-box;}",
  ".node:focus-visible{outline:2px solid var(--primary-color);outline-offset:2px;}",
  ".node ha-icon{--mdc-icon-size:24px;margin-bottom:4px;}",
  ".solar{left:50%;top:19%;}.solar ha-icon{color:var(--warning-color,#d7a300);}",
  ".grid{left:18%;top:59%;}.grid ha-icon{color:var(--info-color,#349ad7);}",
  ".battery{left:82%;top:59%;}.battery ha-icon{color:var(--success-color,#38a57b);}",
  ".home{left:50%;top:59%;min-height:88px;border-color:var(--primary-color);}",
  ".home ha-icon{color:var(--primary-color);}",
  ".node .name{font-size:.75rem;color:var(--secondary-text-color);white-space:nowrap;}",
  ".node .power{font-size:.99rem;font-weight:700;white-space:nowrap;margin-top:2px;}",
  ".node .detail{font-size:.68rem;color:var(--secondary-text-color);",
  "white-space:nowrap;min-height:.9rem;}",
  ".footer{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;",
  "border-top:1px solid var(--divider-color);padding-top:10px;",
  "font-size:.77rem;color:var(--secondary-text-color);}",
  ".notice{font-size:.79rem;color:var(--secondary-text-color);text-align:center;",
  "padding:8px 4px 0;min-height:0;}",
  ".notice:empty{display:none;}",
  "@media(max-width:390px){ha-card{padding:12px;}.canvas{height:298px;}",
  ".node{min-height:74px;padding:5px 3px;border-radius:12px;}",
  ".node .name{font-size:.68rem;}.node .power{font-size:.88rem;}}",
  "@media(prefers-reduced-motion:reduce){.flow{animation:none;stroke-dasharray:none;}}",
].join("");

const SHELL = [
  "<style>", STYLES, "</style>",
  "<ha-card>",
  '<div class="head">',
  '<div id="title" class="title"></div>',
  '<div id="status" class="status" data-state="unknown" role="status">',
  '<span class="dot" aria-hidden="true"></span><span id="status-label"></span>',
  "</div></div>",
  '<div class="canvas" role="group" aria-label="Power flow">',
  '<svg class="links" viewBox="0 0 600 322" preserveAspectRatio="none" aria-hidden="true">',
  '<path class="track" d="M300 60 L300 190"></path>',
  '<path class="track" d="M104 190 L300 190"></path>',
  '<path class="track" d="M496 190 L300 190"></path>',
  '<path id="flow-solar" class="flow off"></path>',
  '<path id="flow-grid" class="flow off"></path>',
  '<path id="flow-battery" class="flow off"></path>',
  "</svg>",
  '<button type="button" class="node solar" data-node="solar">',
  '<ha-icon icon="mdi:solar-power"></ha-icon>',
  '<span class="name" data-name="solar"></span>',
  '<span class="power" data-power="solar">—</span>',
  '<span class="detail" data-detail="solar"></span></button>',
  '<button type="button" class="node grid" data-node="grid">',
  '<ha-icon icon="mdi:transmission-tower"></ha-icon>',
  '<span class="name" data-name="grid"></span>',
  '<span class="power" data-power="grid">—</span>',
  '<span class="detail" data-detail="grid"></span></button>',
  '<button type="button" class="node battery" data-node="battery">',
  '<ha-icon icon="mdi:battery"></ha-icon>',
  '<span class="name" data-name="battery"></span>',
  '<span class="power" data-power="battery">—</span>',
  '<span class="detail" data-detail="battery"></span></button>',
  '<button type="button" class="node home" data-node="home">',
  '<ha-icon icon="mdi:home-lightning-bolt"></ha-icon>',
  '<span class="name" data-name="home"></span>',
  '<span class="power" data-power="home">—</span>',
  '<span class="detail" data-detail="home"></span></button>',
  "</div>",
  '<div class="footer"><span id="frequency"></span><span id="inverter"></span></div>',
  '<div id="notice" class="notice" role="status"></div>',
  "</ha-card>",
].join("");

class LocalEMSFlowCard extends HTMLElement {
  constructor() {
    super();
    this._root = this.attachShadow({ mode: "open" });
    this._root.innerHTML = SHELL;
    this._lastModel = null;
    this._config = {};
    this._root.querySelectorAll("[data-node]").forEach((button) => {
      button.addEventListener("click", () => {
        const source = this._lastModel?.sources?.[button.dataset.node];
        if (typeof source !== "string" || !source) return;
        this.dispatchEvent(new CustomEvent("hass-more-info", {
          bubbles: true, composed: true, detail: { entityId: source },
        }));
      });
    });
  }

  setConfig(config) {
    if (config.entity && (typeof config.entity !== "string" ||
      !config.entity.startsWith("sensor."))) {
      throw new Error("Local EMS Flow: entity must be a sensor ID.");
    }
    this._config = { ...config };
    this._update();
  }

  set hass(hass) {
    this._hass = hass;
    this._update();
  }

  getCardSize() { return 7; }

  getGridOptions() {
    return { columns: 6, min_columns: 3, max_columns: 12, rows: 4, min_rows: 3 };
  }

  static getStubConfig() { return {}; }

  _t() {
    return String(this._hass?.language || "de").startsWith("de") ? TEXTS.de : TEXTS.en;
  }

  _selectFlowEntity() {
    const states = this._hass?.states || {};
    if (this._config.entity) return states[this._config.entity] || null;
    return Object.values(states).find(
      (st) => st?.entity_id?.startsWith("sensor.") &&
        st.attributes?.ems_flow_version === 1
    ) || null;
  }

  _text(selector, text) {
    const item = this._root.querySelector(selector);
    if (item) item.textContent = text ?? "";
  }

  _line(key, active, path, watts) {
    const elem = this._root.getElementById("flow-" + key);
    elem.setAttribute("d", path);
    elem.classList.toggle("off", !active);
    if (active) {
      const speed = Math.max(0.55, Math.min(3, 2.3 - Math.abs(watts) / 4000));
      elem.style.animationDuration = speed.toFixed(2) + "s";
    }
  }

  _update() {
    if (!this._hass || !this._root) return;
    const language = this._t();
    const locale = this._hass?.locale?.language || this._hass?.language || "de-AT";

    this._text("#title", this._config.title || language.title);
    const sourceEntity = this._selectFlowEntity();
    if (!sourceEntity) {
      this._lastModel = null;
      this._text("#notice", language.missing);
      this._text("#status-label", language.unknown);
      this._reset();
      return;
    }

    const model = buildFlowModel(this._hass.states, sourceEntity.attributes);
    this._lastModel = model;
    this._text("#notice", sourceEntity.state === "not_configured"
      ? language.notConfigured : "");
    this._root.getElementById("status").dataset.state = model.gridState;
    this._text("#status-label", language[model.gridState] || language.unknown);
    this._text('[data-name="solar"]', language.solar);
    this._text('[data-name="grid"]', language.grid);
    this._text('[data-name="battery"]', language.battery);
    this._text('[data-name="home"]', language.home);

    this._text('[data-power="solar"]', formatWatts(model.solarW, locale));
    this._text('[data-power="grid"]', formatWatts(model.gridW, locale));
    this._text('[data-power="battery"]', formatWatts(model.batteryW, locale));
    this._text('[data-power="home"]', formatWatts(model.houseW, locale));

    this._text('[data-detail="solar"]',
      model.solarW !== null ? language[model.directions.solar] : "");
    this._text('[data-detail="grid"]',
      model.gridW !== null ? language[model.directions.grid] : "");
    const btext = model.batteryW !== null
      ? language[model.directions.battery] : "";
    const soc = model.batterySoc !== null
      ? new Intl.NumberFormat(locale, { maximumFractionDigits: 0 }).format(model.batterySoc) + " %" : "";
    this._text('[data-detail="battery"]', [btext, soc].filter(Boolean).join(" · "));
    this._text('[data-detail="home"]', "");

    this._line("solar", model.directions.solar === "production",
      "M300 92 L300 160", model.solarW);
    this._line("grid", ["import", "export"].includes(model.directions.grid),
      model.directions.grid === "export"
        ? "M262 190 L122 190" : "M122 190 L262 190", model.gridW);
    this._line("battery", ["discharge", "charge"].includes(model.directions.battery),
      model.directions.battery === "charge"
        ? "M338 190 L478 190" : "M478 190 L338 190", model.batteryW);

    const freq = model.frequency !== null
      ? new Intl.NumberFormat(locale, {
          minimumFractionDigits: 1, maximumFractionDigits: 2,
        }).format(model.frequency) + " Hz" : "—";
    this._text("#frequency", language.freq + ": " + freq);
    this._text("#inverter", model.inverterState
      ? language.inverter + ": " + model.inverterState : "");
    for (const node of this._root.querySelectorAll("[data-node]")) {
      const source = model.sources?.[node.dataset.node];
      node.disabled = !source;
      node.title = source || language.notAvailable;
    }
  }

  _reset() {
    for (const item of this._root.querySelectorAll("[data-power]")) {
      item.textContent = "—";
    }
    for (const item of this._root.querySelectorAll("[data-detail]")) {
      item.textContent = "";
    }
    this._text("#frequency", "");
    this._text("#inverter", "");
    for (const elem of this._root.querySelectorAll(".flow")) {
      elem.classList.add("off");
    }
  }
}

if (typeof customElements !== "undefined" &&
    !customElements.get("local-ems-flow-card")) {
  customElements.define("local-ems-flow-card", LocalEMSFlowCard);
}

if (typeof window !== "undefined") {
  window.customCards = window.customCards || [];
  if (!window.customCards.some((card) => card.type === "local-ems-flow-card")) {
    window.customCards.push({
      type: "local-ems-flow-card",
      name: "Local EMS Energy Flow",
      description: "Grid, PV, battery and home power from the Local EMS integration",
      preview: false,
    });
  }
}
