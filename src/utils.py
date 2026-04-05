import os
import cv2
import numpy as np
import shutil

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def load_image(filepath):
    """Loads an image in RGB format."""
    img = cv2.imread(filepath)
    if img is None:
        return None
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

def save_image(img, filepath, is_rgb=True):
    """Saves an image to disk."""
    ensure_dir(os.path.dirname(filepath))
    if len(img.shape) == 3 and is_rgb:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    cv2.imwrite(filepath, img)

def init_output_dirs(output_images_dir, pipeline_dir):
    for diff in ["Easy", "Medium", "Hard"]:
        ensure_dir(os.path.join(output_images_dir, diff))
    ensure_dir(pipeline_dir)

def clear_dir(dir_path):
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.makedirs(dir_path)
