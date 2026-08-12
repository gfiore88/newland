import { describe, expect, it } from "vitest";

import { displayName, layoutLocations } from "./layout";

describe("layoutLocations", () => {
  it("keeps the initial settlement at the center and is order-independent", () => {
    const first = layoutLocations({
      bosco: ["cittadina_iniziale"],
      cittadina_iniziale: ["bosco", "sorgente"],
      sorgente: ["cittadina_iniziale"],
    });
    const second = layoutLocations({
      sorgente: ["cittadina_iniziale"],
      bosco: ["cittadina_iniziale"],
      cittadina_iniziale: ["bosco", "sorgente"],
    });

    expect(first.get("cittadina_iniziale")).toEqual({ x: 0, y: 0 });
    expect([...first]).toEqual([...second]);
  });

  it("turns canonical identifiers into presentation labels", () => {
    expect(displayName("cittadina_iniziale")).toBe("Cittadina Iniziale");
  });
});
