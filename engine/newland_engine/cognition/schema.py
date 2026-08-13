from typing import Any

def get_cognition_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "intention": {
                "type": "object",
                "properties": {
                    "action_type": {
                        "type": "string",
                        "enum": [
                            "speak",
                            "move",
                            "rest",
                            "offer_help",
                            "gather",
                            "consume",
                            "perform_activity",
                            "propose_cooperation",
                            "respond_cooperation",
                            "perform_cooperation",
                            "open_dispute",
                            "respond_dispute",
                            "attune_resonance",
                        ],
                    },
                    "target_id": {"type": ["string", "null"]},
                    "destination": {"type": ["string", "null"]},
                    "duration_minutes": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 240,
                    },
                    "spoken_content": {"type": ["string", "null"]},
                    "language": {"type": ["string", "null"]},
                    "resource_id": {"type": ["string", "null"]},
                    "quantity": {
                        "type": ["number", "null"],
                        "exclusiveMinimum": 0,
                    },
                    "activity_id": {"type": ["string", "null"]},
                    "proposal_id": {"type": ["string", "null"]},
                    "dispute_id": {"type": ["string", "null"]},
                    "subject_event_id": {"type": ["string", "null"]},
                    "response": {
                        "type": ["string", "null"],
                        "enum": [
                            "accept",
                            "decline",
                            "contest",
                            "offer_resolution",
                            "accept_resolution",
                            None,
                        ],
                    },
                    "node_id": {"type": ["string", "null"]},
                    "motivation_summary": {"type": "string", "maxLength": 300},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                },
                "required": [
                    "action_type",
                    "target_id",
                    "destination",
                    "duration_minutes",
                    "spoken_content",
                    "language",
                    "resource_id",
                    "quantity",
                    "activity_id",
                    "proposal_id",
                    "dispute_id",
                    "subject_event_id",
                    "response",
                    "node_id",
                    "motivation_summary",
                    "confidence",
                ],
                "additionalProperties": False,
            },
            "memory_appraisals": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "source_event_id": {"type": "string"},
                        "subjective_summary": {"type": "string", "maxLength": 500},
                        "salience": {"type": "number", "minimum": 0, "maximum": 1},
                        "emotional_tone": {"type": "string", "maxLength": 100},
                        "confidence": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                        },
                    },
                    "required": [
                        "source_event_id",
                        "subjective_summary",
                        "salience",
                        "emotional_tone",
                        "confidence",
                    ],
                    "additionalProperties": False,
                },
            },
            "mental_updates": {
                "type": "object",
                "properties": {
                    "beliefs": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "key": {"type": "string", "maxLength": 120},
                                "statement": {"type": "string", "maxLength": 500},
                                "confidence": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                },
                                "source_ids": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "minItems": 1,
                                },
                            },
                            "required": [
                                "key",
                                "statement",
                                "confidence",
                                "source_ids",
                            ],
                            "additionalProperties": False,
                        },
                    },
                    "relationships": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "other_agent_id": {"type": "string"},
                                "familiarity_delta": {
                                    "type": "number",
                                    "minimum": -1,
                                    "maximum": 1,
                                },
                                "trust_delta": {
                                    "type": "number",
                                    "minimum": -1,
                                    "maximum": 1,
                                },
                                "warmth_delta": {
                                    "type": "number",
                                    "minimum": -1,
                                    "maximum": 1,
                                },
                                "tension_delta": {
                                    "type": "number",
                                    "minimum": -1,
                                    "maximum": 1,
                                },
                                "interpretation": {
                                    "type": "string",
                                    "maxLength": 500,
                                },
                                "source_ids": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "minItems": 1,
                                },
                            },
                            "required": [
                                "other_agent_id",
                                "familiarity_delta",
                                "trust_delta",
                                "warmth_delta",
                                "tension_delta",
                                "interpretation",
                                "source_ids",
                            ],
                            "additionalProperties": False,
                        },
                    },
                    "affect": {
                        "type": ["object", "null"],
                        "properties": {
                            "calm_delta": {
                                "type": "number",
                                "minimum": -1,
                                "maximum": 1,
                            },
                            "curiosity_delta": {
                                "type": "number",
                                "minimum": -1,
                                "maximum": 1,
                            },
                            "melancholy_delta": {
                                "type": "number",
                                "minimum": -1,
                                "maximum": 1,
                            },
                            "interpretation": {"type": "string", "maxLength": 500},
                            "source_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 1,
                            },
                        },
                        "required": [
                            "calm_delta",
                            "curiosity_delta",
                            "melancholy_delta",
                            "interpretation",
                            "source_ids",
                        ],
                        "additionalProperties": False,
                    },
                    "reflections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "statement": {"type": "string", "maxLength": 700},
                                "confidence": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                },
                                "source_ids": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "minItems": 1,
                                },
                            },
                            "required": [
                                "statement",
                                "confidence",
                                "source_ids",
                            ],
                            "additionalProperties": False,
                        },
                    },
                    "goals": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "operation": {
                                    "type": "string",
                                    "enum": ["add", "remove"],
                                },
                                "goal": {"type": "string", "maxLength": 300},
                                "reason": {"type": "string", "maxLength": 500},
                                "source_ids": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "minItems": 1,
                                },
                            },
                            "required": [
                                "operation",
                                "goal",
                                "reason",
                                "source_ids",
                            ],
                            "additionalProperties": False,
                        },
                    },
                    "plans": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "operation": {
                                    "type": "string",
                                    "enum": ["upsert", "complete", "abandon"],
                                },
                                "plan_key": {"type": "string", "maxLength": 120},
                                "description": {"type": "string", "maxLength": 500},
                                "steps": {
                                    "type": "array",
                                    "items": {"type": "string", "maxLength": 300},
                                },
                                "source_ids": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "minItems": 1,
                                },
                            },
                            "required": [
                                "operation",
                                "plan_key",
                                "description",
                                "steps",
                                "source_ids",
                            ],
                            "additionalProperties": False,
                        },
                    },
                    "commitments": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "operation": {
                                    "type": "string",
                                    "enum": ["add", "complete", "abandon"],
                                },
                                "commitment_key": {
                                    "type": "string",
                                    "maxLength": 120,
                                },
                                "description": {"type": "string", "maxLength": 500},
                                "due_tick": {"type": "integer", "minimum": 0},
                                "involved_agent_ids": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "source_ids": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "minItems": 1,
                                },
                            },
                            "required": [
                                "operation",
                                "commitment_key",
                                "description",
                                "due_tick",
                                "involved_agent_ids",
                                "source_ids",
                            ],
                            "additionalProperties": False,
                        },
                    },
                    "role_interpretations": {
                        "type": "array",
                        "description": (
                            "Interpretazioni soggettive opzionali. Usare remove solo "
                            "per interpretation_key già presenti nel contesto privato."
                        ),
                        "items": {
                            "type": "object",
                            "properties": {
                                "operation": {
                                    "type": "string",
                                    "enum": ["upsert", "remove"],
                                },
                                "interpretation_key": {
                                    "type": "string",
                                    "maxLength": 120,
                                },
                                "subject_agent_id": {"type": "string"},
                                "role_label": {
                                    "type": "string",
                                    "maxLength": 160,
                                },
                                "interpretation": {
                                    "type": "string",
                                    "maxLength": 600,
                                },
                                "confidence": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                },
                                "source_ids": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "minItems": 1,
                                },
                            },
                            "required": [
                                "operation",
                                "interpretation_key",
                                "subject_agent_id",
                                "role_label",
                                "interpretation",
                                "confidence",
                                "source_ids",
                            ],
                            "additionalProperties": False,
                        },
                    },
                    "anamnesis_fragments": {
                        "type": "array",
                        "description": (
                            "Esperienze soggettive opzionali generate solo da segnali "
                            "di risonanza percepiti; non sono fatti canonici sul passato."
                        ),
                        "items": {
                            "type": "object",
                            "properties": {
                                "fragment_key": {
                                    "type": "string",
                                    "maxLength": 120,
                                },
                                "phenomenon_label": {
                                    "type": "string",
                                    "maxLength": 160,
                                },
                                "content": {"type": "string", "maxLength": 900},
                                "interpretation": {
                                    "type": "string",
                                    "maxLength": 700,
                                },
                                "confidence": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                },
                                "source_ids": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "minItems": 1,
                                },
                            },
                            "required": [
                                "fragment_key",
                                "phenomenon_label",
                                "content",
                                "interpretation",
                                "confidence",
                                "source_ids",
                            ],
                            "additionalProperties": False,
                        },
                    },
                    "resonance_orientation": {
                        "type": ["object", "null"],
                        "properties": {
                            "receptive": {"type": "boolean"},
                            "interpretation": {
                                "type": "string",
                                "maxLength": 700,
                            },
                            "source_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 1,
                            },
                        },
                        "required": [
                            "receptive",
                            "interpretation",
                            "source_ids",
                        ],
                        "additionalProperties": False,
                    },
                },
                "required": [
                    "beliefs",
                    "relationships",
                    "affect",
                    "reflections",
                    "goals",
                    "plans",
                    "commitments",
                    "role_interpretations",
                    "anamnesis_fragments",
                    "resonance_orientation",
                ],
                "additionalProperties": False,
            },
            "attention_schedule": {
                "type": "object",
                "properties": {
                    "next_activation_in_ticks": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 144,
                    },
                    "reason": {"type": "string", "maxLength": 300},
                },
                "required": ["next_activation_in_ticks", "reason"],
                "additionalProperties": False,
            },
        },
        "required": [
            "intention",
            "memory_appraisals",
            "mental_updates",
            "attention_schedule",
        ],
        "additionalProperties": False,
    }
