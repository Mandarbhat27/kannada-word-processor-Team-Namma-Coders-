# -*- coding: utf-8 -*-

# suffix → vibhakti_id rules (longest match first)
suffix_vibhakti = [
    ("ರನ್ನು", 2),
    ("ಯನ್ನು", 2),
    ("ಅನ್ನು", 2),
    ("ಇನ್ನು", 2),

    ("ಕ್ಕೆ", 4),
    ("ಗೆ", 4),

    ("ಯಿಂದ", 3),
    ("ಇಂದ", 3),

    ("ದಲ್ಲಿ", 7),
    ("ನಲ್ಲಿ", 7),
]

def reverse_transform(word, suffix):
    base = word[:-len(suffix)]

    # Remove inserted letters
    if suffix in ("ಅನ್ನು", "ಇನ್ನು") and base.endswith("ನ"):
        base = base[:-1]
    if suffix in ("ಯನ್ನು", "ಯಿಂದ") and base.endswith("ಯ"):
        base = base[:-1]
    if suffix == "ದಲ್ಲಿ" and base.endswith("ದ"):
        base = base[:-1]
    if suffix == "ಕ್ಕೆ" and base.endswith("ಕ್ಕ"):
        base = base[:-1]

    return base


def analyze_word(word):
    for suffix, vibhakti_id in suffix_vibhakti:
        if word.endswith(suffix):
            base = reverse_transform(word, suffix)
            return {
                "word": word,
                "vibhakti_id": vibhakti_id,
                "base": base,
                "suffix": suffix
            }
    
    # Default → direct
    return {
        "word": word,
        "vibhakti_id": 0,
        "base": word,
        "suffix": None
    }


# Example test
if __name__ == "__main__":
    test_words = ["ದೇವರನ್ನು", "ರವಿಯಿಂದ", "ಮನೆಯಲ್ಲಿ", "ಮನೆಗೆ", "ಪುಸ್ತಕದಲ್ಲಿ", "ರಾಮ", "ಶಕ್ತಿಯನ್ನು"]
    for w in test_words:
        print(analyze_word(w))
