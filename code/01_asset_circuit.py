#!/usr/bin/env python3
"""
Figure 1 and the Section III.A asset-circuit statistics.

Input : data_raw/560103.xlsx  (ABS 5601.0 Lending Indicators, Table 3)
Output: output/asset_circuit_series.csv
        output/fig1_asset_circuit_share.png
        output/01_results.txt
"""
import openpyxl, pandas as pd, numpy as np, os
from scipy import stats
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW, OUT = os.path.join(HERE,'data_raw'), os.path.join(HERE,'output')
os.makedirs(OUT, exist_ok=True)
log = []
def say(x):
    print(x); log.append(str(x))

# --- load: Original series, $ millions ---
wb = openpyxl.load_workbook(os.path.join(RAW,'560103.xlsx'), read_only=True, data_only=True)
rows = list(wb['Data1'].iter_rows(values_only=True))
names, units, stype = rows[0], rows[1], rows[2]
cols = {i: str(names[i]).split(';')[3].strip()
        for i in range(1, len(names))
        if names[i] and str(units[i]) == '$ Millions' and str(stype[i]) == 'Original'}
data = [r for r in rows[10:] if r[0] is not None]
v = pd.DataFrame({c: [r[i] for r in data] for i, c in cols.items()},
                 index=pd.to_datetime([r[0] for r in data])).astype(float)

tot      = v['Total dwellings excluding refinancing']
existing = v['Purchase of existing dwellings']
newbuild = v['Construction of dwellings'] + v['Purchase of newly erected dwellings']
share    = existing / tot * 100

say(f"identity check: (existing + construction + newly erected) / stated total = {(existing+newbuild).div(tot).mean():.4f}")
say(f"sample {share.index.min().date()} to {share.index.max().date()}, n={len(share)}")
say("")
ma4 = share.rolling(4).mean().dropna()
say(f"asset-circuit share, sample mean       {share.mean():.1f}%  (sd {share.std():.2f})   [paper: 81.4]")
say("  unsmoothed series")
say(f"    minimum {share.min():.1f}% at {share.idxmin().date()}")
say(f"    maximum {share.max():.1f}% at {share.idxmax().date()}")
say("  four-quarter moving average (the series plotted in Figure 1)")
say(f"    low {ma4.min():.1f}% at {ma4.idxmin().date()}                         [paper: 75.4, early 2021]")
say(f"    maximum {ma4.max():.1f}% at {ma4.idxmax().date()}")
say(f"    at end of sample {ma4.iloc[-1]:.1f}% at {ma4.index[-1].date()}         [paper: 84.8, March 2026]")

constr = v['Construction of dwellings'] / tot * 100
say("")
say(f"construction share 2020Q1 {constr.loc['2020-03-01']:.1f}%  ->  2021Q1 {constr.loc['2021-03-01']:.1f}%")
say(f"  maximum before 2020Q2: {constr.loc[:'2020-03'].max():.1f}%")

a = share.loc['2010':'2013']; b = share.loc['2015':'2018']; c = share.loc['2022':]
t1 = stats.ttest_ind(a, b, equal_var=False); t2 = stats.ttest_ind(a, c, equal_var=False)
say("")
say(f"2010-13 mean {a.mean():.2f}  vs 2015-18 mean {b.mean():.2f}   t={t1.statistic:+.2f}  p={t1.pvalue:.3f}")
say(f"2010-13 mean {a.mean():.2f}  vs 2022-26 mean {c.mean():.2f}   t={t2.statistic:+.2f}  p={t2.pvalue:.5f}")

out = pd.DataFrame({
    'total_excl_refi_$m': tot,
    'existing_dwellings_$m': existing,
    'construction_$m': v['Construction of dwellings'],
    'newly_erected_$m': v['Purchase of newly erected dwellings'],
    'asset_circuit_share_pct': share,
    'goods_circuit_share_pct': newbuild / tot * 100,
    'memo_alterations_$m': v['Alterations, additions and repairs'],
    'memo_external_refi_$m': v['External refinancing'],
})
out.index.name = 'quarter'
out.round(3).to_csv(os.path.join(OUT,'asset_circuit_series.csv'))

# --- figure ---
s4 = share.rolling(4).mean().dropna()
INK, MUTED, BAND, BAND2 = '#1a1a1a', '#6b6b6b', '#e8e8e8', '#d6d6d6'
fig, ax = plt.subplots(figsize=(7.2, 3.6))
ax.axvspan(pd.Timestamp('2014-12-01'), pd.Timestamp('2018-12-31'), color=BAND, zorder=0, lw=0)
ax.axvspan(pd.Timestamp('2020-06-01'), pd.Timestamp('2021-03-31'), color=BAND2, zorder=0, lw=0)
ax.plot(s4.index, s4.values, color=INK, lw=2, solid_capstyle='round', zorder=3)
ax.axhline(share.mean(), color=MUTED, lw=1, ls=(0,(4,3)), zorder=1)
ax.annotate(f'sample mean {share.mean():.1f}', xy=(pd.Timestamp('2004-06-01'), share.mean()),
            xytext=(0,4), textcoords='offset points', fontsize=8, color=MUTED, va='bottom')
ax.annotate('APRA sectoral\ninterventions', xy=(pd.Timestamp('2016-11-01'), 86.4),
            fontsize=8, color=MUTED, ha='center', va='top', linespacing=1.25)
ax.annotate('HomeBuilder', xy=(pd.Timestamp('2020-11-01'), 86.4), fontsize=8,
            color=MUTED, ha='center', va='top')
for pt, dx, dy, ha in [(s4.idxmin(), 6, -10, 'left'), (s4.index[-1], -4, 7, 'right')]:
    ax.plot([pt], [s4.loc[pt]], 'o', ms=6, color=INK, mec='white', mew=1.5, zorder=4)
    ax.annotate(f'{s4.loc[pt]:.1f}', xy=(pt, s4.loc[pt]), xytext=(dx, dy),
                textcoords='offset points', fontsize=8.5, color=INK, fontweight='bold', ha=ha)
ax.set_ylim(72, 87); ax.yaxis.set_major_locator(MultipleLocator(3))
ax.set_ylabel('per cent of new commitments', fontsize=9, color=INK)
ax.set_xlim(pd.Timestamp('2003-01-01'), pd.Timestamp('2026-09-01'))
ax.grid(axis='y', color='#ececec', lw=0.8, zorder=0); ax.set_axisbelow(True)
for sp in ['top','right']: ax.spines[sp].set_visible(False)
for sp in ['left','bottom']: ax.spines[sp].set_color('#bdbdbd')
ax.tick_params(colors=MUTED, labelsize=8.5, length=3)
ax.set_title('Purchase of existing dwellings as a share of owner-occupier new loan\n'
             'commitments excluding refinancing, four-quarter moving average',
             fontsize=9.5, color=INK, loc='left', pad=10, linespacing=1.4)
fig.tight_layout(); fig.savefig(os.path.join(OUT,'fig1_asset_circuit_share.png'), dpi=220, facecolor='white')
open(os.path.join(OUT,'01_results.txt'),'w').write('\n'.join(log)+'\n')
say("\nwrote output/asset_circuit_series.csv, output/fig1_asset_circuit_share.png")
