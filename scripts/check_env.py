#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only environment check for the OCR skill.

Auto-detects a suitable Python 3.9-3.12 interpreter (the running one, or one
on PATH / via the Windows `py` launcher) and reports THAT interpreter's
packages and GPU as JSON. Safe to run under any Python version — it will still
locate a 3.10 even if invoked under 3.13/3.14.
"""
import glob
import json
import os
import shutil
import subprocess
import sys

VERSION_MIN = (3, 9)
VERSION_MAX = (3, 12)
PACKAGES = ["rapidocr_onnxruntime", "onnxruntime", "fitz", "torch", "transformers"]


def _run(cmd, code):
    try:
        return subprocess.check_output(
            cmd + ["-c", code], text=True, stderr=subprocess.DEVNULL, timeout=20).strip()
    except Exception:
        return None


def _version_tuple(cmd):
    out = _run(cmd, "import sys;print('%d.%d.%d'%sys.version_info[:3])")
    if not out:
        return None
    try:
        return tuple(int(x) for x in out.split("."))
    except Exception:
        return None


def _iter_pythons():
    """Yield candidate python executables from many sources (dedup'd)."""
    import glob

    seen = set()

    def _emit(p):
        if not p:
            return
        try:
            rp = os.path.realpath(p)
        except Exception:
            rp = p
        if rp not in seen and os.path.isfile(rp):
            seen.add(rp)
            yield rp

    # 1) the running interpreter
    for x in _emit(sys.executable):
        yield x

    # 2) ALL python executables found on PATH (not only the first match).
    #    On Windows every install is named python.exe, so we scan every PATH dir.
    is_nt = os.name == "nt"
    names = ("python",) if is_nt else ("python3.12", "python3.11", "python3.10", "python3.9", "python3", "python")
    exts = (".exe",) if is_nt else ("",)
    for d in os.environ.get("PATH", "").split(os.pathsep):
        if not d:
            continue
        for name in names:
            for ext in exts:
                for x in _emit(os.path.join(d, name + ext)):
                    yield x

    # 3) Windows `py` launcher: list ALL registered interpreters.
    if is_nt and shutil.which("py"):
        try:
            out = subprocess.check_output(["py", "--list-paths"], text=True,
                                          stderr=subprocess.DEVNULL, timeout=15)
            for line in out.splitlines():
                tok = line.strip().split()
                if tok:
                    for x in _emit(tok[-1]):
                        yield x
        except Exception:
            pass

    # 4) Common Windows install locations (catches installs not on PATH).
    if is_nt:
        roots = []
        for env in ("LOCALAPPDATA", "PROGRAMFILES", "PROGRAMFILES(X86)"):
            b = os.environ.get(env)
            if b:
                roots += [os.path.join(b, "Programs", "Python"), b]
        roots += ["C:\\", "D:\\Program Files\\Python", "E:\\Program Files\\Python"]
        for root in roots:
            for pat in (os.path.join(root, "Python3*", "python.exe"),
                        os.path.join(root, "python.exe")):
                for p in glob.glob(pat):
                    for x in _emit(p):
                        yield x


def find_python():
    """Return (exe_path, version_tuple) for the first Python 3.9-3.12 found."""
    for exe in _iter_pythons():
        v = _version_tuple([exe])
        if v and VERSION_MIN <= v[:2] <= VERSION_MAX:
            return exe, v
    return None, None


def has_pkg(python_exe, mod):
    return _run([python_exe],
                "import importlib.util as u;print(1 if u.find_spec('%s') else 0)" % mod) == "1"


def gpu_info(python_exe):
    code = ("import torch\n"
            "print('1' if torch.cuda.is_available() else '0')\n"
            "if torch.cuda.is_available():\n"
            "    p=torch.cuda.get_device_properties(0)\n"
            "    print(p.name); print(p.total_memory/1024**3)\n")
    out = _run([python_exe], code)
    if out is None:
        return {"available": False, "note": "torch not installed"}
    lines = out.splitlines()
    if lines and lines[0] == "1":
        name = lines[1] if len(lines) > 1 else ""
        vram = float(lines[2]) if len(lines) > 2 else 0.0
        return {"available": True, "name": name, "vram_gb": round(vram, 1)}
    return {"available": False}


def main():
    python_exe, version = find_python()
    if not python_exe:
        print(json.dumps({
            "ok": False,
            "error": "No Python 3.9-3.12 found on PATH or via `py` launcher.",
            "hint": "Install Python 3.10/3.11/3.12 from https://www.python.org/ then re-run check_env.py.",
            "current_python": "{}.{}.{}".format(*sys.version_info[:3]),
        }, ensure_ascii=False, indent=2))
        return 1

    pkgs = {m: has_pkg(python_exe, m) for m in PACKAGES}
    gpu = gpu_info(python_exe)

    missing_default = []
    if not pkgs["rapidocr_onnxruntime"]:
        missing_default.append("rapidocr-onnxruntime")
    if not pkgs["fitz"]:
        missing_default.append("pymupdf")
    missing_unlimited = []
    if not pkgs["torch"]:
        missing_unlimited.append("torch")
    if not pkgs["transformers"]:
        missing_unlimited.append("transformers")

    py_short = python_exe if " " not in python_exe else '"' + python_exe + '"'
    if missing_default:
        next_step = "Run: {} scripts/install.py".format(py_short)
    elif missing_unlimited:
        next_step = "Default engine ready. For Unlimited-OCR (GPU): {} scripts/install.py --unlimited".format(py_short)
    else:
        next_step = "All engines ready."

    status = {
        "ok": True,
        "python_path": python_exe,
        "python_version": "{}.{}.{}".format(*version),
        "packages": pkgs,
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
