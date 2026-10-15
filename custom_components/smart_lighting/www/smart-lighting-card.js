/**
 * Smart Lighting Card v12 - Custom Lovelace Card
 *
 * Layout:
 *   TOP-RIGHT badge: profile (🌙/☀️) · actuator set · suspend flag
 *   TOP:     dual timer bars (active + failsafe)
 *   CENTER:  large light icon (tap = toggle)
 *   MIDDLE:  mode label (localised) + raw state below it
 *   BOTTOM:  motion · occupancy · lux icons (click = more-info)
 *   GEAR:    settings popup with all parameters; (i) next to each
 *            parameter toggles its localized help text [Spec §19]
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
    adaptive_factor:"Adaptive Factor", activations:"Activations"
  },
  it: {
    idle:"Inattivo", active:"Automatico", warning:"Avviso",
    temp_override:"Manuale", perm_override:"Override", suspended:"Sospeso",
    settings:"Impostazioni", state:"Stato", profile:"Profilo",
    adaptive_factor:"Fattore Adattivo", activations:"Attivazioni"
  },
  fr: {
    idle:"Inactif", active:"Automatique", warning:"Avertissement",
    temp_override:"Manuel", perm_override:"Forçage", suspended:"Suspendu",
    settings:"Paramètres", state:"État", profile:"Profil",
    adaptive_factor:"Facteur Adaptatif", activations:"Activations"
  },
  es: {
    idle:"Inactivo", active:"Automático", warning:"Advertencia",
    temp_override:"Manual", perm_override:"Anulación", suspended:"Suspendido",
    settings:"Ajustes", state:"Estado", profile:"Perfil",
    adaptive_factor:"Factor Adaptativo", activations:"Activaciones"
  },
  de: {
    idle:"Inaktiv", active:"Automatisch", warning:"Warnung",
    temp_override:"Manuell", perm_override:"Überschreibung", suspended:"Pausiert",
    settings:"Einstellungen", state:"Status", profile:"Profil",
    adaptive_factor:"Adaptiver Faktor", activations:"Aktivierungen"
  }
};

/* BEGIN SL_PARAMS - generated from translations (label, help) [Spec §19] */
var SL_PARAMS = {
 "en": {
  "occupancy_timeout": [
   "Occupancy timeout",
   "Countdown before switch-off. It starts when presence ends (occupancy sensor off, or motion off if no occupancy sensor), restarts at every motion and is cancelled when occupancy returns. When it expires the warning dim starts. Multiplied by the adaptive factor in busy areas."
  ],
  "failsafe_timeout": [
   "Failsafe timeout",
   "Safety net: with no motion for this time everything is forced off, relay included (protects against an occupancy sensor stuck on). Restarts at every motion. Ignored during permanent override."
  ],
  "perm_override_timeout": [
   "Permanent override timeout",
   "Maximum duration of the permanent override (double click). When it expires the light switches off and automatic mode resumes."
  ],
  "temp_override_timeout": [
   "Temporary override timeout",
   "In temporary override (single click) every click toggles the light and restarts this timer. When it expires automatic mode resumes: light on if the area is occupied and dark, otherwise off. 0 = never expires by itself."
  ],
  "warning_dim_pct": [
   "Warning dim",
   "Before switching off, the bulbs are dimmed to this percentage of the current brightness to warn whoever is still in the room. Any motion or occupancy cancels the warning and restores brightness. Effective only with smart bulbs."
  ],
  "warning_dim_duration": [
   "Warning dim duration",
   "How long the light stays dimmed before switching off."
  ],
  "lux_threshold": [
   "Lux threshold",
   "Ambient light level below which motion switches the light on. If the light is on, the reading reaches this value and the occupancy sensor is off, the light switches off. Tip: the 'Set lux threshold' button stores the current reading."
  ],
  "adaptive_window": [
   "Adaptive window",
   "Rolling time window in which automatic activations are counted to detect a high-traffic area."
  ],
  "adaptive_threshold": [
   "Adaptive threshold",
   "Number of activations within the window above which the occupancy timeout starts to be extended."
  ],
  "adaptive_multiplier": [
   "Adaptive multiplier",
   "Each activation beyond the threshold multiplies the occupancy timeout by this factor (factor = multiplier ^ extra activations). Example: 1.5 with 2 extra activations → ×2.25."
  ],
  "adaptive_max_factor": [
   "Adaptive max factor",
   "Upper limit of the extension (e.g. 4.0 → at most 4× the occupancy timeout). Each time the timeout expires normally, the extra part of the factor is halved."
  ],
  "lux_hysteresis_pct": [
   "Natural light margin",
   "Natural-light auto-off: with the light on in the normal profile, if ambient light exceeds threshold × (1 + margin/100) the light switches off even if the area is occupied (e.g. shutters opened)."
  ],
  "lux_hysteresis_time": [
   "Natural light delay",
   "Seconds the reading must stay above the margin before the natural-light auto-off, to ignore short peaks."
  ],
  "set_lux_threshold": [
   "Set Lux Threshold",
   "Reads the illuminance sensor now and stores that value as the new lux threshold. Use it when the room has the light level at which the lights should start switching on."
  ]
 },
 "it": {
  "occupancy_timeout": [
   "Timeout occupazione",
   "Conto alla rovescia prima dello spegnimento. Parte quando la presenza termina (sensore di occupazione spento, o movimento spento se manca il sensore di occupazione), riparte a ogni movimento e si annulla quando l'occupazione ritorna. Alla scadenza inizia il preavviso. Moltiplicato dal fattore adattivo nelle aree di passaggio."
  ],
  "failsafe_timeout": [
   "Timeout di sicurezza",
   "Rete di sicurezza: senza movimento per questo tempo si spegne tutto, relè compreso (protegge da un sensore di occupazione bloccato su attivo). Riparte a ogni movimento. Ignorato durante l'override permanente."
  ],
  "perm_override_timeout": [
   "Timeout override permanente",
   "Durata massima dell'override permanente (doppio click). Alla scadenza la luce si spegne e riprende la modalità automatica."
  ],
  "temp_override_timeout": [
   "Timeout override temporaneo",
   "In override temporaneo (click singolo) ogni click inverte la luce e riavvia questo timer. Alla scadenza riprende la modalità automatica: luce accesa se l'area è occupata e buia, altrimenti spenta. 0 = non scade mai da solo."
  ],
  "warning_dim_pct": [
   "Preavviso: luminosità",
   "Prima dello spegnimento le lampadine scendono a questa percentuale della luminosità attuale, per avvisare chi è ancora nella stanza. Qualsiasi movimento o occupazione annulla il preavviso e ripristina la luminosità. Efficace solo con lampadine smart."
  ],
  "warning_dim_duration": [
   "Preavviso: durata",
   "Per quanto tempo la luce resta abbassata prima di spegnersi."
  ],
  "lux_threshold": [
   "Soglia lux",
   "Livello di luce ambiente sotto il quale il movimento accende la luce. Se la luce è accesa, la lettura raggiunge questo valore e il sensore di occupazione è spento, la luce si spegne. Suggerimento: il pulsante 'Imposta soglia lux' memorizza la lettura attuale."
  ],
  "adaptive_window": [
   "Finestra adattiva",
   "Finestra temporale mobile in cui si contano le accensioni automatiche per riconoscere un'area di passaggio."
  ],
  "adaptive_threshold": [
   "Soglia adattiva",
   "Numero di accensioni nella finestra oltre il quale il timeout di occupazione inizia ad allungarsi."
  ],
  "adaptive_multiplier": [
   "Moltiplicatore adattivo",
   "Ogni accensione oltre la soglia moltiplica il timeout di occupazione per questo fattore (fattore = moltiplicatore ^ accensioni in eccesso). Esempio: 1,5 con 2 accensioni in eccesso → ×2,25."
  ],
  "adaptive_max_factor": [
   "Fattore adattivo massimo",
   "Limite superiore dell'allungamento (es. 4,0 → al massimo 4× il timeout di occupazione). Ogni volta che il timeout scade normalmente, la parte in eccesso del fattore si dimezza."
  ],
  "lux_hysteresis_pct": [
   "Margine luce naturale",
   "Spegnimento per luce naturale: con la luce accesa nel profilo normale, se la luce ambiente supera soglia × (1 + margine/100) la luce si spegne anche se l'area è occupata (es. tapparelle aperte)."
  ],
  "lux_hysteresis_time": [
   "Ritardo luce naturale",
   "Secondi in cui la lettura deve restare sopra il margine prima dello spegnimento per luce naturale, per ignorare picchi brevi."
  ],
  "set_lux_threshold": [
   "Imposta soglia lux",
   "Legge ora il sensore di luminosità e salva quel valore come nuova soglia lux. Usalo quando la stanza ha il livello di luce al quale le luci devono iniziare ad accendersi."
  ]
 },
 "fr": {
  "occupancy_timeout": [
   "Délai d'occupation",
   "Compte à rebours avant extinction. Il démarre à la fin de la présence (occupation inactive, ou mouvement inactif sans capteur d'occupation), redémarre à chaque mouvement et s'annule au retour de l'occupation. À l'échéance, le préavis commence. Multiplié par le facteur adaptatif dans les zones de passage."
  ],
  "failsafe_timeout": [
   "Délai de sécurité",
   "Filet de sécurité : sans mouvement pendant ce temps, tout est éteint, relais compris (protège contre un capteur d'occupation bloqué). Redémarre à chaque mouvement. Ignoré en forçage permanent."
  ],
  "perm_override_timeout": [
   "Délai forçage permanent",
   "Durée maximale du forçage permanent (double clic). À l'échéance, la lumière s'éteint et le mode automatique reprend."
  ],
  "temp_override_timeout": [
   "Délai forçage temporaire",
   "En forçage temporaire (clic simple), chaque clic inverse la lumière et relance cette minuterie. À l'échéance, le mode automatique reprend : allumée si la pièce est occupée et sombre, sinon éteinte. 0 = n'expire jamais seul."
  ],
  "warning_dim_pct": [
   "Préavis : luminosité",
   "Avant l'extinction, les ampoules baissent à ce pourcentage de la luminosité actuelle pour avertir les personnes encore présentes. Tout mouvement ou occupation annule le préavis et rétablit la luminosité. Effectif uniquement avec des ampoules connectées."
  ],
  "warning_dim_duration": [
   "Préavis : durée",
   "Durée pendant laquelle la lumière reste baissée avant de s'éteindre."
  ],
  "lux_threshold": [
   "Seuil lux",
   "Niveau de lumière ambiante sous lequel le mouvement allume la lumière. Si la lumière est allumée, que la mesure atteint cette valeur et que l'occupation est inactive, la lumière s'éteint. Astuce : le bouton « Définir le seuil lux » enregistre la mesure actuelle."
  ],
  "adaptive_window": [
   "Fenêtre adaptative",
   "Fenêtre glissante dans laquelle les allumages automatiques sont comptés pour détecter une zone de passage."
  ],
  "adaptive_threshold": [
   "Seuil adaptatif",
   "Nombre d'allumages dans la fenêtre au-delà duquel le délai d'occupation commence à s'allonger."
  ],
  "adaptive_multiplier": [
   "Multiplicateur adaptatif",
   "Chaque allumage au-delà du seuil multiplie le délai d'occupation par ce facteur (facteur = multiplicateur ^ allumages en excès). Exemple : 1,5 avec 2 allumages en excès → ×2,25."
  ],
  "adaptive_max_factor": [
   "Facteur adaptatif maximal",
   "Limite supérieure de l'allongement (ex. 4,0 → au plus 4× le délai d'occupation). À chaque échéance normale du délai, la part en excès du facteur est divisée par deux."
  ],
  "lux_hysteresis_pct": [
   "Marge lumière naturelle",
   "Extinction par lumière naturelle : lumière allumée en profil normal, si la luminosité dépasse seuil × (1 + marge/100), la lumière s'éteint même si la pièce est occupée (ex. volets ouverts)."
  ],
  "lux_hysteresis_time": [
   "Délai lumière naturelle",
   "Secondes pendant lesquelles la mesure doit rester au-dessus de la marge avant l'extinction, pour ignorer les pics brefs."
  ],
  "set_lux_threshold": [
   "Définir le seuil lux",
   "Lit maintenant le capteur de luminosité et enregistre cette valeur comme nouveau seuil lux. À utiliser quand la pièce a le niveau de lumière auquel l'éclairage doit commencer à s'allumer."
  ]
 },
 "es": {
  "occupancy_timeout": [
   "Tiempo de ocupación",
   "Cuenta atrás antes del apagado. Empieza cuando termina la presencia (ocupación inactiva, o movimiento inactivo si no hay sensor de ocupación), se reinicia con cada movimiento y se cancela si vuelve la ocupación. Al vencer empieza el aviso previo. Se multiplica por el factor adaptativo en zonas de paso."
  ],
  "failsafe_timeout": [
   "Tiempo de seguridad",
   "Red de seguridad: sin movimiento durante este tiempo se apaga todo, relé incluido (protege ante un sensor de ocupación bloqueado). Se reinicia con cada movimiento. Se ignora en anulación permanente."
  ],
  "perm_override_timeout": [
   "Tiempo anulación permanente",
   "Duración máxima de la anulación permanente (doble clic). Al vencer, la luz se apaga y vuelve el modo automático."
  ],
  "temp_override_timeout": [
   "Tiempo anulación temporal",
   "En anulación temporal (clic simple) cada clic invierte la luz y reinicia este temporizador. Al vencer vuelve el modo automático: encendida si el área está ocupada y oscura, si no apagada. 0 = nunca vence por sí sola."
  ],
  "warning_dim_pct": [
   "Aviso: brillo",
   "Antes de apagar, las bombillas bajan a este porcentaje del brillo actual para avisar a quien siga en la sala. Cualquier movimiento u ocupación cancela el aviso y restaura el brillo. Solo es efectivo con bombillas inteligentes."
  ],
  "warning_dim_duration": [
   "Aviso: duración",
   "Tiempo que la luz permanece atenuada antes de apagarse."
  ],
  "lux_threshold": [
   "Umbral lux",
   "Nivel de luz ambiente por debajo del cual el movimiento enciende la luz. Si la luz está encendida, la lectura alcanza este valor y la ocupación está inactiva, la luz se apaga. Consejo: el botón «Fijar umbral lux» guarda la lectura actual."
  ],
  "adaptive_window": [
   "Ventana adaptativa",
   "Ventana de tiempo móvil en la que se cuentan los encendidos automáticos para detectar una zona de paso."
  ],
  "adaptive_threshold": [
   "Umbral adaptativo",
   "Número de encendidos en la ventana a partir del cual el tiempo de ocupación empieza a alargarse."
  ],
  "adaptive_multiplier": [
   "Multiplicador adaptativo",
   "Cada encendido por encima del umbral multiplica el tiempo de ocupación por este factor (factor = multiplicador ^ encendidos en exceso). Ejemplo: 1,5 con 2 encendidos en exceso → ×2,25."
  ],
  "adaptive_max_factor": [
   "Factor adaptativo máximo",
   "Límite superior del alargamiento (p. ej. 4,0 → como máximo 4× el tiempo de ocupación). Cada vez que el tiempo vence con normalidad, la parte en exceso del factor se reduce a la mitad."
  ],
  "lux_hysteresis_pct": [
   "Margen luz natural",
   "Apagado por luz natural: con la luz encendida en perfil normal, si la luz ambiente supera umbral × (1 + margen/100) la luz se apaga aunque el área esté ocupada (p. ej. persianas abiertas)."
  ],
  "lux_hysteresis_time": [
   "Retardo luz natural",
   "Segundos que la lectura debe permanecer por encima del margen antes del apagado, para ignorar picos breves."
  ],
  "set_lux_threshold": [
   "Fijar umbral lux",
   "Lee ahora el sensor de luminosidad y guarda ese valor como nuevo umbral lux. Úsalo cuando la sala tenga el nivel de luz al que las luces deben empezar a encenderse."
  ]
 },
 "de": {
  "occupancy_timeout": [
   "Belegungszeit",
   "Countdown bis zum Ausschalten. Er startet, wenn die Anwesenheit endet (Belegungssensor inaktiv, oder Bewegung inaktiv ohne Belegungssensor), startet bei jeder Bewegung neu und wird abgebrochen, wenn die Belegung zurückkehrt. Danach beginnt die Vorwarnung. Wird in Durchgangsbereichen mit dem adaptiven Faktor multipliziert."
  ],
  "failsafe_timeout": [
   "Sicherheitszeit",
   "Sicherheitsnetz: Ohne Bewegung für diese Zeit wird alles ausgeschaltet, inklusive Relais (schützt vor einem hängenden Belegungssensor). Startet bei jeder Bewegung neu. Wird bei permanenter Übersteuerung ignoriert."
  ],
  "perm_override_timeout": [
   "Dauer permanente Übersteuerung",
   "Maximale Dauer der permanenten Übersteuerung (Doppelklick). Danach schaltet das Licht aus und der Automatikbetrieb wird fortgesetzt."
  ],
  "temp_override_timeout": [
   "Dauer temporäre Übersteuerung",
   "In der temporären Übersteuerung (Einzelklick) schaltet jeder Klick das Licht um und startet diesen Timer neu. Danach wird der Automatikbetrieb fortgesetzt: Licht an, wenn der Bereich belegt und dunkel ist, sonst aus. 0 = läuft nie von selbst ab."
  ],
  "warning_dim_pct": [
   "Vorwarnung: Helligkeit",
   "Vor dem Ausschalten werden die Lampen auf diesen Prozentsatz der aktuellen Helligkeit gedimmt, um Anwesende zu warnen. Jede Bewegung oder Belegung bricht die Vorwarnung ab und stellt die Helligkeit wieder her. Nur mit smarten Lampen wirksam."
  ],
  "warning_dim_duration": [
   "Vorwarnung: Dauer",
   "Wie lange das Licht gedimmt bleibt, bevor es ausschaltet."
  ],
  "lux_threshold": [
   "Lux-Schwelle",
   "Umgebungslicht, unterhalb dessen Bewegung das Licht einschaltet. Ist das Licht an, erreicht der Messwert diesen Wert und ist der Belegungssensor inaktiv, schaltet das Licht aus. Tipp: Die Schaltfläche „Lux-Schwelle setzen“ übernimmt den aktuellen Messwert."
  ],
  "adaptive_window": [
   "Adaptives Fenster",
   "Gleitendes Zeitfenster, in dem automatische Einschaltungen gezählt werden, um einen Durchgangsbereich zu erkennen."
  ],
  "adaptive_threshold": [
   "Adaptive Schwelle",
   "Anzahl der Einschaltungen im Fenster, ab der die Belegungszeit verlängert wird."
  ],
  "adaptive_multiplier": [
   "Adaptiver Multiplikator",
   "Jede Einschaltung über der Schwelle multipliziert die Belegungszeit mit diesem Faktor (Faktor = Multiplikator ^ überzählige Einschaltungen). Beispiel: 1,5 bei 2 überzähligen Einschaltungen → ×2,25."
  ],
  "adaptive_max_factor": [
   "Maximaler adaptiver Faktor",
   "Obergrenze der Verlängerung (z. B. 4,0 → höchstens 4× die Belegungszeit). Bei jedem normalen Ablauf der Belegungszeit wird der überzählige Anteil des Faktors halbiert."
  ],
  "lux_hysteresis_pct": [
   "Tageslicht-Spanne",
   "Abschaltung bei Tageslicht: Ist das Licht im Normalprofil an und übersteigt das Umgebungslicht Schwelle × (1 + Spanne/100), schaltet es aus, auch wenn der Bereich belegt ist (z. B. Rollläden geöffnet)."
  ],
  "lux_hysteresis_time": [
   "Tageslicht-Verzögerung",
   "Sekunden, die der Messwert über der Spanne bleiben muss, bevor wegen Tageslicht abgeschaltet wird, um kurze Spitzen zu ignorieren."
  ],
  "set_lux_threshold": [
   "Lux-Schwelle setzen",
   "Liest jetzt den Helligkeitssensor und speichert diesen Wert als neue Lux-Schwelle. Nutze es, wenn der Raum die Helligkeit hat, ab der das Licht einschalten soll."
  ]
 }
};
/* END SL_PARAMS */

