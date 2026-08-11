# Smart Lighting

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Automazione illuminazione intelligente basata su aree per Home Assistant. Zero dipendenze esterne.

## Caratteristiche

- **Configurazione per area** — selettore area HA con filtraggio entità
- **Movimento + presenza** — il movimento attiva (logica OR per sensori multipli), la presenza previene il timeout
- **Sensibilità alla luce** — si attiva solo sotto soglia configurabile
- **Doppio profilo luminosità** — normale e soffuso (commutazione per orario o entità)
- **Lampadine multiple** — configurabili più lampadine smart per relay, sia per profilo normale che soffuso
- **Attuatori soft alternativi** — lampadine/relè opzionali dedicati al profilo soffuso
- **Avviso pre-spegnimento** — attenuazione a percentuale configurabile prima dello spegnimento
- **Rilevamento click integrato** — monitora un'entità switch, rileva interazioni Fisiche vs Automazione/UI tramite analisi context HA
- **Override manuale** — singolo click (temporaneo) e doppio click (permanente), solo Fisico
- **Timer override dedicati** — timeout override temporaneo (0=mai) e permanente
- **Failsafe** — nessun movimento per lungo tempo → spegnimento forzato (si resetta su motion, immune a perm override)
- **Fallback senza movimento** — presenza ON ma nessun movimento per tempo configurabile → attenuazione → spegnimento
- **Spegnimento per luce naturale** — lux sale significativamente con luci accese → spegne (finestre aperte)
- **Timeout adattivo** — estende il timeout in aree ad alto traffico, decade al valore normale
- **Modalità sospensione** — entità esterna mette in pausa l'automazione (es. modalità film)
- **Imposta soglia lux da sensore** — pulsante cattura lettura corrente come nuova soglia
- **Regolabile a runtime** — tutti i parametri modificabili senza riconfigurare, valori persistenti al riavvio
- **Device virtuale** — tutte le entità raggruppate sotto un dispositivo HA per area
- **Card Lovelace custom** — auto-registrata, con barra timer, indicatore modalità, icone stato, popup impostazioni
- **Multilingua** — EN, IT, FR, ES, DE

## Installazione

### HACS (consigliato)

1. HACS → Integrazioni → ⋮ → Repository personalizzate
2. Aggiungi `https://github.com/dvbit/smart-lighting` come **Integration**
3. Cerca "Smart Lighting" e installa
4. Riavvia Home Assistant

La card Lovelace custom viene auto-registrata come risorsa frontend.

### Manuale

Copia `custom_components/smart_lighting/` in `config/custom_components/` e riavvia. Copia `www/smart-lighting-card.js` in `/config/www/` e aggiungi come risorsa manualmente.

## Configurazione

Aggiungi tramite **Impostazioni → Dispositivi e Servizi → Aggiungi Integrazione → Smart Lighting**.

### Step 1: Area

Seleziona l'area HA. Tutti i selettori entità negli step successivi sono filtrati per quest'area.

### Step 2: Sensori

- **Sensori di movimento** — uno o più binary_sensor (logica OR: qualsiasi attiva)
- **Sensore di presenza** — un binary_sensor (previene il timeout finché occupato)
- **Sensore lux** — un sensor (attivazione solo sotto soglia)
- **Soglia luminosità** — cutoff luce ambientale in lux

### Step 3: Attuatori

- **Lampadine smart** — opzionale, entità light multiple
- **Relè** — opzionale, entità switch
- Almeno un attuatore obbligatorio
- **Lampadine profilo soffuso** — opzionale, entità light multiple per profilo soft
- **Relè profilo soffuso** — opzionale, switch per profilo soft
- **Interruttore monitorato** — opzionale, entità da monitorare per rilevamento click fisici
- **Finestra temporale click** — secondi per accumulare click (default 1.5s)
- **Entità sospensione** — opzionale, binary_sensor/input_boolean per mettere in pausa

### Step 4: Temporizzazioni

