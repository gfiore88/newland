import {
  Application,
  Container,
  Graphics,
  Text,
  type FederatedPointerEvent,
} from "pixi.js";

import { displayName, layoutLocations, type MapPoint } from "./layout";
import { BiomeGenerator } from "./biome-generator";
import type { ObserverWorld } from "./types";
import { UI_CONSTANTS } from "./constants";

export type Selection =
  | { kind: "agent"; id: string }
  | { kind: "location"; id: string }
  | { kind: "resource"; id: string }
  | { kind: "resonance"; id: string };

type SelectHandler = (selection: Selection) => void;

// Agent animation state for lerp movement
interface AnimState {
  prev: MapPoint;
  curr: MapPoint;
  t: number;          // 0 → 1 progress
  duration: number;   // ms
}

const COLORS = {
  ink:          0x161d18,
  inkSoft:      0x1e2820,
  moss:         0x718064,
  mossBright:   0xa5b28d,
  parchment:    0xeee8d6,
  water:        0x708f91,
  resonance:    0xb49ad7,
  resource:     0xc9a86a,
  path:         0x4a5245,
  locationDot:  0x8ea07c,
  agentDead:    0x3a2425,
  agentSleep:   0x4a5045,
  agentCrit:    0xc88168,
};

export class NewlandMapScene {
  private readonly app         = new Application();
  private readonly viewport    = new Container();
  private readonly terrainLayer    = new Container();
  private readonly pathLayer       = new Container();
  private readonly phenomenonLayer = new Container();
  private readonly entityLayer     = new Container();
  private readonly animLayer       = new Container(); // for lerp-animated agents
  private readonly labelLayer      = new Container();

  private readonly resonanceMarks: Graphics[] = [];
  private readonly restMarks: Text[] = [];

  // Movement animation registry: agentId → AnimState
  private readonly movingAgents = new Map<string, AnimState>();
  // Previous known positions: agentId → world pixel
  private readonly prevAgentPositions = new Map<string, MapPoint>();
  // Agent render containers for anim layer: agentId → Container
  private readonly agentContainers = new Map<string, Container>();

  private dragPointer: number | null = null;
  private dragOrigin    = { x: 0, y: 0 };
  private viewportOrigin = { x: 0, y: 0 };

  private constructor(
    private readonly host: HTMLElement,
    private readonly onSelect: SelectHandler,
  ) {}

  static async create(host: HTMLElement, onSelect: SelectHandler): Promise<NewlandMapScene> {
    const scene = new NewlandMapScene(host, onSelect);
    await scene.initialize();
    return scene;
  }

  render(world: ObserverWorld): void {
    this.clearStaticLayers();
    const positions = layoutLocations(world.locations);
    this.drawTerritory();
    this.drawPaths(world, positions);
    this.drawLocations(world, positions);
    this.drawResources(world, positions);
    this.drawResonance(world, positions);
    this.drawAgents(world, positions);
  }

  focus(selection: Selection, world: ObserverWorld): void {
    const positions = layoutLocations(world.locations);
    let locationId = selection.id;
    if (selection.kind === "agent")    locationId = world.agents[selection.id]?.location ?? locationId;
    if (selection.kind === "resource") locationId = world.resources[selection.id]?.location ?? locationId;
    if (selection.kind === "resonance") locationId = world.resonance_nodes[selection.id]?.location ?? locationId;
    const point = positions.get(locationId);
    if (!point) return;
    this.viewport.position.set(
      this.app.renderer.width  / 2 - point.x * this.viewport.scale.x,
      this.app.renderer.height / 2 - point.y * this.viewport.scale.y,
    );
  }

  destroy(): void {
    this.app.destroy(true, { children: true });
  }

