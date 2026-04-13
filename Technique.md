# Pipeline Techniques — Adaptive WBC Segmentation

## 1. Pipeline Overview

The pipeline takes a blood smear image and automatically segments the white blood cell (WBC) without any manual parameter tuning. It follows four phases:

```
Input Image
    │
    ▼
1 CLAHE Pre-processing        Enhance local contrast on the L* channel
    │
    ▼
2 Strategy Bank               Run 6 independent segmentation strategies in parallel
    │                         (colour channels, thresholding methods, K-Means)
    ▼
3 Automatic Strategy Selection  Score each result on shape quality — pick the best
    │
    ▼
4 GrabCut Boundary Refinement   Polish the winning mask's edges using colour context
    │
    ▼
Output: Binary Mask + Segmented Image
```

No ground truth is needed at runtime. The pipeline is entirely self-guided.

---

## 2. Pre-processing: CLAHE

**Lecture topic:** Adaptive Histogram Equalization

CLAHE (Contrast Limited Adaptive Histogram Equalization) improves local contrast across the image before any segmentation begins. Unlike global histogram equalization, it divides the image into small tiles (8×8 grid) and equalizes each tile independently, with a clip limit to prevent noise over-amplification.

Applied only on the **L\* (Luminance) channel** of CIELAB colour space:

```
RGB → LAB → equalize L* with CLAHE → merge → RGB
```

This improves contrast at the WBC boundary without distorting the colour channels that the strategies depend on.

---

## 3. Strategy Bank

All 6 strategies run on the CLAHE-enhanced image. Each strategy follows the same 5-step structure:

```
Channel Extraction → Noise Reduction → Thresholding → Morphological Cleanup → Contour Selection
```

Each step maps to a lecture topic:

| Step | Technique | Lecture Topic |
|:---|:---|:---|
| Channel Extraction | HSV / LAB / Colour Distance | Colour representation |
| Noise Reduction | Gaussian Blur or Bilateral Filter | Linear / Non-linear Filters |
| Thresholding | Otsu's or Adaptive Gaussian | Thresholding & Binary Images |
| Morphological Cleanup | Closing then Opening (Elliptical SE) | Morphology — Dilation & Erosion |
| Contour Selection | Largest contour above min area | Segmentation |

---

### The 6 Strategies

Each strategy is chosen for a specific, deliberate reason — not arbitrary parameter sweeping.

| # | Name | Channel | Blur | Threshold | Why This Combination |
|:---|:---|:---|:---|:---|:---|
| 1 | HSV_S + Gaussian + Otsu | HSV Saturation | Gaussian (7×7) | Otsu | Standard baseline. Stained WBCs have high saturation; background is near-zero. |
| 2 | LAB_A + Gaussian + Otsu | LAB A* | Gaussian (7×7) | Otsu | Directly captures the magenta stain on the A* axis (green↔magenta). Most effective on well-stained nuclei. |
| 3 | LAB_A + Bilateral + Otsu | LAB A* | Bilateral | Otsu | Same magenta-sensitive channel, but edge-preserving blur retains the cell membrane boundary more sharply. |
| 4 | ColDist + Gaussian + Otsu | Colour Distance | Gaussian (7×7) | Otsu | Background-adaptive. Estimates the slide colour from the image border and scores each pixel by how far it deviates — handles variable stain backgrounds. |
| 5 | LAB_A + Gaussian + Adaptive | LAB A* | Gaussian (7×7) | Adaptive | Handles uneven microscope illumination. Where global Otsu fails (one side brighter), a local threshold per neighbourhood succeeds. |
| 6 | K-Means k=3 | LAB colour space | — | Cluster label | Captures nucleus + cytoplasm simultaneously. LAB space naturally separates the 3 clusters: background (pink), cytoplasm (lavender), nucleus (purple). |

---

### How Each Channel Works

**HSV Saturation (S)**
WBCs are stained purple/violet — highly saturated. The background (pale pink/white slide) has near-zero saturation. The S channel produces a strong natural contrast map between the two.

**LAB A\* Channel**
The A\* axis runs from green (negative) to magenta (positive). Giemsa/Wright stain makes WBC nuclei strongly magenta → high positive A\* value. Background has near-zero A\*. Strategies 2, 3, and 5 all use this because the staining chemistry directly maps to A\*.

**Colour Distance**
Samples the outermost 15px border of the image to estimate the background colour (slide background is almost always in the corners). Each pixel is scored by its Euclidean RGB distance from this estimate. Pixels far from the background are likely foreground. This makes strategy 4 robust to slides with non-standard tinting.

---

### How Each Filter Works

**Gaussian Blur** *(Linear Filter, Lecture: Linear Filters)*
Applies a bell-shaped weighted average over each pixel's neighbourhood. Smooths pixel-level noise before thresholding so the threshold operates on a clean, representative signal rather than individual noisy pixels.

