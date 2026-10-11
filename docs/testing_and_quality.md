# Testing and Quality Assurance

## 1. Purpose

This document defines the testing strategy and quality assurance standards for **BeneathTheMarket**, an AI-powered market intelligence platform focused on cross-company behaviour, historical risk, predictive trends, and market regimes.

The objective is to ensure that the system produces reliable analytical outputs, processes market data consistently, persists records correctly, and operates independently across its two primary execution environments:

- **Research Notebook:** Supports exploratory data analysis, feature engineering, model experimentation, and evaluation.
- **Streamlit Application:** Provides interactive access to market analysis, cross-company comparisons, forecasting, risk assessment, and other implemented capabilities.

Both components are intended to use the same local MongoDB database and compatible data schemas without requiring one component to run before the other.

This document describes the intended quality standards. Tests should be marked as passing only after they have been implemented and executed successfully.

---

## 2. Quality Objectives

Testing should address the following objectives.

| Quality area | Objective |
|---|---|
| Data integrity | Ensure market observations are valid, consistent, and traceable |
| Data pipeline | Verify acquisition, validation, transformation, and persistence |
| Database reliability | Prevent unintended duplicates and incorrect updates |
| Component independence | Ensure the notebook and application can run separately |
| Analytical correctness | Validate calculations, transformations, and derived features |
| Model reliability | Evaluate predictive performance using appropriate chronological splits |
| Leakage prevention | Prevent future information from influencing historical predictions |
| Reproducibility | Record the data, configuration, and parameters behind experimental results |
| Error handling | Handle missing data, failed requests, and database interruptions safely |
| Maintainability | Keep shared logic testable, modular, and consistent |

---

## 3. Testing Strategy

The project should use a layered testing strategy rather than relying exclusively on manual application checks.

### 3.1 Unit testing

Unit tests verify individual functions or modules in isolation.

Examples include:

- Validating ticker symbols and date ranges.
- Normalising market-data column names and data types.
- Handling missing or invalid numeric values.
- Calculating returns and volatility features.
- Applying data validation rules.
- Constructing database query filters.
- Preparing features for model training.
- Generating forecasts with the expected output shape.
- Calculating evaluation statistics.
- Formatting analytical results for display.

Unit tests should use small, controlled input samples so that expected outputs can be calculated and checked directly.

External network requests and live MongoDB connections should generally be replaced with mocks or controlled test doubles in unit tests.

### 3.2 Integration testing

Integration tests verify that multiple components work together correctly.

Examples include:

- Retrieving sample market data and passing it through the validation pipeline.
- Persisting validated observations into a test database.
- Reading the persisted observations back and verifying their structure.
- Updating an existing observation without creating an unintended duplicate.
- Saving and retrieving model-evaluation records.
- Confirming that the notebook and application use compatible field names and database configuration.
- Verifying refresh-status records after successful and failed retrieval attempts.

Integration tests should use an isolated test database or disposable test collections. They must not modify production or personal research data.

### 3.3 End-to-end testing

End-to-end tests validate a complete workflow from input to output.

A representative workflow is:

1. Request market observations for a supported ticker.
2. Validate and standardise the returned data.
3. Persist the observations in local MongoDB.
4. Retrieve the observations through the application's data-access layer.
5. Generate an analytical result or forecast using the implemented workflow.
6. Confirm that the output has the expected structure and provenance.
7. Verify that the application handles unavailable data or failed dependencies appropriately.

End-to-end tests should use controlled data wherever possible. Live-provider tests should be separated from deterministic tests because external responses can change.

### 3.4 Manual testing

Manual testing complements automated checks, particularly for interactive behaviour.

It should cover:

- Application startup and navigation.
- Filters and ticker selection.
- Date-range selection.
- Cross-company comparisons.
- Visual handling of missing or incomplete data.
- Forecast and risk-analysis output presentation.
- Database connection failure messages.
- Display of data freshness and refresh status, where implemented.
- Notebook execution from a clean kernel.

Manual testing does not replace automated validation of calculations, data integrity, or model evaluation.

---

## 4. Test Environment and Configuration

Tests should run in a dedicated environment with dependencies compatible with the main project.

The testing configuration should distinguish between:

- Unit tests using controlled inputs and mocks.
- Integration tests using an isolated local MongoDB test database.
- End-to-end tests using controlled data and test configurations.
- Optional live-data checks against `yfinance`.

