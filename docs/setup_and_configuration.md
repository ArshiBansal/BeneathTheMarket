# Setup and Configuration

## 1. Purpose

This document describes the environment setup and configuration requirements for **BeneathTheMarket**, an AI-powered market intelligence platform designed to investigate cross-company behaviour, historical risk, predictive trends, and market regimes.

It covers the development environment, Python dependencies, local MongoDB configuration, application settings, data access, and execution procedures for the project's two independent components:

- **Research Notebook:** Used for exploratory data analysis, feature engineering, experimentation, model training, and evaluation.
- **Streamlit Application:** Used for interactive market analysis, cross-company comparisons, forecasting, risk assessment, and other implemented analytical capabilities.

Both components are intended to operate independently while accessing the same local MongoDB instance and compatible data schemas.

> **Implementation note:** This document defines the intended setup and configuration approach. Commands, environment variables, dependency versions, database names, and entry-point paths must be aligned with the final implementation before being treated as verified project requirements.

---

## 2. Prerequisites

Install the following software before configuring the project.

| Requirement | Purpose |
|---|---|
| Python | Application development, data processing, and modelling |
| pip | Python package installation |
| Git | Repository version control |
| MongoDB Community Server | Local database storage |
| MongoDB Shell (`mongosh`) | Optional database connectivity and inspection |
| Jupyter Notebook or JupyterLab | Research and experimentation |
| Streamlit | Interactive application interface |
| Internet connection | Retrieving market data through `yfinance` |

Use a Python version supported by the selected versions of all project dependencies. Record the chosen Python version in the repository documentation after compatibility has been verified.

MongoDB should run locally. **MongoDB Atlas is not part of the intended deployment configuration.**

---

## 3. Project Setup

### 3.1 Obtain the project

If the project is hosted on GitHub, clone the repository and enter its directory:

```bash
git clone <repository-url>
cd BeneathTheMarket
```

Replace `<repository-url>` with the actual repository URL.

If the repository is already available locally, open its root directory in the terminal or development environment.

### 3.2 Create a virtual environment

A dedicated virtual environment helps isolate project dependencies from other Python projects.

**Windows — Command Prompt or PowerShell:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS or Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

After activation, confirm the interpreter:

```bash
python --version
```

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

The `.venv/` directory should be excluded from version control.

### 3.3 Install dependencies

Install the dependencies listed in the project's `requirements.txt` file:

```bash
python -m pip install -r requirements.txt
```

The dependency list should include only packages required by the implemented project. Depending on the final design, these may include:

- `yfinance` for retrieving market data.
- `pandas` and `numpy` for data processing.
- `pymongo` for MongoDB connectivity.
- `streamlit` for the interactive application.
- `jupyter` or `notebook` for research workflows.
- Selected machine-learning and deep-learning libraries.
- Visualisation libraries used by the implemented analytical views.
- Configuration, validation, and testing libraries where required.

Do not assume every possible library is required. The final dependency file should reflect the models and functionality actually implemented.

---

## 4. Local MongoDB Configuration

### 4.1 Install and start MongoDB

Install MongoDB Community Server using the official documentation for the target operating system.

Official installation documentation:

https://www.mongodb.com/docs/manual/installation/

Start the MongoDB service using the method appropriate to the operating system. On systems where MongoDB is installed as a service, it may start automatically.

The usual local connection URI is:

```text
mongodb://localhost:27017/
```

The URI assumes MongoDB is listening on the default local port. If the server uses another host or port, update the configuration accordingly.

### 4.2 Verify the connection

If `mongosh` is installed, connect to the local server:

```bash
mongosh "mongodb://localhost:27017/"
```

A successful connection indicates that the shell can reach the configured MongoDB server. It does not, by itself, verify that the project's Python application can connect or that its collections and indexes are configured correctly.

### 4.3 Database and collection configuration

The project is expected to use a dedicated local database. The final database name should be defined centrally rather than repeated throughout the codebase.

The proposed logical collections are:

