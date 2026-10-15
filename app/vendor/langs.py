# Tesseract language packs bundled in the Docker image (see .actor/Dockerfile)
BUNDLED = {"eng": "English", "deu": "German", "fra": "French", "spa": "Spanish", "ita": "Italian",
           "por": "Portuguese", "chi_sim": "Chinese (Simplified)", "jpn": "Japanese"}


def validate(spec):
    """'eng+deu' -> 'eng+deu'; raises ValueError for unknown codes."""
    codes = [c.strip() for c in (spec or "eng").replace(",", "+").split("+") if c.strip()]
    bad = [c for c in codes if c not in BUNDLED]
    if bad:
        raise ValueError(f"Unsupported OCR language(s): {', '.join(bad)}. Available: {', '.join(BUNDLED)}")
    return "+".join(dict.fromkeys(codes)) or "eng"
