---
name: ocr
description: Extract/recognize text from images and PDFs via OCR. Use whenever the user wants to OCR, recognize text, or extract text from images (jpg/png/webp/bmp/tiff), screenshots, scanned documents, photos of text, or PDFs. Supports Chinese/English/multilingual, single image, batch directories, and multi-page PDF. Triggers on "OCR", "文字识别", "识别图片", "提取文字", "图片转文字", "图片识字", "扫描件转文本", "scan to text", "image to text".
---

# OCR Skill

Recognize text from images and PDFs. Two engines:

- **RapidOCR** (default): fast, lightweight, CPU-friendly, Chinese + English. Use for almost all OCR needs.
- **Unlimited-OCR** (optional, NVIDIA GPU only): high-fidelity document parsing that produces layout-preserving Markdown. Use only when the user wants layout/table reconstruction from documents AND an NVIDIA GPU is present.

## Python Environment

Python (3.10) is at: `D:/Program Files/Python/Python310/python.exe`

Required packages: `rapidocr-onnxruntime`, `pymupdf` (onnxruntime / numpy / cv2 / PIL are already installed in this environment).

**First use:** run `install.py` once (see Step 1) to install the OCR packages.

## Engine Selection

| Situation | Engine |
|---|---|
| Default OCR: screenshots, photos, scanned pages, general Chinese/English text | `rapidocr` |
| Need layout-preserving Markdown / table reconstruction from documents, and an NVIDIA GPU exists | `unlimited` |

## Step 1 — Check / Install Environment

Check (read-only, prints JSON status + next step):
```bash
"D:/Program Files/Python/Python310/python.exe" "C:/Users/Administrator/.claude/skills/ocr/scripts/check_env.py"
```

Install default engine (RapidOCR + PyMuPDF):
```bash
"D:/Program Files/Python/Python310/python.exe" "C:/Users/Administrator/.claude/skills/ocr/scripts/install.py"
```

Install optional Unlimited-OCR backend (adds transformers; also needs CUDA torch + model download):
```bash
"D:/Program Files/Python/Python310/python.exe" "C:/Users/Administrator/.claude/skills/ocr/scripts/install.py" --unlimited
```

## Step 2 — Run OCR

Core script: `scripts/ocr.py`. It auto-detects the input type by extension/path (`.pdf` → PDF; image extension → single image; directory → batch).

**Single image:**
```bash
"D:/Program Files/Python/Python310/python.exe" "C:/Users/Administrator/.claude/skills/ocr/scripts/ocr.py" --input "<image>" --format text
```

**Batch a directory (recursive):**
```bash
"D:/Program Files/Python/Python310/python.exe" "C:/Users/Administrator/.claude/skills/ocr/scripts/ocr.py" --input "<dir>" --recursive --format text
```

**PDF (each page → text):**
```bash
"D:/Program Files/Python/Python310/python.exe" "C:/Users/Administrator/.claude/skills/ocr/scripts/ocr.py" --input "<file.pdf>" --format md
```

**Options:**
- `--input` file or directory (required)
- `--output-dir` output folder (default: `ocr_output/` next to the input)
- `--engine` `rapidocr` (default) | `unlimited`
- `--format` `text` (default) | `md` | `json`
- `--recursive` include subdirectories (directory input only)
- `--lang` language hint (default `ch`; RapidOCR ships a Chinese+English model)
- `--dpi` PDF render DPI (default 300)

**Output:** one file per source (same base name, new extension) is written to `--output-dir`. A JSON summary is also printed to **stdout** — parse it to read results without re-opening the files.

## Step 3 — Use Results

Parse the stdout JSON summary:
```json
{"engine":"rapidocr","input":"...","output_dir":"...","format":"text",
 "results":[{"source":"...","output":"...","chars":123,"status":"ok","seconds":1.2}],
 "summary":{"total":1,"ok":1,"failed":0,"seconds":1.2}}
```
For full text, read the output files, or use `--format json` to get per-line boxes + confidence scores.

## Unlimited-OCR (optional, GPU)

Only when an NVIDIA GPU is present and layout-preserving parsing is explicitly required:
```bash
"D:/Program Files/Python/Python310/python.exe" "C:/Users/Administrator/.claude/skills/ocr/scripts/unlimited_ocr.py" --input "<doc>" --output-dir "uocr_out" --config gundam
```
Notes:
- First run downloads model `baidu/Unlimited-OCR` (several GB) and needs a CUDA-enabled torch.
- On a 6 GB GPU it may OOM — prefer single-image `--config gundam`, and avoid large multi-page jobs.

## Tips

- RapidOCR runs on CPU; no GPU is needed for the default engine.
- For low-quality scans, a higher PDF DPI (e.g. `--dpi 400`) improves accuracy.
- If a package is missing, re-run `install.py`; `check_env.py` reports exactly what is missing.
- Directory outputs are flattened: `sub/a.jpg` → `sub__a.txt` inside `--output-dir`.