### 4.1 Environment separation

Use separate configuration values for development and testing where necessary.

For example, a test database may use a name such as:

```text
beneath_the_market_test
```

This is an illustrative name; the actual database name should match the project's configuration.

Tests must never silently fall back to a personal development database when a test database is expected.

### 4.2 Testing safeguards

Before any database-writing test begins:

1. Confirm that the test configuration is loaded.
2. Verify that the configured database is the intended test database.
3. Use controlled test records with identifiable keys.
4. Clean up only the records or collections created by that test.
5. Ensure that destructive operations cannot target an unintended database.

A test that cannot verify its target database should fail safely instead of continuing with uncertain configuration.

---

## 5. Market Data Quality Tests

The quality of downstream analysis depends on the quality and consistency of the source observations.

### 5.1 Structural validation

Verify that retrieved data contains the fields required by the selected analytical workflow.

Depending on the source response and selected interval, these may include:

- Ticker symbol.
- Observation date or timestamp.
- Open price.
- High price.
- Low price.
- Close price.
- Adjusted close price, if available and required.
- Trading volume, if available and required.
- Retrieval timestamp.

Not every field is guaranteed to be available in every response. Validation should distinguish required fields from optional fields and reject only the conditions defined by the relevant workflow.

### 5.2 Value validation

The pipeline should check that:

- Required dates are valid and consistently represented.
- Price values are numeric and finite.
- Prices used in calculations satisfy appropriate domain rules.
- High and low values are consistent with the relevant price fields when the source provides those fields.
- Volume values are valid for the selected data representation.
- Duplicate observations are detected.
- Missing values are handled according to documented rules.
- Empty responses are not mistaken for valid datasets.
- Unexpected column names or data structures are handled explicitly.

Do not replace missing observations with arbitrary values simply to make a model execute.

### 5.3 Temporal validation

Market observations must be ordered consistently before time-dependent analysis.

Tests should verify that:

- Observation timestamps can be parsed.
- Records are sorted chronologically before sequence-based calculations.
- Duplicate timestamps are handled according to the selected interval.
- Date ranges respect the requested boundaries.
- Market observation timestamps are distinct from retrieval timestamps.
- Rolling calculations use the intended historical window.
- Any timezone conversion follows one documented convention.

### 5.4 Feature validation

Derived features should be tested independently against known input values.

Potential features include returns, rolling volatility, moving averages, drawdowns, and other implemented indicators.

For each feature:

1. Define the formula and input fields.
2. Establish the expected output for a small sample.
3. Test normal values and boundary conditions.
4. Verify how missing values are treated.
5. Confirm that the feature does not accidentally incorporate future observations.

Features should be computed consistently across the notebook and application.

---

## 6. MongoDB Integrity and Persistence Tests

MongoDB testing should verify the integrity of the shared data contract.

### 6.1 Connection tests

Confirm that the application can:

- Connect to the configured local MongoDB instance.
- Access the intended database.
- Detect connection failures.
- Report missing configuration clearly.
- Close resources appropriately where required.

The project is intended to use a **local MongoDB Community Server**, not MongoDB Atlas.

### 6.2 CRUD and upsert tests

Test the database operations used by the project:

- Insert a valid market observation.
- Read an observation using its defined key.
- Update an existing observation where updates are permitted.
- Upsert an observation without creating an unintended duplicate.
- Persist and retrieve analysis or prediction records.
- Record refresh status for successful and failed operations.
- Handle malformed records without corrupting valid stored data.

### 6.3 Uniqueness and idempotency

Repeated processing of the same input should not produce duplicate logical observations.

For daily market data, the proposed logical uniqueness key is the ticker and observation date. If the implementation supports multiple intervals, exchanges, or observation granularities, the key must include the fields necessary to distinguish separate records.

Tests should confirm that:

- The relevant unique index exists when required.
- Reprocessing an observation produces the expected result.
- Updates do not create duplicate records.
- Index-creation failures are surfaced appropriately.
- Database writes are consistent with the documented data dictionary.

Refer to [`data_dictionary.md`](data_dictionary.md) for the proposed collection contracts.

---

## 7. Notebook Quality Tests

The research notebook should be validated as an independent execution environment.

### 7.1 Execution integrity

Verify that:

- The notebook opens in the supported Jupyter environment.
- It does not depend on variables created by a previous interactive session.
- Cells execute in their documented order from a clean kernel.
- Required imports and configuration are explicit.
- Database access uses the shared project configuration.
- Errors from missing data or unavailable services are handled clearly.

### 7.2 Analytical integrity

Verify that:

- Exploratory summaries match the input data.
- Missing-value analysis reflects the actual dataset.
- Data types and date ranges are reported correctly.
- Feature calculations match their documented definitions.
- Training and evaluation subsets are separated correctly.
- Experimental outputs are labelled with the relevant configuration and period.

### 7.3 Reproducibility

Where possible, record:

- Input tickers and date ranges.
- Data retrieval or snapshot timestamps.
- Feature definitions.
- Model configuration.
- Random seeds for stochastic algorithms.
- Training, validation, and test periods.
- Dependency versions.
- Evaluation results.

Live data may change between runs. Exact numerical equality should therefore only be expected when the underlying inputs and relevant execution conditions are controlled.

---

## 8. Streamlit Application Quality Tests

The Streamlit application should be tested independently of notebook execution.

### 8.1 Startup and navigation

Verify that:

- The application starts using its documented entry point.
- All implemented pages or tabs load without unexpected exceptions.
- Navigation does not depend on execution state from the notebook.
- Missing configuration is reported clearly.
- The application can be stopped and restarted without corrupting stored records.

### 8.2 Input validation

Test representative input conditions:

- Valid and invalid ticker selections.
- Start dates later than end dates.
- Date ranges outside available data.
- Empty query results.
- Missing or unavailable company metadata.
- Invalid numerical parameters.
- Requests that produce insufficient historical observations.

The application should reject invalid inputs or provide a clear explanation rather than generating misleading output.

### 8.3 Visual and analytical consistency

Where the same analytical calculation appears in both the notebook and application, verify that both use equivalent definitions and input windows.

Check that:

- Labels and units are correct.
- Missing values are displayed clearly.
- Chart axes correspond to the displayed variables.
- Forecast horizons and dates are identified.
- Historical observations and future estimates are distinguishable.
- Risk summaries explain the period and calculation used.
- Cached outputs, if used, are invalidated or refreshed according to the documented policy.

A visually correct chart does not establish that the underlying calculation is correct; calculation-level tests are also required.

---

## 9. Machine-Learning and Deep-Learning Evaluation Quality

Predictive modelling must be evaluated using a method appropriate to time-dependent financial data.

### 9.1 Chronological separation

Training, validation, and test observations should be separated chronologically.

The test period must not influence model selection, hyperparameter tuning, feature selection, or preprocessing decisions.

Tests should verify that:

- Training dates precede validation dates.
- Validation dates precede test dates.
- Feature windows use only information available at the prediction timestamp.
- Future target values are not included in input features.
- Scaling, imputation, feature selection, and other fitted transformations use training data only.
- Overlapping windows are handled correctly for the selected prediction task.

Randomly shuffling time-series observations into training and test sets is generally inappropriate when it permits future observations to inform historical predictions.

### 9.2 Baseline comparisons

Every forecasting workflow should be compared against a suitable baseline.

Depending on the target, a baseline might use the latest observed value, a historical average, or another simple reference method.

Tests should ensure that:

- Baseline predictions use the same evaluation dates as the candidate models.
- Models are compared on the same target definition and forecast horizon.
- Evaluation samples are aligned before calculating metrics.
- Model selection is not based on training performance alone.

### 9.3 Metric correctness

Implement and test the selected evaluation metrics independently using small examples with known expected results.

Metric selection should match the target and intended use. Forecasting metrics, classification metrics, and risk-analysis measures are not interchangeable.

Tests should also cover undefined or misleading cases, such as zero denominators, missing predictions, constant targets, or too few observations.

### 9.4 Deep-learning-specific checks

For deep-learning experiments, additionally verify that:

- Sequence construction respects chronological order.
- Input and target shapes are consistent.
- Normalisation is fitted using training data only.
- Model checkpoints are associated with their configuration.
- Validation data is used appropriately for model selection.
- Test data is not repeatedly reused to tune the model.
- Training failures and non-finite losses are detected.

### 9.5 Prediction records

Where predictions are persisted, verify that each record identifies the relevant ticker, generation time, forecast horizon, model or experiment version, and other fields required by the implemented schema.

