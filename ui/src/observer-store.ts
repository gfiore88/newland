import type {
  ChronicleEntry,
  ChronicleResponse,
  ConnectionStatus,
  EventEnvelope,
  EventsResponse,
  ObserverSnapshot,
  ViewMode,
} from "./types";

interface EventStream {
  close(): void;
  addEventListener(type: string, listener: EventListener): void;
  onopen: ((event: Event) => void) | null;
  onerror: ((event: Event) => void) | null;
}

type Fetcher = typeof fetch;
type EventStreamFactory = (url: string) => EventStream;
type Listener = () => void;

export interface ObserverStoreState {
  snapshot: ObserverSnapshot | null;
  viewSnapshot: ObserverSnapshot | null;
  viewMode: ViewMode;
  events: readonly EventEnvelope[];
  viewEvents: readonly EventEnvelope[];
  connection: ConnectionStatus;
  error: string | null;
  liveSequence: number;
  chronicle: readonly ChronicleEntry[];
  chronicleSequence: number;
}

export class ObserverStore {
  readonly apiBase: string;
  private readonly fetcher: Fetcher;
  private readonly streamFactory: EventStreamFactory;
  private readonly listeners = new Set<Listener>();
  private worldStream: EventStream | null = null;
  private chronicleStream: EventStream | null = null;
  private refreshTimer: ReturnType<typeof setTimeout> | null = null;
  private bootstrapRetryTimer: ReturnType<typeof setTimeout> | null = null;
  private seekRequest = 0;
  private mutableState: ObserverStoreState = {
    snapshot: null,
    viewSnapshot: null,
    viewMode: "live",
    events: [],
    viewEvents: [],
    connection: "idle",
    error: null,
    liveSequence: 0,
    chronicle: [],
    chronicleSequence: 0,
  };

  constructor(
    apiBase: string,
    fetcher: Fetcher = fetch,
    streamFactory: EventStreamFactory = (url) => new EventSource(url),
  ) {
    this.apiBase = apiBase.replace(/\/$/, "");
    this.fetcher = fetcher;
    this.streamFactory = streamFactory;
  }

