import "./style.css";

import { displayName } from "./layout";
import { NewlandMapScene, type Selection } from "./map-scene";
import { ObserverStore } from "./observer-store";
import type {
  EventEnvelope,
  ObserverSnapshot,
  AgentMindSnapshot,
  Memory,
  Reflection,
} from "./types";
import { UI_CONSTANTS } from "./constants";

// ── suppress noisy WebGL warnings ──────────────────────────────
const origWarn = console.warn;
console.warn = (...args: unknown[]) => {
  const msg = String(args[0] ?? "");
  if (msg.includes("WebGL") || msg.includes("Alpha-premult") || msg.includes("lazy initialization")) return;
  origWarn.apply(console, args);
};

// ── globals ────────────────────────────────────────────────────
const stage = el<HTMLDivElement>("#world-stage")!;
const apiBase = import.meta.env.VITE_OBSERVER_API ?? window.location.origin;
const store = new ObserverStore(apiBase);
let selection: Selection | null = null;
let lastRenderedSequence = -1;
let mapScene: NewlandMapScene | null = null;
let selectedAgentId: string | null = null;

// ── store subscription ─────────────────────────────────────────
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
  renderCronacaStories(snapshot.last_sequence);
  renderSocialGraph(snapshot);
  renderRelazioni(snapshot);
  renderEventiFullList(store.state.viewEvents, snapshot.last_sequence);
  if (selectedAgentId) renderMentePrivata(snapshot, selectedAgentId);
  if (snapshot.last_sequence !== lastRenderedSequence) {
    mapScene?.render(snapshot.world);
    lastRenderedSequence = snapshot.last_sequence;
  }
});

// ── time controls ──────────────────────────────────────────────
el<HTMLButtonElement>("#time-toggle")?.addEventListener("click", () => {
  stopReplay();
  if (store.state.viewMode === "live") store.pause();
  else store.goLive();
});

let replayActive = false;
let replayTimer: ReturnType<typeof setTimeout> | null = null;
el<HTMLButtonElement>("#replay-toggle")?.addEventListener("click", () => {
  if (replayActive) { stopReplay(); return; }
  replayActive = true;
  const snapshot = store.state.viewSnapshot;
  if (snapshot) renderTimeControls(snapshot);
  void advanceReplay();
});

let seekTimer: ReturnType<typeof setTimeout> | null = null;
let isInteractingWithSlider = false;
const timeSlider = el<HTMLInputElement>("#time-slider")!;
timeSlider?.addEventListener("pointerdown", () => { isInteractingWithSlider = true; });
timeSlider?.addEventListener("pointerup", () => { isInteractingWithSlider = false; });
timeSlider?.addEventListener("touchstart", () => { isInteractingWithSlider = true; }, { passive: true });
timeSlider?.addEventListener("touchend", () => { isInteractingWithSlider = false; });
timeSlider?.addEventListener("change", () => { isInteractingWithSlider = false; });
timeSlider?.addEventListener("input", (event) => {
  stopReplay();
  const sequence = Number((event.currentTarget as HTMLInputElement).value);
  const maximum = Number(timeSlider.max || "0");
  const label = el<HTMLSpanElement>("#time-label");
  if (label) label.textContent = `vista #${sequence} / live #${maximum}`;
  if (seekTimer !== null) clearTimeout(seekTimer);
  seekTimer = setTimeout(() => { seekTimer = null; void store.seek(sequence); }, 40);
});

window.addEventListener("beforeunload", () => { stopReplay(); store.stop(); mapScene?.destroy(); });
void store.start();
void initializeMap();

// ── navigation ─────────────────────────────────────────────────
setupNavigation();
setupChronicleModal();

function setupChronicleModal(): void {
  const modal = document.getElementById("chronicle-modal")!;
  const closeBtn = document.getElementById("cmod-close")!;

  const close = () => {
    modal.hidden = true;
    document.removeEventListener("keydown", onKey);
  };
  const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") close(); };

  closeBtn.addEventListener("click", close);
  modal.addEventListener("click", (e) => { if (e.target === modal) close(); });
}

function setupNavigation(): void {
  document.querySelectorAll<HTMLButtonElement>(".nav-item[data-target]").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".nav-item").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
      const tid = btn.dataset.target;
      if (tid) document.getElementById(tid)?.classList.add("active");
    });
  });

  // pm-tab switching inside Mente Privata
  document.querySelectorAll<HTMLButtonElement>(".pm-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".pm-tab").forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".pm-tab-content").forEach(c => c.classList.remove("active"));
      tab.classList.add("active");
      const tabId = `tab-${tab.dataset.tab}`;
      document.getElementById(tabId)?.classList.add("active");
    });
  });
}

// Open agent Mente Privata from inspector button
document.addEventListener("click", (e) => {
  const target = e.target as HTMLElement;
  if (target.id === "open-profilo-btn" || target.closest("#open-profilo-btn")) {
    if (!selectedAgentId) return;
    // switch to mente privata view
    document.querySelectorAll(".nav-item").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
    document.getElementById("view-mente-privata")?.classList.add("active");
    const snapshot = store.state.viewSnapshot;
    if (snapshot) renderMentePrivata(snapshot, selectedAgentId);
  }
});

