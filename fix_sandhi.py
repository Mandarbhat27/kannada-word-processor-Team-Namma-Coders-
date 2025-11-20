# code/fix_sandhi.py
import csv, pathlib

out = pathlib.Path("dictionaries/sandhi_rules.csv")

rows = [
    {"rule_number":"1","sound1":"ಾ","sound2":"ಆ","result":"","combined_result":"ಮಹಾತ್ಮ","example_word1":"ಮಹಾ","example_word2":"ಆತ್ಮ","notes":"ಾ + ಆ → drop ಆ and merge"},
    {"rule_number":"2","sound1":"ೆ","sound2":"ಅ","result":"ಯ","combined_result":"","example_word1":"ಮನೆ","example_word2":"ಅಂಗಳ","notes":"ೆ + ಅ → insert ಯ"},
    {"rule_number":"3","sound1":"ಿ","sound2":"ಅ","result":"ಯ","combined_result":"","example_word1":"ಶಕ್ತಿ","example_word2":"ಅಭಿಮಾನ","notes":"ಿ + ಅ → insert ಯ"},
    {"rule_number":"4","sound1":"ಂ","sound2":"ಕ","result":"ಂ","combined_result":"ಸಂಕೀರ್ತನೆ","example_word1":"ಸಂ","example_word2":"ಕೀರ್ತನೆ","notes":"anuswara rule"},
    {"rule_number":"5","sound1":"ಂ","sound2":"ಗ","result":"ಂ","combined_result":"ಸಂಗೀತ","example_word1":"ಸಂ","example_word2":"ಗೀತ","notes":"anuswara rule"},
    {"rule_number":"6","sound1":"ಃ","sound2":"ಅ","result":"","combined_result":"ಬ್ರಹ್ಮ ಇತಿ","example_word1":"ಬ್ರಹ್ಮಃ","example_word2":"ಇತಿ","notes":"visarga drop"}
]

fieldnames = ["rule_number","sound1","sound2","result","combined_result","example_word1","example_word2","notes"]

out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

print("Wrote fixed sandhi_rules.csv to", out.resolve())
