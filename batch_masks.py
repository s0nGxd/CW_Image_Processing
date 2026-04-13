import os
import cv2
import config
from src import utils, pipeline

def batch_process():
    """
    Processes all 16K dataset images to generate `_mymask.png` for semantic evaluation.
    """
    print("="*60)
    print("Batch Processing for Semantic Part")
    print("="*60)
    
    utils.ensure_dir(config.STUDENT_MASKS_DIR)
    
    if not os.path.exists(config.DATASET_DIR):
        print(f"Error: Dataset directory not found at {config.DATASET_DIR}")
        return
        
    classes = [d for d in os.listdir(config.DATASET_DIR) if os.path.isdir(os.path.join(config.DATASET_DIR, d)) and not d.startswith('.')]
    classes.sort()
    
    print(f"Found {len(classes)} classes to process. Output directory: {config.STUDENT_MASKS_DIR}")
    
    total_processed = 0
    total_errors = 0
    
    for cls in classes:
        cls_dir = os.path.join(config.DATASET_DIR, cls)
        # Assuming we only need to process PMY for semantic part, or all?
        # The prompt says: "generate mask of the PMY ... feed into semantic eval"
        # The SDK expects all masks.
        
        images = [f for f in os.listdir(cls_dir) if f.lower().endswith('.jpg')] # Using .jpg to avoid duplicates (.png)
        print(f"Processing class [{cls}] - {len(images)} images")
        
        for i, img_name in enumerate(images):
            img_path = os.path.join(cls_dir, img_name)
            
            try:
                img_rgb = utils.load_image(img_path)
                if img_rgb is None:
                    total_errors += 1
                    continue
                    
                # Run pipeline (no need to save stages)
                _, final_mask = pipeline.run_pipeline(
                    img_rgb, 
                    method=config.COLOR_SPACE_METHOD,
                    blur_k=config.BLUR_KERNEL_SIZE,
                    morph_se=config.MORPH_SE_SIZE,
                    min_area=config.MIN_AREA_THRESHOLD,
                    save_stages_dir=None
                )
                
                # Format required by SDK: original_name_plus_mymask  "image_1_mymask.png"
                base_name = img_name.split('.')[0]
                mask_filename = f"{base_name}_mymask.png"
                mask_path = os.path.join(config.STUDENT_MASKS_DIR, mask_filename)
                
                # Save just the binary mask
                utils.save_image(final_mask, mask_path, is_rgb=False)
                total_processed += 1
                
                if (i + 1) % 500 == 0:
                    print(f"  ... processed {i+1} / {len(images)} for {cls}")
                    
            except Exception as e:
                print(f"Error processing {img_path}: {e}")
                total_errors += 1
                
    print("\nBatch processing complete!")
    print(f"Successfully generated {total_processed} masks.")
    if total_errors > 0:
        print(f"Failed on {total_errors} images.")

if __name__ == "__main__":
    # Note: Running this takes a long time for 16K images. 
    # Use with caution or modify to do a subset!
    batch_process()