// ── WebGL map init ─────────────────────────────────────────────
async function initializeMap(): Promise<void> {
  const mapError = el<HTMLDivElement>("#map-error");
  const slowInit = setTimeout(() => {
    if (mapError) { mapError.hidden = false; mapError.textContent = "WebGL non risponde ancora…"; }
  }, UI_CONSTANTS.SLOW_INIT_WARNING_MS);
  try {
    const scene = await NewlandMapScene.create(stage, (nextSel) => {
      selection = nextSel;
      if (nextSel?.kind === "agent") selectedAgentId = nextSel.id;
      const snap = store.state.viewSnapshot;
      if (snap) { renderInspector(snap, selection); renderInhabitants(snap, selection); }
    });
    mapScene = scene;
    clearTimeout(slowInit);
    if (mapError) mapError.hidden = true;
    const canvas = stage.querySelector<HTMLCanvasElement>("canvas");
    canvas?.addEventListener("webglcontextlost", (ev) => {
      ev.preventDefault();
      if (mapError) { mapError.hidden = false; mapError.textContent = "Contesto WebGL perso."; }
    });
    canvas?.addEventListener("webglcontextrestored", () => {
      if (mapError) mapError.hidden = true;
      const snap = store.state.viewSnapshot;
      if (snap) scene.render(snap.world);
    });
    const snap = store.state.viewSnapshot;
    if (snap) { scene.render(snap.world); lastRenderedSequence = snap.last_sequence; }
  } catch (err) {
    clearTimeout(slowInit);
    if (mapError) {
      mapError.hidden = false;
      mapError.textContent = `WebGL non disponibile: ${err instanceof Error ? err.message : String(err)}`;
    }
  }
}

// ── render: connection ─────────────────────────────────────────
function renderConnection(): void {
  const ind = el<HTMLDivElement>("#connection");
  const lbl = el<HTMLSpanElement>("#connection-label");
  if (ind) ind.dataset.state = store.state.connection;
  if (lbl) lbl.textContent = store.state.error
    ? "non raggiungibile"
    : store.state.viewMode === "paused"
      ? `${store.state.connection} · vista in pausa`
      : store.state.connection;
}

// ── render: clock ──────────────────────────────────────────────
function renderClock(snapshot: ObserverSnapshot): void {
  const d = el<HTMLSpanElement>("#world-date");
  if (d) d.textContent = formatWorldTime(snapshot.world.world_time);
  const td = el<HTMLSpanElement>("#world-tick-display");
  if (td) td.textContent = `GIORNO ${formatDay(snapshot.world.world_time)} · ${formatHour(snapshot.world.world_time)}`;
  const seq = el<HTMLSpanElement>("#event-sequence");
  if (seq) seq.textContent = String(snapshot.last_sequence);
  const cseq = el<HTMLSpanElement>("#canonical-tick-display");
  if (cseq) cseq.textContent = `TICK ${snapshot.world.tick}`;
}

// ── render: time controls ──────────────────────────────────────
function renderTimeControls(snapshot: ObserverSnapshot): void {
  const toggle = el<HTMLButtonElement>("#time-toggle");
  const replay = el<HTMLButtonElement>("#replay-toggle");
  const slider = el<HTMLInputElement>("#time-slider");
  const label = el<HTMLSpanElement>("#time-label");
  if (!slider) return;
  const maximum = Math.max(store.state.liveSequence, snapshot.latest_sequence);
  slider.max = String(maximum);
  if (document.activeElement !== slider && !isInteractingWithSlider) {
    slider.value = String(snapshot.last_sequence);
    if (label) label.textContent = `vista #${snapshot.last_sequence} / live #${maximum}`;
  }
  if (toggle) toggle.textContent = store.state.viewMode === "live" ? "Pausa visiva" : "Torna al presente";
  if (replay) {
    replay.disabled = store.state.viewMode === "live" || snapshot.last_sequence >= maximum;
    replay.textContent = replayActive ? "Ferma replay" : "Riproduci";
  }
}

async function advanceReplay(): Promise<void> {
  if (!replayActive) return;
  const snapshot = store.state.viewSnapshot;
  if (!snapshot || snapshot.last_sequence >= store.state.liveSequence) { stopReplay(); return; }
  await store.seek(snapshot.last_sequence + 1);
  if (!replayActive) return;
  replayTimer = setTimeout(() => void advanceReplay(), UI_CONSTANTS.REPLAY_STEP_MS);
}

function stopReplay(): void {
  replayActive = false;
  if (replayTimer !== null) { clearTimeout(replayTimer); replayTimer = null; }
  const snapshot = store.state.viewSnapshot;
  if (snapshot) renderTimeControls(snapshot);
}

// ── agent status helpers ───────────────────────────────────────
function agentStatusBadge(agent: import('./types').MaterialAgent): string {
  if (!agent.active) return `<span class="status-badge dead">💀 morto</span>`;
  if (agent.energy < UI_CONSTANTS.ENERGY_CRITICAL_THRESHOLD) return `<span class="status-badge crit">⚡ critico</span>`;
  const a = agent.current_action ?? "";
  if (a.includes("rest") || a.includes("sleep")) return `<span class="status-badge sleep">💤 dormiente</span>`;
  if (a.includes("move") || a.includes("travel")) return `<span class="status-badge move">🚶 in cammino</span>`;
  return "";
}

