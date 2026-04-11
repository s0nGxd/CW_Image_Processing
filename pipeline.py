import cv2
import numpy as np
import os


def largest_component(mask):
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if num_labels <= 1:
        return mask

    largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    out = np.zeros_like(mask)
    out[labels == largest_label] = 255
    return out


def fill_holes(mask):
    flood = mask.copy()
    h, w = mask.shape
    ffmask = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(flood, ffmask, (0, 0), 255)
    holes = cv2.bitwise_not(flood)
    return cv2.bitwise_or(mask, holes)


def component_touching_seed(mask, seed_mask):
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if num_labels <= 1:
        return mask

    seed_labels = labels[seed_mask > 0]
    seed_labels = seed_labels[seed_labels != 0]

    if len(seed_labels) == 0:
        return largest_component(mask)

    unique, counts = np.unique(seed_labels, return_counts=True)
    chosen = unique[np.argmax(counts)]

    out = np.zeros_like(mask)
    out[labels == chosen] = 255
    return out


def remove_small_components(mask, min_area=100):
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    out = np.zeros_like(mask)
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] >= min_area:
            out[labels == i] = 255
    return out


def safe_grabcut(img, init_mask, iters=5):
    gc_mask = init_mask.copy()

    if np.count_nonzero(gc_mask == cv2.GC_FGD) == 0:
        fg_candidate = (gc_mask == cv2.GC_PR_FGD)
        if np.count_nonzero(fg_candidate) > 0:
            ys, xs = np.where(fg_candidate)
            cy, cx = int(np.mean(ys)), int(np.mean(xs))
            r = 3
            y1 = max(0, cy - r)
            y2 = min(gc_mask.shape[0], cy + r + 1)
            x1 = max(0, cx - r)
            x2 = min(gc_mask.shape[1], cx + r + 1)
            gc_mask[y1:y2, x1:x2] = cv2.GC_FGD

    if np.count_nonzero(gc_mask == cv2.GC_BGD) == 0:
        gc_mask[0, :] = cv2.GC_BGD
        gc_mask[-1, :] = cv2.GC_BGD
        gc_mask[:, 0] = cv2.GC_BGD
        gc_mask[:, -1] = cv2.GC_BGD

    has_fg = np.count_nonzero((gc_mask == cv2.GC_FGD) | (gc_mask == cv2.GC_PR_FGD)) > 0
    has_bg = np.count_nonzero((gc_mask == cv2.GC_BGD) | (gc_mask == cv2.GC_PR_BGD)) > 0

    if not (has_fg and has_bg):
        return np.where(
            (gc_mask == cv2.GC_FGD) | (gc_mask == cv2.GC_PR_FGD),
            255,
            0
        ).astype(np.uint8)

    bgdModel = np.zeros((1, 65), np.float64)
    fgdModel = np.zeros((1, 65), np.float64)

    try:
        cv2.grabCut(
            img,
            gc_mask,
            None,
            bgdModel,
            fgdModel,
            iters,
            cv2.GC_INIT_WITH_MASK
        )
        return np.where(
            (gc_mask == cv2.GC_FGD) | (gc_mask == cv2.GC_PR_FGD),
            255,
            0
        ).astype(np.uint8)
    except cv2.error:
        return np.where(
            (gc_mask == cv2.GC_FGD) | (gc_mask == cv2.GC_PR_FGD),
            255,
            0
        ).astype(np.uint8)


