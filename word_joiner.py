# code/word_joiner.py
# Heavy WordJoiner: sandhi, reverse-sandhi, vibhakti (single input), samasa (dictionary + fuzzy), transliteration.
# Works with optional CSVs in "../dictionaries/"

from typing import Optional, Tuple, List, Dict
import os, csv, difflib, re
from code.fuzzy_utils import fuzzy_matches, best_match, norm_str


# Kannada character sets
INDEPENDENT_VOWELS = set("ಅಆಇಈಉಊಋಎಏಐಒಓಔ")
DEPENDENT_VOWELS = set("ಾಿೀುೂೃೆೇೈೊೋೌ")
VIRAMA = "್"

def _data_path(filename: str) -> str:
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base, "dictionaries", filename)

def _is_kannada_char(ch: str) -> bool:
    return '\u0c80' <= ch <= '\u0cff'

def _is_kannada(s: str) -> bool:
    return any(_is_kannada_char(ch) for ch in (s or ""))

class WordJoiner:
    def __init__(self,
                 sandhi_csv: str = "dictionaries/sandhi_rules.csv",
                 vibhakti_csv: str = "dictionaries/vibhakti_rules.csv",
                 compound_csv: str = "dictionaries/compound_words.csv",
                 root_csv: str = "dictionaries/root_words.csv"):

        # CSV path resolution (safe)
        self.sandhi_csv = sandhi_csv if os.path.isabs(sandhi_csv) else _data_path(os.path.basename(sandhi_csv))
        self.vibhakti_csv = vibhakti_csv if os.path.isabs(vibhakti_csv) else _data_path(os.path.basename(vibhakti_csv))
        self.compound_csv = compound_csv if os.path.isabs(compound_csv) else _data_path(os.path.basename(compound_csv))
        self.root_csv = root_csv if os.path.isabs(root_csv) else _data_path(os.path.basename(root_csv))

        # load if present
        self.sandhi_rules_csv = self._load_csv_dict(self.sandhi_csv)
        self.vibhakti_rules_csv = self._load_csv_dict(self.vibhakti_csv)
        self.compound_rows = self._load_csv_dict(self.compound_csv)
        self.root_set = self._load_roots(self.root_csv)

        # sandhi & vibhakti tables (built-in minimal set; CSVs can override)
        self.sandhi_table = self._build_default_sandhi_table()
        if self.sandhi_rules_csv:
            self._merge_sandhi_csv(self.sandhi_rules_csv)

        self.vibhakti_table = self._build_default_vibhakti_table()
        if self.vibhakti_rules_csv:
            self._merge_vibhakti_csv(self.vibhakti_rules_csv)

        # compound dict for exact mapping
        self.compound_map = {}
        for r in self.compound_rows:
            key = (r.get("combined") or "").strip()
            if key:
                self.compound_map[key] = r
        self._compound_list = list(self.compound_map.keys())
        self._root_list = sorted(list(self.root_set))

        # typical vibhakti suffix groups for detection (longest-first usage)
        self.vibhakti_suffixes = {
            "2": ["ವನ್ನು","ಅನ್ನು","ನ್ನು"],
            "3": ["ಯಿಂದ","ಇಂದ","ರಿಂದ"],
            "4": ["ಕ್ಕೆ","ಗೆ"],
            "6": ["ನ","ಅದ","ಆದ"],
            "7": ["ನಲ್ಲಿ","ಅಲ್ಲಿ","ಲ್ಲಿ"]
        }

    # ---------- CSV helpers ----------
    def _load_csv_dict(self, path: str) -> List[Dict[str,str]]:
        rows=[]
        try:
            if os.path.exists(path):
                with open(path, newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for r in reader:
                        clean = {k.strip(): (v.strip() if v is not None else "") for k,v in r.items()}
                        rows.append(clean)
        except Exception:
            rows=[]
        return rows

    def _load_roots(self, path: str) -> set:
        s=set()
        try:
            if os.path.exists(path):
                with open(path, newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader, None)
                    for r in reader:
                        if r:
                            s.add(r[0].strip())
        except Exception:
            s=set()
        return s

    # --------- default sandhi table (representative rules) ----------
    def _build_default_sandhi_table(self) -> List[Dict[str,str]]:
        T=[]
        def add(rn,s1,s2,res,comb,ex1,ex2,notes,delf):
            T.append({
                "rule_number": str(rn),
                "sound1": s1, "sound2": s2,
                "result": res, "combined_result": comb,
                "example_word1": ex1, "example_word2": ex2,
                "notes": notes,
                "delete_first_of_w2": "yes" if delf else "no"
            })
        add(1,"ಾ","ಆ","","","ಮಹಾತ್ಮ","ಆತ್ಮ","ಾ + ಆ -> drop ಆ",True)
        add(4,"ಇ","ಅ","ಯ","","ಶಕ್ತಿ","ಅಭಿಮಾನ","ಇ + ಅ -> ಯ",True)
        add(7,"ಉ","ಅ","ವ","","ಗುರು","ಅನು","ಉ + ಅ -> ವ",True)
        add(18,"ಅ","ಋ","ರ್","","ಶರ","ಋಷಿ","ಅ + ಋ -> ರ್",False)
        add(34,"ರ","ಇ","ಯ","","ನರ","ಇಂದ್ರ","Special nar+indra",True)
        add(37,"ಾ","ಇ","ಯ","","ರಾ","ಇಲ","aa + i -> ಯ",True)
        return T

    def _merge_sandhi_csv(self, rows):
        for r in rows:
            rn=r.get("rule_number") or ""
            if rn:
                found=False
                for idx,tr in enumerate(self.sandhi_table):
                    if tr.get("rule_number")==rn:
                        merged={}; merged.update(tr); merged.update({k:str(v).strip() for k,v in r.items()})
                        self.sandhi_table[idx]=merged; found=True; break
                if not found:
                    self.sandhi_table.append({k:str(v).strip() for k,v in r.items()})
            else:
                self.sandhi_table.append({k:str(v).strip() for k,v in r.items()})

    # ---------- default vibhakti ----------
    def _build_default_vibhakti_table(self) -> List[Dict[str,str]]:
        return [
            {"vibhakti_id":"1","base":"ರಾಮ","ending":"ಗೆ","output":"ರಾಮನಿಗೆ"},
            {"vibhakti_id":"2","base":"ರಾಮ","ending":"ಅನ್ನು","output":"ರಾಮನನ್ನು"},
            {"vibhakti_id":"3","base":"ಶಕ್ತಿ","ending":"ಅನ್ನು","output":"ಶಕ್ತಿಯನ್ನು"},
            {"vibhakti_id":"4","base":"ದೇವ","ending":"ರನ್ನು","output":"ದೇವರನ್ನು"},
        ]

    def _merge_vibhakti_csv(self, rows):
        for r in rows:
            idv=r.get("vibhakti_id") or ""
            if idv:
                found=False
                for idx,tr in enumerate(self.vibhakti_table):
                    if tr.get("vibhakti_id")==idv:
                        merged={}; merged.update(tr); merged.update({k:str(v).strip() for k,v in r.items()})
                        self.vibhakti_table[idx]=merged; found=True; break
                if not found:
                    self.vibhakti_table.append({k:str(v).strip() for k,v in r.items()})
            else:
                self.vibhakti_table.append({k:str(v).strip() for k,v in r.items()})

    # ---------- small helpers ----------
    def _first_char(self, w: str) -> str:
        w=(w or "").strip(); return w[0] if w else ""

    def _last_char(self, w: str) -> str:
        w=(w or "").strip()
        if not w: return ""
        if w[-1]==VIRAMA and len(w)>1:
            return w[-2]
        return w[-1]

    def _norm(self, s: str) -> str:
        return norm_str(s)

    # ---------- sandhi apply ----------
    def find_sandhi_rule(self, last: str, first: str) -> Optional[Dict[str,str]]:
        for r in self.sandhi_table:
            if r.get("sound1")==last and r.get("sound2")==first:
                return r
        for r in self.sandhi_table:
            if r.get("sound2")==first:
                return r
        return None

        # ---------------- apply_sandhi (UPDATED) ----------------
    def apply_sandhi(self, w1: str, w2: str) -> str:
        """
        Improved sandhi with extra rules for vowel+vowel like ಇ/ಈ cases,
        and conservative fallbacks. Returns the combined word (Kannada).
        """
        w1 = self._norm(w1)
        w2 = self._norm(w2)
        if not w1 or not w2:
            return w1 + w2

        # transliterate roman-ish inputs if needed (keeps previous translit logic)
        if (re.search(r'[A-Za-z]', w1) or re.search(r'[A-Za-z]', w2)) and (not _is_kannada(w1) or not _is_kannada(w2)):
            w1t = self.transliterate(w1) if re.search(r'[A-Za-z]', w1) else w1
            w2t = self.transliterate(w2) if re.search(r'[A-Za-z]', w2) else w2
            if _is_kannada(w1t) and _is_kannada(w2t):
                w1, w2 = w1t, w2t

        last = self._last_char(w1)
        first = self._first_char(w2)

        # --- Special explicit rule: when w2 starts with independent vowels ಇ/ಈ,
        #     insert e-sound (ೆ) between rather than naive concat.
        # Example: ರಾಮ + ಈಶ್ವರ -> ರಾಮೇಶ್ವರ
        if first in ("ಇ", "ಈ"):
            # Conservative: insert 'ೆ' (e-matra) and drop initial vowel of w2
            # If w1 already ends with a vowel matra, remove it first to avoid duplication.
            if last in DEPENDENT_VOWELS:
                base = w1[:-1]
            else:
                base = w1
            # use 'ೆ' (short e) or 'ೇ' (long e) depending on previous vowel length — keep simple: 'ೆ'
            combined = base + "ೆ" + w2[1:]
            return combined

        # --- Existing CSV override rules (unchanged) ---
        if self.sandhi_rules_csv:
            for r in self.sandhi_rules_csv:
                s1 = r.get("sound1", "")
                s2 = r.get("sound2", "")
                if s1 == last and s2 == first:
                    comb = r.get("combined_result", "").strip()
                    res = r.get("result", "").strip()
                    del_first = str(r.get("delete_first_of_w2", "")).strip().lower() == "yes"
                    if comb:
                        return w1 + comb + (w2[1:] if del_first and len(w2) > 0 else w2)
                    if res:
                        if last in DEPENDENT_VOWELS and len(w1) >= 1:
                            w1_base = w1[:-1]
                        else:
                            w1_base = w1
                        return w1_base + res + (w2[1:] if del_first and len(w2) > 0 else w2)

        # --- Built-in rule table (unchanged logic) ---
        rule = self.find_sandhi_rule(last, first)
        if rule:
            comb = (rule.get("combined_result") or "").strip()
            res = (rule.get("result") or "").strip()
            del_first = str(rule.get("delete_first_of_w2") or "").strip().lower() == "yes"
            if comb:
                return w1 + comb + (w2[1:] if del_first and len(w2) > 0 else w2)
            if res:
                w1_base = w1[:-1] if last in DEPENDENT_VOWELS and len(w1) >= 1 else w1
                return w1_base + res + (w2[1:] if del_first and len(w2) > 0 else w2)

        # --- Heuristic fallbacks (keep existing) ---
        if last in ("ಇ","ಈ","ಎ","ಏ","ಐ") and first == "ಅ":
            return w1 + "ಯ" + w2[1:]
        if last in ("ಉ","ಊ","ಒ","ಓ","ಔ") and first == "ಅ":
            return w1 + "ವ" + w2[1:]
        if last and first and last == first:
            return w1 + w2[1:]

        # default concat
        return w1 + w2


    # ---------------- reverse_sandhi (UPDATED formatting-friendly) ----------------
    def reverse_sandhi(self, combined: str) -> List[Tuple[str,str]]:
        """
        Return ordered list of candidate splits (w1, w2).
        Heuristics + table-based reverse lookups.
        """
        w = self._norm(combined)
        if not w:
            return []
        candidates = []

        # 1) exact combined_result -> example splits
        if self.sandhi_table:
            for r in self.sandhi_table:
                comb = (r.get("combined_result") or "").strip()
                if comb and w.startswith(comb):
                    ex1 = (r.get("example_word1") or "").strip()
                    ex2 = (r.get("example_word2") or "").strip()
                    if ex1 and ex2:
                        candidates.append((ex1, ex2))

        # 2) inserted char heuristics (ಯ/ವ)
        for ch in ("ಯ","ವ"):
            pos = w.find(ch)
            if pos > 0:
                w1 = w[:pos]
                w2 = w[pos+1:]
                if w1 and w2:
                    candidates.append((w1, w2))

        # 3) brute-force splits validated by a sandhi rule
        n = len(w)
        for i in range(1, n):
            left = w[:i]; right = w[i:]
            last = self._last_char(left); first = self._first_char(right)
            rule = self.find_sandhi_rule(last, first)
            if rule:
                del_first = str(rule.get("delete_first_of_w2") or "").strip().lower() == "yes"
                if del_first and first:
                    candidates.append((left, first + right))
                else:
                    candidates.append((left, right))

        # 4) vowel-boundary fallback
        for i in range(1, n):
            if w[i] in INDEPENDENT_VOWELS:
                left = w[:i]; right = w[i:]
                if len(left) >= 2 and len(right) >= 2:
                    candidates.append((left, right))

        # deduplicate preserving order
        seen = set(); unique = []
        for a,b in candidates:
            key = (a,b)
            if key not in seen:
                seen.add(key); unique.append((a,b))
        return unique

    # ---------- vibhakti (word+ending) ----------
    def apply_vibhakti(self, word: str, ending: str) -> Tuple[str, Optional[str]]:
        w = self._norm(word); e = self._norm(ending)
        if not w or not e:
            return w + e, None

        # CSV override
        if self.vibhakti_rules_csv:
            for r in self.vibhakti_rules_csv:
                if r.get("base")==w and r.get("ending")==e:
                    return (r.get("output") or w+e, r.get("vibhakti_id") or None)

        # table
        for r in self.vibhakti_table:
            if r.get("base")==w and r.get("ending")==e:
                return (r.get("output") or w+e, r.get("vibhakti_id") or None)

        last = self._last_char(w)
        if e=="ಅನ್ನು":
            if last in INDEPENDENT_VOWELS or last in DEPENDENT_VOWELS or _is_kannada(last):
                return w + "ರನ್ನು", "2"
            return w + "ನ್ನು", "2"
        if e=="ಇಂದ":
            if last in INDEPENDENT_VOWELS or last in DEPENDENT_VOWELS or _is_kannada(last):
                return w + "ಯಿಂದ", "3"
            return w + "ಇಂದ", "3"
        if e in ("ಗೆ","ಕ್ಕೆ"):
            return w + e, "4"
        if e=="ಅಲ್ಲಿ":
            if last=="ಎ":
                return w[:-1] + "ೆಯಲ್ಲಿ", "7"
            return w + "ಲ್ಲಿ", "7"
        return w + e, None

    # ---------- vibhakti single helper (fuzzy/translit + default ending 'ಗೆ') ----------
    def apply_vibhakti_single(self, word: str, default_ending: str = "ಗೆ") -> Tuple[str, Optional[str]]:
        w = self._norm(word)
        if not w:
            return "", None

        # transliterate roman input
        if re.search(r'[A-Za-z]', w) and not _is_kannada(w):
            w_t = self.transliterate(w)
            if _is_kannada(w_t):
                w = w_t

        # exact base match in table -> prefer default ending row
        for r in self.vibhakti_table:
            if r.get("base")==w:
                for r2 in self.vibhakti_table:
                    if r2.get("base")==w and r2.get("ending")==default_ending:
                        return r2.get("output") or (w + default_ending), r2.get("vibhakti_id")
                return (r.get("output") or (w + default_ending)), r.get("vibhakti_id")

        # fuzzy match pool = vibhakti bases + roots
        pool = [r.get("base") for r in self.vibhakti_table if r.get("base")] + self._root_list
        pool = [p for p in pool if p]
        if pool:
            match = best_match(w, pool, cutoff=0.55)
            if match:
                # if there's an exact default ending row, use it
                for r in self.vibhakti_table:
                    if r.get("base")==match and r.get("ending")==default_ending:
                        return r.get("output") or (match + default_ending), r.get("vibhakti_id")
                return self.apply_vibhakti(match, default_ending)

        # try transliteration fallback
        if re.search(r'[A-Za-z]', word):
            w2 = self.transliterate(word)
            return self.apply_vibhakti(w2, default_ending)

        return self.apply_vibhakti(w, default_ending)

    # ---------- detect vibhakti id and suffix (from a full Kannada word if possible) ----------
    def detect_vibhakti(self, word: str) -> Tuple[Optional[str], Optional[str]]:
        w = self._norm(word)
        if not w:
            return None, None

        # check explicit vibhakti table outputs first
        for r in self.vibhakti_table:
            out = (r.get("output") or "").strip()
            base = (r.get("base") or "").strip()
            if out and w.endswith(out[-6:]):
                if w==out or out in w:
                    suf = out[len(base):] if base and out.startswith(base) else None
                    return r.get("vibhakti_id"), suf

        # longest-first suffix detection
        cand=[]
        for vid, s_list in self.vibhakti_suffixes.items():
            for s in s_list:
                if s and w.endswith(s):
                    cand.append((len(s), vid, s))
        if cand:
            cand.sort(reverse=True)
            _, vid, s = cand[0]
            return vid, s

        # fuzzy suffix on last up to 4 chars
        tail = w[-4:]
        suffix_pool = []
        for vid,s_list in self.vibhakti_suffixes.items():
            for s in s_list:
                if s:
                    suffix_pool.append((vid,s))
        pool = [s for (_,s) in suffix_pool]
        match = best_match(tail, pool, cutoff=0.6)
        if match:
            for vid,s in suffix_pool:
                if s==match:
                    return vid, s
        return None, None

    # ---------- validate compound (samasa) using dictionary + fuzzy fallback ----------
    def validate_compound(self, combined_word: str) -> Optional[Tuple[str,str]]:
        w = self._norm(combined_word)
        if not w:
            return None

        # 1) exact compound csv
        if w in self.compound_map:
            row = self.compound_map[w]
            b1 = row.get("base1") or row.get("part1") or row.get("example_word1") or ""
            b2 = row.get("base2") or row.get("part2") or row.get("example_word2") or ""
            if b1 and b2:
                return b1.strip(), b2.strip()

        # 2) reverse sandhi candidates -> pick first candidate with both parts in root_set or plausible
        cands = self.reverse_sandhi(w)
        for a,b in cands:
            if (self._is_valid_kannada_word(a) and self._is_valid_kannada_word(b)):
                return a,b
            # if root list exists, use fuzzy to check membership
            if self._root_list:
                if best_match(a, self._root_list, cutoff=0.6) or best_match(b, self._root_list, cutoff=0.6):
                    return a,b

        # 3) fuzzy lookup in compound map keys
        sugg = fuzzy_matches(w, list(self.compound_map.keys()), n=1, cutoff=0.5)
        if sugg:
            key = sugg[0]
            row = self.compound_map.get(key)
            if row:
                b1 = row.get("base1") or row.get("example_word1") or ""
                b2 = row.get("base2") or row.get("example_word2") or ""
                if b1 and b2:
                    return b1.strip(), b2.strip()

        # 4) vowel fallback split (last independent vowel)
        n=len(w)
        for i in range(1,n):
            if w[i] in INDEPENDENT_VOWELS:
                left=w[:i]; right=w[i:]
                if len(left)>=2 and len(right)>=2:
                    return left, right

        return None

    def apply_compound(self, word: str) -> Optional[Tuple[str,str]]:
        return self.validate_compound(word)

    def _is_valid_kannada_word(self, w: str) -> bool:
        w=self._norm(w)
        if len(w)<2: return False
        if not _is_kannada(w): return False
        if self.root_set:
            return w in self.root_set or any(r.startswith(w) or w.startswith(r) for r in self.root_set)
        return True

    # ---------- suggestions ----------
    def get_suggestions(self, word: str, n:int=6) -> List[str]:
        w=self._norm(word)
        if not w: return []
        pool = list(dict.fromkeys(self._compound_list + self._root_list))
        if not pool: return []
        return fuzzy_matches(w, pool, n=n, cutoff=0.5)

    # ---------- transliteration (conservative) ----------
    def transliterate(self, latin: str) -> str:
        s=(latin or "").strip().lower()
        if not s: return ""
        patterns = [
            ("sh","ಶ"),("ch","ಚ"),("kh","ಖ"),("gh","ಘ"),
            ("th","ಥ"),("dh","ಧ"),("ph","ಫ"),("bh","ಭ"),
            ("aa","ಾ"),("ii","ೀ"),("ee","ೀ"),("oo","ೋ"),
            ("au","ೌ"),("ai","ೈ")
        ]
        out=""; i=0
        while i < len(s):
            matched=False
            for pat,rep in patterns:
                if s.startswith(pat,i):
                    out += rep; i += len(pat); matched=True; break
            if matched: continue
            ch=s[i]
            table = {
                "a":"ಅ","i":"ಇ","u":"ಉ","e":"ಎ","o":"ಒ",
                "k":"ಕ","g":"ಗ","j":"ಜ","t":"ಟ","d":"ಡ",
                "n":"ನ","p":"ಪ","b":"ಬ","m":"ಮ","y":"ಯ",
                "r":"ರ","l":"ಲ","v":"ವ","s":"ಸ","h":"ಹ","w":"ವ"
            }
            out += table.get(ch,ch)
            i += 1
        out = re.sub(r"ಅಅ+", "ಆ", out)
        return out

# quick test driver
if __name__ == "__main__":
    wj = WordJoiner()
    print("Sandhi: ಶಕ್ತಿ + ಅಭಿಮಾನ ->", wj.apply_sandhi("ಶಕ್ತಿ","ಅಭಿಮಾನ"))
    print("Reverse sandhi candidates for 'ಶಕ್ತ್ಯಭಿಮಾನ':", wj.reverse_sandhi("ಶಕ್ತ್ಯಭಿಮಾನ"))
    print("Vibhakti single: raama ->", wj.apply_vibhakti_single("raama"))
    print("Samasa validate: ಲಕ್ಷ್ಮೀನಾರಾಯಣ ->", wj.validate_compound("ಲಕ್ಷ್ಮೀನಾರಾಯಣ"))
    print("Suggestions:", wj.get_suggestions("ಲಕ್ಷ್ಮೀನಾರಾ"))