function agentStatusPill(agent: import('./types').MaterialAgent): string {
  if (!agent.active) return `<span class="status-pill dead">● MORTO</span>`;
  if (agent.energy < UI_CONSTANTS.ENERGY_CRITICAL_THRESHOLD) return `<span class="status-pill crit">● CRITICO</span>`;
  const a = agent.current_action ?? "";
  if (a.includes("rest") || a.includes("sleep")) return `<span class="status-pill sleep">● A RIPOSO</span>`;
  if (a.includes("move") || a.includes("travel")) return `<span class="status-pill move">● IN MOVIMENTO</span>`;
  return `<span class="status-pill alive">● ATTIVO</span>`;
}

// ── render: inhabitants (Presenze panel) ───────────────────────
function renderInhabitants(snapshot: ObserverSnapshot, active: Selection | null): void {
  const agents = Object.values(snapshot.world.agents).sort((a, b) => a.name.localeCompare(b.name));
  const countEl = el<HTMLSpanElement>("#inhabitant-count");
  if (countEl) countEl.textContent = String(agents.length);
  const container = el<HTMLDivElement>("#inhabitants");
  if (!container) return;
  container.replaceChildren(...agents.map(agent => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "inhabitant-card";
    btn.dataset.active = String(active?.kind === "agent" && active.id === agent.agent_id);
    btn.dataset.dead = String(!agent.active);
    btn.innerHTML = `
      <span class="inhabitant-mark${!agent.active ? " dead" : ""}">${escapeHtml(initials(agent.name))}</span>
      <span class="inhabitant-info">
        <span class="inhabitant-name-row">
          <strong>${escapeHtml(agent.name)}</strong>
          ${agentStatusBadge(agent)}
        </span>
        <small>${escapeHtml(displayName(agent.location))}</small>
      </span>
      <span class="energy-glyph" title="Energia ${Math.round(agent.energy * 100)}%">
        <i style="--level:${agent.energy}"></i>
      </span>
    `;
    btn.addEventListener("click", () => {
      selection = { kind: "agent", id: agent.agent_id };
      selectedAgentId = agent.agent_id;
      renderInspector(snapshot, selection);
      renderInhabitants(snapshot, selection);
      mapScene?.focus(selection, snapshot.world);
    });
    return btn;
  }));
}

// ── render: inspector (panel on mondo view) ────────────────────
function renderInspector(snapshot: ObserverSnapshot, active: Selection | null): void {
  const inspector = el<HTMLDivElement>("#inspector");
  if (!inspector) return;
  if (!active) {
    inspector.className = "inspector empty-state";
    inspector.innerHTML = "<p>Seleziona una presenza, un luogo o una traccia materiale. L'osservazione non produce effetti nel mondo.</p>";
    return;
  }
  inspector.className = "inspector";
  if (active.kind === "agent") {
    const agent = snapshot.world.agents[active.id];
    const mind = snapshot.minds[active.id];
    if (!agent) {
      inspector.innerHTML = `<p class="empty-state">Questa presenza non esisteva ancora nella sequenza osservata.</p>`;
      return;
    }
    inspector.innerHTML = `
      <div class="inspector-title">
        <span class="inhabitant-mark large${!agent.active ? " dead" : ""}">${escapeHtml(initials(agent.name))}</span>
        <div>
          <h2>${escapeHtml(agent.name)}</h2>
          <p>${escapeHtml(displayName(agent.location))}</p>
        </div>
      </div>
      <div class="inspector-status-row">
        ${agentStatusPill(agent)}
        ${agent.current_action ? `<span class="current-action-label">${escapeHtml(agent.current_action)}</span>` : ""}
      </div>
      <div class="vitals">
        ${meter("energia", agent.energy, false)}
        ${meter("fame", agent.hunger, false)}
        ${meter("sete", agent.thirst, false)}
      </div>
      ${tagSection("Valori", mind?.values ?? [])}
      ${tagSection("Temperamento", mind?.temperament ?? [])}
      ${listSection("Obiettivi", mind?.goals ?? [])}
      ${detailRow("Prossima attenzione", mind?.next_activation_tick == null ? "non fissata" : `tick ${mind.next_activation_tick}`)}
      ${expandableListSection("Memorie", (mind?.memories ?? []).map((m: Memory) => m.summary))}
      ${expandableListSection("Riflessioni", (mind?.reflections ?? []).map((r: Reflection) => r.statement))}
      ${!snapshot.is_live ? `<p class="privacy-note">Le menti storiche non sono ricostruite: mostra solo lo stato materiale.</p>` : ""}
      <button id="open-profilo-btn" class="btn-outline-sm mt-3">Apri profilo agente ↗</button>
    `;
    return;
  }
  if (active.kind === "location") {
    const occupants = Object.values(snapshot.world.agents).filter(a => a.location === active.id);
    const resources = Object.values(snapshot.world.resources).filter(r => r.location === active.id);
    inspector.innerHTML = `
      <h2 class="serif-md mb-2">${escapeHtml(displayName(active.id))}</h2>
      ${detailRow("Collegamenti", String(snapshot.world.locations[active.id]?.length ?? 0))}
      ${listSection("Presenze", occupants.map(a => a.name))}
      ${listSection("Risorse", resources.map(r => `${r.label}: ${r.quantity} ${r.unit}`))}
    `;
    return;
  }
  if (active.kind === "resource") {
    const resource = snapshot.world.resources[active.id];
    if (!resource) return;
    inspector.innerHTML = `
      <h2 class="serif-md mb-2">${escapeHtml(resource.label)}</h2>
      ${detailRow("Luogo", displayName(resource.location))}
      ${detailRow("Quantità", `${resource.quantity} ${resource.unit}`)}
      ${detailRow("Rinnovabile", resource.renewable ? "sì" : "no")}
    `;
    return;
  }
  const node = snapshot.world.resonance_nodes[active.id];
  if (!node) return;
  inspector.innerHTML = `
    <h2 class="serif-md mb-2">${escapeHtml(node.label)}</h2>
    ${detailRow("Luogo", displayName(node.location))}
    ${detailRow("Intensità", `${Math.round(node.intensity * 100)}%`)}
    <p class="privacy-note mt-2">Il significato non appartiene al nodo: nasce nella mente di chi lo percepisce.</p>
  `;
}

