# Blood Cell Semantic Segmentation Pipeline

This project is an automated Image Processing Pipeline that segments blood cells from images.

## Prerequisites

To run this program, you need to have **Python** installed on your computer. If you don't have it, download and install it from [python.org](https://www.python.org/downloads/). Make sure to check the box that says "Add Python to PATH" during installation if you are on Windows.

## How to Run the Program (Step-by-Step)

### For Windows Users:
1. **Open Command Prompt or PowerShell**: Press the Windows key, type `cmd` or `powershell`, and hit Enter.
2. **Navigate to the project folder**: Use the `cd` command to go to the folder where this project is located. For example:
   ```cmd
   cd path\to\CW_Image_Processing
   ```
3. **Install the required libraries**: Run the following command to install the necessary tools:
   ```cmd
   pip install -r requirements.txt
   ```
4. **Run the pipeline**: Execute the main program by running:
   ```cmd
   python main.py
   ```

### For Mac Users:
1. **Open Terminal**: Press `Command + Space`, type `Terminal`, and hit Enter.
2. **Navigate to the project folder**: Use the `cd` command to go to the folder where this project is located. For example:
   ```bash
   cd path/to/CW_Image_Processing
   ```
3. **Install the required libraries**: Run the following command to install the necessary tools. (Depending on your Mac setup, you might need to use `pip3` instead of `pip`):
   ```bash
   pip3 install -r requirements.txt
   ```
4. **Run the pipeline**: Execute the main program by running. (You might need to use `python3` instead of `python`):
   ```bash
   python3 main.py
   ```

## Where to find the Output?

Once the program finishes running, it will automatically create a new folder named **`Results 2026 IIP - Group015`** in the same directory. 

Inside this folder, you will find:
- **`001 - Input Images/`**: A copy of the original images.
- **`002 - Image Processing Pipeline/`**: Visualizations showing the step-by-step processing stages for each image.
- **`003 - Output Images/`**: The final result—the segmented cells placed on a clean white background.

## Do I need to change any directories before running?

**No.** The code is designed to be fully plug-and-play. It uses dynamic relative paths, meaning it will automatically detect the project folder no matter where you saved it on your computer. 

If you ever want to test the pipeline on your own custom images, simply place them into the respective subfolders (`Easy`, `Medium`, or `Hard`) inside the **`001 - Input Images`** directory before running the program!