- **Timeout presenza** — secondi prima dell'attenuazione dopo che la presenza si azzera (default 300s)
- **Timeout failsafe** — secondi senza movimento prima dello spegnimento forzato (default 3600s)
- **Timeout override permanente** — auto-scadenza override permanente (default 3600s)
- **Timeout override temporaneo** — auto-scadenza override temporaneo, 0=mai (default 0)
- **Attenuazione avviso %** — percentuale luminosità durante avviso (default 30%)
- **Durata attenuazione** — secondi di attenuazione prima dello spegnimento (default 10s)
- **Timeout senza movimento** — secondi con presenza ma senza movimento prima dello spegnimento (default 1800s)
- **Finestra adattiva** — finestra mobile per conteggio attivazioni (default 600s)
- **Soglia adattiva** — attivazioni nella finestra prima di estendere il timeout (default 3)
- **Moltiplicatore adattivo** — fattore per ogni attivazione extra (default 1.5)
- **Fattore massimo adattivo** — cap massimo del moltiplicatore (default 4.0)
- **Isteresi lux %** — percentuale sopra soglia per spegnimento luce naturale (default 10%)
- **Tempo isteresi lux** — secondi che la lux deve restare alta prima dello spegnimento (default 5s)

### Step 5: Profili Luminosità

- **Luminosità normale** — 1-255
- **Luminosità soffusa** — 1-255
- **Modalità profilo** — fascia oraria o basata su entità
- **Inizio/fine fascia soffusa** — orario per profilo soft
- **Entità profilo soffuso** — binary_sensor/input_boolean trigger

Tutte le impostazioni modificabili tramite **Opzioni** senza rimuovere l'integrazione.

## Entità

Ogni area configurata crea un dispositivo virtuale con queste entità:

### Light

| Entità | Descrizione |
|--------|-------------|
| `light.smart_lighting_{area}` | Controller principale, tap = toggle |

### Sensori (diagnostic)

| Entità | Descrizione |
|--------|-------------|
| `sensor.*_state` | Macchina a stati: idle, active, warning, temp_override, perm_override, suspended |
| `sensor.*_profile` | Profilo attivo: normal o soft |
| `sensor.*_occupancy_timer` | Timeout presenza rimanente (s) |
| `sensor.*_failsafe_timer` | Timeout failsafe rimanente (s) |
| `sensor.*_override_timer` | Timeout override attivo rimanente (s) |
| `sensor.*_warning_timer` | Attenuazione avviso rimanente (s) |
| `sensor.*_adaptive_factor` | Moltiplicatore adattivo corrente |
| `sensor.*_activation_count` | Attivazioni nella finestra adattiva |
| `sensor.*_lux` | Luce ambientale corrente (lx), tempo reale |
| `sensor.*_click_count` | Conteggio click nella finestra |
| `sensor.*_interaction_type` | Ultima interazione: Physical/Automation/UI |
| `sensor.*_acting_user` | Ultimo utente o "Physical" |
| `sensor.*_click_time_window` | Finestra click configurata (s) |

### Numeri (config, regolabili a runtime, persistenti)

| Entità | Descrizione |
|--------|-------------|
| `number.*_occupancy_timeout` | Timeout presenza (s) |
| `number.*_failsafe_timeout` | Timeout failsafe (s) |
| `number.*_perm_override_timeout` | Timeout override permanente (s) |
| `number.*_temp_override_timeout` | Timeout override temporaneo (s), 0=mai |
| `number.*_warning_dim_pct` | Luminosità attenuazione avviso (%) |
| `number.*_warning_dim_duration` | Durata attenuazione avviso (s) |
| `number.*_no_motion_timeout` | Timeout senza movimento (s) |
| `number.*_lux_threshold` | Soglia lux (lx) |
| `number.*_adaptive_window` | Finestra adattiva (s) |
| `number.*_adaptive_threshold` | Soglia adattiva (conteggio) |
| `number.*_adaptive_multiplier` | Moltiplicatore adattivo |
| `number.*_adaptive_max_factor` | Fattore massimo adattivo |
| `number.*_lux_hysteresis_pct` | Isteresi lux (%) |
| `number.*_lux_hysteresis_time` | Tempo isteresi lux (s) |

### Button

| Entità | Descrizione |
|--------|-------------|
| `button.*_set_lux_threshold` | Cattura lettura lux corrente come nuova soglia |

## Logica Principale

### Attivazione

