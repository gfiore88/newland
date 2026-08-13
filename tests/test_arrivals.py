from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import json
from io import BytesIO
from unittest.mock import patch

from helpers import ScriptedTestCognition
from newland_engine.arrival_factory import GenerativeArrivalFactory
from newland_engine.arrivals import ArrivalProfile
from newland_engine.event_store import EventStore
from newland_engine.models import AgentMind
from newland_engine.perception import PerceptionService
from newland_engine.simulation import NewlandSimulation
from newland_engine.world import replay


class ArrivalTests(unittest.TestCase):
    def test_family_arrival_is_atomic_private_and_replayable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "newland.db"
            profiles = self._family_profiles()
            with NewlandSimulation(
                path, cognition=ScriptedTestCognition()
            ) as simulation:
                persisted = simulation.admit_arrivals(profiles)
                state = simulation.state

                self.assertEqual(
                    {"nwl-101", "nwl-102"}, state.family_groups["fam-rivera"]
                )
                self.assertEqual("es", state.agents["nwl-101"].native_language)
                self.assertEqual(0.7, state.agents["nwl-101"].skills["orientamento"])
                self.assertIn("nwl-101", simulation.minds)
                self.assertIn("nwl-102", simulation.minds)

                family_event = next(
                    event
                    for event in persisted
                    if event.event_type == "FamilyGroupUpdated"
                )
                self.assertEqual(("nwl-101", "nwl-102"), family_event.recipient_ids)
                transitions = [
                    event
                    for event in persisted
                    if event.event_type == "TransitionRemembered"
                ]
                perception = PerceptionService()
                self.assertEqual(1, len(perception.perceive("nwl-101", transitions)))
                self.assertEqual([], perception.perceive("nwl-001", transitions))

            with EventStore(path) as store:
                reconstructed = replay(store.events())
                loaded_minds = store.load_minds()
            self.assertEqual(
                {"nwl-101", "nwl-102"}, reconstructed.family_groups["fam-rivera"]
            )
            self.assertEqual(
                {"es": 1.0},
                reconstructed.agents["nwl-101"].language_proficiencies,
            )
            self.assertIn("nwl-101", loaded_minds)
            self.assertIn("nwl-102", loaded_minds)

    def test_new_arrival_uses_own_language_in_autonomous_activation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "newland.db"
            with NewlandSimulation(
                path, cognition=ScriptedTestCognition()
            ) as simulation:
                simulation.admit_arrivals(self._family_profiles())
                produced = simulation.run(max_activations=2)
                produced.extend(simulation.run(max_activations=1))

            speech = next(
                event for event in produced if event.event_type == "SpeechUttered"
            )
            self.assertEqual(("nwl-101",), speech.actor_ids)
            self.assertEqual("es", speech.payload["language"])

    @staticmethod
    def _family_profiles() -> tuple[ArrivalProfile, ArrivalProfile]:
        return (
            ArrivalProfile(
                mind=AgentMind(
                    agent_id="nwl-101",
                    name="Lucía Rivera",
                    values=["cura", "lealtà"],
                    temperament=["attenta", "diretta"],
                ),
                native_language="es",
                arrival_memory="Ricordo una strada secondaria diventata silenziosa.",
                skills={"orientamento": 0.7, "cura_materiali": 0.4},
                family_group_id="fam-rivera",
            ),
            ArrivalProfile(
                mind=AgentMind(
                    agent_id="nwl-102",
                    name="Mateo Rivera",
                    values=["protezione", "onestà"],
                    temperament=["prudente", "paziente"],
                ),
                native_language="es",
                arrival_memory="Ricordo Lucía accanto a me lungo la deviazione.",
                skills={"orientamento": 0.5, "osservazione": 0.6},
                family_group_id="fam-rivera",
            ),
        )


    def test_live_simulation_detects_external_arrivals_dynamically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "newland.db"
            with NewlandSimulation(
                path, cognition=ScriptedTestCognition()
            ) as main_sim:
                main_sim.initialize()
                self.assertEqual(0, len(main_sim.minds))
                self.assertEqual([], main_sim.run(max_activations=1))

                with NewlandSimulation(
                    path, cognition=ScriptedTestCognition()
                ) as external_sim:
                    external_sim.admit_arrivals(self._family_profiles()[:1])

                produced = main_sim.run(max_activations=1)
                self.assertIn("nwl-101", main_sim.minds)
                self.assertEqual("Lucía Rivera", main_sim.minds["nwl-101"].name)
                self.assertGreaterEqual(len(produced), 1)


    @patch("newland_engine.arrival_factory.urlopen")
    def test_generative_arrival_factory(self, mock_urlopen) -> None:
        """Verify GenerativeArrivalFactory produces a valid ArrivalProfile (ADR-0011)."""
        mock_response = {
            "model": "test-model",
            "message": {
                "content": json.dumps({
                    "values": ["coraggio", "libertà"],
                    "temperament": ["vivace", "ribelle"],
                    "goals": ["esplorare ogni angolo della cittadina"],
                    "skills": {"corsa": 0.8, "sopravvivenza": 0.4},
                    "arrival_memory": "Stavo correndo lungo il fiume, l'acqua si è fatta stranamente silenziosa e mi sono ritrovato qui."
                })
            }
        }
        
        class MockResponseContextManager:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def read(self):
                return json.dumps(mock_response).encode("utf-8")
                
        mock_urlopen.return_value = MockResponseContextManager()

        factory = GenerativeArrivalFactory(model="test-model")
        profile, provenance = factory.generate(name="Marco Rossi", native_language="it")

        self.assertEqual("Marco Rossi", profile.mind.name)
        self.assertEqual(["coraggio", "libertà"], profile.mind.values)
        self.assertEqual(["vivace", "ribelle"], profile.mind.temperament)
        self.assertEqual(["esplorare ogni angolo della cittadina"], profile.mind.goals)
        self.assertEqual(0.8, profile.skills["corsa"])
        self.assertEqual("Stavo correndo lungo il fiume, l'acqua si è fatta stranamente silenziosa e mi sono ritrovato qui.", profile.arrival_memory)
        
        self.assertEqual("ollama", provenance.provider)
        self.assertEqual("test-model", provenance.model)
        self.assertEqual(1, provenance.attempts)


if __name__ == "__main__":
    unittest.main()
