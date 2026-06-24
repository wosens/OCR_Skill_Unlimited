#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Optional Unlimited-OCR document parsing backend (NVIDIA GPU required).

Wraps the official Transformers inference from baidu/Unlimited-OCR. First run
downloads the model (several GB). On low-VRAM GPUs (e.g. 6GB) prefer
single-image 'gundam' mode and expect possible OOM.
"""
import argparse
import json
import os
import sys
import tempfile


def log(m):
    sys.stderr.write(str(m) + "\n")
    sys.stderr.flush()


def pdf_to_images(pdf_path, dpi):
    import fitz
    doc = fitz.open(pdf_path)
    tmp = tempfile.mkdtemp(prefix="uocr_pdf_")
    mat = fitz.Matrix(dpi / 72.0, dpi / 72.0)
    paths = []
    for i, page in enumerate(doc):
        out = os.path.join(tmp, "page_{:04d}.png".format(i + 1))
        page.get_pixmap(matrix=mat).save(out)
        paths.append(out)
    doc.close()
    return paths


def check_gpu():
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA not available. Unlimited-OCR requires an NVIDIA GPU.")
    p = torch.cuda.get_device_properties(0)
    vram = p.total_memory / 1024**3
    log("GPU: {} ({:.1f} GB)".format(p.name, vram))
    if vram < 8:
        log("WARNING: <8GB VRAM detected; OOM risk. Use single-image --config gundam.")
    return p


def load(model_name):
    import torch
    from transformers import AutoModel, AutoTokenizer
    log("Loading tokenizer/model {} ...".format(model_name))
    tok = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModel.from_pretrained(
        model_name, trust_remote_code=True, use_safetensors=True,
        torch_dtype=torch.bfloat16).eval().cuda()
    return tok, model


def infer_single(tok, model, image_file, output_dir, config):
    common = dict(prompt="document parsing.", output_path=output_dir, base_size=1024,
                  max_length=32768, no_repeat_ngram_size=35, save_results=True)
    if config == "gundam":
        model.infer(tok, image_file=image_file, image_size=640, crop_mode=True,
                    ngram_window=128, **common)
    else:
        model.infer(tok, image_file=image_file, image_size=1024, crop_mode=False,
                    ngram_window=128, **common)


def infer_multi(tok, model, image_files, output_dir):
    model.infer_multi(tok, prompt="Multi page parsing.", image_files=image_files,
                      output_path=output_dir, image_size=1024, max_length=32768,
                      no_repeat_ngram_size=35, ngram_window=1024, save_results=True)


def main():
    ap = argparse.ArgumentParser(description="Unlimited-OCR document parsing (GPU).")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output-dir", default="uocr_out")
    ap.add_argument("--model", default="baidu/Unlimited-OCR")
    ap.add_argument("--config", choices=("gundam", "base"), default="gundam")
    ap.add_argument("--format", choices=("text", "md", "json"), default="md")
    ap.add_argument("--dpi", type=int, default=300)
    args = ap.parse_args()

    check_gpu()
    os.makedirs(args.output_dir, exist_ok=True)
    tok, model = load(args.model)

    inp = args.input
    results = []
    if inp.lower().endswith(".pdf"):
        pages = pdf_to_images(inp, args.dpi)
        log("PDF -> {} pages, running multi-page parsing ...".format(len(pages)))
        infer_multi(tok, model, pages, args.output_dir)
        results = [{"source": inp, "pages": len(pages), "output_dir": args.output_dir, "status": "ok"}]
    elif os.path.isdir(inp):
        from glob import glob
        exts = ("*.png", "*.jpg", "*.jpeg", "*.webp", "*.bmp", "*.tif", "*.tiff")
        imgs = []
        for e in exts:
            imgs += glob(os.path.join(inp, "**", e), recursive=True)
        imgs = sorted(set(imgs))
        log("{} images, running multi-page parsing ...".format(len(imgs)))
        infer_multi(tok, model, imgs, args.output_dir)
        results = [{"source": inp, "images": len(imgs), "output_dir": args.output_dir, "status": "ok"}]
    else:
        log("Single image, config={} ...".format(args.config))
        infer_single(tok, model, inp, args.output_dir, args.config)
        results = [{"source": inp, "output_dir": args.output_dir, "config": args.config, "status": "ok"}]

    print(json.dumps({"engine": "unlimited", "model": args.model, "results": results}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