def get_nucleus_mask(img):
    blur = cv2.GaussianBlur(img, (5, 5), 0)

    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(blur, cv2.COLOR_BGR2LAB)

    _, s, _ = cv2.split(hsv)
    l, a, b = cv2.split(lab)

    darkness = 255 - l
    magenta = np.clip(a.astype(np.int16) - 128, 0, 127).astype(np.uint8)
    blue_bias = np.clip(128 - b.astype(np.int16), 0, 127).astype(np.uint8)

    score = (
        0.42 * darkness.astype(np.float32) +
        0.28 * s.astype(np.float32) +
        0.20 * magenta.astype(np.float32) +
        0.10 * blue_bias.astype(np.float32)
    )
    score = np.clip(score, 0, 255).astype(np.uint8)

    _, otsu_mask = cv2.threshold(score, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    color_mask1 = cv2.inRange(hsv, (105, 35, 20), (175, 255, 220))
    color_mask2 = cv2.inRange(a, 128, 210)
    color_mask3 = cv2.inRange(b, 65, 150)

    color_mask = cv2.bitwise_and(color_mask1, color_mask2)
    color_mask = cv2.bitwise_and(color_mask, color_mask3)

    nucleus = cv2.bitwise_and(otsu_mask, color_mask)

    k1 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    k2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

    nucleus = cv2.morphologyEx(nucleus, cv2.MORPH_OPEN, k1)
    nucleus = cv2.morphologyEx(nucleus, cv2.MORPH_CLOSE, k2)
    nucleus = remove_small_components(nucleus, min_area=30)
    nucleus = largest_component(nucleus)

    return nucleus


def expand_box(x, y, w, h, img_w, img_h, scale=4.8, min_size=170):
    cx = x + w / 2
    cy = y + h / 2

    new_w = max(int(w * scale), min_size)
    new_h = max(int(h * scale), min_size)

    x1 = max(0, int(cx - new_w / 2))
    y1 = max(0, int(cy - new_h / 2))
    x2 = min(img_w, int(cx + new_w / 2))
    y2 = min(img_h, int(cy + new_h / 2))

    return x1, y1, x2, y2


def estimate_background_stats(crop):
    lab = cv2.cvtColor(crop, cv2.COLOR_BGR2LAB)
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

    h, w = crop.shape[:2]
    border_w = max(10, min(h, w) // 10)

    border_mask = np.zeros((h, w), np.uint8)
    border_mask[:border_w, :] = 255
    border_mask[-border_w:, :] = 255
    border_mask[:, :border_w] = 255
    border_mask[:, -border_w:] = 255

    border_pixels = lab[border_mask > 0].reshape(-1, 3).astype(np.float32)
    mean = border_pixels.mean(axis=0)
    std = border_pixels.std(axis=0) + 1e-6

    return lab, hsv, border_mask, mean, std


def build_wbc_candidate(crop, nucleus_crop):
    lab, hsv, border_mask, bg_mean, bg_std = estimate_background_stats(crop)

    l, a, b = cv2.split(lab)
    h, s, v = cv2.split(hsv)

    z = np.sqrt((((lab.astype(np.float32) - bg_mean) / bg_std) ** 2).sum(axis=2))

    darkness = 255 - l
    magenta = np.clip(a.astype(np.int16) - 128, 0, 127).astype(np.uint8)
    blue_bias = np.clip(128 - b.astype(np.int16), 0, 127).astype(np.uint8)

    nucleus_like = (
        0.45 * darkness.astype(np.float32) +
        0.30 * s.astype(np.float32) +
        0.15 * magenta.astype(np.float32) +
        0.10 * blue_bias.astype(np.float32)
    )

    cytoplasm_like = (
        0.45 * z.astype(np.float32) +
        0.25 * s.astype(np.float32) +
        0.20 * darkness.astype(np.float32) +
        0.10 * magenta.astype(np.float32)
    )

    # WBC pixels are usually unlike the plain background,
    # and more stain-heavy than RBC/background.
    combined = np.maximum(nucleus_like, cytoplasm_like)
    combined = cv2.GaussianBlur(combined.astype(np.uint8), (5, 5), 0)

    _, cand1 = cv2.threshold(combined, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    cand2 = (
        ((z > 2.0) & (darkness > 10)) |
        ((s > 28) & (darkness > 8)) |
        ((magenta > 6) & (z > 1.6))
    ).astype(np.uint8) * 255

    candidate = cv2.bitwise_or(cand1, cand2)

    # keep only region around nucleus
    ys, xs = np.where(nucleus_crop > 0)
    cy = int(np.mean(ys))
    cx = int(np.mean(xs))
    nucleus_area = max(1, cv2.countNonZero(nucleus_crop))
    est_radius = int(max(28, min(90, np.sqrt(nucleus_area) * 5.8)))

    yy, xx = np.indices(candidate.shape)
    dist = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    distance_gate = (dist <= est_radius).astype(np.uint8) * 255

    candidate = cv2.bitwise_and(candidate, distance_gate)

    k_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    k_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))

    candidate = cv2.morphologyEx(candidate, cv2.MORPH_OPEN, k_open)
    candidate = cv2.morphologyEx(candidate, cv2.MORPH_CLOSE, k_close)

    seed = cv2.dilate(
        nucleus_crop,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)),
        iterations=1
    )

    candidate = component_touching_seed(candidate, seed)
    candidate = cv2.bitwise_or(candidate, seed)

    sure_bg = (
        (border_mask > 0) |
        ((z < 1.15) & (s < 22) & (l > 205))
    ).astype(np.uint8) * 255

    return candidate, sure_bg, border_mask, est_radius


def break_thin_bridges(mask, nucleus_crop):
    # Erode slightly to break accidental thin links to RBCs,
    # then regrow only the part connected to the nucleus.
    eroded = cv2.erode(
        mask,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
        iterations=1
    )
    kept = component_touching_seed(eroded, nucleus_crop)
    restored = cv2.dilate(
        kept,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
        iterations=1
    )
    restored = cv2.bitwise_or(restored, nucleus_crop)
    return restored


