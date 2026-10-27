#!/usr/bin/env python
"""CLI runner script for Model Autopsy Experiment E006: Systematic Distribution Shift (RQ6)."""

import argparse
from pathlib import Path
import sys

# Ensure ml_engine/src is on the module search path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ML_ENGINE_SRC = PROJECT_ROOT / "ml_engine" / "src"
if str(ML_ENGINE_SRC) not in sys.path:
    sys.path.insert(0, str(ML_ENGINE_SRC))

from model_autopsy.experiments.e006_runner import run_e006_experiment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Execute Model Autopsy Experiment E006: Systematic Distribution Shift (RQ6).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "configs" / "experiments" / "e006.yaml",
        help="Path to YAML experiment configuration.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "experiments" / "E006",
        help="Destination directory for output artifacts.",
    )
    parser.add_argument(
        "--seeds",
        nargs="+",
        type=int,
        default=[42, 123, 456, 789, 1011],
        help="Random seeds for 5-seed statistical evaluation.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print("=" * 78)
    print("MODEL AUTOPSY — EXPERIMENT E006: SYSTEMATIC DISTRIBUTION SHIFT (RQ6)")
    print(f"Config: {args.config}")
    print(f"Seeds: {args.seeds}")
    print(f"Output Directory: {args.output_dir}")
    print("=" * 78)

    try:
        result = run_e006_experiment(
            config_path=args.config,
            seeds=args.seeds,
            output_dir=args.output_dir,
        )

        total_cells = result.get("total_evaluation_cells", 0)
        print("\n[SUCCESS] E006 distribution shift experiment completed successfully.")
        print(f"  - Total evaluation cells: {total_cells}")
        print(f"  - Artifacts generated in: {result['output_dir']}")
        for k, v in result["artifacts"].items():
            print(f"    * {k} -> {v}")
        return 0

    except Exception as exc:
        print(f"\n[ERROR] E006 experiment failed: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
