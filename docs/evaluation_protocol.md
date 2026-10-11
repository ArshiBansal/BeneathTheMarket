# Evaluation Protocol — BeneathTheMarket

**Document:** `docs/evaluation_protocol.md`  
**Project:** BeneathTheMarket  
**Purpose:** Define consistent, reproducible procedures for evaluating forecasting models, comparing model performance, and validating analytical outputs.  
**Data source:** `yfinance`  
**Database:** Local MongoDB Community Server  
**Status:** Proposed protocol — final procedures and results must be confirmed against the implemented experiments.

---

## 1. Purpose

BeneathTheMarket evaluates historical market behaviour and develops predictive models across a selected universe of publicly traded companies. This protocol establishes a consistent basis for assessing model performance and determining whether a model provides useful information beyond simple reference methods.

It covers:

- Historical market-data preparation.
- Forecasting experiments and model comparison.
- Machine-learning and deep-learning evaluation.
- Baseline comparisons.
- Risk-analysis validation.
- Market-regime analysis.
- Cross-company robustness.
- Reproducibility and result recording.
- Limitations of market-data-based evaluation.

This document specifies how evaluation should be conducted. It does not claim that any model has already been trained, tested, or shown to outperform another model.

## 2. Evaluation Principles

All experiments should follow these principles:

1. **Chronological integrity:** Future observations must not be used to predict earlier observations.
2. **Fair comparison:** Models being compared must use equivalent data periods, targets, forecast horizons, and evaluation splits.
3. **Baseline-first evaluation:** Complex models must be compared against simple reference methods.
4. **Reproducibility:** Each experiment must record its configuration, input-data cutoff, model version, and evaluation results.
5. **Cross-company validation:** Performance should be assessed across multiple companies rather than relying on one ticker.
6. **Separation of training and testing:** Final test observations must not influence model selection or hyperparameter tuning.
7. **Transparent reporting:** Poor results, failed experiments, and limitations must be recorded rather than omitted.
8. **No unsupported investment claims:** Historical predictive performance does not guarantee future performance or profitability.

## 3. Data and Evaluation Scope

### 3.1 Data source

Market observations are obtained through the `yfinance` library. The source may provide historical prices, volume, and related fields depending on ticker availability and retrieval configuration.

The evaluation pipeline must record the source data and the observation period used for each experiment.

The data source is not guaranteed to be complete, uninterrupted, or suitable for every ticker and time period. Missing observations, corporate actions, ticker changes, and source inconsistencies must be considered during preprocessing.

### 3.2 Company universe

Evaluate the configured company universe across the project's selected technology, fintech, semiconductor, enterprise-software, and other relevant technical categories.

The exact ticker list must be maintained in project configuration or company metadata rather than duplicated in the evaluation protocol.

Report the number of companies successfully evaluated and identify exclusions caused by insufficient or unsuitable data.

### 3.3 Evaluation targets

Each experiment must define its target explicitly. Possible targets include:

- Future closing price.
- Future price return.
- Direction of the future price movement.
- A volatility or risk-related quantity.
- Market-regime classification, where an appropriate definition and validation method have been implemented.

These targets are not interchangeable. Price forecasts, return forecasts, direction classification, volatility estimation, and regime classification require different evaluation procedures.

Only report results for targets that are implemented and supported by the available data.

### 3.4 Forecast horizons

Every forecasting experiment must define its horizon and unit. For example, a five-trading-day horizon is different from five calendar days.

Use the same horizon when comparing models for the same experiment. If multiple horizons are supported, evaluate and report them separately.

---

## 4. Data Preparation

### 4.1 Data validation

Before training or evaluation:

- Validate ticker identifiers and observation dates.
- Check numeric fields for invalid or non-finite values.
- Inspect missing observations and duplicated ticker/date records.
- Check OHLC consistency when all relevant fields are available.
- Confirm that data are ordered chronologically.
- Verify that the selected target can be calculated for the intended forecast horizon.
- Record exclusions and the reasons for them.

