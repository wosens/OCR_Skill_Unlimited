#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only environment check for the OCR skill. Prints JSON status + next step."""
import importlib
import json
import sys

PY_PATH = r"D:\Program Files\Python\Python310\python.exe"


def has(mod):
    try:
        importlib.import_module(mod)
        return True
    except Exception:
        return False


def gpu_info():
    try:
        import torch
        if torch.cuda.is_available():
            p = torch.cuda.get_device_properties(0)
            return {"available": True, "name": p.name,
                    "vram_gb": round(p.total_memory / 1024**3, 1)}
        return {"available": False}
    except Exception:
        return {"available": False, "note": "torch not installed or no CUDA"}


def main():
    rapid_ok = has("rapidocr_onnxruntime")
    fitz_ok = has("fitz")
    ort_ok = has("onnxruntime")
    torch_ok = has("torch")
    tf_ok = has("transformers")
    gpu = gpu_info()

    missing_default = []
    if not rapid_ok:
        missing_default.append("rapidocr-onnxruntime")
    if not fitz_ok:
        missing_default.append("pymupdf")

    missing_unlimited = []
    if not torch_ok:
        missing_unlimited.append("torch")
    if not tf_ok:
        missing_unlimited.append("transformers")

    if missing_default:
        next_step = "Install default engine: run scripts/install.py"
    elif missing_unlimited:
        next_step = "Default engine ready. For Unlimited-OCR (GPU): run scripts/install.py --unlimited"
    else:
        next_step = "All engines ready."

    status = {
        "python_path": PY_PATH,
        "python_version": "{}.{}.{}".format(*sys.version_info[:3]),
        "packages": {
            "rapidocr_onnxruntime": rapid_ok,
            "onnxruntime": ort_ok,
            "pymupdf_fitz": fitz_ok,
            "torch": torch_ok,
            "transformers": tf_ok,
        },
        "gpu": gpu,
        "default_engine_ready": not missing_default,
        "unlimited_engine_ready": (not missing_unlimited) and gpu.get("available", False),
        "missing_for_default": missing_default,
        "missing_for_unlimited": missing_unlimited,
        "next_step": next_step,
    }
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
