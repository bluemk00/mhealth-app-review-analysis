# Environment Setup

This guide describes a tested environment for running the mHealth app review analysis pipeline, including data collection, app classification, factor scoring, and statistical analysis.

The configuration below was tested on Windows 11 with an NVIDIA RTX 5090. Other recent NVIDIA GPUs may also work, but GPU-specific installation details can differ.

## Requirements

- Windows 11, 64-bit
- Python 3.13
- An NVIDIA GPU and a recent NVIDIA driver for GPU-accelerated factor scoring
- Internet access for package installation, Google Play data collection, model download, and API-based app classification

For RTX 50-series GPUs, use a PyTorch build with CUDA 12.8 or later. A separate CUDA Toolkit installation is not required when using the PyTorch CUDA wheel.

## 1. Check the Python and GPU setup

Verify that Python and the NVIDIA driver are available:

```bash
python --version
nvidia-smi
```

The tested configuration used Python 3.13 and an RTX 5090. If `nvidia-smi` is unavailable, install or update the NVIDIA driver before continuing.

## 2. Create a virtual environment

From the repository root:

```bash
python -m venv .venv
```

Activate the environment:

```bash
.venv\Scripts\activate
```

Then update the packaging tools:

```bash
python -m pip install --upgrade pip setuptools wheel
```

If the repository is stored in a cloud-synced directory and package installation produces file-lock or permission errors, create the virtual environment outside the synced directory instead.

## 3. Install PyTorch

For RTX 50-series GPUs, install the CUDA 12.8 build of PyTorch:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu128
```

Verify GPU access:

```bash
python -c "import torch; print('PyTorch:', torch.__version__); print('CUDA available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

For an RTX 5090, `torch.cuda.is_available()` should return `True`.

## 4. Install the remaining dependencies

Install the project dependencies from the repository root:

```bash
pip install -r requirements.txt
```

The main packages used by the pipeline include:

- `transformers` and `sentencepiece` for NLI-based factor scoring
- `google-play-scraper` for review collection
- `openai` for app classification
- `numpy`, `pandas`, `scipy`, `scikit-learn`, and `statsmodels` for analysis
- `matplotlib` and `seaborn` for visualization
- `jupyterlab` and `ipykernel` for notebook execution

Exact package versions used in the tested environment are recorded in `requirements.lock.txt`.

## 5. Optional: register a Jupyter kernel

If running the analysis in Jupyter:

```bash
python -m ipykernel install --user --name medapp --display-name "Python (medapp)"
```

Select `Python (medapp)` as the notebook kernel.

## 6. Verify the factor-scoring model

The factor-scoring stage uses:

`MoritzLaurer/deberta-v3-large-zeroshot-v2.0`

A simple GPU check is:

```bash
python -c "from transformers import pipeline; clf = pipeline('zero-shot-classification', model='MoritzLaurer/deberta-v3-large-zeroshot-v2.0', device=0); print(clf('This app is very helpful', ['positive overall sentiment','negative overall sentiment'], multi_label=True))"
```

The first run downloads the model weights. If no compatible GPU is available, set `device=-1` to run on CPU.

## 7. Reproducibility

Some stages depend on external or time-varying sources and should not be expected to reproduce bit-for-bit when re-run:

- Google Play review collection can change over time as reviews and app metadata are updated.
- GPT-based app classification depends on an external API and may vary across model versions or service updates.
- GPU-based NLI inference can show small floating-point differences across hardware and software configurations.

For reproduction of the reported statistical analyses, use the fixed analysis inputs generated for the study rather than re-collecting or re-classifying the source data. With fixed inputs, the regression and plotting stages are deterministic apart from negligible platform-level numerical differences.

## 8. Troubleshooting

| Problem | Suggested action |
|---|---|
| `nvidia-smi` is not recognized | Install or update the NVIDIA driver. |
| `CUDA error: no kernel image is available` | Reinstall PyTorch using a CUDA build compatible with the GPU; RTX 50-series GPUs require CUDA 12.8 or later. |
| `sentencepiece` fails to build on Windows | Use `sentencepiece>=0.2.1`. |
| Package installation fails with file-lock or permission errors | If the environment is inside a cloud-synced directory, recreate it outside that directory. |
| CUDA is unavailable in PyTorch | Confirm the NVIDIA driver, PyTorch CUDA build, and GPU compatibility. |

## Tested environment

The current setup was tested with:

- Windows 11
- Python 3.13
- NVIDIA RTX 5090
- PyTorch 2.11.0 with CUDA 12.8
- Transformers 4.55.0
- OpenAI Python library 1.99.6
- google-play-scraper 1.2.7

See `requirements.txt` for the project dependencies and `requirements.lock.txt` for the exact tested package versions.
