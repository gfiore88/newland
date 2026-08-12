from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from helpers import ScriptedTestCognition
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
                simulation.admit_arrivals((self._family_profiles()[0],))
                produced = simulation.run(max_activations=1)

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


if __name__ == "__main__":
    unittest.main()
