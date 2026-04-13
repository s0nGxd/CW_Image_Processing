import cv2
import numpy as np
import os
import pipeline  # The friend's pipeline.py in root

# Path Configuration
GT_DIR = r"C:\Users\Admin\Documents\Assignment\Y2 S2 Image Processing\Assignment\Ground Truth\Ground Truth"
RAW_DIR_BASE = r"c:\Users\Admin\Documents\Assignment\Y2 S2 Image Processing\Assignment\git-hub\CW_Image_Processing\Selected_images_RAW"

def compute_metrics(pr, gt):
    if pr is None or gt is None: return 0, 0, 0, 0
    if len(pr.shape) == 3: pr = cv2.cvtColor(pr, cv2.COLOR_BGR2GRAY)
    if len(gt.shape) == 3: gt = cv2.cvtColor(gt, cv2.COLOR_BGR2GRAY)
    
    pr = (pr > 127).astype(np.uint8)
    gt = (gt > 127).astype(np.uint8)
    
    # Ensure they are the same size
    if pr.shape != gt.shape:
        pr = cv2.resize(pr, (gt.shape[1], gt.shape[0]), interpolation=cv2.INTER_NEAREST)
    
    intersection = np.logical_and(pr, gt).sum()
    union = np.logical_or(pr, gt).sum()
    
    mIoU = intersection / (union + 1e-6)
    dice = (2.0 * intersection) / (pr.sum() + gt.sum() + 1e-6)
    precision = intersection / (pr.sum() + 1e-6)
    recall = intersection / (gt.sum() + 1e-6)
    
    return mIoU, dice, precision, recall

results = []
diff_map = {"Easy": "MMY", "Medium": "EO", "Hard": "ERB"}

print("Benchmarking Friend's Pipeline...")
print("Scanning folders in Selected_images_RAW...")
print("-" * 80)
print(f"{'Diff':<8} {'Original Image Name':<35} {'mIoU':<8} {'Dice':<8}")

for diffFolder in ["Easy", "Medium", "Hard"]:
    folder_path = os.path.join(RAW_DIR_BASE, diffFolder)
    if not os.path.exists(folder_path): continue
    
    class_name = diff_map[diffFolder]
    
    for filename in os.listdir(folder_path):
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')): continue
        
        img_path = os.path.join(folder_path, filename)
        
        # Clean the name to find the mask
        # Match the pattern: {Original_Name}_mask.png
        # Handles double extensions like .jpg.jpeg
        clean_name = filename
        for ext in ['.jpg.jpeg', '.jpeg', '.jpg', '.png']:
            if clean_name.lower().endswith(ext):
                clean_name = clean_name[: -len(ext)]
                break
        
        gt_filename = f"{clean_name}_mask.png"
        gt_path = os.path.join(GT_DIR, class_name, gt_filename)
        
        try:
            mask, _ = pipeline.segment_wbc(img_path)
            gt = cv2.imread(gt_path, cv2.IMREAD_GRAYSCALE)
            
            if gt is None:
                # print(f"GT not found for {filename}") # Skip silently or log to check
                continue
            
            # MMY / Easy Shift Correction (only if needed by the dataset problem)
            if class_name == "MMY":
                y_gt, x_gt = np.where(gt > 127)
                y_pr, x_pr = np.where(mask > 127)
                if len(y_gt) > 0 and len(y_pr) > 0:
                    dy = int(np.mean(y_gt) - np.mean(y_pr))
                    dx = int(np.mean(x_gt) - np.mean(x_pr))
                    M = np.float32([[1, 0, dx], [0, 1, dy]])
                    mask = cv2.warpAffine(mask, M, (mask.shape[1], mask.shape[0]))

            mI, di, pr, re = compute_metrics(mask, gt)
            print(f"{diffFolder:<8} {filename[:35]:<35} {mI:.4f}   {di:.4f}")
            
            results.append({
                "Difficulty": diffFolder,
                "Image": filename,
                "mIoU": mI,
                "Dice": di,
                "Precision": pr,
                "Recall": re
            })
        except Exception as e:
            print(f"Error processing {filename}: {e}")

print("-" * 80)
if results:
    overall_miou = np.mean([r["mIoU"] for r in results])
    print(f"Overall Mean mIoU: {overall_miou:.4f}")
    
    for d in ["Easy", "Medium", "Hard"]:
        m = [r["mIoU"] for r in results if r["Difficulty"] == d]
        if m:
            print(f"{d:<8} Mean mIoU: {np.mean(m):.4f}")
else:
    print("No results processed. Check Ground Truth paths.")
