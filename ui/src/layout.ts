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

  const center =
    names.find((name) => name === "cittadina_iniziale") ??
    names.find((name) => name.includes("village") || name.includes("cittadina")) ??
    names[0];
  if (!center) return positions;
  positions.set(center, { x: 0, y: 0 });

  const orbit = names.filter((name) => name !== center);
  orbit.forEach((name, index) => {
    const angle = -Math.PI / 2 + (index / Math.max(1, orbit.length)) * Math.PI * 2;
    positions.set(name, {
      x: Math.cos(angle) * 330,
      y: Math.sin(angle) * 220,
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
