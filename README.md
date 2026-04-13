# Blood Cell Semantic Segmentation Pipeline
## COMP2032 Image Processing Coursework 2026

---

## 1. Intro
This repository contains a robust, adaptive image processing pipeline designed to segment white blood cells (specifically pro-myelocytes) from peripheral blood smear microscopic images. The project aims to achieve high-accuracy semantic segmentation across varying difficulty levels (Easy, Medium, Hard) as defined by the Naturalize Dataset, facilitating downstream automated hematological analysis.

## 2. Segmentation Strategy
Unlike rigid single-filter pipelines, this system employs an **Adaptive Multi-Strategy Selection Engine**. 

For every input image, the pipeline concurrently executes **10 distinct image processing strategies** (including HSV Saturation, CIELAB A* channel, Euclidean Color Distance, and K-Means Clustering). Each resulting candidate mask is automatically evaluated by a **Quality Heuristic Scorer** that measures:
- **Solidity**: To ensure a single non-fragmented cell mass.
- **Circularity**: To match the biological expectation of round/oval cells.
- **Area Ratio**: To filter out small noise and large background artifacts.
- **Centeredness**: To prioritize the primary cell usually positioned at the image center.

The highest-scoring strategy is automatically selected as the final output, ensuring the pipeline remains robust across different lighting conditions and cell morphologies.

## 3. Method
The winning strategy's path typically follows a 5-stage refinement process:
1. **Channel Extraction**: Isolating the most discriminative color channel (e.g., Saturation in HSV space).
2. **Noise Reduction**: Applying **Bilateral Filtering** to smooth background grain while preserving sharp cell boundaries.
3. **Thresholding**: Using **Otsu’s Bimodal Method** or **Adaptive Gaussian Thresholding** to create a binary mask.
4. **Morphological Cleanup**: Utilizing Elliptical Opening and Closing operations, followed by **Flood-Fill Hole Closure** to capture pale cytoplasm regions.
5. **GrabCut Refinement**: Initializing a GrabCut algorithm with the coarse mask to leverage color distribution and achieve pixel-perfect edge alignment.

## 4. Output
Running the pipeline generates the following deliverables:
- **Segmentation Masks**: Binary `.png` files (0/255) for both the curated 9 images and the full dataset.
- **Segmented Visuals**: JPG images showing the isolated cell against a clean white background.
- **Evaluation Reports**: A console summary and saved text file containing `mIoU`, `Dice Coefficient`, `Precision`, and `Recall` metrics.
- **Stage Visualizations**: (Optional) Step-by-step images of the pipeline (01_channel, 02_blurred, etc.) for debugging.

## 5. Setup Requirements
The pipeline requires Python 3.x and the following core dependencies:
- **OpenCV** (`opencv-python`): Core image processing and GrabCut.
- **NumPy**: Matrix operations and mask manipulation.
- **Pandas**: Evaluation result logging.

To install dependencies:
```bash
pip install opencv-python numpy pandas
```

## 6. Deliverable Generation
To execute the pipeline on the 9 curated "Conference Paper" images and generate the submission-ready folder:

```bash
python main.py
```

### Submission Pack
The script automatically organizes all required files into a folder named:
`Results 2026 IIP - GroupXXX`

This folder includes:
- `002 - Image Processing Pipeline/`: Showing consistent processing stages.
- `003 - Output Images/`: Final segmented cells on white backgrounds.
- `final_metrics.txt`: The definitive performance record for the report.

For a deeper dive into the algorithm's mathematics, see [Technique.md](./Technique.md).
For a history of development iterations, see [CHANGELOG.md](./CHANGELOG.md).