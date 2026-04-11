# CW_Image_Processing

### Segmentation Strategy

The segmentation pipeline detects the **dark purple nucleus first**, then uses it as an anchor to segment the full white blood cell.

#### Why use the nucleus?

The nucleus is the most reliable feature across the dataset:

- The nucleus usually appears **dark blue/purple** because of staining.
- The surrounding cytoplasm is much less consistent. It may be faint, blended into the background, or visually similar to nearby red blood cells.
- A simple threshold over the whole cell is often not reliable enough, especially in crowded blood smear images.
- Using the nucleus as a **sure foreground seed** gives the pipeline a strong starting point for isolating the correct white blood cell.

This makes the segmentation more stable across different stain strengths, lighting conditions, and image difficulty levels. The pipeline also restricts the candidate region to stay close to the nucleus, which helps prevent nearby red blood cells or background structures from being incorrectly included. :contentReference[oaicite:0]{index=0}

---

### Method

The segmentation pipeline consists of the following steps:

1. **Color Space Conversion**  
   Convert the image into both **LAB** and **HSV** color spaces so stain colour, brightness, and saturation can be analysed more effectively.

2. **Nucleus Detection**  
   Compute a nucleus score using a combination of:
   - darkness
   - saturation
   - magenta intensity
   - blue bias  

   This helps identify the dark purple nucleus more robustly than using a single fixed threshold.

3. **Morphological Cleaning**  
   Apply morphological opening and closing to remove small noise and smooth the nucleus region.

4. **Largest Nucleus Selection**  
   Keep the most likely nucleus by selecting the largest valid connected component.

5. **Region Expansion**  
   Build a crop around the nucleus so the full white blood cell is likely included while limiting interference from the rest of the image.

6. **Background Estimation**  
   Estimate background statistics from the border of the cropped region. This gives a reference for what the plain slide background looks like.

7. **Candidate Cell Construction**  
   Build a likely white-blood-cell region using:
   - deviation from background colour
   - stain intensity
   - darkness
   - closeness to the nucleus  

   This step produces a foreground candidate that is more specific than simply taking all non-background pixels.

8. **Distance Constraint from Nucleus**  
   Restrict the candidate region so it remains within a reasonable distance from the nucleus. This reduces the chance of including nearby red blood cells or unrelated structures.

9. **GrabCut Segmentation**  
   Run GrabCut using:
   - the nucleus as **sure foreground**
   - the candidate cell region as **probable foreground**
   - border and background-like pixels as **sure background**

10. **Component Filtering**  
    Keep only the segmented component connected to the nucleus so that detached cells or artifacts are removed.

11. **Bridge Removal**  
    Slightly erode and regrow the mask to break thin accidental connections to nearby red blood cells while preserving the main white blood cell.

12. **Post-processing**  
    Apply morphological refinement and hole filling to produce a cleaner final mask.

13. **Final Reconstruction**  
    Place the segmented crop back into the full image and generate the final binary mask and white-background output. :contentReference[oaicite:1]{index=1}

---

### Output

The pipeline produces two outputs for each input image:

- **Binary Mask** – a mask identifying the segmented white blood cell  
- **Segmented Cell Image** – the extracted cell placed on a white background

---

### Summary

In short, the pipeline works by first finding the nucleus, then using colour, background contrast, and spatial distance to estimate the rest of the white blood cell. GrabCut is then used to refine the segmentation, followed by connected-component filtering and morphological cleanup to improve the final result. This makes the method more robust on both easy and difficult blood smear images. :contentReference[oaicite:2]{index=2}