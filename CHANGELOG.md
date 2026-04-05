# CHANGELOG — COMP2032 Image Processing Pipeline

All changes, design decisions, experiments, and suggestions are logged here.

---

## [v0.1.0] — 2026-04-04 | Initial Planning & Project Setup

### 📋 What Was Done
- Analysed the assessment sheet (COMP2032 Coursework 2026) in full detail
- Explored the dataset: 16K+ images across 11 classes (BA, BNE, EO, ERB, LY, MMY, MO, MY, PLT, PMY, SNE)
- Examined ground truth masks: binary (0/255), L mode, 360×363 pixels
- Reviewed the 9 curated input images:
  - **Easy**: MMY class — clear single dark cell on light background
  - **Medium**: EO class — cell surrounded by more RBCs, multi-lobed nucleus
  - **Hard**: ERB class — small dark cell densely packed among many RBCs
- Identified naming conventions: GT masks use `*_mask.png`, student masks need `*_mymask.png`
- Created implementation plan with full pipeline design

### 🔬 Key Observations

| Observation | Detail |
|---|---|
| **Easy images (MMY)** | Single large dark cell on clean light background; minimal RBC interference |
| **Medium images (EO)** | Multi-lobed nucleus cell with surrounding RBCs; moderate segmentation challenge |
| **Hard images (ERB)** | Small, densely-stained cell surrounded by many overlapping RBCs; hardest to isolate |
| **GT mask format** | Binary grayscale (L mode), 0 = background, 255 = cell region |
| **Image size** | All images are 360×363 pixels, RGB mode |
| **Dataset has duplicates** | Each image exists as both `.jpg` and `.png` in the dataset |

### 🧠 Design Decisions Made
1. **Colour space**: Will test both HSV and CIELAB — stained cells have distinct hue/chromaticity
2. **Thresholding**: Otsu's method chosen as primary — fully automatic, ideal for bimodal distributions
3. **Morphology**: Closing → Opening → Connected components → Largest component retention
4. **Architecture**: Modular pipeline with each stage as a separate function for debugging

### ❓ Open Questions
- [ ] What is the group number? (Needed for `Results 2026 IIP - GroupXXX`)
- [ ] Confirm: should the pipeline process ALL 11 classes or just the 9 curated images?
- [ ] Confirm dataset and ground truth paths
- [ ] Python environment details (version, venv/conda?)

---

## Suggestions Log

### 🔮 Future Improvements to Consider

#### Priority 1 — Must-Do (Before Submission)
- [ ] **Parameter tuning**: Systematically test blur kernel sizes (3, 5, 7, 9) and morphological SE sizes (3, 5, 7)
- [ ] **Colour space comparison**: Compare HSV vs LAB quantitatively on all 9 images
- [ ] **Generate 16K masks**: Run batch processing for semantic part
- [ ] **SDK evaluation**: Run on Google Colab with MaskQualityEvaluator
- [ ] **Metrics collection**: Produce mIoU, Dice, Precision tables for paper

#### Priority 2 — Should-Do (Improves Marks)
- [ ] **Adaptive thresholding fallback**: For images where Otsu fails (uneven illumination)
- [ ] **Edge refinement**: Use Canny + morphological gradient to sharpen cell boundaries
- [ ] **Multi-channel combination**: Combine masks from multiple colour channels for robustness
- [ ] **Error analysis**: Document failure cases and explain why they fail

#### Priority 3 — Could-Do (Stretch Goals)
- [ ] **K-means colour clustering**: Unsupervised segmentation in LAB space
- [ ] **Watershed segmentation**: For touching/overlapping cells
- [ ] **GrabCut refinement**: Semi-automatic foreground extraction
- [ ] **Histogram equalization**: Pre-processing for contrast enhancement

#### Priority 4 — Conference Paper Specifics
- [ ] **Literature review**: Research Otsu, colour spaces in medical imaging, morphological ops in haematology
- [ ] **Pipeline diagrams**: Create flowcharts for the paper
- [ ] **Comparison tables**: Pipeline metrics across difficulty levels
- [ ] **Failure case analysis**: Show and discuss hard cases where pipeline struggles
- [ ] **Classification result analysis**: Discuss how mask quality impacts downstream classification

---

## Next Steps Checklist

### Phase 1: Pipeline Implementation
- [ ] Create `config.py` with all paths and parameters
- [ ] Create `src/utils.py` with utility functions
- [ ] Create `src/pipeline.py` with full pipeline stages
- [ ] Create `src/evaluate.py` with metrics
- [ ] Create `main.py` entry point
- [ ] Create `002 - Image Processing Pipeline/` folder
- [ ] Test pipeline on 9 curated images
- [ ] Verify output naming conventions

### Phase 2: Optimisation & Tuning
- [ ] Test HSV path vs LAB path
- [ ] Tune all parameters
- [ ] Evaluate on ground truth masks
- [ ] Document results in CHANGELOG

### Phase 3: Semantic Part (Batch Processing)
- [ ] Create `batch_masks.py`
- [ ] Generate `_mymask.png` for all 16K images
- [ ] Upload to Google Colab
- [ ] Run SDK evaluation
- [ ] Collect mIoU, Dice, Precision metrics

### Version 0.2.0 - Adaptive Multi-Strategy Pipeline
- **Problem**: Fixed pipeline parameters achieved good scores on Medium/Hard images but struggled to generalize.
- **Solution**: Implemented an adaptive multi-strategy algorithm in `pipeline.py`.
- **How it works**:
  - Dynamically processes each image using multiple approaches concurrently (HSV+Otsu, LAB+Otsu, Colour Distance + Adaptive, K-means Clustering).
  - Calculates a "self-assessment score" for each mask based on heuristics: Area Ratio (2-15%), Circularity, Solidity, and Centredness.
  - Automatically selects the best-scoring mask.
  - Refines edges using GrabCut initialization.
- **Results**:
  - **Medium mIoU**: Increased from `0.937` to `0.988`
  - **Hard mIoU**: Increased from `0.698` to `0.883`
  - **Overall Accuracy**: Jumped to `0.949`
  
### Phase 4: Conference Paper
- [ ] Compile all quantitative results
- [ ] Create figures and tables
- [ ] Write methodology section
- [ ] Write results section
- [ ] Write discussion (strengths/weaknesses)
- [ ] Final review and formatting
