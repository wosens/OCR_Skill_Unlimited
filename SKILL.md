---
name: ocr
description: CROSS-PLATFORM OCR (Python + RapidOCR PP-OCRv4; runs on Windows / macOS / Linux). Use this when the user needs macOS/Linux support, is NOT on Windows x64, or explicitly wants the Python version — otherwise the DEFAULT on Windows is 'ocr-cpp' (native C++, faster, zero-dependency). Supports single image, batch directories, and multi-page PDF. Triggers on "OCR", "文字识别", "识别图片", "提取文字", "图片转文字", "图片识字", "扫描件转文本" + "跨平台", "macOS", "Linux", "Python".
---

# OCR Skill

Recognize text from images and PDFs. Two engines:

- **RapidOCR** (default): fast, lightweight, CPU-friendly, Chinese + English. Use for almost all OCR needs.
- **Unlimited-OCR** (optional, NVIDIA GPU only): high-fidelity, layout-preserving document parsing → Markdown. Use only for layout/table reconstruction from documents, with an NVIDIA GPU present.

## Requirements

- **Python 3.9–3.12** (3.13+ has no onnxruntime/paddle wheels). Any of 3.10/3.11/3.12 works.
- The skill auto-detects the interpreter — no manual path config needed.
- RapidOCR runs on **CPU** (no GPU required). Unlimited-OCR needs an **NVIDIA GPU**.

## First-time setup (run once)

Run from this skill's directory (where `SKILL.md` lives):

```bash
# 1) Check environment — prints which Python it will use + what's missing
python scripts/check_env.py
```
If `check_env.py` reports missing packages, install them:
```bash
# 2) Install the default engine (RapidOCR + PyMuPDF)
python scripts/install.py
```
Notes:
- If your default `python` is 3.13+, `check_env.py` still finds a 3.10–3.12 if one is installed and prints its path as `python_path` — use that path in place of `python` below.
- `install.py` tries the default PyPI first, then falls back to a mirror automatically.

## Run OCR

`scripts/ocr.py` auto-detects the input type by extension (`.pdf` → PDF; image extension → single image; directory → batch).

**Single image:**
```bash
python scripts/ocr.py --input "<image>" --format text
```
**Batch a directory (recursive):**
```bash
python scripts/ocr.py --input "<dir>" --recursive --format text
```
**PDF (each page → text):**
```bash
python scripts/ocr.py --input "<file.pdf>" --format md
```

**Options:** `--input` (required) · `--output-dir` (default `ocr_output/` next to input) · `--engine rapidocr|unlimited` (default `rapidocr`) · `--format text|md|json` (default `text`) · `--recursive` · `--lang` (default `ch`) · `--dpi` (PDF, default 300).

**Output:** one file per source (same base name, `.txt`/`.md`/`.json`) into `--output-dir`; a JSON summary is also printed to **stdout** for parsing.

## Engine selection

| Situation | Engine |
|---|---|
| Default OCR: screenshots, photos, scans, general text | `rapidocr` |
| Layout-preserving Markdown / table reconstruction + NVIDIA GPU | `unlimited` |

## Unlimited-OCR (optional, GPU)

Only when an NVIDIA GPU is present and layout-preserving parsing is required:
```bash
python scripts/unlimited_ocr.py --input "<doc>" --output-dir "uocr_out" --config gundam
```
First run downloads model `baidu/Unlimited-OCR` (several GB) and needs a CUDA-enabled torch. On low-VRAM GPUs (≤6 GB) prefer `--config gundam`; large multi-page jobs may OOM.

## Troubleshooting

- **`No Python 3.9-3.12 found`**: install Python 3.10/3.11/3.12 from https://www.python.org/ , then re-run `check_env.py`.
- **`ModuleNotFoundError: rapidocr_onnxruntime`**: run `python scripts/install.py`.
- **pip install fails (SSL / network)**: `install.py` auto-falls back to a mirror; if it still fails, set one manually:
  `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn rapidocr-onnxruntime pymupdf`.
- **Directory outputs are flattened**: `sub/a.jpg` → `sub__a.txt` in `--output-dir`.

## Benchmark (reference, same Windows x64 machine, CPU)

Test image `benchmark/sample.jpg` — **564×533, 93 KB, 12 lines of Chinese + English**:

![benchmark sample — 12 lines of Chinese + English](benchmark/sample.jpg)

| Metric | This skill (ocr, PP-OCRv4) |
|---|---|
| End-to-end wall time | 6.3 s |
| Inference (engine-reported) | 5.48 s |
| Characters recognized | 471 |

Recognized text (excerpt — note English word spacing is dropped, a known RapidOCR behavior):
```
人生活的真实写照：善有善报，恶有善报
everyman'slife:goodbegetsgood,andevilleadstoevil.
We Chinese have a saying:If a man plants melons,he will reap
```
On the same image the native `ocr-cpp` skill takes **3.6 s** end-to-end (~45% faster) and preserves English spacing better. Use this Python `ocr` skill when you need **cross-platform (macOS/Linux)** or **PDF** support.
