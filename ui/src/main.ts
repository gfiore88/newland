import "./style.css";

import { displayName } from "./layout";
import { NewlandMapScene, type Selection } from "./map-scene";
import { ObserverStore } from "./observer-store";
import type { EventEnvelope, ObserverSnapshot } from "./types";

const root = document.querySelector<HTMLDivElement>("#app");
if (!root) throw new Error("Missing #app root");

root.innerHTML = `
  <main class="observer-shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">NEWLAND / OSSERVATORE</p>
        <h1>Il territorio respira.</h1>
      </div>
      <div class="world-clock" aria-live="polite">
        <span id="world-date">Tempo non disponibile</span>
        <span id="world-tick">tick —</span>
      </div>
      <div class="connection" id="connection" data-state="connecting">
        <span class="connection-dot"></span>
        <span id="connection-label">connessione</span>
      </div>
    </header>

    <section class="map-panel" aria-label="Territorio osservabile">
      <div class="map-atmosphere"></div>
      <div id="world-stage" class="world-stage"></div>
      <div class="map-guidance">trascina per muovere · rotella per avvicinare</div>
      <nav class="time-controls" aria-label="Navigazione temporale dell'Observer">
        <button id="time-toggle" type="button">Pausa visiva</button>
        <button id="replay-toggle" type="button" disabled>Riproduci</button>
        <input id="time-slider" type="range" min="0" max="0" value="0" step="1" />
        <span id="time-label">vista #0 / live #0</span>
      </nav>
      <div id="map-error" class="map-error" hidden></div>
      <article class="chronicle-panel" aria-live="polite">
        <div class="section-heading">
          <p class="eyebrow">IL CRONISTA SILENZIOSO</p>
          <span id="chronicle-sequence">voce —</span>
        </div>
        <div id="chronicle-entry" class="chronicle-entry empty-state">
          Il Cronista è in ascolto. Nessuna voce generativa è ancora stata persistita.
        </div>
      </article>
    </section>

    <aside class="side-panel">
      <section class="panel-block inhabitants-block">
        <div class="section-heading">
          <p class="eyebrow">PRESENZE</p>
          <span id="inhabitant-count">0</span>
        </div>
        <div id="inhabitants" class="inhabitants" aria-label="Newlander osservabili"></div>
      </section>

      <section class="panel-block inspector-block" aria-live="polite">
        <p class="eyebrow">CONSOLE DELL'ARCHITETTO</p>
        <div id="inspector" class="inspector empty-state">
          Seleziona una presenza, un luogo o una traccia materiale. L'osservazione non produce effetti nel mondo.
        </div>
      </section>

      <section class="panel-block event-block">
        <div class="section-heading">
          <p class="eyebrow">REGISTRO CANONICO</p>
          <span id="event-sequence">#—</span>
        </div>
        <ol id="event-list" class="event-list"></ol>
      </section>
    </aside>
  </main>
`;

const stage = requiredElement<HTMLDivElement>("#world-stage");
const apiBase = import.meta.env.VITE_OBSERVER_API ?? window.location.origin;
const store = new ObserverStore(apiBase);
let selection: Selection | null = null;
let lastRenderedSequence = -1;
let mapScene: NewlandMapScene | null = null;

store.subscribe(() => {
  renderConnection();
  const snapshot = store.state.viewSnapshot;
  if (!snapshot) return;
  renderClock(snapshot);
  renderTimeControls(snapshot);
  renderInhabitants(snapshot, selection);
  renderInspector(snapshot, selection);
  renderEvents(store.state.viewEvents, snapshot.last_sequence);
  renderChronicle(snapshot.last_sequence);
  if (snapshot.last_sequence !== lastRenderedSequence) {
    mapScene?.render(snapshot.world);
    lastRenderedSequence = snapshot.last_sequence;
  }
});

requiredElement<HTMLButtonElement>("#time-toggle").addEventListener("click", () => {
  stopReplay();
  if (store.state.viewMode === "live") store.pause();
  else store.goLive();
});

let replayActive = false;
let replayTimer: ReturnType<typeof setTimeout> | null = null;
requiredElement<HTMLButtonElement>("#replay-toggle").addEventListener("click", () => {
  if (replayActive) {
    stopReplay();
    return;
  }
  replayActive = true;
  const snapshot = store.state.viewSnapshot;
  if (snapshot) renderTimeControls(snapshot);
  void advanceReplay();
});

