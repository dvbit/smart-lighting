/**
 * Smart Lighting Card v9 - Custom Lovelace Card
 *
 * Features:
 * - Area name displayed under light icon
 * - Customizable main and soft profile icons
 * - Click status icons to open more-info of source entity
 * - Timer bar with 1s refresh
 * - Mode indicator (localized)
 * - Settings popup with all number entities
 * - Localized: EN, IT, FR, ES, DE
 *
 * YAML config:
 *   type: custom:smart-lighting-card
 *   area: cucina                        # required: area name
 *   name: Cucina                        # optional: display name (default: area)
 *   icon_main: mdi:ceiling-light        # optional: icon when normal profile
 *   icon_soft: mdi:lamp                 # optional: icon when soft profile
 */

var SL_I18N = {
  en: {
    idle: "Idle", active: "Automatic", warning: "Warning",
    temp_override: "Manual", perm_override: "Override", suspended: "Suspended",
    settings: "Settings", state: "State", profile: "Profile",
    adaptive_factor: "Adaptive Factor", activations: "Activations",
    occupancy_timeout: "Occupancy Timeout", failsafe_timeout: "Failsafe Timeout",
    override_timeout: "Override Timeout", temp_override_timeout: "Temp Override Timeout",
    warning_dim_pct: "Warning Dim %", warning_dim_duration: "Warning Dim Duration", no_motion_timeout: "No-Motion Timeout",
    lux_threshold: "Lux Threshold", set_lux: "Set Lux from Sensor",
    adaptive_window: "Adaptive Window", adaptive_threshold_n: "Adaptive Threshold",
    adaptive_multiplier: "Adaptive Multiplier", adaptive_max_factor: "Max Adaptive Factor",
    lux_hysteresis_pct: "Lux Hysteresis %", lux_hysteresis_time: "Lux Hysteresis Time"
  },
  it: {
    idle: "Inattivo", active: "Automatico", warning: "Avviso",
    temp_override: "Manuale", perm_override: "Override", suspended: "Sospeso",
    settings: "Impostazioni", state: "Stato", profile: "Profilo",
    adaptive_factor: "Fattore Adattivo", activations: "Attivazioni",
    occupancy_timeout: "Timeout Presenza", failsafe_timeout: "Timeout Sicurezza",
    override_timeout: "Timeout Override", temp_override_timeout: "Timeout Override Temp.",
    warning_dim_pct: "Attenuazione Avviso %", warning_dim_duration: "Durata Attenuazione", no_motion_timeout: "Timeout Senza Movimento",
    lux_threshold: "Soglia Lux", set_lux: "Imposta Lux da Sensore",
    adaptive_window: "Finestra Adattiva", adaptive_threshold_n: "Soglia Adattiva",
    adaptive_multiplier: "Moltiplicatore Adattivo", adaptive_max_factor: "Fattore Max Adattivo",
    lux_hysteresis_pct: "Isteresi Lux %", lux_hysteresis_time: "Tempo Isteresi Lux"
  },
  fr: {
    idle: "Inactif", active: "Automatique", warning: "Avertissement",
    temp_override: "Manuel", perm_override: "Forçage", suspended: "Suspendu",
    settings: "Paramètres", state: "État", profile: "Profil",
    adaptive_factor: "Facteur Adaptatif", activations: "Activations",
    occupancy_timeout: "Délai Présence", failsafe_timeout: "Délai Sécurité",
    override_timeout: "Délai Forçage", temp_override_timeout: "Délai Override Temp.",
    warning_dim_pct: "Atténuation %", warning_dim_duration: "Durée Atténuation", no_motion_timeout: "Délai Sans Mouvement",
    lux_threshold: "Seuil Lux", set_lux: "Définir Lux depuis Capteur",
    adaptive_window: "Fenêtre Adaptative", adaptive_threshold_n: "Seuil Adaptatif",
    adaptive_multiplier: "Multiplicateur Adaptatif", adaptive_max_factor: "Facteur Max Adaptatif",
    lux_hysteresis_pct: "Hystérésis Lux %", lux_hysteresis_time: "Temps Hystérésis Lux"
  },
  es: {
    idle: "Inactivo", active: "Automático", warning: "Advertencia",
    temp_override: "Manual", perm_override: "Anulación", suspended: "Suspendido",
    settings: "Ajustes", state: "Estado", profile: "Perfil",
    adaptive_factor: "Factor Adaptativo", activations: "Activaciones",
    occupancy_timeout: "Timeout Ocupación", failsafe_timeout: "Timeout Seguridad",
    override_timeout: "Timeout Anulación", temp_override_timeout: "Timeout Override Temp.",
    warning_dim_pct: "Atenuación %", warning_dim_duration: "Duración Atenuación", no_motion_timeout: "Timeout Sin Movimiento",
    lux_threshold: "Umbral Lux", set_lux: "Fijar Lux desde Sensor",
    adaptive_window: "Ventana Adaptativa", adaptive_threshold_n: "Umbral Adaptativo",
    adaptive_multiplier: "Multiplicador Adaptativo", adaptive_max_factor: "Factor Max Adaptativo",
    lux_hysteresis_pct: "Histéresis Lux %", lux_hysteresis_time: "Tiempo Histéresis Lux"
  },
  de: {
    idle: "Inaktiv", active: "Automatisch", warning: "Warnung",
    temp_override: "Manuell", perm_override: "Überschreibung", suspended: "Pausiert",
    settings: "Einstellungen", state: "Status", profile: "Profil",
    adaptive_factor: "Adaptiver Faktor", activations: "Aktivierungen",
    occupancy_timeout: "Anwesenheits-Timeout", failsafe_timeout: "Sicherheits-Timeout",
    override_timeout: "Überschreibungs-Timeout", temp_override_timeout: "Temp. Override-Timeout",
    warning_dim_pct: "Dimmung %", warning_dim_duration: "Dimmung Dauer", no_motion_timeout: "Timeout Ohne Bewegung",
    lux_threshold: "Lux-Schwelle", set_lux: "Lux vom Sensor übernehmen",
    adaptive_window: "Adaptives Fenster", adaptive_threshold_n: "Adaptiver Schwellenwert",
    adaptive_multiplier: "Adaptiver Multiplikator", adaptive_max_factor: "Adaptiver Max-Faktor",
    lux_hysteresis_pct: "Lux-Hysterese %", lux_hysteresis_time: "Lux-Hysterese Zeit"
  }
};

