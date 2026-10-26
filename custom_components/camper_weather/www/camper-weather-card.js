/* Camper Weather card v0.1.0-beta.1. No credentials or GPS history are stored here. */
const VERSION = "0.1.0-beta.1";
const CARD_TYPE = "camper-weather-card";

class CamperWeatherCard extends HTMLElement {
  static getConfigElement() { return document.createElement("camper-weather-card-editor"); }
  static getStubConfig() { return {type: `custom:${CARD_TYPE}`}; }
  setConfig(config) { this.config = {...config}; this._render(); }
  set hass(value) {
    const same = this._hass?.connection === value?.connection && this._hass?.states === value?.states;
    this._hass = value;
    if (!same) this._load();
  }
  async _load() {
    if (!this._hass || !this.config || this._loading) return;
    this._loading = true;
    try { this._data = await this._hass.callWS({type: "camper_weather/card_data", entry_id: this.config.entry_id}); }
    catch (error) { this._data = {errors: [error.message || "WebSocket-Fehler"]}; }
    finally { this._loading = false; this._render(); }
  }
  _render() {
    if (!this.config) return;
    const d = this._data || {};
    const current = d.current || {};
    this.innerHTML = `<ha-card><div class="wrap"><header><div><h2>Camper Weather</h2><small>${d.name || "Wetter"} · v${VERSION}</small></div><strong class="score">${d.camping_score ?? "—"}/100</strong></header><nav>${["Übersicht","Vorhersage","Warnungen","Aktivitäten","Planer","Karte","Anbieter"].map((x,i)=>`<button data-tab="${i}" class="${i===0?"active":""}">${x}</button>`).join("")}</nav><section class="panel">${this._overview(current,d)}</section></div></ha-card>`;
    this._style();
    this.querySelectorAll("button[data-tab]").forEach((button) => button.addEventListener("click", () => this._tab(Number(button.dataset.tab))));
  }
  _overview(c,d) { return `<div class="current"><span class="temp">${c.temperature ?? "—"}°C</span><span>Gefühlt ${c.apparent_temperature ?? "—"}°C</span><span>Wind ${c.wind ?? "—"} km/h</span><span>Böen ${c.gusts ?? "—"} km/h</span></div><div class="chips">${(d.risks || []).map(r=>`<span class="risk ${r.severity}">${r.reason}</span>`).join("") || "Keine berechneten Campingrisiken"}</div><p class="muted">Quellen: ${(d.sources || []).join(", ") || "keine"} · Aktualisiert: ${d.updated_at || "—"}</p>`; }
  _tab(index) { const d=this._data||{}; const panel=this.querySelector(".panel"); if(index===0) panel.innerHTML=this._overview(d.current||{},d); else if(index===1) panel.innerHTML=`<div class="forecast">${(d.forecast||[]).slice(0,24).map(h=>`<article><b>${new Date(h.time).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"})}</b><span>${h.temperature ?? "—"}°C</span><span>${h.wind ?? "—"} km/h</span><strong>${h.score ?? "—"}</strong></article>`).join("")}</div>`; else if(index===2) panel.innerHTML=`<h3>Warnungen</h3>${(d.warnings||[]).map(w=>`<article class="warning">${w.headline || w.description || "Amtliche Warnung"}</article>`).join("") || "Keine DWD-Warnungen empfangen."}`; else if(index===3||index===4) panel.innerHTML=`<h3>${index===3?"Aktivitäten":"Freizeitplaner"}</h3><p>Bewertung über die nächsten vier Vorhersagestunden ist über die Integration vorbereitet. Aktivität auswählen und Zeitraum planen folgt in der nächsten Beta.</p>`; else if(index===5) panel.innerHTML=this._map(d); else panel.innerHTML=`<h3>Anbieterstatus</h3><p>Aktiv: ${(d.sources||[]).join(", ") || "—"}</p><p>Fehler: ${(d.errors||[]).join(", ") || "keine"}</p>`; }
  _map(d) { const p=d.location||{}; const radar=d.radar||{}; return `<div class="map" data-lat="${p.latitude||0}" data-lon="${p.longitude||0}"><div class="map-controls"><button data-zoom="1">+</button><button data-zoom="-1">−</button></div><div class="marker">📍</div><div class="map-label">${p.latitude?.toFixed?.(4)||"—"}, ${p.longitude?.toFixed?.(4)||"—"}<br><small>OpenStreetMap · Radar: ${radar.source||"nicht verfügbar"}</small></div></div>`; }
  _style() { if(this.querySelector("style"))return; const s=document.createElement("style"); s.textContent=`:host{display:block}.wrap{padding:16px}header{display:flex;justify-content:space-between;align-items:center}h2{margin:0;font-size:1.2rem}.score{font-size:1.5rem;color:var(--primary-color)}small,.muted{color:var(--secondary-text-color)}nav{display:flex;gap:4px;overflow:auto;margin:14px -4px 10px}button{border:0;background:var(--secondary-background-color);color:var(--primary-text-color);border-radius:12px;padding:8px 10px;white-space:nowrap}button.active{background:var(--primary-color);color:var(--text-primary-color,#fff)}.current{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.temp{font-size:2rem;grid-column:span 2}.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:14px}.risk,.warning{padding:8px;border-radius:8px;background:var(--secondary-background-color);display:block}.risk.critical{background:rgba(220,50,50,.18)}.forecast{display:grid;grid-template-columns:repeat(auto-fill,minmax(90px,1fr));gap:6px}.forecast article{display:grid;gap:4px;padding:8px;border:1px solid var(--divider-color);border-radius:8px}.map{height:260px;background:linear-gradient(135deg,#dbeafe,#bbf7d0);position:relative;overflow:hidden;border-radius:10px;background-image:linear-gradient(rgba(255,255,255,.4) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.4) 1px,transparent 1px);background-size:32px 32px}.marker{position:absolute;left:50%;top:45%;font-size:28px;transform:translate(-50%,-50%)}.map-label{position:absolute;bottom:10px;left:10px;background:rgba(255,255,255,.85);color:#123;padding:6px;border-radius:6px}.map-controls{position:absolute;right:8px;top:8px;display:grid;gap:4px}`; this.appendChild(s); }
}
class CamperWeatherCardEditor extends HTMLElement { setConfig(config){this.config=config;this.innerHTML=`<label>Camper Weather Eintrag <input value="${config.entry_id||""}" placeholder="entry_id"></label>`;this.querySelector("input").addEventListener("change",e=>this.dispatchEvent(new CustomEvent("config-changed",{bubbles:true,composed:true,detail:{config:{...config,entry_id:e.target.value}}})));} }
if(!customElements.get(CARD_TYPE)) customElements.define(CARD_TYPE,CamperWeatherCard);
if(!customElements.get("camper-weather-card-editor")) customElements.define("camper-weather-card-editor",CamperWeatherCardEditor);
window.customCards=window.customCards||[];
if(!window.customCards.some(c=>c.type===CARD_TYPE)) window.customCards.push({type:CARD_TYPE,name:"Camper Weather",description:"Wetter- und Campingkarte für Wohnmobile",preview:true});