Do not automatically interpret missing market observations as zero values.

### 4.2 Feature construction

Features may include price-derived returns, rolling statistics, volatility estimates, volume-related variables, and other features supported by the selected market data.

For each feature, document:

- Its definition.
- Its input fields.
- Its lookback window, where applicable.
- The earliest date at which it can be calculated.
- Whether it is available at the forecast origin.
- Its missing-value handling method.

Every feature used to generate a forecast must be calculable from information available at that forecast origin.

### 4.3 Prevention of look-ahead bias

The following are prohibited:

- Using future closing prices to calculate features for earlier predictions.
- Computing rolling statistics with future observations included.
- Fitting scalers, imputers, or feature selectors on the full dataset before splitting.
- Selecting models or tuning hyperparameters based on the final test period.
- Randomly shuffling time-series observations before splitting them into training and test sets.
- Using labels that would not have been available at the time the forecast was supposed to be generated.

Fit preprocessing transformations on training data only. Apply the fitted transformations to validation and test data without refitting them on those periods.

### 4.4 Adjustments and corporate actions

Document whether the experiment uses adjusted or unadjusted prices. Apply a consistent target and feature convention across all models in a comparison.

Where corporate actions affect the observed price series, investigate whether the resulting discontinuities could distort returns, volatility estimates, or forecast errors.

Do not combine price series with inconsistent adjustment conventions without explicitly addressing the difference.

---

## 5. Chronological Evaluation Design

### 5.1 Time-ordered data splits

Use chronological training, validation, and test periods.

The following proportions may be used as an initial configuration, provided the dataset is long enough:

| Partition | Suggested proportion | Purpose |
|---|---:|---|
| Training | 70% | Fit model parameters. |
| Validation | 15% | Select model configurations and tune hyperparameters. |
| Test | 15% | Final, held-out evaluation. |

These proportions are guidelines, not mandatory universal values. Choose boundaries by date and adjust them when data length, forecast horizon, or the model's lookback requirements make the initial split unsuitable.

All models in a comparison should use the same date boundaries whenever their data requirements permit.

### 5.2 Rolling-origin evaluation

Where computationally feasible, supplement the fixed split with rolling-origin evaluation:

1. Train using observations available up to a defined cutoff.
2. Generate predictions for a subsequent period.
3. Move the cutoff forward.
4. Retrain or update the model according to the experiment design.
5. Repeat across multiple chronological windows.
6. Aggregate results across the evaluation windows.

This approach helps assess whether performance is dependent on one particular market period.

The retraining frequency, window length, and prediction frequency must be documented.

### 5.3 Overlapping forecast horizons

When multi-step forecasts overlap, their errors may be statistically dependent. Document how overlapping predictions are generated and aggregated.

Do not treat all forecast errors as independent observations when drawing conclusions about model reliability.

### 5.4 Final test-set protection

The final test set must remain separate from model selection. If test results are used to make design decisions, the test set is no longer an untouched final evaluation period.

Record any such reuse and establish a new held-out period if a genuinely independent evaluation is needed.

---

## 6. Forecasting Model Comparison

### 6.1 Model groups

The project intends to compare more than three machine-learning approaches and more than three deep-learning approaches, subject to implementation feasibility and data suitability.

Organise implemented models into documented groups, such as:

- Machine-learning forecasting models.
- Deep-learning forecasting models.
- Simple reference or baseline methods.

The actual model inventory, configurations, and implementation status should be recorded in the experiment configuration or results, rather than assumed by this protocol.

### 6.2 Baseline methods

Every forecasting task should include an appropriate simple baseline. Depending on the target, possible baselines include:

- Last-observation forecast.
- Historical mean or another clearly defined reference forecast.
- A simple direction or class-frequency reference for classification tasks.

