import pandas as pd

df = pd.read_csv('bbl.csv')
df[df.full_bib.str.contains('arXiv:')].to_csv('arxiv_bbls.csv', index=False)
pass