# OCR Skill（Claude Code 文字识别技能）

[English](README.md) | [中文](README_zh.md)

一个 [Claude Code](https://docs.claude.com/en/docs/claude-code) 技能，通过 OCR **识别 / 提取图片和 PDF 中的文字**。支持单张图片、批量目录、多页 PDF；中英文及多语种。

提供两种引擎：
- **RapidOCR**（默认）—— 快速、轻量，可在 **CPU** 上运行，无需 GPU。适合截图、照片、扫描件、通用文字。
- **Unlimited-OCR**（可选）—— 百度高保真、**保版式**文档解析（输出 Markdown）。需要 **NVIDIA GPU** + 数 GB 模型下载。仅在需要表格 / 版式还原时使用。

## 环境要求

- **Python 3.9–3.12**（3.13+ 暂无 `onnxruntime` / `paddle` wheel）。3.10 / 3.11 / 3.12 任一即可。
- 技能会**自动探测**你的 Python（含 Windows `py` launcher、PATH 全量扫描、常见安装目录）—— 无需手动配置路径。
- RapidOCR：CPU 即可。Unlimited-OCR：需 NVIDIA GPU + CUDA 版 torch。

## 安装

克隆到你的 Claude 技能目录：

```bash
# macOS / Linux
git clone https://github.com/wosens/OCR_Skill_Unlimited.git ~/.claude/skills/ocr

# Windows（Git Bash / cmd）
git clone https://github.com/wosens/OCR_Skill_Unlimited.git "%USERPROFILE%\.claude\skills\ocr"
```

然后在技能目录下安装依赖：

```bash
python scripts/check_env.py     # 显示将使用哪个 Python + 缺什么
python scripts/install.py       # 安装 RapidOCR + PyMuPDF（默认引擎）
```

`install.py` 会先尝试默认 PyPI，若被墙 / 慢则自动切换镜像源。

## 用法

安装完成后，直接用自然语言对 Claude Code 说即可 —— 例如「识别这张图的文字」「提取这个 PDF 的文字」「批量识别这个文件夹里的所有图片」，技能会自动被调用。

也可以直接运行脚本：

```bash
# 单张图片
python scripts/ocr.py --input photo.jpg --format text

# 整个目录（递归）
python scripts/ocr.py --input ./scans --recursive --format text

# PDF（每页 → 文字）
python scripts/ocr.py --input doc.pdf --format md
```

参数：`--input` · `--output-dir`（默认输入旁的 `ocr_output/`）· `--engine rapidocr|unlimited` · `--format text|md|json` · `--recursive` · `--lang`（默认 `ch`）· `--dpi`（PDF，默认 300）。

每个输入生成一个 `.txt` / `.md` / `.json` 文件，并在 stdout 打印 JSON 摘要。

## 常见问题

| 现象 | 解决 |
|---|---|
| `No Python 3.9-3.12 found` | 从 [python.org](https://www.python.org/) 安装 Python 3.10/3.11/3.12，再跑一次 `check_env.py` |
| `ModuleNotFoundError: rapidocr_onnxruntime` | 运行 `python scripts/install.py` |
| pip 安装失败（SSL / 网络） | `install.py` 会自动切镜像；或手动指定：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn rapidocr-onnxruntime pymupdf` |
| `python` 指向 3.13+ | 跑 `check_env.py`，用它报告的 `python_path` 代替 `python` |
| Unlimited-OCR 在低显存 GPU 上 OOM | 用 `--config gundam`；多页文档建议 ≥8 GB 显存 |

## 工作原理

- `scripts/check_env.py` —— 只读环境探测（自动找 Python、检查包 / GPU、输出 JSON + 下一步）。
- `scripts/install.py` —— 安装依赖（默认引擎，或 `--unlimited` 装 GPU 后端）。
- `scripts/ocr.py` —— 核心 OCR：图片 / 目录 / PDF → 文本 / Markdown / JSON。
- `scripts/unlimited_ocr.py` —— 可选的 Unlimited-OCR（GPU）后端。
- `references/engines.md` —— 引擎对比。

## 许可证

MIT（见 [LICENSE](LICENSE)）。本技能仅*调用* OCR 引擎；引擎本身（RapidOCR / Unlimited-OCR）由各用户从官方源自行安装，保留各自许可证。