// ── render: chronicle ──────────────────────────────────────────
function renderChronicle(throughSequence: number): void {
  const container = el<HTMLDivElement>("#chronicle-entry");
  const entry = store.state.chronicle
    .filter(c => c.through_sequence <= throughSequence)
    .at(-1);
  if (!entry || !container) return;
  container.className = "chronicle-entry";
  container.innerHTML = `
    <h2>${escapeHtml(entry.title)}</h2>
    ${entry.prose.split(/\n\s*\n/).map(p => `<p>${escapeHtml(p)}</p>`).join("")}
    <footer>
      <span>${escapeHtml(entry.model)} · tentativo ${entry.attempts}</span>
      <span>eventi ${entry.from_sequence}–${entry.through_sequence}</span>
    </footer>
  `;
}

// ── render: events (cronaca center + eventi view) ──────────────
function renderEvents(events: readonly EventEnvelope[], throughSequence: number): void {
  const list = el<HTMLUListElement>("#event-list");
  if (!list) return;
  const recent = events.filter(e => e.sequence <= throughSequence).slice(-UI_CONSTANTS.EVENTS_PANEL_LIMIT).reverse();
  list.replaceChildren(...recent.map(e => buildEventLi(e)));
}

function renderEventiFullList(events: readonly EventEnvelope[], throughSequence: number): void {
  const list = el<HTMLUListElement>("#eventi-full-list");
  if (!list) return;
  const filterEl = el<HTMLSelectElement>("#event-filter-visibility");
  const filterVal = filterEl?.value ?? "all";
  const filtered = events
    .filter(e => e.sequence <= throughSequence)
    .filter(e => filterVal === "all" || e.visibility === filterVal)
    .slice().reverse();
  list.replaceChildren(...filtered.map(e => buildEventLi(e)));
}

el<HTMLSelectElement>("#event-filter-visibility")?.addEventListener("change", () => {
  const snap = store.state.viewSnapshot;
  if (snap) renderEventiFullList(store.state.viewEvents, snap.last_sequence);
});

function buildEventLi(event: EventEnvelope): HTMLLIElement {
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
}

// ── render: cronaca stories ────────────────────────────────────
function renderCronacaStories(throughSequence: number): void {
  const container = el<HTMLDivElement>("#cronaca-stories");
  if (!container) return;
  const entries = store.state.chronicle
    .filter(c => c.through_sequence <= throughSequence)
    .slice().reverse().slice(0, UI_CONSTANTS.CHRONICLE_STORIES_LIMIT);
  if (!entries.length) {
    container.innerHTML = `<div class="empty-state">Il Cronista sta elaborando le storie del mondo…</div>`;
    return;
  }
  container.replaceChildren(...entries.map(entry => {
    const preview = entry.prose.replace(/\n/g, " ").trim();
    const card = document.createElement("div");
    card.className = "story-card";
    card.setAttribute("role", "button");
    card.setAttribute("tabindex", "0");
    card.title = "Clicca per leggere il testo completo";
    card.innerHTML = `
      <h3>${escapeHtml(entry.title)}</h3>
      <p>${escapeHtml(preview.slice(0, UI_CONSTANTS.STORY_PREVIEW_CHARS))}…</p>
      <div class="story-meta">
        <span>Giorno ${formatDay(entry.world_time)} · ${formatHour(entry.world_time)}</span>
        <span class="story-read-more">Leggi tutto →</span>
      </div>
    `;
    const openModal = () => openChronicleModal(
      entry.title,
      entry.prose,
      `Giorno ${formatDay(entry.world_time)} · ${formatHour(entry.world_time)} · eventi ${entry.from_sequence}–${entry.through_sequence}`,
      `${entry.model} · tentativo ${entry.attempts}`,
    );
    card.addEventListener("click", openModal);
    card.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") openModal(); });
    return card;
  }));
}

function openChronicleModal(title: string, prose: string, meta: string, footerMeta: string): void {
  const modal = document.getElementById("chronicle-modal");
  const titleEl = document.getElementById("cmod-title");
  const metaEl = document.getElementById("cmod-meta");
  const bodyEl = document.getElementById("cmod-body");
  const footerEl = document.getElementById("cmod-footer-meta");
  if (!modal || !titleEl || !metaEl || !bodyEl || !footerEl) return;

  titleEl.textContent = title;
  metaEl.textContent = meta;
  footerEl.textContent = footerMeta;

  // Render each double-newline-separated paragraph
  bodyEl.innerHTML = prose
    .split(/\n\s*\n/)
    .filter(p => p.trim())
    .map(p => `<p>${escapeHtml(p.trim())}</p>`)
    .join("");

  modal.hidden = false;
  bodyEl.scrollTop = 0;

  // Close on Escape (re-registered each open)
  const onKey = (e: KeyboardEvent) => {
    if (e.key === "Escape") {
      modal.hidden = true;
      document.removeEventListener("keydown", onKey);
    }
  };
  document.addEventListener("keydown", onKey);
}



