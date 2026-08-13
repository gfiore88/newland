import { Container, Graphics } from "pixi.js";

const BIOME_COLORS = {
  forestBase: 0x1a261f,
  forestTree: 0x131a15,
  forestHighlight: 0x243329,
  fieldBase: 0x1f241a,
  fieldTuft: 0x2b3323,
  waterBase: 0x182429,
  waterRipple: 0x22353b,
  settlementBase: 0x242220,
  settlementStructure: 0x332e2b,
};

export class BiomeGenerator {
  /**
   * Generates a procedural biome based on the semantic name of the location.
   */
  public static generate(name: string, radiusX: number, radiusY: number): Container {
    const container = new Container();
    const type = this.inferBiomeType(name);
    
    // Draw base halo shape
    const base = new Graphics();
    
    // Define bounds for random generation
    const bounds = { rx: radiusX, ry: radiusY };

    switch (type) {
      case "forest":
        this.drawForest(base, bounds);
        break;
      case "field":
        this.drawField(base, bounds);
        break;
      case "water":
        this.drawWater(base, bounds);
        break;
      case "settlement":
        this.drawSettlement(base, bounds);
        break;
      default:
        this.drawField(base, bounds); // Fallback
        break;
    }

    container.addChild(base);
    // Cache the procedurally generated graphics to a bitmap for extreme performance
    container.cacheAsBitmap = true;

    return container;
  }

  private static inferBiomeType(name: string): "forest" | "field" | "water" | "settlement" | "unknown" {
    const n = name.toLowerCase();
    if (n.includes("bosco") || n.includes("foresta") || n.includes("selva")) return "forest";
    if (n.includes("campo") || n.includes("prato") || n.includes("radura") || n.includes("pianura")) return "field";
    if (n.includes("sorgente") || n.includes("lago") || n.includes("fiume")) return "water";
    if (n.includes("città") || n.includes("villaggio") || n.includes("roccaforte") || n.includes("accampamento") || n.includes("cittadina")) return "settlement";
    return "unknown";
  }

  private static drawBlob(g: Graphics, bounds: { rx: number, ry: number }, color: number, alpha: number) {
    const points: {x: number, y: number}[] = [];
    const segments = 24;
    // Base radius
    const baseR = Math.max(bounds.rx, bounds.ry) * 0.9;
    
    for (let i = 0; i < segments; i++) {
      const angle = (i / segments) * Math.PI * 2;
      // Irregularity: varying radius by +/- 15%
      const r = baseR * (0.85 + Math.random() * 0.3);
      // Squeeze it into the bounds ratio
      const x = Math.cos(angle) * r * (bounds.rx / baseR);
      const y = Math.sin(angle) * r * (bounds.ry / baseR);
      points.push({x, y});
    }

    g.moveTo(points[0]!.x, points[0]!.y);
    for (let i = 1; i < points.length; i++) {
      // Create organic curves (approximate spline with quadratic curve to midpoints)
      const prev = points[i - 1]!;
      const curr = points[i]!;
      const midX = (prev.x + curr.x) / 2;
      const midY = (prev.y + curr.y) / 2;
      g.quadraticCurveTo(prev.x, prev.y, midX, midY);
    }
    // Close the blob
    g.quadraticCurveTo(points[points.length-1]!.x, points[points.length-1]!.y, points[0]!.x, points[0]!.y);
    g.fill({ color, alpha });
  }

  private static drawForest(g: Graphics, bounds: { rx: number, ry: number }) {
    this.drawBlob(g, bounds, BIOME_COLORS.forestBase, 0.95);
    
    const treeCount = Math.floor((bounds.rx * bounds.ry) / 40); 
    for (let i = 0; i < treeCount; i++) {
      const angle = Math.random() * Math.PI * 2;
      const r = Math.pow(Math.random(), 0.6); 
      const x = Math.cos(angle) * bounds.rx * r;
      const y = Math.sin(angle) * bounds.ry * r;
      const treeSize = 4 + Math.random() * 8;
      
      g.circle(x, y, treeSize).fill({ color: BIOME_COLORS.forestTree, alpha: 0.9 });
      g.circle(x - 1, y - 2, treeSize * 0.7).fill({ color: BIOME_COLORS.forestHighlight, alpha: 0.6 });
    }
  }

  private static drawField(g: Graphics, bounds: { rx: number, ry: number }) {
    this.drawBlob(g, bounds, BIOME_COLORS.fieldBase, 0.9);
    
    const tuftCount = Math.floor((bounds.rx * bounds.ry) / 80); 
    for (let i = 0; i < tuftCount; i++) {
      const angle = Math.random() * Math.PI * 2;
      const r = Math.pow(Math.random(), 0.7); 
      const x = Math.cos(angle) * bounds.rx * r;
      const y = Math.sin(angle) * bounds.ry * r;
      
      g.moveTo(x, y + 2).lineTo(x - 2, y - 2).lineTo(x + 2, y - 1).fill({ color: BIOME_COLORS.fieldTuft, alpha: 0.8 });
    }
  }

  private static drawWater(g: Graphics, bounds: { rx: number, ry: number }) {
    this.drawBlob(g, bounds, BIOME_COLORS.waterBase, 0.9);
    
    const rippleCount = Math.floor((bounds.rx * bounds.ry) / 60); 
    for (let i = 0; i < rippleCount; i++) {
      const angle = Math.random() * Math.PI * 2;
      const r = Math.pow(Math.random(), 0.8); 
      const x = Math.cos(angle) * bounds.rx * r;
      const y = Math.sin(angle) * bounds.ry * r;
      const w = 6 + Math.random() * 12;
      const h = 1.5 + Math.random() * 2;
      g.ellipse(x, y, w, h).fill({ color: BIOME_COLORS.waterRipple, alpha: 0.8 });
    }
  }

  private static drawSettlement(g: Graphics, bounds: { rx: number, ry: number }) {
    this.drawBlob(g, bounds, BIOME_COLORS.settlementBase, 0.95);
    
    const structureCount = Math.floor((bounds.rx * bounds.ry) / 100); 
    for (let i = 0; i < structureCount; i++) {
      const angle = Math.random() * Math.PI * 2;
      const r = Math.pow(Math.random(), 1.5); 
      const x = Math.cos(angle) * bounds.rx * r;
      const y = Math.sin(angle) * bounds.ry * r;
      const w = 8 + Math.random() * 12;
      const h = 6 + Math.random() * 10;
      g.rect(x - w/2, y - h/2, w, h).fill({ color: BIOME_COLORS.settlementStructure, alpha: 0.9 });
      g.rect(x - w/2, y - h/2, w, 2).fill({ color: 0x4a433f, alpha: 0.5 });
    }
  }
}
