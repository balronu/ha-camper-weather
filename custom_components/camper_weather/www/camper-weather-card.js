/* Camper Weather card v0.1.0-beta.2. No credentials or GPS history are stored here. */
const VERSION = "0.1.0-beta.2";
const CARD_TYPE = "camper-weather-card";
const TABS = ["Übersicht", "Vorhersage", "Warnungen", "Aktivitäten", "Planer", "Karte", "Anbieter"];
const ACTIVITIES = [["walking", "Spazieren"], ["hiking", "Wandern"], ["cycling", "Fahrrad"], ["ebike", "E-Bike"], ["jogging", "Joggen"], ["skiing", "Skifahren"], ["swimming", "Schwimmen"], ["barbecue", "Grillen"], ["fishing", "Angeln"]];

const esc = (value) => String(value ?? "—").replace(/[&<>\"']/g, (char) => ({"&":"&amp;", "<":"&lt;", ">":"&gt;", "\"":"&quot;", "'":"&#39;"}[char]));
const tileX = (lon, zoom) => Math.floor((lon + 180) / 360 * 2 ** zoom);
const tileY = (lat, zoom) => Math.floor((1 - Math.asinh(Math.tan(lat * Math.PI / 180)) / Math.PI) / 2 * 2 ** zoom);
const isoLocal = (date, time) => { const parsed = new Date(`${date}T${time}`); return Number.isNaN(parsed.getTime()) ? "" : parsed.toISOString(); };