// ── render: social graph ───────────────────────────────────────
function renderSocialGraph(snapshot: ObserverSnapshot): void {
  const svgEl = el<SVGSVGElement>("#social-graph-svg");
  if (!svgEl) return;
  const container = svgEl.parentElement;
  if (!container) return;
  const W = container.clientWidth || 400;
  const H = container.clientHeight || 300;
  svgEl.setAttribute("viewBox", `0 0 ${W} ${H}`);

  const agents = Object.values(snapshot.world.agents);
  if (!agents.length) { svgEl.innerHTML = ""; return; }

  // Position agents in a circle
  const cx = W / 2, cy = H / 2;
  const r = Math.min(W, H) * 0.35;
  const positions: Record<string, { x: number; y: number }> = {};
  agents.forEach((agent, i) => {
    const angle = (i / agents.length) * Math.PI * 2 - Math.PI / 2;
    positions[agent.agent_id] = { x: cx + Math.cos(angle) * r, y: cy + Math.sin(angle) * r };
  });

  // Build SVG
  let svgContent = "";

  // Draw cooperation edges
  Object.values(snapshot.world.cooperations).forEach(coop => {
    const a = positions[coop.proposer_id];
    const b = positions[coop.target_id];
    if (a && b) {
      const color = coop.status === "accepted" ? "#c5a164" : "#98a887";
      svgContent += `<line x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}" stroke="${color}" stroke-width="1.5" opacity="0.6"/>`;
    }
  });

  // Draw dispute edges (dashed)
  Object.values(snapshot.world.disputes).forEach(disp => {
    const a = positions[disp.opener_id];
    const b = positions[disp.target_id];
    if (a && b) {
      svgContent += `<line x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}" stroke="#c88168" stroke-width="1.5" stroke-dasharray="4 3" opacity="0.7"/>`;
    }
  });

  // Draw agent nodes
  agents.forEach(agent => {
    const p = positions[agent.agent_id]!;
    const initl = initials(agent.name);
    const isSelected = agent.agent_id === selectedAgentId;
    const strokeColor = isSelected ? "#ae96ca" : "#98a887";
    svgContent += `
      <g class="social-node" data-agent="${escapeHtml(agent.agent_id)}" style="cursor:pointer">
        <circle cx="${p.x}" cy="${p.y}" r="26" fill="#161d18" stroke="${strokeColor}" stroke-width="${isSelected ? 2 : 1}"/>
        <circle cx="${p.x}" cy="${p.y}" r="22" fill="#1e2820" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
        <text x="${p.x}" y="${p.y}" text-anchor="middle" dy="0.35em" fill="#eae7da" font-size="11" font-family="Inter,sans-serif" font-weight="500">${escapeHtml(initl)}</text>
        <text x="${p.x}" y="${p.y + 35}" text-anchor="middle" fill="#7a8476" font-size="10" font-family="Inter,sans-serif">${escapeHtml(agent.name.split(" ")[0] ?? agent.name)}</text>
      </g>
    `;
  });

  svgEl.innerHTML = svgContent;

  // Attach click handlers
  svgEl.querySelectorAll<SVGGElement>(".social-node").forEach(node => {
    node.addEventListener("click", () => {
      const agentId = node.dataset.agent ?? "";
      selectedAgentId = agentId;
      selection = { kind: "agent", id: agentId };
      const snap = store.state.viewSnapshot;
      if (snap) { renderMentePrivata(snap, agentId); }
      // Navigate to Mente Privata
      document.querySelectorAll(".nav-item").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
      document.getElementById("view-mente-privata")?.classList.add("active");
    });
  });
}

// ── render: relazioni ──────────────────────────────────────────
function renderRelazioni(snapshot: ObserverSnapshot): void {
  const cooEl = el<HTMLDivElement>("#cooperations-list");
  const disEl = el<HTMLDivElement>("#disputes-list");

  if (cooEl) {
    const coops = Object.values(snapshot.world.cooperations);
    if (coops.length === 0) {
      cooEl.innerHTML = `<p class="muted text-sm">Nessuna cooperazione attiva.</p>`;
    } else {
      cooEl.replaceChildren(...coops.map(coop => {
        const proposer = snapshot.world.agents[coop.proposer_id]?.name ?? coop.proposer_id;
        const target = snapshot.world.agents[coop.target_id]?.name ?? coop.target_id;
        const activity = snapshot.world.activities[coop.activity_id]?.label ?? coop.activity_id;
        const card = document.createElement("div");
        card.className = "rel-card";
        card.innerHTML = `
          <span class="rel-badge rel-badge-coop">${escapeHtml(coop.status.toUpperCase())}</span>
          <h4>${escapeHtml(proposer)} ↔ ${escapeHtml(target)}</h4>
          <p>${escapeHtml(activity)}</p>
          <p class="muted text-sm mt-1">Tick ${coop.created_tick}</p>
        `;
        return card;
      }));
    }
  }

  if (disEl) {
    const disputes = Object.values(snapshot.world.disputes);
    if (disputes.length === 0) {
      disEl.innerHTML = `<p class="muted text-sm">Nessuna disputa aperta.</p>`;
    } else {
      disEl.replaceChildren(...disputes.map(disp => {
        const opener = snapshot.world.agents[disp.opener_id]?.name ?? disp.opener_id;
        const target = snapshot.world.agents[disp.target_id]?.name ?? disp.target_id;
        const card = document.createElement("div");
        card.className = "rel-card";
        card.innerHTML = `
          <span class="rel-badge rel-badge-disp">${escapeHtml(disp.status.toUpperCase())}</span>
          <h4>${escapeHtml(opener)} ← → ${escapeHtml(target)}</h4>
          <p class="muted text-sm mt-1">Aperta al tick ${disp.created_tick}</p>
        `;
        return card;
      }));
    }
  }
}

