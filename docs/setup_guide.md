# RTX 5090 환경 구축 가이드 — mHealthApps 리뷰 분석 파이프라인

> 작성일: 2026-06-05 · 대상 PC: Windows 11 + RTX 5090 · 목적: 두 개로 나뉘어 있던 가상환경(`torch-cu121`, `bert-topic-2`)을 **하나의 안정적인 환경**으로 통합하여 수집·전처리·감성분석·회귀 전 과정을 동일 결과로 재현

---

## 0. 최종 구성 요약 (빠른 참조)

| 항목 | 값 |
|---|---|
| OS | Windows 11 Pro (build 26200), x64 (AMD64) |
| GPU | RTX 5090 (Blackwell, **sm_120**), 드라이버 610.47 (CUDA 13.3까지 지원) |
| Python | 3.13.12 (python.org 정식 설치본) |
| 가상환경 위치 | `C:\Users\Master\venvs\medapp` (**Dropbox·OneDrive 밖**) |
| 프로젝트 폴더 | `D:\Dropbox\2026문서작업\mHealthApps_reprod_2` (코드·데이터) |
| PyTorch | `torch 2.11.0+cu128` (CUDA 런타임 내장) |
| Jupyter 커널 | `Python (medapp)` |
| 재현성 기준 파일 | `requirements.lock.txt` (전체 버전 박제) |

---

## 1. 핵심 주의사항 (실행 전에 먼저 읽기)

1. **명령은 한 줄씩 실행한다.** 여러 줄을 한꺼번에 붙여넣으면 줄이 붙어 엉뚱하게 실행될 수 있다(예: `pip freeze`가 다음 줄의 `-c`를 옵션으로 잘못 받아 실패). 한 줄 입력 → Enter → 다음 줄.
2. **가상환경은 Dropbox/OneDrive 안에 만들지 않는다.** 동기화가 수천 개 파일을 실시간으로 잠그면서 pip 설치가 깨지거나 환경이 손상된다. venv는 `C:\Users\Master\venvs\...`, 코드·데이터만 Dropbox에 둔다.
3. **PyTorch는 반드시 cu128 인덱스로 설치한다.** RTX 5090(sm_120)은 CUDA 12.8+ 빌드에서만 동작. 그냥 `pip install torch`를 쓰면 `CUDA error: no kernel image is available` 오류가 난다.
4. **CUDA Toolkit을 따로 설치할 필요는 없다.** cu128 휠에 CUDA 런타임이 내장되어 있고, 시스템엔 NVIDIA 드라이버만 있으면 된다(이미 설치됨).
5. **sentencepiece는 0.2.1 이상을 쓴다.** 0.2.0은 Python 3.13용 휠이 없어 Windows에서 소스 빌드를 시도하다 실패한다(토큰화 결과는 버전과 무관하게 동일).
6. **가상환경을 켜도 현재 폴더는 바뀌지 않는다.** 항상 프로젝트 루트에서 작업해야 `pip install -r requirements.txt`와 `from lib...` import가 정상 동작한다.
7. **"결과 동일성"은 재실행이 아니라 캐시로 지킨다.** 아래 6번 항목(재현성) 참조.

---

## 2. 사양 확인 (Phase A)

> 명령 프롬프트(cmd) 또는 PowerShell에서 실행.

```
nvidia-smi
```
→ 확인: **GPU 모델(RTX 5090)**, 드라이버 버전, 우측 상단 **CUDA 버전(최대 지원치)**. CUDA 13.3 ≥ 12.8 이므로 5090 요건 충족. `nvidia-smi`가 "인식되지 않는 명령어"면 드라이버 미설치 신호.

```
echo %PROCESSOR_ARCHITECTURE%
```
→ 확인: **`AMD64`** (64비트). PyTorch는 64비트 휠만 제공하므로 이 값이면 충족.

```
systeminfo | findstr /B /C:"OS 이름" /C:"OS 버전" /C:"시스템 종류"
```
→ 확인: **Windows 11**, 64비트. ⚠️ 한글판 Windows라 항목명이 한글이다. 영어("OS Name")로 거르면 아무것도 안 나오니 위처럼 한글 항목명을 써야 한다.

```
where python
where conda
```
→ 확인: 기존 Python/conda 잔재 여부. `...\WindowsApps\python.exe`만 나오면 **실제 Python이 아니라 Microsoft Store 더미 스텁**이므로 사실상 백지 상태. `conda`가 "찾지 못했습니다"면 conda 없음.

---

## 3. Python 설치 (Phase B)

**버전 선택 근거**: Python 3.12는 바이너리 설치본이 3.12.10에서 끊겼고(이후 보안 수정만), 3.14는 일부 연구 패키지 호환이 늦다. 그 사이에서 **유지보수가 살아 있고 생태계 호환이 넓은 3.13**이 최적.

