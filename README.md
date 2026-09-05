# Restricted Mean Survival Time (RMST) Calculator

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Standards:** CAP / CLSI / ISO Standards

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## Overview

Restricted Mean Survival Time (RMST) Difference Calculator computes the area under the Kaplan-Meier survival curve up to a truncation time tau and calculates the RMST difference between two treatment arms.

This zero-dependency Python implementation supports single-case evaluation and batch CSV processing, with an enterprise-grade multi-agent supervisor system for clinical decision support.

**Author:** Dr. Abu Suraih Sakhri
**License:** MIT

---

## Key Features

### Core RMST Calculation (`rmst_calc.py`)
- **`calculate_metrics()`** - Core scoring algorithm with weighted parameter evaluation
- **`process_single()`** - Evaluate a single case with v1, v2, v3 parameters
- **`process_batch()`** - Process CSV files with multiple records

### Enterprise Agent System (`agents/`)
- **Multi-Agent Supervisor** - Orchestrates QC, Safety, and Protocol Conformance workers
- **Zero-PHI Outbound Guard** - AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers
- **HMAC-SHA256 Audit Trail** - Cryptographically chained, tamper-evident logging
- **FastAPI REST API** - OpenAPI endpoints with Prometheus telemetry

### Enrichment Engines (`enrichment.py`)
- Current State Engine
- RMST Ratio & Restricted Mean Time Lost (RMTL)
- Data-Driven Tau Selection (Rust et al.)
- RMST-Based Sample Size Calculator (Royston & Parmar)
- ANCOVA-RMST Covariate Adjustment
- Non-Proportional Hazards Diagnostics
- RMST Landmark Analysis

---

## Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/restricted-mean-survival-time-rmst.git
cd restricted-mean-survival-time-rmst

# Install dependencies
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

---

## Usage

### Core RMST Calculator (`rmst_calc.py`)

**Single case evaluation:**
```bash
python rmst_calc.py single --v1 14.5 --v2 4.2 --v3 1.8
```

**Batch CSV processing:**
```bash
python rmst_calc.py batch -i sample.csv -o results.csv
```

### Enterprise CLI (`cli.py`)

**Run a single audit task:**
```bash
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2
```

**Batch process CSV records:**
```bash
python cli.py batch -i input.csv -o output.csv
```

**Verify audit trail integrity:**
```bash
python cli.py verify-audit
```

**Launch FastAPI REST server:**
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

**Supervisory chat query:**
```bash
python cli.py chat "Explain RMST methodology"
```

### Input Data Schema (Batch CSV)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Patient identifier | Required |
| `v1` | Primary measurement value | Required |
| `v2` | Secondary measurement value | Required |
| `v3` | Tertiary measurement value | Required |

---

## REST API Endpoints

When running the FastAPI server (`cli.py serve`):

| Endpoint | Method | Description |
|:---------|:-------|:------------|
| `/health` | GET | Service health check |
| `/metrics` | GET | Prometheus-compatible metrics |
| `/api/audit` | POST | Submit task for evaluation |
| `/api/chat` | POST | Query supervisory chat |
| `/api/audit/logs` | GET | Retrieve audit trail |

---

## Security Features

- **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, emails, DOBs, and patient names
- **HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation
- **Input Validation:** File existence, format validation, and error handling on all batch operations

**Production Note:** Set the `AUDIT_SECRET_KEY` environment variable for production deployments. Without it, a development key is used with a warning.

---

## Testing

```bash
# Run all tests
pytest -v

# Run with coverage (if pytest-cov installed)
pytest -v --cov=. --cov-report=term-missing
```

### Test Coverage
- Core RMST calculation and batch processing
- PHI guard enforcement and security
- Multi-agent worker evaluations
- Supervisor consensus and audit trail
- Enrichment engine suite execution
- CLI command integration

---

## Simulation & Benchmarking

```bash
# Run high-throughput simulation (default: 100 iterations)
python simulator.py

# Run with custom iteration count
python simulator.py 500
```

---

## Docker Deployment

```bash
# Build and run with Docker
docker build -t restricted-mean-survival-time-rmst .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key restricted-mean-survival-time-rmst

# Or use Docker Compose
docker-compose up -d
```

---

## Project Structure

```
.
├── rmst_calc.py          # Core RMST calculation engine
├── cli.py                # Enterprise CLI interface
├── enrichment.py         # Enrichment engine suite
├── simulator.py          # High-throughput simulation
├── sample.csv            # Sample input data
├── test_rmst_calc.py     # Core calculation tests
├── pyproject.toml        # Project configuration
├── Dockerfile            # Container build
├── docker-compose.yml    # Container orchestration
├── agents/               # Enterprise agent system
│   ├── __init__.py
│   ├── api.py            # FastAPI REST server
│   ├── base.py           # Security, PHI guard, audit trail
│   ├── models.py         # Pydantic data models
│   ├── supervisor.py     # Multi-agent orchestrator
│   ├── workers.py        # Specialized domain workers
│   ├── llm_factory.py    # LLM provider factory
│   ├── metrics.py        # Prometheus metrics
│   ├── learning.py       # Bayesian calibration engine
│   └── streamer.py       # WebSocket telemetry
└── tests/                # Test suite
    ├── test_enrichment.py
    └── test_restricted_mean_survival_time_rmst.py
```
