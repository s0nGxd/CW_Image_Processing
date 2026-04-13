"""
Adaptive Multi-Strategy Image Processing Pipeline for Blood Cell Segmentation.

This pipeline automatically tries multiple colour-space + thresholding strategies
on each image and selects the one that produces the most plausible cell mask,
using shape-based quality heuristics (no ground truth needed at runtime).

Strategies explored per image:
    1. HSV Saturation channel + Otsu
    2. CIELAB A* channel + Otsu  
    3. Colour distance from estimated background + Otsu
    4. Inverted Grayscale + Otsu
    5. HSV Saturation + Adaptive Gaussian threshold
    6. K-means colour clustering (k=3)
    7. Colour distance + Adaptive threshold with tighter params

Each strategy is scored by a quality metric that rewards:
    - Area ratio within expected cell range (2-20% of image)
    - Circularity / compactness (blood cells are roughly round)
    - Solidity (filled shape, not fragmented)
    - Centredness (cell tends to be near image centre in these micrographs)

The best-scoring strategy's mask is selected as the final output.
"""

import cv2
import numpy as np


# ---------------------------------------------------------------------------
#  Individual pipeline stages
# ---------------------------------------------------------------------------

def estimate_background(img_rgb, margin=15):
    """Estimate background colour from image border pixels."""
    h, w = img_rgb.shape[:2]
    border = np.concatenate([
        img_rgb[:margin, :].reshape(-1, 3),
        img_rgb[-margin:, :].reshape(-1, 3),
        img_rgb[margin:-margin, :margin].reshape(-1, 3),
        img_rgb[margin:-margin, -margin:].reshape(-1, 3),
    ])
    return np.median(border, axis=0).astype(np.float64)


def colour_distance_map(img_rgb, bg_colour):
    """Per-pixel Euclidean distance from estimated background colour."""
    diff = img_rgb.astype(np.float64) - bg_colour
    dist = np.sqrt(np.sum(diff ** 2, axis=2))
    # Normalise to 0-255
    if dist.max() > 0:
        dist = (dist / dist.max() * 255).astype(np.uint8)
    else:
        dist = np.zeros(img_rgb.shape[:2], dtype=np.uint8)
    return dist


def extract_channel(img_rgb, method):
    """Extract a single-channel representation for thresholding."""
    if method == "HSV_S":
        return cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)[:, :, 1]
    elif method == "HSV_V_INV":
        return 255 - cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)[:, :, 2]
    elif method == "LAB_A":
        return cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB)[:, :, 1]
    elif method == "LAB_B":
        return cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB)[:, :, 2]
    elif method == "GRAY_INV":
        return 255 - cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    elif method == "COL_DIST":
        bg = estimate_background(img_rgb)
        return colour_distance_map(img_rgb, bg)
    else:
        return 255 - cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)


def apply_clahe(img_rgb, clip_limit=2.0, tile_grid=(8, 8)):
    """
    Adaptive Histogram Equalization (CLAHE) pre-processing step.

    Applies Contrast Limited Adaptive Histogram Equalization to the
    Luminance (L*) channel of the CIELAB colour space.  This improves
    local contrast across the image without over-amplifying noise,
    making the WBC stand out more clearly from the stained background.

    Lecture technique: CV Histogram Equalization / Adaptive HE.
    """
    # Convert RGB -> LAB
    lab = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB)
    l_ch, a_ch, b_ch = cv2.split(lab)

    # Apply CLAHE on the L channel only
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid)
    l_eq = clahe.apply(l_ch)

    # Merge back and convert to RGB
    lab_eq = cv2.merge([l_eq, a_ch, b_ch])
    return cv2.cvtColor(lab_eq, cv2.COLOR_LAB2RGB)


def reduce_noise(channel, kernel_size=(5, 5)):
    """Gaussian or bilateral blur for noise suppression."""
    if kernel_size == "bilateral":
        return cv2.bilateralFilter(channel, 9, 75, 75)
    return cv2.GaussianBlur(channel, kernel_size, 0)


def threshold_otsu(blurred):
    """Otsu's automatic global threshold."""
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh


def threshold_adaptive(blurred, block_size=51, C=5):
    """Adaptive Gaussian threshold (handles uneven illumination)."""
    return cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block_size, -C
    )