Select baselines that are meaningful for the task. A baseline for future returns may not be suitable for a price-level forecast.

### 6.3 Fair comparison requirements

Models being compared for the same task must share:

- Target definition and units.
- Forecast horizon.
- Training, validation, and test periods.
- Available information at the forecast origin.
- Evaluation observations.
- Metric definitions.
- Missing-value and exclusion policies.

Where a model requires a longer lookback window, document the resulting difference in usable observations. Avoid comparing scores calculated on different test observations without explaining the difference.

### 6.4 Hyperparameter selection

Use the training and validation data for model development. Hyperparameter selection must not use the final test results.

Record the search configuration and chosen parameters. Use a fixed random seed where supported, and record software or hardware constraints that may affect reproducibility.

### 6.5 Forecast evaluation metrics

Choose metrics appropriate to the target and report their units.

| Metric | Main purpose | Interpretation |
|---|---|---|
| Mean Absolute Error (MAE) | Measure average absolute prediction error. | Lower is better. |
| Root Mean Squared Error (RMSE) | Penalise larger errors more strongly. | Lower is better. |
| Mean Absolute Percentage Error (MAPE) | Express error relative to actual values. | Lower is better, but problematic when actual values are zero or near zero. |
| Directional accuracy | Measure the proportion of correctly predicted movement directions. | Higher is better, subject to a clearly defined direction rule. |

Use only metrics suitable for the chosen target. MAPE is not appropriate for targets that can be zero or near zero, and it may be misleading for returns that can be negative. Do not use percentage error as the sole metric.

For return prediction, consider MAE, RMSE, and directional accuracy where applicable. For price-level prediction, report the units of the price and consider whether price differences across companies make pooled errors difficult to interpret.

Do not rank models using metrics calculated on incompatible targets or scales.

### 6.6 Aggregation across companies

Report results at two levels:

1. **Per-company results:** Performance for each ticker.
2. **Cross-company summary:** A documented aggregate across the evaluated companies.

State how the aggregate is calculated. For example, the mean of per-company MAE values gives each company equal weight, whereas pooling all prediction errors may give companies with more observations greater influence.

Report the number of companies and observations represented by each summary. Where appropriate, report variability across companies or evaluation windows alongside the average.

---

## 7. Deep-Learning Evaluation

Deep-learning models must follow the same chronological and leakage-prevention rules as machine-learning models.

Additional requirements include:

- Fit input scaling using training data only.
- Construct sequences so that every input window ends no later than its forecast origin.
- Ensure that training labels do not cross into prohibited evaluation periods.
- Apply the same forecast target and horizon used in the corresponding comparison.
- Record the input lookback length, forecast horizon, training configuration, and model version.
- Use validation data for early stopping or model selection, if those techniques are implemented.
- Record the random seed and training settings where supported.
- Compare against suitable baselines and simpler models.

Deep-learning models should not be considered superior merely because they are more complex. Their additional computational cost and sensitivity to training configuration should be considered alongside predictive performance.

---

## 8. Risk-Analysis Evaluation

Risk-analysis features must be evaluated according to what they claim to measure. A descriptive risk statistic is not automatically a prediction of future risk.

### 8.1 Historical risk statistics

For descriptive outputs such as realised volatility, drawdown, or other historical risk summaries:

- Define the calculation and lookback period.
- Verify the implementation against a small manually checked example or an independent calculation.
- Ensure that the reported period matches the selected analysis window.
- Distinguish historical observations from estimates of future conditions.
- Use consistent return and price-adjustment conventions.

### 8.2 Predictive risk estimates

If the project predicts a future risk quantity, compare the prediction against a clearly defined realised outcome over the corresponding future horizon.

Use error measures appropriate to the target and ensure the realised outcome is not used as an input to the earlier prediction.

### 8.3 Cross-company risk comparisons

When comparing companies:

- Use consistent calculation windows.
- State whether the comparison uses absolute values, percentage returns, or another common basis.
- Avoid directly comparing raw price levels as if they represented equivalent risk.
- Identify companies with insufficient data.
- Explain any normalisation used for visual comparison.

Risk outputs must be described as analytical estimates, not guarantees of future safety or returns.

---

## 9. Market-Regime Evaluation

Market-regime analysis is intended to identify patterns or periods with differing market characteristics. Its evaluation depends on whether the implemented method is descriptive, unsupervised, or supervised.

### 9.1 Descriptive or unsupervised regimes

If regimes are inferred without externally labelled ground truth:

- Document the features used to identify regimes.
- Record the fitting period and model configuration.
- Check whether the resulting groups are distinguishable using relevant characteristics.
- Examine whether assignments are stable across time windows or reasonable configuration changes.
- Check whether the model has been fitted using future information that would not have been available at the time of a historical assignment.

Without a suitable ground-truth label, do not report ordinary classification accuracy as though the inferred regimes had known correct labels.

### 9.2 Supervised regime classification

If verified labels are available and a supervised classifier is implemented:

- Define the source and meaning of each label.
- Use chronological training, validation, and test periods.
- Report an appropriate classification metric set.
- Include a confusion matrix where informative.
- Account for class imbalance when interpreting performance.
- Inspect whether the label-generation procedure introduces look-ahead bias.

### 9.3 Interpretation

Regime labels are model outputs and may not correspond to universally agreed market states. Avoid interpreting a regime as a guaranteed forecast of future market behaviour.

---

## 10. NLP Evaluation

NLP is only within the evaluation scope when the project actually implements a text-based feature and documents the text source.

The project excludes news data. Therefore, NLP experiments must not depend on news articles, news feeds, or news-derived sentiment unless the project scope is explicitly changed and approved.

Potential non-news text sources must be documented in `docs/nlp_source_notes.md`, including provenance, collection method, date or version where available, and permitted use.

### 10.1 NLP task definition

For every implemented NLP task, specify:

- The intended task and output.
- The text source and provenance.
- The preprocessing procedure.
- Whether labels exist and how they were obtained.
- The dataset or text records used for training and evaluation.
- The evaluation method and its limitations.

Do not introduce synthetic or unverified labels and present them as ground truth.

### 10.2 Evaluation requirements

For a labelled classification task, use appropriate classification metrics and inspect class imbalance. For an unlabelled exploratory task, use evidence suitable for the specific task and avoid claiming supervised predictive accuracy without ground-truth labels.

If the selected text source cannot support a meaningful evaluation, document the limitation rather than forcing an unsupported comparison.

---

## 11. Robustness and Generalisation

A model that performs well for one ticker or one period may not generalise to other companies or market conditions.

Where data availability permits, assess:

- Performance across different companies.
- Performance across distinct chronological windows.
- Differences between company categories.
- Sensitivity to the forecast horizon.
- Sensitivity to feature or lookback choices.
- The effect of missing or limited observations.
- Whether improvements over a baseline persist outside one favourable period.

Report the number of evaluated companies and any exclusions. Avoid claiming broad generalisation when only a small subset of the configured universe has been tested.

Do not change the evaluation design after inspecting results without recording the change.

---

## 12. Experiment Tracking and Reproducibility

Every completed experiment should have a unique identifier and a record of the information required to interpret its results.

At minimum, record:

- Experiment identifier.
- Model name and model family.
- Model version or configuration identifier.
- Target and forecast horizon, where applicable.
- Tickers evaluated.
- Data period and input-data cutoff.
- Training, validation, and test split configuration.
- Feature and preprocessing configuration.
- Evaluation metrics and their values.
- Experiment status.
- Start and completion timestamps, when available.
- Relevant notes about exclusions or limitations.

Persist evaluation records in the proposed `model_evaluations` MongoDB collection when that functionality is implemented. The actual stored field definitions must agree with `docs/data_dictionary.md`.

