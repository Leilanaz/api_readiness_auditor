# API Readiness Auditor

A small CLI tool that fetches an OpenAPI spec from GitHub, audits it for integration-readiness issues, prints a human-readable report, optionally generates an AI summary, and writes a JSONL audit log.

## Problem

Before an API can be turned into SDKs, docs, or agent-facing tools, the OpenAPI spec needs to be understandable and consistent enough for developers and tooling to rely on it. In a customer-facing integration setting, an engineer may need to quickly inspect a customer’s API spec and identify issues that could make integration harder.

This project solves a small version of that problem: it fetches an OpenAPI spec from GitHub and checks for common readiness issues such as missing `operationId`, missing operation-level explanations, and missing documented error responses.

## What it does

The tool:

* Fetches an OpenAPI/Swagger file from a GitHub repository using the GitHub Contents API.
* Supports optional GitHub authentication through `GITHUB_TOKEN`.
* Supports an optional GitHub `ref` so a user can audit a specific branch, tag, or commit.
* Parses the fetched YAML/JSON spec.
* Extracts API operations from the `paths` object.
* Runs a small set of deterministic audit rules.
* Prints a readable terminal report.
* Writes a JSONL audit log for lightweight observability.
* Optionally calls Claude to generate a plain-English integration-readiness summary.

## How to run

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the audit:

```bash
python -m api_auditor.main \
  --owner OAI \
  --repo learn.openapis.org \
  --path examples/v3.0/petstore.yaml
```

Run with a specific branch/tag/commit:

```bash
python -m api_auditor.main \
  --owner OAI \
  --repo learn.openapis.org \
  --path examples/v3.0/petstore.yaml \
  --ref main
```

Run with an optional AI summary:

```bash
python -m api_auditor.main \
  --owner OAI \
  --repo learn.openapis.org \
  --path examples/v3.0/petstore.yaml \
  --ai-summary
```

## Credentials and setup

The GitHub token is optional for public repositories, but can be used for higher rate limits or private repositories:

```bash
export GITHUB_TOKEN="your_github_token"
```

The AI summary is optional. To use it, set:

```bash
export ANTHROPIC_API_KEY="your_anthropic_api_key"
```

The tool still works without Anthropic credentials as long as `--ai-summary` is not used.

## Example output

```text
API Operations Readiness Report

Source: OAI/learn.openapis.org/examples/v3.0/petstore.yaml
API title: Swagger Petstore
API version: 1.0.0
Spec version: 3.0.0

Operations checked: 3
Findings: 0

No issues found.
```

With `--ai-summary`, the tool also prints a short customer-readable explanation of the audit result.

## Architecture

The project is split by responsibility:

```text
api_auditor/
  main.py          CLI orchestration
  fetchers.py      GitHub API fetching, authentication, decoding, and parsing
  openapi.py       OpenAPI metadata extraction and operation extraction
  rules.py         Deterministic audit rules
  report.py        Terminal report formatting
  logger.py        JSONL audit logging
  ai_summary.py    Optional Claude-generated summary
```

High-level flow:

```text
CLI arguments
  ↓
GitHub Contents API
  ↓
base64 decode file content
  ↓
parse YAML/JSON
  ↓
validate that it looks like OpenAPI/Swagger
  ↓
extract operations
  ↓
run deterministic audit rules
  ↓
print report
  ↓
write JSONL audit log
  ↓
optionally generate AI summary
```

## Audit rules

The current version checks for:

### 1. Missing `operationId`

`operationId` matters because SDK generators and agent-tool generators often use it to create stable function or method names.

### 2. Missing operation explanation

The tool checks whether each operation has either a `summary` or an operation-level `description`. Response-level descriptions are not counted for this rule because they describe specific responses, not the operation itself.

### 3. Missing error response documentation

The tool checks whether an operation documents at least one `4xx`, one `5xx`, or a `default` response. This helps identify operations where failure behavior may be unclear to developers or generated clients.

## Error handling

The tool handles several failure cases:

* GitHub file not found.
* GitHub forbidden or rate-limited response.
* Other non-success GitHub API responses.
* Network timeout.
* Invalid YAML/JSON.
* Parsed content that is not an OpenAPI/Swagger object.
* Specs missing a valid `paths` object.

Failed runs are also written to the JSONL audit log.

## Observability

Each audit run appends one JSON object to:

```text
logs/audit_runs.jsonl
```

Example:

```json
{"timestamp": "2026-06-29T04:46:05.153904+00:00", "source": "OAI/learn.openapis.org/examples/v3.0/petstore.yaml", "status": "success", "operations_checked": 3, "findings_count": 0, "ai_summary_requested": false}
```

I chose JSONL instead of a database or dashboard because this is a small proof of concept. JSONL is simple, append-only, easy to inspect, and enough to demonstrate lightweight observability.

## AI usage

I used AI as a learning and pair-programming assistant while building this project. AI helped me reason through project scope, understand OpenAPI/MCP-related concepts, review architecture tradeoffs, debug Python issues, and improve the README.

I did not use AI as the source of truth for audit findings. The audit rules are deterministic Python checks. The optional Claude integration only turns the structured findings into a concise, customer-readable summary. This separation was intentional: the correctness path should be repeatable and explainable, while the LLM is used only as a presentation layer.

## Tradeoffs

I intentionally kept the scope small. This is not a full OpenAPI validator and does not attempt to replace production tools. It focuses on a few integration-readiness checks that are easy to understand, useful in a customer-facing context, and directly tied to SDK/doc/tool generation quality.

I also did not build a UI or database. A CLI plus JSONL logging was enough for the timebox and made the system easier to explain.

## What I would improve with more time

With more time, I would add:

* More OpenAPI validation rules.
* A severity system for findings.
* A readiness score.
* Detection of auth/security scheme issues.
* Checks for duplicate or poorly named `operationId` values.
* Support for local files and direct URLs in addition to GitHub.
* Markdown report export.
* Tests for each audit rule.
* A small HTML dashboard for log inspection.
