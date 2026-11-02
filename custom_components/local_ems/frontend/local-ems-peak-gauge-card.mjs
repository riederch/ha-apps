// SPDX-License-Identifier: GPL-3.0-or-later
/** 15-minute demand gauge, bundled with the Local EMS Home Assistant integration. */
import {
  arcPath, formatKw, formatRemaining, makePeakGaugeModel, needleTip,
} from "./peak-gauge-model.mjs";

const I18N = {
  de: {
    title: "15-Minuten-Netzbezug",
    actual: "Ist-Durchschnitt",
    forecast: "Prognose",
    warning: "Warnschwelle",
    limit: "Grenzwert",
    notFound: "Kein Local-EMS-Peak-Monitor gefunden.",
    noData: "Noch kein gültiger Viertelstundenwert.",
    starting: "Startet",
    source_unavailable: "Zähler nicht verfügbar",
    quarter_rollover: "Viertelstundenwechsel",
    waiting_for_sample: "Warte auf Messwert",
    missing_boundary: "Zählerstand zum Intervallbeginn fehlt",
    boundary_gap: "Zu große Lücke am Intervallbeginn",
    stale: "Zählerwert veraltet",
    counter_reset: "Zählerstand zurückgesetzt",
    invalid_configuration: "Grenzwerte ungültig",
    missing_source: "Zählerdaten fehlen",
    estimated_boundary: "Intervallbeginn interpoliert",
    ok: "Messung gültig",
    quality: "Datenqualität",
    remaining: "Noch",
    forecastWarning: "Prognose über der Warnschwelle",
    forecastLimit: "Prognose am/über dem Grenzwert",
    hover: "Local-EMS-Datenqualität anzeigen",
  },
  en: {
    title: "15-minute grid demand",
    actual: "Actual average",
    forecast: "Forecast",
    warning: "Warning threshold",
    limit: "Demand limit",
    notFound: "No Local EMS peak monitor found.",
    noData: "No valid quarter-hour demand reading yet.",
    starting: "Starting",
    source_unavailable: "Meter unavailable",
    quarter_rollover: "Quarter-hour rollover",
    waiting_for_sample: "Waiting for sample",
    missing_boundary: "Missing meter reading at interval start",
    boundary_gap: "Excessive gap at interval start",
    stale: "Meter reading stale",
    counter_reset: "Meter counter reset",
    invalid_configuration: "Invalid limits",
    missing_source: "No meter samples",
    estimated_boundary: "Interval boundary interpolated",
    ok: "Measurement valid",
    quality: "Data quality",
    remaining: "Remaining",
    forecastWarning: "Forecast above warning threshold",
    forecastLimit: "Forecast at/above demand limit",
    hover: "Open Local EMS measurement quality",
  },
};

const CSS = [
  ":host{display:block;width:100%;min-width:0;}",
  "ha-card{box-sizing:border-box;padding:16px 16px 12px;width:100%;}",
  ".head{display:flex;justify-content:space-between;align-items:center;gap:8px;}",
  ".title{font-size:1.04rem;font-weight:600;color:var(--primary-text-color);}",
  ".status{font-size:.75rem;padding:5px 9px;border-radius:20px;",
  "background:var(--secondary-background-color);color:var(--secondary-text-color);",
  "white-space:nowrap;}",
  ".status[data-severity='ok']{color:var(--success-color,#2da66b);}",
  ".status[data-severity='warning']{color:var(--warning-color,#dda621);}",
  ".status[data-severity='limit']{color:var(--error-color,#db5353);}",
  ".gauge{width:100%;max-width:345px;margin:2px auto 0;text-align:center;}",
  ".gauge svg{width:100%;height:auto;display:block;overflow:visible;}",
  ".arc{fill:none;stroke-width:16;stroke-linecap:butt;}",
  ".arc-green{stroke:var(--success-color,#2da66b);}",
  ".arc-yellow{stroke:var(--warning-color,#dda621);}",
  ".arc-red{stroke:var(--error-color,#db5353);}",
  ".arc-empty{stroke:var(--divider-color,rgba(127,127,127,.3));}",
  "#needle{stroke:var(--primary-text-color);stroke-width:3.5;stroke-linecap:round;}",
  "#needle-hub{fill:var(--primary-text-color);}",
  ".marks{font-size:12px;fill:var(--secondary-text-color);}",
  ".actual{font-size:1.95rem;line-height:1.1;font-weight:700;",
  "color:var(--primary-text-color);font-variant-numeric:tabular-nums;}",
  ".actual-caption{font-size:.78rem;color:var(--secondary-text-color);margin-top:4px;}",
  ".stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:4px;",
  "margin-top:15px;}",
  ".stat{text-align:center;min-width:0;padding:4px 2px;}",
  ".stat-title{font-size:.73rem;color:var(--secondary-text-color);margin-bottom:5px;}",
  ".stat-value{font-size:1rem;font-weight:600;white-space:nowrap;",
  "color:var(--primary-text-color);font-variant-numeric:tabular-nums;}",
  ".stat-value.warning{color:var(--warning-color,#dda621);}",
  ".stat-value.limit{color:var(--error-color,#db5353);}",
  ".footer{border-top:1px solid var(--divider-color);margin-top:12px;",
  "padding-top:10px;display:flex;align-items:center;justify-content:space-between;",
  "gap:6px;font-size:.73rem;color:var(--secondary-text-color);}",
  ".quality{margin-top:7px;color:var(--secondary-text-color);",
  "font-size:.71rem;text-align:center;}",
  ".hint{margin:8px 0 2px;color:var(--secondary-text-color);",
  "font-size:.78rem;line-height:1.4;text-align:center;}",
  ".hint:empty{display:none;}",
  "@media(max-width:400px){ha-card{padding:14px 10px;}",
  ".title{font-size:.96rem;}.stat-value{font-size:.85rem;}",
  ".actual{font-size:1.65rem;}.status{font-size:.68rem;}}",
].join("");