let seekTimer: ReturnType<typeof setTimeout> | null = null;
requiredElement<HTMLInputElement>("#time-slider").addEventListener("input", (event) => {
  stopReplay();
  const sequence = Number((event.currentTarget as HTMLInputElement).value);
  if (seekTimer !== null) clearTimeout(seekTimer);
  seekTimer = setTimeout(() => {
    seekTimer = null;
    void store.seek(sequence);
  }, 70);
});

window.addEventListener("beforeunload", () => {
  stopReplay();
  store.stop();
  mapScene?.destroy();
});

void store.start();
void initializeMap();

async function initializeMap(): Promise<void> {
  const mapError = requiredElement<HTMLDivElement>("#map-error");
  const slowInitialization = setTimeout(() => {
    mapError.hidden = false;
    mapError.textContent =
      "WebGL non risponde ancora. I dati dell'Observer restano disponibili.";
  }, 5_000);
  try {
    const scene = await NewlandMapScene.create(stage, (nextSelection) => {
      selection = nextSelection;
      const snapshot = store.state.viewSnapshot;
      if (snapshot) {
        renderInspector(snapshot, selection);
        renderInhabitants(snapshot, selection);
      }
    });
    mapScene = scene;
    clearTimeout(slowInitialization);
    mapError.hidden = true;
    const canvas = stage.querySelector<HTMLCanvasElement>("canvas");
    canvas?.addEventListener("webglcontextlost", (event) => {
      event.preventDefault();
      mapError.hidden = false;
      mapError.textContent =
        "Contesto WebGL perso. Firefox sta tentando di ripristinarlo.";
    });
    canvas?.addEventListener("webglcontextrestored", () => {
      mapError.hidden = true;
      const snapshot = store.state.viewSnapshot;
      if (snapshot) scene.render(snapshot.world);
    });
    const snapshot = store.state.viewSnapshot;
    if (snapshot) {
      scene.render(snapshot.world);
      lastRenderedSequence = snapshot.last_sequence;
    }
  } catch (error) {
    clearTimeout(slowInitialization);
    const message = error instanceof Error ? error.message : String(error);
    mapError.hidden = false;
    mapError.textContent = `WebGL non disponibile: ${message}`;
  }
}

function renderConnection(): void {
  const indicator = requiredElement<HTMLDivElement>("#connection");
  const label = requiredElement<HTMLSpanElement>("#connection-label");
  indicator.dataset.state = store.state.connection;
  label.textContent = store.state.error
    ? "non raggiungibile"
    : store.state.viewMode === "paused"
      ? `${store.state.connection} · vista in pausa`
      : store.state.connection;
  indicator.title = store.state.error ?? "Flusso Observer locale";
}

function renderChronicle(throughSequence: number): void {
  const container = requiredElement<HTMLDivElement>("#chronicle-entry");
  const sequence = requiredElement<HTMLSpanElement>("#chronicle-sequence");
  const entry = store.state.chronicle
    .filter((candidate) => candidate.through_sequence <= throughSequence)
    .at(-1);
  if (!entry) {
    sequence.textContent = "voce —";
    container.className = "chronicle-entry empty-state";
    container.textContent =
      "Il Cronista è in ascolto. Nessuna voce generativa è ancora stata persistita.";
    return;
  }
  sequence.textContent = `voce ${entry.sequence}`;
  container.className = "chronicle-entry";
  container.innerHTML = `
    <h2>${escapeHtml(entry.title)}</h2>
    ${entry.prose
      .split(/\n\s*\n/)
      .map((paragraph) => `<p>${escapeHtml(paragraph)}</p>`)
      .join("")}
    <footer>
      <span>${escapeHtml(entry.model)} · tentativo ${entry.attempts}</span>
      <span>eventi ${entry.from_sequence}–${entry.through_sequence}</span>
    </footer>
  `;
}

function renderTimeControls(snapshot: ObserverSnapshot): void {
  const toggle = requiredElement<HTMLButtonElement>("#time-toggle");
  const replay = requiredElement<HTMLButtonElement>("#replay-toggle");
  const slider = requiredElement<HTMLInputElement>("#time-slider");
  const label = requiredElement<HTMLSpanElement>("#time-label");
  const maximum = Math.max(store.state.liveSequence, snapshot.latest_sequence);
  slider.max = String(maximum);
  slider.value = String(snapshot.last_sequence);
  toggle.textContent =
    store.state.viewMode === "live" ? "Pausa visiva" : "Torna al presente";
  toggle.dataset.mode = store.state.viewMode;
  replay.disabled =
    store.state.viewMode === "live" || snapshot.last_sequence >= maximum;
  replay.textContent = replayActive ? "Ferma replay" : "Riproduci";
  replay.dataset.active = String(replayActive);
  label.textContent = `vista #${snapshot.last_sequence} / live #${maximum}`;
}

