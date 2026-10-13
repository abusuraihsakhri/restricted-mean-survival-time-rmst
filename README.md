# Restricted Mean Survival Time (RMST) Calculator

### [Open the browser application →](https://abusuraihsakhri.github.io/restricted-mean-survival-time-rmst/)

A descriptive Kaplan–Meier restricted mean survival time calculator for individual-level right-censored time-to-event data. Calculate single-group RMST/RMTL or compare two groups at a common truncation horizon τ. Time units carry through to the estimates (days, months, etc.).

## Features

- **RMST:** area beneath the right-continuous Kaplan–Meier estimate from 0 through τ.
- **RMTL:** τ − RMST.
- **Two-group comparison:** RMST difference and ratio (comparison/reference; groups sorted by label).
- **Browser:** paste or import CSV/TSV, display KM curves, export an aggregate CSV. Pure JavaScript; no backend, account, installation, Python runtime or external API is required.
- **Python:** standard-library-only statistical estimator, CSV/TSV reader, summary export, and console interface; see `rmst_calc.py`.
- **Optional backend:** `/api/rmst` FastAPI endpoint plus a separate legacy audit demonstration.

## Use the application

Open the [browser calculator](https://abusuraihsakhri.github.io/restricted-mean-survival-time-rmst/) or use `web/index.html` locally. Select **Load example**, or paste/upload data and specify τ. The browser processes observations locally; it does not transmit or store uploaded data. No identifying patient information is required or recommended.

Input columns (case-sensitive in Python, case-insensitive in the browser):

| Column | Meaning |
| --- | --- |
| `time` | Nonnegative finite follow-up time |
| `event` | 1 = event occurred, 0 = right censored |
| `group` | Optional arm label; omit for one group |

For example, see [sample.csv](sample.csv). The same τ is used in both groups and must not exceed each group's maximum observed follow-up. Missing/invalid observations, negative times, nonfinite values, and more than two groups are rejected. For inference, censoring should be independent of the event time; the unadjusted estimator does not correct confounding.

## Run with Python

Python 3.10+ is supported.

```bash
git clone https://github.com/abusuraihsakhri/restricted-mean-survival-time-rmst.git
cd restricted-mean-survival-time-rmst
python -m pip install -e ".[dev]"
python rmst_calc.py batch -i sample.csv -o results.csv --tau 10
python rmst_calc.py single --times 2 4 6 --events 1 0 1 --tau 6
python -m pytest -q
```

The `rmst` installed entry point runs the **separate legacy audit demonstration** (`cli.py`); for statistical analysis use `python rmst_calc.py`. The `enrichment.py` classes provide generic threshold demonstrations; **they do not implement** covariate-adjusted RMST, Rust-style τ selection, power calculations, Schoenfeld diagnostics, or other methods suggested by their class names.

## Optional API and Docker

```bash
python cli.py serve --host 127.0.0.1 --port 8000
# POST /api/rmst with:
# {"tau": 10, "observations": [{"time": 2, "event": 1, "group": "A"}, ...]}
```

For the Docker service, supply a unique secret via `AUDIT_SECRET_KEY` before running `docker compose up --build`. The demo audit log is **in-memory only**, its HMAC chain is not an immutable or persistent record, and identifier-pattern filtering is not a comprehensive PHI detection or de-identification mechanism. Do not deploy the unauthenticated legacy audit API with sensitive information.

## Interpretation and limitations

RMST(τ) = ∫₀^τ Ŝ(t)dt measures time free of the defined event during the first τ time units. A positive RMST difference means the comparison group has a higher estimated restricted event-free time than the reference group. Ratios are unavailable if the reference RMST is zero.

**No confidence intervals, hypothesis tests, covariate adjustment, competing-risks analysis, or clinical risk classification are provided.** Results are descriptive and must not be used as a clinical decision rule.

## Technology and compatibility

The browser interface uses standard HTML, CSS, SVG and JavaScript (modern desktop/mobile browsers; no Pyodide). The Python package uses the standard library for RMST and FastAPI/Pydantic/Uvicorn for its optional backend. GitHub Actions tests Python 3.10–3.12 and Node.js browser logic. MIT license: [LICENSE](LICENSE).
