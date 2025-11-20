# generate_test_cases.py
import pandas as pd, csv, argparse, random
from tqdm import tqdm

def main(target=500, out="../test_cases/word_pairs_test.csv"):
    comp = pd.read_csv("../dictionaries/compound_words.csv", dtype=str).fillna('')
    roots = pd.read_csv("../dictionaries/root_words.csv", dtype=str).fillna('')
    rows = []
    # add valid pairs from compounds (as many as possible)
    for idx, r in comp.iterrows():
        if len(rows) >= target*0.6:
            break
        rows.append({
            "test_id": len(rows)+1,
            "word1": r['word1'],
            "word2": r['word2'],
            "expected_result": r['combined'],
            "sandhi_rule_used": "",
            "is_valid_compound":"yes"
        })
    # add negatives (random pairings)
    while len(rows) < target:
        w1 = roots.sample(1).iloc[0]['word']
        w2 = roots.sample(1).iloc[0]['word']
        combined = w1 + w2
        rows.append({
            "test_id": len(rows)+1,
            "word1": w1,
            "word2": w2,
            "expected_result": combined,
            "sandhi_rule_used": "",
            "is_valid_compound":"no"
        })
    # save
    with open(out,"w",encoding="utf-8",newline="") as f:
        fieldnames = ["test_id","word1","word2","expected_result","sandhi_rule_used","is_valid_compound"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    print(f"Wrote {len(rows)} test cases to {out}")

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=500)
    parser.add_argument("--out", type=str, default="../test_cases/word_pairs_test.csv")
    args = parser.parse_args()
    main(args.target, args.out)