def morphological_cleanup(binary, se_size=(5, 5)):
    """Close then open to fill holes and remove small blobs."""
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, se_size)
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=3)
    opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel, iterations=2)
    return opened


def keep_best_contour(binary, min_area=300, fill_holes=False):
    """Keep only the largest contour (filled) above min_area.
    
    fill_holes: if True, run a flood-fill pass to close internal gaps before
                finding contours.  Only use on the main strategy selection pass,
                NOT inside GrabCut cleanup (recursive amplification risk).
    """
    if fill_holes:
        # Flood-fill from corner to detect enclosed interior holes
        h, w = binary.shape
        flood_filled = binary.copy()
        mask_ff = np.zeros((h + 2, w + 2), np.uint8)
        cv2.floodFill(flood_filled, mask_ff, (0, 0), 255)
        holes = cv2.bitwise_not(flood_filled)
        binary = cv2.bitwise_or(binary, holes)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return np.zeros_like(binary), None
    largest = max(contours, key=cv2.contourArea)
    mask = np.zeros_like(binary)
    if cv2.contourArea(largest) > min_area:
        cv2.drawContours(mask, [largest], -1, 255, cv2.FILLED)
        return mask, largest
    return np.zeros_like(binary), None


def kmeans_segment(img_rgb, k=3):
    """K-means clustering in LAB space; select the cluster most different from bg."""
    lab = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB)
    h, w = lab.shape[:2]
    pixels = lab.reshape(-1, 3).astype(np.float32)

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1.0)
    _, labels, centres = cv2.kmeans(pixels, k, None, criteria, 5, cv2.KMEANS_PP_CENTERS)
    labels = labels.reshape(h, w)

    # Estimate background as the cluster that dominates the borders
    border = np.concatenate([
        labels[:10, :].ravel(), labels[-10:, :].ravel(),
        labels[10:-10, :10].ravel(), labels[10:-10, -10:].ravel()
    ])
    bg_label = np.argmax(np.bincount(border.astype(int)))

    # Build mask where all non-bg clusters are foreground
    mask = np.where(labels != bg_label, 255, 0).astype(np.uint8)
    return mask


# ---------------------------------------------------------------------------
#  Quality scoring (self-assessment without ground truth)
# ---------------------------------------------------------------------------

def score_mask(mask, contour, img_shape):
    """
    Score a candidate mask based on shape plausibility.
    Higher is better.  Returns 0.0 if mask is empty.
    """
    h, w = img_shape[:2]
    total_pixels = h * w
    fg_pixels = np.sum(mask > 0)

    if fg_pixels == 0 or contour is None:
        return 0.0

    area_ratio = fg_pixels / total_pixels

    # --- Area score: ideal cell is 2-15% of image ---
    if 0.02 <= area_ratio <= 0.25:
        area_score = 1.0
    elif 0.01 <= area_ratio < 0.02 or 0.25 < area_ratio <= 0.35:
        area_score = 0.6
    elif area_ratio > 0.5:
        area_score = 0.0  # clearly wrong
    else:
        area_score = 0.3

    # --- Circularity score ---
    perimeter = cv2.arcLength(contour, True)
    area = cv2.contourArea(contour)
    if perimeter > 0:
        circularity = 4 * np.pi * area / (perimeter ** 2)
    else:
        circularity = 0
    circ_score = min(circularity / 0.60, 1.0)  # 0.60+ is perfectly acceptable since cells can be irregular

    # --- Solidity score ---
    hull = cv2.convexHull(contour)
    hull_area = cv2.contourArea(hull)
    solidity = area / (hull_area + 1e-6)
    solidity_score = min(solidity / 0.85, 1.0)

    # --- Centredness score (cell should be roughly in image centre) ---
    M = cv2.moments(contour)
    if M["m00"] > 0:
        cx = M["m10"] / M["m00"]
        cy = M["m01"] / M["m00"]
        dist_from_centre = np.sqrt((cx - w/2)**2 + (cy - h/2)**2)
        max_dist = np.sqrt((w/2)**2 + (h/2)**2)
        centredness = 1.0 - (dist_from_centre / max_dist)
    else:
        centredness = 0.0

    # Weighted combination
    score = (
        0.40 * area_score
        + 0.20 * circ_score
        + 0.25 * solidity_score
        + 0.15 * centredness
    )
    return score


