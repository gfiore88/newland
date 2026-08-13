import { UI_CONSTANTS } from "./constants";

export interface MapPoint {
  x: number;
  y: number;
}

export function layoutLocations(
  locations: Record<string, string[]>,
): Map<string, MapPoint> {
  const names = Object.keys(locations).sort((left, right) => left.localeCompare(right));
  const positions = new Map<string, MapPoint>();
  if (names.length === 0) return positions;

  // Center = node with most connections (natural graph hub)
  const center = names.reduce((best, name) =>
    (locations[name]?.length ?? 0) >= (locations[best]?.length ?? 0) ? name : best
  , names[0] ?? "");

  if (!center) return positions;
  positions.set(center, { x: 0, y: 0 });

  const orbit = names.filter((name) => name !== center);
  
  // Try to find natural directions from names
  orbit.forEach((name, index) => {
    let angle = -Math.PI / 2 + (index / Math.max(1, orbit.length)) * Math.PI * 2;
    
    // Explicit compass directions
    if (name.includes("_nord") || name.includes("nord_")) angle = -Math.PI / 2;
    else if (name.includes("_est") || name.includes("est_")) angle = 0;
    else if (name.includes("_sud") || name.includes("sud_")) angle = Math.PI / 2;
    else if (name.includes("_ovest") || name.includes("ovest_")) angle = Math.PI;

    positions.set(name, {
      x: Math.cos(angle) * UI_CONSTANTS.LAYOUT_RADIUS_X,
      y: Math.sin(angle) * UI_CONSTANTS.LAYOUT_RADIUS_Y,
    });
  });
  return positions;
}

export function displayName(identifier: string): string {
  return identifier
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
