# Data Pipeline

**Document:** `docs/data_pipeline.md`  
**Project:** BeneathTheMarket  
**Purpose:** Document the acquisition, validation, transformation, storage, and consumption of market data.  
**Data provider:** `yfinance`  
**Database:** Local MongoDB Community Server  
**Database driver:** PyMongo  
**Status:** Proposed pipeline design — update this document to reflect the implemented behaviour.

---

## 1. Purpose

BeneathTheMarket uses historical and refreshed market data to investigate cross-company behaviour, historical risk, predictive trends, and market regimes.

This document describes the intended data pipeline, from retrieving market observations to making validated data available to analytical processes, forecasting models, the Jupyter Notebook, and the Streamlit application.

The pipeline is designed to:

- Retrieve market data for the configured company universe.
- Validate and standardise incoming observations.
- Prevent duplicate market records.
- Store market data in local MongoDB.
- Support reproducible feature engineering and model evaluation.
- Make shared data available to the notebook and application independently.
- Track refresh attempts and data-quality issues.

The pipeline does not use news data. Any NLP functionality must rely on a separately documented, approved non-news text source, as described in `docs/nlp_source_notes.md`.

## 2. Pipeline Overview

The intended flow is:

```text
Configured Company Universe
            |
            v
      yfinance Retrieval
            |
            v
      Source Response
            |
            v
   Validation and Cleaning
            |
            v
  Standardisation and Mapping
            |
            v
 Local MongoDB Upsert Operations
            |
            v
     Shared Market Data
            |
       +----+----+
       |         |
       v         v
Jupyter Notebook  Streamlit Application
       |         |
       v         v
Exploration,      Interactive Analysis,
Feature Building, Forecasting and
Experiments       Visualisation
       |         |
       +----+----+
            |
            v
 Persisted Results and Refresh Records
```

This diagram represents the intended logical flow. The actual module boundaries and persistence operations must match the implemented code.

## 3. Data Source and Company Universe

### 3.1 Market-data retrieval

Use the Python `yfinance` library to request historical market observations for the configured ticker universe.

Depending on source availability and retrieval configuration, the pipeline may obtain:

- Open price.
- High price.
- Low price.
- Close price.
- Adjusted close, when available.
- Trading volume.
- Dividend or stock-split information, when returned.

The pipeline must inspect the actual response rather than assume every field exists for every ticker.

### 3.2 Company universe

Maintain the selected company universe in a central configuration or a controlled company-metadata source.

Each company entry should identify its canonical ticker and, where supported, its display name and project-defined category.

The company universe should be consistent across:

- Market-data retrieval.
- Historical analysis.
- Forecast generation.
- Cross-company comparison.
- Application filters.
- Model evaluation.

Do not duplicate different ticker lists across unrelated modules.

### 3.3 Source limitations

`yfinance` is a third-party interface to market information, not a guarantee of uninterrupted or complete data availability.

The pipeline must tolerate missing observations, unavailable tickers, source errors, and variations in returned fields. Retrieval failures should be recorded rather than silently treated as valid empty market histories.

## 4. Data Acquisition

### 4.1 Retrieval procedure

For each scheduled or manually triggered retrieval:

1. Load the configured company universe.
2. Determine the requested date range and interval.
3. Request data from `yfinance`.
4. Validate the response structure.
5. Identify the ticker associated with each observation.
6. Standardise column names and data types.
7. Record retrieval metadata.
8. Pass validated records to the persistence layer.
9. Record the outcome of the retrieval attempt.

Use a consistent retrieval configuration for comparable companies and experiments. If different intervals or adjustment settings are used, record them so the resulting records remain interpretable.

### 4.2 Historical and incremental retrieval

Historical retrieval supplies the observations needed for exploratory analysis and model training. Incremental retrieval attempts to obtain more recent observations.

Where supported by the source, request only the required range rather than repeatedly processing unnecessary historical data.

However, recent observations can be corrected or revised by the provider. The pipeline should therefore permit existing records to be updated when the same ticker/date observation is retrieved again.

### 4.3 Retrieval failures

A failure for one ticker should not automatically prevent all other tickers from being processed.

Where practical:

