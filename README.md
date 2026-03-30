# CW_Image_Processing
detect the dark purple nucleus first, then use that as a seed to segment the whole white blood cell.
Why?
- The nucleus is the most reliable part across your examples. It is consistently dark blue-purple.
- The cytoplasm is much less reliable. Sometimes it is pale, sometimes pinkish, sometimes thin, sometimes partly blended with background or RBCs.
- A single color threshold for the whole cell will often fail, especially in the blood-smear images with many red blood cells.
- Using the nucleus as a sure foreground marker lets GrabCut expand outward and capture the rest of the cell much better.
Method:
1. Convert image to LAB and HSV
2. Threshold for the dark purple nucleus
3. Clean it with morphology
4. Keep the most likely nucleus blob
5. Build a box around that blob
6. Run GrabCut using that box
7. Force the nucleus to remain foreground
8. Keep the component connected to the nucleus
9. Output:
    - binary mask
    - white-background segmented cell