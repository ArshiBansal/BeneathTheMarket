# NLP Source Notes

**Document:** `docs/nlp_source_notes.md`  
**Project:** BeneathTheMarket  
**Purpose:** Document the sources, provenance, suitability, and limitations of textual data considered for Natural Language Processing (NLP).  
**Market data source:** `yfinance`  
**Database:** Local MongoDB Community Server  
**Status:** Source assessment and implementation guidance

---

## 1. Purpose

BeneathTheMarket primarily analyses historical market data to investigate cross-company behaviour, risk, predictive trends, and market regimes.

This document establishes the conditions under which NLP may be included in the project. It records the distinction between structured numerical market data and textual information, identifies the limitations of the available sources, and prevents unsupported claims about text-based analysis.

The project explicitly excludes news data. Consequently, news headlines, news articles, news feeds, and news-derived sentiment must not be used as inputs unless the project scope is formally changed.

NLP functionality should only be implemented when a suitable non-news text source has been identified, its provenance documented, and its intended analytical purpose justified.

## 2. NLP Scope

NLP may be considered for analysing descriptive text associated with companies, industries, or other relevant entities.

Potential applications include:

- Extracting descriptive terms from company or sector descriptions.
- Comparing textual similarity between companies.
- Identifying recurring themes in company descriptions.
- Exploring relationships between text-derived characteristics and numerical market features.

These are potential applications, not claims that the corresponding functionality is already implemented.

The following are outside the current scope:

- News-based sentiment analysis.
- News headline classification.
- News-driven price prediction.
- Claims that company descriptions reveal real-time investor sentiment.
- Text-based predictions without a documented source, target, and evaluation procedure.

## 3. Textual Data Source Assessment

### 3.1 `yfinance` company information

The `yfinance` library is the project's primary interface for obtaining market information. Depending on the ticker and the current library response, company information may include descriptive fields such as a business summary or industry information.

| Attribute | Assessment |
|---|---|
| Potential source | Company information returned through `yfinance` |
| Data type | Descriptive text and associated metadata, where available |
| News data | Excluded |
| Availability | May vary by ticker, source response, and library behaviour |
| Provenance | Record the provider, retrieval time, and source field |
| Potential NLP use | Descriptive text comparison, keyword extraction, or exploratory theme analysis |
| Limitation | Text may be missing, outdated, inconsistent, or unavailable for some companies |

**Implementation requirement:** Inspect the actual responses for the configured ticker universe before relying on any descriptive field. Do not assume that every company has a complete or current business description.

The presence of company-description text does not establish that it contains meaningful sentiment or that it can predict future market behaviour.

### 3.2 Other non-news text sources

Additional sources may be considered only if a clear project requirement cannot be met using the existing source and the source can be accessed and used appropriately.

Before adding a source, document:

- Source name and provider.
- Official source location or documentation.
- Text fields collected.
- Collection method and retrieval date.
- Licensing, access restrictions, and applicable usage terms.
- Update frequency and historical availability.
- Missing-data characteristics.
- Whether the source contains news or other excluded material.
- The specific NLP task the source is intended to support.

Do not introduce another source simply to increase the number of NLP techniques or make the project appear more complex.

**Current status:** No additional non-news text source is assumed to be approved by this document. Any proposed source must be assessed before implementation.

## 4. Source Provenance and Metadata

Every text record used for NLP should retain enough information to identify its origin and processing history.

Where applicable, record the following metadata:

| Field | Purpose |
|---|---|
| `ticker` | Company associated with the text, when applicable |
| `source` | Provider from which the text was obtained |
| `source_field` | Original field name or type of textual content |
| `retrieved_at` | Timestamp when the text was retrieved |
| `source_updated_at` | Source-provided update timestamp, if available |
| `language` | Text language, when known or reliably identified |
| `content_hash` | Optional hash used to identify content changes without duplicating the full text |
| `processing_version` | Version of the preprocessing procedure used |
| `schema_version` | Version of the stored record schema |

These are proposed metadata fields. Store only the fields supported by the actual source and implementation.

Do not invent source timestamps when the provider does not supply them. Distinguish the retrieval time from the original publication or update time.

If the text itself must be stored, verify that storage and reuse are permitted under the relevant source terms.

## 5. Text Cleaning and Preprocessing

Preprocessing must be selected according to the intended task rather than applied indiscriminately.

Potential steps include:

1. Validate that the input is a non-empty text value.
2. Normalise whitespace and handle encoding inconsistencies.
3. Apply a documented casing policy.
4. Remove irrelevant formatting where appropriate.
5. Tokenise text when required by the selected method.
6. Apply stop-word removal or lemmatisation only when suitable for the task.
7. Preserve meaningful domain terms, company names, and technical terminology.
8. Record the preprocessing configuration and version.

For embedding-based or transformer-based methods, aggressive preprocessing can remove information that the model needs. Compare preprocessing choices where they materially affect results.

Keep the original source content separate from its processed representation whenever storing both is permitted and useful.

## 6. Potential NLP Approaches

The following approaches may be evaluated if an approved text source supports them. Listing an approach does not imply that it has been implemented or that it is suitable for every source.

