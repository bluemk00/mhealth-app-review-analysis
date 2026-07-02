# Configs for Medical App Collection

This directory holds the keyword / term lists used by the **medical/health app collector
(`MedicalAppCollector`)**. The code (`medical_app_collector.py`) loads these files automatically,
so editing their contents takes effect immediately.

---

## Files

- **`keywords_medical.txt`**
  Keywords **used to search** for medical/health apps.
  - One per line
  - Example:
    ```
    medical education
    patient education
    health education
    ```

- **`terms_medical.txt`**
  Filter words that **confirm an app is medical-related** from its title/description.
  - One per line
  - Example:
    ```
    medical
    hospital
    doctor
    ```

- **`terms_pet.txt`**
  Words to **exclude (filter out pet-related apps)**.
  - One per line
  - Example:
    ```
    pet
    dog
    cat
    veterinary
    ```

---

## Rules

1. **One keyword/term per line** — spaces allowed (`medical education`, `pet care`).
2. **No duplicates** — repeated words cause unnecessary matches.
3. **Case-insensitive** — matched case-insensitively in regex, so lowercase is recommended.
4. **Takes effect on save** — the collector re-reads these files on run, so no code change is needed.

---

## Tips

- For a specific research focus (e.g., "mental health apps only"), create a new txt file and just point
  the collector to its path.
- To manage experimental versions, splitting into folders like `configs/v1/`, `configs/v2/` also works.