Movimento rilevato + lux sotto soglia → luce ON alla luminosità del profilo corrente.

### Disattivazione

Presenza si azzera → timeout presenza → attenuazione avviso (luminosità ridotta a X%) → dopo durata attenuazione → OFF.

### Regole di Attuazione

- **Lampadine multiple + relè**: tutte le lampadine ON con stessa luminosità, relè ON. OFF: tutte le lampadine OFF, relè resta ON.
- **Solo lampadine**: on/off standard per tutte.
- **Solo relè**: on/off standard.
- **Profilo soffuso**: se attuatori soft configurati, usa quelli durante il profilo soft.
- **Failsafe OFF**: spegne tutto incluso il relè.

## Override Manuale

### Rilevamento Click (integrato)

Monitora un'entità switch/light configurata. Analizza il `context.user_id` dell'evento HA:
- `None` → Fisico (pressione interruttore a muro)
- `user_id` con `parent_id` → Automazione → ignorato per override
- `user_id` senza `parent_id` → UI → ignorato per override

I click si accumulano nella finestra temporale. Alla scadenza:
- **1 click** → override temporaneo
- **2 click** → override permanente
- **3+ click** → ignorati (accidentali)

### Override Temporaneo (1 click)

- Commuta la luce, congela lo stato
- Uscita: altro click singolo OPPURE temp_override_timeout (0 = resta indefinitamente)
- All'uscita: rivaluta condizioni motion + lux
- Casi d'uso: "restare al buio", "simulare presenza"

### Override Permanente (2 click)

- Commuta la luce, congela lo stato
- Uscita: altro doppio click OPPURE perm_override_timeout
- Immune al failsafe
- All'uscita: rivaluta condizioni motion + lux

## Failsafe

Si resetta ad ogni rilevamento movimento (anche durante override). Se nessun movimento per `failsafe_timeout` secondi:
- Forza lo spegnimento di tutto incluso il relè
- Eccezione: l'override permanente è immune

## Fallback Senza Movimento

Se il sensore presenza resta ON ma nessun movimento per `no_motion_timeout` secondi → attenuazione → OFF. Protegge contro sensori presenza bloccati o fonti di calore statiche (es. laptop caldo sulla scrivania).

## Spegnimento per Luce Naturale

Se le luci sono ON in profilo normale (non soffuso, non override) e la luce ambientale supera `soglia_lux × (1 + lux_hysteresis_pct/100)` per `lux_hysteresis_time` secondi consecutivi → spegne. Gestisce l'apertura delle finestre.

## Timeout Adattivo

Nelle aree ad alto traffico, il ciclaggio frequente acceso/spento viene prevenuto:
- Attivazioni contate in una finestra mobile
- Quando il conteggio supera la soglia: timeout occupancy moltiplicato progressivamente
- Il fattore decade quando il timeout scade normalmente (traffico calato)
- Monitorabile via `sensor.*_adaptive_factor` e `sensor.*_activation_count`

## Modalità Sospensione

Entità opzionale `suspend_entity` (binary_sensor/input_boolean):
- **ON**: stato = "suspended", tutti i timer cancellati, la luce resta com'è, tutti gli eventi ignorati
- **OFF**: rivaluta condizioni motion + lux, attiva o disattiva di conseguenza
- Caso d'uso: automazione scenario esterna (modalità film) prende il controllo dell'illuminazione

## Card Custom

```yaml
type: custom:smart-lighting-card
area: cucina
name: Cucina                    # nome visualizzato opzionale
icon_main: mdi:ceiling-light    # opzionale, icona profilo normale
icon_soft: mdi:lamp             # opzionale, icona profilo soffuso
```

- **Alto**: barra progresso timer con icona tipo (nascosta se idle)
- **Centro**: icona grande luce (cambia per profilo), tap = toggle
- **Sotto icona**: nome area
- **Indicatore modalità**: Inattivo / Automatico / Avviso / Manuale / Override / Sospeso
- **Basso-sinistra**: icone movimento, presenza, luminosità — click apre more-info dell'entità sorgente
- **Basso-destra**: ingranaggio → popup con tutti i parametri + pulsante imposta soglia lux

## Licenza

MIT