| Collection | Intended purpose |
|---|---|
| `market_data` | Retrieved and standardised historical market observations |
| `company_metadata` | Company and ticker reference information |
| `analysis_results` | Persisted analytical outputs, where appropriate |
| `predictions` | Forecasts and their associated metadata |
| `model_evaluations` | Model evaluation results and experiment details |
| `refresh_status` | Data retrieval and refresh execution records |

These names describe the proposed data contract. Create collections and indexes through the project's database initialisation logic where appropriate, rather than relying on manually created collections.

Refer to [`data_dictionary.md`](data_dictionary.md) for the proposed collection schemas and field definitions.

### 4.4 Data persistence principles

The database layer should follow these principles:

1. Use a consistent schema across the research notebook and Streamlit application.
2. Standardise ticker symbols, observation dates, timestamps, and numeric field types.
3. Use an appropriate unique key to prevent duplicate market observations.
4. Prefer idempotent writes, such as upserts, where the selected schema supports them.
5. Keep retrieval timestamps distinct from market observation timestamps.
6. Store model outputs with enough metadata to identify the input period, model version, forecast horizon, and generation time, where applicable.
7. Handle database connection failures explicitly rather than silently treating missing data as valid results.

For market observations, a proposed uniqueness constraint is the combination of ticker and observation date. The exact key must account for the chosen market interval and data granularity.

---

## 5. Environment Variables

Configuration values should be kept separate from application logic. A local `.env` file may be used if the project adopts an environment-variable loader.

Create a local `.env` file from the repository's `.env.example` template, if one is provided.

Example configuration:

```dotenv
# Local MongoDB connection
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=beneath_the_market

# Application configuration
APP_ENV=development
LOG_LEVEL=INFO

# Data retrieval configuration
DATA_REFRESH_INTERVAL_HOURS=1
```

These are **illustrative proposed variable names and defaults**, not a guarantee that the current implementation reads them. Use the exact names defined by the project's configuration module.

### Configuration descriptions

| Variable | Intended purpose |
|---|---|
| `MONGODB_URI` | Local MongoDB connection string |
| `MONGODB_DATABASE` | Database name used by the application |
| `APP_ENV` | Identifies the current execution environment |
| `LOG_LEVEL` | Controls logging verbosity |
| `DATA_REFRESH_INTERVAL_HOURS` | Configures the intended retrieval-attempt interval |

If a variable is not implemented, do not add it merely to make the configuration appear complete.

### Security and repository hygiene

- Commit `.env.example` with non-sensitive example values.
- Do not commit `.env` or credentials.
- Add `.env` to `.gitignore`.
- Do not hard-code passwords, tokens, or private connection strings.
- Keep development and any future deployment configurations separate.
- Avoid exposing sensitive configuration values in logs or exception messages.

The standard local MongoDB URI shown above is suitable only when the server is configured to accept that connection. If authentication is enabled, configure credentials securely.

---

## 6. Market Data Configuration

### 6.1 Data source

The project uses the Python `yfinance` library to retrieve market data. It does not rely on a manually downloaded or bundled stock-price dataset as its primary source.

The data acquisition layer should centralise:

- The supported ticker universe.
- The requested historical period.
- The requested interval.
- The retrieval-attempt schedule.
- Validation and normalisation rules.
- Persistence and duplicate-handling behaviour.

These settings should be configurable where they are expected to change during development.

### 6.2 Ticker universe

Maintain the supported company and ticker mapping in one configuration location or reference collection.

Each entry should use a valid market ticker and, where applicable, include a company name and sector or analytical category.

Do not assume that every company has complete data for every requested period. Ticker availability, exchange coverage, market holidays, listing history, and provider limitations may affect the observations returned.

Private firms without publicly available market tickers should not be treated as ordinary entries in a public-equity price analysis.

### 6.3 Refresh behaviour

The intended design distinguishes between **retrieval frequency** and **database persistence policy**.