- Handle failures at the ticker or retrieval-batch level.
- Record the affected tickers.
- Preserve previously stored valid records.
- Avoid replacing valid stored data with an empty or malformed response.
- Allow a later refresh to retry failed retrievals.

The refresh record should distinguish complete success, partial success, and failure if these outcomes are implemented.

## 5. Validation and Cleaning

Incoming data must pass validation before being written to the canonical market-data collection.

### 5.1 Structural validation

Check that:

- The ticker is present and belongs to the configured universe.
- The observation date is valid.
- Required market fields have the expected structure.
- Column names map correctly to the storage schema.
- Numeric fields can be converted safely.
- Duplicate ticker/date observations are handled consistently.

### 5.2 Numeric validation

Where values are available:

- Ensure prices are numeric and finite.
- Ensure volume is a non-negative integer when present.
- Inspect high–low and open–close consistency.
- Identify invalid values and document their treatment.
- Preserve missing values as missing rather than converting them to zero.

Do not automatically discard a record merely because an optional field is absent. Apply validation according to the field's documented requirements in `docs/data_dictionary.md`.

### 5.3 Date and time handling

Maintain a distinction between:

- **Observation date:** The trading date represented by a market record.
- **Retrieval timestamp:** When the pipeline obtained the record.
- **Processing timestamp:** When the record was validated or transformed, if tracked.

Use a consistent date representation and timestamp convention throughout the application.

Do not treat a trading date as a retrieval timestamp, and do not assume that a newly retrieved value corresponds to a completed trading session.

### 5.4 Data-quality outcomes

Each batch should have a clear outcome:

- Valid records accepted for persistence.
- Invalid records rejected or quarantined according to the implemented policy.
- Missing or unavailable observations identified.
- Retrieval or validation errors recorded.

Record counts should follow a consistent convention so that refresh summaries are meaningful.

## 6. Standardisation and Transformation

Before persistence, map source responses into the canonical market-data schema.

### 6.1 Standardisation

Standardisation includes:

- Normalising ticker representation.
- Mapping source column names to project field names.
- Converting values to the selected numeric types.
- Standardising dates and timestamps.
- Adding source provenance.
- Removing duplicate observations within the incoming batch.

The source-specific mapping should be isolated from downstream analysis so that changes in the returned response do not require rewriting every analytical component.

### 6.2 Feature engineering

Feature engineering should occur in a distinct processing layer, after the underlying market observations have been validated.

Potential derived features include:

- Daily or multi-period returns.
- Rolling volatility.
- Moving averages.
- Momentum-related variables.
- Drawdown statistics.
- Volume-based measures.
- Cross-company relative-performance features.

Only calculate features supported by the available data and the project's implemented scope.

For every feature, document its formula, lookback period, required inputs, and availability at the prediction origin.

### 6.3 Feature leakage prevention

A feature used for a forecast must be computable using information available at that forecast origin.

The pipeline must not:

- Use future observations in historical rolling calculations.
- Calculate preprocessing parameters using the complete dataset before a chronological split.
- Include a target-derived value that would not have been available at prediction time.
- Use text that became available later as though it had been available historically.

Training, validation, and test procedures are defined in `docs/evaluation_protocol.md`.

## 7. Local MongoDB Persistence

### 7.1 Database connection

Use a local MongoDB Community Server instance accessed through PyMongo. The project does not require MongoDB Atlas.

The connection URI, database name, and other environment-specific settings should be defined centrally and configurable through environment variables or the project's configuration mechanism.

Do not hard-code connection settings separately in the notebook and application.

### 7.2 Collections

The proposed persistence layer uses these collections:

| Collection | Responsibility |
|---|---|
| `market_data` | Canonical market observations |
| `company_metadata` | Company identifiers and categories |
| `analysis_results` | Persisted analytical outputs |
| `predictions` | Forecast outputs and their input context |
| `model_evaluations` | Experiment configurations and evaluation results |
| `refresh_status` | Refresh attempts and their outcomes |

Refer to `docs/data_dictionary.md` for field definitions, required status, and validation rules.

### 7.3 Upsert strategy

Use an idempotent write strategy for market observations.

The recommended unique key is:

`(ticker, observation_date)`

An upsert should insert a new observation when the key does not exist and update the existing observation when the same key is retrieved again.

