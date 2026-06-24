# OCR Skill for Claude Code

[English](README.md) | [中文](README_zh.md)

A [Claude Code](https://docs.claude.com/en/docs/claude-code) skill that recognizes/extracts text from **images and PDFs** via OCR. Supports single image, batch directories, and multi-page PDF; Chinese + English + multilingual.

Two engines:
- **RapidOCR** (default) — fast, lightweight, runs on **CPU**, no GPU needed. Good for screenshots, photos, scans, general text.
- **Unlimited-OCR** (optional) — Baidu's high-fidelity, **layout-preserving** document parser (Markdown output). Needs an **NVIDIA GPU** + several-GB model download. Use only when you need table/layout reconstruction.

## Requirements

- **Python 3.9–3.12** (3.13+ has no `onnxruntime`/`paddle` wheels yet). Any of 3.10 / 3.11 / 3.12 works.
- The skill **auto-detects** your Python (including via the Windows `py` launcher) — no path editing required.
- RapidOCR: CPU is fine. Unlimited-OCR: NVIDIA GPU + CUDA-enabled torch.

## Install

Clone into your Claude skills folder:

```bash
# macOS / Linux
git clone https://github.com/wosens/OCR_Skill_Unlimited.git ~/.claude/skills/ocr

# Windows (Git Bash / cmd)
git clone https://github.com/wosens/OCR_Skill_Unlimited.git "%USERPROFILE%\.claude\skills\ocr"
```

Then install dependencies (run from the skill directory):

```bash
python scripts/check_env.py     # shows which Python is used + what's missing
python scripts/install.py       # installs RapidOCR + PyMuPDF (default engine)
```

`install.py` tries the default PyPI first and automatically falls back to a mirror if the default is blocked/slow.

## Usage

Once installed, just ask Claude Code in natural language — e.g. *"OCR this image"*, *"extract text from this PDF"*, *"batch-recognize all images in this folder"* — and the skill is invoked automatically.

You can also run the script directly:

```bash
# single image
python scripts/ocr.py --input photo.jpg --format text

# a whole folder (recursive)
python scripts/ocr.py --input ./scans --recursive --format text

# a PDF (each page -> text)
python scripts/ocr.py --input doc.pdf --format md
```

Options: `--input` · `--output-dir` (default `ocr_output/` next to input) · `--engine rapidocr|unlimited` · `--format text|md|json` · `--recursive` · `--lang` (default `ch`) · `--dpi` (PDF, default 300).

Each input produces one `.txt`/`.md`/`.json` file, and a JSON summary is printed to stdout.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `No Python 3.9-3.12 found` | Install Python 3.10/3.11/3.12 from python.org, then re-run `check_env.py` |
| `ModuleNotFoundError: rapidocr_onnxruntime` | Run `python scripts/install.py` |
| pip install fails (SSL/network) | `install.py` auto-falls back to a mirror; or set one manually: `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn rapidocr-onnxruntime pymupdf` |
| `python` points to 3.13+ | Run `check_env.py` and use the `python_path` it reports in place of `python` |
| Unlimited-OCR OOM on low-VRAM GPU | Use `--config gundam`; prefer ≥8 GB VRAM for multi-page docs |

## How it works

- `scripts/check_env.py` — read-only environment probe (auto-detects Python, checks packages/GPU, prints JSON + next step).
- `scripts/install.py` — installs dependencies (default engine, or `--unlimited` for the GPU backend).
- `scripts/ocr.py` — core OCR: image / directory / PDF → text/Markdown/JSON.
- `scripts/unlimited_ocr.py` — optional Unlimited-OCR (GPU) backend.
- `references/engines.md` — engine comparison.

## License

MIT (see [LICENSE](LICENSE)). This skill only *calls* the OCR engines; the engines themselves (RapidOCR / Unlimited-OCR) are installed by each user from their official sources and retain their own licenses.