  // ── initialize ────────────────────────────────────────────────
  private async initialize(): Promise<void> {
    try {
      await this.app.init({
        resizeTo: this.host,
        preference:          "webgl",
        preferWebGLVersion:  1,
        antialias:           false,
        autoDensity:         true,
        resolution:          Math.min(window.devicePixelRatio, 1.5),
        backgroundAlpha:     0,
        hello:               false,
      });
    } catch (e) {
      console.error("PixiJS WebGL init failed:", e);
      throw e;
    }
    this.app.ticker.maxFPS = 30;
    this.app.canvas.className = "world-canvas";
    this.app.canvas.setAttribute("aria-label", "Mappa WebGL del territorio di Newland");
    this.host.appendChild(this.app.canvas);

    this.viewport.addChild(
      this.terrainLayer,
      this.pathLayer,
      this.phenomenonLayer,
      this.entityLayer,
      this.animLayer,
      this.labelLayer,
    );
    this.viewport.position.set(this.app.renderer.width / 2, this.app.renderer.height / 2);
    this.app.stage.addChild(this.viewport);
    this.installCameraControls();

    // Ticker: resonance pulse + rest bob + movement lerp
    this.app.ticker.add((ticker) => {
      const now   = performance.now();
      const phase = now / 900;

      // Resonance pulsation
      for (const [index, mark] of this.resonanceMarks.entries()) {
        mark.alpha   = 0.28 + Math.sin(phase + index * 0.7) * 0.12;
        mark.scale.set(1 + Math.sin(phase + index) * 0.025);
      }
      // Rest Zzz bob
      for (const [index, mark] of this.restMarks.entries()) {
        mark.y     = -22 + Math.sin(phase * 2 + index) * 3;
        mark.alpha = 0.6 + Math.sin(phase * 2 + index) * 0.4;
      }

      // Movement lerp animation
      const dt = ticker.deltaMS;
      for (const [agentId, anim] of this.movingAgents) {
        anim.t += dt / anim.duration;
        if (anim.t >= 1) {
          anim.t = 1;
          this.movingAgents.delete(agentId);
        }
        const container = this.agentContainers.get(agentId);
        if (container) {
          container.x = lerp(anim.prev.x, anim.curr.x, easeOut(anim.t));
          container.y = lerp(anim.prev.y, anim.curr.y, easeOut(anim.t));
          this.updateGhostTrail(container, anim);
        }
      }
      void ticker;
    });
  }

  // ── camera ────────────────────────────────────────────────────
  private installCameraControls(): void {
    const canvas = this.app.canvas;
    canvas.addEventListener("pointerdown", (event) => {
      this.dragPointer  = event.pointerId;
      this.dragOrigin   = { x: event.clientX, y: event.clientY };
      this.viewportOrigin = { x: this.viewport.x, y: this.viewport.y };
      canvas.setPointerCapture(event.pointerId);
      canvas.classList.add("is-dragging");
    });
    canvas.addEventListener("pointermove", (event) => {
      if (event.pointerId !== this.dragPointer) return;
      this.viewport.position.set(
        this.viewportOrigin.x + event.clientX - this.dragOrigin.x,
        this.viewportOrigin.y + event.clientY - this.dragOrigin.y,
      );
    });
    const endDrag = (event: PointerEvent) => {
      if (event.pointerId !== this.dragPointer) return;
      this.dragPointer = null;
      canvas.classList.remove("is-dragging");
    };
    canvas.addEventListener("pointerup",     endDrag);
    canvas.addEventListener("pointercancel", endDrag);
    canvas.addEventListener("wheel", (event) => {
      event.preventDefault();
      const bounds    = canvas.getBoundingClientRect();
      const cursor    = { x: event.clientX - bounds.left, y: event.clientY - bounds.top };
      const local     = this.viewport.toLocal(cursor);
      const nextScale = clamp(this.viewport.scale.x * Math.exp(-event.deltaY * 0.001), UI_CONSTANTS.ZOOM_MIN, UI_CONSTANTS.ZOOM_MAX);
      this.viewport.scale.set(nextScale);
      this.viewport.position.set(
        cursor.x - local.x * nextScale,
        cursor.y - local.y * nextScale,
      );
    }, { passive: false });
  }

  // ── terrain ───────────────────────────────────────────────────
  private drawTerritory(): void {
    const outer = new Graphics()
      .ellipse(0, 0, 510, 370)
      .fill({ color: 0x1b251e, alpha: 0.94 })
      .stroke({ color: 0x7e8b75, alpha: 0.22, width: 1.5 });
    const inner = new Graphics()
      .ellipse(0, 0, 440, 310)
      .stroke({ color: 0xa3ae93, alpha: 0.08, width: 1 });
    this.terrainLayer.addChild(outer, inner);
  }

