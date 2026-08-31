#!/usr/bin/env python3
"""
Table 3 and Figure 2: credit composition, house prices and rents, 21 economies.

Input : data_raw/oecd_house_prices_raw.csv   (OECD analytical house price indicators)
        data_raw/bis_fredgraph*.csv          (BIS credit via FRED, 4 files)
Output: output/panel_annual.csv
        output/fig2_credit_prices_rents.png
        output/02_results.txt
"""
import pandas as pd, numpy as np, glob, os
import statsmodels.formula.api as smf
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW, OUT = os.path.join(HERE,'data_raw'), os.path.join(HERE,'output')
os.makedirs(OUT, exist_ok=True)
SEED = 7
log=[]
def say(x):
    print(x); log.append(str(x))

# ---------- credit ----------
frames=[pd.read_csv(f, parse_dates=['observation_date']).set_index('observation_date')
        for f in sorted(glob.glob(os.path.join(RAW,'bis_fredgraph*.csv')))]
cr=pd.concat(frames, axis=1).apply(pd.to_numeric, errors='coerce')
recs=[]
for c in cr.columns:
    s=cr[c].dropna()
    recs.append(pd.DataFrame({'iso2':c[1:3], 'var':'hh' if c[3]=='H' else 'nfc',
                              'date':s.index, 'val':s.values}))
w=pd.concat(recs).pivot_table(index=['iso2','date'], columns='var', values='val').reset_index()
w['hh_share']=w.hh/(w.hh+w.nfc)*100
w=w.dropna(subset=['hh_share'])

# ---------- OECD prices ----------
d=pd.read_csv(os.path.join(RAW,'oecd_house_prices_raw.csv'), low_memory=False)
d=d[(d.FREQ=='Q') & (d.MEASURE.isin(['HPI_RPI','HPI','RPI']))].copy()
d['date']=pd.PeriodIndex(d.TIME_PERIOD, freq='Q').to_timestamp()
p=d.pivot_table(index=['REF_AREA','date'], columns='MEASURE', values='OBS_VALUE').reset_index()
iso={'AUS':'AU','AUT':'AT','BEL':'BE','CAN':'CA','CHE':'CH','DEU':'DE','DNK':'DK','ESP':'ES',
     'FIN':'FI','FRA':'FR','GBR':'GB','IRL':'IE','ITA':'IT','JPN':'JP','KOR':'KR','NLD':'NL',
     'NOR':'NO','NZL':'NZ','PRT':'PT','SWE':'SE','USA':'US'}
p['iso2']=p.REF_AREA.map(iso)
p=p.dropna(subset=['iso2','HPI_RPI'])

m=p.merge(w[['iso2','date','hh_share']], on=['iso2','date'], how='inner').sort_values(['iso2','date'])
a=m[m.date.dt.month==10].copy(); a['year']=a.date.dt.year
for v,nm in [('HPI_RPI','ptr'),('HPI','hp'),('RPI','rent')]:
    a['d_'+nm]=a.groupby('iso2')[v].transform(lambda s: np.log(s).diff()*100)
a['d_hh']=a.groupby('iso2')['hh_share'].diff()
a=a.dropna(subset=['d_ptr','d_hp','d_rent','d_hh','hh_share'])
a.to_csv(os.path.join(OUT,'panel_annual.csv'), index=False)
say(f"panel: {len(a)} country-years, {a.iso2.nunique()} countries, {a.year.min()}-{a.year.max()}")

def fit(df, dep, reg='d_hh'):
    r=smf.ols(f"{dep} ~ {reg} + C(iso2) + C(year)", data=df).fit(
        cov_type='cluster', cov_kwds={'groups':df.iso2})
    return r.params[reg], r.bse[reg], r.tvalues[reg], r.pvalues[reg], int(r.nobs)

def wildboot(dep, reg='d_hh', B=999):
    rng=np.random.default_rng(SEED)
    t_obs=fit(a,dep,reg)[2]
    r0=smf.ols(f"{dep} ~ C(iso2) + C(year)", data=a).fit()
    fit0,res0=r0.fittedvalues,r0.resid
    codes=pd.factorize(a.iso2.values)[0]; G=codes.max()+1
    d=a.copy(); cnt=0
    for _ in range(B):
        d['_y']=fit0+res0*rng.choice([-1.0,1.0],size=G)[codes]
        tb=smf.ols(f"_y ~ {reg} + C(iso2) + C(year)", data=d).fit(
            cov_type='cluster',cov_kwds={'groups':d.iso2}).tvalues[reg]
        if abs(tb)>=abs(t_obs): cnt+=1
    return (cnt+1)/(B+1)