def segment_wbc(image_path, save_mask_path=None, save_output_path=None, debug_dir=None):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    original = img.copy()
    H, W = img.shape[:2]

    nucleus = get_nucleus_mask(img)
    if cv2.countNonZero(nucleus) == 0:
        raise ValueError("No nucleus detected")

    ys, xs = np.where(nucleus > 0)
    x, y, w, h = cv2.boundingRect(np.column_stack((xs, ys)))
    x1, y1, x2, y2 = expand_box(x, y, w, h, W, H)

    crop = original[y1:y2, x1:x2].copy()
    nucleus_crop = nucleus[y1:y2, x1:x2]

    candidate, sure_bg, border_mask, est_radius = build_wbc_candidate(crop, nucleus_crop)

    gc_mask = np.full(crop.shape[:2], cv2.GC_PR_BGD, np.uint8)
    gc_mask[candidate > 0] = cv2.GC_PR_FGD
    gc_mask[nucleus_crop > 0] = cv2.GC_FGD
    gc_mask[sure_bg > 0] = cv2.GC_BGD

    mask_crop = safe_grabcut(crop, gc_mask, iters=5)
    mask_crop = cv2.bitwise_or(mask_crop, nucleus_crop)
    mask_crop = component_touching_seed(mask_crop, nucleus_crop)

    mask_crop = break_thin_bridges(mask_crop, nucleus_crop)

    mask_crop = cv2.morphologyEx(
        mask_crop,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    )
    mask_crop = cv2.morphologyEx(
        mask_crop,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    )

    mask_crop = fill_holes(mask_crop)
    mask_crop = component_touching_seed(mask_crop, nucleus_crop)

    # final distance safety gate
    ys, xs = np.where(nucleus_crop > 0)
    cy = int(np.mean(ys))
    cx = int(np.mean(xs))
    yy, xx = np.indices(mask_crop.shape)
    dist = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    max_radius = int(est_radius * 1.15)
    radius_gate = (dist <= max_radius).astype(np.uint8) * 255
    mask_crop = cv2.bitwise_and(mask_crop, radius_gate)
    mask_crop = cv2.bitwise_or(mask_crop, nucleus_crop)

    mask_crop = fill_holes(mask_crop)
    mask_crop = component_touching_seed(mask_crop, nucleus_crop)

    mask = np.zeros((H, W), np.uint8)
    mask[y1:y2, x1:x2] = mask_crop

    output = np.full_like(original, 255)
    output[mask == 255] = original[mask == 255]

    if save_mask_path is not None:
        cv2.imwrite(save_mask_path, mask)

    if save_output_path is not None:
        cv2.imwrite(save_output_path, output)

    if debug_dir is not None:
        os.makedirs(debug_dir, exist_ok=True)

        box_vis = original.copy()
        cv2.rectangle(box_vis, (x1, y1), (x2, y2), (0, 255, 0), 2)

        cand_full = np.zeros((H, W), np.uint8)
        cand_full[y1:y2, x1:x2] = candidate

        bg_full = np.zeros((H, W), np.uint8)
        bg_full[y1:y2, x1:x2] = sure_bg

        cv2.imwrite(os.path.join(debug_dir, "01_original.png"), original)
        cv2.imwrite(os.path.join(debug_dir, "02_nucleus_mask.png"), nucleus)
        cv2.imwrite(os.path.join(debug_dir, "03_crop_box.png"), box_vis)
        cv2.imwrite(os.path.join(debug_dir, "04_candidate.png"), cand_full)
        cv2.imwrite(os.path.join(debug_dir, "05_sure_bg.png"), bg_full)
        cv2.imwrite(os.path.join(debug_dir, "06_final_mask.png"), mask)
        cv2.imwrite(os.path.join(debug_dir, "07_output.png"), output)

    return mask, output


def process_folder(input_folder, mask_folder, output_folder, debug_root=None):
    os.makedirs(mask_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)

    valid_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}

    for filename in os.listdir(input_folder):
        name, ext = os.path.splitext(filename)
        if ext.lower() not in valid_exts:
            continue

        image_path = os.path.join(input_folder, filename)
        mask_path = os.path.join(mask_folder, f"{name}_mymask.png")
        output_path = os.path.join(output_folder, f"{name}.jpg")

        debug_dir = None
        if debug_root is not None:
            debug_dir = os.path.join(debug_root, name)

        try:
            segment_wbc(
                image_path,
                save_mask_path=mask_path,
                save_output_path=output_path,
                debug_dir=debug_dir
            )
            print(f"Processed: {filename}")
        except Exception as e:
            print(f"Failed: {filename} -> {e}")


if __name__ == "__main__":
    input_folder = "Selected_images"
    mask_folder = "student_mask"
    output_folder = "output_images"
    debug_root = "debug_pipeline"

    process_folder(input_folder, mask_folder, output_folder, debug_root)