// ── render: mente privata ──────────────────────────────────────
function renderMentePrivata(snapshot: ObserverSnapshot, agentId: string): void {
  const agent = snapshot.world.agents[agentId];
  const mind = snapshot.minds[agentId] as AgentMindSnapshot | undefined;

  const nameEl = el<HTMLElement>("#pm-agent-name");
  if (nameEl) nameEl.textContent = agent?.name ?? agentId;

  const breadEl = el<HTMLElement>("#pm-breadcrumbs");
  if (breadEl) breadEl.innerHTML = `Mondo / <span>${escapeHtml(agent?.name ?? agentId)}</span> / <strong>Mente privata</strong>`;

  // NEEDS
  const needsEl = el<HTMLDivElement>("#pm-needs");
  if (needsEl && mind?.needs) {
    needsEl.innerHTML = Object.entries(mind.needs).map(([key, val]) => `
      <div class="need-row">
        <span class="need-label">${escapeHtml(key)}</span>
        <div class="need-track">
          <div class="need-fill" style="width:${Math.round(Number(val) * 100)}%"></div>
          <div class="need-thumb" style="left:${Math.round(Number(val) * 100)}%"></div>
        </div>
      </div>
    `).join("") + `<div class="sldr-legend"><span>basso</span><span>alto</span></div>`;
  } else if (needsEl) {
    needsEl.innerHTML = `<p class="muted text-sm">Bisogni non disponibili.</p>`;
  }

  // AFFECT
  const affEl = el<HTMLDivElement>("#pm-affect");
  if (affEl && mind?.affect) {
    const entries = Object.entries(mind.affect);
    affEl.innerHTML = entries.map(([key, val]) => `
      <div class="need-row">
        <span class="need-label">${escapeHtml(key)}</span>
        <div class="need-track">
          <div class="need-fill" style="width:${Math.round(Number(val) * 100)}%"></div>
          <div class="need-thumb" style="left:${Math.round(Number(val) * 100)}%"></div>
        </div>
      </div>
    `).join("") + `<div class="sldr-legend"><span>distante</span><span>molto caldo</span></div>`;
  }

  // VALUES
  const valEl = el<HTMLDivElement>("#pm-values");
  if (valEl) valEl.innerHTML = (mind?.values ?? []).map(v => `<span class="tag">${escapeHtml(v)}</span>`).join("") || `<span class="muted text-sm">—</span>`;

  // TEMPERAMENT
  const tmpEl = el<HTMLDivElement>("#pm-temperament");
  if (tmpEl) tmpEl.innerHTML = (mind?.temperament ?? []).map(t => `<span class="tag">${escapeHtml(t)}</span>`).join("") || `<span class="muted text-sm">—</span>`;

  // NEXT ACTIVATION
  const nextEl = el<HTMLElement>("#pm-next-activation");
  if (nextEl) nextEl.textContent = mind?.next_activation_tick != null ? `tick ${mind.next_activation_tick} · ${escapeHtml(mind.next_activation_reason)}` : "non fissata";

  // BELIEFS
  const belEl = el<HTMLDivElement>("#pm-beliefs-list");
  if (belEl && mind?.beliefs) {
    const beliefEntries = Object.entries(mind.beliefs).slice(0, UI_CONSTANTS.BELIEFS_PANEL_LIMIT);
    if (!beliefEntries.length) {
      belEl.innerHTML = `<p class="muted text-sm">Nessuna credenza attiva.</p>`;
    } else {
      belEl.innerHTML = beliefEntries.map(([key, val]) => {
        const b = val as Record<string, unknown>;
        const content = typeof b === "object" && b !== null ? (String(b["content"] ?? b["statement"] ?? key)) : String(b);
        const confidence = typeof b === "object" && b !== null && typeof b["confidence"] === "number" ? (b["confidence"] as number) : UI_CONSTANTS.BELIEF_FALLBACK_CONFIDENCE;
        return `
          <div class="belief-card">
            <p class="eyebrow violet mb-2">CREDENZA ATTIVA</p>
            <h2 class="belief-h">${escapeHtml(content.slice(0, 80))}</h2>
            <div class="belief-stats mt-3">
              <div>
                <div class="b-stat-label">Fiducia</div>
                <div class="b-stat-val">${Math.round(confidence * 100)}%</div>
                <div class="confidence-bar">
                  <div class="confidence-bar-track"><div class="confidence-bar-fill" style="width:${Math.round(confidence * 100)}%"></div></div>
                </div>
              </div>
            </div>
          </div>
        `;
      }).join("");
    }
  }

  // GOALS
  const goalsEl = el<HTMLUListElement>("#pm-goals");
  if (goalsEl) {
    const goals = mind?.goals ?? [];
    goalsEl.innerHTML = goals.length
      ? goals.map((g, i) => `<li class="goal-item"><span class="goal-num">${i + 1}</span> ${escapeHtml(g)}</li>`).join("")
      : `<li class="muted text-sm">Nessun obiettivo.</li>`;
  }

  // REFLECTIONS
  const refEl = el<HTMLDivElement>("#pm-reflections");
  if (refEl) {
    const refs: Reflection[] = mind?.reflections ?? [];
    refEl.innerHTML = refs.length
      ? refs.slice(0, UI_CONSTANTS.MEMORIES_PANEL_LIMIT).map(r => `<p class="reflection-item">${escapeHtml(r.statement)}</p>`).join("")
      : `<p class="muted text-sm">Nessuna riflessione.</p>`;
  }

  // MEMORIES (compact)
  const memEl = el<HTMLDivElement>("#pm-memories");
  if (memEl) renderMemories(memEl, mind?.memories ?? [], UI_CONSTANTS.MEMORIES_PANEL_LIMIT);

  // MEMORIES (full tab)
  const memFull = el<HTMLDivElement>("#pm-memories-full");
  if (memFull) renderMemories(memFull, mind?.memories ?? [], UI_CONSTANTS.MEMORIES_FULL_LIMIT);

  // BELIEFS full tab
  const belFull = el<HTMLDivElement>("#pm-beliefs-full");
  if (belFull && mind?.beliefs) {
    const all = Object.entries(mind.beliefs);
    belFull.innerHTML = all.map(([key, val]) => {
      const b = val as Record<string, unknown>;
      const content = typeof b === "object" && b !== null ? String(b["content"] ?? b["statement"] ?? key) : String(b);
      const confidence = typeof b === "object" && b !== null && typeof b["confidence"] === "number" ? (b["confidence"] as number) : UI_CONSTANTS.BELIEF_FALLBACK_CONFIDENCE;
      return `<div class="belief-card">
        <p class="eyebrow violet mb-2">CREDENZA</p>
        <h3 class="serif-md mb-2">${escapeHtml(content.slice(0, 120))}</h3>
        <div class="confidence-bar"><div class="confidence-bar-track"><div class="confidence-bar-fill" style="width:${Math.round(confidence * 100)}%"></div></div><span class="ml-2 text-sm violet">${Math.round(confidence * 100)}%</span></div>
      </div>`;
    }).join("") || `<p class="muted text-sm">Nessuna credenza.</p>`;
  }

  // RELATIONS tab
  const relsEl = el<HTMLDivElement>("#pm-relationships-list");
  if (relsEl && mind?.relationships) {
    const rels = Object.entries(mind.relationships);
    if (!rels.length) {
      relsEl.innerHTML = `<p class="muted text-sm">Nessuna relazione.</p>`;
    } else {
      relsEl.innerHTML = rels.map(([otherId, data]) => {
        const otherName = snapshot.world.agents[otherId]?.name ?? otherId;
        const d = data as Record<string, unknown>;
        return `<div class="pm-card">
          <h4 class="card-h">${escapeHtml(otherName)}</h4>
          <pre class="text-xs muted" style="white-space:pre-wrap">${escapeHtml(JSON.stringify(d, null, 2).slice(0, 300))}</pre>
        </div>`;
      }).join("");
    }
  }

  // PIANI tab
  const plansEl = el<HTMLDivElement>("#pm-plans-list");
  if (plansEl && mind?.plans) {
    const plans = Object.entries(mind.plans);
    if (!plans.length) {
      plansEl.innerHTML = `<p class="muted text-sm">Nessun piano attivo.</p>`;
    } else {
      plansEl.innerHTML = plans.map(([planId, data]) => {
        const d = data as Record<string, unknown>;
        const label = String(d["label"] ?? d["goal"] ?? planId);
        const steps = Array.isArray(d["steps"]) ? (d["steps"] as string[]) : [];
        return `<div class="pm-card border-moss">
          <p class="eyebrow moss mb-2">🎯 PIANO</p>
          <h3 class="serif-md mb-3">${escapeHtml(label)}</h3>
          <ul class="goals-list">
            ${steps.map((s, i) => `<li class="goal-item"><span class="goal-num">${i + 1}</span> ${escapeHtml(String(s))}</li>`).join("")}
          </ul>
        </div>`;
      }).join("");
    }
  }

  // COMPARE
  const canonEl = el<HTMLElement>("#pm-canonical-truth");
  const subjEl = el<HTMLElement>("#pm-subjective-truth");
  if (canonEl && agent) {
    canonEl.textContent = `${escapeHtml(agent.name)} si trova a ${escapeHtml(displayName(agent.location))}. Energia ${Math.round(agent.energy * 100)}%, fame ${Math.round(agent.hunger * 100)}%, sete ${Math.round(agent.thirst * 100)}%.`;
  }
  if (subjEl) {
    const topBelief = mind?.beliefs ? Object.values(mind.beliefs)[0] as Record<string, unknown> | undefined : undefined;
    if (topBelief) {
      subjEl.textContent = String(topBelief["content"] ?? topBelief["statement"] ?? "—");
    } else {
      subjEl.textContent = "Nessuna credenza disponibile per questa sequenza.";
    }
  }
}

