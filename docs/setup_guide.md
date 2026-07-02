# Environment Setup Guide (RTX 5090) — mHealth App Review Analysis Pipeline

> Written 2026-06-05 · Target machine: Windows 11 + RTX 5090 · Goal: consolidate two previously
> separate virtual environments (`torch-cu121`, `bert-topic-2`) into a **single stable environment**
> that reproduces the whole flow (collection, preprocessing, sentiment analysis, regression) with
> identical results.

---

## 0. Final configuration (quick reference)

| Item | Value |
|---|---|
| OS | Windows 11 Pro (build 26200), x64 (AMD64) |
| GPU | RTX 5090 (Blackwell, **sm_120**), driver 610.47 (supports up to CUDA 13.3) |
| Python | 3.13.12 (official python.org installer) |
| venv location | `C:\Users\<you>\venvs\medapp` (**outside Dropbox/OneDrive**) |
| Project folder | `<project root>` (code & data) |
| PyTorch | `torch 2.11.0+cu128` (bundled CUDA runtime) |
| Jupyter kernel | `Python (medapp)` |
| Reproducibility reference | `requirements.lock.txt` (all versions pinned) |

---

## 1. Key cautions (read before running)

1. **Run commands one line at a time.** Pasting multiple lines at once can concatenate them and run
   incorrectly (e.g., `pip freeze` mistakenly taking the next line's `-c` as an option and failing).
   One line → Enter → next line.
2. **Do not create the venv inside Dropbox/OneDrive.** Sync locks thousands of files in real time,
   breaking pip installs or corrupting the environment. Put the venv under `C:\Users\<you>\venvs\...`
   and keep only code/data in Dropbox.
3. **Install PyTorch from the cu128 index.** RTX 5090 (sm_120) works only with CUDA 12.8+ builds.
   A plain `pip install torch` causes `CUDA error: no kernel image is available`.
4. **No separate CUDA Toolkit needed.** The cu128 wheel bundles the CUDA runtime; the system only
   needs the NVIDIA driver (already installed).
5. **Use sentencepiece 0.2.1 or later.** 0.2.0 has no Python 3.13 wheel and tries to build from source
   on Windows and fails (tokenization results are identical regardless of version).
6. **Activating the venv does not change your current directory.** Always work from the project root so
   `pip install -r requirements.txt` and `from lib...` imports work.
7. **"Identical results" are preserved via cache, not re-runs.** See section 6 (reproducibility).

---

## 2. Check specs (Phase A)

> Run in Command Prompt (cmd) or PowerShell.

```
nvidia-smi
```
→ Check: **GPU model (RTX 5090)**, driver version, and **CUDA version (max supported)** at the top right.
CUDA 13.3 ≥ 12.8, so the 5090 requirement is met. If `nvidia-smi` is "not recognized," the driver is not installed.

```
echo %PROCESSOR_ARCHITECTURE%
```
→ Check: **`AMD64`** (64-bit). PyTorch ships only 64-bit wheels, so this value satisfies it.

```
systeminfo | findstr /B /C:"OS Name" /C:"OS Version" /C:"System Type"
```
→ Check: **Windows 11**, 64-bit. ⚠️ On localized (non-English) Windows the field names are localized;
filtering by the English labels returns nothing, so use the localized field names for your language.

```
where python
where conda
```
→ Check: leftover Python/conda. If only `...\WindowsApps\python.exe` appears, that is the
**Microsoft Store dummy stub, not a real Python** — effectively a blank slate. If `conda` is "not found,"
there is no conda.

---

## 3. Install Python (Phase B)

**Why this version**: Python 3.12 binary installers stopped at 3.12.10 (security-only afterward), and
3.14 has lagging compatibility for some research packages. In between, **3.13 — actively maintained with
broad ecosystem support — is optimal.**

1. Download: `https://www.python.org/ftp/python/3.13.12/python-3.13.12-amd64.exe`
2. On the first install screen, be sure to check **"Add python.exe to PATH."**
3. On the final screen, click **"Disable path length limit"** (removes the 260-char path limit — prevents
   `path too long` in deep dependency trees).

Verify:

```
python --version
```
→ Expect: `Python 3.13.12`

```
pip --version
```
→ Expect: a path pointing to `...\Programs\Python\Python313\...` (i.e., PATH points to the real install,
not the Store stub).

---

## 4. Build the unified venv (Phase C — 5 steps)

> Start location: open Command Prompt at the **project root** (where `lib` and `requirements.txt` are).
> In Explorer, open that folder and type `cmd` in the address bar → Enter to open cmd there.

### Step 1 — create & activate the venv (outside Dropbox)

```
python -m venv C:\Users\<you>\venvs\medapp
```
→ Expect: exits without error. (The venv is created under C:, your current location stays at the project folder.)

```
C:\Users\<you>\venvs\medapp\Scripts\activate
```
→ Expect: **`(medapp)`** prefix on the prompt, e.g., `(medapp) <project root>>`.

### Step 2 — refresh pip + install PyTorch (cu128)

```
python -m pip install --upgrade pip setuptools wheel
```
→ Expect: `Successfully installed ...` (fine if torch later reverts setuptools to 70.x).

```
pip install torch --index-url https://download.pytorch.org/whl/cu128
```
→ Expect: downloads the `torch-2.11.0+cu128 ... cp313` wheel (~2.8GB, a few minutes).
`Successfully installed ... torch-2.11.0+cu128`

```
python -c "import torch; print('torch:', torch.__version__); print('CUDA:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0)); print('cap:', torch.cuda.get_device_capability(0))"
```
→ Expect all of:
- `CUDA: True`
- `GPU: NVIDIA GeForce RTX 5090`
- `cap: (12, 0)` ← Blackwell sm_120 recognized
- ⚠️ The `Failed to initialize NumPy` warning here is **normal** (numpy not installed yet). It disappears after Step 3.

### Step 3 — install the remaining packages

> `requirements.txt` must be in the current folder (project root).

```
pip install -r requirements.txt
```
→ Expect:
- Final line `Successfully installed ...`, no red errors.
- **`sentencepiece-0.2.1`** installs from a wheel without building.
- Key pinned versions: `transformers-4.55.0`, `tokenizers-0.21.4`, `accelerate-1.10.0`, `openai-1.99.6`, `google-play-scraper-1.2.7`.

### Step 4 — register the Jupyter kernel + freeze versions

```
python -m ipykernel install --user --name medapp --display-name "Python (medapp)"
```
→ Expect: `Installed kernelspec medapp in ...`

```
pip freeze > requirements.lock.txt
```
→ Expect: `requirements.lock.txt` created in the project folder (shows as `requirements.lock` if
extensions are hidden). This file is the reproducibility reference.

```
python -c "import torch, numpy, pandas, scipy, sklearn, statsmodels, matplotlib, seaborn, transformers, sentencepiece, openai, google_play_scraper; print('imports OK')"
```
→ Expect: **`imports OK`** (12 core libraries import cleanly, numpy warning gone).

### Step 5 — (optional) end-to-end sentiment model check

> Downloads the DeBERTa-large model (~1.7GB) once (needed anyway when running 03).

```
python -c "from transformers import pipeline; clf = pipeline('zero-shot-classification', model='MoritzLaurer/deberta-v3-large-zeroshot-v2.0', device=0); print(clf('This app is very helpful', ['positive overall sentiment','negative overall sentiment'], multi_label=True))"
```
→ Expect:
- `Device set to use cuda:0` (inference on GPU)
- Scores like positive ≈ 0.95, negative ≈ 0.0003 (reasonable)
- ⚠️ The `hf_xet` warning can be ignored (affects download speed only).

---

## 5. What was excluded/included (design rationale)

**Included**: sentiment (transformers, sentencepiece, torch-cu128), collection (google-play-scraper),
preprocessing (openai, regex), stats/plots (numpy, pandas, scipy, scikit-learn, statsmodels, matplotlib,
seaborn), notebooks (jupyterlab, ipykernel).

**Deliberately excluded**:
- `bertopic / sentence-transformers / umap-learn / hdbscan / numba / llvmlite` — not imported by the
  published code. The numba stack is the most conflict-prone part on Python 3.13 + numpy 2.x, so
  excluding it directly improves stability. If you return to topic modeling, use a **separate dedicated environment**.
- `bitsandbytes` — its Windows install breaks often and is unnecessary for zero-shot inference.
- `nltk / emoji / langid / wordcloud / plotly` — not used by the current code.

---

## 6. Usage & reproducibility principles

**Daily use**
1. Activate the venv: `C:\Users\<you>\venvs\medapp\Scripts\activate`
2. When running notebooks, select the **`Python (medapp)`** kernel.
3. **Run from the project root** so `from lib...` imports work.

**Result identity (most important)**

Stages that inherently cannot yield identical results on re-run:
- **01 collection**: Google Play live data → re-scraping changes reviews/ratings.
- **02 GPT classification**: API calls (`gpt-5-2025-08-07`) → output varies with call time / model changes.
- **03 sentiment inference**: switching hardware from an old GPU (CUDA 12.1) to the RTX 5090 (CUDA 12.8+)
  changes floating-point accumulation order, so scores differ in the low-order digits (bit-exact match impossible).

Conversely, **the final analysis is deterministically reproducible**: regression/plots start from the
`scores_with_factors.csv` saved by 03, and statsmodels OLS / robust SE match to the reported digits
regardless of library version.

> **Principle**: keep the existing intermediate artifacts (raw reviews, `cleaned_reviews_*.csv`, GPT labels,
> `scores_with_factors.csv`) and, in a new environment, **re-run only the final analysis from those CSVs**.
> Run 01/02/03 only when producing new data (accepting the non-determinism above).

If you must re-run 03 on GPU: add `from transformers import set_seed; set_seed(42)` before inference.
Even so, scores differ from the old ones in the low-order digits, so **for exact reproduction, do not
re-run 03 — reuse the cached CSVs.**

---

## 7. Quick troubleshooting (symptom → cause/fix)

| Symptom | Cause / fix |
|---|---|
| `systeminfo \| findstr` returns blank | Localized Windows. Use localized field names instead of the English ones. |
| `nvidia-smi` not recognized | NVIDIA driver not installed/recognized → install the driver first |
| `CUDA error: no kernel image is available` | Plain torch installed → reinstall from the cu128 index |
| `sentencepiece` build fails during install | Using 0.2.0 → use `sentencepiece==0.2.1` |
| Permission/lock error during pip install | venv is inside Dropbox/OneDrive → move it outside sync |
| `pip freeze` says `no such option: -c` | Two commands merged onto one line → run one line at a time |
| `Failed to initialize NumPy` at Step 2 | Normal (numpy not installed). Gone after Step 3 |

---

## Appendix — requirements.txt contents

> torch is not included here (installed first from the cu128 index in Step 2). The statistics stack is
> left as ranges but pinned exactly to `requirements.lock.txt` after install.

```
# Sentiment (03): HuggingFace zero-shot DeBERTa-v3
transformers==4.55.0
tokenizers==0.21.4
huggingface-hub==0.34.3
safetensors==0.6.1
accelerate==1.10.0
sentencepiece==0.2.1        # 0.2.0 has no py3.13 wheel -> Windows build fails
protobuf>=5.27,<6           # needed for DeBERTa-v2 tokenizer conversion

# Scraping (01)
google-play-scraper==1.2.7  # pin exactly (breaks easily when Google endpoints change)

# GPT classification (02)
openai==1.99.6
regex==2025.7.34

# Statistics & analysis (03 OLS, revised_results)
numpy>=2.1,<3
pandas>=2.2,<3
scipy>=1.14,<2
scikit-learn>=1.5,<2
statsmodels>=0.14.2,<0.15
matplotlib>=3.9,<4
seaborn>=0.13,<0.14

# Notebook runtime
jupyterlab>=4.2,<5
ipykernel>=6.29,<7
ipywidgets>=8.1,<9
tqdm>=4.66,<5

# I/O helpers
openpyxl>=3.1,<4
```