This strategy helps prevent duplicate daily records when refreshes overlap or are repeated.

If the implementation stores multiple intervals or observation types, extend the unique key accordingly.

### 7.4 Write integrity

- Validate documents before writing.
- Use bulk writes where appropriate for efficiency.
- Handle individual write failures without concealing them.
- Maintain unique indexes required by the data contract.
- Avoid deleting valid historical records merely because a refresh failed.
- Keep analytical outputs distinguishable from raw or standardised market observations.

### 7.5 Shared database contract

The notebook and Streamlit application must use the same database conventions and collection schemas.

Neither component should depend on the other being open or running. Both should be able to connect to local MongoDB and execute their own supported workflows.

## 8. Refresh Strategy

### 8.1 Intended refresh behaviour

The project intends to attempt market-data refreshes hourly while the relevant scheduler or application process is running and able to reach the data source.

A separate persistence policy should ensure that stored observations are updated through validated upserts. Where the project uses daily persistence or reconciliation, that policy must be implemented explicitly rather than assumed to follow automatically from hourly retrieval.

Retrieval frequency and database-write frequency are separate design decisions and should be configured independently.

### 8.2 Important scheduling limitation

An in-process hourly scheduler does not continue running when its host process is stopped.

Therefore:

- The scheduler must be active for scheduled attempts to occur.
- The host must have access to local MongoDB and the data source.
- Missed intervals should be handled according to the implemented retry or catch-up policy.
- The application must not claim that data are continuously refreshed when no refresh process is running.

If reliable background refresh is required independently of the Streamlit session, use a separately managed local scheduler or background process.

### 8.3 Market hours and observation freshness

An hourly retrieval attempt does not guarantee a new market observation every hour.

Markets have trading calendars, closures, holidays, and periods without new completed daily observations. The source may also return unchanged data.

The application should distinguish:

- Last successful retrieval time.
- Latest stored observation date.
- Latest available observation for a selected ticker.
- Most recent refresh outcome.

Do not interpret a successful retrieval as proof that every ticker's data have advanced.

### 8.4 Retries and overlapping jobs

Where implemented, retries should be bounded and should not create duplicate records.

Prevent simultaneous refresh jobs from conflicting through an appropriate locking, scheduling, or single-worker strategy. If overlapping attempts are allowed, the persistence design must remain idempotent.

Record retry outcomes and avoid repeated requests that could unnecessarily burden the source.

## 9. Data Consumption

### 9.1 Jupyter Notebook

The notebook should connect directly to local MongoDB and retrieve the data required for its research workflow.

Its responsibilities may include:

- Exploratory data analysis.
- Data-quality inspection.
- Historical trend and cross-company analysis.
- Feature engineering.
- Model development and evaluation.
- Visualisation and interpretation.
- Recording selected experiment results.

The notebook must not require the Streamlit application to run.

### 9.2 Streamlit application

The application should independently connect to local MongoDB and use the shared data contract.

Its responsibilities may include:

- Market overview.
- Cross-company comparisons.
- Risk analysis.
- Market-regime analysis.
- Forecast generation and inspection.
- Model-performance comparison.
- Data freshness and refresh status.

The application must not rely on variables, in-memory DataFrames, or runtime state created by the notebook.

### 9.3 Shared services

Both components should reuse consistent database access, schema validation, and feature definitions where the repository design permits.

Shared code should not introduce a runtime dependency between the notebook and Streamlit. Each should be able to run independently using the common configuration and database layer.

## 10. Error Handling and Observability

The pipeline should make failures diagnosable without exposing credentials or other sensitive configuration.

### 10.1 Errors to track

Examples include:

- Source retrieval failures.
- Missing or malformed source fields.
- Invalid dates or numeric values.
- MongoDB connection failures.
- Write or index errors.
- Partial ticker coverage.
- Feature-generation failures.
- Scheduler failures.

### 10.2 Refresh records

The proposed `refresh_status` collection should identify each refresh attempt and record its status.

Where implemented, record:

- Job identifier.
- Source.
- Tickers included.
- Start and completion timestamps.
- Outcome.
- Inserted, updated, and processed record counts.
- Concise error summary, when applicable.