say("\nTABLE 3 — regressor: annual change in the household share of total credit (pp)")
say(f"{'dependent (annual change, log pts)':38s} {'coef':>8s} {'clSE':>7s} {'t':>7s} {'boot p':>8s}")
for dep,lab in [('d_hp','nominal house prices'),('d_rent','rents'),('d_ptr','price-to-rent ratio')]:
    b,se,t,_,n=fit(a,dep); say(f"{lab:38s} {b:+8.3f} {se:7.3f} {t:+7.2f} {wildboot(dep):8.3f}")
b,se,t,pv,n=fit(a,'d_ptr','hh_share')
say(f"\nmemo: level of the household credit share on price-to-rent  b={b:+.3f} (se {se:.3f}, t={t:+.2f}) -- convergence")

say("\nROBUSTNESS (dependent = nominal house prices | rents)")
tests=[('baseline',a),
       ('excl. Australia and New Zealand', a[~a.iso2.isin(['AU','NZ'])]),
       ('excl. United States', a[a.iso2!='US']),
       ('1990 onwards', a[a.year>=1990]),
       ('excl. 2007-2012', a[~a.year.between(2007,2012)]),
       ('excl. 2020-2021', a[~a.year.between(2020,2021)])]
for lab,df in tests:
    bh,seh,th,ph,nh=fit(df,'d_hp'); br,ser,tr,pr,_=fit(df,'d_rent')
    say(f"  {lab:34s} prices {bh:+6.3f} (p={ph:.4f}) | rents {br:+6.3f} (p={pr:.3f})  n={nh}")

# ---------- Figure 2 ----------
H=range(0,6); res={'HPI':[],'RPI':[]}
say("\nLOCAL PROJECTIONS (cumulative, country+year FE)")
for h in H:
    for v in ['HPI','RPI']:
        a[f'c_{v}']=a.groupby('iso2')[v].transform(lambda s:(np.log(s.shift(-h))-np.log(s.shift(1)))*100)
    dd=a.dropna(subset=['c_HPI','c_RPI','d_hh'])
    row=[]
    for v in ['HPI','RPI']:
        b,se,t,pv,n=fit(dd,f'c_{v}'); res[v].append((b,se)); row.append(f"{v} {b:+6.3f} ({se:.3f}) p={pv:.3f}")
    say(f"  h={h}  " + "   ".join(row))

INK,GREY='#1a1a1a','#8a8a8a'
fig,ax=plt.subplots(figsize=(6.6,3.5)); x=np.array(list(H))
for v,col,ls,lab in [('HPI',INK,'-','House prices'),('RPI',GREY,'--','Rents')]:
    b=np.array([r[0] for r in res[v]]); se=np.array([r[1] for r in res[v]])
    ax.fill_between(x,b-1.96*se,b+1.96*se,color=col,alpha=0.11,lw=0)
    ax.plot(x,b,color=col,lw=2,ls=ls,solid_capstyle='round',zorder=3)
    ax.annotate(lab, xy=(x[-1],b[-1]), xytext=(6,0), textcoords='offset points',
                fontsize=9, color=col, va='center', fontweight='bold')
ax.axhline(0,color='#c4c4c4',lw=1,zorder=1)
ax.set_xlabel('years after the change in credit composition', fontsize=9, color=INK)
ax.set_ylabel('cumulative response (%)', fontsize=9, color=INK)
ax.set_xlim(-0.15,5.9); ax.set_xticks(list(H))
ax.grid(axis='y', color='#efefef', lw=0.8); ax.set_axisbelow(True)
for sp in ['top','right']: ax.spines[sp].set_visible(False)
for sp in ['left','bottom']: ax.spines[sp].set_color('#bdbdbd')
ax.tick_params(colors='#6b6b6b', labelsize=8.5, length=3)
ax.set_title('Response to a one-point rise in the household share of credit:\n'
             '21 advanced economies, country and year fixed effects',
             fontsize=9.5, color=INK, loc='left', pad=10, linespacing=1.4)
fig.tight_layout(); fig.savefig(os.path.join(OUT,'fig2_credit_prices_rents.png'),
                                dpi=220, facecolor='white', bbox_inches='tight')
open(os.path.join(OUT,'02_results.txt'),'w').write('\n'.join(log)+'\n')
say("\nwrote output/panel_annual.csv, output/fig2_credit_prices_rents.png")
