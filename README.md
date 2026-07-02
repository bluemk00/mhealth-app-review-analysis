# 의료·헬스 앱 리뷰 분석 파이프라인

Google Play(및 iOS) **의료/헬스/교육 앱**의 메타데이터·리뷰를 수집하고,
전처리 → 감성·토픽 분류 → 회귀분석까지 수행하는 재현 가능한 파이프라인입니다.

> ⚠️ **이 폴더는 정리된 코드 사본입니다.** 원본 작업본(재현 기준)은
> [`../mHealthApps_reprod`](../mHealthApps_reprod)에 그대로 보존되어 있습니다.
> 정리본이 동일 결과를 재현하는지 확인되기 전까지 원본을 정본으로 삼으세요.

---

## 📂 구조

```
GitHub/
├─ code/
│  ├─ settings.py                              # 01·03 설정 (수집량·모델·RUN_STAMP·라벨셋)
│  ├─ 01_collect_android.py                    # 앱·리뷰 수집 (스크립트)
│  ├─ 02_preprocess.ipynb                      # 리뷰 정제 + 대상사용자 자동분류
│  ├─ 03_sentiment_scoring_and_regression.py   # 제로샷 감성 스코어링 + OLS 회귀
│  └─ 04_analysis_20250904.ipynb               # 메인 분석/결과 (20250904)
├─ lib/                                        # 재사용 패키지
│  ├─ collectors/   medical_app_collector.py
│  ├─ scrapers/     base.py · google_play.py · ios_app_store.py
│  └─ utils/        text_preprocessing.py
├─ configs/                                    # 키워드·필터 용어 + 키 템플릿
│  ├─ keywords_medical.txt · terms_medical.txt · terms_pet.txt
│  └─ config_local.json (빈 템플릿) · README.md
├─ docs/setup_guide.md                         # 환경 구축 가이드
├─ requirements.txt · requirements.lock.txt
├─ .gitignore
└─ README.md
```

`data/`(검증 라벨 제외)·`outputs/`는 대용량이라 저장소에서 **제외(.gitignore)** 합니다. 아래 "데이터 배치" 참고.

---

## 🔁 실행 순서

| 단계 | 파일 | 입력 → 출력 |
|------|------|-------------|
| 1 | `01_collect_android.py` | 앱스토어 → `data/raw/..._<stamp>_android(.reviews).json` |
| 2 | `02_preprocess.ipynb` | raw JSON → 대상사용자 자동분류 + 리뷰 정제·카테고리 분리 (**아래 상세**) |
| 3 | `03_sentiment_scoring_and_regression.py` | `data/processed_<stamp>/cleaned_reviews_of_categoryN.csv` → `outputs/anal_res_<stamp>/categoryN/` |
| 4 | `04_analysis_20250904.ipynb` | 결과 집계·표/그림 |

### 2단계 상세 — 대상사용자(consumer/provider) 분류
저자가 손으로 하던 분류를 자동화한 **GPT 자동초안 → 사람 검증** 2단계입니다.

1. **자동 초안** — `02`가 각 앱의 description을 GPT로 분류하여
   `data/processed_<stamp>/app_information_with_description.csv` 생성
   (컬럼: 앱정보 + `Description` + `machine_key` + `Target_Users` + `gpt_reason`).
2. **사람 검증** — 저자가 전 항목을 검토하고, 교신저자 2인이 무작위 표본을 검토·합의하여
   최종 라벨 `data/processed_<stamp>/app_target_users_validated.csv`(`AppId·Title·Target_Users`) 확정.
   *(GitHub에 커밋되는 유일한 검증 산출물이자, 02가 실제로 읽는 파일)*
3. **리뷰 분리** — `02` 후반부가 검증본 `app_target_users_validated.csv`의 `Target_Users`로 리뷰를 category1/2로 나눠
   `cleaned_reviews_of_categoryN.csv` 등을 저장 (→ 3단계 입력).

> ⚠️ **논문 수치는 검증본 `app_target_users_validated.csv` 기준으로 재현됩니다.** GPT 자동초안은 재현·투명성을 위해 제공되며,
> 검증본과 배정이 조금 다를 수 있습니다(GPT 비결정성 + 사람 검증 반영). 독자는 검증본 없이도 1)까지 자동 재현 가능.

### run-stamp 규칙
- `03`은 `settings.py`의 **`RUN_STAMP`**(예: `20250904`)로 경로를 조립합니다.
  - 입력: `../data/processed_<stamp>/cleaned_reviews_of_categoryN.csv`
  - 출력: `../outputs/anal_res_<stamp>/categoryN/`
- **메인 데이터셋 = `20250904`** (기본값). 다른 날짜(20260518 등)는 실험용.
- `01`·`03`의 설정(수집량·모델·라벨셋 등)은 모두 `code/settings.py`에서 조정합니다.

