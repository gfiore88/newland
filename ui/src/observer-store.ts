import type {
  ConnectionStatus,
  EventEnvelope,
  EventsResponse,
  ObserverSnapshot,
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
  events: readonly EventEnvelope[];
  connection: ConnectionStatus;
  error: string | null;
  liveSequence: number;
}

export class ObserverStore {
  readonly apiBase: string;
  private readonly fetcher: Fetcher;
  private readonly streamFactory: EventStreamFactory;
  private readonly listeners = new Set<Listener>();
  private stream: EventStream | null = null;
  private refreshTimer: ReturnType<typeof setTimeout> | null = null;
  private mutableState: ObserverStoreState = {
    snapshot: null,
    events: [],
    connection: "idle",
    error: null,
    liveSequence: 0,
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
      const history = await this.getJson<EventsResponse>(
        `/api/events?after_sequence=${historyStart}&limit=200`,
      );
      this.mutableState = {
        snapshot,
        events: uniqueOrdered(history.events),
        connection: "connecting",
        error: null,
        liveSequence: snapshot.last_sequence,
      };
      this.emit();
      this.openStream(snapshot.last_sequence);
    } catch (error) {
      this.patch({
        connection: "offline",
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }

  stop(): void {
    this.stream?.close();
    this.stream = null;
    if (this.refreshTimer !== null) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  private openStream(afterSequence: number): void {
    const stream = this.streamFactory(
      `${this.apiBase}/api/stream?after_sequence=${afterSequence}`,
    );
    this.stream = stream;
    stream.onopen = () => this.patch({ connection: "live", error: null });
    stream.onerror = () => this.patch({ connection: "reconnecting" });
    stream.addEventListener("newland-event", (message) => {
      const event = JSON.parse((message as MessageEvent<string>).data) as EventEnvelope;
      if (event.sequence <= this.mutableState.liveSequence) return;
      this.mutableState = {
        ...this.mutableState,
        events: uniqueOrdered([...this.mutableState.events, event]).slice(-200),
        liveSequence: event.sequence,
      };
      this.emit();
      this.scheduleSnapshotRefresh();
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
      this.patch({ snapshot, error: null });
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
