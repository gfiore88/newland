---
id: adr-0010
title: "Dynamic Embodied Carrying Capacity"
status: "Proposed"
date: "2026-08-12"
authors: ["Agent AI", "Giovanni Fiore"]
tags: ["agents", "body", "health", "inventory", "event-sourcing", "adjudication"]
---

# ADR-0010: Dynamic Embodied Carrying Capacity

## Context & Problem Statement

Newland currently assigns `inventory_capacity = 20.0` to every inhabitant in the material state, initial registration, arrival profile, and legacy replay path. The world adjudicator then compares the numerical sum of inventory quantities with that shared value. This flattens physically different people into the same body and also treats litres and kilograms as if their numeric quantities were interchangeable.

Carrying capacity is not an inhabitant decision: a Newlander decides in real time what to attempt, but their body and the physical world determine whether the attempted load is sustainable. The capacity must therefore derive from the inhabitant's agent sheet at admission and evolve from canonical bodily events. The event log, rather than the mutable Markdown sheet, remains authoritative after admission according to ADR-0007.

The current character template exposes only a textual `apparent_age` placeholder. It does not provide canonical age, somatotype, body mass, strength, conditioning, health, injury, illness, mobility, or fatigue. Existing Elia and Amina bootstrap records likewise contain no such facts. Newland must not silently invent those missing facts or retain `20.0` as a compatibility fallback.

## Decision Drivers

- [DRV-001] **Physical Individuality**: Carrying capacity must differ according to each inhabitant's age, somatotype, body mass, physical condition, and health.
- [DRV-002] **Temporal Evolution**: Training, exertion, rest, nutrition, hydration, injury, illness, recovery, disability, and ageing must be able to improve or worsen effective capacity over time.
- [DRV-003] **Agent Autonomy**: The body model may constrain an attempted action but must never decide which action, load, training regimen, or response the inhabitant chooses.
- [DRV-004] **Replayability**: The same committed body history and formula version must reconstruct the same effective capacity without another LLM call.
- [DRV-005] **No Fabricated Defaults**: Missing body facts must produce an explicit admission or migration error, not a universal capacity or an invented average person.
- [DRV-006] **Physical Units**: Inventory load must be normalized to mass before comparison with a capacity expressed in kilograms.
- [DRV-007] **Explainability**: The Observer and tests must be able to show which profile and current-state factors produced a capacity without exposing private cognition.
- [DRV-008] **Continuity Under Decline**: A reduction in capacity must not destroy or silently discard already carried objects.

## Considered Alternatives

### Alternative 1: Universal Static Capacity

- **Description**: Keep `20.0` for every inhabitant and adjust it manually only for exceptional characters.
- **Rejection Rationale**: [REJ-001] This preserves a physically homogeneous population, cannot evolve coherently, and makes exceptions arbitrary and difficult to replay.

### Alternative 2: LLM-Selected Capacity on Every Action

- **Description**: Ask the active inhabitant's cognition model how much they can carry whenever they attempt to gather or move an object.
- **Rejection Rationale**: [REJ-002] A subjective model response cannot be authoritative physical evidence, is vulnerable to prompt drift, and would make identical world history replay to different material outcomes.

### Alternative 3: Single Mutable Health Multiplier

- **Description**: Derive one initial capacity and multiply it by a generic `health` scalar.
- **Rejection Rationale**: [REJ-003] One scalar cannot distinguish fatigue, injury, illness, mobility, conditioning, or long-term strength, and provides insufficient provenance for believable evolution.

### Alternative 4: Versioned Body Profile and Event-Sourced Physical State

- **Description**: Import required body facts from the agent sheet, evolve separate physical dimensions through canonical events, normalize inventory to mass, and derive effective carrying capacity with a versioned physical policy.
- **Rejection Rationale**: N/A (Selected Option).

## Decision Outcome

Chosen Option: **Alternative 4 (Versioned Body Profile and Event-Sourced Physical State)**.

### Detailed Decision Points