class SmartLightingCard extends HTMLElement {

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._config = null;
    this._rendered = false;
    this._timer = null;
    this._lang = "en";
  }

  _t(key) {
    var d = SL_I18N[this._lang] || SL_I18N["en"];
    return d[key] || (SL_I18N["en"][key] || key);
  }

  setConfig(config) {
    if (!config.area) throw new Error("'area' is required");
    this._config = config;
    this._rendered = false;
    this._iconMain = config.icon_main || "mdi:ceiling-light";
    this._iconSoft = config.icon_soft || "mdi:lamp";

    var a = config.area;
    this._ent = {
      light:                "light.smart_lighting_" + a,
      state:                "sensor.smart_lighting_" + a + "_state",
      profile:              "sensor.smart_lighting_" + a + "_profile",
      occupancy_timer:      "sensor.smart_lighting_" + a + "_occupancy_timer",
      failsafe_timer:       "sensor.smart_lighting_" + a + "_failsafe_timer",
      override_timer:       "sensor.smart_lighting_" + a + "_override_timer",
      warning_timer:        "sensor.smart_lighting_" + a + "_warning_timer",
      adaptive_factor:      "sensor.smart_lighting_" + a + "_adaptive_factor",
      activation_count:     "sensor.smart_lighting_" + a + "_activation_count",
      lux:                  "sensor.smart_lighting_" + a + "_lux",
      occupancy_timeout:    "number.smart_lighting_" + a + "_occupancy_timeout",
      failsafe_timeout:     "number.smart_lighting_" + a + "_failsafe_timeout",
      perm_override_timeout:"number.smart_lighting_" + a + "_perm_override_timeout",
      temp_override_timeout:"number.smart_lighting_" + a + "_temp_override_timeout",
      warning_dim_pct:      "number.smart_lighting_" + a + "_warning_dim_pct",
      warning_dim_duration: "number.smart_lighting_" + a + "_warning_dim_duration",
      no_motion_timeout:    "number.smart_lighting_" + a + "_no_motion_timeout",
      lux_threshold:        "number.smart_lighting_" + a + "_lux_threshold",
      adaptive_window:      "number.smart_lighting_" + a + "_adaptive_window",
      adaptive_threshold_n: "number.smart_lighting_" + a + "_adaptive_threshold",
      adaptive_multiplier:  "number.smart_lighting_" + a + "_adaptive_multiplier",
      adaptive_max_factor:  "number.smart_lighting_" + a + "_adaptive_max_factor",
      lux_hysteresis_pct:   "number.smart_lighting_" + a + "_lux_hysteresis_pct",
      lux_hysteresis_time:  "number.smart_lighting_" + a + "_lux_hysteresis_time",
      set_lux_threshold:    "button.smart_lighting_" + a + "_set_lux_threshold"
    };
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._config) return;
    var newLang = (hass.language || "en").split("-")[0].toLowerCase();
    if (newLang !== this._lang) { this._lang = newLang; this._rendered = false; }
    if (!this._rendered) this._build();
    this._refresh();
  }

  getCardSize() { return 4; }

  connectedCallback() {
    var self = this;
    this._timer = setInterval(function() {
      if (self._hass && self._rendered) self._refreshBar();
    }, 1000);
  }

  disconnectedCallback() {
    if (this._timer) { clearInterval(this._timer); this._timer = null; }
  }

  /* ── Helpers ────────────────────────────────────────────── */

  _st(id) {
    if (!this._hass || !this._hass.states || !this._hass.states[id]) return "unavailable";
    return this._hass.states[id].state;
  }

  _num(id) { var v = parseFloat(this._st(id)); return isNaN(v) ? 0 : v; }

  _lightAttr(key) {
    var s = this._hass && this._hass.states && this._hass.states[this._ent.light];
    if (!s || !s.attributes) return undefined;
    return s.attributes[key];
  }

  /** Fire hass-more-info event to open entity popup */
  _moreInfo(entityId) {
    var ev = new Event("hass-more-info", { bubbles: true, composed: true });
    ev.detail = { entityId: entityId };
    this.shadowRoot.dispatchEvent(ev);
  }

  _activeTimer() {
    var s = this._st(this._ent.state);
    if (s === "perm_override") {
      return { rem: this._num(this._ent.override_timer),
               tot: this._num(this._ent.perm_override_timeout) || 3600,
               icon: "mdi:cancel", color: "#db4437" };
    }
    if (s === "temp_override") {
      var rem = this._num(this._ent.override_timer);
      var tot = this._num(this._ent.temp_override_timeout);
      if (tot > 0 && rem > 0) {
        return { rem: rem, tot: tot, icon: "mdi:hand-back-left", color: "#ffa726" };
      }
      return { rem: 1, tot: 1, icon: "mdi:hand-back-left", color: "#ffa726" };
    }
    if (s === "warning") {
      var r = this._num(this._ent.warning_timer);
      return { rem: r, tot: r || 5, icon: "mdi:alert-outline", color: "#ffa726" };
    }
    if (s === "active") {
      var r = this._num(this._ent.occupancy_timer);
      var tot = this._num(this._ent.occupancy_timeout) || 300;
      if (r > 0) return { rem: r, tot: tot, icon: "mdi:robot", color: "#03a9f4" };
      return { rem: tot, tot: tot, icon: "mdi:robot", color: "#03a9f4" };
    }
    return null;
  }

  _modeInfo() {
    var s = this._st(this._ent.state);
    var map = {
      "idle":          { key: "idle",          icon: "mdi:sleep",          color: "var(--disabled-text-color,#9e9e9e)" },
      "active":        { key: "active",        icon: "mdi:robot",          color: "var(--primary-color,#03a9f4)" },
      "warning":       { key: "warning",       icon: "mdi:alert-outline",  color: "#ffa726" },
      "temp_override": { key: "temp_override", icon: "mdi:hand-back-left", color: "#ffa726" },
      "perm_override": { key: "perm_override", icon: "mdi:cancel",         color: "#db4437" },
      "suspended":     { key: "suspended",     icon: "mdi:pause-circle",   color: "#ff9800" }
    };
    var m = map[s] || map["idle"];
    m.label = this._t(m.key);
    return m;
  }

  /* ── Build ──────────────────────────────────────────────── */

  _build() {
    var root = this.shadowRoot;
    root.innerHTML = "";

    var style = document.createElement("style");
    style.textContent = [
      ":host{display:block}",
      "ha-card{overflow:hidden}",
      ".w{position:relative;padding:16px;display:flex;flex-direction:column;align-items:center;min-height:180px}",
      ".tr{width:100%;display:none;align-items:center;gap:8px;margin-bottom:8px}",
      ".tr.v{display:flex}",
      ".bt{flex:1;height:6px;border-radius:3px;background:var(--divider-color,#e0e0e0);overflow:hidden}",
      ".bf{height:100%;border-radius:3px;transition:width 1s linear;width:0}",
      ".ti{--mdc-icon-size:18px;flex-shrink:0}",
      ".c{display:flex;align-items:center;justify-content:center;cursor:pointer;padding:16px 0 4px;-webkit-tap-highlight-color:transparent}",
      ".c ha-icon{--mdc-icon-size:64px;transition:color .3s,filter .3s,opacity .3s}",
      ".mi{display:flex;align-items:center;gap:6px;padding:4px 12px;border-radius:12px;margin:4px 0 12px;cursor:pointer;-webkit-tap-highlight-color:transparent}",
      ".mi ha-icon{--mdc-icon-size:16px}",
      ".mi span{font-size:13px;font-weight:500;letter-spacing:.3px}",
      ".an{font-size:14px;font-weight:500;color:var(--primary-text-color,#212121);text-transform:capitalize;margin:0 0 4px;letter-spacing:.3px}",
      ".b{width:100%;display:flex;align-items:center;justify-content:space-between}",
      ".s{display:flex;gap:14px;align-items:center}",
      ".s ha-icon{--mdc-icon-size:24px;transition:color .3s,opacity .3s;cursor:pointer;-webkit-tap-highlight-color:transparent}",
      ".g{--mdc-icon-size:24px;cursor:pointer;-webkit-tap-highlight-color:transparent}",
      ".ov{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.5);z-index:9999;align-items:center;justify-content:center}",
      ".ov.op{display:flex}",
      ".md{background:var(--ha-card-background,var(--card-background-color,#fff));border-radius:12px;padding:20px;min-width:300px;max-width:400px;max-height:80vh;overflow-y:auto;box-shadow:0 8px 32px rgba(0,0,0,.3);color:var(--primary-text-color,#212121)}",
      ".mh{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;font-size:18px;font-weight:500}",
      ".mh ha-icon{cursor:pointer;--mdc-icon-size:20px;color:var(--secondary-text-color,#727272)}",
      ".mr{display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid var(--divider-color,#e0e0e0)}",
      ".mr:last-of-type{border-bottom:none}",
      ".ml{font-size:14px;flex:1}",
      ".mv{display:flex;align-items:center;gap:6px}",
      ".mv input{width:72px;padding:4px 8px;border:1px solid var(--divider-color,#e0e0e0);border-radius:6px;background:transparent;color:var(--primary-text-color,#212121);font-size:14px;text-align:right;-webkit-appearance:none}",
      ".mv input:focus{outline:none;border-color:var(--primary-color,#03a9f4)}",
      ".mu{font-size:12px;color:var(--secondary-text-color,#727272);min-width:14px}",
      ".lb{display:flex;align-items:center;justify-content:center;gap:6px;padding:10px 16px;margin-top:14px;border:none;border-radius:8px;background:var(--primary-color,#03a9f4);color:#fff;font-size:14px;cursor:pointer;width:100%;-webkit-appearance:none}",
      ".lb ha-icon{--mdc-icon-size:18px}",
      ".ir{display:flex;align-items:center;justify-content:space-between;padding:6px 0;font-size:13px;color:var(--secondary-text-color,#727272)}",
      ".sep{border:none;border-top:1px solid var(--divider-color,#e0e0e0);margin:10px 0}"
    ].join("\n");
    root.appendChild(style);

    var card = document.createElement("ha-card");
    var w = document.createElement("div"); w.className = "w";

    /* timer row */
    var tr = document.createElement("div"); tr.className = "tr"; tr.id = "R";
    var bt = document.createElement("div"); bt.className = "bt";
    var bf = document.createElement("div"); bf.className = "bf"; bf.id = "F";
    bt.appendChild(bf); tr.appendChild(bt);
    var ti = document.createElement("ha-icon"); ti.className = "ti"; ti.id = "I";
    tr.appendChild(ti); w.appendChild(tr);

    /* center icon - tap=toggle */
    var c = document.createElement("div"); c.className = "c"; c.id = "T";
    var li = document.createElement("ha-icon"); li.id = "L";
    c.appendChild(li); w.appendChild(c);

    /* area name label */
    var an = document.createElement("div"); an.className = "an"; an.id = "AN";
    an.textContent = this._config.name || this._config.area;
    w.appendChild(an);

    /* mode indicator - click=more-info for state sensor */
    var mi = document.createElement("div"); mi.className = "mi"; mi.id = "MI";
    var mii = document.createElement("ha-icon"); mii.id = "MII";
    mi.appendChild(mii);
    var mil = document.createElement("span"); mil.id = "MIL";
    mi.appendChild(mil); w.appendChild(mi);

    /* bottom row */
    var b = document.createElement("div"); b.className = "b";
    var s = document.createElement("div"); s.className = "s";
    var mI = document.createElement("ha-icon"); mI.id = "M"; mI.setAttribute("icon", "mdi:motion-sensor"); s.appendChild(mI);
    var oI = document.createElement("ha-icon"); oI.id = "O"; oI.setAttribute("icon", "mdi:home-account"); s.appendChild(oI);
    var xI = document.createElement("ha-icon"); xI.id = "X"; xI.setAttribute("icon", "mdi:brightness-6"); s.appendChild(xI);
    b.appendChild(s);
    var gear = document.createElement("ha-icon"); gear.className = "g"; gear.id = "G"; gear.setAttribute("icon", "mdi:cog");
    b.appendChild(gear); w.appendChild(b);
    card.appendChild(w); root.appendChild(card);

    /* modal */
    var ov = document.createElement("div"); ov.className = "ov"; ov.id = "V";
    var md = document.createElement("div"); md.className = "md";
    var mh = document.createElement("div"); mh.className = "mh";
    var mhT = document.createElement("span"); mhT.id = "MHT";
    mh.appendChild(mhT);
    var mhC = document.createElement("ha-icon"); mhC.setAttribute("icon", "mdi:close"); mhC.id = "C";
    mh.appendChild(mhC); md.appendChild(mh);
    var mb = document.createElement("div"); mb.id = "B";
    md.appendChild(mb); ov.appendChild(md); root.appendChild(ov);

    /* ── Events ───────────────────────────────────────────── */
    var self = this;

    /* Center icon: tap = toggle */
    c.addEventListener("click", function() { self._toggle(); });

    /* Mode indicator: click = more-info for state sensor */
    mi.addEventListener("click", function() { self._moreInfo(self._ent.state); });

    /* Motion icon: click = more-info for first configured motion sensor */
    mI.addEventListener("click", function() {
      var sensors = self._lightAttr("motion_sensors");
      if (sensors && sensors.length > 0) {
        self._moreInfo(sensors[0]);
      } else {
        self._moreInfo(self._ent.light);
      }
    });

    /* Occupancy icon: click = more-info for configured occupancy sensor */
    oI.addEventListener("click", function() {
      var occ = self._lightAttr("occupancy_sensor");
      if (occ) {
        self._moreInfo(occ);
      } else {
        self._moreInfo(self._ent.light);
      }
    });

    /* Lux icon: click = more-info for configured lux sensor */
    xI.addEventListener("click", function() {
      var lux = self._lightAttr("lux_sensor");
      if (lux) {
        self._moreInfo(lux);
      } else {
        self._moreInfo(self._ent.lux);
      }
    });

    /* Timer bar: click = more-info for override timer sensor */
    tr.addEventListener("click", function() { self._moreInfo(self._ent.override_timer); });

    /* Gear = settings popup */
    gear.addEventListener("click", function() { self._openM(); });
    mhC.addEventListener("click", function() { self._closeM(); });
    ov.addEventListener("click", function(e) { if (e.target === ov) self._closeM(); });

    this._rendered = true;
  }

  /* ── Refresh ────────────────────────────────────────────── */

  _refresh() {
    if (!this._rendered || !this._hass) return;
    var r = this.shadowRoot;
    var isOn = this._st(this._ent.light) === "on";
    var profile = this._lightAttr("profile") || this._st(this._ent.profile);
    var machineState = this._lightAttr("smart_lighting_state") || this._st(this._ent.state);
    var isSuspended = machineState === "suspended";

    var L = r.getElementById("L");
    if (L) {
      L.setAttribute("icon", profile === "soft" ? this._iconSoft : this._iconMain);
      if (isSuspended) {
        L.style.color = "#ff9800"; L.style.filter = "none"; L.style.opacity = "0.5";
      } else if (isOn) {
        L.style.color = "var(--amber-color,#ffc107)";
        L.style.filter = "drop-shadow(0 0 10px var(--amber-color,#ffc107))";
        L.style.opacity = "1";
      } else {
        L.style.color = "var(--disabled-text-color,#bdbdbd)"; L.style.filter = "none"; L.style.opacity = "1";
      }
    }

    var mode = this._modeInfo();
    var MII = r.getElementById("MII");
    var MIL = r.getElementById("MIL");
    if (MII) { MII.setAttribute("icon", mode.icon); MII.style.color = mode.color; }
    if (MIL) { MIL.textContent = mode.label; MIL.style.color = mode.color; }

    this._refreshBar();

    /* Motion */
    var mIcon = r.getElementById("M");
    if (mIcon) {
      var motionRaw = this._lightAttr("motion_active");
      var motionOn = (motionRaw === true || motionRaw === "True" || motionRaw === "true");
      if (motionRaw === undefined || motionRaw === null) {
        motionOn = (machineState === "active" || machineState === "warning");
      }
      mIcon.style.color = motionOn ? "var(--primary-color,#03a9f4)" : "var(--disabled-text-color,#bdbdbd)";
      mIcon.style.opacity = motionOn ? "1" : "0.4";
    }

    /* Occupancy */
    var oIcon = r.getElementById("O");
    if (oIcon) {
      var occRaw = this._lightAttr("occupancy_active");
      var occOn = (occRaw === true || occRaw === "True" || occRaw === "true");
      oIcon.style.color = occOn ? "var(--primary-color,#03a9f4)" : "var(--disabled-text-color,#bdbdbd)";
      oIcon.style.opacity = occOn ? "1" : "0.4";
    }

    /* Lux */
    var xIcon = r.getElementById("X");
    if (xIcon) {
      var luxRaw = this._lightAttr("lux_sufficient");
      if (luxRaw === undefined || luxRaw === null) {
        xIcon.style.color = "var(--disabled-text-color,#bdbdbd)"; xIcon.style.opacity = "0.4";
      } else {
        var luxOk = (luxRaw === true || luxRaw === "True" || luxRaw === "true");
        xIcon.style.color = luxOk ? "#ffa726" : "var(--disabled-text-color,#bdbdbd)";
        xIcon.style.opacity = luxOk ? "1" : "0.35";
      }
    }

    var gear = r.getElementById("G");
    if (gear) gear.style.color = "var(--secondary-text-color,#727272)";
  }

  _refreshBar() {
    if (!this._rendered || !this._hass) return;
    var t = this._activeTimer();
    var R = this.shadowRoot.getElementById("R");
    var F = this.shadowRoot.getElementById("F");
    var I = this.shadowRoot.getElementById("I");
    if (!R || !F || !I) return;
    if (t) {
      R.classList.add("v");
      var pct = Math.min(100, (t.rem / t.tot) * 100);
      F.style.width = pct + "%"; F.style.background = t.color;
      I.setAttribute("icon", t.icon); I.style.color = t.color;
    } else {
      R.classList.remove("v");
    }
  }

  /* ── Actions ────────────────────────────────────────────── */

  _toggle() {
    if (this._hass) this._hass.callService("light", "toggle", { entity_id: this._ent.light });
  }

  _openM() {
    var ov = this.shadowRoot.getElementById("V");
    var body = this.shadowRoot.getElementById("B");
    var mhT = this.shadowRoot.getElementById("MHT");
    if (!ov || !body) return;
    if (mhT) mhT.textContent = this._t("settings");

    var settings = [
      { e: this._ent.occupancy_timeout,      k: "occupancy_timeout",    u: "s",  s: 10  },
      { e: this._ent.failsafe_timeout,       k: "failsafe_timeout",     u: "s",  s: 60  },
      { e: this._ent.perm_override_timeout,   k: "override_timeout",     u: "s",  s: 60  },
      { e: this._ent.temp_override_timeout,   k: "temp_override_timeout",u: "s",  s: 60  },
      { e: this._ent.warning_dim_pct,        k: "warning_dim_pct",      u: "%",  s: 5   },
      { e: this._ent.warning_dim_duration,    k: "warning_dim_duration", u: "s",  s: 1   },
      { e: this._ent.no_motion_timeout,       k: "no_motion_timeout",    u: "s",  s: 60  },
      { e: this._ent.lux_threshold,           k: "lux_threshold",        u: "lx", s: 1   },
      { e: this._ent.adaptive_window,         k: "adaptive_window",      u: "s",  s: 60  },
      { e: this._ent.adaptive_threshold_n,    k: "adaptive_threshold_n", u: "",   s: 1   },
      { e: this._ent.adaptive_multiplier,     k: "adaptive_multiplier",  u: "",   s: 0.1 },
      { e: this._ent.adaptive_max_factor,     k: "adaptive_max_factor",  u: "",   s: 0.5 },
      { e: this._ent.lux_hysteresis_pct,      k: "lux_hysteresis_pct",   u: "%",  s: 1   },
      { e: this._ent.lux_hysteresis_time,     k: "lux_hysteresis_time",  u: "s",  s: 1   }
    ];

    body.innerHTML = "";
    var self = this;

    /* info section */
    var infoItems = [
      { e: this._ent.state,            k: "state" },
      { e: this._ent.profile,          k: "profile" },
      { e: this._ent.adaptive_factor,  k: "adaptive_factor" },
      { e: this._ent.activation_count, k: "activations" }
    ];
    for (var j = 0; j < infoItems.length; j++) {
      var inf = infoItems[j];
      var val = this._st(inf.e);
      if (val === "unavailable") continue;
      var ir = document.createElement("div"); ir.className = "ir";
      var irL = document.createElement("span"); irL.textContent = this._t(inf.k); ir.appendChild(irL);
      var irV = document.createElement("span"); irV.textContent = val; irV.style.fontWeight = "600"; ir.appendChild(irV);
      body.appendChild(ir);
    }

    var sep = document.createElement("hr"); sep.className = "sep";
    body.appendChild(sep);

    /* editable numbers */
    for (var i = 0; i < settings.length; i++) {
      var c = settings[i];
      var so = this._hass.states[c.e];
      if (!so) continue;
      var v = parseFloat(so.state) || 0;
      var mn = so.attributes.min || 0;
      var mx = so.attributes.max || 99999;

      var row = document.createElement("div"); row.className = "mr";
      var label = document.createElement("span"); label.className = "ml";
      label.textContent = this._t(c.k); row.appendChild(label);
      var valDiv = document.createElement("div"); valDiv.className = "mv";
      var input = document.createElement("input");
      input.type = "number"; input.value = v; input.min = mn; input.max = mx; input.step = c.s;
      valDiv.appendChild(input);
      var unit = document.createElement("span"); unit.className = "mu"; unit.textContent = c.u;
      valDiv.appendChild(unit); row.appendChild(valDiv);
      body.appendChild(row);

      (function(entity) {
        input.addEventListener("change", function(ev) {
          var nv = parseFloat(ev.target.value);
          if (!isNaN(nv)) self._hass.callService("number", "set_value", { entity_id: entity, value: nv });
        });
      })(c.e);
    }

    /* set lux button */
    var btn = document.createElement("button"); btn.className = "lb";
    var btnI = document.createElement("ha-icon"); btnI.setAttribute("icon", "mdi:brightness-auto");
    btn.appendChild(btnI);
    btn.appendChild(document.createTextNode(" " + this._t("set_lux")));
    btn.addEventListener("click", function() {
      self._hass.callService("button", "press", { entity_id: self._ent.set_lux_threshold });
    });
    body.appendChild(btn);
    ov.classList.add("op");
  }

  _closeM() {
    var ov = this.shadowRoot.getElementById("V");
    if (ov) ov.classList.remove("op");
  }
}

customElements.define("smart-lighting-card", SmartLightingCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "smart-lighting-card",
  name: "Smart Lighting Card",
  description: "Smart lighting control with more-info popups, timer bar, and full settings",
  preview: true
});
console.info(
  "%c SMART-LIGHTING-CARD %c v9 ",
  "color:#fff;background:#03a9f4;font-weight:700;padding:2px 6px;border-radius:3px 0 0 3px",
  "color:#03a9f4;background:#e3f2fd;padding:2px 6px;border-radius:0 3px 3px 0"
);
