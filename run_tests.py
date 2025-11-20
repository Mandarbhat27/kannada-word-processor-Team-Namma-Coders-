# run_tests.py
import pandas as pd
from word_joiner import WordJoiner
import csv, os

def main(test_csv="../test_cases/word_pairs_test.csv"):
    wj = WordJoiner()
    tests = pd.read_csv(test_csv, dtype=str).fillna('')
    total = len(tests)
    correct = 0
    failures = []
    for _, row in tests.iterrows():
        w1 = row['word1']
        w2 = row['word2']
        expected = row['expected_result']
        combined, rule = wj.apply_sandhi(w1, w2)
        is_ok = (combined == expected)
        if is_ok:
            correct += 1
        else:
            failures.append({
                "word1":w1, "word2":w2, "expected":expected, "got":combined, "rule":rule
            })
    acc = correct/total*100
    print(f"Total: {total}, Correct: {correct}, Accuracy: {acc:.2f}%")
    os.makedirs("test_results", exist_ok=True)
    with open("test_results/failures.csv","w",encoding="utf-8",newline="") as f:
        fieldnames = ["word1","word2","expected","got","rule"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in failures:
            writer.writerow(r)
    print(f"Wrote {len(failures)} failures to test_results/failures.csv")

if __name__=="__main__":
    main()
