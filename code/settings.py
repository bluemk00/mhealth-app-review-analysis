"""Configuration for the pipeline scripts.

Edit the values here instead of touching the script logic.
  - 01_collect_android.py                  -> "Collection" section
  - 03_sentiment_scoring_and_regression.py -> "Sentiment scoring & regression" section
"""

# ============================================================
# Collection (01_collect_android.py)
# ============================================================
# Google Play locale
COUNTRY = "us"
LANGUAGE = "en"

# Collection scope
TARGET_APP_COUNT = 10000      # number of apps to collect
REVIEWS_PER_APP = 100         # reviews to fetch per app
REVIEW_SLEEP_SEC = 0.3        # delay between apps (rate limiting)


# ============================================================
# Sentiment scoring & regression (03_sentiment_scoring_and_regression.py)
# ============================================================
# Zero-shot classifier
ZS_MODEL_ID = "MoritzLaurer/deberta-v3-large-zeroshot-v2.0"
HYPOTHESIS_TEMPLATE = "This review is about {}."

# Processed-data date to analyze.
# Reads  ../data/processed_<RUN_STAMP>/cleaned_reviews_of_category{1,2}.csv
# Writes ../outputs/anal_res_<RUN_STAMP>/...
RUN_STAMP = 20250904          # main dataset (alt: 20260518, ...)

# Zero-shot labelsets. The active list is scored; uncomment a block to swap
# the dimension set. Each block: candidate_labels (paired pos/neg phrases),
# paired_labels (pos, neg) tuples, new_cols (factor names, 'sentiment' first).
CANDIDATES = [
    # {
    #     # Paper Set 1 (suffix 1) — MARS Original (5 dimensions)
    #     "suffix": "1",
    #     "name": "MARS_Original",
    #     "candidate_labels": [
    #         "positive overall sentiment", "negative overall sentiment",
    #         "enjoyable and engaging to use", "boring and unengaging to use",
    #         "fast and reliable with easy navigation", "slow or unreliable with difficult navigation",
    #         "visually attractive and well-designed", "visually unattractive or poorly designed",
    #         "accurate and credible health information", "inaccurate or unreliable health information",
    #     ],
    #     "paired_labels": [
    #         ("positive overall sentiment", "negative overall sentiment"),
    #         ("enjoyable and engaging to use", "boring and unengaging to use"),
    #         ("fast and reliable with easy navigation", "slow or unreliable with difficult navigation"),
    #         ("visually attractive and well-designed", "visually unattractive or poorly designed"),
    #         ("accurate and credible health information", "inaccurate or unreliable health information"),
    #     ],
    #     "new_cols": [
    #         "sentiment",
    #         "engagement",
    #         "functionality",
    #         "aesthetics",
    #         "information_quality",
    #     ],
    # },
    {
        # Paper Set 2 (suffix 2) — Hybrid Core: literature-convergent (current optimal)
        "suffix": "2",
        "name": "Hybrid_Core",
        "candidate_labels": [
            "positive overall sentiment", "negative overall sentiment",
            "fair pricing and few ads", "expensive or too many ads",
            "effective and trustworthy health education", "unhelpful health education",
            "smooth performance without bugs", "frequent crashes or errors",
            "easy to use interface", "hard to use or poorly designed interface",
            "motivates healthy behavior change", "boring or lacks engagement",
            "transparent and ethical data use", "privacy concerns or unclear data policy",
        ],
        "paired_labels": [
            ("positive overall sentiment", "negative overall sentiment"),
            ("fair pricing and few ads", "expensive or too many ads"),
            ("effective and trustworthy health education", "unhelpful health education"),
            ("smooth performance without bugs", "frequent crashes or errors"),
            ("easy to use interface", "hard to use or poorly designed interface"),
            ("motivates healthy behavior change", "boring or lacks engagement"),
            ("transparent and ethical data use", "privacy concerns or unclear data policy"),
        ],
        "new_cols": [
            "sentiment",
            "pricing_and_ads",
            "health_education_quality",
            "technical_stability",
            "usability",
            "engagement_and_motivation",
            "privacy_and_ethical_data_use",
        ],
    },
    # {
    #     # Paper Set 3 (suffix 3) — Comprehensive Extension
    #     "suffix": "3",
    #     "name": "Comprehensive_Extension",
    #     "candidate_labels": [
    #         "positive overall sentiment", "negative overall sentiment",
    #         "fair pricing and few ads", "expensive or too many ads",
    #         "effective and trustworthy health education", "poor health education content",
    #         "smooth performance without bugs", "frequent crashes or errors",
    #         "easy to use interface", "hard to use or poorly designed interface",
    #         "motivates healthy behavior change", "boring or lacks engagement",
    #         "transparent and ethical data use", "privacy concerns or unclear data policy",
    #         "responsive and helpful customer support", "unresponsive or unhelpful customer support",
    #         "personalized to my needs", "not personalized to my needs",
    #     ],
    #     "paired_labels": [
    #         ("positive overall sentiment", "negative overall sentiment"),
    #         ("fair pricing and few ads", "expensive or too many ads"),
    #         ("effective and trustworthy health education", "poor health education content"),
    #         ("smooth performance without bugs", "frequent crashes or errors"),
    #         ("easy to use interface", "hard to use or poorly designed interface"),
    #         ("motivates healthy behavior change", "boring or lacks engagement"),
    #         ("transparent and ethical data use", "privacy concerns or unclear data policy"),
    #         ("responsive and helpful customer support", "unresponsive or unhelpful customer support"),
    #         ("personalized to my needs", "not personalized to my needs"),
    #     ],
    #     "new_cols": [
    #         "sentiment",
    #         "pricing_and_ads",
    #         "health_education_quality",
    #         "technical_stability",
    #         "usability",
    #         "engagement_and_motivation",
    #         "privacy_and_ethical_data_use",
    #         "customer_service",
    #         "personalization",
    #     ],
    # },
]