const LAYOUT = [
  "<style>", CSS, "</style>",
  "<ha-card>",
  '<div class="head"><span class="title" id="title"></span>',
  '<span class="status" id="status" data-severity="unknown"></span></div>',
  '<div class="gauge">',
  '<svg viewBox="0 0 320 180" role="img" aria-label="Quarter-hour demand">',
  '<path class="arc arc-empty" id="arc-empty"></path>',
  '<path class="arc arc-green" id="arc-green"></path>',
  '<path class="arc arc-yellow" id="arc-yellow"></path>',
  '<path class="arc arc-red" id="arc-red"></path>',
  '<line id="needle" x1="160" y1="150" x2="160" y2="55"></line>',
  '<circle id="needle-hub" cx="160" cy="150" r="7"></circle>',
  '<text class="marks" x="43" y="176" text-anchor="middle">0</text>',
  '<text class="marks" id="scale-max" x="277" y="176" text-anchor="middle"></text>',
  "</svg>",
  '<div class="actual" id="actual">—</div>',
  '<div class="actual-caption" id="actual-caption"></div>',
  "</div>",
  '<div class="stats">',
  '<div class="stat"><div class="stat-title" id="forecast-label"></div>',
  '<div class="stat-value" id="forecast"></div></div>',
  '<div class="stat"><div class="stat-title" id="warning-label"></div>',
  '<div class="stat-value warning" id="warning"></div></div>',
  '<div class="stat"><div class="stat-title" id="limit-label"></div>',
  '<div class="stat-value limit" id="limit"></div></div>',
  "</div>",
  '<div class="footer"><span id="window"></span><span id="remaining"></span></div>',
  '<div class="quality" id="quality"></div>',
  '<div class="hint" id="hint"></div>',
  "</ha-card>",
].join("");

export class LocalEMSPeakGaugeCard extends HTMLElement {
  constructor() {
    super();
    this._root = this.attachShadow({ mode: "open" });
    this._root.innerHTML = LAYOUT;
    this._config = {};
    this._qualityEntity = null;
    this._root.querySelector("ha-card").addEventListener("click", () => {
      if (!this._qualityEntity) return;
      this.dispatchEvent(new CustomEvent("hass-more-info", {
        bubbles: true, composed: true,
        detail: { entityId: this._qualityEntity.entity_id },
      }));
    });
  }

  setConfig(config) {
    if (config.entity && (typeof config.entity !== "string" ||
        !config.entity.startsWith("sensor."))) {
      throw new Error("Local EMS Peak Gauge: entity must be a sensor");
    }
    this._config = { ...config };
    this._update();
  }

  set hass(hass) {
    this._hass = hass;
    this._update();
  }

  getCardSize() { return 5; }

  getGridOptions() {
    return { columns: 6, min_columns: 4, max_columns: 12, rows: "auto" };
  }

