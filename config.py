import os

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))

# Inputs
CURATED_IMAGES_DIR = os.path.join(BASE_DIR, "001 - Input Images")

# Outputs
RESULTS_DIR = os.path.join(BASE_DIR, "Results 2026 IIP - Group015") # Output Folder
OUTPUT_PIPELINE_DIR = os.path.join(RESULTS_DIR, "002 - Image Processing Pipeline") # Image Processing Pipeline Folder
OUTPUT_IMAGES_DIR = os.path.join(RESULTS_DIR, "003 - Output Images") # Output Images Folder

# Pipeline Parameters
# Optimal tested params can be stored here
COLOR_SPACE_METHOD = 'HSV_S' # Test: 'HSV_S', 'LAB_A', 'GRAY_INV'
BLUR_KERNEL_SIZE = (9, 9)
MORPH_SE_SIZE = (5, 5)
MIN_AREA_THRESHOLD = 1000

# Classes
DIFFICULTIES = ["Easy", "Medium", "Hard"]
