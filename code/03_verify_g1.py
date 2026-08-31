#!/usr/bin/env python3
"""
Verifies the Australian tradables / non-tradables inflation figures quoted in
Section III.A against RBA Statistical Table G1.

Input : data_raw/rba_table_g1.csv
Output: output/03_results.txt
"""
import csv, os, numpy as np, pandas as pd

HERE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW,OUT=os.path.join(HERE,'data_raw'),os.path.join(HERE,'output')
os.makedirs(OUT,exist_ok=True); log=[]
def say(x):
    print(x); log.append(str(x))

rows=list(csv.reader(open(os.path.join(RAW,'rba_table_g1.csv'), encoding='utf-8-sig')))
sid=[r for r in rows if r and r[0]=='Series ID'][0]
data=[r for r in rows[rows.index(sid)+1:] if r and r[0]]
idx=pd.to_datetime([r[0] for r in data], dayfirst=True, errors='coerce')
def col(code):
    j=sid.index(code)
    return pd.Series([pd.to_numeric(r[j],errors='coerce') if j<len(r) else np.nan
                      for r in data], index=idx).astype(float)

# Series as named in the paper's Appendix B.
t, nt, cpi = col('GCPITXVIYP'), col('GCPINTIYP'), col('GCPIAGYP')
say("Mean of year-ended quarterly rates (per cent)")
say(f"{'period':12s} {'tradables':>10s} {'non-tradables':>14s} {'headline':>10s}   paper says")
claims={'1997-2017':(0.38,3.26),'2022':(5.9,None),'2023':(4.5,None),'2024':(1.0,4.3),'2025':(1.6,3.8)}
for lab,(pt,pn) in claims.items():
    a,b=(lab.split('-')+[lab])[:2] if '-' in lab else (lab,lab)
    f=lambda s: s.loc[f'{a}-01-01':f'{b}-12-31'].dropna().mean()
    note=f"tradables {pt}" + (f", non-tradables {pn}" if pn is not None else "")
    say(f"{lab:12s} {f(t):10.2f} {f(nt):14.2f} {f(cpi):10.2f}   {note}")
x=t.loc['1997':'2017'].dropna(); yr=x.groupby(x.index.year).mean()
say(f"\ntradables at or below zero in {(yr<=0).sum()} of {len(yr)} years, 1997-2017   paper says 7 of 21")
open(os.path.join(OUT,'03_results.txt'),'w').write('\n'.join(log)+'\n')