class SmartLightingCard extends HTMLElement {

  constructor() {
    super();
    this.attachShadow({ mode:"open" });
    this._hass = null; this._config = null;
    this._rendered = false; this._timer = null; this._lang = "en";
  }

  _t(k) { var d=SL_I18N[this._lang]||SL_I18N.en; return d[k]||(SL_I18N.en[k]||k); }

  /* Parameter [label, help] in the HA language, English fallback [Spec §19] */
  _p(k) { var d=SL_PARAMS[this._lang]||SL_PARAMS.en; return d[k]||SL_PARAMS.en[k]||[k,""]; }

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
      ".pw{border-bottom:1px solid var(--divider-color,#e0e0e0)}",
      ".pw:last-of-type{border-bottom:none}",
      ".mr{display:flex;align-items:center;justify-content:space-between;padding:9px 0}",
      /* (i) help toggle + help text [Spec §19] */
      ".hi{--mdc-icon-size:16px;color:var(--secondary-text-color,#727272);cursor:pointer;margin-left:4px;vertical-align:middle;-webkit-tap-highlight-color:transparent}",
      ".hi.on{color:var(--primary-color,#03a9f4)}",
      ".ht{display:none;font-size:12px;line-height:1.4;color:var(--secondary-text-color,#727272);padding:0 0 9px 0}",
      ".ht.op{display:block}",
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
      {e:this._ent.perm_override_timeout,  k:"perm_override_timeout",u:"s",  s:60},
      {e:this._ent.temp_override_timeout,  k:"temp_override_timeout",u:"s",  s:60},
      {e:this._ent.warning_dim_pct,       k:"warning_dim_pct",      u:"%",  s:5},
      {e:this._ent.warning_dim_duration,  k:"warning_dim_duration",  u:"s",  s:1},
      {e:this._ent.lux_threshold,         k:"lux_threshold",        u:"lx", s:1},
      {e:this._ent.adaptive_window,       k:"adaptive_window",      u:"s",  s:60},
      {e:this._ent.adaptive_threshold_n,  k:"adaptive_threshold",   u:"",   s:1},
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
      var pt=this._p(c.k);
      var pw=document.createElement("div"); pw.className="pw";
      var row=document.createElement("div"); row.className="mr";
      var lbl=document.createElement("span"); lbl.className="ml"; lbl.textContent=pt[0];
      var help=this._helpRow(lbl, pt[1]); row.appendChild(lbl);
      var vd=document.createElement("div"); vd.className="mv";
      var inp=document.createElement("input"); inp.type="number"; inp.value=v; inp.min=mn; inp.max=mx; inp.step=c.s;
      vd.appendChild(inp);
      var un=document.createElement("span"); un.className="mu"; un.textContent=c.u; vd.appendChild(un);
      row.appendChild(vd); pw.appendChild(row); if(help)pw.appendChild(help); body.appendChild(pw);
      (function(entity){inp.addEventListener("change",function(ev){var nv=parseFloat(ev.target.value);if(!isNaN(nv))self._hass.callService("number","set_value",{entity_id:entity,value:nv});});})(c.e);
    }

    /* button */
    var btn=document.createElement("button"); btn.className="lb";
    var btnI=document.createElement("ha-icon"); btnI.setAttribute("icon","mdi:brightness-auto"); btn.appendChild(btnI);
    var bp=this._p("set_lux_threshold");
    btn.appendChild(document.createTextNode(" "+bp[0]));
    btn.addEventListener("click",function(){self._hass.callService("button","press",{entity_id:self._ent.set_lux_threshold});});
    body.appendChild(btn);
    if (bp[1]) { var bh=document.createElement("div"); bh.className="ht op"; bh.textContent=bp[1]; bh.style.paddingTop="8px"; body.appendChild(bh); }
    ov.classList.add("op");
  }

  /* Append an (i) icon to the label and return the hidden help element
     it toggles; null when there is no help text [Spec §19] */
  _helpRow(lbl, text) {
    if (!text) return null;
    var ht=document.createElement("div"); ht.className="ht"; ht.textContent=text;
    var hi=document.createElement("ha-icon"); hi.className="hi"; hi.setAttribute("icon","mdi:information-outline");
    hi.addEventListener("click",function(ev){ ev.stopPropagation(); ht.classList.toggle("op"); hi.classList.toggle("on"); });
    lbl.appendChild(hi);
    return ht;
  }

  _closeM() { var ov=this.shadowRoot.getElementById("V"); if(ov)ov.classList.remove("op"); }
}

customElements.define("smart-lighting-card",SmartLightingCard);
window.customCards=window.customCards||[];
window.customCards.push({type:"smart-lighting-card",name:"Smart Lighting Card",description:"Smart lighting with dual timer bars, state indicator, profile/actuator/suspend badge",preview:true});
console.info("%c SMART-LIGHTING-CARD %c v12 ","color:#fff;background:#03a9f4;font-weight:700;padding:2px 6px;border-radius:3px 0 0 3px","color:#03a9f4;background:#e3f2fd;padding:2px 6px;border-radius:0 3px 3px 0");
