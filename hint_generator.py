# hint_generator.py
import pandas as pd

class HintGenerator:
    def __init__(self, compound_csv="../dictionaries/compound_words.csv"):
        self.df = pd.read_csv(compound_csv, dtype=str).fillna('')

    def hints_for(self, word1, limit=5):
        df = self.df[self.df['word1']==word1]
        if df.empty:
            # fallback: any compound where word1 is a substring
            df = self.df[self.df['word1'].str.contains(word1, na=False)]
        df = df.head(limit)
        return df.to_dict('records')
