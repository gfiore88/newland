from __future__ import annotations

import threading
import unittest

from newland_engine.inference import InferenceAdmission


class InferenceAdmissionTests(unittest.TestCase):
    def test_serializes_all_workloads_and_records_health(self) -> None:
        admission = InferenceAdmission(agent_weight=2)
        release = threading.Event()
        agent_started = threading.Event()
        order: list[str] = []

        def agent_job() -> None:
            def operation() -> None:
                order.append("agent-start")
                agent_started.set()
                release.wait(timeout=2)
                order.append("agent-end")

            admission.run("agent", operation)

        def chronicle_job() -> None:
            admission.run("chronicle", lambda: order.append("chronicle"))

        agent = threading.Thread(target=agent_job)
        chronicle = threading.Thread(target=chronicle_job)
        agent.start()
        self.assertTrue(agent_started.wait(timeout=1))
        chronicle.start()
        self.assertEqual("agent", admission.snapshot().in_flight)
        self.assertEqual(1, admission.snapshot().chronicle_queue_depth)
        release.set()
        agent.join(timeout=2)
        chronicle.join(timeout=2)

        self.assertEqual(["agent-start", "agent-end", "chronicle"], order)
        snapshot = admission.snapshot()
        self.assertEqual(1, snapshot.completed_agent_jobs)
        self.assertEqual(1, snapshot.completed_chronicle_jobs)
        self.assertIsNone(snapshot.in_flight)

    def test_waiting_chronicler_runs_after_weighted_agent_round(self) -> None:
        admission = InferenceAdmission(agent_weight=2)
        first_release = threading.Event()
        first_started = threading.Event()
        order: list[str] = []

        def run(label: str, workload: str, *, block: bool = False) -> None:
            def operation() -> None:
                order.append(label)
                if block:
                    first_started.set()
                    first_release.wait(timeout=2)

            admission.run(workload, operation)  # type: ignore[arg-type]

        first = threading.Thread(target=run, args=("agent-1", "agent"), kwargs={"block": True})
        chronicle = threading.Thread(target=run, args=("chronicle", "chronicle"))
        second = threading.Thread(target=run, args=("agent-2", "agent"))
        third = threading.Thread(target=run, args=("agent-3", "agent"))
        first.start()
        self.assertTrue(first_started.wait(timeout=1))
        chronicle.start()
        second.start()
        third.start()
        first_release.set()
        for thread in (first, chronicle, second, third):
            thread.join(timeout=2)

        self.assertEqual("agent-1", order[0])
        self.assertEqual("chronicle", order[2])
        self.assertEqual({"agent-2", "agent-3"}, {order[1], order[3]})
        self.assertEqual(3, admission.snapshot().completed_agent_jobs)

    def test_failure_releases_slot_without_becoming_fallback(self) -> None:
        admission = InferenceAdmission()

        with self.assertRaisesRegex(RuntimeError, "provider failed"):
            admission.run(
                "agent", lambda: (_ for _ in ()).throw(RuntimeError("provider failed"))
            )

        self.assertEqual("next", admission.run("chronicle", lambda: "next"))
        snapshot = admission.snapshot()
        self.assertEqual(1, snapshot.failed_agent_jobs)
        self.assertEqual(1, snapshot.completed_chronicle_jobs)


if __name__ == "__main__":
    unittest.main()