function renderMemories(container: HTMLElement, memories: Memory[], limit: number): void {
  if (!memories.length) {
    container.innerHTML = `<p class="muted text-sm">Nessun ricordo disponibile.</p>`;
    return;
  }
  container.replaceChildren(...memories.slice(0, limit).map(mem => {
    const card = document.createElement("div");
    card.className = "memory-card";
    const tone = mem.emotional_tone ?? "";
    card.innerHTML = `
      <div class="mem-tick">
        <span class="mem-tick-label">Tick</span>
        <span class="mem-tick-val">${mem.created_tick}</span>
        <span class="text-xs muted">Fiducia<br/>${Math.round(mem.confidence * 100)}%</span>
        <span class="text-xs muted">Accessi<br/>${mem.access_count}</span>
      </div>
      <div class="mem-body">
        <div class="mem-h">${escapeHtml(mem.event_type)}</div>
        <p class="mem-quote">"${escapeHtml(mem.summary.slice(0, 100))}"</p>
        ${mem.location ? `<span class="tag text-xs mt-1">${escapeHtml(displayName(mem.location))}</span>` : ""}
      </div>
      <div class="mem-dots">
        <div class="dot-row">
          <span class="dot-row-label">Salienza</span>
          <div class="dots-row">${dotRow(mem.salience ?? 0.5, false)}</div>
        </div>
        <div class="dot-row">
          <span class="dot-row-label">Tono</span>
          <div class="dots-row">${dotRow(0.5, tone.includes("fear") || tone.includes("sad"))}</div>
        </div>
      </div>
    `;
    return card;
  }));
}

