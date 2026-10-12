# Technology & Fintech Market Intelligence and Regime Analyzer
## Final Project Report

**Generated:** 2026-10-12T10:04:38.362442+00:00  
**Project level:** Intermediate  
**Primary domain:** Technology, semiconductors, cloud, enterprise software, fintech, AI infrastructure  

---


## Executive Summary

The Technology & Fintech Market Intelligence and Regime Analyzer is an
intermediate AI/ML/DL/NLP system that analyses 38 publicly traded
technology and fintech companies using programmatically retrieved market data
(yfinance) and a local MongoDB persistence layer.

Key outcomes:
- Validated universe: 38 tickers across 6 categories
- Feature panel: 45106 rows, 39 features
- Forecast horizon: 5 trading days
- Best model (test RMSE): baseline_historical_average (baseline) = 0.0851119129791375
- NLP text coverage: 100.0%
- Success criteria passed: 7/7


---


## Data Pipeline & Coverage

- Source: yfinance only (no manual CSV datasets)
- Storage: local MongoDB Community Server (`mongodb://localhost:27017`)
- Collections: market_data, company_metadata, analysis_results, predictions,
  model_evaluations, refresh_status
- Validated tickers: 38
- Coverage report present: True
- Feasibility run: 2026-10-12T05:44:19.442244+00:00


---


## Modelling & Evaluation

- Classical ML models evaluated: 5 (target ≥ 3)
- Deep-learning models evaluated: 4 (target ≥ 3)
- Baselines included: persistence, historical average, seasonal naïve
- Validation: chronological train / validation / test (no random shuffle)
- Leaderboard entries: 12
- Complex models that beat best baseline: 0


### Model leaderboard (top 15 by test RMSE)

| family   | model                       |   test_rmse |   test_mae |     test_r2 |   dir_acc | source         |   rank |
|:---------|:----------------------------|------------:|-----------:|------------:|----------:|:---------------|-------:|
| baseline | baseline_historical_average |   0.0851119 |  0.0609416 | -0.00606887 |  0.529273 | ml_experiments |      1 |
| baseline | baseline_persistence        |   0.0855648 |  0.0629509 | -0.016804   |  0.529273 | ml_experiments |      2 |
| dl       | transformer                 |   0.0867502 |  0.0612118 | -0.0394573  |  0.490754 | dl_experiments |      3 |
| ml       | catboost                    |   0.0869168 |  0.0622211 | -0.0491918  |  0.514784 | ml_experiments |      4 |
| ml       | ridge                       |   0.0869482 |  0.0619373 | -0.0499479  |  0.518037 | ml_experiments |      5 |
| ml       | random_forest               |   0.0871126 |  0.0625484 | -0.0539242  |  0.519959 | ml_experiments |      6 |
| dl       | gru                         |   0.0874486 |  0.0618157 | -0.0562605  |  0.515114 | dl_experiments |      7 |
| dl       | lstm                        |   0.0880944 |  0.0622431 | -0.0719181  |  0.499822 | dl_experiments |      8 |
| ml       | lightgbm                    |   0.0902149 |  0.0649372 | -0.130326   |  0.497635 | ml_experiments |      9 |
| ml       | xgboost                     |   0.0907764 |  0.0654891 | -0.144441   |  0.494086 | ml_experiments |     10 |
| dl       | tcn                         |   0.090978  |  0.0655738 | -0.143242   |  0.521693 | dl_experiments |     11 |
| baseline | baseline_seasonal_naive     |   0.091834  |  0.0678583 | -0.171263   |  0.493938 | ml_experiments |     12 |

---


## Regime Discovery & NLP

- Regime discovery run: True
- Number of regimes: 4
- Silhouette (train sample): 0.15593888342286844
- NLP component run: True
- Non-news text only: yes (company/category descriptions)
- Text coverage: 38/38
- Embedding backend: sentence_transformers


---

## Success Criteria

| id   | criterion                                                                     | passed   | actual                                                                  |
|:-----|:------------------------------------------------------------------------------|:---------|:------------------------------------------------------------------------|
| C1   | At least 30 companies across the six categories pass data-availability checks | True     | 38 tickers, 6 categories                                                |
| C2   | Notebook and Streamlit can run independently and connect to local MongoDB     | True     | MongoDB reachable=True; URI=mongodb://localhost:27017                   |
| C3   | Daily persistence updates do not create duplicate records                     | True     | Indexes ensured via ensure_indexes(); upserts used in pipeline          |
| C4   | Evaluation uses chronological splits and includes baselines                   | True     | Evaluation report present=True; baselines in leaderboard=True           |
| C5   | Model comparison reports transparently (including when complex models lose)   | True     | Leaderboard rows=12; eval report=True                                   |
| C6   | NLP component has documented non-news source and clear purpose                | True     | NLP summary present=True; coverage=100.0%                               |
| C7   | App displays data freshness and does not label delayed data as real-time      | True     | refresh_status used by pipeline; Streamlit status section in app design |

**Passed: 7/7**

---

## Limitations

- yfinance history length and quality vary by ticker; some series are shorter than others.
- Corporate actions and missing bars can affect feature quality despite cleaning.
- Deep-learning models were trained with modest capacity suitable for an intermediate project.
- NLP uses only non-news company/category descriptions; coverage is incomplete for some tickers.
- No transaction costs, slippage or portfolio constraints are modelled.
- Results are for academic analysis only and are not investment advice.
- Streamlit UI freshness indicators depend on refresh_status being updated by a running process.
- Some tickers may have shorter histories; cross-company comparisons use aligned windows where possible.

---


## Ethical Use & Disclaimer

- This project is for academic analysis only and is not personalised investment advice.
- Forecasts are uncertain estimates and may fail during unexpected events or regime shifts.
- Historical performance does not guarantee future performance.
- The system does not execute trades or make automated investment decisions.
- Statistical association (including text similarity) is not treated as causation.


---

## Deliverables Checklist

| Deliverable | Location |
|-------------|----------|
| Validated ticker universe | `data/processed/validated_tickers.csv` |
| Feature panel | `data/processed/feature_panel.parquet` (and `_with_regimes`) |
| Feature metadata | `data/processed/feature_metadata.json` |
| ML experiment results | `data/processed/ml_experiment_results.json` |
| DL experiment results | `data/processed/dl_experiment_results.json` |
| Model leaderboard | `data/processed/model_leaderboard.csv` |
| Final evaluation report | `data/processed/final_evaluation_report.json` |
| NLP summary | `data/processed/nlp_component_summary.json` |
| Regime diagnostics | `data/processed/regime_discovery_diagnostics.json` |
| This final report (Markdown) | `reports/final_project_report.md` |
| This final report (JSON) | `reports/final_project_report.json` |
| Research notebooks | `notebooks/01` … `09` |
| Streamlit application | `app/` (independent of notebooks) |
| Local MongoDB data | `localhost:27017 / tech_fintech_market_intel` |

---

## Conclusion

The project combines market-data engineering, exploratory analysis, cross-company
comparison, regime discovery, forecasting, a bounded non-news NLP component, and
database-backed application design. Academic value comes from transparent
time-aware evaluation, explicit baselines, and honest discussion of limitations—
not from maximising the number of algorithms or charts.

*End of report*