  // ── paths ─────────────────────────────────────────────────────
  private drawPaths(world: ObserverWorld, positions: Map<string, MapPoint>): void {
    const drawn = new Set<string>();
    for (const [from, neighbors] of Object.entries(world.locations)) {
      for (const to of neighbors) {
        const key = [from, to].sort().join("::");
        if (drawn.has(key)) continue;
        drawn.add(key);
        const start = positions.get(from);
        const end   = positions.get(to);
        if (!start || !end) continue;
        // Dashed path: multiple small segments
        const steps  = 18;
        const g      = new Graphics();
        for (let i = 0; i < steps; i++) {
          if (i % 2 === 0) {
            const t0 = i / steps;
            const t1 = (i + 0.6) / steps;
            g.moveTo(lerp(start.x, end.x, t0), lerp(start.y, end.y, t0))
              .lineTo(lerp(start.x, end.x, t1), lerp(start.y, end.y, t1));
          }
        }
        g.stroke({ color: COLORS.path, alpha: 0.45, width: 1.5 });
        this.pathLayer.addChild(g);
      }
    }
  }

  // ── locations: DIAMOND marker ─────────────────────────────────
  private drawLocations(world: ObserverWorld, positions: Map<string, MapPoint>): void {
    for (const location of Object.keys(world.locations).sort()) {
      const point = positions.get(location);
      if (!point) continue;
      const group = new Container({ x: point.x, y: point.y });

      // Biome terrain
      const biome = BiomeGenerator.generate(location, 94, 48);
      biome.y = 8;
      biome.eventMode = "static";
      biome.cursor = "pointer";
      biome.on("pointertap", (event: FederatedPointerEvent) => {
        event.stopPropagation();
        this.onSelect({ kind: "location", id: location });
      });

      // ── DIAMOND marker (distinguishes location from agent) ──
      // Draw a square rotated 45° = diamond shape
      const size = 10;
      const diamond = new Graphics();
      // polygon: top, right, bottom, left
      diamond.poly([
        0,    -size,  // top
        size,  0,     // right
        0,     size,  // bottom
        -size, 0,     // left
      ])
        .fill({ color: COLORS.locationDot, alpha: 0.95 })
        .stroke({ color: 0xffffff, alpha: 0.18, width: 1 });
      diamond.y = -2;
      diamond.eventMode = "static";
      diamond.cursor = "pointer";
      diamond.on("pointertap", (event: FederatedPointerEvent) => {
        event.stopPropagation();
        this.onSelect({ kind: "location", id: location });
      });

      group.addChild(biome, diamond);
      this.entityLayer.addChild(group);

      const label = new Text({
        text: displayName(location),
        style: {
          fill:        COLORS.parchment,
          fontFamily:  "Georgia, serif",
          fontSize:    17,
          letterSpacing: 0.5,
        },
      });
      label.anchor.set(0.5);
      label.position.set(point.x, point.y + 72);
      this.labelLayer.addChild(label);
    }
  }