- [BDY-001] **Required Admission Profile**: Every new arrival will provide `age_years_at_arrival`, `body_mass_kg`, a structured continuous somatotype profile, baseline strength, baseline conditioning, mobility, and an initial health assessment. The agent-sheet schema will use bounded numeric fields rather than relying on prose labels alone.
- [BDY-002] **Somatotype Representation**: We will preserve the requested somatotype as three continuous components (`endomorphy`, `mesomorphy`, `ectomorphy`) and retain body mass separately. We will not reduce a person to a categorical body label or treat somatotype as a direct synonym for strength.
- [BDY-003] **Canonical Import Boundary**: A `.agent.md` sheet will be an admission input and human-readable projection. Registration will copy validated body facts into versioned canonical events; subsequent physical changes will come from the event log, not silent Markdown edits.
- [BDY-004] **Separated Physical State**: Canonical state will distinguish slow-changing `strength`, `conditioning`, and `mobility` from transient `fatigue`, `injury`, `illness`, `nutrition`, and `hydration`. A generic health score may be exposed as a derived summary but will not replace these causes.
- [BDY-005] **Derived Capacity**: `effective_carry_capacity_kg` will be computed, not freely stored or supplied by cognition. A versioned `CarryingCapacityPolicy` will combine body mass, age, somatotype, strength, conditioning, mobility, and current health burdens, with explicit bounds and inspectable factor contributions.
- [BDY-006] **No Per-Agent Magic Number**: The policy will contain globally versioned physical calibration coefficients and equations, not an identical per-agent capacity. Changing calibration will require a new policy version and an explicit migration or branch because it can change adjudication outcomes.
- [BDY-007] **Age Progression**: Effective age will derive from `age_years_at_arrival`, arrival tick, and world elapsed time. Age effects will use a continuous bounded curve rather than abrupt age categories.
- [BDY-008] **Event-Sourced Evolution**: Accepted physical activity, exertion, rest, consumption, deprivation, injury, illness, treatment, recovery, and elapsed time may emit explicit bodily consequence events. Reducers will update physical state from those events; replay will never rerun an LLM to reconstruct the body.
- [BDY-009] **Agency Boundary**: Generative cognition will choose whether to gather, carry, rest, train, seek help, discard, transfer, or continue while burdened. The physiological system and adjudicator will only calculate consequences and validate physical feasibility.
- [BDY-010] **Grounded Consequences**: An LLM intention or self-description cannot directly create strength, health, injury, or capacity. A bodily change requires an accepted action or world event with explicit causation and a deterministic or recorded stochastic outcome.
- [INV-001] **Mass-Normalized Load**: Resource and item definitions will expose mass in kilograms or a deterministic conversion to kilograms. Water volume will use a declared density conversion. The inventory will compare total carried mass, including containers when introduced, against capacity in kilograms.
- [INV-002] **Overburdened State**: If illness, injury, fatigue, or ageing lowers capacity beneath the current load, inventory remains intact and the agent becomes physically overburdened. The runtime will reject additional load and apply versioned movement/exertion constraints; it will not choose what the inhabitant drops.
- [INV-003] **Observer Projection**: The read model will expose current load, effective capacity, overburdened status, policy version, and factor breakdown. It will not expose private thoughts and will not accept capacity edits.
- [MIG-001] **No `20.0` Compatibility Fallback**: New registrations missing required body data will fail validation. Replay of historical `AgentRegistered` events may use a separately persisted `AgentBodyProfileConfigured` migration event, but never a hidden default.
- [MIG-002] **Existing Inhabitants**: Elia and Amina require explicit body facts in their agent profiles before the migration can complete. Newland will report the missing fields and will not fabricate their ages, somatotypes, mass, condition, or health.
- [TST-001] **Invariant Tests**: Tests will verify differing profiles produce differing capacities, health and conditioning changes evolve capacity, unit conversion is correct, overload never deletes inventory, cognition cannot set material capacity, and replay reproduces capacity and its factor breakdown exactly.

## Consequences

### Positive Consequences

- [POS-001] Every Newlander's carrying ability becomes an individual, embodied property rather than a shared constant.
- [POS-002] Physical improvement and decline acquire explicit causes and become observable across the inhabitant's history.
- [POS-003] The LLM retains full behavioral autonomy while the world maintains coherent, replayable physical limits.
- [POS-004] Mass normalization removes the current ambiguity between kilograms, litres, and future item units.
- [POS-005] Factor provenance makes unexpected adjudication outcomes explainable and testable.

### Negative Consequences & Risks

- [NEG-001] **Calibration Risk**: A compact body model can create false physiological precision or unfair outcomes. - **Mitigation**: Keep factors inspectable, document units and bounds, test representative profiles, and version every calibration change.
- [NEG-002] **Sensitive Character Data**: Health and body measurements may be private diegetic facts. - **Mitigation**: Store canonical events with explicit visibility and expose them only through the privileged local Observer, not ordinary inhabitant perception.
- [NEG-003] **Additional State Complexity**: Body profiles, transient conditions, item mass, and policy versions expand schemas and replay logic. - **Mitigation**: Implement profile import and pure capacity derivation first, then add evolution events incrementally with focused commits.
- [NEG-004] **Legacy World Cannot Auto-Migrate**: Existing inhabitants lack the required source facts. - **Mitigation**: Provide a validation report and explicit profile-enrichment path; pause migration until the missing facts are supplied.
- [NEG-005] **Somatotype Limitations**: Somatotype is a descriptive abstraction and not a complete predictor of strength or health. - **Mitigation**: Represent it continuously, combine it with measured body mass and independent physical-state dimensions, and avoid categorical behavioral inference.
- [NEG-006] **Capacity Can Fall Below Current Load**: Health deterioration can create a state previously impossible under a static cap. - **Mitigation**: Model overburden explicitly, preserve inventory, and leave the response to the inhabitant's next generative decision.

## Compliance & RAG Impact

- [CMP-001] **Related Decisions**: ADR-0007 defines the authoritative world adjudicator and canonical event log; ADR-0008 reserves every inhabitant decision for real-time generative cognition.
- [CMP-002] **RAG Files Updated**: `docs/README.md`, `docs/index.md`, and `docs/log.md` index this proposal.
- [CMP-003] **Implementation After Approval**: We will update the agent-sheet schema, body and inventory contracts, event reducers, arrival validation, projections, migrations, and invariant tests in small monitored commits.
- [CMP-004] **Approval Required**: This ADR is proposed and must be explicitly approved by Giovanni Fiore before implementation begins.