### 데이터 배치
`code/`에서 실행하므로 데이터·출력은 **저장소 루트**에 다음처럼 둡니다(또는 원본에서 복사/링크):
```
GitHub/
├─ data/raw/                          # 익명화 JSON (content+score+at, PII 없음 / gitignore)
├─ data/processed_20250904/           # 전처리 산출물(gitignore) + app_target_users_validated.csv (← 커밋)
└─ outputs/anal_res_20250904/         # 분석 결과 (gitignore)
```
원본 위치: `../mHealthApps_reprod/data/raw`, `../mHealthApps_reprod/data_20250904`, `../mHealthApps_reprod/outputs`

### 🔒 개인정보 · 익명화
수집·저장 단계에서 **리뷰어 개인정보를 저장하지 않습니다.** 수집기(`lib/collectors`, `01`)는
디스크에 쓰기 전에 각 레코드를 분석에 필요한 필드로만 축소합니다(`slim_app_record`):
- **리뷰:** `content`, `score`, `at`  — `userName`·`userImage`·`reviewId`·답글 등 식별자는 저장 안 함
- **앱:** `appId`, `title`, `score`, `genre`, `free`, `installs`, `description`

따라서 `data/raw/*_android.json`은 재현에 필요한 정보만 담긴 **익명화 데이터**이며, 저장소에 함께 커밋합니다.
같은 날짜(20250904) 스냅샷은 재수집이 불가능하므로, 이 익명화본을 재현용으로 공개합니다
(파이프라인이 최종적으로 쓰는 값은 리뷰 `content`+`score`뿐).

### 데이터 출처 · 이용 조건
- **출처:** Google Play (US, 2025-09-04 스냅샷), `google-play-scraper`로 수집.
- **목적:** 본 데이터는 **비영리 학술 재현 목적**으로만 제공됩니다. 리뷰 텍스트의 저작권은 각 작성자에게,
  앱 설명은 각 개발사에 있습니다.
- **개인정보:** 리뷰어 식별정보(이름·프로필·리뷰ID 등)는 포함하지 않습니다(익명화).
- 재배포·상업적 이용 시 Google Play 약관 및 원저작자 권리를 준수하세요.

---

## 🔑 API 키 설정 (02_preprocess의 GPT 분류용)

키는 **저장소에 포함하지 않습니다.** 실제 키 파일은 **저장소 상위 폴더**에 둡니다.

1. `configs/config_local.json`(빈 템플릿)을 복사해 **저장소 바로 위 폴더**에 `config_local.json`으로 저장:
   ```
   2026mHealthApp논문작업/
   ├─ config_local.json   ← 여기 (실제 키, .gitignore·저장소 밖)
   └─ GitHub/             ← 저장소 루트
      └─ code/
   ```
2. 파일에 키 입력:
   ```json
   { "openai_api_key": "sk-...", "gpt_model": "gpt-5-2025-08-07" }
   ```
3. `02_preprocess.ipynb`는 `code/`에서 실행되며 `../../config_local.json`(=상위 폴더)에서 키를 읽습니다.

> 이전 버전은 노트북에 키가 하드코딩돼 있었으나 제거했습니다. `configs/config_local.json`은 **키가 빈** 템플릿입니다.

---

## 🗂 원본 → 정리본 매핑

| 원본(`mHealthApps_reprod/code`) | 정리본(`GitHub/code`) |
|---|---|
| `01_collect_android_final.ipynb` | `01_collect_android.py` (노트북 → 스크립트 변환) |
| `02_preprocess.ipynb` | `02_preprocess.ipynb` |
| `03_sentiment_scoring_and_regression_4.py` (최신) | `03_sentiment_scoring_and_regression.py` |
| `revised_results_20250904_relabel.ipynb` | `04_analysis_20250904.ipynb` |

> 제외된 것: 옛 스크립트 `_3.py`, 분석 변형본(`revised_results_20250904.ipynb`, `_2 copy`, `20260518*`), 스크래치(`Untitled*`), `.ipynb_checkpoints` — 필요 시 원본에서 확인하세요.

---

## ⚙️ 환경

| 파일 | 용도 |
|------|------|
| `requirements.txt` | 설치용 의존성 목록 (torch 제외 — 아래 순서 주의) |
| `requirements.lock.txt` | 검증된 설치의 전체 버전 박제 (재현성 기준) |
| [`docs/setup_guide.md`](docs/setup_guide.md) | RTX 5090 환경 구축 상세 가이드 (Python·venv·CUDA·검증) |

**설치 (요약)** — 대상: Python 3.13 / Windows x64 / (GPU 사용 시) CUDA 12.8+
```bash
# 1) torch를 먼저 CUDA 12.8 인덱스로 설치 (그냥 pip install torch 금지 — CPU판 잡힘)
pip install torch --index-url https://download.pytorch.org/whl/cu128
# 2) 나머지
pip install -r requirements.txt
```
> ⚠️ 가상환경은 **Dropbox/OneDrive 밖**(예: `C:\Users\<id>\venvs\medapp`)에 만드세요. 자세한 이유·검증 절차는 [`docs/setup_guide.md`](docs/setup_guide.md) 참고.
