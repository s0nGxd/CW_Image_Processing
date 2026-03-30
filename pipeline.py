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


def component_touching_seed(mask, seed_mask):
    """
    Keep only the connected component in mask that overlaps the seed_mask.
    """
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if num_labels <= 1:
        return mask

    seed_labels = labels[seed_mask > 0]
    seed_labels = seed_labels[seed_labels != 0]

    if len(seed_labels) == 0:
        return largest_component(mask)

    # choose the overlapping label with the largest overlap
    unique, counts = np.unique(seed_labels, return_counts=True)
    chosen = unique[np.argmax(counts)]

    out = np.zeros_like(mask)
    out[labels == chosen] = 255
    return out


def get_nucleus_mask(img):
    """
    Detect the dark purple nucleus using LAB + HSV.
    """
    blur = cv2.GaussianBlur(img, (5, 5), 0)

    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(blur, cv2.COLOR_BGR2LAB)

    h = hsv[:, :, 0]
    s = hsv[:, :, 1]
    v = hsv[:, :, 2]

    a = lab[:, :, 1]   # magenta/red tendency
    b = lab[:, :, 2]   # yellow-blue tendency

    # Purple-blue nucleus tends to have:
    # - moderately high saturation
    # - lower brightness than background/RBCs
    # - stronger magenta-blue staining than surrounding cells
    mask1 = cv2.inRange(hsv, (110, 40, 20), (170, 255, 190))
    mask2 = cv2.inRange(a, 135, 200)
    mask3 = cv2.inRange(b, 80, 145)

    nucleus = cv2.bitwise_and(mask1, mask2)
    nucleus = cv2.bitwise_and(nucleus, mask3)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    nucleus = cv2.morphologyEx(nucleus, cv2.MORPH_OPEN, kernel)
    nucleus = cv2.morphologyEx(nucleus, cv2.MORPH_CLOSE, kernel)

    nucleus = largest_component(nucleus)
    return nucleus


def expand_box(x, y, w, h, img_w, img_h, scale=2.2):
    cx = x + w / 2
    cy = y + h / 2

    new_w = int(w * scale)
    new_h = int(h * scale)

    x1 = max(0, int(cx - new_w / 2))
    y1 = max(0, int(cy - new_h / 2))
    x2 = min(img_w, int(cx + new_w / 2))
    y2 = min(img_h, int(cy + new_h / 2))

    return x1, y1, x2, y2


def segment_wbc(image_path, save_mask_path=None, save_output_path=None, debug_dir=None):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    original = img.copy()
    H, W = img.shape[:2]

    nucleus = get_nucleus_mask(img)

    if cv2.countNonZero(nucleus) == 0:
        raise ValueError("No nucleus detected")

    # Bounding box around nucleus
    ys, xs = np.where(nucleus > 0)
    x, y, w, h = cv2.boundingRect(np.column_stack((xs, ys)))
    x1, y1, x2, y2 = expand_box(x, y, w, h, W, H, scale=2.8)

    # GrabCut mask initialization
    gc_mask = np.full((H, W), cv2.GC_BGD, np.uint8)

    # probable foreground in ROI around nucleus
    gc_mask[y1:y2, x1:x2] = cv2.GC_PR_FGD

    # sure foreground = nucleus
    gc_mask[nucleus > 0] = cv2.GC_FGD

    # sure background = border margin outside expanded ROI
    # already background by default

    bgdModel = np.zeros((1, 65), np.float64)
    fgdModel = np.zeros((1, 65), np.float64)

    cv2.grabCut(
        img,
        gc_mask,
        None,
        bgdModel,
        fgdModel,
        5,
        cv2.GC_INIT_WITH_MASK
    )

    # Foreground = sure/probable foreground
    mask = np.where(
        (gc_mask == cv2.GC_FGD) | (gc_mask == cv2.GC_PR_FGD),
        255,
        0
    ).astype(np.uint8)

    # Make sure nucleus stays included
    mask = cv2.bitwise_or(mask, nucleus)

    # Clean the final mask
    kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    kernel_big = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))

    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_big)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_small)

    # Keep only the component connected to the nucleus
    mask = component_touching_seed(mask, nucleus)

    # Optional hole filling
    flood = mask.copy()
    ffmask = np.zeros((H + 2, W + 2), np.uint8)
    cv2.floodFill(flood, ffmask, (0, 0), 255)
    holes = cv2.bitwise_not(flood)
    mask = cv2.bitwise_or(mask, holes)
    mask = component_touching_seed(mask, nucleus)

    # White background output
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

        cv2.imwrite(os.path.join(debug_dir, "01_original.png"), original)
        cv2.imwrite(os.path.join(debug_dir, "02_nucleus_mask.png"), nucleus)
        cv2.imwrite(os.path.join(debug_dir, "03_grabcut_box.png"), box_vis)
        cv2.imwrite(os.path.join(debug_dir, "04_final_mask.png"), mask)
        cv2.imwrite(os.path.join(debug_dir, "05_output.png"), output)

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
    input_folder = "input_images"
    mask_folder = "student_mask"
    output_folder = "output_images"
    debug_root = "debug_pipeline"

    process_folder(input_folder, mask_folder, output_folder, debug_root)