  // ── agents: circle with state visuals ─────────────────────────
  private drawAgents(world: ObserverWorld, positions: Map<string, MapPoint>): void {
    // Clear agent containers from previous render
    for (const [, c] of this.agentContainers) c.destroy({ children: true });
    this.agentContainers.clear();

    const byLocation = new Map<string, string[]>();
    for (const agent of Object.values(world.agents)) {
      const list = byLocation.get(agent.location) ?? [];
      list.push(agent.agent_id);
      byLocation.set(agent.location, list);
    }

    for (const [location, agentIds] of byLocation) {
      const origin = positions.get(location);
      if (!origin) continue;

      agentIds.sort().forEach((agentId, index) => {
        const agent = world.agents[agentId];
        if (!agent) return;

        // Determine state
        const isDead    = !agent.active;
        const isCrit    = !isDead && agent.energy < 0.10;
        const isSleeping = !isDead && !isCrit &&
          (agent.current_action === "rest" || agent.current_action?.includes("sleep") === true);
        const isMoving   = !isDead && !isSleeping &&
          (agent.current_action?.includes("move") === true || agent.current_action?.includes("travel") === true);

        // Spread multiple agents around the location center
        const angle = (index / Math.max(1, agentIds.length)) * Math.PI * 2 - Math.PI / 2;
        const spread = agentIds.length > 1 ? UI_CONSTANTS.SPREAD_PIXELS : 0;
        const targetX = origin.x + Math.cos(angle) * spread;
        const targetY = origin.y + Math.sin(angle) * spread - 8;

        // Check if this agent was somewhere else last frame
        const prev = this.prevAgentPositions.get(agentId);
        const curr: MapPoint = { x: targetX, y: targetY };

        // Register anim if position changed meaningfully
        if (prev && (Math.abs(prev.x - curr.x) > 5 || Math.abs(prev.y - curr.y) > 5)) {
          this.movingAgents.set(agentId, { prev, curr, t: 0, duration: UI_CONSTANTS.MOVE_ANIM_MS });
        }
        this.prevAgentPositions.set(agentId, curr);

        // Build container
        const group = new Container();
        // Start at current pos (anim will override x/y if lerping)
        const existingAnim = this.movingAgents.get(agentId);
        if (existingAnim) {
          group.x = lerp(existingAnim.prev.x, existingAnim.curr.x, easeOut(existingAnim.t));
          group.y = lerp(existingAnim.prev.y, existingAnim.curr.y, easeOut(existingAnim.t));
        } else {
          group.x = targetX;
          group.y = targetY;
        }

        // ── Ghost trail placeholder container (children added by updateGhostTrail) ──
        const ghostContainer = new Container();
        ghostContainer.name = "ghost";
        group.addChild(ghostContainer);

        // ── Shadow ──
        const shadow = new Graphics()
          .ellipse(0, 14, isDead ? 5 : 8, isDead ? 2 : 3)
          .fill({ color: COLORS.ink, alpha: isDead ? 0.25 : 0.5 });
        group.addChild(shadow);

        // ── Outer glow ring (not for dead) ──
        if (!isDead) {
          const glowColor = isCrit ? COLORS.agentCrit : isSleeping ? COLORS.agentSleep : COLORS.mossBright;
          const glow = new Graphics()
            .circle(0, 0, 12)
            .fill({ color: glowColor, alpha: isCrit ? 0.25 : 0.12 });
          group.addChild(glow);
          // Inner ring
          const ring = new Graphics()
            .circle(0, 0, 8.5)
            .stroke({ color: glowColor, alpha: 0.4, width: 1 });
          group.addChild(ring);
        }

        // ── Body circle ──
        const bodyColor  = isDead ? COLORS.agentDead : isCrit ? COLORS.agentCrit : isSleeping ? COLORS.agentSleep : COLORS.parchment;
        const bodyAlpha  = isDead ? 0.5 : 1.0;
        const bodyRadius = isDead ? 5 : 6;
        const body = new Graphics()
          .circle(0, 0, bodyRadius)
          .fill({ color: bodyColor, alpha: bodyAlpha })
          .stroke({ color: COLORS.ink, width: 1.5 });
        body.eventMode = "static";
        body.cursor    = "pointer";
        body.on("pointertap", (event: FederatedPointerEvent) => {
          event.stopPropagation();
          this.onSelect({ kind: "agent", id: agentId });
        });
        group.addChild(body);

        // ── Dead: X cross ──
        if (isDead) {
          const cross = new Graphics()
            .moveTo(-3, -3).lineTo(3, 3)
            .moveTo(3, -3).lineTo(-3, 3)
            .stroke({ color: 0xcc4444, alpha: 0.8, width: 1.5 });
          group.addChild(cross);
        }

        // ── Sleep: Zzz ──
        if (isSleeping) {
          const zzz = new Text({
            text: "💤",
            style: { fontFamily: "Inter, sans-serif", fontSize: 12 },
          });
          zzz.anchor.set(0.5, 1);
          zzz.position.set(0, -10);
          group.addChild(zzz);
          this.restMarks.push(zzz);
        }

        // ── Critical: exclamation ──
        if (isCrit && !isDead) {
          const warn = new Text({
            text: "⚡",
            style: { fontFamily: "Inter, sans-serif", fontSize: 10 },
          });
          warn.anchor.set(0.5, 1);
          warn.position.set(8, -6);
          group.addChild(warn);
        }

        // ── Moving indicator ──
        if (isMoving) {
          const walkDot = new Graphics()
            .circle(0, 0, 3)
            .fill({ color: COLORS.mossBright, alpha: 0.7 });
          walkDot.x = 9;
          walkDot.y = -9;
          group.addChild(walkDot);
        }

        // ── Name label ──
        const name = new Text({
          text: agent.name,
          style: {
            fill:       isDead ? 0x885555 : COLORS.parchment,
            fontFamily: "Inter, sans-serif",
            fontSize:   11,
            fontWeight: "600",
          },
        });
        name.anchor.set(0.5, 0);
        name.position.set(0, 14);
        group.addChild(name);

        this.animLayer.addChild(group);
        this.agentContainers.set(agentId, group);

        // Draw initial ghost trail if already in anim
        if (existingAnim) this.updateGhostTrail(group, existingAnim);
      });
    }
  }

