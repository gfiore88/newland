import { describe, expect, it, vi } from "vitest";

import { ObserverStore } from "./observer-store";
import type { EventEnvelope, ObserverSnapshot } from "./types";

class FakeEventStream {
  onopen: ((event: Event) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  closed = false;
  readonly listeners = new Map<string, EventListener>();

  close(): void {
    this.closed = true;
  }

  addEventListener(type: string, listener: EventListener): void {
    this.listeners.set(type, listener);
  }

  emit(type: string, event: Event): void {
    this.listeners.get(type)?.(event);
  }
}

describe("ObserverStore", () => {
  it("bootstraps at one sequence and opens the ordered SSE cursor", async () => {
    const snapshot = makeSnapshot(7);
    const history = [makeEvent(6), makeEvent(7)];
    const fetcher = vi.fn(async (input: string | URL | Request) => {
      const url = String(input);
      return new Response(JSON.stringify(url.includes("snapshot") ? snapshot : { events: history }));
    });
    const stream = new FakeEventStream();
    const streamFactory = vi.fn(() => stream);
    const store = new ObserverStore("http://127.0.0.1:8765/", fetcher, streamFactory);

    await store.start();

    expect(store.state.snapshot?.last_sequence).toBe(7);
    expect(store.state.events.map((event) => event.sequence)).toEqual([6, 7]);
    expect(streamFactory).toHaveBeenCalledWith(
      "http://127.0.0.1:8765/api/stream?after_sequence=7",
    );
  });

  it("accepts each live event once and refreshes canonical state", async () => {
    vi.useFakeTimers();
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(makeSnapshot(1))))
      .mockResolvedValueOnce(new Response(JSON.stringify({ events: [makeEvent(1)] })))
      .mockResolvedValueOnce(new Response(JSON.stringify(makeSnapshot(2))));
    const stream = new FakeEventStream();
    const store = new ObserverStore("http://127.0.0.1:8765", fetcher, () => stream);
    await store.start();
    const event = makeEvent(2);

    stream.emit("newland-event", new MessageEvent("newland-event", { data: JSON.stringify(event) }));
    stream.emit("newland-event", new MessageEvent("newland-event", { data: JSON.stringify(event) }));
    await vi.advanceTimersByTimeAsync(80);

    expect(store.state.events.map((item) => item.sequence)).toEqual([1, 2]);
    expect(store.state.snapshot?.last_sequence).toBe(2);
    expect(fetcher).toHaveBeenCalledTimes(3);
    store.stop();
    vi.useRealTimers();
  });
});

function makeSnapshot(sequence: number): ObserverSnapshot {
  return {
    schema_version: 1,
    observer_scope: "architect-local-read-only",
    last_sequence: sequence,
    world: {
      tick: sequence,
      world_time: "0001-01-01T06:00:00+00:00",
      locations: { village: [] },
      agents: {},
      resources: {},
      activities: {},
      resonance_nodes: {},
      family_groups: {},
      cooperations: {},
      disputes: {},
    },
    minds: {},
  };
}

function makeEvent(sequence: number): EventEnvelope {
  return {
    event_id: `event-${sequence}`,
    sequence,
    schema_version: 1,
    world_tick: sequence,
    world_time: "0001-01-01T06:00:00+00:00",
    event_type: "WorldObserved",
    actor_ids: [],
    location: null,
    payload: {},
    visibility: "public",
    recipient_ids: [],
    causation_id: null,
  };
}