Predictions should not be presented as guaranteed future outcomes. Evaluation results describe observed performance on specific historical periods and do not establish future profitability.

Refer to [`evaluation_protocol.md`](evaluation_protocol.md) for the proposed model-validation and reporting methodology.

---

## 10. Risk and Market-Regime Analysis Tests

Risk and regime calculations require explicit definitions and consistent input periods.

### Risk analysis

Test implemented measures such as volatility, drawdown, or other risk indicators against known samples.

Verify that:

- The observation window is correct.
- Return definitions are consistent.
- Missing observations are treated appropriately.
- Units and annualisation assumptions are documented where applicable.
- Results remain consistent when calculations are repeated on identical inputs.

### Market-regime analysis

For any implemented regime-identification workflow, test that:

- Required input features are available.
- Labels or states are produced in the expected format.
- The training and evaluation procedure respects temporal constraints.
- Regime boundaries and dates are aligned correctly.
- Missing or insufficient observations are handled explicitly.
- Any interpretation of a regime is supported by the implemented method.

A detected regime should not be described as a guaranteed prediction of future market behaviour.

---

## 11. NLP Quality Tests

NLP functionality is conditional on an appropriate, documented non-news text source being available. No news dataset or news-based sentiment pipeline is assumed by this project.

If NLP functionality is implemented, test:

- Text-source provenance and permitted usage.
- Missing, empty, and malformed text handling.
- Text normalisation and tokenisation.
- Consistent preprocessing between training and inference.
- Label quality for supervised tasks.
- Duplicate and near-duplicate text handling.
- Temporal availability of text used in historical analysis.
- Evaluation using task-appropriate measures.
- Clear communication of source coverage and limitations.

Text must not be used to explain historical market movements if the text was unavailable at the relevant time, unless the analysis explicitly treats it as retrospective rather than predictive.

If no suitable text source is verified, NLP functionality should remain out of scope rather than relying on fabricated or unsupported data.

Refer to [`nlp_source_notes.md`](nlp_source_notes.md) for source-selection and methodology considerations.

---

## 12. External Data and Failure Handling

The `yfinance` data source depends on external availability and may return incomplete, delayed, or changed results.

Testing should cover:

- Network timeouts.
- Provider errors.
- Empty responses.
- Invalid ticker symbols.
- Partial historical coverage.
- Repeated retrieval attempts.
- MongoDB disconnections during persistence.
- Interrupted refresh operations.
- Unavailable or stale cached data.

The pipeline should preserve valid previously stored observations when a refresh fails, unless a documented correction procedure requires a different action.

Refresh records should distinguish at least the attempt outcome from the time of the latest valid market observation, where those fields are implemented.

Do not write tests that assume a scheduled retrieval always produces a new observation. Market hours, holidays, provider limitations, and process availability can affect the result.

---

## 13. Performance and Resource Checks

Performance testing should focus on practical requirements for an intermediate-level academic project.

Measure or inspect:

- Time taken to retrieve and validate a representative data range.
- Database query performance for common ticker and date filters.
- Notebook execution time for core analytical workflows.
- Model training and inference duration.
- Streamlit page-load responsiveness for typical workloads.
- Memory use when processing multiple companies.
- Behaviour when historical data grows.

Use representative test sizes rather than arbitrarily large datasets. Add database indexes based on actual query patterns and validate their usefulness with representative queries.

Performance expectations should be documented only after measurements have been taken on a specified environment.

---

## 14. Logging and Error Reporting

The system should provide enough diagnostic information to investigate failures without exposing sensitive configuration.

Useful log events include:

- Data retrieval started and completed.
- Number of observations received and accepted.
- Validation failures and skipped records.
- Database connection and write outcomes.
- Refresh attempt status.
- Model training and evaluation completion.
- Application-level errors.

Logs should include appropriate timestamps and contextual identifiers, such as a ticker or execution identifier, when useful.

Avoid logging credentials, private connection strings, or unnecessarily large raw data payloads. Errors should be actionable, but they should not be silently suppressed.

---

## 15. Suggested Test Organisation

The following is a proposed organisation, not a claim about the current repository structure:

```text
tests/
├── conftest.py
├── unit/
│   ├── test_data_validation.py
│   ├── test_feature_engineering.py
│   ├── test_metrics.py
│   └── test_input_validation.py
├── integration/
│   ├── test_mongodb_repository.py
│   ├── test_data_pipeline.py
│   └── test_shared_schema.py
└── smoke/
    ├── test_notebook_execution.py
    └── test_application_startup.py
```