Record forecast outputs separately in `predictions` when persistent forecast history is required. A stored forecast should identify the model and the input-data cutoff used to generate it.

Use consistent experiment identifiers in logs, saved results, and application views so that a result can be traced to its experiment.

---

## 13. Model Selection Rules

Choose a final model using a documented decision process rather than selecting the model with the most attractive single result.

The selection process should:

1. Confirm that the experiment passed data-quality and leakage checks.
2. Compare models on the same target and evaluation observations.
3. Review the relevant primary metric and supporting metrics.
4. Compare results against the selected baseline.
5. Examine performance across companies and chronological windows.
6. Consider model complexity, computational requirements, and reproducibility.
7. Document trade-offs and limitations.

The primary metric must be chosen before the final test results are used for model selection. If several metrics conflict, explain the trade-off rather than presenting a single unexplained ranking.

A model should not be described as the best-performing model unless the evidence supports that conclusion for the stated target, period, and evaluation setup.

---

## 14. Reporting Requirements

A model comparison report should include:

- Experiment identifier and date.
- Model name and model family.
- Target and forecast horizon.
- Data period and number of evaluated observations.
- Number of companies included.
- Chronological split configuration.
- Baseline performance.
- Evaluation metrics with units and direction of preference.
- Per-company results and cross-company summaries, where applicable.
- Failed experiments and material exclusions.
- Known limitations and reproducibility notes.

For risk and regime analysis, describe what was evaluated and whether the output is historical, descriptive, or predictive.

Charts should identify the target, evaluation period, and units. Forecast plots should distinguish actual observations from predictions. Do not display forecasts as observed market data.

---

## 15. Limitations

The evaluation results are subject to several limitations:

- Historical market behaviour may not continue in the future.
- `yfinance` data availability and returned fields may vary.
- Corporate actions and changes in ticker coverage can affect historical series.
- Results may depend on the chosen company universe, observation period, and forecast horizon.
- Financial time series may contain noise, changing distributions, and abrupt structural changes.
- Good statistical forecast performance does not establish that a trading strategy would be profitable after transaction costs, slippage, taxes, and execution constraints.
- Regime outputs may depend on the features and configuration used.
- NLP results depend on the quality and suitability of the non-news text source, where NLP is implemented.

Unless a separate trading simulation is implemented with a defensible methodology, model-evaluation results must not be presented as evidence of investment profitability.

---

## 16. Completion Checklist

- [ ] Each implemented target has an explicit definition.
- [ ] Data preparation and feature construction are documented.
- [ ] Training, validation, and test data are separated chronologically.
- [ ] Preprocessing is fitted using training data only.
- [ ] Forecast horizons and units are consistent within each comparison.
- [ ] Suitable baseline methods are evaluated.
- [ ] Metrics match the target and are reported with their units.
- [ ] Machine-learning and deep-learning comparisons use fair evaluation conditions.
- [ ] Cross-company and chronological robustness are assessed where feasible.
- [ ] Risk and regime outputs are evaluated according to their actual purpose.
- [ ] Any NLP experiment uses a documented non-news text source.
- [ ] Experiment configurations and results are recorded reproducibly.
- [ ] The final test set has not been used improperly for model selection.
- [ ] Limitations and failed experiments are reported.
- [ ] Stored evaluation records match `docs/data_dictionary.md`.

---

## 17. Related Documentation

- `docs/architecture.md` — system components and data flow.
- `docs/data_dictionary.md` — MongoDB collection definitions and stored fields.
- `docs/nlp_source_notes.md` — non-news text provenance and NLP data limitations.
- `README.md` — setup, dependencies, local MongoDB configuration, and execution instructions.

**Maintenance note:** Update this protocol whenever the project's targets, feature definitions, evaluation splits, metric choices, or experiment procedures change. Report measured results separately from the proposed methodology.