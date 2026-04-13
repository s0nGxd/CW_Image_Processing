# Blood Cell Semantic Segmentation Pipeline
## COMP2032 Image Processing Coursework 2026

---

## 1. Intro
## The Solution: Adaptive Strategy Bank

This project features a fully automated, **Adaptive Strategy Bank** pipeline that achieves **97.2% overall mIoU** on the benchmark dataset. 

Rather than relying on a single, fragile algorithm to segment all images perfectly, the pipeline runs **6 independent segmentation strategies** in parallel and selects the best result dynamically based on shape heuristics.

Key features include:
1.  **Phase 1: Pre-processing (CLAHE)** - Enhances local contrast on the `L*` channel without modifying color components.
2.  **Phase 2: Strategy Bank** - Executes 6 methods in parallel:
    -   `HSV_S + Gaussian + Otsu`
    -   `LAB_A + Bilateral + Otsu`
    -   `ColDist + Gaussian + Otsu`
    -   `LAB_A + Adaptive Threshold`
    -   `K-Means Clustering (k=3)`
3.  **Phase 3: Assessment Scoring** - Automatically ranks masks by penalizing unrealistic cell characteristics (e.g., poor circularity or un-centered regions) to choose the best segment.
4.  **Phase 4: Optimization (GrabCut)** - Polishes the boundaries of the chosen mask utilizing color probability modeling. No manual tuning is involved.

For a full academic breakdown of the algorithms used and how they align with the coursework, see `Technique.md`.

## Deliverables

The pipeline handles directory structures automatically. All evaluation outputs and results are saved in the submission folder:
**📁 `Results 2026 IIP - GroupXXX`** 5-stage refinement process:
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