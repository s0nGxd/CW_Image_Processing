import os

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(os.path.dirname(BASE_DIR)) # Go up two levels from src to get out of git-hub

# Inputs
CURATED_IMAGES_DIR = os.path.join(BASE_DIR, "001 - Input Images")
DATASET_DIR = os.path.join(PARENT_DIR, "Naturalize Dataset", "Naturalize Dataset")
GROUND_TRUTH_DIR = os.path.join(PARENT_DIR, "Ground Truth", "Ground Truth")

# Outputs
OUTPUT_PIPELINE_DIR = os.path.join(BASE_DIR, "002 - Image Processing Pipeline")
OUTPUT_IMAGES_DIR = os.path.join(BASE_DIR, "003 - Output Images")
RESULTS_DIR = os.path.join(BASE_DIR, "Results 2026 IIP - GroupXXX") # Output folder specifically requested
STUDENT_MASKS_DIR = os.path.join(BASE_DIR, "student_mask")

# Pipeline Parameters
# Optimal tested params can be stored here
COLOR_SPACE_METHOD = 'HSV_S' # Test: 'HSV_S', 'LAB_A', 'GRAY_INV'
BLUR_KERNEL_SIZE = (9, 9)
MORPH_SE_SIZE = (5, 5)
MIN_AREA_THRESHOLD = 1000

# Classes
DIFFICULTIES = ["Easy", "Medium", "Hard"]
