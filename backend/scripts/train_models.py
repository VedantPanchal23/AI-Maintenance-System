"""
CLI script to train all ML models.

Usage:
    python -m scripts.train_models
    python -m scripts.train_models --algorithm xgboost
"""

import argparse
import json
import sys

from app.ml.training import TrainingPipeline, MODEL_CONFIGS


def main():
    parser = argparse.ArgumentParser(description="Train predictive maintenance ML models")
    parser.add_argument(
        "--algorithm",
        choices=list(MODEL_CONFIGS.keys()) + ["all"],
        default="all",
        help="Algorithm to train (default: all)",
    )
    parser.add_argument(
        "--data", type=str, default=None,
        help="Path to CSV data file (default: synthetic data)",
    )
    parser.add_argument(
        "--test-size", type=float, default=0.2,
        help="Test set ratio (default: 0.2)",
    )
    args = parser.parse_args()

    pipeline = TrainingPipeline()

    print("=" * 60)
    print("AI Predictive Maintenance — Model Training")
    print("=" * 60)

    if args.algorithm == "all":
        results = pipeline.train_all_models(args.data)
        print(f"\n{'Algorithm':<20} {'F1':<8} {'Precision':<10} {'Recall':<8} {'AUC':<8} {'Time(s)':<8}")
        print("-" * 70)
        for r in results:
            if "metrics" in r:
                m = r["metrics"]
                print(
                    f"{r['algorithm']:<20} {m['f1']:<8.4f} {m['precision']:<10.4f} "
                    f"{m['recall']:<8.4f} {m['auc_roc']:<8.4f} {r['training_duration_seconds']:<8.1f}"
                )
            else:
                print(f"{r['algorithm']:<20} FAILED: {r.get('error', 'Unknown error')}")

        # Pick best model
        best = max(
            [r for r in results if "metrics" in r],
            key=lambda r: r["metrics"]["f1"],
        )
        print(f"\n✓ Best model: {best['algorithm']} (F1={best['metrics']['f1']:.4f})")
        print(f"  Saved to: {best['model_path']}")
    else:
        result = pipeline.train_model(args.algorithm, args.data, args.test_size)
        print(f"\nAlgorithm: {result['algorithm']}")
        print(f"Version: {result['version']}")
        print(f"Training samples: {result['training_samples']}")
        print(f"Test samples: {result['test_samples']}")
        print(f"Duration: {result['training_duration_seconds']:.1f}s")
        print(f"\nMetrics:")
        for key, value in result["metrics"].items():
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")


if __name__ == "__main__":
    main()
