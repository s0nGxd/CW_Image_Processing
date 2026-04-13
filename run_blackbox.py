import os
import sys
from myevalsdk.api import MaskQualityEvaluator
import config

def main():
    print("="*60)
    print("Semantic Evaluation SDK (Blackbox)")
    print("="*60)

    # Resolve absolute paths
    gt_dir = os.path.abspath(config.GROUND_TRUTH_DIR)
    masks_dir = os.path.abspath(config.STUDENT_MASKS_DIR)
    dataset_dir = os.path.abspath(config.DATASET_DIR)
    output_file = os.path.abspath(os.path.join(config.RESULTS_DIR, "blackbox_results.csv"))

    print(f"GT Directory:  {gt_dir}")
    print(f"Masks Dir:     {masks_dir}")
    print(f"Dataset Dir:   {dataset_dir}")
    print(f"Output CSV:    {output_file}")
    print("-" * 60)

    # Basic Pre-check
    if not os.path.exists(masks_dir):
        print(f"Error: Masks directory not found. Please run 'python batch_masks.py' first.")
        return

    # Initialize Evaluator
    # Note: The SDK naming requirement (original_name_mymask.png) 
    # must be matched by batch_masks.py (which it is).
    evaluator = MaskQualityEvaluator(
        gt_root=gt_dir,
        pred_root=masks_dir,
        image_root=dataset_dir,
        output_csv=output_file,
        verbose=True
    )

    print("Running evaluation... (this might take a while on CPU)")
    try:
        summary_text = evaluator.run()
        print("\n" + "="*60)
        print("EVALUATION SUMMARY")
        print("="*60)
        print(summary_text)
        print(f"\nDetailed results saved to: {output_file}")
    except Exception as e:
        print(f"\nEvaluation failed error: {e}")

if __name__ == "__main__":
    main()
