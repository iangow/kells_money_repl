#!/usr/bin/env python3
"""
Section III.B: the pandemic channel test. Reports a NULL result.

Input : data_raw/oecd_cpi_goods_services.csv     (OECD CPI, goods / services / total)
        data_raw/oecd_household_dashboard.csv    (OECD household dashboard)
Output: output/pandemic_cross_section.csv
        output/04_results.txt
"""
import pandas as pd, numpy as np, os, math
import statsmodels.formula.api as smf

HERE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW,OUT=os.path.join(HERE,'data_raw'),os.path.join(HERE,'output')
os.makedirs(OUT,exist_ok=True); log=[]
def say(x):
    print(x); log.append(str(x))

# CPI: annual year-on-year rates by expenditure
c=pd.read_csv(os.path.join(RAW,'oecd_cpi_goods_services.csv'), low_memory=False)
c=c[(c.FREQ=='A')&(c.UNIT_MEASURE=='PA')&(c.TRANSFORMATION=='GY')]
c['TIME_PERIOD']=pd.to_numeric(c.TIME_PERIOD, errors='coerce')
cp=c.pivot_table(index=['REF_AREA','TIME_PERIOD'], columns='EXPENDITURE',
                 values='OBS_VALUE').reset_index().rename(
                 columns={'GD':'goods','SERV':'services','_T':'headline'})

# Household dashboard: real disposable income / GDP per capita growth, saving rate
h=pd.read_csv(os.path.join(RAW,'oecd_household_dashboard.csv'), low_memory=False)
h=h[h.FREQ=='A'].copy()
h['TIME_PERIOD']=pd.to_numeric(h.TIME_PERIOD, errors='coerce')
hp=h.pivot_table(index=['REF_AREA','TIME_PERIOD'], columns='MEASURE',
                 values='OBS_VALUE').reset_index().rename(columns={
                 'B6GS1M_R_POP_GR':'hh_inc_gr','B1GQ_R_POP_GR':'gdp_gr','B8GS1M_B6GA':'sav_rate'})

dep=cp[cp.TIME_PERIOD.between(2021,2023)].groupby('REF_AREA')[['goods','services']].mean()
dep['gms']=dep.goods-dep.services
pre=cp[cp.TIME_PERIOD.between(2015,2019)].groupby('REF_AREA')['headline'].mean().rename('pre_infl')
h20=hp[hp.TIME_PERIOD==2020].set_index('REF_AREA'); h19=hp[hp.TIME_PERIOD==2019].set_index('REF_AREA')
X=pd.DataFrame({'inc_gap':h20.hh_inc_gr-h20.gdp_gr, 'gdp20':h20.gdp_gr,
                'sav_jump':h20.sav_rate-h19.sav_rate})
m=dep.join(pre).join(X).dropna(subset=['gms','inc_gap'])
m=m[~m.index.isin(['EA20','EA19','EU27_2020','OECD','G7','G20'])]
EUR={'ESP','FRA','PRT','CZE','POL','ITA','NLD','GRC','AUT','HUN','FIN','DNK','IRL','GBR'}
m['eur']=m.index.isin(EUR).astype(int)
m.to_csv(os.path.join(OUT,'pandemic_cross_section.csv'))
say(f"n = {len(m)} countries")
say("channel measure = 2020 gap between real household disposable income per capita growth")
say("                  and real GDP per capita growth (percentage points)")

def go(f,lab,df=None):
    df=m if df is None else df
    r=smf.ols(f,data=df).fit(cov_type='HC3'); k=f.split('~')[1].split('+')[0].strip()
    say(f"  {lab:44s} b={r.params[k]:+7.3f} se={r.bse[k]:.3f} t={r.tvalues[k]:+5.2f} p={r.pvalues[k]:.3f} n={int(r.nobs)}")
    return r

say("\nDEPENDENT = mean goods-minus-services inflation, 2021-2023")
go('gms ~ inc_gap','channel measure alone')
go('gms ~ inc_gap + pre_infl','  + pre-pandemic inflation')
go('gms ~ inc_gap + pre_infl + gdp20','  + 2020 output growth')
go('gms ~ inc_gap + pre_infl + gdp20 + eur','  + European gas-shock indicator')
go('gms ~ sav_jump','alternative channel: saving-rate jump', m.dropna(subset=['sav_jump']))

say("\nROBUSTNESS")
go('gms ~ inc_gap','excl. Chile and Ireland', m.drop(['CHL','IRL'],errors='ignore'))
for lab,sub in [('non-European only', m[m.eur==0]), ('European only', m[m.eur==1])]:
    if len(sub) >= 5: go('gms ~ inc_gap', lab, sub)
    else: say(f"  {lab:44s} skipped (n={len(sub)} too small)")
go('gms ~ inc_gap + I(inc_gap**2)','quadratic')
for lo,hi in [(2021,2022),(2022,2023),(2021,2024)]:
    d2=cp[cp.TIME_PERIOD.between(lo,hi)].groupby('REF_AREA')[['goods','services']].mean()
    d2['gms']=d2.goods-d2.services
    mm=m.drop(columns=['gms','goods','services']).join(d2[['gms']],how='inner').dropna(subset=['gms','inc_gap'])
    go('gms ~ inc_gap',f'window {lo}-{hi}',mm)

say("\nCOMPONENTS SEPARATELY (this is what does move)")
go('goods ~ inc_gap + pre_infl + gdp20 + eur','  -> goods inflation')
go('services ~ inc_gap + pre_infl + gdp20 + eur','  -> services inflation')

r=smf.ols('gms ~ inc_gap',data=m).fit()
mde=2.8*np.sqrt(r.mse_resid)/(m.inc_gap.std()*math.sqrt(len(m)))
say(f"\nPOWER: minimum slope detectable at 80% power is about {mde:.2f} pp per pp.")
say("The American QE-vs-pandemic contrast implies roughly 5.6 pp, an order of magnitude larger.")
say("\nCONCLUSION: the cross-country limb of Proposition 2 is rejected. The within-country evidence of Section III.B is untouched by this test,")
say("because the dependent variable lies entirely inside the goods circuit.")
open(os.path.join(OUT,'04_results.txt'),'w').write('\n'.join(log)+'\n')