- Retrieval attempts may be scheduled hourly while the relevant process or scheduler is running.
- Stored observations may be refreshed or updated according to the implemented daily persistence policy.
- Historical observations should be checked for duplicates and updated only according to defined correction and upsert rules.
- A failed retrieval should be recorded and should not automatically erase valid previously stored observations.
- The system should record the time of the retrieval attempt and the latest market observation returned.

An hourly schedule does not guarantee that new market prices will be available every hour. Markets have trading hours and holidays, and data-provider availability can vary. A scheduled task also cannot execute while its hosting process or machine is stopped.

Refer to [`data_pipeline.md`](data_pipeline.md) for the intended acquisition, validation, persistence, and refresh workflow.

---

## 7. Running the Research Notebook

The research notebook must be usable independently of the Streamlit application.

Start Jupyter from the activated virtual environment:

```bash
jupyter notebook
```

Alternatively, use JupyterLab if it is installed:

```bash
jupyter lab
```

Open the project's implemented research notebook and execute its cells in the documented order.

### Notebook responsibilities

The notebook is intended to support:

- Data availability and quality checks.
- Exploratory data analysis.
- Cross-company comparisons.
- Feature engineering and preparation.
- Machine-learning and deep-learning experiments.
- Chronological validation and testing.
- Forecast and risk-analysis evaluation.
- Recording and interpreting experimental results.

Where MongoDB integration is implemented, the notebook should read from and write to the same configured local database used by the application.

It should not require Streamlit to be running. Notebook outputs should not be treated as reproducible model results unless the input data, date range, parameters, dependencies, and random seeds—where applicable—are recorded adequately.

---

## 8. Running the Streamlit Application

The Streamlit application must be runnable without executing the research notebook first.

Use the actual entry-point path in the implemented repository. For example, if the entry point is `app.py`, run:

```bash
streamlit run app.py
```

If the entry point is located elsewhere, substitute its actual path.

The application should load its configuration, connect to local MongoDB, retrieve available stored observations, and present appropriate messages when data or analysis results are unavailable.

### Expected operational behaviour

- The app should not require the notebook's in-memory variables.
- It should use the shared database contract for persisted data.
- It should distinguish missing data from valid zero-valued observations.
- It should indicate when the available observations were last updated, where that information is available.
- It should handle connection and retrieval errors without presenting stale results as freshly updated data.
- It should avoid retraining expensive models on every interaction unless that behaviour is explicitly designed and evaluated.

If the application uses a separate model-training workflow, document how trained artefacts are persisted and loaded. Do not assume that model files exist until that workflow is implemented.

---

## 9. Independent Execution and Shared Resources

The notebook and application are separate entry points, not sequential stages that must both remain open.

| Capability | Research notebook | Streamlit application |
|---|---|---|
| Runs independently | Yes, intended | Yes, intended |
| Uses Python dependencies | Yes | Yes |
| Connects to local MongoDB | If database integration is implemented | If database integration is implemented |
| Reads shared market observations | Intended | Intended |
| Performs analysis | Research and experimentation | Interactive analytical workflows |
| Requires Streamlit to run | No | Not applicable |
| Requires notebook execution first | No | No, provided required data or model artefacts are available |

Both components should use shared configuration and database-access utilities where practical. Shared utility code does not mean that one component must launch or import the other component's entry point.

A clean environment should be able to run each component after the documented dependencies and required services are configured.

---

## 10. Configuration Validation

Before running analytical workflows, verify the following items.

### Environment

- [ ] The supported Python version is installed.
- [ ] The virtual environment is active.
- [ ] Required packages install successfully.
- [ ] The actual configuration variable names match the code.
- [ ] Local configuration files are excluded from version control where appropriate.

### MongoDB

- [ ] MongoDB Community Server is installed and running.
- [ ] The configured URI points to the intended local server.
- [ ] The application can connect to the configured database.
- [ ] Collection schemas and required indexes are initialised or validated.
- [ ] Duplicate observations are handled correctly.
- [ ] Both entry points use compatible database and field conventions.

