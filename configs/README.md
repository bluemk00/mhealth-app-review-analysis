# Configs for Medical App Collection

이 디렉토리는 **의료/헬스 앱 수집기(MedicalAppCollector)** 에서 사용하는
키워드/용어 리스트를 관리합니다.  
코드(`medical_app_collector.py`)는 이 파일들을 자동으로 불러오기 때문에,
내용만 수정해도 즉시 반영됩니다.

---

## 파일 설명

- **`keywords_medical.txt`**  
  의료/헬스 관련 앱을 **검색할 때 사용하는 키워드 목록**  
  - 줄 단위로 구분  
  - 예:  
    ```
    medical education
    patient education
    health education
    ```

- **`terms_medical.txt`**  
  앱 제목/설명에서 **의료 관련 앱임을 확인하는 필터 단어**  
  - 줄 단위로 구분  
  - 예:  
    ```
    medical
    hospital
    doctor
    ```

- **`terms_pet.txt`**  
  **제외할 단어(애완동물 관련 앱 필터링)**  
  - 줄 단위로 구분  
  - 예:  
    ```
    pet
    dog
    cat
    veterinary
    ```

---

## 사용 규칙

1. **한 줄 = 하나의 키워드/용어**  
   공백 포함 가능 (`medical education`, `pet care`).

2. **중복 금지**  
   같은 단어가 여러 번 있으면 불필요하게 매칭됩니다.

3. **대소문자 무시**  
   정규식에서 case-insensitive로 처리하므로, 전부 소문자로 적는 것을 권장합니다.

4. **저장 후 바로 반영**  
   Collector 실행 시 해당 파일들을 다시 읽어오기 때문에 코드 수정 불필요합니다.

---

## 팁

- 특정 연구 목적(예: "정신건강 앱만")이 있다면, 새로운 txt 파일을 만들어서 Collector에서 경로만 바꿔주면 됩니다.  
- 실험 버전을 관리하려면 `configs/v1/`, `configs/v2/` 식으로 폴더를 나누는 것도 방법입니다.
