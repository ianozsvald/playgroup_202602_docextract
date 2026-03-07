# Doubleword Batch API models — model names use HuggingFace conventions
# Verify model availability at https://app.doubleword.ai/ before running
# Pricing shown is approximate Doubleword batch pricing (significantly cheaper than real-time)

DOUBLEWORD_MODELS = {

    # ── Multimodal (Vision + Language) ──────────────────────────
    "dw-qwen3-vl-30b": {
        "model":      "Qwen/Qwen3-VL-30B-A3B-Instruct-FP8",
        "multimodal": True,
        "modalities": ["text", "image", "video"],
        "tier":       "great_value",
        "price_in":   0.03, "price_out": 0.10,
        "ctx":        131_000,
        "notes":      "30B VL MoE, strong doc/OCR, Doubleword reference model",
    },
    "dw-qwen-2.5-vl-72b": {
        "model":      "Qwen/Qwen2.5-VL-72B-Instruct",
        "multimodal": True,
        "modalities": ["text", "image", "video"],
        "tier":       "great_value",
        "price_in":   0.16, "price_out": 0.16,
        "ctx":        33_000,
        "notes":      "72B VL flagship, best open doc AI, 32-lang OCR",
    },

    # ── Text-only ───────────────────────────────────────────────
    "dw-qwen3-235b": {
        "model":      "Qwen/Qwen3-235B-A22B-FP8",
        "multimodal": False,
        "modalities": ["text"],
        "tier":       "great_value",
        "price_in":   0.03, "price_out": 0.08,
        "ctx":        41_000,
        "notes":      "235B MoE (22B active), frontier open-source reasoning",
    },
    "dw-llama-3.3-70b": {
        "model":      "meta-llama/Llama-3.3-70B-Instruct",
        "multimodal": False,
        "modalities": ["text"],
        "tier":       "great_value",
        "price_in":   0.08, "price_out": 0.18,
        "ctx":        131_000,
        "notes":      "Strong multilingual 70B, 8 languages",
    },
    "dw-mistral-small": {
        "model":      "mistralai/Mistral-Small-3.1-24B-Instruct-2503",
        "multimodal": False,
        "modalities": ["text"],
        "tier":       "ultra_cheap",
        "price_in":   0.02, "price_out": 0.06,
        "ctx":        33_000,
        "notes":      "24B, fast and efficient, Apache 2.0",
    },
}