1. 다운로드: `https://www.python.org/ftp/python/3.13.12/python-3.13.12-amd64.exe`
2. 설치 시 첫 화면 하단 **"Add python.exe to PATH" 체크박스를 반드시 켠다.**
3. 설치 끝 화면에서 **"Disable path length limit"** 클릭(260자 경로 제한 해제 — 깊은 의존성 트리에서 `path too long` 예방).

검증:

```
python --version
```
→ 확인: `Python 3.13.12`

```
pip --version
```
→ 확인: 경로가 `...\Programs\Python\Python313\...` 를 가리킬 것. (Store 더미가 아니라 정식 설치본을 PATH가 가리킨다는 뜻)

---

## 4. 통합 가상환경 구축 (Phase C — 5단계)

> 시작 위치: 명령 프롬프트를 **프로젝트 루트**(`D:\Dropbox\...\mHealthApps_reprod_2`, `lib`와 `requirements.txt`가 있는 곳)에서 연다.
> 탐색기에서 그 폴더를 열고 주소 표시줄에 `cmd` 입력 → Enter 하면 그 위치에서 cmd가 열린다.

### 1단계 — 가상환경 생성·활성화 (Dropbox 밖)

```
python -m venv C:\Users\Master\venvs\medapp
```
→ 확인: 오류 없이 종료. (venv는 C: 경로에 생기고, 현재 위치는 D: 프로젝트 폴더 그대로)

```
C:\Users\Master\venvs\medapp\Scripts\activate
```
→ 확인: 프롬프트 맨 앞에 **`(medapp)`** 이 붙는다. 예: `(medapp) D:\Dropbox\...\mHealthApps_reprod_2>`

### 2단계 — pip 정비 + PyTorch(cu128) 설치

```
python -m pip install --upgrade pip setuptools wheel
```
→ 확인: `Successfully installed ...` (이후 torch가 setuptools를 70.x로 되돌려도 정상)

```
pip install torch --index-url https://download.pytorch.org/whl/cu128
```
→ 확인: `torch-2.11.0+cu128 ... cp313` 휠을 받는다(약 2.8GB, 수 분 소요). `Successfully installed ... torch-2.11.0+cu128`

```
python -c "import torch; print('torch:', torch.__version__); print('CUDA:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0)); print('cap:', torch.cuda.get_device_capability(0))"
```
→ 확인: 다음이 함께 떠야 한다.
- `CUDA: True`
- `GPU: NVIDIA GeForce RTX 5090`
- `cap: (12, 0)` ← Blackwell sm_120 정상 인식
- ⚠️ 이 단계에서 뜨는 `Failed to initialize NumPy` 경고는 **정상**(아직 numpy 미설치). 3단계 후 사라진다.

### 3단계 — 나머지 패키지 일괄 설치

> `requirements.txt`가 현재 폴더(프로젝트 루트)에 있어야 한다.

```
pip install -r requirements.txt
```
→ 확인:
- 마지막 줄 `Successfully installed ...`, 빨간 에러 없음.
- **`sentencepiece-0.2.1`** 이 빌드 없이 휠로 설치됨.
- 핵심 핀 버전 확인: `transformers-4.55.0`, `tokenizers-0.21.4`, `accelerate-1.10.0`, `openai-1.99.6`, `google-play-scraper-1.2.7`.

### 4단계 — Jupyter 커널 등록 + 버전 동결

```
python -m ipykernel install --user --name medapp --display-name "Python (medapp)"
```
→ 확인: `Installed kernelspec medapp in ...`

```
pip freeze > requirements.lock.txt
```
→ 확인: 프로젝트 폴더에 `requirements.lock.txt` 생성(탐색기에서 확장자 숨김이면 `requirements.lock`으로 보임). 이 파일이 재현성 기준점.

```
python -c "import torch, numpy, pandas, scipy, sklearn, statsmodels, matplotlib, seaborn, transformers, sentencepiece, openai, google_play_scraper; print('imports OK')"
```
→ 확인: **`imports OK`** (12개 핵심 라이브러리 정상 import, numpy 경고 사라짐).

### 5단계 — (선택) 감성 모델 끝단 검증

> DeBERTa-large 모델 약 1.7GB를 처음 한 번 내려받는다(03 실행 시 어차피 필요).

```
python -c "from transformers import pipeline; clf = pipeline('zero-shot-classification', model='MoritzLaurer/deberta-v3-large-zeroshot-v2.0', device=0); print(clf('This app is very helpful', ['positive overall sentiment','negative overall sentiment'], multi_label=True))"
```
→ 확인:
- `Device set to use cuda:0` (GPU에서 추론)
- 점수 출력 예: positive ≈ 0.95, negative ≈ 0.0003 (합리적 결과)
- ⚠️ `hf_xet` 경고는 무시 가능(다운로드 속도만 영향).