async function advanceReplay(): Promise<void> {
  if (!replayActive) return;
  const snapshot = store.state.viewSnapshot;
  if (!snapshot || snapshot.last_sequence >= store.state.liveSequence) {
    stopReplay();
    return;
  }
  await store.seek(snapshot.last_sequence + 1);
  if (!replayActive) return;
  replayTimer = setTimeout(() => void advanceReplay(), 520);
}

function stopReplay(): void {
  replayActive = false;
  if (replayTimer !== null) {
    clearTimeout(replayTimer);
    replayTimer = null;
  }
  const snapshot = store.state.viewSnapshot;
  if (snapshot) renderTimeControls(snapshot);
}

function renderClock(snapshot: ObserverSnapshot): void {
  requiredElement<HTMLSpanElement>("#world-date").textContent = formatWorldTime(
    snapshot.world.world_time,
  );
  requiredElement<HTMLSpanElement>("#world-tick").textContent = `tick ${snapshot.world.tick}`;
  requiredElement<HTMLSpanElement>("#event-sequence").textContent =
    `#${snapshot.last_sequence}`;
}

function renderInhabitants(snapshot: ObserverSnapshot, active: Selection | null): void {
  const agents = Object.values(snapshot.world.agents).sort((left, right) =>
    left.name.localeCompare(right.name),
  );
  requiredElement<HTMLSpanElement>("#inhabitant-count").textContent = String(agents.length);
  const container = requiredElement<HTMLDivElement>("#inhabitants");
  container.replaceChildren(
    ...agents.map((agent) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "inhabitant-card";
      button.dataset.active = String(active?.kind === "agent" && active.id === agent.agent_id);
      button.innerHTML = `
        <span class="inhabitant-mark">${escapeHtml(initials(agent.name))}</span>
        <span>
          <strong>${escapeHtml(agent.name)}</strong>
          <small>${escapeHtml(displayName(agent.location))}</small>
        </span>
        <span class="energy-glyph" title="Energia ${Math.round(agent.energy * 100)}%">
          <i style="--level:${agent.energy}"></i>
        </span>
      `;
      button.addEventListener("click", () => {
        selection = { kind: "agent", id: agent.agent_id };
        renderInspector(snapshot, selection);
        renderInhabitants(snapshot, selection);
        mapScene?.focus(selection, snapshot.world);
      });
      return button;
    }),
  );
}

