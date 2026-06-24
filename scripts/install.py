#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Install OCR dependencies into the skill's Python 3.10 environment.

Default: rapidocr-onnxruntime + pymupdf (CPU-capable, the default engine).
--unlimited: additionally install transformers for the Unlimited-OCR backend
             (still needs a CUDA-enabled torch + model download; see notes).
"""
import subprocess
import sys

DEFAULT_PKGS = ["rapidocr-onnxruntime", "pymupdf"]
UNLIMITED_PKGS = ["transformers>=4.57"]


def pip_install(pkgs):
    # Try the default PyPI first; fall back to the Tsinghua mirror where
    # pypi.org is slow/blocked (e.g. mainland China).
    attempts = [
        ([], "default PyPI"),
        (["-i", "https://pypi.tuna.tsinghua.edu.cn/simple",
          "--trusted-host", "pypi.tuna.tsinghua.edu.cn"], "Tsinghua mirror"),
    ]
    last_rc = 1
    for extra, label in attempts:
        cmd = [sys.executable, "-m", "pip", "install"] + extra + pkgs
        print("Running ({}): {}".format(label, " ".join(cmd)))
        last_rc = subprocess.call(cmd)
        if last_rc == 0:
            print("Installed via {}.".format(label))
            return 0
        print("-> {} failed (exit {}); trying next source...".format(label, last_rc))
    return last_rc


def main():
    unlimited = "--unlimited" in sys.argv
    print("Installing default OCR packages: {}".format(DEFAULT_PKGS))
    rc = pip_install(DEFAULT_PKGS)
    if rc != 0:
        print("ERROR: default install failed (exit {}).".format(rc))
        return rc
    if unlimited:
        print("\nInstalling Unlimited-OCR packages: {}".format(UNLIMITED_PKGS))
        rc = pip_install(UNLIMITED_PKGS)
        if rc != 0:
            print("WARN: unlimited install failed (exit {}).".format(rc))
        print("\nNOTE: Unlimited-OCR also needs:")
        print("  - CUDA-enabled torch, e.g.:")
        print("    pip install torch --index-url https://download.pytorch.org/whl/cu121")
        print("  - Model download on first run: baidu/Unlimited-OCR (several GB)")
    print("\nDone. Run check_env.py to verify.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