---

## 5. 환경에서 제외/포함한 것 (설계 근거)

**포함**: 감성(transformers·sentencepiece·torch-cu128), 수집(google-play-scraper), 전처리(openai·regex), 통계/도표(numpy·pandas·scipy·scikit-learn·statsmodels·matplotlib·seaborn), 노트북(jupyterlab·ipykernel).

**의도적으로 제외**:
- `bertopic / sentence-transformers / umap-learn / hdbscan / numba / llvmlite` — 업로드된 코드가 import하지 않음. numba 계열은 Python 3.13 + numpy 2.x에서 가장 충돌이 잦은 부분이라, 빼는 것이 안정성에 직결. 토픽 모델링을 다시 쓰게 되면 **별도 전용 환경**을 권장.
- `bitsandbytes` — Windows 설치가 잦게 깨지고, zero-shot 추론에 불필요.
- `nltk / emoji / langid / wordcloud / plotly` — 현재 코드 미사용.

---

## 6. 사용법 & 재현성 원칙

**일상 사용**
1. 가상환경 활성화: `C:\Users\Master\venvs\medapp\Scripts\activate`
2. 노트북 실행 시 커널을 **`Python (medapp)`** 로 선택.
3. **프로젝트 루트에서 실행**해야 `from lib...` import가 동작.

**결과 동일성 (가장 중요)**

파이프라인 중 재실행으로는 동일 결과가 원천 불가능한 단계:
- **01 수집**: Google Play 라이브 데이터 → 다시 긁으면 리뷰·평점이 달라짐.
- **02 GPT 분류**: API 호출(`gpt-5-2025-08-07`) → 호출 시점·모델 변경에 따라 출력 변동.
- **03 감성 추론**: 옛 GPU(CUDA 12.1) → RTX 5090(CUDA 12.8+)으로 하드웨어가 바뀌면 부동소수점 누적 순서가 달라져 점수가 하위 자리에서 미세하게 달라짐(비트 단위 일치 불가능).

반대로 **최종 분석은 결정적으로 재현 가능**: 03이 저장한 `scores_with_factors.csv`에서 회귀·도표가 시작되며, statsmodels OLS·robust SE는 라이브러리 버전과 무관하게 보고 자릿수까지 동일.

> **원칙**: 기존 중간 산출물(원시 리뷰, `cleaned_reviews_*.csv`, GPT 라벨, `scores_with_factors.csv`)을 그대로 보관하고, 새 환경에서는 **그 CSV에서 최종 분석만 재실행**한다. 01·02·03은 새 데이터를 만들 때만 돌린다(이때 위 비결정성을 감수).

03을 GPU에서 부득이 재실행할 경우: 추론 전 `from transformers import set_seed; set_seed(42)`를 넣는다. 그래도 옛 점수와는 하위 자리에서 차이가 나므로, **정확한 재현이 목적이면 03을 재실행하지 말고 캐시된 CSV를 재사용**한다.

---

## 7. 함정 빠른 점검 (증상 → 원인/조치)

| 증상 | 원인 / 조치 |
|---|---|
| `systeminfo | findstr` 결과가 빈칸 | 한글판 Windows. 영어 항목명 대신 한글("OS 이름" 등) 사용 |
| `nvidia-smi` 인식 안 됨 | NVIDIA 드라이버 미설치/미인식 → 드라이버 먼저 설치 |
| `CUDA error: no kernel image is available` | 일반 torch 설치됨 → cu128 인덱스로 재설치 |
| `sentencepiece` 설치 중 빌드 실패 | 0.2.0 사용. → `sentencepiece==0.2.1`로 |
| pip 설치 중 권한/잠금 오류 | venv가 Dropbox/OneDrive 안 → 동기화 밖으로 이동 |
| `pip freeze`가 `no such option: -c` | 두 명령이 한 줄로 붙음 → 한 줄씩 실행 |
| 2단계에서 `Failed to initialize NumPy` | 정상(numpy 미설치). 3단계 후 사라짐 |

---

## 부록 — requirements.txt 내용

> torch는 여기 포함하지 않는다(2단계에서 cu128 인덱스로 먼저 설치). 통계 스택은 범위로 두되 설치 후 `requirements.lock.txt`로 정확한 버전을 박제한다.

```
# Sentiment (03): HuggingFace zero-shot DeBERTa-v3
transformers==4.55.0
tokenizers==0.21.4
huggingface-hub==0.34.3
safetensors==0.6.1
accelerate==1.10.0
sentencepiece==0.2.1        # 0.2.0은 py3.13 휠 없음 → Windows 빌드 실패
protobuf>=5.27,<6           # DeBERTa-v2 토크나이저 변환에 필요

# Scraping (01)
google-play-scraper==1.2.7  # 정확히 고정(구글 엔드포인트 변경 시 잘 깨짐)

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
