#!/usr/bin/env python
"""CLI runner script for Model Autopsy Experiment E003: Cross-Model Robustness Comparison (RQ5)."""

import argparse
from pathlib import Path
import sys

# Ensure ml_engine/src is on the module search path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ML_ENGINE_SRC = PROJECT_ROOT / "ml_engine" / "src"
if str(ML_ENGINE_SRC) not in sys.path:
    sys.path.insert(0, str(ML_ENGINE_SRC))

from model_autopsy.experiments.e003_runner import run_e003_experiment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Execute Model Autopsy Experiment E003: Cross-Model Robustness Comparison (RQ5).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "configs" / "experiments" / "e003.yaml",
        help="Path to YAML experiment configuration.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "experiments" / "E003",
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
    print("MODEL AUTOPSY — EXPERIMENT E003: CROSS-MODEL ROBUSTNESS COMPARISON (RQ5)")
    print(f"Config: {args.config}")
    print(f"Seeds: {args.seeds}")
    print(f"Output Directory: {args.output_dir}")
    print("=" * 78)

    try:
        result = run_e003_experiment(
            config_path=args.config,
            seeds=args.seeds,
            output_dir=args.output_dir,
        )

        print("\n[SUCCESS] E003 cross-model evaluation completed successfully.")
        print(f"Output directory: {result['output_dir']}")
        print("\nGenerated Artifacts:")
        for k, v in result["artifacts"].items():
            print(f"  - {k}: {v}")

        print("\n" + "=" * 78)
        print("MODEL SUMMARY AT WORST-CASE NOISE SEVERITY (s = 0.30):")
        print("=" * 78)
        for model_id, corr_dict in result["results_by_model"].items():
            print(f"\nModel: {model_id.upper()}")
            for corr_id, res in corr_dict.items():
                b_rec = res.severity_aggregates[0]
                worst_rec = res.severity_aggregates[-1]
                mean_b = f"s*={res.mean_observed_boundary:.2f}" if res.mean_observed_boundary is not None else "None"
                indiv_b = f"s*={res.earliest_individual_boundary:.2f}" if res.earliest_individual_boundary is not None else "None"
                print(
                    f"  - {corr_id:25s}: Baseline={b_rec.macro_f1.mean:.4f} -> Worst={worst_rec.macro_f1.mean:.4f} "
                    f"(Drop={worst_rec.absolute_degradation_pp.mean:+.2f}pp) | MeanBoundary={mean_b:10s} | IndivBoundary={indiv_b}"
                )
        print("=" * 78)
        return 0

    except Exception as exc:
        print(f"\n[ERROR] E003 execution failed: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
