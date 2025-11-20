# fuzzy_utils.py
import difflib

def norm_str(s: str) -> str:
    """Normalize string for comparison."""
    return s.lower().strip()

def fuzzy_matches(word: str, candidates: list, cutoff: float = 0.6):
    """Return list of (candidate, score) with score >= cutoff."""
    word_n = norm_str(word)
    cand_norm = [norm_str(c) for c in candidates]
    matches = difflib.get_close_matches(word_n, cand_norm, n=10, cutoff=cutoff)

    results = []
    for m in matches:
        for c in candidates:
            if norm_str(c) == m:
                score = difflib.SequenceMatcher(None, word_n, m).ratio()
                results.append((c, score))
                break
    return sorted(results, key=lambda x: x[1], reverse=True)

def best_match(word: str, candidates: list, cutoff: float = 0.6):
    """Return best matching candidate or original word."""
    matches = fuzzy_matches(word, candidates, cutoff)
    if matches:
        return matches[0][0]
    return word
