import os
import cv2
import numpy as np
import shutil
import config
from src import utils, pipeline

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

    print(f"\nCompleted! All deliverables are ready in the folder: {os.path.basename(config.RESULTS_DIR)}")

if __name__ == "__main__":
    main()