  // ── Ghost trail: 3 fading circles behind the agent ────────────
  private updateGhostTrail(container: Container, anim: AnimState): void {
    const ghostContainer = container.getChildByName("ghost") as Container | null;
    if (!ghostContainer) return;
    // Clear old ghosts
    for (const child of ghostContainer.removeChildren()) child.destroy({ children: true });
    if (anim.t >= 1) return;
    // Draw 3 ghost dots at previous positions
    const steps = [0.35, 0.18, 0.08];
    for (const [i, alpha] of steps.entries()) {
      const gt = 1 - (i + 1) * 0.25; // interpolation back along prev→curr
      const gx = lerp(anim.curr.x, anim.prev.x, gt) - container.x;
      const gy = lerp(anim.curr.y, anim.prev.y, gt) - container.y;
      const ghost = new Graphics()
        .circle(gx, gy, 4 - i)
        .fill({ color: COLORS.mossBright, alpha });
      ghostContainer.addChild(ghost);
    }
  }

  // ── resources ─────────────────────────────────────────────────
  private drawResources(world: ObserverWorld, positions: Map<string, MapPoint>): void {
    const resources = Object.values(world.resources).sort((a, b) =>
      a.resource_id.localeCompare(b.resource_id),
    );
    resources.forEach((resource, index) => {
      const origin = positions.get(resource.location);
      if (!origin) return;
      const x = origin.x - 62 + (index % 3) * 18;
      const y = origin.y + 24 + Math.floor(index / 3) * 16;
      const mark = new Graphics()
        .rect(x - 5, y - 5, 10, 10)
        .fill({ color: resource.quantity > 0 ? COLORS.resource : COLORS.path, alpha: 0.9 });
      mark.eventMode = "static";
      mark.cursor    = "pointer";
      mark.on("pointertap", (event: FederatedPointerEvent) => {
        event.stopPropagation();
        this.onSelect({ kind: "resource", id: resource.resource_id });
      });
      this.entityLayer.addChild(mark);
    });
  }

  // ── resonance ─────────────────────────────────────────────────
  private drawResonance(world: ObserverWorld, positions: Map<string, MapPoint>): void {
    for (const node of Object.values(world.resonance_nodes)) {
      const origin = positions.get(node.location);
      if (!origin) continue;
      const radius = 74 + node.intensity * 34;
      const pulse  = new Graphics()
        .circle(origin.x, origin.y, radius)
        .stroke({ color: COLORS.resonance, alpha: 0.65, width: 2 });
      pulse.pivot.set(origin.x, origin.y);
      pulse.position.set(origin.x, origin.y);
      pulse.eventMode = "static";
      pulse.cursor    = "pointer";
      pulse.on("pointertap", (event: FederatedPointerEvent) => {
        event.stopPropagation();
        this.onSelect({ kind: "resonance", id: node.node_id });
      });
      this.resonanceMarks.push(pulse);
      this.phenomenonLayer.addChild(pulse);
    }
  }

  // ── clear (per render) ────────────────────────────────────────
  private clearStaticLayers(): void {
    this.resonanceMarks.length = 0;
    this.restMarks.length      = 0;
    // Don't clear agentContainers here — done in drawAgents
    for (const layer of [
      this.terrainLayer,
      this.pathLayer,
      this.phenomenonLayer,
      this.entityLayer,
      this.labelLayer,
    ]) {
      for (const child of layer.removeChildren()) child.destroy({ children: true });
    }
    // Also clear animLayer (agent containers rebuilt in drawAgents)
    for (const child of this.animLayer.removeChildren()) {
      if (!this.agentContainers.has(child.label ?? "")) {
        child.destroy({ children: true });
      }
    }
  }
}

// ── math helpers ──────────────────────────────────────────────
function clamp(value: number, minimum: number, maximum: number): number {
  return Math.min(maximum, Math.max(minimum, value));
}
function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}
function easeOut(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}
