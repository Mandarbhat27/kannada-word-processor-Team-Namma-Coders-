# extract_compounds_from_wiki.py

import requests, argparse, csv, time, re, os
from collections import Counter
from tqdm import tqdm

API = "https://kn.wikipedia.org/w/api.php"
HEADERS = {"User-Agent":"CompoundExtractor/1.0"}

def get_random_pages(n=100):
    params = {
        "action":"query",
        "list":"random",
        "rnlimit":n,
        "rnnamespace":0,
        "format":"json"
    }
    r = requests.get(API, params=params, headers=HEADERS, timeout=20).json()
    return [p['title'] for p in r['query']['random']]

def get_page_text(title):
    params = {
        "action":"query",
        "prop":"extracts",
        "explaintext":"1",
        "titles":title,
        "format":"json"
    }
    r = requests.get(API, params=params, headers=HEADERS, timeout=20).json()
    pages = r['query']['pages']
    page = next(iter(pages.values()))
    return page.get('extract','')

def tokenize(text):
    # Kannada Unicode range \u0C80-\u0CFF
    tokens = re.findall(r'[\u0C80-\u0CFF]+', text)
    return tokens

def main(target=2500, outpath="../dictionaries/compound_words.csv"):
    pairs = Counter()

    # progress bar
    pbar = tqdm(total=target, desc="Collecting compound candidates")

    while len(pairs) < target:
        titles = get_random_pages(60)

        for t in titles:
            text = get_page_text(t)
            toks = tokenize(text)

            for i in range(len(toks)-1):
                w1, w2 = toks[i], toks[i+1]

                if len(w1) < 2 or len(w2) < 2:
                    continue

                pairs[(w1, w2)] += 1
                pbar.update(1)

                if len(pairs) >= target:
                    break

            if len(pairs) >= target:
                break

        time.sleep(1)

    pbar.close()

    # ensure directory exists
    out_dir = os.path.dirname(outpath)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    # write CSV
    rows = []
    for (w1, w2), count in pairs.most_common(target):
        combined = w1 + w2
        freq = "high" if count > 10 else ("medium" if count > 3 else "low")
        rows.append({
            "word1": w1,
            "word2": w2,
            "combined": combined,
            "frequency": freq
        })

    with open(outpath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["word1","word2","combined","frequency"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"\n✔ Successfully wrote {len(rows)} compounds to {outpath}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=2500)
    parser.add_argument("--out", type=str, default="../dictionaries/compound_words.csv")
    args = parser.parse_args()
    main(args.target, args.out)