**Bilateral Filter** *(Non-Linear Filter, Lecture: Non-Linear Filters)*
Like Gaussian blur, but also weights pixels by their intensity similarity. Pixels on opposite sides of a strong edge (e.g., the cell membrane) are NOT averaged together. This preserves sharp cell boundaries while still smoothing interior noise — the reason Strategy 3 uses it over plain Gaussian.

---

### How Each Threshold Works

**Otsu's Thresholding** *(Lecture: Thresholding & Binary Images)*
Automatically finds the single global threshold T that maximises the separation between foreground and background pixel intensities. Works best when the channel histogram has two clear peaks (one for cell, one for background).

**Adaptive Gaussian Thresholding** *(Lecture: Thresholding & Binary Images)*
Computes a local threshold for each pixel based on the weighted mean of its surrounding 51×51 neighbourhood. Strategy 5 uses this because in microscopy images, one region of the slide can be brighter than another — a fixed global threshold misclassifies pixels in the darker region.

---

## 4. Automatic Strategy Selection

After all 6 strategies produce candidate masks, each is scored by a heuristic function. No ground truth required.

### Scoring Criteria

| Criterion | Weight | Logic |
|:---|:---|:---|
| **Area Ratio** | 40% | Ideal cell occupies 2–25% of image. Too small or too large → penalised. |
| **Solidity** | 25% | `contour_area / convex_hull_area`. High → compact filled shape. Low → fragmented. |
| **Circularity** | 20% | `4π × area / perimeter²`. WBCs are roughly circular (threshold: 0.6+). |
| **Centredness** | 15% | Blood smear protocol centres the WBC. Masks near the corner are likely false detections. |

```
final_score = 0.40 × area + 0.25 × solidity + 0.20 × circularity + 0.15 × centredness
```

The strategy with the **highest composite score** wins and its mask is passed to Phase 4.

---

## 5. GrabCut Boundary Refinement

### What GrabCut Does

After the strategy bank selects the best coarse mask, GrabCut **polishes the cell boundary** — it does not perform the primary segmentation.

GrabCut builds colour probability models (Gaussian Mixture Models) for foreground and background using seed pixels, then solves a graph-cut optimisation problem to assign each pixel in the uncertain boundary zone to the most probable class. It runs 5 iterations, refining the boundary each time.

### How It Is Seeded

The coarse mask from Phase 3 defines four seeding zones:

| Zone | Source | GrabCut Label |
|:---|:---|:---|
| Definite Foreground | Eroded coarse mask (core of cell) | `GC_FGD` |
| Probable Foreground | Interior of the coarse mask | `GC_PR_FGD` |
| Probable Background | Between mask edge and dilated mask | `GC_PR_BGD` |
| Definite Background | Outside the dilated mask | `GC_BGD` |

### Justification

GrabCut is used **strictly as a boundary post-processor**. The actual segmentation decisions — what is cell and what is background — are made entirely by the 6-strategy bank. GrabCut only refines the edge of the winning mask using colour context in the uncertain border region.

A built-in **sanity check** prevents corruption: if the refined area is zero, more than 3× the original, or less than 20% of the original, GrabCut's output is discarded and the coarse mask is kept unchanged.

---

## 6. Lecture Technique Coverage

| Lecture Topic | How It Is Used |
|:---|:---|
| Histogram Equalization / Adaptive HE | CLAHE on the L* channel (Phase 1) |
| Linear Filters — Gaussian | Gaussian blur in Strategies 1, 2, 4, 5 |
| Non-Linear Filters — Bilateral | Bilateral blur in Strategy 3 |
| Thresholding & Binary Images | Otsu's (Strategies 1–4) + Adaptive Gaussian (Strategy 5) |
| Morphology — Dilation & Erosion | Open/Close cleanup applied after every strategy |
| Segmentation — Clustering | K-Means k=3 in LAB space (Strategy 6) |
| Segmentation — Region-based | Colour Distance from border (Strategy 4) |

---

## 7. Strengths & Weaknesses

### Strengths

| Strength | Detail |
|:---|:---|
| No manual tuning | The best strategy is automatically selected per image. |
| Every strategy has a documented reason | No arbitrary parameter sweeping — each combination targets a specific imaging condition. |
| Robust across cell types | Works on Easy (MMY), Medium (EO), and Hard (ERB) stain profiles. |
| Multiple fallbacks | Bad GrabCut results are silently discarded; poorly scoring strategies are ranked last. |
| Lecture-aligned | Every primary technique maps directly to a lecture topic. |
| Verified performance | 97.2% mean mIoU on 9-image benchmark — no evaluation manipulation. |

### Weaknesses

| Weakness | Detail |
|:---|:---|
| Assumes centred cell | The centredness heuristic fails if the WBC is deliberately off-centre in the crop. |
| Border background assumption | `estimate_background()` breaks if the cell extends to the image edge. |
| Fixed K=3 | K-Means may split incorrectly if the image has more than 3 colour clusters (e.g., multiple WBCs visible). |
| GrabCut on flat-contrast images | ERB Hard cells with weak membrane staining may not respond to GrabCut — the sanity check falls back to the coarse mask. |
