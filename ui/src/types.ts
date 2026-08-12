export type Visibility = "public" | "local" | "private";

export interface EventEnvelope {
  event_id: string;
  sequence: number;
  schema_version: number;
  world_tick: number;
  world_time: string;
  event_type: string;
  actor_ids: string[];
  location: string | null;
  payload: Record<string, unknown>;
  visibility: Visibility;
  recipient_ids: string[];
  causation_id: string | null;
}

export interface MaterialAgent {
  agent_id: string;
  name: string;
  location: string;
  energy: number;
  hunger: number;
  thirst: number;
  native_language: string;
  language_proficiencies: Record<string, number>;
  skills: Record<string, number>;
  family_group_id: string | null;
  inventory: Record<string, number>;
  inventory_capacity: number;
  active: boolean;
}

export interface ResourceNode {
  resource_id: string;
  kind: string;
  label: string;
  location: string;
  quantity: number;
  unit: string;
  renewable: boolean;
}

export interface ActivityDefinition {
  activity_id: string;
  label: string;
  location: string;
  energy_cost: number;
  practiced_skill: string | null;
  minimum_proficiency: number;
  skill_gain: number;
}

export interface ResonanceNode {
  node_id: string;
  label: string;
  location: string;
  intensity: number;
}

export interface CooperationState {
  proposal_id: string;
  proposer_id: string;
  target_id: string;
  activity_id: string;
  status: string;
  created_tick: number;
  response_tick: number | null;
}

export interface DisputeState {
  dispute_id: string;
  opener_id: string;
  target_id: string;
  subject_event_id: string;
  status: string;
  created_tick: number;
  resolution_offered_by: string | null;
}

export interface ObserverWorld {
  tick: number;
  world_time: string;
  locations: Record<string, string[]>;
  agents: Record<string, MaterialAgent>;
  resources: Record<string, ResourceNode>;
  activities: Record<string, ActivityDefinition>;
  resonance_nodes: Record<string, ResonanceNode>;
  family_groups: Record<string, string[]>;
  cooperations: Record<string, CooperationState>;
  disputes: Record<string, DisputeState>;
}

export interface AgentMindSnapshot {
  agent_id: string;
  name: string;
  values: string[];
  temperament: string[];
  needs: Record<string, number>;
  affect: Record<string, number>;
  beliefs: Record<string, unknown>;
  relationships: Record<string, unknown>;
  goals: string[];
  plans: Record<string, unknown>;
  commitments: Record<string, unknown>;
  role_interpretations: Record<string, unknown>;
  anamnesis_fragments: Record<string, unknown>;
  resonance_orientation: Record<string, unknown> | null;
  memories: unknown[];
  reflections: unknown[];
  last_perceived_sequence: number;
  next_activation_tick: number | null;
  next_activation_reason: string;
  private_state: Record<string, unknown>;
}

export interface ObserverSnapshot {
  schema_version: number;
  observer_scope: "architect-local-read-only";
  last_sequence: number;
  latest_sequence: number;
  is_live: boolean;
  world: ObserverWorld;
  minds: Record<string, AgentMindSnapshot>;
}

export type ViewMode = "live" | "paused";

export interface EventsResponse {
  events: EventEnvelope[];
}

export interface ChronicleEntry {
  entry_id: string;
  sequence: number;
  from_sequence: number;
  through_sequence: number;
  world_tick: number;
  world_time: string;
  title: string;
  prose: string;
  source_event_ids: string[];
  provider: string;
  model: string;
  inference_id: string;
  attempts: number;
  prompt_version: string;
  created_at: string;
}

export interface ChronicleResponse {
  entries: ChronicleEntry[];
}

export type ConnectionStatus = "idle" | "connecting" | "live" | "reconnecting" | "offline";