The exact files should reflect the modules and entry points that are actually implemented. Avoid adding placeholder tests that do not execute meaningful assertions.

### Suggested test tools

Depending on the final dependency set, suitable tools may include:

- **pytest** for automated tests.
- **unittest.mock** for isolating external dependencies.
- A disposable local MongoDB test database for integration checks.
- Notebook execution tooling for validating notebook cells.
- Streamlit's testing utilities for supported application interaction tests.

Select tools based on the implemented architecture and keep the testing setup manageable.

---

## 16. Example Test Commands

If the project uses `pytest`, the following commands are typical.

Run the complete automated test suite:

```bash
python -m pytest
```

Run only unit tests:

```bash
python -m pytest tests/unit/
```

Run integration tests:

```bash
python -m pytest tests/integration/
```

Run smoke tests:

```bash
python -m pytest tests/smoke/
```

These commands assume that the proposed directories exist and contain executable tests. Update the paths to match the actual repository.

A test run should report the number of passed, failed, and skipped tests. Skipped tests should have a documented reason, particularly when they depend on external services.

---

## 17. Quality Gates

Before accepting a substantial change, use the following quality gates.

### Required checks

- [ ] Relevant unit tests pass.
- [ ] Data validation tests pass.
- [ ] MongoDB writes preserve the documented data contract.
- [ ] No unintended duplicate observations are introduced.
- [ ] The notebook executes independently with a clean kernel.
- [ ] The Streamlit application starts independently.
- [ ] Shared database configuration remains consistent.
- [ ] Chronological evaluation and leakage-prevention checks pass.
- [ ] Missing data and external-service failures are handled clearly.
- [ ] Documentation reflects implemented behaviour.

### Recommended checks

- [ ] Integration tests pass against an isolated local test database.
- [ ] Representative end-to-end workflows pass.
- [ ] Dependencies install in a clean virtual environment.
- [ ] Key calculations are tested against known expected outputs.
- [ ] Model results are reproducible from recorded inputs and settings where feasible.
- [ ] Performance has been checked on representative workloads.
- [ ] Logs provide useful diagnostic information without exposing secrets.

A check should not be marked complete solely because the relevant code exists. Completion requires an appropriate test or documented verification.

---

## 18. Test Results and Reporting

Record test results in a consistent format. For significant modelling or pipeline changes, a report should identify:

- Date and environment of execution.
- Code revision or version identifier.
- Tests executed.
- Passed, failed, and skipped test counts.
- Known failures and limitations.
- Data source and observation period where relevant.
- Model evaluation period and configuration, if applicable.
- Follow-up actions.

Do not include fabricated test results, performance measurements, or model scores in project documentation. Numerical claims should be based on actual execution records.

---

## 19. Limitations

The following limitations should be acknowledged:

1. External market-data responses can change over time.
2. A passing test suite cannot guarantee future predictive performance.
3. Historical model performance may not generalise to unseen market conditions.
4. Integration tests depend on the availability and configuration of local MongoDB.
5. Live-provider tests may be less deterministic than tests using controlled data.
6. NLP validation depends on the existence and quality of an approved non-news text source.
7. A successful application startup does not prove that every analytical result is correct.

These limitations should inform how results are interpreted and how the system is demonstrated.

---

## 20. Related Documentation

- [`README.md`](../README.md) — Project overview and primary usage instructions.
- [`architecture.md`](architecture.md) — System components and interactions.
- [`setup_and_configuration.md`](setup_and_configuration.md) — Environment, dependencies, and local MongoDB setup.
- [`data_dictionary.md`](data_dictionary.md) — Database schemas and validation rules.
- [`data_pipeline.md`](data_pipeline.md) — Data acquisition, processing, and persistence.
- [`evaluation_protocol.md`](evaluation_protocol.md) — Model validation and evaluation methodology.
- [`nlp_source_notes.md`](nlp_source_notes.md) — Non-news text-source considerations for potential NLP functionality.

---

## 21. Completion Criteria

Testing and quality assurance are considered adequately established when the project has meaningful automated checks for its core data transformations, database operations, and analytical calculations; the notebook and application run independently; predictive evaluation follows a documented chronological protocol; and failures are handled without silently producing misleading results.

