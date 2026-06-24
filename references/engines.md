# OCR Engine Selection

| Engine | Best for | Key dependencies | GPU | Install |
|---|---|---|---|---|
| **RapidOCR** (onnxruntime) | General text, screenshots, scans, Chinese/English; default engine | `rapidocr-onnxruntime`, `pymupdf`, `onnxruntime` | Optional (runs on CPU) | `scripts/install.py` |
| PaddleOCR (not wired by default) | Same model family as RapidOCR, paddle ecosystem | `paddlepaddle`, `paddleocr` | Optional | manual pip |
| **Unlimited-OCR** (optional) | Layout-preserving document parsing, tables, long docs → Markdown | `transformers`, CUDA `torch`, model `baidu/Unlimited-OCR` (several GB) | **Required (NVIDIA)** | `scripts/install.py --unlimited` |

## When to use which

- **Default to RapidOCR.** It is fast, runs on CPU, and matches PaddleOCR accuracy for plain text recognition. This is the right choice for screenshots, photos, scanned pages, and general Chinese/English text.
- **Reach for Unlimited-OCR only when** the user needs layout/table reconstruction or high-fidelity structured Markdown from documents, and an NVIDIA GPU is available.
- RapidOCR is text-only (no layout). If the user says "reconstruct the table" or "preserve the layout", that is the signal to consider Unlimited-OCR.

## Notes on this machine

- Python 3.10 at `D:/Program Files/Python/Python310/python.exe` already has `onnxruntime`, `torch`, `cv2`, `PIL`, `numpy`.
- GPU: NVIDIA RTX 3060 Laptop (~6 GB). Unlimited-OCR may OOM here; prefer single-image `gundam` mode. For heavy multi-page document parsing, a ≥8 GB GPU is recommended.
