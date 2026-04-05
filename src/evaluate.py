import numpy as np
import pandas as pd

def compute_metrics(pred_mask, gt_mask):
    """
    Computes mIoU, Dice, Precision, Recall, Accuracy.
    Mask values should be scaled around 0 and 255.
    """
    pred = (pred_mask > 127).astype(np.uint8)
    gt = (gt_mask > 127).astype(np.uint8)
    
    intersection = np.sum(pred * gt)
    union = np.sum(pred) + np.sum(gt) - intersection
    
    tp = intersection
    fp = np.sum(pred) - tp
    fn = np.sum(gt) - tp
    tn = np.sum((1 - pred) * (1 - gt))
    
    iou = tp / (union + 1e-6)
    dice = (2 * tp) / (np.sum(pred) + np.sum(gt) + 1e-6)
    precision = tp / (tp + fp + 1e-6)
    recall = tp / (tp + fn + 1e-6)
    accuracy = (tp + tn) / (pred.size + 1e-6)
    
    return {
        'mIoU': iou,
        'Dice': dice,
        'Precision': precision,
        'Recall': recall,
        'Accuracy': accuracy
    }

def print_summary(results_list):
    if not results_list:
        print("No evaluation results to summarize.")
        return
        
    df = pd.DataFrame(results_list)
    cols = ['Difficulty', 'Image', 'mIoU', 'Dice', 'Precision', 'Recall', 'Accuracy']
    df = df[cols]
    
    print("\n" + "="*70)
    print("EVALUATION SUMMARY")
    print("="*70)
    print(df.to_string(index=False))
    print("-" * 70)
    
    mean_metrics = df.drop(columns=['Image']).groupby('Difficulty').mean()
    print("MEAN METRICS BY DIFFICULTY:")
    print(mean_metrics.to_string())
    print("-" * 70)
    
    overall_mean = df[['mIoU', 'Dice', 'Precision', 'Recall', 'Accuracy']].mean()
    print("OVERALL MEAN METRICS:")
    for metric, val in overall_mean.items():
        print(f"  {metric}: {val:.4f}")
        
    print("="*70 + "\n")
