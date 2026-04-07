# PindouCV

**PindouCV** is a lightweight computer vision tool designed for **Perler bead (拼豆)** enthusiasts. It automatically analyzes bead images and generates a corresponding **Artkal color code list**, helping users quickly understand the required materials for recreating a design.

---

## ✨ Features

* 📸 Upload a Perler bead image and analyze it automatically
* 🎯 Detect grid structure of bead layouts
* 🎨 Extract dominant colors from each bead cell
* 🧩 Map extracted colors to **Artkal color codes**
* 📊 Output a clean list of required colors and quantities
* 🌐 Simple and interactive UI powered by Gradio

---

## 📂 Project Structure

```
project/
│
├── app.py                # Gradio UI
├── pipeline.py           # Main pipeline (entry point)
│
├── core/
│   ├── preprocess.py     # Image preprocessing
│   ├── grid_detect.py    # Grid detection
│   ├── color_extract.py  # Color extraction
│   ├── color_map.py      # Map to Artkal color codes
│   └── postprocess.py    # Output formatting
│
├── data/
│   └── artkal_colors.json  # Artkal color palette
│
└── utils/
    └── image_utils.py
```

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd PindouCV
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Or manually install:

```bash
pip install gradio opencv-python numpy
```

---

## 🚀 Usage

### Run the application

```bash
python app.py
```

Then open the local URL shown in the terminal (usually `http://127.0.0.1:7860`) in your browser.

---

## 🧠 How It Works

The processing pipeline consists of five main steps:

1. **Preprocessing**

   * Resize and denoise the input image

2. **Grid Detection**

   * Split the image into bead-sized cells (fixed or adaptive grid)

3. **Color Extraction**

   * Compute the average color of each cell

4. **Color Mapping**

   * Match extracted colors to the closest Artkal color (RGB distance)

5. **Postprocessing**

   * Count occurrences and format output

---

## 📊 Output Example

```json
[
  {"color": "C01", "count": 120},
  {"color": "C03", "count": 85},
  {"color": "C15", "count": 42}
]
```

---

## 🎨 Artkal Color Palette

The file:

```
data/artkal_colors.json
```

contains mappings like:

```json
{
  "code": "C01",
  "rgb": [255, 255, 255]
}
```

You can expand or modify this file to support more colors.

---

## 🔧 Customization

* Adjust grid size in `grid_detect.py`
* Improve color matching in `color_map.py`

  * Switch to LAB color space for better accuracy
* Add perspective correction for real-world images
* Replace rule-based pipeline with ML models (future upgrade)

---

## 📦 Packaging (Optional)

To distribute as a standalone application:

```bash
pip install pyinstaller
pyinstaller -F app.py
```

This will generate an executable file in the `dist/` folder.

---

## 🚧 Future Improvements

* ✅ Automatic grid detection (no manual size)
* 🎯 Perspective correction for angled photos
* 🤖 Deep learning-based bead classification
* 📱 Mobile-friendly interface or app version
* 🎨 Generate visual bead pattern output

---

## 📜 License

MIT License (or specify your own)

---

## 🙌 Acknowledgements

Built for Perler bead enthusiasts who want a faster and smarter way to plan their creations.
