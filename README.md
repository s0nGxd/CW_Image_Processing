# CW_Image_Processing
### Segmentation Strategy

The segmentation pipeline detects the **dark purple nucleus first**, then uses it as a seed to segment the entire white blood cell.

#### Why use the nucleus?

The nucleus is the most reliable feature across the dataset:

- The nucleus consistently appears **dark blue/purple** due to staining.
- The cytoplasm is much less consistent. It can appear pale, pinkish, thin, or partially blended with the background or nearby red blood cells.
- A single color threshold for the entire cell is unreliable, especially in blood smear images where many red blood cells are present.
- Using the nucleus as a **sure foreground marker** allows GrabCut to expand outward and capture the rest of the cell more robustly.

By anchoring the segmentation on the nucleus, the pipeline becomes significantly more stable across different lighting conditions, stains, and surrounding cells.

---

### Method

The segmentation pipeline consists of the following steps:

1. **Color Space Conversion**  
   Convert the image into both **LAB** and **HSV** color spaces to better separate stain colors and intensity information.

2. **Nucleus Detection**  
   Identify candidate nucleus regions using color and intensity thresholds that capture the dark purple staining.

3. **Morphological Cleaning**  
   Apply morphological operations (opening and closing) to remove noise and smooth the detected nucleus region.

4. **Nucleus Selection**  
   Keep the most likely nucleus component by selecting the largest valid connected region.

5. **Region Expansion**  
   Create a bounding region around the detected nucleus to ensure the full white blood cell is included.

6. **Background Estimation**  
   Estimate background color statistics from the border of the cropped region to distinguish foreground objects from the slide background.

7. **GrabCut Segmentation**  
   Run GrabCut using:
   - the nucleus as **sure foreground**
   - border pixels as **sure background**
   - candidate cell regions as **probable foreground**

8. **Component Filtering**  
   Keep only the segmented region connected to the nucleus to remove nearby red blood cells or artifacts.

9. **Post-processing**  
   Apply morphological refinement and hole filling to produce a clean final mask.

---

### Output

The pipeline produces two outputs for each input image:

- **Binary Mask** – a mask identifying the segmented white blood cell  
- **Segmented Cell Image** – the extracted cell placed on a white background