function dotRow(value: number, alt: boolean): string {
  const n = Math.round(value * 5);
  return Array.from({ length: 5 }, (_, i) => {
    const on = i < n;
    return `<span class="d ${on ? (alt ? "on-oc" : "on") : "off"}"></span>`;
  }).join("");
}

// ── helper: inspector subcomponents ───────────────────────────
function meter(label: string, value: number, inverse: boolean): string {
  const display = Math.round(value * 100);
  const normalized = inverse ? 1 - value : value;
  return `<div class="meter"><span>${label}</span><i><b style="--level:${normalized}"></b></i><em>${display}%</em></div>`;
}
function tagSection(label: string, values: string[]): string {
  if (!values.length) return "";
  return `<section class="inspect-section"><h3>${escapeHtml(label)}</h3><div class="tags">${values.map(v => `<span>${escapeHtml(v)}</span>`).join("")}</div></section>`;
}
function listSection(label: string, values: string[]): string {
  if (!values.length) return "";
  return `<section class="inspect-section"><h3>${escapeHtml(label)}</h3><ul>${values.map(v => `<li>${escapeHtml(v)}</li>`).join("")}</ul></section>`;
}
function detailRow(label: string, value: string): string {
  return `<div class="detail-row"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;
}
function expandableListSection(title: string, items: string[]): string {
  if (!items.length) return detailRow(title, "0");
  return `<details class="inspector-details"><summary class="detail-row"><span>${title}</span><span class="count-badge">${items.length} ▾</span></summary><ul class="expandable-list">${items.map(i => `<li>${escapeHtml(i)}</li>`).join("")}</ul></details>`;
}

// ── utility ────────────────────────────────────────────────────
function el<T extends Element>(sel: string): T | null {
  return document.querySelector<T>(sel);
}

// Keep backward compat alias used in a few places
function requiredElement<T extends Element>(sel: string): T {
  const e = el<T>(sel);
  if (!e) { console.warn(`Missing ${sel}`); return document.createElement("div") as unknown as T; }
  return e;
}
void requiredElement; // suppress unused warning

function splitEventType(v: string): string {
  return v.replace(/([a-z])([A-Z])/g, "$1 $2");
}
function initials(name: string): string {
  return name.split(/\s+/).slice(0, 2).map(p => p[0] ?? "").join("").toUpperCase();
}
function escapeHtml(value: string): string {
  return value.replace(/[&<>'"\n]/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;", "\n": " "
  })[c] ?? c);
}
function formatWorldTime(v: string): string {
  const m = v.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/);
  return m ? `Giorno ${Number(m[3])} · ${m[4]}:${m[5]}` : v;
}
function formatDay(v: string): string {
  const m = v.match(/^(\d{4})-(\d{2})-(\d{2})/);
  return m ? String(Number(m[3])) : "—";
}
function formatHour(v: string): string {
  const m = v.match(/T(\d{2}):(\d{2})/);
  return m ? `${m[1]}:${m[2]}` : "—";
}

// also add a small "btn-outline-sm" style inline to not break TS
document.head.insertAdjacentHTML("beforeend", `<style>.btn-outline-sm{background:transparent;border:1px solid rgba(255,255,255,0.15);color:var(--muted);padding:.4rem .9rem;border-radius:6px;font-size:.78rem;cursor:pointer;transition:.15s;}.btn-outline-sm:hover{color:var(--paper);}</style>`);
