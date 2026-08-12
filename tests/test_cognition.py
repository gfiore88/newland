from __future__ import annotations

import unittest

from helpers import ScriptedTestCognition, UnavailableTestCognition
from newland_engine.cognition import CognitionContext, GenerativeCognitionPool
from newland_engine.models import AgentMind, MaterialAgentState


def context() -> CognitionContext:
    mind = AgentMind(
        agent_id="nwl-test",
        name="Test Newlander",
        values=["autonomia"],
        temperament=["vigile"],
    )
    return CognitionContext(
        mind=mind,
        material_state=MaterialAgentState("nwl-test", "Test Newlander", "village"),
        observations=(),
        nearby_agents=(("nwl-other", "Other Newlander"),),
        activation_reason="test generative failover",
    )


class GenerativeCognitionPoolTests(unittest.TestCase):
    def test_failover_uses_another_generative_provider(self) -> None:
        pool = GenerativeCognitionPool(
            [UnavailableTestCognition(), ScriptedTestCognition()]
        )
        result = pool.decide(context())
        self.assertEqual("test-double", result.provider)
        self.assertEqual("speak", result.intention.action_type)

    def test_pool_without_provider_is_invalid(self) -> None:
        with self.assertRaises(ValueError):
            GenerativeCognitionPool([])


if __name__ == "__main__":
    unittest.main()