class CamperWeatherCard extends HTMLElement {
  static getConfigElement() { return document.createElement("camper-weather-card-editor"); }
  static getStubConfig() { return {}; }
  setConfig(config) { this.config = {...config}; this._tabIndex = Number.isInteger(this._tabIndex) ? this._tabIndex : Number(config.default_view || 0); this._draft = this._draft || {}; this._ensureShell(); }
  set hass(value) {
    const connectionChanged = this._hass?.connection !== value?.connection;
    this._hass = value;
    if (connectionChanged || !this._data) this._load();
  }
  async _load() {
    if (!this._hass || !this.config || this._loading) return;
    this._loading = true;
    try { this._data = await this._hass.callWS({type: "camper_weather/card_data", entry_id: this.config.entry_id}); }
    catch (error) { this._data = {errors: [error?.message || "WebSocket-Fehler"]}; }
    finally { this._loading = false; this._ensureShell(); }
  }
  _ensureShell() {
    if (!this.config) return;
    if (!this.querySelector(".wrap")) {
      this.innerHTML = `<ha-card><div class="wrap"><header><div><h2>Camper Weather</h2><small class="subtitle"></small></div><strong class="score"></strong></header><nav></nav><section class="panel"></section></div></ha-card>`;
      this._style();
      this.addEventListener("click", (event) => this._click(event));
      this.addEventListener("change", (event) => this._change(event));
    }
    const data = this._data || {};
    this.querySelector(".subtitle").textContent = `${data.name || "Wetter"} · v${VERSION}`;
    this.querySelector(".score").textContent = `${data.camping_score ?? "—"}/100`;
    const nav = this.querySelector("nav");
    const visible = this.config.visible_views || TABS.map((_, index) => index);
    nav.innerHTML = TABS.map((name, index) => visible.includes(index) ? `<button data-tab="${index}" class="${index === this._tabIndex ? "active" : ""}">${name}</button>` : "").join("");
    this._renderPanel();
  }
  _click(event) {
    const tab = event.target.closest("[data-tab]");
    if (tab) { this._tabIndex = Number(tab.dataset.tab); this._ensureShell(); return; }
    if (event.target.matches("[data-map-zoom]")) { this._mapZoom(Number(event.target.dataset.mapZoom)); return; }
    if (event.target.matches("[data-radar-frame]")) { this._radarFrame(Number(event.target.dataset.radarFrame)); return; }
    if (event.target.matches("[data-radar-play]")) { this._radarPlaying = !this._radarPlaying; this._radarLoop(); this._renderPanel(); return; }
    if (event.target.matches("[data-plan-action]")) { this._planAction(event.target.dataset.planAction); return; }
    if (event.target.matches("[data-delete-plan]")) { this._deletePlan(event.target.dataset.deletePlan); }
  }
  _change(event) {
    if (event.target.matches("[data-plan-field]")) this._draft[event.target.dataset.planField] = event.target.value;
    if (event.target.matches("[data-radar-speed]")) { this._radarSpeed = Number(event.target.value); }
  }
  _renderPanel() {
    const panel = this.querySelector(".panel"); if (!panel) return;
    const d = this._data || {};
    if (this._tabIndex === 0) panel.innerHTML = this._overview(d.current || {}, d);
    else if (this._tabIndex === 1) panel.innerHTML = `<div class="forecast">${(d.forecast || []).slice(0, 48).map((h) => `<article><b>${new Date(h.time).toLocaleString([], {weekday:"short",hour:"2-digit",minute:"2-digit"})}</b><span>${esc(h.temperature)} °C</span><span>Wind ${esc(h.wind)} km/h</span><strong>${esc(h.score)}/100</strong></article>`).join("") || "Keine Prognosedaten."}</div>`;
    else if (this._tabIndex === 2) panel.innerHTML = `<h3>Amtliche Warnungen</h3>${(d.warnings || []).map((warning) => `<article class="warning"><b>${esc(warning.headline || warning.event || "DWD-Warnung")}</b><br>${esc(warning.description || warning.instruction || "")}</article>`).join("") || "Keine DWD-Warnungen empfangen."}`;
    else if (this._tabIndex === 3) panel.innerHTML = this._activities(d);
    else if (this._tabIndex === 4) { panel.innerHTML = this._planner(d); if (!this._plans && this._data?.entry_id) this._loadPlans(); }
    else if (this._tabIndex === 5) panel.innerHTML = this._map(d);
    else panel.innerHTML = `<h3>Anbieterstatus</h3><p>Aktiv: ${esc((d.sources || []).join(", ") || "—")}</p><p>Fehler: ${esc((d.errors || []).join(", ") || "keine")}</p><p class="muted">Datenalter: ${esc(d.updated_at || "—")}</p>`;
  }
  _overview(current, d) { return `<div class="current"><span class="temp">${esc(current.temperature)}°C</span><span>Gefühlt ${esc(current.apparent_temperature)}°C</span><span>Wind ${esc(current.wind)} km/h</span><span>Böen ${esc(current.gusts)} km/h</span></div><div class="chips">${(d.risks || []).map((risk) => `<span class="risk ${esc(risk.severity)}">${esc(risk.reason)}</span>`).join("") || "Keine berechneten Campingrisiken"}</div><p class="muted">Quellen: ${esc((d.sources || []).join(", ") || "keine")} · Aktualisiert: ${esc(d.updated_at)}</p>`; }
  _activities(d) { const recommendation = Object.values(d.recommendations || {}).flat().sort((a, b) => (b.score || 0) - (a.score || 0)).slice(0, 5); return `<h3>Aktivitätsbewertungen</h3><p>Bewertung basiert auf echten Prognosestunden; kritische Risiken setzen den Score auf 0.</p>${recommendation.map((item) => `<article class="recommendation"><b>${new Date(item.start).toLocaleString([], {weekday:"short",hour:"2-digit",minute:"2-digit"})}</b> · ${esc(item.score)}/100 · ${esc(item.duration_minutes)} min</article>`).join("") || "Keine ausreichenden Prognosedaten für Empfehlungen."}`; }
  _planner(d) { const draft = this._draft; const now = new Date(Date.now() + 3600000); const date = draft.date || now.toISOString().slice(0, 10); const time = draft.time || now.toISOString().slice(11, 16); const plans = this._plans || []; return `<h3>Freizeitplaner</h3><div class="form"><label>Aktivität<select data-plan-field="activity">${ACTIVITIES.map(([key, label]) => `<option value="${key}" ${(draft.activity || "walking") === key ? "selected" : ""}>${label}</option>`).join("")}</select></label><label>Datum<input data-plan-field="date" type="date" value="${esc(date)}"></label><label>Startzeit<input data-plan-field="time" type="time" value="${esc(time)}"></label><label>Dauer (Minuten)<input data-plan-field="duration_minutes" type="number" min="15" max="720" step="15" value="${esc(draft.duration_minutes || 120)}"></label><label>Standort<select data-plan-field="location_mode"><option value="current">Aktueller GPS-Standort</option><option value="manual">Manueller Standort</option></select></label></div><p>${this._assessment ? `${esc(this._assessment.score ?? "—")}/100 · ${esc((this._assessment.risks || []).map((risk) => risk.reason).join("; ") || "Keine Risiken")}` : "Ändere die Planung für eine Bewertung."}</p><button data-plan-action="assess">Bewerten</button> <button data-plan-action="save">Speichern</button><h4>Gespeicherte Aktivitäten</h4>${plans.map((plan) => `<article class="plan"><b>${esc(plan.activity)}</b> · ${esc(plan.start_at)} · ${esc(plan.duration_minutes)} min · ${esc(plan.assessment?.score ?? "—")}/100 <button data-delete-plan="${esc(plan.id)}">Löschen</button></article>`).join("") || "Noch keine gespeicherten Aktivitäten."}`; }
  async _planAction(action) { if (action === "assess") await this._assessPlan(); if (action === "save") { await this._assessPlan(); const plan = this._planPayload(); try { await this._hass.callWS({type:"camper_weather/planner/save", entry_id:this._data.entry_id, ...plan}); await this._loadPlans(); } catch (error) { this._assessment = {score:null, risks:[{reason:error.message}]}; this._renderPanel(); } } }
  _planPayload() { const draft = this._draft; return {activity:draft.activity || "walking", start_at:isoLocal(draft.date || new Date().toISOString().slice(0,10), draft.time || "12:00"), duration_minutes:Number(draft.duration_minutes || 120), location_mode:draft.location_mode || "current"}; }
  async _assessPlan() { if (!this._hass || !this._data?.entry_id) return; try { this._assessment = await this._hass.callWS({type:"camper_weather/planner/assess", entry_id:this._data.entry_id, ...this._planPayload()}); this._renderPanel(); } catch (_) { /* The form remains usable while the connection recovers. */ } }
  async _loadPlans() { try { this._plans = await this._hass.callWS({type:"camper_weather/planner/list", entry_id:this._data.entry_id}); } catch (_) { this._plans = []; } this._renderPanel(); }
  async _deletePlan(id) { await this._hass.callWS({type:"camper_weather/planner/delete", entry_id:this._data.entry_id, plan_id:id}); await this._loadPlans(); }
  _map(d) { const location = d.location || {}; const radar = d.radar || {}; const frames = radar.frames || []; const frame = frames[this._radarIndex || 0]; const zoom = this._mapState?.zoom || 5; const x = tileX(Number(location.longitude) || 0, zoom); const y = tileY(Number(location.latitude) || 0, zoom); const tiles = []; for (let dx = -1; dx <= 1; dx += 1) for (let dy = -1; dy <= 1; dy += 1) { const tx = x + dx, ty = y + dy; const base = `https://tile.openstreetmap.org/${zoom}/${tx}/${ty}.png`; const overlay = frame ? `<img class="tile radar" src="${frame.tile_template.replace("{z}", zoom).replace("{x}", tx).replace("{y}", ty)}" alt="Radar" loading="lazy">` : ""; tiles.push(`<div class="tile-wrap" style="left:${(dx + 1) * 33.33}%;top:${(dy + 1) * 33.33}%"><img class="tile" src="${base}" alt="OpenStreetMap" loading="lazy">${overlay}</div>`); } return `<div class="map"><div class="tiles">${tiles.join("")}</div><div class="marker">📍</div><div class="map-controls"><button data-map-zoom="1">+</button><button data-map-zoom="-1">−</button></div><div class="map-label">${esc(Number(location.latitude).toFixed?.(4))}, ${esc(Number(location.longitude).toFixed?.(4))}<br><small>© OpenStreetMap · Radar: © <a href="https://www.rainviewer.com/" target="_blank" rel="noreferrer">RainViewer</a></small></div></div><div class="radar-controls"><button data-radar-play>${this._radarPlaying ? "Pause" : "Start"}</button><input data-radar-speed type="range" min="250" max="1500" step="250" value="${this._radarSpeed || 750}">${frames.map((item, index) => `<button data-radar-frame="${index}" class="${index === (this._radarIndex || 0) ? "active" : ""}">${new Date(Number(item.time) * 1000).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"})}</button>`).join("") || "Keine Radarframes verfügbar."}</div>`; }
  _mapZoom(delta) { this._mapState = {...this._mapState, zoom: Math.max(3, Math.min(7, (this._mapState?.zoom || 5) + delta))}; this._renderPanel(); }
  _radarFrame(index) { this._radarIndex = index; this._renderPanel(); }
  _radarLoop() { clearTimeout(this._radarTimer); if (!this._radarPlaying) return; const frames = this._data?.radar?.frames || []; this._radarIndex = ((this._radarIndex || 0) + 1) % Math.max(frames.length, 1); this._renderPanel(); this._radarTimer = setTimeout(() => this._radarLoop(), this._radarSpeed || 750); }
  _style() { if (this.querySelector("style")) return; const s = document.createElement("style"); s.textContent = `:host{display:block}.wrap{padding:16px}header{display:flex;justify-content:space-between;align-items:center}h2{margin:0;font-size:1.2rem}.score{font-size:1.5rem;color:var(--primary-color)}small,.muted{color:var(--secondary-text-color)}nav{display:flex;gap:4px;overflow:auto;margin:14px -4px 10px}button,select,input{border:1px solid var(--divider-color);background:var(--secondary-background-color);color:var(--primary-text-color);border-radius:8px;padding:8px;white-space:nowrap}button{cursor:pointer}button.active{background:var(--primary-color);color:var(--text-primary-color,#fff)}.current{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.temp{font-size:2rem;grid-column:span 2}.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:14px}.risk,.warning,.recommendation,.plan{padding:8px;margin:6px 0;border-radius:8px;background:var(--secondary-background-color)}.risk.critical{background:rgba(220,50,50,.18)}.forecast{display:grid;grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:6px}.forecast article{display:grid;gap:4px;padding:8px;border:1px solid var(--divider-color);border-radius:8px}.form{display:grid;gap:8px}.form label{display:grid;gap:4px}.map{height:300px;position:relative;overflow:hidden;border-radius:10px;background:#cde3c1}.tiles{position:absolute;inset:0}.tile-wrap{position:absolute;width:33.34%;height:33.34%;overflow:hidden}.tile,.radar{position:absolute;width:100%;height:100%;object-fit:cover}.radar{opacity:.58}.marker{position:absolute;left:50%;top:50%;font-size:28px;transform:translate(-50%,-50%);z-index:3}.map-label{position:absolute;bottom:8px;left:8px;background:rgba(255,255,255,.88);color:#123;padding:6px;border-radius:6px;z-index:4}.map-controls{position:absolute;right:8px;top:8px;display:grid;gap:4px;z-index:4}.radar-controls{display:flex;gap:5px;align-items:center;overflow:auto;margin-top:8px}.radar-controls input{min-width:80px;max-width:120px}@media(max-width:600px){.wrap{padding:12px}.radar-controls{flex-wrap:wrap}.current{grid-template-columns:1fr 1fr}}`; this.appendChild(s); }
}

class CamperWeatherCardEditor extends HTMLElement {
  setConfig(config) { this.config = {...config}; const visible = config.visible_views || TABS.map((_, index) => index); this.innerHTML = `<div class="editor"><label>Camper Weather Eintrag <input data-key="entry_id" value="${esc(config.entry_id || "")}" placeholder="entry_id"></label><label>Standardansicht <select data-key="default_view">${TABS.map((tab, index) => `<option value="${index}" ${String(config.default_view ?? 0) === String(index) ? "selected" : ""}>${tab}</option>`).join("")}</select></label><fieldset><legend>Sichtbare Bereiche</legend>${TABS.map((tab, index) => `<label><input type="checkbox" data-view="${index}" ${visible.includes(index) ? "checked" : ""}> ${tab}</label>`).join("")}</fieldset><p>Die Karte lädt den einzigen geladenen Eintrag automatisch; entry_id ist nur bei mehreren Fahrzeugen erforderlich.</p></div>`; this.querySelectorAll("[data-key]").forEach((input) => input.addEventListener("change", () => { const next = {...this.config, [input.dataset.key]: input.value}; this.dispatchEvent(new CustomEvent("config-changed", {bubbles:true, composed:true, detail:{config:next}})); })); this.querySelectorAll("[data-view]").forEach((input) => input.addEventListener("change", () => { const next = {...this.config, visible_views: [...this.querySelectorAll("[data-view]:checked")].map((item) => Number(item.dataset.view))}; this.dispatchEvent(new CustomEvent("config-changed", {bubbles:true, composed:true, detail:{config:next}})); })); }
}
if (!customElements.get(CARD_TYPE)) customElements.define(CARD_TYPE, CamperWeatherCard);
if (!customElements.get("camper-weather-card-editor")) customElements.define("camper-weather-card-editor", CamperWeatherCardEditor);
window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === CARD_TYPE)) window.customCards.push({type:CARD_TYPE, name:"Camper Weather", description:"Wetter- und Campingkarte für Wohnmobile", preview:true});
