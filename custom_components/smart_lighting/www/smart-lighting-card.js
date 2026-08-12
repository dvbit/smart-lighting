/**
 * Smart Lighting Card v11 - Custom Lovelace Card
 *
 * Layout:
 *   TOP-RIGHT badge: profile (🌙/☀️) · actuator set · suspend flag
 *   TOP:     dual timer bars (active + failsafe)
 *   CENTER:  large light icon (tap = toggle)
 *   MIDDLE:  mode label (localised) + raw state below it
 *   BOTTOM:  motion · occupancy · lux icons (click = more-info)
 *   GEAR:    settings popup with all parameters
 *
 * YAML:
 *   type: custom:smart-lighting-card
 *   area: cucina
 *   name: Cucina           # optional display name
 *   icon_main: mdi:ceiling-light
 *   icon_soft: mdi:lamp
 */

var SL_I18N = {
  en: {
    idle:"Idle", active:"Automatic", warning:"Warning",
    temp_override:"Manual", perm_override:"Override", suspended:"Suspended",
    settings:"Settings", state:"State", profile:"Profile",
    adaptive_factor:"Adaptive Factor", activations:"Activations",
    occupancy_timeout:"Occupancy Timeout", failsafe_timeout:"Failsafe Timeout",
    override_timeout:"Override Timeout", temp_override_timeout:"Temp Override Timeout",
    warning_count:"Warning Count", warning_interval:"Warning Interval",
    lux_threshold:"Lux Threshold", set_lux:"Set Lux from Sensor",
    adaptive_window:"Adaptive Window", adaptive_threshold_n:"Adaptive Threshold",
    adaptive_multiplier:"Adaptive Multiplier", adaptive_max_factor:"Max Adaptive Factor",
    lux_hysteresis_pct:"Lux Hysteresis %", lux_hysteresis_time:"Lux Hysteresis Time",
    warning_dim_pct:"Warning Dim %", warning_dim_duration:"Warning Dim Duration",
    temp_override_timeout:"Temp Override Timeout"
  },
  it: {
    idle:"Inattivo", active:"Automatico", warning:"Avviso",
    temp_override:"Manuale", perm_override:"Override", suspended:"Sospeso",
    settings:"Impostazioni", state:"Stato", profile:"Profilo",
    adaptive_factor:"Fattore Adattivo", activations:"Attivazioni",
    occupancy_timeout:"Timeout Presenza", failsafe_timeout:"Timeout Sicurezza",
    override_timeout:"Timeout Override", temp_override_timeout:"Timeout Override Temp.",
    warning_count:"Conteggio Lampeggi", warning_interval:"Intervallo Lampeggi",
    lux_threshold:"Soglia Lux", set_lux:"Imposta Lux da Sensore",
    adaptive_window:"Finestra Adattiva", adaptive_threshold_n:"Soglia Adattiva",
    adaptive_multiplier:"Moltiplicatore Adattivo", adaptive_max_factor:"Fattore Max Adattivo",
    lux_hysteresis_pct:"Isteresi Lux %", lux_hysteresis_time:"Tempo Isteresi Lux",
    warning_dim_pct:"Attenuazione Avviso %", warning_dim_duration:"Durata Attenuazione",
    temp_override_timeout:"Timeout Override Temp."
  },
  fr: {
    idle:"Inactif", active:"Automatique", warning:"Avertissement",
    temp_override:"Manuel", perm_override:"Forçage", suspended:"Suspendu",
    settings:"Paramètres", state:"État", profile:"Profil",
    adaptive_factor:"Facteur Adaptatif", activations:"Activations",
    occupancy_timeout:"Délai Présence", failsafe_timeout:"Délai Sécurité",
    override_timeout:"Délai Forçage", temp_override_timeout:"Délai Override Temp.",
    warning_count:"Nombre Clignotements", warning_interval:"Intervalle Clignotements",
    lux_threshold:"Seuil Lux", set_lux:"Définir Lux depuis Capteur",
    adaptive_window:"Fenêtre Adaptative", adaptive_threshold_n:"Seuil Adaptatif",
    adaptive_multiplier:"Multiplicateur Adaptatif", adaptive_max_factor:"Facteur Max Adaptatif",
    lux_hysteresis_pct:"Hystérésis Lux %", lux_hysteresis_time:"Temps Hystérésis Lux",
    warning_dim_pct:"Atténuation %", warning_dim_duration:"Durée Atténuation",
    temp_override_timeout:"Délai Override Temp."
  },
  es: {
    idle:"Inactivo", active:"Automático", warning:"Advertencia",
    temp_override:"Manual", perm_override:"Anulación", suspended:"Suspendido",
    settings:"Ajustes", state:"Estado", profile:"Perfil",
    adaptive_factor:"Factor Adaptativo", activations:"Activaciones",
    occupancy_timeout:"Timeout Ocupación", failsafe_timeout:"Timeout Seguridad",
    override_timeout:"Timeout Anulación", temp_override_timeout:"Timeout Override Temp.",
    warning_count:"Cantidad Parpadeos", warning_interval:"Intervalo Parpadeos",
    lux_threshold:"Umbral Lux", set_lux:"Fijar Lux desde Sensor",
    adaptive_window:"Ventana Adaptativa", adaptive_threshold_n:"Umbral Adaptativo",
    adaptive_multiplier:"Multiplicador Adaptativo", adaptive_max_factor:"Factor Max Adaptativo",
    lux_hysteresis_pct:"Histéresis Lux %", lux_hysteresis_time:"Tiempo Histéresis Lux",
    warning_dim_pct:"Atenuación %", warning_dim_duration:"Duración Atenuación",
    temp_override_timeout:"Timeout Override Temp."
  },
  de: {
    idle:"Inaktiv", active:"Automatisch", warning:"Warnung",
    temp_override:"Manuell", perm_override:"Überschreibung", suspended:"Pausiert",
    settings:"Einstellungen", state:"Status", profile:"Profil",
    adaptive_factor:"Adaptiver Faktor", activations:"Aktivierungen",
    occupancy_timeout:"Anwesenheits-Timeout", failsafe_timeout:"Sicherheits-Timeout",
    override_timeout:"Überschreibungs-Timeout", temp_override_timeout:"Temp. Override-Timeout",
    warning_count:"Blinkanzahl", warning_interval:"Blinkintervall",
    lux_threshold:"Lux-Schwelle", set_lux:"Lux vom Sensor übernehmen",
    adaptive_window:"Adaptives Fenster", adaptive_threshold_n:"Adaptiver Schwellenwert",
    adaptive_multiplier:"Adaptiver Multiplikator", adaptive_max_factor:"Adaptiver Max-Faktor",
    lux_hysteresis_pct:"Lux-Hysterese %", lux_hysteresis_time:"Lux-Hysterese Zeit",
    warning_dim_pct:"Dimmung %", warning_dim_duration:"Dimmung Dauer",
    temp_override_timeout:"Temp. Override-Timeout"
  }
};

