#!/usr/bin/env python3
"""
Checks every number this package reproduces against the value quoted in the paper.

Run after the other scripts. Reads their outputs, compares each figure with the
value printed in the draft, and reports PASS / FAIL with the tolerance used.
Exits non-zero if anything fails, so the package can be run in a checking loop.

Input : output/ (produced by scripts 01-04)
Output: output/05_check.txt
"""
import os, re, sys
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'output')
log = []
def say(x):
    print(x); log.append(str(x))

rows = []
def check(where, what, paper, got, tol):
    ok = got is not None and abs(got - paper) <= tol
    rows.append((where, what, paper, got, tol, ok))

# ---------------------------------------------------------------- 01
ser = pd.read_csv(os.path.join(OUT, 'asset_circuit_series.csv'),
                  parse_dates=['quarter']).set_index('quarter')['asset_circuit_share_pct']
ma4 = ser.rolling(4).mean().dropna()
check('III.A', 'asset-circuit share, sample mean (unsmoothed)', 81.4, ser.mean(), 0.05)
check('III.A', 'sample low, four-quarter MA, 2021Q1',            75.4, ma4.min(), 0.05)
check('III.A', 'end of sample, four-quarter MA, 2026Q1',         84.8, ma4.iloc[-1], 0.05)

r01 = open(os.path.join(OUT, '01_results.txt')).read()
m = re.search(r'2010-13 mean ([\d.]+)\s+vs 2015-18 mean ([\d.]+)\s+t=([+-][\d.]+)', r01)
if m:
    check('III.A', '2010-13 mean',                     80.1, float(m.group(1)), 0.05)
    check('III.A', '2015-18 mean',                     79.9, float(m.group(2)), 0.05)
    check('III.A', 't, 2010-13 vs 2015-18',            0.49, float(m.group(3)), 0.005)
m = re.search(r'2010-13 mean [\d.]+\s+vs 2022-26 mean [\d.]+\s+t=([+-][\d.]+)', r01)
if m:
    check('III.A', 't, 2010-13 vs recent',            -8.5, float(m.group(1)), 0.05)

# ---------------------------------------------------------------- 02
r02 = open(os.path.join(OUT, '02_results.txt')).read()
for label, coef, se, tstat, bp in [
        ('nominal house prices', 0.503, 0.178, 2.84, 0.013),
        ('rents',                0.040, 0.150, 0.27, 0.899),
        ('price-to-rent ratio',  0.463, 0.249, 1.86, 0.091)]:
    m = re.search(re.escape(label) + r'\s+([+-][\d.]+)\s+([\d.]+)\s+([+-][\d.]+)\s+([\d.]+)', r02)
    if m:
        check('III.D / Table 3', label + ', coefficient',   coef, float(m.group(1)), 0.0005)
        check('III.D / Table 3', label + ', cluster SE',    se,   float(m.group(2)), 0.0005)
        check('III.D / Table 3', label + ', t',             tstat,float(m.group(3)), 0.005)
        check('III.D / Table 3', label + ', bootstrap p',   bp,   float(m.group(4)), 0.0005)

for label, paper in [('excl. Australia and New Zealand', 0.417),
                     ('excl. United States',             0.492),
                     ('1990 onwards',                    0.675),
                     ('excl. 2007-2012',                 0.338),
                     ('excl. 2020-2021',                 0.501)]:
    m = re.search(re.escape(label) + r'\s+prices ([+-][\d.]+)', r02)
    if m:
        check('III.D robustness', label, paper, float(m.group(1)), 0.0005)
m = re.search(r'excl\. 2007-2012\s+prices [+-][\d.]+ \(p=([\d.]+)\)', r02)
if m:
    check('III.D robustness', 'excl. 2007-2012, p', 0.085, float(m.group(1)), 0.001)
m = re.search(r'h=1\s+HPI ([+-][\d.]+)', r02)
if m:
    check('III.D', 'local projection, cumulative at h=1', 0.84, float(m.group(1)), 0.005)

# ---------------------------------------------------------------- 03
r03 = open(os.path.join(OUT, '03_results.txt')).read()
m = re.search(r'1997-2017\s+([\d.]+)\s+([\d.]+)', r03)
if m:
    check('III.C', 'traded inflation, 1997-2017',     0.38, float(m.group(1)), 0.005)
    check('III.C', 'non-traded inflation, 1997-2017', 3.26, float(m.group(2)), 0.005)

# ---------------------------------------------------------------- report
say("CHECKS OF REPRODUCED FIGURES AGAINST THE PAPER")
say("=" * 88)
say(f"{'section':18s} {'quantity':44s} {'paper':>8s} {'here':>8s}  ")
say("-" * 88)
fails = 0
for where, what, paper, got, tol, ok in rows:
    if not ok: fails += 1
    g = '  n/a' if got is None else f'{got:8.3f}'
    say(f"{where:18s} {what:44s} {paper:8.3f} {g}  {'PASS' if ok else 'FAIL'}")
say("-" * 88)
say(f"{len(rows)} checks, {len(rows)-fails} passed, {fails} failed.")

say("")
say("NOT CHECKED HERE. The Australian structural-break and monetary-aggregate results")
say("(III.A, III.C), the American series of Table 2 and III.B, the New Zealand and")
say("American flow-versus-stock results (III.D) and the wealth decompositions (III.E)")
say("are computed from the published series named in Appendix B and are not re-estimated")
say("in this package. Appendix B documents their construction.")

open(os.path.join(OUT, '05_check.txt'), 'w').write('\n'.join(log) + '\n')
sys.exit(1 if fails else 0)
