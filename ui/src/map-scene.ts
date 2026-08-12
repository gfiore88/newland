import {
  Application,
  Batcher,
  Container,
  Graphics,
  Text,
  type FederatedPointerEvent,
} from "pixi.js";

import { displayName, layoutLocations, type MapPoint } from "./layout";
import type { ObserverWorld } from "./types";

// Pixi otherwise opens and intentionally loses a temporary WebGL context to
// probe this limit. Newland's primitive-only scene needs far fewer than eight.
Batcher.defaultOptions.maxTextures = 8;

export type Selection =
  | { kind: "agent"; id: string }
  | { kind: "location"; id: string }
  | { kind: "resource"; id: string }
  | { kind: "resonance"; id: string };

type SelectHandler = (selection: Selection) => void;

const COLORS = {
  ink: 0x161d18,
  moss: 0x718064,
  mossBright: 0xa5b28d,
  parchment: 0xeee8d6,
  water: 0x708f91,
  resonance: 0xb49ad7,
  resource: 0xc9a86a,
  path: 0x6b725f,
};

export class NewlandMapScene {
  private readonly app = new Application();
  private readonly viewport = new Container();
  private readonly terrainLayer = new Container();
  private readonly pathLayer = new Container();
  private readonly phenomenonLayer = new Container();
  private readonly entityLayer = new Container();
  private readonly labelLayer = new Container();
  private readonly resonanceMarks: Graphics[] = [];
  private dragPointer: number | null = null;
  private dragOrigin = { x: 0, y: 0 };
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
    this.clearLayers();
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
    if (selection.kind === "agent") locationId = world.agents[selection.id]?.location ?? locationId;
    if (selection.kind === "resource") {
      locationId = world.resources[selection.id]?.location ?? locationId;
    }
    if (selection.kind === "resonance") {
      locationId = world.resonance_nodes[selection.id]?.location ?? locationId;
    }
    const point = positions.get(locationId);
    if (!point) return;
    this.viewport.position.set(
      this.app.renderer.width / 2 - point.x * this.viewport.scale.x,
      this.app.renderer.height / 2 - point.y * this.viewport.scale.y,
    );
  }

  destroy(): void {
    this.app.destroy(true, { children: true });
  }

  private async initialize(): Promise<void> {
    await this.app.init({
      resizeTo: this.host,
      preference: "webgl",
      preferWebGLVersion: 1,
      antialias: false,
      powerPreference: "low-power",
      autoDensity: true,
      resolution: Math.min(window.devicePixelRatio, 1.5),
      backgroundAlpha: 0,
    });
    this.app.ticker.maxFPS = 30;
    this.app.canvas.className = "world-canvas";
    this.app.canvas.setAttribute("aria-label", "Mappa WebGL del territorio di Newland");
    this.host.appendChild(this.app.canvas);
    this.viewport.addChild(
      this.terrainLayer,
      this.pathLayer,
      this.phenomenonLayer,
      this.entityLayer,
      this.labelLayer,
    );
    this.viewport.position.set(this.app.renderer.width / 2, this.app.renderer.height / 2);
    this.app.stage.addChild(this.viewport);
    this.installCameraControls();
    this.app.ticker.add((ticker) => {
      const phase = performance.now() / 900;
      for (const [index, mark] of this.resonanceMarks.entries()) {
        mark.alpha = 0.28 + Math.sin(phase + index * 0.7) * 0.12;
        mark.scale.set(1 + Math.sin(phase + index) * 0.025);
      }
      void ticker;
    });
  }

  private installCameraControls(): void {
    const canvas = this.app.canvas;
    canvas.addEventListener("pointerdown", (event) => {
      this.dragPointer = event.pointerId;
      this.dragOrigin = { x: event.clientX, y: event.clientY };
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
    canvas.addEventListener("pointerup", endDrag);
    canvas.addEventListener("pointercancel", endDrag);
    canvas.addEventListener(
      "wheel",
      (event) => {
        event.preventDefault();
        const bounds = canvas.getBoundingClientRect();
        const cursor = { x: event.clientX - bounds.left, y: event.clientY - bounds.top };
        const local = this.viewport.toLocal(cursor);
        const nextScale = clamp(
          this.viewport.scale.x * Math.exp(-event.deltaY * 0.001),
          0.55,
          2.2,
        );
        this.viewport.scale.set(nextScale);
        this.viewport.position.set(
          cursor.x - local.x * nextScale,
          cursor.y - local.y * nextScale,
        );
      },
      { passive: false },
    );
  }

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

  private drawPaths(world: ObserverWorld, positions: Map<string, MapPoint>): void {
    const drawn = new Set<string>();
    for (const [from, neighbors] of Object.entries(world.locations)) {
      for (const to of neighbors) {
        const key = [from, to].sort().join("::");
        if (drawn.has(key)) continue;
        drawn.add(key);
        const start = positions.get(from);
        const end = positions.get(to);
        if (!start || !end) continue;
        this.pathLayer.addChild(
          new Graphics()
            .moveTo(start.x, start.y)
            .lineTo(end.x, end.y)
            .stroke({ color: COLORS.path, alpha: 0.5, width: 3 }),
        );
      }
    }
  }

  private drawLocations(world: ObserverWorld, positions: Map<string, MapPoint>): void {
    for (const location of Object.keys(world.locations).sort()) {
      const point = positions.get(location);
      if (!point) continue;
      const group = new Container({ x: point.x, y: point.y });
      const halo = new Graphics()
        .ellipse(0, 8, 94, 48)
        .fill({ color: 0x293329, alpha: 0.92 })
        .stroke({ color: COLORS.moss, alpha: 0.65, width: 1.5 });
      halo.eventMode = "static";
      halo.cursor = "pointer";
      halo.on("pointertap", (event: FederatedPointerEvent) => {
        event.stopPropagation();
        this.onSelect({ kind: "location", id: location });
      });
      const marker = new Graphics()
        .circle(0, -2, 8)
        .fill({ color: COLORS.mossBright, alpha: 0.9 });
      group.addChild(halo, marker);
      this.entityLayer.addChild(group);

      const label = new Text({
        text: displayName(location),
        style: {
          fill: COLORS.parchment,
          fontFamily: "Georgia, serif",
          fontSize: 17,
          letterSpacing: 0.5,
        },
      });
      label.anchor.set(0.5);
      label.position.set(point.x, point.y + 72);
      this.labelLayer.addChild(label);
    }
  }

  private drawAgents(world: ObserverWorld, positions: Map<string, MapPoint>): void {
    const byLocation = new Map<string, string[]>();
    for (const agent of Object.values(world.agents)) {
      const occupants = byLocation.get(agent.location) ?? [];
      occupants.push(agent.agent_id);
      byLocation.set(agent.location, occupants);
    }
    for (const [location, agentIds] of byLocation) {
      const origin = positions.get(location);
      if (!origin) continue;
      agentIds.sort().forEach((agentId, index) => {
        const agent = world.agents[agentId];
        if (!agent) return;
        const angle = (index / Math.max(1, agentIds.length)) * Math.PI * 2 - Math.PI / 2;
        const x = origin.x + Math.cos(angle) * 48;
        const y = origin.y + Math.sin(angle) * 26 - 8;
        const group = new Container({ x, y });
        const shadow = new Graphics().ellipse(0, 12, 12, 5).fill({
          color: COLORS.ink,
          alpha: 0.55,
        });
        const body = new Graphics()
          .circle(0, 0, 10)
          .fill({ color: agent.active ? COLORS.parchment : COLORS.path })
          .stroke({ color: COLORS.ink, width: 2 });
        body.eventMode = "static";
        body.cursor = "pointer";
        body.on("pointertap", (event: FederatedPointerEvent) => {
          event.stopPropagation();
          this.onSelect({ kind: "agent", id: agentId });
        });
        const name = new Text({
          text: agent.name,
          style: {
            fill: COLORS.parchment,
            fontFamily: "Inter, sans-serif",
            fontSize: 11,
            fontWeight: "600",
          },
        });
        name.anchor.set(0.5, 0);
        name.position.set(0, 17);
        group.addChild(shadow, body, name);
        this.entityLayer.addChild(group);
      });
    }
  }

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
      mark.cursor = "pointer";
      mark.on("pointertap", (event: FederatedPointerEvent) => {
        event.stopPropagation();
        this.onSelect({ kind: "resource", id: resource.resource_id });
      });
      this.entityLayer.addChild(mark);
    });
  }

  private drawResonance(world: ObserverWorld, positions: Map<string, MapPoint>): void {
    for (const node of Object.values(world.resonance_nodes)) {
      const origin = positions.get(node.location);
      if (!origin) continue;
      const radius = 74 + node.intensity * 34;
      const pulse = new Graphics()
        .circle(origin.x, origin.y, radius)
        .stroke({ color: COLORS.resonance, alpha: 0.65, width: 2 });
      pulse.pivot.set(origin.x, origin.y);
      pulse.position.set(origin.x, origin.y);
      pulse.eventMode = "static";
      pulse.cursor = "pointer";
      pulse.on("pointertap", (event: FederatedPointerEvent) => {
        event.stopPropagation();
        this.onSelect({ kind: "resonance", id: node.node_id });
      });
      this.resonanceMarks.push(pulse);
      this.phenomenonLayer.addChild(pulse);
    }
  }

  private clearLayers(): void {
    this.resonanceMarks.length = 0;
    for (const layer of [
      this.terrainLayer,
      this.pathLayer,
      this.phenomenonLayer,
      this.entityLayer,
      this.labelLayer,
    ]) {
      for (const child of layer.removeChildren()) child.destroy({ children: true });
    }
  }
}

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.min(maximum, Math.max(minimum, value));
}
