import os
import cv2
import numpy as np
import shutil
import config
from src import utils, pipeline, evaluate

def format_output_name(filename, difficulty, idx):
    # Extracts base name and formats e.g. "MMY 2K-PBC Train (61)-easy_1.jpg"
    base = filename.split('.')[0]
    return f"{base}-{difficulty.lower()}_{idx}.jpg"

def main():
    print("="*60)
    print("COMP2032 Image Processing Pipeline")
    print("="*60)
    print("Initializing submission directory...")
    # Clean/Reset the final Results folder at the start
    utils.clear_dir(config.RESULTS_DIR)
    
    # 1. Copy Input Images (001) to the submission folder immediately
    dest_001 = os.path.join(config.RESULTS_DIR, "001 - Input Images")
    if os.path.exists(config.CURATED_IMAGES_DIR):
        shutil.copytree(config.CURATED_IMAGES_DIR, dest_001)
    
    # Setup subdirectories for the pipeline and outputs (now inside RESULTS_DIR)
    utils.init_output_dirs(config.OUTPUT_IMAGES_DIR, config.OUTPUT_PIPELINE_DIR)
    
    results = []
    
    for difficulty in config.DIFFICULTIES:
        input_dir = os.path.join(config.CURATED_IMAGES_DIR, difficulty)
        output_diff_dir = os.path.join(config.OUTPUT_IMAGES_DIR, difficulty)
        
        if not os.path.exists(input_dir):
            print(f"Warning: Input directory {input_dir} not found.")
            continue
            
        images = [f for f in os.listdir(input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        images.sort()
        
        print(f"\nProcessing [{difficulty}] images ({len(images)} found)...")
        
        for i, img_name in enumerate(images, 1):
            img_path = os.path.join(input_dir, img_name)
            print(f"  [{i}/{len(images)}] {img_name}")
            
            # Load Image
            img_rgb = utils.load_image(img_path)
            if img_rgb is None:
                print(f"    Failed to load {img_name}")
                continue
            
            # Setup pipeline stages directory
            base_name = img_name.split('.')[0]
            stages_dir = os.path.join(config.OUTPUT_PIPELINE_DIR, base_name)
            
            # Run pipeline
            output_img, final_mask = pipeline.run_pipeline(
                img_rgb, 
                method=config.COLOR_SPACE_METHOD,
                blur_k=config.BLUR_KERNEL_SIZE,
                morph_se=config.MORPH_SE_SIZE,
                min_area=config.MIN_AREA_THRESHOLD,
                save_stages_dir=stages_dir
            )
            
            # Save Output Image
            out_filename = format_output_name(img_name, difficulty, i)
            out_path = os.path.join(output_diff_dir, out_filename)
            utils.save_image(output_img, out_path)
            print(f"    -> Saved output to {out_filename}")

            # Evaluate using Ground Truth
            try:
                class_name = base_name.split(' ')[0]
                # User note: MMY masks for 'Easy' are located in the 'PMY' folder
                gt_folder = "PMY" if "MMY" in class_name else class_name

                # GT name format is "*_mask.png"
                gt_path = os.path.join(config.GROUND_TRUTH_DIR, gt_folder, f"{base_name}_mask.png")

                if os.path.exists(gt_path):
                    gt_img = cv2.imread(gt_path, cv2.IMREAD_GRAYSCALE)
                    if gt_img is not None:
                        metrics = evaluate.compute_metrics(final_mask, gt_img)
                        metrics['Image'] = base_name
                        metrics['Difficulty'] = difficulty
                        results.append(metrics)
                        print(f"    -> GT Evaluated: mIoU={metrics['mIoU']:.4f}, Dice={metrics['Dice']:.4f}")
                    else:
                        print(f"    -> GT mask could not be loaded at {gt_path}")
                else:
                    print(f"    -> GT mask not found at {gt_path}")
            except Exception as e:
                print(f"    Error finding/evaluating GT: {e}")

    evaluate.print_summary(results)
    
    print(f"\nCompleted! All deliverables are ready in the folder: {os.path.basename(config.RESULTS_DIR)}")

if __name__ == "__main__":
    main()
