# scrape_wikipedia_roots.py

import requests, time, csv, argparse, re, os
from tqdm import tqdm
from collections import OrderedDict

API = "https://kn.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "WordBuilderBot/1.0 (contact: you@example.com)"}

def get_random_pages(n=50):
    params = {
        "action": "query",
        "list": "random",
        "rnlimit": n,
        "rnnamespace": 0,
        "format": "json"
    }
    r = requests.get(API, params=params, headers=HEADERS, timeout=20).json()
    return [p['title'] for p in r['query']['random']]

def get_page_text(title):
    params = {
        "action": "query",
        "prop": "extracts",
        "explaintext": "1",
        "titles": title,
        "format": "json"
    }
    r = requests.get(API, params=params, headers=HEADERS, timeout=20).json()
    pages = r['query']['pages']
    page = next(iter(pages.values()))
    return page.get('extract', '')

def tokenize_kannada_text(text):
    # Kannada Unicode range \u0C80-\u0CFF
    tokens = re.findall(r'[\u0C80-\u0CFF]+', text)
    return tokens

def normalize_word(w):
    return w.strip()

def main(target=5000, outpath="../dictionaries/root_words.csv"):

    seen = OrderedDict()

    # Try to load seed file
    try:
        with open("../dictionaries/root_words_seed.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                w = normalize_word(r["word"])
                seen[w] = r
    except FileNotFoundError:
        pass

    pbar = tqdm(total=target, desc="Collecting words")
    pbar.update(len(seen))

    # Start scraping random pages
    while len(seen) < target:
        try:
            titles = get_random_pages(30)
        except Exception as e:
            print("API error:", e)
            time.sleep(3)
            continue

        for t in titles:
            text = get_page_text(t)
            tokens = tokenize_kannada_text(text)

            for tok in tokens:
                tok = normalize_word(tok)

                # skip too short words or numeric content
                if len(tok) < 2 or any(ch.isdigit() for ch in tok):
                    continue

                if tok not in seen:
                    seen[tok] = {
                        "word": tok,
                        "meaning": "",
                        "word_type": "",
                        "last_sound": tok[-1],
                        "can_combine": "yes"
                    }
                    pbar.update(1)

                if len(seen) >= target:
                    break

            if len(seen) >= target:
                break

        time.sleep(1)

    pbar.close()

    # ----------------------------
    # FIXED: Ensure output folder exists
    # ----------------------------
    out_dir = os.path.dirname(outpath)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    # ----------------------------
    # Write final CSV output
    # ----------------------------
    with open(outpath, "w", encoding="utf-8", newline="") as f:
        fieldnames = ["word", "meaning", "word_type", "last_sound", "can_combine"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for w, row in seen.items():
            writer.writerow({
                "word": row.get("word", w),
                "meaning": row.get("meaning", ""),
                "word_type": row.get("word_type", ""),
                "last_sound": row.get("last_sound", w[-1] if w else ""),
                "can_combine": row.get("can_combine", "yes")
            })

    print(f"\n✔ Successfully wrote {len(seen)} words to {outpath}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=5000, help="target # of root words")
    parser.add_argument("--out", type=str, default="../dictionaries/root_words.csv")
    args = parser.parse_args()
    main(args.target, args.out)
