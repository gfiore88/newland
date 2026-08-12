import { describe, expect, it, vi } from "vitest";

import { ObserverStore } from "./observer-store";
import type { ChronicleEntry, EventEnvelope, ObserverSnapshot } from "./types";

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
      if (url.includes("snapshot")) return new Response(JSON.stringify(snapshot));
      if (url.includes("chronicle")) return new Response(JSON.stringify({ entries: [] }));
      return new Response(JSON.stringify({ events: history }));
    });
    const worldStream = new FakeEventStream();
    const chronicleStream = new FakeEventStream();
    const streamFactory = vi.fn((url: string) =>
      url.includes("chronicle") ? chronicleStream : worldStream,
    );
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
    const fetcher = vi.fn(async (input: string | URL | Request) => {
      const url = String(input);
      if (url.includes("chronicle")) return new Response(JSON.stringify({ entries: [] }));
      if (url.includes("events")) {
        return new Response(JSON.stringify({ events: [makeEvent(1)] }));
      }
      const snapshotSequence = fetcher.mock.calls.length > 3 ? 2 : 1;
      return new Response(JSON.stringify(makeSnapshot(snapshotSequence)));
    });
    const worldStream = new FakeEventStream();
    const store = new ObserverStore(
      "http://127.0.0.1:8765",
      fetcher,
      (url) => (url.includes("chronicle") ? new FakeEventStream() : worldStream),
    );
    await store.start();
    const event = makeEvent(2);

    worldStream.emit(
      "newland-event",
      new MessageEvent("newland-event", { data: JSON.stringify(event) }),
    );
    worldStream.emit(
      "newland-event",
      new MessageEvent("newland-event", { data: JSON.stringify(event) }),
    );
    await vi.advanceTimersByTimeAsync(80);

    expect(store.state.events.map((item) => item.sequence)).toEqual([1, 2]);
    expect(store.state.snapshot?.last_sequence).toBe(2);
    expect(fetcher).toHaveBeenCalledTimes(4);
    store.stop();
    vi.useRealTimers();
  });

  it("receives generative chronicle entries on their independent cursor", async () => {
    const firstEntry = makeChronicleEntry(1);
    const fetcher = vi.fn(async (input: string | URL | Request) => {
      const url = String(input);
      if (url.includes("snapshot")) return new Response(JSON.stringify(makeSnapshot(4)));
      if (url.includes("chronicle")) {
        return new Response(JSON.stringify({ entries: [firstEntry] }));
      }
      return new Response(JSON.stringify({ events: [] }));
    });
    const chronicleStream = new FakeEventStream();
    const streamFactory = vi.fn((url: string) =>
      url.includes("chronicle") ? chronicleStream : new FakeEventStream(),
    );
    const store = new ObserverStore("http://127.0.0.1:8765", fetcher, streamFactory);
    await store.start();
    const secondEntry = makeChronicleEntry(2);

    chronicleStream.emit(
      "chronicle-entry",
      new MessageEvent("chronicle-entry", { data: JSON.stringify(secondEntry) }),
    );
    chronicleStream.emit(
      "chronicle-entry",
      new MessageEvent("chronicle-entry", { data: JSON.stringify(secondEntry) }),
    );

    expect(store.state.chronicle.map((entry) => entry.sequence)).toEqual([1, 2]);
    expect(store.state.chronicleSequence).toBe(2);
    expect(streamFactory).toHaveBeenCalledWith(
      "http://127.0.0.1:8765/api/chronicle-stream?after_sequence=1",
    );
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

function makeChronicleEntry(sequence: number): ChronicleEntry {
  return {
    entry_id: `chronicle-${sequence}`,
    sequence,
    from_sequence: sequence,
    through_sequence: sequence,
    world_tick: sequence,
    world_time: "0001-01-01T06:00:00+00:00",
    title: `Voce ${sequence}`,
    prose: "Testo generato.",
    source_event_ids: [`event-${sequence}`],
    provider: "test-double",
    model: "generated",
    inference_id: `inference-${sequence}`,
    attempts: 1,
    prompt_version: "silent-chronicler-v2",
    created_at: "2026-08-12T00:00:00+00:00",
  };
}