# ---------------------------------------------------------------------------
#  Strategy definitions
# ---------------------------------------------------------------------------

def _run_single_strategy(img_rgb, channel_method, threshold_fn, blur_k, morph_se, min_area):
    """Run one complete strategy and return (mask, contour, stage_images)."""
    stages = {}

    # 1. Channel extraction
    channel = extract_channel(img_rgb, channel_method)
    stages["01_channel"] = channel

    # 2. Noise reduction
    blurred = reduce_noise(channel, blur_k)
    stages["02_blurred"] = blurred

    # 3. Thresholding
    thresh = threshold_fn(blurred)
    stages["03_threshold"] = thresh

    # 4. Morphology
    cleaned = morphological_cleanup(thresh, morph_se)
    stages["04_morphology"] = cleaned

    # 5. Largest contour
    mask, contour = keep_best_contour(cleaned, min_area, fill_holes=True)
    stages["05_mask"] = mask

    return mask, contour, stages


def _build_strategies():
    """Return a list of (name, channel, threshold_fn, blur_kernel, morph_se, min_area) tuples."""
    return [
        # (name,         channel,     thresh_fn,        blur_k,  morph_se, min_area)
        ("HSV_S+Otsu",   "HSV_S",     threshold_otsu,   (7, 7),  (5, 5),   500),
        ("LAB_A+Otsu",   "LAB_A",     threshold_otsu,   (7, 7),  (5, 5),   500),
        ("ColDist+Otsu", "COL_DIST",  threshold_otsu,   (7, 7),  (5, 5),   500),
        ("GrayInv+Otsu", "GRAY_INV",  threshold_otsu,   (7, 7),  (5, 5),   500),
        ("HSV_S+Adapt",  "HSV_S",     lambda b: threshold_adaptive(b, 51, 7),
                                                         (7, 7),  (5, 5),   500),
        ("ColDist+Adapt","COL_DIST",  lambda b: threshold_adaptive(b, 51, 7),
                                                         (7, 7),  (5, 5),   500),
        ("ColDist+Otsu_sm", "COL_DIST", threshold_otsu, (5, 5),  (3, 3),   300),
        ("LAB_A+Adapt",  "LAB_A",     lambda b: threshold_adaptive(b, 51, 5),
                                                         (7, 7),  (7, 7),   500),
        ("HSV_S+Bilat",  "HSV_S",     threshold_otsu,   "bilateral", (5, 5),   500),
        ("LAB_A+Bilat",  "LAB_A",     threshold_otsu,   "bilateral", (5, 5),   500),
    ]


# ---------------------------------------------------------------------------
#  Main adaptive pipeline
# ---------------------------------------------------------------------------

def generate_output_image(img_rgb, mask):
    """Apply mask to original image with white background."""
    white_bg = np.full_like(img_rgb, 255)
    mask_3ch = np.stack([mask] * 3, axis=-1)
    return np.where(mask_3ch == 255, img_rgb, white_bg)