The exact field contract is defined in `docs/data_dictionary.md`.

### 10.3 Logging

Logs should provide enough context to diagnose failures, including the relevant ticker or job identifier and the processing stage.

Do not log secrets, credentials, or unnecessary sensitive information.

Avoid treating a warning as a successful completion unless the pipeline's outcome rules explicitly allow partial success.

## 11. Pipeline Testing

The pipeline should be tested before it is relied upon by the notebook or application.

### Source and transformation tests

- Verify source-column mapping.
- Test missing optional fields.
- Test invalid dates and numeric values.
- Test duplicate observations within a batch.
- Test handling of empty or malformed responses.
- Verify feature calculations against known examples.

### MongoDB tests

- Confirm that valid records can be inserted.
- Verify that repeated upserts do not create duplicate ticker/date observations.
- Check that invalid records are rejected according to the defined policy.
- Test connection failure handling.
- Verify that both components can read the expected collections.

### Scheduling and refresh tests

- Verify the configured refresh interval.
- Confirm that a failed ticker does not silently invalidate successful tickers.
- Test retry behaviour where implemented.
- Verify that stopped processes do not falsely report ongoing refresh.
- Check that refresh records accurately reflect outcomes.

### Independent execution tests

- Run the notebook without launching Streamlit.
- Run Streamlit without executing the notebook first.
- Verify that each component reads the shared MongoDB schema correctly.
- Confirm that neither component relies on uncommitted in-memory state from the other.

Detailed testing procedures belong in `docs/testing_and_quality.md`.

## 12. Security and Configuration

- Keep environment-specific configuration outside committed source code.
- Use environment variables or an appropriate local configuration file for the MongoDB URI.
- Do not commit credentials, private connection strings, or secrets.
- Validate external data before persistence.
- Handle source and database errors without exposing sensitive information.
- Document required local services and dependencies in `README.md`.

The local MongoDB deployment should be configured appropriately for the development environment. Do not assume that a local service is automatically protected merely because it is not hosted in the cloud.

## 13. Known Limitations

The pipeline is subject to the following limitations:

- `yfinance` availability and response structure may change.
- Some tickers or fields may be unavailable for particular periods.
- Retrieval schedules do not guarantee new market observations.
- A stopped scheduler cannot execute refresh jobs.
- Local MongoDB availability depends on the local service and machine.
- Historical observations may be corrected by the source.
- Data quality affects all downstream analysis and predictions.
- The pipeline does not independently establish the accuracy or profitability of predictive models.

These limitations should be reflected in data-status displays and project documentation where relevant.

## 14. Implementation Checklist

- [ ] The company universe is configured centrally.
- [ ] Retrieval settings are consistent and configurable.
- [ ] Source responses are validated before persistence.
- [ ] Dates, numeric values, and source provenance are standardised.
- [ ] Duplicate observations are removed or handled safely.
- [ ] A unique ticker/date index is enforced for daily market data.
- [ ] Upserts preserve valid historical records.
- [ ] Feature calculations prevent future-data leakage.
- [ ] Hourly scheduling is implemented with its runtime limitations documented.
- [ ] Refresh outcomes are recorded accurately.
- [ ] The notebook connects to MongoDB independently.
- [ ] The Streamlit application connects to MongoDB independently.
- [ ] Both components use the same schema and database conventions.
- [ ] Pipeline tests cover invalid data, database failures, and repeated refreshes.
- [ ] Documentation matches the implemented behaviour.

---

## 15. Related Documentation

- `docs/architecture.md` — system components and overall data flow.
- `docs/data_dictionary.md` — MongoDB collection schemas and field definitions.
- `docs/evaluation_protocol.md` — model evaluation and chronological validation.
- `docs/nlp_source_notes.md` — approved non-news text sources and NLP limitations.
- `docs/testing_and_quality.md` — test strategy and quality checks.
- `docs/setup_and_configuration.md` — local setup and configuration.
- `README.md` — project overview, prerequisites, and execution instructions.

**Maintenance note:** This document describes the intended pipeline. Update it when the retrieval process, refresh schedule, storage contract, validation rules, or downstream data flow changes. Do not describe proposed behaviour as implemented until it has been verified in the codebase.