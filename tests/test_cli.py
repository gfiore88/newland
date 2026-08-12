from __future__ import annotations

import unittest

from newland_engine.cli import build_parser, run_continuously


class FakeContinuousSimulation:
    def __init__(self) -> None:
        self.activations = 0

    def run(self, *, max_activations: int = 8) -> list[object]:
        if max_activations != 1:
            raise AssertionError(
                "continuous runner must advance one activation at a time"
            )
        self.activations += 1
        return [{"activation": self.activations}]


class CliTests(unittest.TestCase):
    def test_continuous_mode_is_explicit_and_preserves_finite_default(self) -> None:
        parser = build_parser()

        finite = parser.parse_args(["run"])
        continuous = parser.parse_args(["run", "--continuous"])

        self.assertEqual(8, finite.activations)
        self.assertFalse(finite.continuous)
        self.assertTrue(continuous.continuous)

    def test_live_mode_defaults_to_agent_first_supervision(self) -> None:
        args = build_parser().parse_args(["live"])

        self.assertEqual("live", args.command)
        self.assertEqual(8, args.agent_weight)
        self.assertEqual("127.0.0.1", args.host)
        self.assertEqual(8765, args.port)

    def test_continuous_runner_stops_between_complete_activations(self) -> None:
        simulation = FakeContinuousSimulation()
        emitted: list[list[object]] = []

        count = run_continuously(
            simulation,
            emit=emitted.append,
            stop_requested=lambda: simulation.activations >= 3,
        )

        self.assertEqual(3, count)
        self.assertEqual(3, simulation.activations)
        self.assertEqual(
            [[{"activation": 1}], [{"activation": 2}], [{"activation": 3}]],
            emitted,
        )


if __name__ == "__main__":
    unittest.main()