def run_pipeline(img_rgb, method=None, blur_k=(7, 7), morph_se=(5, 5),
                 min_area=500, save_stages_dir=None):
    """
    Adaptive pipeline: tries multiple strategies, scores each, picks the best.

    Parameters
    ----------
    img_rgb : ndarray   – Input image in RGB.
    method  : str|None  – If given, force a single strategy (backward compat).
    save_stages_dir : str|None – If given, save all intermediate images.

    Returns
    -------
    output_img : ndarray – Segmented cell on white background.
    final_mask : ndarray – Binary mask (0/255).
    """
    best_score = -1
    best_mask = np.zeros(img_rgb.shape[:2], dtype=np.uint8)
    best_stages = {}
    best_name = "none"

    # -----------------------------------------------------------------------
    # PRE-PROCESSING: Adaptive Histogram Equalization (CLAHE)
    # Enhances local contrast on the Luminance channel before any strategy
    # runs. Lecture technique: CV Adaptive Histogram Equalization.
    # -----------------------------------------------------------------------
    img_clahe = apply_clahe(img_rgb)

    strategies = _build_strategies()

    # Also include K-means as a special strategy
    kmeans_mask_raw = kmeans_segment(img_clahe, k=3)
    kmeans_cleaned = morphological_cleanup(kmeans_mask_raw, (5, 5))
    kmeans_final, kmeans_contour = keep_best_contour(kmeans_cleaned, min_area, fill_holes=True)
    kmeans_score = score_mask(kmeans_final, kmeans_contour, img_rgb.shape)

    candidate_results = [("KMeans_k3", kmeans_final, kmeans_contour, kmeans_score,
                          {"01_channel": kmeans_mask_raw, "02_blurred": kmeans_mask_raw,
                           "03_threshold": kmeans_mask_raw, "04_morphology": kmeans_cleaned,
                           "05_mask": kmeans_final})]

    for name, ch_method, thresh_fn, bk, ms, ma in strategies:
        try:
            mask, contour, stages = _run_single_strategy(img_clahe, ch_method, thresh_fn, bk, ms, ma)
            s = score_mask(mask, contour, img_clahe.shape)
            candidate_results.append((name, mask, contour, s, stages))
        except Exception:
            pass

    # Pick the best
    for name, mask, contour, score, stages in candidate_results:
        if score > best_score:
            best_score = score
            best_mask = mask
            best_stages = stages
            best_name = name

    # --- Edge refinement on the winning mask ---
    best_mask = _refine_mask_edges(img_rgb, best_mask)

    # Generate output
    output_img = generate_output_image(img_rgb, best_mask)

    # Save stages
    if save_stages_dir:
        import os
        from .utils import save_image, ensure_dir
        ensure_dir(save_stages_dir)

        save_image(img_rgb, os.path.join(save_stages_dir, "00_original.jpg"))
        for stage_name, stage_img in sorted(best_stages.items()):
            is_color = len(stage_img.shape) == 3
            save_image(stage_img, os.path.join(save_stages_dir, f"{stage_name}.jpg"),
                       is_rgb=is_color)
        save_image(best_mask, os.path.join(save_stages_dir, "06_final_mask.jpg"), is_rgb=False)
        save_image(output_img, os.path.join(save_stages_dir, "07_segmented_output.jpg"))

        # Save strategy info
        with open(os.path.join(save_stages_dir, "strategy_info.txt"), "w") as f:
            f.write(f"Selected strategy: {best_name}\n")
            f.write(f"Score: {best_score:.4f}\n\n")
            f.write("All candidates:\n")
            for name, _, _, score, _ in candidate_results:
                marker = " <-- SELECTED" if name == best_name else ""
                f.write(f"  {name:20s}  score={score:.4f}{marker}\n")

    return output_img, best_mask


def _refine_mask_edges(img_rgb, mask):
    """
    GrabCut refinement: use the coarse mask as initialisation and let
    GrabCut refine the boundary using colour information.
    Falls back to original mask if GrabCut fails.
    """
    if np.sum(mask > 0) == 0:
        return mask

    try:
        h, w = mask.shape
        img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

        # Build GrabCut init mask
        gc_mask = np.where(mask > 0, cv2.GC_PR_FGD, cv2.GC_PR_BGD).astype(np.uint8)

        # Fixed, empirically-tuned margins: erode=2 (tight sure-fg), dilate=8 (generous uncertain zone)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        sure_fg = cv2.erode(mask, kernel, iterations=2)
        gc_mask[sure_fg > 0] = cv2.GC_FGD

        # Dilate to get definite background
        sure_bg = cv2.dilate(mask, kernel, iterations=8)
        gc_mask[sure_bg == 0] = cv2.GC_BGD

        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)

        cv2.grabCut(img_bgr, gc_mask, None, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_MASK)

        refined = np.where((gc_mask == cv2.GC_FGD) | (gc_mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)

        # Final cleanup
        refined = morphological_cleanup(refined, (3, 3))
        refined, _ = keep_best_contour(refined, 300)

        # Refined should be somewhere close in size to original
        orig_area = np.sum(mask > 0)
        new_area = np.sum(refined > 0)
        if new_area == 0 or new_area > orig_area * 3 or new_area < orig_area * 0.2:
            return mask

        return refined
    except Exception:
        return mask