  static getStubConfig() { return {}; }

  _strings() {
    return String(this._hass?.language || "de").startsWith("de")
      ? I18N.de : I18N.en;
  }

  _text(id, value) {
    this._root.getElementById(id).textContent = value ?? "";
  }

  _findQualityEntity() {
    const all = this._hass?.states || {};
    if (this._config.entity) return all[this._config.entity] || null;
    return Object.values(all).find((state) => (
      state.entity_id?.startsWith("sensor.") &&
      state.attributes?.ems_peak_gauge_version === 1
    )) || null;
  }

  _setArc(id, from, to, max) {
    this._root.getElementById("arc-" + id).setAttribute(
      "d", arcPath(from, to, max)
    );
  }

  _formatInterval(model, locale) {
    if (!model.quarterStart || !model.quarterEnd) return "";
    const start = new Date(model.quarterStart);
    const end = new Date(model.quarterEnd);
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return "";
    const options = {
      hour: "2-digit", minute: "2-digit", hour12: false,
    };
    const timeZone = this._hass?.config?.time_zone;
    if (timeZone) options.timeZone = timeZone;
    const formatter = new Intl.DateTimeFormat(locale, options);
    return formatter.format(start) + "–" + formatter.format(end);
  }

  _update() {
    if (!this._hass) return;
    const t = this._strings();
    const locale = this._hass.locale?.language || this._hass.language || "de-AT";
    this._text("title", this._config.title || t.title);
    this._text("actual-caption", t.actual);
    this._text("forecast-label", t.forecast);
    this._text("warning-label", t.warning);
    this._text("limit-label", t.limit);

    const source = this._findQualityEntity();
    this._qualityEntity = source;
    const model = makePeakGaugeModel(source?.attributes);
    const status = this._root.getElementById("status");
    status.dataset.severity = source ? model.severity : "invalid";
    status.textContent = !source ? t.noData :
      model.severity === "limit" ? t.forecastLimit :
      model.severity === "warning" ? t.forecastWarning :
      model.valid ? t.ok : t.noData;

    this._text("actual", formatKw(model.averageKw, locale));
    this._text("forecast", formatKw(model.forecastKw, locale));
    this._text("warning", formatKw(model.warningKw, locale));
    this._text("limit", formatKw(model.limitKw, locale));
    this._text("scale-max", formatKw(model.scaleMax, locale));
    this._text("window", this._formatInterval(model, locale));
    this._text("remaining", model.valid &&
      model.remainingSeconds !== null
      ? t.remaining + " " + formatRemaining(model.remainingSeconds) : "");
    this._text("quality", source ? t.quality + ": " +
      (t[model.quality] || model.quality.replaceAll("_", " ")) : "");

    if (model.warningKw !== null && model.limitKw !== null) {
      this._setArc("empty", 0, 0, model.scaleMax);
      this._setArc("green", 0, model.warningKw, model.scaleMax);
      this._setArc("yellow", model.warningKw, model.limitKw, model.scaleMax);
      this._setArc("red", model.limitKw, model.scaleMax, model.scaleMax);
    } else {
      this._setArc("empty", 0, model.scaleMax, model.scaleMax);
      for (const name of ["green", "yellow", "red"]) {
        this._setArc(name, 0, 0, model.scaleMax);
      }
    }
    const tip = needleTip(model.needleFraction);
    const needle = this._root.getElementById("needle");
    const hub = this._root.getElementById("needle-hub");
    needle.style.display = hub.style.display = tip ? "" : "none";
    if (tip) {
      needle.setAttribute("x2", tip.x.toFixed(2));
      needle.setAttribute("y2", tip.y.toFixed(2));
    }
    this._text("hint", !source ? t.notFound :
      !model.valid ? t[model.quality] || t.noData :
      model.averageKw === null ? t.noData : "");
  }
}

if (typeof customElements !== "undefined" &&
    !customElements.get("local-ems-peak-gauge-card")) {
  customElements.define("local-ems-peak-gauge-card", LocalEMSPeakGaugeCard);
}

if (typeof window !== "undefined") {
  window.customCards = window.customCards || [];
  if (!window.customCards.some((c) => c.type === "local-ems-peak-gauge-card")) {
    window.customCards.push({
      type: "local-ems-peak-gauge-card",
      name: "Local EMS 15-minute Gauge",
      description: "Elapsed-quarter import average and demand forecast",
      preview: false,
    });
  }
}
