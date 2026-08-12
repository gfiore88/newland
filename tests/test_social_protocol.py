from __future__ import annotations

import unittest

from newland_engine.models import (
    ActivityDefinition,
    EventEnvelope,
    Intention,
    MaterialAgentState,
    WorldState,
    world_time_for_tick,
)
from newland_engine.world import WorldAdjudicator, reduce_event


class SocialProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = WorldState(
            locations={"village": set()},
            agents={
                "nwl-001": MaterialAgentState(
                    "nwl-001",
                    "Elia",
                    "village",
                    native_language="it",
                    language_proficiencies={"it": 1.0},
                    skills={"building": 0.6},
                ),
                "nwl-002": MaterialAgentState(
                    "nwl-002",
                    "Amina",
                    "village",
                    native_language="ar",
                    language_proficiencies={"ar": 1.0},
                    skills={"building": 0.5},
                ),
            },
            activities={
                "repair_roof": ActivityDefinition(
                    "repair_roof",
                    "repair a dry-stone roof",
                    "village",
                    energy_cost=0.05,
                    practiced_skill="building",
                    minimum_proficiency=0.4,
                    skill_gain=0.02,
                )
            },
        )
        self.adjudicator = WorldAdjudicator()

    def test_cooperation_requires_explicit_consent_before_joint_effects(self) -> None:
        proposal_events = self.adjudicator.adjudicate(
            self.state,
            "nwl-001",
            Intention(
                action_type="propose_cooperation",
                target_id="nwl-002",
                activity_id="repair_roof",
                spoken_content="Vuoi riparare il tetto insieme?",
                language="it",
            ),
            tick=1,
        )
        self._reduce(proposal_events)
        proposal = proposal_events[-1]
        self.assertEqual("pending", self.state.cooperations[proposal.event_id].status)

        premature = self.adjudicator.adjudicate(
            self.state,
            "nwl-001",
            Intention(
                action_type="perform_cooperation",
                proposal_id=proposal.event_id,
            ),
            tick=2,
        )
        self.assertEqual("ActionRejected", premature[-1].event_type)

        response_events = self.adjudicator.adjudicate(
            self.state,
            "nwl-002",
            Intention(
                action_type="respond_cooperation",
                proposal_id=proposal.event_id,
                response="accept",
                spoken_content="نعم، سأعمل معك.",
                language="ar",
            ),
            tick=2,
        )
        self._reduce(response_events)
        self.assertEqual("accepted", self.state.cooperations[proposal.event_id].status)

        performance_events = self.adjudicator.adjudicate(
            self.state,
            "nwl-001",
            Intention(
                action_type="perform_cooperation",
                proposal_id=proposal.event_id,
                duration_minutes=20,
            ),
            tick=3,
        )
        self._reduce(performance_events)
        performed = performance_events[-1]
        self.assertEqual("CooperationPerformed", performed.event_type)
        self.assertEqual(("nwl-001", "nwl-002"), performed.actor_ids)
        self.assertEqual("nwl-001", performed.payload["initiator_id"])
        self.assertEqual("completed", self.state.cooperations[proposal.event_id].status)
        self.assertAlmostEqual(0.7, self.state.agents["nwl-001"].energy)
        self.assertAlmostEqual(0.7, self.state.agents["nwl-002"].energy)
        self.assertAlmostEqual(0.62, self.state.agents["nwl-001"].skills["building"])
        self.assertAlmostEqual(0.52, self.state.agents["nwl-002"].skills["building"])

    def test_declined_cooperation_has_no_joint_material_effect(self) -> None:
        proposal_events = self.adjudicator.adjudicate(
            self.state,
            "nwl-001",
            Intention(
                action_type="propose_cooperation",
                target_id="nwl-002",
                activity_id="repair_roof",
                spoken_content="Lavoriamo insieme?",
                language="it",
            ),
            tick=1,
        )
        self._reduce(proposal_events)
        proposal_id = proposal_events[-1].event_id
        decline_events = self.adjudicator.adjudicate(
            self.state,
            "nwl-002",
            Intention(
                action_type="respond_cooperation",
                proposal_id=proposal_id,
                response="decline",
                spoken_content="لا، ليس الآن.",
                language="ar",
            ),
            tick=2,
        )
        self._reduce(decline_events)

        attempt = self.adjudicator.adjudicate(
            self.state,
            "nwl-001",
            Intention(action_type="perform_cooperation", proposal_id=proposal_id),
            tick=3,
        )
        self.assertEqual("ActionRejected", attempt[-1].event_type)
        self.assertEqual(0.8, self.state.agents["nwl-001"].energy)
        self.assertEqual(0.8, self.state.agents["nwl-002"].energy)

    def test_dispute_is_opened_by_an_agent_and_resolved_by_mutual_actions(self) -> None:
        subject = EventEnvelope(
            event_type="SpeechUttered",
            world_tick=1,
            world_time=world_time_for_tick(1),
            actor_ids=("nwl-002",),
            location="village",
            payload={
                "target_id": "nwl-001",
                "content": "Questa legna ora è mia.",
                "language": "ar",
            },
            visibility="local",
            recipient_ids=("nwl-001", "nwl-002"),
        )
        reduce_event(self.state, subject)
        opened_events = self.adjudicator.adjudicate(
            self.state,
            "nwl-001",
            Intention(
                action_type="open_dispute",
                target_id="nwl-002",
                subject_event_id=subject.event_id,
                spoken_content="Quella legna serviva al tetto comune.",
                language="it",
            ),
            tick=2,
        )
        self._reduce(opened_events)
        dispute_id = opened_events[-1].event_id
        self.assertEqual("open", self.state.disputes[dispute_id].status)

        offered = self.adjudicator.adjudicate(
            self.state,
            "nwl-002",
            Intention(
                action_type="respond_dispute",
                dispute_id=dispute_id,
                response="offer_resolution",
                spoken_content="سأعيد جزءًا منها إلى السقف.",
                language="ar",
            ),
            tick=3,
        )
        self._reduce(offered)
        self.assertEqual("resolution_offered", self.state.disputes[dispute_id].status)

        accepted = self.adjudicator.adjudicate(
            self.state,
            "nwl-001",
            Intention(
                action_type="respond_dispute",
                dispute_id=dispute_id,
                response="accept_resolution",
                spoken_content="Accetto questa soluzione.",
                language="it",
            ),
            tick=4,
        )
        self._reduce(accepted)
        self.assertEqual("resolved", self.state.disputes[dispute_id].status)

    def test_agent_cannot_dispute_an_event_it_did_not_perceive(self) -> None:
        private_event = EventEnvelope(
            event_type="TransitionRemembered",
            world_tick=1,
            world_time=world_time_for_tick(1),
            actor_ids=("nwl-002",),
            payload={"experience": "Un ricordo strettamente privato."},
            visibility="private",
            recipient_ids=("nwl-002",),
        )
        reduce_event(self.state, private_event)

        attempt = self.adjudicator.adjudicate(
            self.state,
            "nwl-001",
            Intention(
                action_type="open_dispute",
                target_id="nwl-002",
                subject_event_id=private_event.event_id,
                spoken_content="Contesto qualcosa che non posso conoscere.",
                language="it",
            ),
            tick=2,
        )

        self.assertEqual("ActionRejected", attempt[-1].event_type)
        self.assertEqual(
            "actor did not perceive the dispute subject event",
            attempt[-1].payload["reason"],
        )

    def _reduce(self, events: list[EventEnvelope]) -> None:
        for event in events:
            reduce_event(self.state, event)


if __name__ == "__main__":
    unittest.main()