| Approach | Potential purpose | Key limitation |
|---|---|---|
| Keyword extraction | Identify prominent terms in descriptions | Frequent terms do not necessarily represent important business characteristics. |
| TF-IDF representation | Represent text using term importance | Results depend on the available corpus and vocabulary. |
| Text similarity | Compare descriptions across companies | Similar wording does not necessarily imply similar products, risks, or market behaviour. |
| Topic modelling | Explore recurring themes in a sufficiently large corpus | Topics may be unstable or difficult to interpret with a small or homogeneous corpus. |
| Text embeddings | Represent semantic relationships between descriptions | Embeddings may obscure domain-specific distinctions and require appropriate interpretation. |
| Text classification | Assign predefined labels to text | Requires defensible labels and a suitable evaluation dataset. |

Select methods based on source suitability, project complexity, and measurable analytical value. Do not implement every listed method solely to increase the model count.

## 7. Relationship Between Text and Market Data

Any relationship between textual features and market observations must be investigated carefully.

Company descriptions generally provide contextual information; they are not equivalent to real-time market sentiment.

If text-derived features are compared with market variables:

- Identify the date at which the text was available, if that information can be established.
- Ensure that historical predictions do not use text that became available only later.
- Document whether text is static, periodically refreshed, or time-dependent.
- Distinguish exploratory correlation from predictive evidence.
- Avoid causal claims unless the research design supports them.
- Compare results against a numerical-data-only reference where relevant.

If a description cannot be dated reliably, do not use it as a time-varying historical feature in a way that assumes it was available at every past forecast origin.

For a cross-company similarity analysis, describe the result as textual similarity rather than evidence that the companies share the same market dynamics.

## 8. NLP Evaluation Requirements

Evaluation depends on the task being performed.

### 8.1 Exploratory tasks

For keyword extraction, similarity analysis, and exploratory topic modelling:

- Document the corpus and preprocessing procedure.
- Inspect representative outputs for relevance.
- Assess whether results are interpretable and stable.
- Explain the limitations of the chosen method.
- Avoid reporting classification accuracy without labelled ground truth.

### 8.2 Supervised tasks

For classification or another supervised task:

- Define the target labels.
- Explain how labels were obtained and validated.
- Separate training, validation, and test data appropriately.
- Prevent duplicates or closely related records from causing leakage across splits.
- Use metrics appropriate to the target and class distribution.
- Record the evaluation period or split configuration.

If labels cannot be obtained reliably, do not present an unlabelled exploratory method as a supervised predictive system.

### 8.3 Market-related prediction

If text is ever used to predict a market target, it must be evaluated under the chronological protocol defined in `docs/evaluation_protocol.md`.

The evaluation must establish that the text was available at the forecast origin and that the text-derived feature contributes measurable value beyond a suitable numerical-data-only baseline.

A relationship discovered in historical data is not, by itself, proof of predictive usefulness.

## 9. MongoDB Storage Considerations

If NLP data are persisted, their schema must be documented in `docs/data_dictionary.md` before the implementation is treated as final.

Possible storage choices include:

- Extending `company_metadata` with approved descriptive-text fields and provenance.
- Adding a dedicated text collection if text records require independent versioning or history.
- Storing derived NLP outputs in `analysis_results` when they are analytical results rather than source records.

Choose one design based on actual query and retention requirements. Avoid duplicating large text fields across unrelated collections.

Where text is updated, retain sufficient provenance to distinguish a refreshed source value from an older version if historical reproducibility is required.

The notebook and Streamlit application must follow the same storage conventions when both use NLP records.

## 10. Quality, Limitations, and Risks

NLP results can be affected by:

- Missing or incomplete descriptions.
- Outdated or inconsistent source text.
- Different writing styles across companies.
- Limited corpus size.
- Domain-specific vocabulary.
- Ambiguous or weakly defined labels.
- Changes in text availability over time.
- Data leakage caused by using text that was not historically available.
- Unsupported interpretations of similarity, topics, or sentiment.

The project must not infer investor sentiment from company descriptions or imply that static descriptive text provides a reliable signal of future prices.

Any limitation affecting interpretation or reproducibility should be documented with the corresponding experiment.

## 11. Implementation Decision Criteria

NLP functionality should be included only when the following conditions are met:

- [ ] A non-news text source has been identified.
- [ ] Source provenance and access conditions have been documented.
- [ ] The source provides enough suitable text for the proposed task.
- [ ] The task has a clear purpose within BeneathTheMarket.
- [ ] The selected method is appropriate for the data.
- [ ] Data leakage and availability timing have been considered.
- [ ] Evaluation requirements are defined.
- [ ] MongoDB storage, if required, is documented.
- [ ] Results can be interpreted without unsupported market or investment claims.

If these conditions are not met, retain NLP as a future extension rather than presenting it as an implemented capability.

## 12. Related Documentation

- `docs/architecture.md` — system architecture and data flow.
- `docs/data_dictionary.md` — persisted data fields and MongoDB schemas.
- `docs/evaluation_protocol.md` — evaluation methodology and leakage prevention.
- `README.md` — project overview, installation, configuration, and execution instructions.

---

**Maintenance note:** Update this document when a text source is approved, an NLP task is implemented, or the source schema and preprocessing pipeline change. Clearly distinguish proposed approaches from implemented and evaluated functionality.