function renderInspector(snapshot: ObserverSnapshot, active: Selection | null): void {
  const inspector = requiredElement<HTMLDivElement>("#inspector");
  if (!active) {
    inspector.className = "inspector empty-state";
    inspector.textContent =
      "Seleziona una presenza, un luogo o una traccia materiale. L'osservazione non produce effetti nel mondo.";
    return;
  }
  inspector.className = "inspector";
  if (active.kind === "agent") {
    const agent = snapshot.world.agents[active.id];
    const mind = snapshot.minds[active.id];
    if (!agent) {
      inspector.className = "inspector empty-state";
      inspector.textContent =
        "Questa presenza non esisteva ancora nella sequenza osservata.";
      return;
    }
    inspector.innerHTML = `
      <div class="inspector-title">
        <span class="inhabitant-mark large">${escapeHtml(initials(agent.name))}</span>
        <div><h2>${escapeHtml(agent.name)}</h2><p>${escapeHtml(displayName(agent.location))}</p></div>
      </div>
      <div class="vitals">
        ${meter("energia", agent.energy, false)}
        ${meter("fame", agent.hunger, true)}
        ${meter("sete", agent.thirst, true)}
      </div>
      ${tagSection("Valori", mind?.values ?? [])}
      ${tagSection("Temperamento", mind?.temperament ?? [])}
      ${listSection("Obiettivi correnti", mind?.goals ?? [])}
      ${detailRow("Prossima attenzione", mind?.next_activation_tick == null ? "non fissata" : `tick ${mind.next_activation_tick}`)}
      ${detailRow("Memorie", String(mind?.memories.length ?? 0))}
      ${detailRow("Riflessioni", String(mind?.reflections.length ?? 0))}
      ${
        snapshot.is_live
          ? ""
          : '<p class="privacy-note">Le menti storiche non sono ricostruite: questa vista mostra soltanto lo stato materiale replayable.</p>'
      }
    `;
    return;
  }
  if (active.kind === "location") {
    const occupants = Object.values(snapshot.world.agents).filter(
      (agent) => agent.location === active.id,
    );
    const resources = Object.values(snapshot.world.resources).filter(
      (resource) => resource.location === active.id,
    );
    inspector.innerHTML = `
      <h2>${escapeHtml(displayName(active.id))}</h2>
      ${detailRow("Collegamenti", String(snapshot.world.locations[active.id]?.length ?? 0))}
      ${listSection("Presenze", occupants.map((agent) => agent.name))}
      ${listSection("Risorse", resources.map((resource) => `${resource.label}: ${resource.quantity} ${resource.unit}`))}
    `;
    return;
  }
  if (active.kind === "resource") {
    const resource = snapshot.world.resources[active.id];
    if (!resource) return;
    inspector.innerHTML = `
      <h2>${escapeHtml(resource.label)}</h2>
      ${detailRow("Luogo", displayName(resource.location))}
      ${detailRow("Quantità", `${resource.quantity} ${resource.unit}`)}
      ${detailRow("Rinnovabile", resource.renewable ? "sì" : "no")}
    `;
    return;
  }
  const node = snapshot.world.resonance_nodes[active.id];
  if (!node) return;
  inspector.innerHTML = `
    <h2>${escapeHtml(node.label)}</h2>
    ${detailRow("Luogo", displayName(node.location))}
    ${detailRow("Intensità fisica", `${Math.round(node.intensity * 100)}%`)}
    <p class="privacy-note">Il significato non appartiene al nodo: nasce, se nasce, nella mente di chi lo percepisce.</p>
  `;
}

function renderEvents(events: readonly EventEnvelope[], throughSequence: number): void {
  const list = requiredElement<HTMLOListElement>("#event-list");
  const recent = events
    .filter((event) => event.sequence <= throughSequence)
    .reverse()
    .slice(0, 24);
  list.replaceChildren(
    ...recent.map((event) => {
      const item = document.createElement("li");
      item.className = "event-entry";
      item.dataset.visibility = event.visibility;
      const actors = event.actor_ids.length > 0 ? event.actor_ids.join(", ") : "mondo";
      item.innerHTML = `
        <span class="event-index">${event.sequence}</span>
        <span class="event-body">
          <strong>${escapeHtml(splitEventType(event.event_type))}</strong>
          <small>${escapeHtml(actors)} · ${escapeHtml(event.location ? displayName(event.location) : "senza luogo")}</small>
        </span>
        <span class="visibility-mark" title="Visibilità: ${event.visibility}"></span>
      `;
      return item;
    }),
  );
}

function meter(label: string, value: number, inverse: boolean): string {
  const displayValue = Math.round(value * 100);
  const normalized = inverse ? 1 - value : value;
  return `<div class="meter"><span>${label}</span><i><b style="--level:${normalized}"></b></i><em>${displayValue}%</em></div>`;
}

function tagSection(label: string, values: string[]): string {
  if (values.length === 0) return "";
  return `<section class="inspect-section"><h3>${escapeHtml(label)}</h3><div class="tags">${values.map((value) => `<span>${escapeHtml(value)}</span>`).join("")}</div></section>`;
}

function listSection(label: string, values: string[]): string {
  if (values.length === 0) return "";
  return `<section class="inspect-section"><h3>${escapeHtml(label)}</h3><ul>${values.map((value) => `<li>${escapeHtml(value)}</li>`).join("")}</ul></section>`;
}

function detailRow(label: string, value: string): string {
  return `<div class="detail-row"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;
}

function splitEventType(value: string): string {
  return value.replace(/([a-z])([A-Z])/g, "$1 $2");
}

function initials(name: string): string {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0] ?? "")
    .join("")
    .toUpperCase();
}

function formatWorldTime(value: string): string {
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/);
  if (!match) return value;
  return `giorno ${Number(match[3])} · ${match[4]}:${match[5]}`;
}

function escapeHtml(value: string): string {
  return value.replace(
    /[&<>'"]/g,
    (character) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[
        character
      ] ?? character,
  );
}

function requiredElement<T extends Element>(selector: string): T {
  const element = document.querySelector<T>(selector);
  if (!element) throw new Error(`Missing ${selector}`);
  return element;
}
