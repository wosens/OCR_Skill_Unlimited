#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OCR over a single image, an image directory, or a PDF.

Default engine: RapidOCR (onnxruntime). Optional: Unlimited-OCR (delegated to
unlimited_ocr.py, NVIDIA GPU required).

Input type is auto-detected:
  .pdf              -> render pages to images, OCR each page
  image extension   -> single image
  directory         -> all images inside (use --recursive for subdirs)

One output file per source is written to --output-dir, and a JSON summary is
printed to stdout (RapidOCR's own log noise is redirected to stderr).
"""
import argparse
import contextlib
import io
import json
import os
import sys
import time
import traceback

IMG_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")


def log(msg):
    sys.stderr.write(str(msg) + "\n")
    sys.stderr.flush()


def collect_images(path, recursive):
    out = []
    if recursive:
        for root, _dirs, names in os.walk(path):
            for n in names:
                if n.lower().endswith(IMG_EXTS):
                    out.append(os.path.join(root, n))
    else:
        for n in os.listdir(path):
            full = os.path.join(path, n)
            if os.path.isfile(full) and n.lower().endswith(IMG_EXTS):
                out.append(full)
    return sorted(out)


def pdf_to_images(pdf_path, dpi):
    import fitz
    import tempfile

    doc = fitz.open(pdf_path)
    tmp_dir = tempfile.mkdtemp(prefix="ocr_pdf_")
    mat = fitz.Matrix(dpi / 72.0, dpi / 72.0)
    paths = []
    for i, page in enumerate(doc):
        out = os.path.join(tmp_dir, "page_{:04d}.png".format(i + 1))
        page.get_pixmap(matrix=mat).save(out)
        paths.append(out)
    doc.close()
    return paths


class RapidEngine:
    """Thin wrapper around rapidocr_onnxruntime.RapidOCR."""

    def __init__(self):
        from rapidocr_onnxruntime import RapidOCR
        self._engine = RapidOCR()

    def ocr(self, image_path):
        # RapidOCR may print debug lines to stdout; capture them so our stdout
        # stays a clean JSON document.
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            result, elapse = self._engine(image_path)
        if buf.getvalue():
            sys.stderr.write(buf.getvalue())
        items = []
        if result:
            for row in result:
                text = row[1]
                score = row[2] if len(row) > 2 else None
                items.append({
                    "text": text,
                    "score": (float(score) if score is not None else None),
                })
        return items, elapse


def render_text(items):
    return "\n".join(it["text"] for it in items if it["text"])


def write_output(output_dir, rel_stem, ext, content):
    os.makedirs(output_dir, exist_ok=True)
    safe = rel_stem.replace(os.sep, "__").replace("/", "__")
    out_path = os.path.join(output_dir, safe + ext)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    return out_path


def stem(path):
    return os.path.splitext(os.path.basename(path))[0]


def run_single(engine, image_path, fmt, page_label=None):
    items, elapse = engine.ocr(image_path)
    text = render_text(items)
    if fmt == "json":
        content = json.dumps(
            {"source": image_path, "items": items,
             "elapse": [float(x) for x in elapse] if elapse else []},
            ensure_ascii=False, indent=2)
    elif fmt == "md":
        body = "\n".join(it["text"] for it in items if it["text"])
        content = "## {}\n\n{}".format(page_label, body) if page_label else body
    else:  # text
        content = text
    return content, len(text)


def delegate_unlimited(args):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    unlimited_script = os.path.join(script_dir, "unlimited_ocr.py")
    import subprocess
    cmd = [sys.executable, unlimited_script, "--input", args.input,
           "--output-dir", args.output_dir or "uocr_out", "--format", args.format]
    log("Delegating to Unlimited-OCR backend.")
    sys.exit(subprocess.call(cmd))


def main():
    ap = argparse.ArgumentParser(description="OCR images / directories / PDFs (RapidOCR).")
    ap.add_argument("--input", required=True, help="image file, directory, or PDF")
    ap.add_argument("--output-dir", default="", help="output folder (default: ocr_output next to input)")
    ap.add_argument("--engine", choices=("rapidocr", "unlimited"), default="rapidocr")
    ap.add_argument("--format", choices=("text", "md", "json"), default="text")
    ap.add_argument("--recursive", action="store_true", help="recurse into subdirectories")
    ap.add_argument("--lang", default="ch", help="language hint (RapidOCR ships a Chinese+English model)")
    ap.add_argument("--dpi", type=int, default=300, help="PDF render DPI")
    args = ap.parse_args()

    if args.engine == "unlimited":
        return delegate_unlimited(args)

    inp = args.input
    if not os.path.exists(inp):
        print(json.dumps({"error": "input not found: " + inp}, ensure_ascii=False))
        return 1

    output_dir = args.output_dir or os.path.join(
        os.path.dirname(os.path.abspath(inp)) or ".", "ocr_output")

    # Build job list: (image_path, output_rel_stem, page_label_or_None)
    jobs = []
    is_pdf = inp.lower().endswith(".pdf")
    if is_pdf:
        log("Rendering PDF to images @ {} dpi ...".format(args.dpi))
        pages = pdf_to_images(inp, args.dpi)
        base = stem(inp)
        for idx, p in enumerate(pages, 1):
            jobs.append((p, "{}_page_{:04d}".format(base, idx), "Page {}".format(idx)))
    elif os.path.isdir(inp):
        imgs = collect_images(inp, args.recursive)
        if not imgs:
            print(json.dumps({"error": "no images found in directory: " + inp}, ensure_ascii=False))
            return 1
        for p in imgs:
            rel = os.path.relpath(p, inp)
            jobs.append((p, os.path.splitext(rel)[0], None))
    else:
        jobs.append((inp, stem(inp), None))

    log("Loading RapidOCR engine ...")
    engine = RapidEngine()
    log("Engine ready. {} job(s).".format(len(jobs)))

    ext_for = {"text": ".txt", "md": ".md", "json": ".json"}[args.format]

    results = []
    t0 = time.time()
    for idx, (image_path, out_stem, page_label) in enumerate(jobs, 1):
        t = time.time()
        try:
            content, chars = run_single(engine, image_path, args.format, page_label)
            out_path = write_output(output_dir, out_stem, ext_for, content)
            dt = time.time() - t
            log("  [{}/{}] {} -> {} ({} chars, {:.1f}s)".format(
                idx, len(jobs), os.path.basename(image_path),
                os.path.basename(out_path), chars, dt))
            results.append({"source": image_path, "output": out_path, "chars": chars,
                            "status": "ok", "seconds": round(dt, 2)})
        except Exception as e:
            dt = time.time() - t
            log("  [{}/{}] {} FAILED: {}".format(idx, len(jobs), os.path.basename(image_path), e))
            log(traceback.format_exc())
            results.append({"source": image_path, "output": None, "chars": 0,
                            "status": "failed", "error": str(e), "seconds": round(dt, 2)})

    total = len(results)
    ok = sum(1 for r in results if r["status"] == "ok")
    summary = {
        "engine": "rapidocr",
        "input": inp,
        "output_dir": output_dir,
        "format": args.format,
        "results": results,
        "summary": {"total": total, "ok": ok, "failed": total - ok,
                    "seconds": round(time.time() - t0, 2)},
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