class SmartLightingCard extends HTMLElement {

  constructor() {
    super();
    this.attachShadow({ mode:"open" });
    this._hass = null; this._config = null;
    this._rendered = false; this._timer = null; this._lang = "en";
  }

  _t(k) { var d=SL_I18N[this._lang]||SL_I18N.en; return d[k]||(SL_I18N.en[k]||k); }

  setConfig(config) {
    if (!config.area) throw new Error("'area' is required");
    this._config = config; this._rendered = false;
    this._iconMain = config.icon_main || "mdi:ceiling-light";
    this._iconSoft  = config.icon_soft  || "mdi:lamp";
    var a = config.area;
    this._ent = {
      light:                "light.smart_lighting_"+a,
      state:                "sensor.smart_lighting_"+a+"_state",
      profile:              "sensor.smart_lighting_"+a+"_profile",
      occupancy_timer:      "sensor.smart_lighting_"+a+"_occupancy_timer",
      failsafe_timer:       "sensor.smart_lighting_"+a+"_failsafe_timer",
      override_timer:       "sensor.smart_lighting_"+a+"_override_timer",
      warning_timer:        "sensor.smart_lighting_"+a+"_warning_timer",
      adaptive_factor:      "sensor.smart_lighting_"+a+"_adaptive_factor",
      activation_count:     "sensor.smart_lighting_"+a+"_activation_count",
      lux:                  "sensor.smart_lighting_"+a+"_lux",
      occupancy_timeout:    "number.smart_lighting_"+a+"_occupancy_timeout",
      failsafe_timeout:     "number.smart_lighting_"+a+"_failsafe_timeout",
      perm_override_timeout:"number.smart_lighting_"+a+"_perm_override_timeout",
      temp_override_timeout:"number.smart_lighting_"+a+"_temp_override_timeout",
      warning_dim_pct:      "number.smart_lighting_"+a+"_warning_dim_pct",
      warning_dim_duration: "number.smart_lighting_"+a+"_warning_dim_duration",
      lux_threshold:        "number.smart_lighting_"+a+"_lux_threshold",
      adaptive_window:      "number.smart_lighting_"+a+"_adaptive_window",
      adaptive_threshold_n: "number.smart_lighting_"+a+"_adaptive_threshold",
      adaptive_multiplier:  "number.smart_lighting_"+a+"_adaptive_multiplier",
      adaptive_max_factor:  "number.smart_lighting_"+a+"_adaptive_max_factor",
      lux_hysteresis_pct:   "number.smart_lighting_"+a+"_lux_hysteresis_pct",
      lux_hysteresis_time:  "number.smart_lighting_"+a+"_lux_hysteresis_time",
      set_lux_threshold:    "button.smart_lighting_"+a+"_set_lux_threshold"
    };
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._config) return;
    var nl = (hass.language||"en").split("-")[0].toLowerCase();
    if (nl !== this._lang) { this._lang = nl; this._rendered = false; }
    if (!this._rendered) this._build();
    this._refresh();
  }

  getCardSize() { return 5; }
  connectedCallback() { var s=this; this._timer=setInterval(function(){if(s._hass&&s._rendered)s._refreshBars();},1000); }
  disconnectedCallback() { if(this._timer){clearInterval(this._timer);this._timer=null;} }

  /* ── Helpers ──────────────────────────────────────────────── */
  _st(id) { var h=this._hass; if(!h||!h.states||!h.states[id])return"unavailable"; return h.states[id].state; }
  _num(id){ var v=parseFloat(this._st(id)); return isNaN(v)?0:v; }
  _attr(key){ var s=this._hass&&this._hass.states&&this._hass.states[this._ent.light]; if(!s||!s.attributes)return undefined; return s.attributes[key]; }
  _bool(key){ var v=this._attr(key); return v===true||v==="True"||v==="true"; }
  _moreInfo(id){ var e=new Event("hass-more-info",{bubbles:true,composed:true}); e.detail={entityId:id}; this.shadowRoot.dispatchEvent(e); }

  _activeTimer() {
    var s = this._st(this._ent.state);
    if (s==="perm_override") return {rem:this._num(this._ent.override_timer),tot:this._num(this._ent.perm_override_timeout)||3600,icon:"mdi:cancel",color:"#f85149"};
    if (s==="temp_override") {
      var rem=this._num(this._ent.override_timer), tot=this._num(this._ent.temp_override_timeout);
      return tot>0&&rem>0?{rem:rem,tot:tot,icon:"mdi:hand-back-left",color:"#ffa726"}:{rem:1,tot:1,icon:"mdi:hand-back-left",color:"#ffa726"};
    }
    if (s==="warning") { var r=this._num(this._ent.warning_timer); return {rem:r,tot:r||5,icon:"mdi:alert-outline",color:"#ffa726"}; }
    if (s==="active") {
      var r=this._num(this._ent.occupancy_timer), tot=this._num(this._ent.occupancy_timeout)||300;
      return r>0?{rem:r,tot:tot,icon:"mdi:robot",color:"#03a9f4"}:{rem:tot,tot:tot,icon:"mdi:robot",color:"#03a9f4"};
    }
    return null;
  }

  _modeInfo() {
    var s=this._st(this._ent.state);
    var map={
      idle:         {key:"idle",         icon:"mdi:sleep",          color:"var(--disabled-text-color,#9e9e9e)"},
      active:       {key:"active",       icon:"mdi:robot",          color:"var(--primary-color,#03a9f4)"},
      warning:      {key:"warning",      icon:"mdi:alert-outline",  color:"#ffa726"},
      temp_override:{key:"temp_override",icon:"mdi:hand-back-left", color:"#ffa726"},
      perm_override:{key:"perm_override",icon:"mdi:cancel",         color:"#f85149"},
      suspended:    {key:"suspended",    icon:"mdi:pause-circle",   color:"#ff9800"}
    };
    var m=map[s]||map.idle; m.label=this._t(m.key); m.rawState=s||"idle"; return m;
  }

  /* ── Build ────────────────────────────────────────────────── */
  _build() {
    var root=this.shadowRoot; root.innerHTML="";
    var style=document.createElement("style");
    style.textContent=[
      ":host{display:block}",
      "ha-card{overflow:hidden;position:relative}",
      ".w{padding:12px 16px 16px;display:flex;flex-direction:column;align-items:center;min-height:200px}",

      /* top-right badge */
      ".badge{position:absolute;top:10px;right:10px;display:flex;gap:5px;align-items:center}",
      ".bpill{display:flex;align-items:center;gap:3px;padding:3px 7px;border-radius:10px;font-size:10px;font-weight:600;line-height:1}",
      ".bpill ha-icon{--mdc-icon-size:13px}",

      /* dual timer bars */
      ".bars{width:100%;display:flex;flex-direction:column;gap:3px;margin-bottom:8px}",
      ".trow{width:100%;display:none;align-items:center;gap:6px}",
      ".trow.v{display:flex}",
      ".ti{--mdc-icon-size:15px;flex-shrink:0}",
      ".bt{flex:1;height:5px;border-radius:3px;background:var(--divider-color,#e0e0e0);overflow:hidden}",
      ".bf{height:100%;border-radius:3px;transition:width 1s linear;width:0}",
      ".tl{font-size:10px;color:var(--secondary-text-color,#727272);min-width:30px;text-align:right;font-variant-numeric:tabular-nums}",

      /* center icon */
      ".c{display:flex;align-items:center;justify-content:center;cursor:pointer;padding:12px 0 4px;-webkit-tap-highlight-color:transparent}",
      ".c ha-icon{--mdc-icon-size:64px;transition:color .3s,filter .3s,opacity .3s}",

      /* area name */
      ".an{font-size:14px;font-weight:500;color:var(--primary-text-color,#212121);text-transform:capitalize;margin:0 0 2px;letter-spacing:.3px}",

      /* mode indicator */
      ".mi{display:flex;align-items:center;gap:5px;padding:3px 10px;border-radius:10px;cursor:pointer;-webkit-tap-highlight-color:transparent}",
      ".mi ha-icon{--mdc-icon-size:14px}",
      ".mi .mlabel{font-size:12px;font-weight:600;letter-spacing:.3px}",
      ".mi .mraw{font-size:10px;opacity:.7;margin-left:4px}",

      /* bottom */
      ".b{width:100%;display:flex;align-items:center;justify-content:space-between;margin-top:10px}",
      ".s{display:flex;gap:12px;align-items:center}",
      ".s ha-icon{--mdc-icon-size:24px;transition:color .3s,opacity .3s;cursor:pointer;-webkit-tap-highlight-color:transparent}",
      ".g{--mdc-icon-size:24px;cursor:pointer;-webkit-tap-highlight-color:transparent}",

      /* modal */
      ".ov{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.5);z-index:9999;align-items:center;justify-content:center}",
      ".ov.op{display:flex}",
      ".md{background:var(--ha-card-background,var(--card-background-color,#fff));border-radius:12px;padding:20px;min-width:300px;max-width:400px;max-height:80vh;overflow-y:auto;box-shadow:0 8px 32px rgba(0,0,0,.3);color:var(--primary-text-color,#212121)}",
      ".mh{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;font-size:18px;font-weight:500}",
      ".mh ha-icon{cursor:pointer;--mdc-icon-size:20px;color:var(--secondary-text-color,#727272)}",
      ".mr{display:flex;align-items:center;justify-content:space-between;padding:9px 0;border-bottom:1px solid var(--divider-color,#e0e0e0)}",
      ".mr:last-of-type{border-bottom:none}",
      ".ml{font-size:13px;flex:1}",
      ".mv{display:flex;align-items:center;gap:5px}",
      ".mv input{width:68px;padding:3px 6px;border:1px solid var(--divider-color,#e0e0e0);border-radius:5px;background:transparent;color:var(--primary-text-color,#212121);font-size:13px;text-align:right;-webkit-appearance:none}",
      ".mv input:focus{outline:none;border-color:var(--primary-color,#03a9f4)}",
      ".mu{font-size:11px;color:var(--secondary-text-color,#727272);min-width:12px}",
      ".lb{display:flex;align-items:center;justify-content:center;gap:6px;padding:9px 14px;margin-top:12px;border:none;border-radius:8px;background:var(--primary-color,#03a9f4);color:#fff;font-size:13px;cursor:pointer;width:100%;-webkit-appearance:none}",
      ".lb ha-icon{--mdc-icon-size:17px}",
      ".ir{display:flex;align-items:center;justify-content:space-between;padding:5px 0;font-size:12px;color:var(--secondary-text-color,#727272)}",
      ".sep{border:none;border-top:1px solid var(--divider-color,#e0e0e0);margin:8px 0}"
    ].join("\n");
    root.appendChild(style);

    var card=document.createElement("ha-card");
    var w=document.createElement("div"); w.className="w";

    /* ── Top-right badge ─────────────────────────────────── */
    var badge=document.createElement("div"); badge.className="badge"; badge.id="BDG";
    /* profile pill */
    var ppill=document.createElement("div"); ppill.className="bpill"; ppill.id="PP";
    var picon=document.createElement("ha-icon"); picon.id="PICO"; ppill.appendChild(picon);
    var ptxt=document.createElement("span"); ptxt.id="PTXT"; ppill.appendChild(ptxt);
    badge.appendChild(ppill);
    /* actuator pill */
    var apill=document.createElement("div"); apill.className="bpill"; apill.id="AP";
    var aicon=document.createElement("ha-icon"); aicon.id="AICO"; apill.appendChild(aicon);
    badge.appendChild(apill);
    /* suspend pill */
    var spill=document.createElement("div"); spill.className="bpill"; spill.id="SP";
    var sicon=document.createElement("ha-icon"); sicon.id="SICO"; spill.appendChild(sicon);
    var stxt=document.createElement("span"); stxt.id="STXT"; spill.appendChild(stxt);
    badge.appendChild(spill);
    card.appendChild(badge);

    /* ── Timer bars ──────────────────────────────────────── */
    var bars=document.createElement("div"); bars.className="bars";

    var trA=document.createElement("div"); trA.className="trow"; trA.id="RA";
    var tiA=document.createElement("ha-icon"); tiA.className="ti"; tiA.id="IA";
    trA.appendChild(tiA);
    var btA=document.createElement("div"); btA.className="bt";
    var bfA=document.createElement("div"); bfA.className="bf"; bfA.id="FA";
    btA.appendChild(bfA); trA.appendChild(btA);
    var tlA=document.createElement("span"); tlA.className="tl"; tlA.id="TLA"; trA.appendChild(tlA);
    bars.appendChild(trA);

    var trF=document.createElement("div"); trF.className="trow"; trF.id="RF";
    var tiF=document.createElement("ha-icon"); tiF.className="ti"; tiF.id="IF";
    tiF.setAttribute("icon","mdi:shield-alert-outline"); trF.appendChild(tiF);
    var btF=document.createElement("div"); btF.className="bt";
    var bfF=document.createElement("div"); bfF.className="bf"; bfF.id="FF";
    btF.appendChild(bfF); trF.appendChild(btF);
    var tlF=document.createElement("span"); tlF.className="tl"; tlF.id="TLF"; trF.appendChild(tlF);
    bars.appendChild(trF);
    w.appendChild(bars);

    /* ── Center icon ─────────────────────────────────────── */
    var c=document.createElement("div"); c.className="c"; c.id="T";
    var li=document.createElement("ha-icon"); li.id="L"; c.appendChild(li); w.appendChild(c);

    /* ── Area name ───────────────────────────────────────── */
    var an=document.createElement("div"); an.className="an"; an.id="AN";
    an.textContent=this._config.name||this._config.area; w.appendChild(an);

    /* ── Mode indicator ──────────────────────────────────── */
    var mi=document.createElement("div"); mi.className="mi"; mi.id="MI";
    var mii=document.createElement("ha-icon"); mii.id="MII"; mi.appendChild(mii);
    var mlabel=document.createElement("span"); mlabel.className="mlabel"; mlabel.id="MIL"; mi.appendChild(mlabel);
    var mraw=document.createElement("span"); mraw.className="mraw"; mraw.id="MIR"; mi.appendChild(mraw);
    w.appendChild(mi);

    /* ── Bottom row ──────────────────────────────────────── */
    var b=document.createElement("div"); b.className="b";
    var s=document.createElement("div"); s.className="s";
    var mI=document.createElement("ha-icon"); mI.id="M"; mI.setAttribute("icon","mdi:motion-sensor"); s.appendChild(mI);
    var oI=document.createElement("ha-icon"); oI.id="O"; oI.setAttribute("icon","mdi:home-account"); s.appendChild(oI);
    var xI=document.createElement("ha-icon"); xI.id="X"; xI.setAttribute("icon","mdi:brightness-6"); s.appendChild(xI);
    b.appendChild(s);
    var gear=document.createElement("ha-icon"); gear.className="g"; gear.id="G"; gear.setAttribute("icon","mdi:cog");
    b.appendChild(gear); w.appendChild(b);
    card.appendChild(w); root.appendChild(card);

    /* ── Modal ───────────────────────────────────────────── */
    var ov=document.createElement("div"); ov.className="ov"; ov.id="V";
    var md=document.createElement("div"); md.className="md";
    var mh=document.createElement("div"); mh.className="mh";
    var mhT=document.createElement("span"); mhT.id="MHT"; mh.appendChild(mhT);
    var mhC=document.createElement("ha-icon"); mhC.setAttribute("icon","mdi:close"); mhC.id="C";
    mh.appendChild(mhC); md.appendChild(mh);
    var mb=document.createElement("div"); mb.id="B";
    md.appendChild(mb); ov.appendChild(md); root.appendChild(ov);

    /* ── Events ──────────────────────────────────────────── */
    var self=this;
    c.addEventListener("click",function(){self._toggle();});
    mi.addEventListener("click",function(){self._moreInfo(self._ent.state);});
    mI.addEventListener("click",function(){
      var ss=self._attr("motion_sensors"); if(ss&&ss.length)self._moreInfo(ss[0]); else self._moreInfo(self._ent.light);
    });
    oI.addEventListener("click",function(){
      var oo=self._attr("occupancy_sensor"); if(oo)self._moreInfo(oo); else self._moreInfo(self._ent.light);
    });
    xI.addEventListener("click",function(){
      var xx=self._attr("lux_sensor"); if(xx)self._moreInfo(xx); else self._moreInfo(self._ent.lux);
    });
    bars.addEventListener("click",function(){self._moreInfo(self._ent.override_timer);});
    gear.addEventListener("click",function(){self._openM();});
    mhC.addEventListener("click",function(){self._closeM();});
    ov.addEventListener("click",function(e){if(e.target===ov)self._closeM();});

    this._rendered=true;
  }

  /* ── Refresh ──────────────────────────────────────────────── */
  _refresh() {
    if (!this._rendered||!this._hass) return;
    var r=this.shadowRoot;
    var isOn=this._st(this._ent.light)==="on";
    var profile=this._attr("profile")||this._st(this._ent.profile);
    var machineState=this._attr("smart_lighting_state")||this._st(this._ent.state);
    var isSuspended=machineState==="suspended";
    var softActors=this._bool("soft_actuators_active");
    var suspendActive=this._bool("suspend_active");

    /* ── Center icon ─────────────────────────────────────── */
    var L=r.getElementById("L");
    if (L) {
      L.setAttribute("icon",profile==="soft"?this._iconSoft:this._iconMain);
      if (isSuspended)      { L.style.color="#ff9800"; L.style.filter="none"; L.style.opacity="0.5"; }
      else if (isOn)        { L.style.color="var(--amber-color,#ffc107)"; L.style.filter="drop-shadow(0 0 10px var(--amber-color,#ffc107))"; L.style.opacity="1"; }
      else                  { L.style.color="var(--disabled-text-color,#bdbdbd)"; L.style.filter="none"; L.style.opacity="1"; }
    }

    /* ── Mode indicator (label + raw state) ──────────────── */
    var mode=this._modeInfo();
    var MII=r.getElementById("MII"), MIL=r.getElementById("MIL"), MIR=r.getElementById("MIR");
    if (MII) { MII.setAttribute("icon",mode.icon); MII.style.color=mode.color; }
    if (MIL) { MIL.textContent=mode.label; MIL.style.color=mode.color; }
    if (MIR) { MIR.textContent="("+mode.rawState+")"; MIR.style.color=mode.color; }

    /* ── Top-right badge ─────────────────────────────────── */
    /* Profile pill */
    var PP=r.getElementById("PP"), PICO=r.getElementById("PICO"), PTXT=r.getElementById("PTXT");
    if (PP&&PICO&&PTXT) {
      var isSoft=profile==="soft";
      PP.style.background=isSoft?"rgba(99,50,180,0.15)":"rgba(251,188,5,0.15)";
      PP.style.color=isSoft?"#ab47bc":"#f9a825";
      PICO.setAttribute("icon",isSoft?"mdi:weather-night":"mdi:weather-sunny");
      PICO.style.color=isSoft?"#ab47bc":"#f9a825";
      PTXT.textContent=isSoft?"soft":"normal";
    }

    /* Actuator pill */
    var AP=r.getElementById("AP"), AICO=r.getElementById("AICO");
    if (AP&&AICO) {
      if (softActors) {
        AP.style.display="flex";
        AP.style.background="rgba(99,50,180,0.15)"; AP.style.color="#ab47bc";
        AICO.setAttribute("icon","mdi:lightbulb-group"); AICO.style.color="#ab47bc";
      } else {
        AP.style.display="flex";
        AP.style.background="rgba(3,169,244,0.12)"; AP.style.color="#03a9f4";
        AICO.setAttribute("icon","mdi:lightbulb"); AICO.style.color="#03a9f4";
      }
    }

    /* Suspend pill */
    var SP=r.getElementById("SP"), SICO=r.getElementById("SICO"), STXT=r.getElementById("STXT");
    if (SP&&SICO) {
      if (isSuspended||suspendActive) {
        SP.style.display="flex";
        SP.style.background="rgba(255,152,0,0.15)"; SP.style.color="#ff9800";
        SICO.setAttribute("icon","mdi:pause-circle"); SICO.style.color="#ff9800";
        if (STXT) STXT.textContent="suspended";
      } else {
        SP.style.display="none";
      }
    }

    /* ── Timer bars ──────────────────────────────────────── */
    this._refreshBars();

    /* ── Motion ──────────────────────────────────────────── */
    var mIcon=r.getElementById("M");
    if (mIcon) {
      var motionRaw=this._attr("motion_active");
      var motionOn=(motionRaw===true||motionRaw==="True"||motionRaw==="true");
      if (motionRaw===undefined||motionRaw===null) motionOn=(machineState==="active"||machineState==="warning");
      mIcon.style.color=motionOn?"var(--primary-color,#03a9f4)":"var(--disabled-text-color,#bdbdbd)";
      mIcon.style.opacity=motionOn?"1":"0.4";
    }

    /* ── Occupancy ───────────────────────────────────────── */
    var oIcon=r.getElementById("O");
    if (oIcon) {
      var occRaw=this._attr("occupancy_active");
      var occOn=(occRaw===true||occRaw==="True"||occRaw==="true");
      oIcon.style.color=occOn?"var(--primary-color,#03a9f4)":"var(--disabled-text-color,#bdbdbd)";
      oIcon.style.opacity=occOn?"1":"0.4";
    }

    /* ── Lux ─────────────────────────────────────────────── */
    var xIcon=r.getElementById("X");
    if (xIcon) {
      var luxRaw=this._attr("lux_sufficient");
      if (luxRaw===undefined||luxRaw===null) { xIcon.style.color="var(--disabled-text-color,#bdbdbd)"; xIcon.style.opacity="0.4"; }
      else { var luxOk=(luxRaw===true||luxRaw==="True"||luxRaw==="true"); xIcon.style.color=luxOk?"#ffa726":"var(--disabled-text-color,#bdbdbd)"; xIcon.style.opacity=luxOk?"1":"0.35"; }
    }

    /* ── Gear ────────────────────────────────────────────── */
    var gear=r.getElementById("G");
    if (gear) gear.style.color="var(--secondary-text-color,#727272)";
  }

  _refreshBars() {
    if (!this._rendered||!this._hass) return;
    var isOn=this._st(this._ent.light)==="on";

    /* Active timer */
    var t=this._activeTimer();
    var RA=this.shadowRoot.getElementById("RA"), FA=this.shadowRoot.getElementById("FA"),
        IA=this.shadowRoot.getElementById("IA"), TLA=this.shadowRoot.getElementById("TLA");
    if (RA&&FA&&IA) {
      if (t) {
        RA.classList.add("v");
        var pct=Math.min(100,(t.rem/t.tot)*100);
        FA.style.width=pct+"%"; FA.style.background=t.color;
        IA.setAttribute("icon",t.icon); IA.style.color=t.color;
        if (TLA) TLA.textContent=Math.round(t.rem)+"s";
      } else { RA.classList.remove("v"); }
    }

    /* Failsafe timer */
    var RF=this.shadowRoot.getElementById("RF"), FF=this.shadowRoot.getElementById("FF"),
        IF=this.shadowRoot.getElementById("IF"), TLF=this.shadowRoot.getElementById("TLF");
    if (RF&&FF) {
      var fsRem=this._num(this._ent.failsafe_timer), fsTot=this._num(this._ent.failsafe_timeout)||3600;
      if (isOn&&fsRem>0) {
        RF.classList.add("v");
        FF.style.width=Math.min(100,(fsRem/fsTot)*100)+"%"; FF.style.background="#ef5350";
        if (IF) IF.style.color="#ef5350";
        if (TLF) TLF.textContent=Math.round(fsRem)+"s";
      } else { RF.classList.remove("v"); }
    }
  }

  /* ── Actions ──────────────────────────────────────────────── */
  _toggle() { if(this._hass) this._hass.callService("light","toggle",{entity_id:this._ent.light}); }

  _openM() {
    var ov=this.shadowRoot.getElementById("V"), body=this.shadowRoot.getElementById("B"), mhT=this.shadowRoot.getElementById("MHT");
    if (!ov||!body) return;
    if (mhT) mhT.textContent=this._t("settings");

    var settings=[
      {e:this._ent.occupancy_timeout,     k:"occupancy_timeout",    u:"s",  s:10},
      {e:this._ent.failsafe_timeout,      k:"failsafe_timeout",     u:"s",  s:60},
      {e:this._ent.perm_override_timeout,  k:"override_timeout",     u:"s",  s:60},
      {e:this._ent.temp_override_timeout,  k:"temp_override_timeout",u:"s",  s:60},
      {e:this._ent.warning_dim_pct,       k:"warning_dim_pct",      u:"%",  s:5},
      {e:this._ent.warning_dim_duration,  k:"warning_dim_duration",  u:"s",  s:1},
      {e:this._ent.lux_threshold,         k:"lux_threshold",        u:"lx", s:1},
      {e:this._ent.adaptive_window,       k:"adaptive_window",      u:"s",  s:60},
      {e:this._ent.adaptive_threshold_n,  k:"adaptive_threshold_n", u:"",   s:1},
      {e:this._ent.adaptive_multiplier,   k:"adaptive_multiplier",  u:"",   s:0.1},
      {e:this._ent.adaptive_max_factor,   k:"adaptive_max_factor",  u:"",   s:0.5},
      {e:this._ent.lux_hysteresis_pct,    k:"lux_hysteresis_pct",   u:"%",  s:1},
      {e:this._ent.lux_hysteresis_time,   k:"lux_hysteresis_time",  u:"s",  s:1}
    ];

    body.innerHTML=""; var self=this;

    /* info */
    var info=[{e:this._ent.state,k:"state"},{e:this._ent.profile,k:"profile"},{e:this._ent.adaptive_factor,k:"adaptive_factor"},{e:this._ent.activation_count,k:"activations"}];
    for (var j=0;j<info.length;j++) {
      var val=this._st(info[j].e); if(val==="unavailable")continue;
      var ir=document.createElement("div"); ir.className="ir";
      var irL=document.createElement("span"); irL.textContent=this._t(info[j].k); ir.appendChild(irL);
      var irV=document.createElement("span"); irV.textContent=val; irV.style.fontWeight="600"; ir.appendChild(irV);
      body.appendChild(ir);
    }
    var sep=document.createElement("hr"); sep.className="sep"; body.appendChild(sep);

    /* numbers */
    for (var i=0;i<settings.length;i++) {
      var c=settings[i], so=this._hass.states[c.e]; if(!so)continue;
      var v=parseFloat(so.state)||0, mn=so.attributes.min||0, mx=so.attributes.max||99999;
      var row=document.createElement("div"); row.className="mr";
      var lbl=document.createElement("span"); lbl.className="ml"; lbl.textContent=this._t(c.k); row.appendChild(lbl);
      var vd=document.createElement("div"); vd.className="mv";
      var inp=document.createElement("input"); inp.type="number"; inp.value=v; inp.min=mn; inp.max=mx; inp.step=c.s;
      vd.appendChild(inp);
      var un=document.createElement("span"); un.className="mu"; un.textContent=c.u; vd.appendChild(un);
      row.appendChild(vd); body.appendChild(row);
      (function(entity){inp.addEventListener("change",function(ev){var nv=parseFloat(ev.target.value);if(!isNaN(nv))self._hass.callService("number","set_value",{entity_id:entity,value:nv});});})(c.e);
    }

    /* button */
    var btn=document.createElement("button"); btn.className="lb";
    var btnI=document.createElement("ha-icon"); btnI.setAttribute("icon","mdi:brightness-auto"); btn.appendChild(btnI);
    btn.appendChild(document.createTextNode(" "+this._t("set_lux")));
    btn.addEventListener("click",function(){self._hass.callService("button","press",{entity_id:self._ent.set_lux_threshold});});
    body.appendChild(btn);
    ov.classList.add("op");
  }

  _closeM() { var ov=this.shadowRoot.getElementById("V"); if(ov)ov.classList.remove("op"); }
}

customElements.define("smart-lighting-card",SmartLightingCard);
window.customCards=window.customCards||[];
window.customCards.push({type:"smart-lighting-card",name:"Smart Lighting Card",description:"Smart lighting with dual timer bars, state indicator, profile/actuator/suspend badge",preview:true});
console.info("%c SMART-LIGHTING-CARD %c v11 ","color:#fff;background:#03a9f4;font-weight:700;padding:2px 6px;border-radius:3px 0 0 3px","color:#03a9f4;background:#e3f2fd;padding:2px 6px;border-radius:0 3px 3px 0");
