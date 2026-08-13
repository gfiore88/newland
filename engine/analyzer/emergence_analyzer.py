import argparse
import json
import sqlite3
from collections import defaultdict
from pathlib import Path


def analyze_emergence(db_path: str) -> None:
    if not Path(db_path).exists():
        print(f"Error: Database {db_path} does not exist.")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Metrics
    interactions = defaultdict(int)  # (agent_a, agent_b) -> count
    speakers = defaultdict(int)
    activities = defaultdict(int)
    cooperations = defaultdict(int)

    rows = conn.execute("SELECT event_type, actor_ids, payload FROM events").fetchall()

    for row in rows:
        event_type = row["event_type"]
        actor_ids = json.loads(row["actor_ids"])
        payload = json.loads(row["payload"])

        if event_type == "AgentSpoke":
            if actor_ids:
                speakers[actor_ids[0]] += 1
            target_id = payload.get("target_id")
            if target_id and actor_ids:
                pair = tuple(sorted([actor_ids[0], target_id]))
                interactions[pair] += 1

        elif event_type == "SocialCooperationCompleted":
            initiator = payload.get("proposer_id")
            target = payload.get("target_id")
            if initiator and target:
                pair = tuple(sorted([initiator, target]))
                interactions[pair] += 2  # Cooperations count more for relationship strength
                cooperations[pair] += 1

        elif event_type == "ActivityPerformed":
            if actor_ids:
                activities[actor_ids[0]] += 1
                
        elif event_type == "ItemTransferred":
            from_id = payload.get("from_id")
            to_id = payload.get("to_id")
            if from_id and to_id:
                pair = tuple(sorted([from_id, to_id]))
                interactions[pair] += 1

    print("=== Emergence Analyzer Report ===")
    print(f"Total Events Analyzed: {len(rows)}\n")

    print("--- Social Interactions (Top Pairs) ---")
    sorted_interactions = sorted(interactions.items(), key=lambda x: x[1], reverse=True)
    for pair, count in sorted_interactions[:10]:
        print(f"{pair[0]} <-> {pair[1]}: {count} interactions")

    print("\n--- Social Cooperations (Top Pairs) ---")
    sorted_cooperations = sorted(cooperations.items(), key=lambda x: x[1], reverse=True)
    for pair, count in sorted_cooperations[:10]:
        print(f"{pair[0]} <-> {pair[1]}: {count} cooperations")

    print("\n--- Most Active Speakers ---")
    sorted_speakers = sorted(speakers.items(), key=lambda x: x[1], reverse=True)
    for agent, count in sorted_speakers[:5]:
        print(f"{agent}: {count} speech acts")

    print("\n--- Most Active Workers ---")
    sorted_activities = sorted(activities.items(), key=lambda x: x[1], reverse=True)
    for agent, count in sorted_activities[:5]:
        print(f"{agent}: {count} activities")
        
    # Analyze if there are emergent groups (cliques)
    print("\n--- Emergent Social Groups ---")
    print("Graph analysis for cliques requires networkx, but based on top pairs:")
    if sorted_interactions:
        print("Strongest bond exists between: ", sorted_interactions[0][0])
    else:
        print("No significant social bonds detected yet.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze Newland EventStore for emergent social structures.")
    parser.add_argument("--db", type=str, required=True, help="Path to the sqlite EventStore database.")
    args = parser.parse_args()
    
    analyze_emergence(args.db)
