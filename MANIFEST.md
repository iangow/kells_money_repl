# Manifest of input files

Every file in `data_raw/` is unmodified as retrieved. SHA-256 truncated to 16 characters.
All nine hashes were re-verified against the files in this package on 26 August 2026 and
are unchanged from the previous package.

| File | Bytes | SHA-256 | Source |
|---|---|---|---|
| `560103.xlsx` | 80,242 | `4448e04c48f59f90` | ABS Lending Indicators cat. 5601.0, Table 3 (Households; Housing finance; Owner occupiers; By detailed purpose; New loan commitments). Retrieved from abs.gov.au, workbook dated 11 May 2026. |
| `bis_fredgraph.csv` | 13,658 | `013da9a297032351` | BIS credit to households, per cent of GDP, adjusted for breaks: QAUHAM770A QATHAM770A QBEHAM770A QCAHAM770A QCHHAM770A QDEHAM770A QDKHAM770A QESHAM770A QFIHAM770A QFRHAM770A QGBHAM770A. Retrieved via FRED, 22 August 2026. |
| `bis_fredgraph1.csv` | 14,843 | `4156a2d0a721796a` | BIS credit to households: QIEHAM770A QITHAM770A QJPHAM770A QKRHAM770A QNLHAM770A QNOHAM770A QNZHAM770A QPTHAM770A QSEHAM770A QUSHAM770A. Retrieved via FRED, 22 August 2026. |
| `bis_fredgraph2.csv` | 13,588 | `de390f4566c1f96e` | BIS credit to non-financial corporations: QAUNAM770A QATNAM770A QBENAM770A QCANAM770A QCHNAM770A QDENAM770A QDKNAM770A QESNAM770A QFINAM770A QFRNAM770A QGBNAM770A. Retrieved via FRED, 22 August 2026. |
| `bis_fredgraph3.csv` | 15,401 | `405938b3786ba699` | BIS credit to non-financial corporations: QIENAM770A QITNAM770A QJPNAM770A QKRNAM770A QNLNAM770A QNONAM770A QNZNAM770A QPTNAM770A QSENAM770A QUSNAM770A. Retrieved via FRED, 22 August 2026. |
| `oecd_cpi_goods_services.csv` | 535,492 | `bd4244d570d9ae60` | OECD consumer prices, dataflow OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL, measure CPI, expenditure GD+SERV+_T, annual, 2015-2025. Retrieved via the OECD SDMX REST API, 22 August 2026. |
| `oecd_house_prices_raw.csv` | 6,354,486 | `28637229cb8962a5` | OECD analytical house price indicators, dataflow OECD.ECO.MPD,DSD_AN_HOUSE_PRICES@DF_HOUSE_PRICES, all reference areas, startPeriod=1970. Retrieved via the OECD SDMX REST API, 22 August 2026. |
| `oecd_household_dashboard.csv` | 2,557,364 | `42ac38d6e38eb9f7` | OECD household dashboard, dataflow OECD.SDD.NAD,DSD_HHDASH@DF_HHDASH_INDIC, all indicators and reference areas, 2015-2024. Retrieved via the OECD SDMX REST API, 22 August 2026. |
| `rba_table_g1.csv` | 39,812 | `ee59242fd824a6a0` | Reserve Bank of Australia, Statistical Table G1 Consumer Price Inflation. Publication date 30 April 2026. |

## Series not re-retrieved here

The Australian credit aggregates (RBA Tables D1, D2, D3), household balance sheet (E1, E2)
and output (H1), and the American series from FRED and the Financial Accounts, are used in
Sections III.A, III.B, III.C and III.E as reported in the author's earlier working papers.
Their identifiers and construction are documented in the paper's Appendix B and in the
replication packages accompanying those papers, and are not duplicated here.

Package assembled 26 August 2026.
