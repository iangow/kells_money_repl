# Replication package

**The composition of money creation has large but underappreciated impacts on
inflation, asset prices, the distribution of wealth and the effectiveness of
monetary policy**

Package assembled 26 August 2026.

This package reproduces every result the paper estimates from raw inputs:

* Figure 1 and the asset-circuit statistics of Section III.A;
* Table 3, Figure 2 and the panel robustness of Section III.D;
* the traded and non-traded inflation rates quoted in Section III.C, re-derived
  directly from Reserve Bank of Australia Table G1.

It also carries one result the paper does **not** report — a nineteen-country
pandemic-channel cross-section, which returns a null (script 04, and see below).

The Australian structural-break and monetary-aggregate results of Sections III.A
and III.C, the American series behind Table 2 and Section III.B, the New Zealand
and American flow-versus-stock results of Section III.D, and the wealth
decompositions of Section III.E are computed from the published series named in
the paper's Appendix B. Their construction is documented there and they are not
re-estimated here.

## Running it

Install `uv` if needed:

    curl -LsSf https://astral.sh/uv/install.sh | sh

Then install the project dependencies and run the replication package:

    uv sync
    uv run code/run_all.py

Runtime is about a minute, most of it the wild cluster bootstrap. Everything is
written to `output/`. All inputs are in `data_raw/` — no network access is required.

## Contents

    code/01_asset_circuit.py         Figure 1; Section III.A asset-circuit statistics
    code/02_credit_prices_rents.py   Table 3; Figure 2; Section III.D robustness
    code/03_verify_g1.py             Section III.C inflation rates, from RBA Table G1
    code/04_pandemic_channel.py      Cross-country pandemic channel test (a null; not in the paper)
    code/05_check_against_paper.py   Compares every reproduced figure with the paper's
    code/run_all.py                  Driver
    data_raw/                        Inputs, unmodified as retrieved (see MANIFEST.md)
    output/                          Generated figures, series and result logs

## Verification

`code/05_check_against_paper.py` is the quickest way to audit the package. It reads
the other scripts' outputs, compares each reproduced number with the value quoted in
the draft, and prints a PASS/FAIL table with the tolerance used. On the current draft it
runs 28 checks and all 28 pass. It exits non-zero if any check fails, so the package
can be re-run against a revised draft and any mismatch read straight off.

## Method notes

**Asset circuit (01).** The asset circuit is the purchase of existing dwellings; the
goods circuit is construction plus purchase of newly erected dwellings. The two sum
to the published total excluding refinancing to within 0.05 per cent, and the script
prints that identity check. Refinancing is excluded from both — it involves no bid
for any dwelling. "Purchase of residential land" is ambiguous between the circuits,
is published only from 2019Q3, and is excluded from both. Series are Original (not
seasonally adjusted) and in dollars. Section III.A's sample mean is the unsmoothed
quarterly series; the low and the end-of-sample reading are the four-quarter moving
average plotted in Figure 1, as the text states. Script 01 prints both series.

**Panel (02).** Observations are taken at the fourth quarter of each year. The
regressor is the annual change in household credit as a share of household plus
non-financial-corporate credit, both adjusted for breaks and measured against GDP.
All specifications carry country and year fixed effects, so identification is off
within-country deviations from a common annual shock. Standard errors are clustered
on country. Because 21 clusters is few enough for cluster-robust inference to
over-reject, headline p-values come from a wild cluster bootstrap — 999 Rademacher
replications imposing the null (Cameron, Gelbach and Miller 2008), seeded at 7.
Bootstrap p-values move in the third decimal place across seeds; the coefficients
and cluster-robust standard errors do not.

**What the panel result is.** A conditional correlation within countries, not a
causal estimate. Credit composition is not exogenous and the fixed effects do not
make it so. What it establishes is that the association has the shape the credit
account predicts and not the shape a contemporaneous supply-constraint account
predicts. As Appendix A.9 of the paper notes, it does not exclude a forward-looking
supply explanation.

**Pandemic channel (04), and why it is here.** This test is not reported in the paper
and nothing in the paper depends on it. It is retained because it was run, it bears on
Proposition 2, and a null is worth preserving. The channel measure is the 2020 gap
between real household disposable income per capita growth and real GDP per capita
growth — the national-accounts trace of money credited into household accounts in a
year when output fell. The dependent variable is mean goods-minus-services consumer
inflation over 2021–23. Nineteen countries have both; the binding constraint is
household disposable income, not the price data. Standard errors are HC3. The script
reports the null across controls, subsamples, functional form and four inflation
windows, and prints the minimum detectable effect at 80 per cent power, so the null
can be distinguished from low power. The cross-country limb of Proposition 2 is
rejected on this test. The within-country evidence of Section III.B is untouched by
it, because the dependent variable lies entirely inside the goods circuit.
