#!/usr/bin/env python3
"""CLI runner script for Experiment E001:

Robustness of Random Forest under Additive Gaussian Noise on the Iris Benchmark.

Usage:
    python scripts/experiments/run_e001.py
    python scripts/experiments/run_e001.py --seed 42 --config configs/experiments/e001.yaml
"""

import argparse
from pathlib import Path
import sys

# Ensure ml_engine/src is on the Python path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ML_ENGINE_SRC = REPO_ROOT / "ml_engine" / "src"
if str(ML_ENGINE_SRC) not in sys.path:
    sys.path.insert(0, str(ML_ENGINE_SRC))

try:
    from model_autopsy.experiments.e001_runner import run_e001_experiment, run_e001_multiseed_experiment
except ImportError as exc:
    print(f"[FATAL ERROR] Failed to import model_autopsy from {ML_ENGINE_SRC}: {exc}", file=sys.stderr)
    sys.exit(1)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Execute Model Autopsy Experiment E001 (Random Forest on Iris under Gaussian Noise)."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO_ROOT / "configs" / "experiments" / "e001.yaml",
        help="Path to experiment configuration YAML file.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Model and noise PRNG seed (default: 42 for development validation).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Destination directory for output artifacts.",
    )
    parser.add_argument(
        "--multi-seed",
        action="store_true",
        help="Execute the full 5-seed research suite [42, 123, 456, 789, 1011].",
    )

    args = parser.parse_args()

    print("=" * 78)
    print("MODEL AUTOPSY — EXPERIMENT E001 RUNNER")
    print("Gaussian Noise Robustness Evaluation of Random Forest on Iris")
    print("=" * 78)

    if args.multi_seed:
        out_dir = args.output_dir or (REPO_ROOT / "artifacts" / "experiments" / "E001_multi_seed")
        print("[MODE] Multi-Seed Research Evaluation Suite (R=5 Seeds)")
        print(f"[CONFIG] Protocol configuration: {args.config}")
        print(f"[DESTINATION] Artifacts directory: {out_dir}")

        try:
            res = run_e001_multiseed_experiment(
                config_path=args.config,
                output_dir=out_dir,
            )
            m_res = res["multi_seed_result"]

            print("\n" + "-" * 78)
            print("MULTI-SEED STATISTICAL AGGREGATE TABLE (R=5 Seeds)")
            print("-" * 78)
            print(
                f"{'Severity':<9} | {'Mean Macro-F1':<13} | {'SEM':<9} | {'95% Student t CI':<19} | "
                f"{'Mean Acc':<9} | {'Failures':<8} | {'Status':<6}"
            )
            print("-" * 78)
            for agg in m_res.severity_aggregates:
                s = agg.severity
                f1_m = agg.macro_f1.mean
                sem = agg.macro_f1.sem
                ci_str = f"[{agg.macro_f1.ci_lower:.3f}, {agg.macro_f1.ci_upper:.3f}]"
                acc_m = agg.accuracy.mean
                fail_s = f"{agg.failure_count}/{agg.n_successful_runs}"
                stat = "FAIL" if agg.is_mean_failed else "PASS"
                print(
                    f"{s:<9.2f} | {f1_m:<13.4f} | ±{sem:<8.4f} | {ci_str:<19} | "
                    f"{acc_m:<9.4f} | {fail_s:<8} | {stat:<6}"
                )

            print("\n" + "-" * 78)
            print("PER-SEED FAILURE BOUNDARIES BREAKDOWN")
            print("-" * 78)
            for s_val, b_val in m_res.per_seed_boundaries.items():
                b_s = f"s* = {b_val:.2f}" if b_val is not None else "s* > 0.30 (Not observed)"
                print(f"  • Seed {s_val:<5} -> Observed Boundary: {b_s}")

            mean_b = m_res.mean_observed_boundary
            mb_str = f"s* = {mean_b:.2f}" if mean_b is not None else "Not observed (s* > 0.30)"
            print(f"\nMean Performance Failure Boundary: {mb_str}")
            earliest_b = m_res.earliest_individual_boundary
            eb_str = f"s* = {earliest_b:.2f}" if earliest_b is not None else "None"
            print(f"Earliest Individual Run Boundary:  {eb_str}")
            print(f"Mandated Caption:                  \"{m_res.boundary_caption}\"")

            print("\n" + "-" * 78)
            print("GENERATED MULTI-SEED ARTIFACTS")
            print("-" * 78)
            for name, path in res["artifacts"].items():
                print(f"  • {name:<30} -> {path}")

            print("\n[SUCCESS] Multi-seed research evaluation executed and verified successfully.")
            return 0
        except Exception as exc:
            print(f"\n[FATAL ERROR] Multi-seed evaluation failed: {exc}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return 1

    out_dir = args.output_dir or (REPO_ROOT / "artifacts" / "experiments" / "E001")
    print(f"[CONFIG] Loading protocol configuration from: {args.config}")
    print(f"[SETUP] Execution seed: {args.seed} (Development Validation Run)")
    print(f"[SETUP] Artifacts destination: {out_dir}")

    try:
        result = run_e001_experiment(
            config_path=args.config,
            seed=args.seed,
            output_dir=out_dir,
        )

        print("\n" + "-" * 76)
        print("EXPERIMENT EXECUTION SUMMARY")
        print("-" * 76)
        print(f"Status:               {result['status'].upper()}")
        print(f"Experiment ID:        {result['experiment_id']}")
        print(f"Baseline Macro-F1:    {result['baseline_macro_f1']:.4f}")
        print(f"Baseline Accuracy:    {result['baseline_accuracy']:.4f}")

        fb = result["failure_boundary"]
        obs_b = fb.get("observed_boundary")
        b_str = f"s* = {obs_b:.2f}" if obs_b is not None else "Not observed (s* > 0.30)"
        print(f"Observed Boundary:    {b_str}")
        print(f"Boundary Caption:     \"{fb.get('boundary_caption')}\"")

        print("\n" + "-" * 76)
        print("SEVERITY SWEEP DEGRADATION TABLE")
        print("-" * 76)
        print(f"{'Severity':<10} | {'Macro-F1':<10} | {'Accuracy':<10} | {'Abs Drop (pp)':<14} | {'Status':<8}")
        print("-" * 62)
        for r in result["severity_records"]:
            stat = "FAIL" if r["is_failed"] else "PASS"
            print(
                f"{r['severity']:<10.2f} | {r['macro_f1']:<10.4f} | {r['accuracy']:<10.4f} | "
                f"{r['absolute_degradation_pp']:<+14.2f} | {stat:<8}"
            )

        print("\n" + "-" * 76)
        print("GENERATED ARTIFACTS")
        print("-" * 76)
        for name, path in result["artifacts"].items():
            print(f"  • {name:<26} -> {path}")

        print("\n[SUCCESS] Experiment E001 executed and verified successfully.")
        return 0

    except Exception as exc:
        print(f"\n[FATAL ERROR] Experiment failed with exception: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
