import argparse
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from peoples_priorities import create_app
from peoples_priorities.db import get_db, reset_db, init_db
from peoples_priorities.seed_data.generator import generate


def print_summary(summary):
    print(f"\nSeeded {summary['total']} grievances.\n")

    print("By ward:")
    for ward, count in sorted(summary["by_ward"].items()):
        print(f"  {ward:24s} {count}")

    print("\nBy category:")
    for cat, count in sorted(summary["by_category"].items()):
        print(f"  {cat:20s} {count}")

    print("\nBy status:")
    for status, count in sorted(summary["by_status"].items()):
        print(f"  {status:15s} {count}")

    print("\nBy urgency level:")
    for level, count in sorted(summary["by_urgency_level"].items()):
        print(f"  {level:10s} {count}")

    print(f"\nClusters formed this run: {summary['cluster_count']}")
    print(f"Total clustered rows: {summary['clustered_rows']}")
    print("Top clusters by size:")
    for cluster_id, size in summary["top_clusters"]:
        print(f"  {cluster_id}: {size} reports")


def main():
    parser = argparse.ArgumentParser(description="Seed the People's Priorities database with synthetic data.")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate tables before seeding.")
    parser.add_argument("-n", "--count", type=int, default=330, help="Number of grievances to generate.")
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed, so demo ticket IDs/wards stay stable across re-seeds.",
    )
    args = parser.parse_args()
    random.seed(args.seed)

    app = create_app()
    with app.app_context():
        db = get_db()
        if args.reset:
            reset_db()
        else:
            init_db()
        summary = generate(db, n=args.count)
        print_summary(summary)


if __name__ == "__main__":
    main()
