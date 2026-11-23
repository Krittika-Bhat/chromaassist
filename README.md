# ChromaAssist 🎨👁️

**ChromaAssist** is an accessible, colorblind-friendly image processing application designed to simulate and compensate for Color Vision Deficiency (CVD).

The project implements physiologically-grounded algorithms from scratch using NumPy and OpenCV (without external "black-box" CVD libraries), backed by a modern FastAPI server and a responsive React + Vite + Tailwind CSS frontend.

---

## 📑 Table of Contents
- [What the Project Does](#what-the-project-does)
- [Folder Structure](#folder-structure)
- [System Architecture & Processing Pipeline](#system-architecture--processing-pipeline)
- [Setup & Running](#setup--running)
  - [1. Backend Setup](#1-backend-setup)
  - [2. Frontend Setup](#2-frontend-setup)
- [Running the Tests](#running-the-tests)
- [Running the Evaluation Script (`evaluate.py`)](#running-the-evaluation-script-evaluatepy)
- [Interpreting Delta-E ($\Delta E$) Metrics](#interpreting-delta-e-delta-e-metrics)
- [Limitations & Practical Considerations](#limitations--practical-considerations)
- [Viva & Technical Reference](#viva--technical-reference)

---

## What the Project Does

1. **CVD Simulation (Machado et al. 2009):**
   - Accurately models **Protanopia** (L-cone absent/shifted), **Deuteranopia** (M-cone absent/shifted), and **Tritanopia** (S-cone absent/shifted).
   - Computes calculations in physically-linear RGB space by removing sRGB gamma, applying a 3×3 spectral projection matrix, and re-encoding with the IEC 61966-2-1 transfer curve.
   - Supports continuous severity interpolation from $0.0$ (normal trichromat) to $1.0$ (complete dichromat).
2. **Daltonization (Error-Map Redistribution):**
   - Calculates the loss signal: $\mathbf{E} = \text{Original} - \text{Simulated}$.
   - Shifts confusing red/green chromatic information into the blue channel and luminance using a configurable transfer matrix $\mathbf{M}$.
3. **Targeted Correction:**
   - Converts the image to HSV to isolate confusing hue bands (reds, greens, oranges, browns).
   - Applies morphological opening (noise removal) and closing (hole filling) to form a smooth binary mask.
   - Daltonizes only pixels within the mask, keeping background and unaffected regions unchanged.
4. **Pseudo-Color Mode:**
   - Maps ITU-R BT.709 grayscale luminance onto perceptually uniform, CVD-safe colormaps (**Viridis** or **Cividis**).
5. **Interactive Frontend:**
   - Drag-and-drop file upload (PNG/JPEG ≤ 10 MB).
   - Interactive Before/After split slider.
   - 4-way comparison grid (Original, Simulated, Corrected, Corrected-then-Simulated).
   - Instant PNG download of processed results.
   - High-contrast, dark-mode-ready, accessible interface.

---

## Folder Structure

```
├── backend/
│   ├── main.py                  # FastAPI application & REST endpoints
│   ├── evaluate.py              # Batch benchmark & comparison generator
│   ├── requirements.txt         # Pinned Python dependencies
│   ├── processing/              # Core hand-implemented processing modules
│   │   ├── __init__.py
│   │   ├── color_spaces.py      # sRGB ↔ linear RGB, RGB ↔ HSV, RGB → CIELAB
│   │   ├── simulation.py        # Machado 2009 matrices & severity interpolation
│   │   ├── daltonize.py         # Error-map daltonization & pseudo-coloring
│   │   ├── segmentation.py      # HSV hue masking & morphological cleanup
│   │   └── metrics.py           # CIE 1976 ΔE₇₆ and region statistics
│   └── tests/
│       ├── test_simulation.py   # Identity @ sev 0, range, and effect tests
│       ├── test_daltonize.py    # Clipping, shapes, and targeted mask tests
│       └── test_api.py          # FastAPI endpoint integration tests
├── frontend/
│   ├── package.json             # React, Vite, Tailwind CSS v3 dependencies
│   ├── vite.config.js           # Vite dev server configuration (port 5173)
│   ├── tailwind.config.js       # Tailwind CSS v3 configuration (darkMode: 'class')
│   ├── postcss.config.js
│   ├── index.html
│   └── src/
│       ├── App.jsx              # App layout, dark mode, React Router
│       ├── main.jsx
│       ├── index.css
│       ├── components/          # Reusable UI components
│       │   ├── Navbar.jsx
│       │   ├── ImageDropzone.jsx
│       │   ├── ControlPanel.jsx
│       │   ├── BeforeAfterSlider.jsx
│       │   ├── ComparisonGrid.jsx
│       │   ├── MetricsDisplay.jsx
│       │   └── Toast.jsx
│       ├── pages/
│       │   ├── ConverterPage.jsx # Main image converter page
│       │   └── AboutPage.jsx     # Scientific background & limitations
│       └── utils/
│           └── api.js           # Fetch API client for backend communication
├── samples/                     # Test images (Ishihara plates, transit maps, etc.)
├── evaluation_output/           # Generated 4-way composites & results.csv
└── README.md                    # Project documentation
```

---

## System Architecture & Processing Pipeline

```
  +------------------+
  |  Original sRGB   |
  +--------+---------+
           |
           v
  +-------------------------------------------------------+
  |  sRGB -> Linear RGB (IEC 61966-2-1 piecewise gamma)  |
  +--------+----------------------------------------------+
           |
           +---------------------------------+
           |                                 |
           v                                 v
+------------------------+      +--------------------------+
| Machado Matrix (sev s) |      | Targeted HSV Mask        |
| M_eff = (1-s)I + s*M   |      | H in [0,45] U [80,160]   |
+----------+-------------+      | Morphological Open/Close |
           |                    +------------+-------------+
           v                                 |
+------------------------+                   |
| Linear -> sRGB uint8   |                   |
| Simulated Image (S)    |                   |
+----------+-------------+                   |
           |                                 |
           v                                 |
+------------------------------------+       |
| Error Signal: E = Original - S     |       |
+----------+-------------------------+       |
           |                                 |
           v                                 |
+------------------------------------+       |
| Channel Shift: shift = M_dalton * E|       |
| Corrected = Original + shift       |       |
+----------+-------------------------+       |
           |                                 |
           +-----------------+---------------+
                             |
                             v
              +------------------------------+
              | Blend using Targeted Mask    |
              | (or Global full-frame)       |
              +--------------+---------------+
                             |
                             v
              +------------------------------+
              | Final Daltonized Image       |
              +------------------------------+
```

---

## Setup & Running

### Prerequisites
- **Python**: 3.11 or higher
- **Node.js**: 18.0 or higher (v24+ supported)
- **npm**: 9.0 or higher

---

### 1. Backend Setup

Open a terminal and navigate to `/backend`:

```powershell
# Navigate to backend directory
cd backend

# Create a virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1
# On Linux/macOS: source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt

# Start the development server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- **API Base URL**: `http://localhost:8000`
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### 2. Frontend Setup

Open a second terminal and navigate to `/frontend`:

```powershell
# Navigate to frontend directory
cd frontend

# Install dependencies (React, Vite, Tailwind CSS v3, Lucide icons)
npm install

# Start the Vite development server
npm run dev
```

- **Frontend App URL**: [http://localhost:5173](http://localhost:5173)

---

## Running the Tests

ChromaAssist includes 41 comprehensive automated tests covering mathematical properties, clipping, shapes, and API endpoints.

From the `backend` folder with the virtual environment activated:

```powershell
# Run all unit and integration tests
pytest tests\ -v

# Run only numerical and simulation unit tests
pytest tests\test_simulation.py tests\test_daltonize.py -v

# Run only FastAPI integration tests
pytest tests\test_api.py -v
```

### Test Coverage Highlights
- **Identity at Severity 0**: Protanopia, Deuteranopia, and Tritanopia at severity 0 return pixel-identical images ($\pm 1$ LSB float round-trip tolerance).
- **Bound Guarantee**: All outputs stay strictly within `[0, 255]`.
- **Dichromacy Differentiation**: Severity 1.0 produces statistically meaningful colour shifts on chromatic images.
- **File Validation**: Non-PNG/JPEG uploads are rejected with HTTP 400; uploads $> 10\text{ MB}$ return HTTP 413.

---

## Running the Evaluation Script (`evaluate.py`)

The batch evaluation script processes all images in `/samples` (e.g., Ishihara plates, transit diagrams, color charts), runs both global and targeted daltonization for Protanopia and Deuteranopia at severity 1.0, records $\Delta E$ metrics into a CSV, prints a summary table, and generates 4-panel visual composites.

```powershell
cd backend
python evaluate.py
```

### Optional Arguments
```powershell
python evaluate.py --samples-dir "path/to/samples" --output-dir "path/to/output"
```

### Outputs Generated in `/evaluation_output`:
1. **`results.csv`**: Structured benchmark metrics for all tested image/deficiency/method combinations.
2. **`*_protanopia_global.png`**, **`*_deuteranopia_targeted.png`**, etc.: High-resolution 4-panel comparison images containing:
   - Panel 1: Original image
   - Panel 2: Simulated CVD view
   - Panel 3: Daltonized corrected image
   - Panel 4: Predicted perception of corrected image by a CVD viewer

---

## Interpreting Evaluation & Quality Metrics

ChromaAssist evaluates both **global perceptual deviation** and **targeted pair discriminability** using the standard **CIE 1976 $\Delta E_{76}$** formula computed in the CIELAB color space:

$$\Delta E = \sqrt{(\Delta L^*)^2 + (\Delta a^*)^2 + (\Delta b^*)^2}$$

### 1. Pair Discriminability Metric (Primary Goal)

The true measure of daltonization success is whether **confusable color pairs (such as red and green) become distinguishable** to the color-deficient viewer.

1. **Group Segmentation**: Red/orange/brown pixels and green/olive pixels are segmented in HSV space.
2. **Simulated Baseline ($\Delta E$ Pair Orig)**: We compute the mean CIELAB color of both groups in the *simulated original image* and measure the $\Delta E$ between them. In complete deuteranopia, this distance collapses significantly (e.g. down to 11–15 units), meaning reds and greens look almost identical.
3. **Corrected Perception ($\Delta E$ Pair Corr)**: We compute the mean CIELAB color of both groups in the *simulated corrected image* and measure the $\Delta E$ between them.
4. **Discriminability Gain (%)**: $\frac{\Delta E_{\text{corr}} - \Delta E_{\text{orig}}}{\Delta E_{\text{orig}}} \times 100\%$.

> [!IMPORTANT]
> **For Pair Discriminability:**
> **HIGHER is better.** A larger $\Delta E$ between red and green means the daltonized image successfully restores contrast (via lightness and blue shifts), allowing the viewer to clearly separate the two colors (e.g., +80% to +165% improvement on Ishihara plates).

---

### 2. Whole-Image Perceptual Loss ($\Delta E$ Lost Info)

| Column | What It Measures | Desired Direction |
|---|---|---|
| **$\Delta E$ Lost Info: Original** | Mean pixel-by-pixel $\Delta E$ between the original and its CVD simulation. | Baseline perceptual loss across the entire scene. |
| **$\Delta E$ Lost Info: Corrected** | Mean pixel-by-pixel $\Delta E$ between the corrected image and its CVD simulation. | **Lower is better.** Indicates that the viewer's view of the corrected image deviates less from the intended scene than the uncorrected baseline. |

---

### 3. Sample Images Breakdown

The test suite in `/samples` contains three programmatically generated benchmark test patterns designed to rigorously stress-test CVD edge cases:

1. **`ishihara_plate_8.png`** *(Generated)*: A synthetic pseudoisochromatic Ishihara test plate consisting of randomized stippled dots where the numeral "8" is drawn with red/orange dots ($H \in [0^\circ, 35^\circ]$) embedded in a background of green/olive dots ($H \in [90^\circ, 135^\circ]$).
2. **`metro_transit_map.png`** *(Generated)*: A schematic public transit map featuring crossing red ($225, 30, 30$), green ($30, 180, 50$), blue ($30, 90, 220$), and orange ($240, 140, 20$) subway lines with white station nodes.
3. **`apples_and_pears.png`** *(Generated)*: A multi-object still-life pattern with overlapping red apples, green pears, and brown stems against a neutral light-gray background.

*(Any additional real-world photographs or scanned medical Ishihara plates placed into `/samples` will automatically be detected and benchmarked by `evaluate.py`.)*

---

## Limitations & Practical Considerations

While daltonization is a valuable assistive technology, it is important to understand its scientific limitations:

1. **Distinction over Naturalness:**
   Daltonization is designed to make confused hues **distinguishable**, not to recreate true physiological color vision. By routing red/green contrast into blue and brightness, the resulting image will look unnatural, tinted, or exaggerated to trichromats (people with normal color vision).
2. **Individual Variation:**
   Color vision deficiency exists on a continuum. Two individuals diagnosed with deuteranomaly may have different spectral sensitivities depending on their specific cone photopigment variants. A severity slider allows tuning the correction intensity to individual needs.
3. **Clipping & Dynamic Range:**
   Because shifting chromatic errors into remaining channels adds energy to the signal, bright saturated colors can saturate or clip at 255. ChromaAssist handles this through strict non-wrapping clipping.
4. **Information Trade-off:**
   Since a 2-cone system has 1 fewer degree of freedom than a 3-cone system, projecting 3D color data into a 2D perceptual space will inevitably involve trade-offs (e.g., slight loss of contrast in natively blue regions when blue is used to encode red/green error).

---

## Viva & Technical Reference

When presenting this project in a viva or technical review, key implementation highlights include:

- **Why sRGB gamma removal is mandatory:** Matrix multiplication in non-linear sRGB space is physically incorrect because pixel values do not represent linear photon counts. Gamma de-quantization ($C_{\text{linear}} = ((C+0.055)/1.055)^{2.4}$) linearizes the light intensities before the 3×3 Machado transformation is applied.
- **Machado et al. 2009 physiological model:** Unlike older dichromacy models (e.g. Brettel 1997) that project onto arbitrary planes in LMS space, Machado uses experimentally measured cone absorption spectra to compute a linear transformation in RGB space that interpolates smoothly between normal vision ($I_{3\times3}$) and full dichromacy ($M_{\text{full}}$).
- **HSV Targeted Masking:** Global daltonization alters every pixel in the image, often tinting white, gray, or blue areas unnecessarily. Targeted mode isolates specific hue ranges ($0^\circ - 45^\circ$ and $80^\circ - 160^\circ$) using HSV thresholding, followed by morphological opening ($7\times7$ elliptical structuring element) to remove salt-and-pepper noise and closing to fill region holes.
- **CIELAB Conversion:** Implemented by hand via CIE XYZ (using D65 standard illuminant white point $[0.95047, 1.00000, 1.08883]$) and the cube-root transformation function $f(t)$ defined in CIE 1976.
