# MoSPI MCP Validation — February 13, 2026

## Connection
- URL used: https://mcp.mospi.gov.in
- Connection time: MISSING (not in JSON outputs)
- Any auth required? No

## Dataset: CPI
- Step 1 time: 1.84s
- Step 2 time: 0.61s — indicators found: base_year (2010/2012/2024), level (Group/Item), series (Current/Back)
- Step 3 time: 1.35s — filters available: series, year, state, sector, month, division, group, class, sub_class, item, imputation
- Step 4 time: 0.60s — data format: list of rows with CPI index values (e.g., base_year/series/year/month/state/sector/division/index) plus pagination metadata
- Usable for our claims:
  - "Inflation is out of control": Yes (time series CPI/inflation can test magnitude and trend)
  - "Food prices have doubled": Yes (food division/group/item over time)
  - "Rural India has it worse than cities": Yes (rural vs urban sector comparison)
  - "Petrol prices drive everything up": No (CPI can show fuel price trends, but not causality)

## Dataset: PLFS
- Step 1 time: 0.74s
- Step 2 time: 1.88s — indicators found: LFPR, WPR, UR, worker distribution, employment conditions (regular wage), earnings (regular/casual/self), etc. (annual set 1–8)
- Step 3 time: 0.88s — filters available: year, age, education, gender, religion, sector, social_category, state, weekly_status (plus codes for industry/status/contract/enterprise/nic/nco/quarter)
- Step 4 time: 1.90s — data format: rows with year, frequency, indicator, state, gender, sector, age group, weekly status, religion, social group, education, quarter/month, value, unit
- Usable for our claims:
  - "Nobody's hiring anymore": Yes (employment/unemployment rates and worker population ratio as proxy)
  - "Youth unemployment is a crisis": Yes (age_code 15–29)
  - "Women are leaving the workforce": Yes (gender-based LFPR/WPR)
  - "Government jobs are the only stable option": No (PLFS doesn’t explicitly isolate government vs private stability)
  - "Educated people are more unemployed than uneducated": Yes (education_code)

## Dataset: NAS
- Step 1 time: 0.75s
- Step 2 time: 0.56s — indicators found: GVA, net taxes on products, taxes/subsidies, GDP, etc. with series (Current/Back) and frequency (Annual/Quarterly)
- Step 3 time: 0.47s — filters available: year, approach (expenditure/production), revision, industry, subindustry, institutional_sector (codes)
- Step 4 time: 0.43s — data format: No Data Found for chosen filter combination (needs different filters)
- Usable for our claims (using NAS + IIP + ASI):
  - "GDP numbers are fake": No (can check trends/consistency, not falsity)
  - "Manufacturing is dead in India": Yes (ASI/IIP manufacturing + NAS industry GVA)
  - "Only services sector is growing": Yes (NAS industry breakdown; compare sectors)
  - "India's economy is slowing down": Yes (NAS GDP/GVA time series)

## Go/No-Go Decision
- [ ] Reliable (works 3/3 times)
- [ ] Fast enough (< 3s per step)
- [ ] Data is usable (can verify claims)
- [ ] DECISION: GO / NO-GO
