# CW_Image_Processing - Blood Cell Semantic Segmentation

This repository contains the image processing pipeline for the COMP2032 Coursework 2026. The objective is to use image processing techniques to segment pro-myelocytes (PMYs) from peripheral blood smears.

## Setup Requirements

Before running the code, ensure the following Python modules are installed:

```bash
pip install -r requirements.txt
```

*(Includes: `opencv-python`, `numpy`, `pillow`, `pandas`, `scikit-learn`)*

## Repository Structure

- `001 - Input Images/`: The 9 curated images selected for the conference paper (3 easy, 3 medium, 3 hard).
- `002 - Image Processing Pipeline/`: intermediate stages of the image processing pipeline are automatically generated and saved here.
- `003 - Output Images/`: The final results showing isolated segmented PMYs against a white background.
- `src/`: The core pipeline source code.
  - `pipeline.py`: Contains modular stages of the image processing components (Colour Space, Blur, Otsu Threshold, Morphology, Contours).
  - `evaluate.py`: Calculates metrics like `mIoU`, `Dice`, and `Precision`.
- `config.py`: Contains all parameters and paths (`COLOR_SPACE_METHOD`, kernel sizes, etc.), avoiding random magic numbers throughout the code.
- `main.py`: Generates the images for the coursework deliverables (segmentation part).
- `batch_masks.py`: Generates binary image masks for the entire 16k Naturalize Dataset (semantic part).

## Deliverable Generation

### 1. Segmentation Deliverable (Conference Paper Outputs)

To generate the final output images and test the segmentation pipeline:

```bash
python main.py
```

This will:
1. Apply the image processing pipeline on the 9 input images.
2. Calculate intersection over union (`mIoU`), `Dice`, and `Precision` metrics (if the Ground Truth directory is linked correctly in `config.py`).
3. Generate the required layout into the `Results 2026 IIP - GroupXXX` zip-ready folder!

### 2. Semantic Deliverable (`_mymask` Generation)

To generate the mask segmentations across the dataset (16,000 images) to be evaluated on Google Colab:

```bash
python batch_masks.py
```

## Future Work & Evaluation
- Adjust `COLOR_SPACE_METHOD` in `config.py`. Using `HSV_S` yields high accuracy on specific images but has weaknesses in specific datasets compared to `LAB_A` or `GRAY_INV`. 
- Further tuning of OpenCV morphological processing parameters could yield more precise precision and recall across all difficulty classes.