  get state(): ObserverStoreState {
    return this.mutableState;
  }

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    listener();
    return () => this.listeners.delete(listener);
  }

  async start(): Promise<void> {
    this.stop();
    this.patch({ connection: "connecting", error: null });
    try {
      const snapshot = await this.getJson<ObserverSnapshot>("/api/snapshot");
      const historyStart = Math.max(0, snapshot.last_sequence - 199);
      const [history, chronicle] = await Promise.all([
        this.getJson<EventsResponse>(
          `/api/events?after_sequence=${historyStart}&limit=200`,
        ),
        this.getJson<ChronicleResponse>("/api/chronicle?after_sequence=0&limit=200"),
      ]);
      const chronicleEntries = uniqueChronicle(chronicle.entries);
      const chronicleSequence = chronicleEntries.at(-1)?.sequence ?? 0;
      this.mutableState = {
        snapshot,
        viewSnapshot: snapshot,
        viewMode: "live",
        events: uniqueOrdered(history.events),
        viewEvents: uniqueOrdered(history.events),
        connection: "connecting",
        error: null,
        liveSequence: snapshot.last_sequence,
        chronicle: chronicleEntries,
        chronicleSequence,
      };
      this.emit();
      this.openStream(snapshot.last_sequence);
      this.openChronicleStream(chronicleSequence);
    } catch (error) {
      this.patch({
        connection: "offline",
        error: error instanceof Error ? error.message : String(error),
      });
      this.bootstrapRetryTimer = setTimeout(() => {
        this.bootstrapRetryTimer = null;
        void this.start();
      }, 2_000);
    }
  }

  stop(): void {
    this.worldStream?.close();
    this.chronicleStream?.close();
    this.worldStream = null;
    this.chronicleStream = null;
    if (this.refreshTimer !== null) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
    if (this.bootstrapRetryTimer !== null) {
      clearTimeout(this.bootstrapRetryTimer);
      this.bootstrapRetryTimer = null;
    }
  }

  pause(): void {
    if (!this.mutableState.snapshot) return;
    this.seekRequest += 1;
    this.patch({
      viewMode: "paused",
      viewSnapshot: this.mutableState.viewSnapshot ?? this.mutableState.snapshot,
    });
  }

  goLive(): void {
    if (!this.mutableState.snapshot) return;
    this.seekRequest += 1;
    this.patch({
      viewMode: "live",
      viewSnapshot: this.mutableState.snapshot,
      viewEvents: this.mutableState.events,
      error: null,
    });
    void this.refreshSnapshot();
  }

  async seek(sequence: number): Promise<void> {
    const maximum = this.mutableState.liveSequence;
    if (!Number.isInteger(sequence) || sequence < 0 || sequence > maximum) {
      throw new RangeError(`sequence must be between 0 and ${maximum}`);
    }
    const request = ++this.seekRequest;
    this.patch({ viewMode: "paused", error: null });
    try {
      const historyStart = Math.max(0, sequence - 199);
      const [snapshot, history] = await Promise.all([
        this.getJson<ObserverSnapshot>(`/api/snapshot?at_sequence=${sequence}`),
        this.getJson<EventsResponse>(
          `/api/events?after_sequence=${historyStart}&limit=200`,
        ),
      ]);
      if (request !== this.seekRequest) return;
      this.patch({
        viewSnapshot: snapshot,
        viewEvents: uniqueOrdered(history.events).filter(
          (event) => event.sequence <= sequence,
        ),
        error: null,
      });
    } catch (error) {
      if (request !== this.seekRequest) return;
      this.patch({
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }

  private openStream(afterSequence: number): void {
    const stream = this.streamFactory(
      `${this.apiBase}/api/stream?after_sequence=${afterSequence}`,
    );
    this.worldStream = stream;
    stream.onopen = () => this.patch({ connection: "live", error: null });
    stream.onerror = () => this.patch({ connection: "reconnecting" });
    stream.addEventListener("newland-event", (message) => {
      const event = JSON.parse((message as MessageEvent<string>).data) as EventEnvelope;
      if (event.sequence <= this.mutableState.liveSequence) return;
      this.mutableState = {
        ...this.mutableState,
        events: uniqueOrdered([...this.mutableState.events, event]).slice(-200),
        viewEvents:
          this.mutableState.viewMode === "live"
            ? uniqueOrdered([...this.mutableState.events, event]).slice(-200)
            : this.mutableState.viewEvents,
        liveSequence: event.sequence,
      };
      this.emit();
      this.scheduleSnapshotRefresh();
    });
  }

  private openChronicleStream(afterSequence: number): void {
    const stream = this.streamFactory(
      `${this.apiBase}/api/chronicle-stream?after_sequence=${afterSequence}`,
    );
    this.chronicleStream = stream;
    stream.addEventListener("chronicle-entry", (message) => {
      const entry = JSON.parse((message as MessageEvent<string>).data) as ChronicleEntry;
      if (entry.sequence <= this.mutableState.chronicleSequence) return;
      this.mutableState = {
        ...this.mutableState,
        chronicle: uniqueChronicle([...this.mutableState.chronicle, entry]).slice(-200),
        chronicleSequence: entry.sequence,
      };
      this.emit();
    });
  }

  private scheduleSnapshotRefresh(): void {
    if (this.refreshTimer !== null) return;
    this.refreshTimer = setTimeout(() => {
      this.refreshTimer = null;
      void this.refreshSnapshot();
    }, 80);
  }

  private async refreshSnapshot(): Promise<void> {
    try {
      const snapshot = await this.getJson<ObserverSnapshot>("/api/snapshot");
      if (snapshot.last_sequence < (this.mutableState.snapshot?.last_sequence ?? 0)) {
        return;
      }
      this.patch({
        snapshot,
        viewSnapshot:
          this.mutableState.viewMode === "live"
            ? snapshot
            : this.mutableState.viewSnapshot,
        error: null,
      });
    } catch (error) {
      this.patch({
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }

  private async getJson<T>(path: string): Promise<T> {
    const response = await this.fetcher(`${this.apiBase}${path}`, {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      throw new Error(`Observer API ${response.status}: ${response.statusText}`);
    }
    return (await response.json()) as T;
  }

  private patch(patch: Partial<ObserverStoreState>): void {
    this.mutableState = { ...this.mutableState, ...patch };
    this.emit();
  }

  private emit(): void {
    for (const listener of this.listeners) listener();
  }
}

function uniqueOrdered(events: EventEnvelope[]): EventEnvelope[] {
  const bySequence = new Map<number, EventEnvelope>();
  for (const event of events) bySequence.set(event.sequence, event);
  return [...bySequence.values()].sort((left, right) => left.sequence - right.sequence);
}

function uniqueChronicle(entries: ChronicleEntry[]): ChronicleEntry[] {
  const bySequence = new Map<number, ChronicleEntry>();
  for (const entry of entries) bySequence.set(entry.sequence, entry);
  return [...bySequence.values()].sort((left, right) => left.sequence - right.sequence);
}