### Market data

- [ ] `yfinance` can retrieve data for at least one supported ticker.
- [ ] Returned data contains the required fields.
- [ ] Dates, time zones, and numeric values are normalised consistently.
- [ ] Empty responses and retrieval failures are handled.
- [ ] Refresh status records distinguish attempt time from observation time.

### Application and notebook

- [ ] The notebook starts without launching Streamlit.
- [ ] The application starts without requiring notebook execution.
- [ ] Both components can access the shared database.
- [ ] Missing data produces a clear, non-misleading message.
- [ ] Analytical outputs can be traced to their input data and configuration.

---

## 11. Troubleshooting

| Problem | Possible cause | Recommended action |
|---|---|---|
| Python command is not recognised | Python is not installed or is missing from `PATH` | Verify the installation and interpreter command |
| Package installation fails | Unsupported Python version or incompatible dependencies | Check package compatibility and install from the project's dependency file |
| MongoDB connection is refused | MongoDB is stopped or the URI/port is incorrect | Start the local service and verify the connection settings |
| Authentication fails | MongoDB requires credentials | Configure an authorised local connection securely |
| Market data is empty | Invalid ticker, unavailable period, market closure, or provider issue | Check the ticker, interval, requested dates, and retrieval response |
| Stored observations are duplicated | Missing or incorrect uniqueness rules | Review the schema, unique indexes, and upsert logic |
| Notebook cannot find expected data | Incorrect database settings or no data has been persisted | Verify the URI, database, collection, and data availability |
| Streamlit cannot start | Wrong entry-point path or missing dependencies | Confirm the entry-point file and active virtual environment |
| The app shows stale observations | Refresh did not run, failed, or returned no newer data | Inspect refresh status and distinguish the latest attempt from the latest observation |
| Predictions differ between runs | Different data windows, parameters, seeds, or dependency versions | Record experiment configuration and use chronological evaluation consistently |

Troubleshooting messages should avoid exposing credentials or other sensitive configuration values.

---

## 12. Reproducibility and Maintenance

For reliable development and evaluation:

1. Pin or otherwise manage dependency versions consistently.
2. Record the Python and MongoDB versions used during development.
3. Keep configuration values in one documented location.
4. Track data retrieval and processing timestamps.
5. Record modelling parameters, feature definitions, and evaluation periods.
6. Keep the notebook and application aligned with the same data dictionary.
7. Test database connection failures and incomplete market-data responses.
8. Review dependency compatibility before upgrading major packages.
9. Document configuration changes when they affect reproducibility.
10. Never claim that historical observations, model outputs, or refresh status are current without verifying their timestamps.

Market data retrieved from an external provider may change or become unavailable. Re-running the same notebook at a later date may therefore produce different results even when the source code remains unchanged.

---

## 13. Related Documentation

- [`README.md`](../README.md) — Project overview, features, and primary usage instructions.
- [`architecture.md`](architecture.md) — System components, boundaries, and interactions.
- [`data_dictionary.md`](data_dictionary.md) — Proposed MongoDB collections, fields, and validation rules.
- [`data_pipeline.md`](data_pipeline.md) — Data acquisition, processing, persistence, and refresh behaviour.
- [`evaluation_protocol.md`](evaluation_protocol.md) — Model validation and evaluation methodology.
- [`nlp_source_notes.md`](nlp_source_notes.md) — Potential non-news text sources and NLP implementation considerations.

---

## 14. Completion Criteria

The setup and configuration process can be considered complete when:

- The project environment can be recreated from its documented dependencies.
- Local MongoDB connectivity is verified.
- Configuration is centralised and does not require secrets to be committed.
- Market data can be retrieved and validated through the intended pipeline.
- The notebook can run independently of the application.
- The Streamlit application can run independently of the notebook.
- Both components follow the same database contract.
- Configuration errors and unavailable data are handled clearly.
- The actual commands, paths, dependency versions, and configuration keys have been verified against the implemented repository.

