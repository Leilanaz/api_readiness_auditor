# API Readiness Auditor

API Readiness Auditor is a small CLI tool that fetches an OpenAPI/Swagger spec from GitHub, audits it for integration-readiness issues, prints a readable report, optionally generates an AI summary, and writes a JSONL audit log.

The goal is not to build a full OpenAPI validator. The goal is to provide a practical first-pass check that helps an API-facing engineer understand whether a spec is ready for SDK generation, documentation, or agent-facing tooling.

---

## Target user

The primary user is a technical person working with customer APIs, such as:

* Forward Deployed Engineer
* Solutions Engineer
* API platform engineer
* Developer experience engineer
* Customer engineering team preparing an API for SDK/docs/tool generation

A typical use case:

> A customer wants to generate SDKs, docs, or agent tools from their OpenAPI spec. Before doing that, an engineer wants to quickly inspect whether the spec has obvious integration-readiness issues.

---

## Problem

OpenAPI specs are often treated as the source of truth for API tooling. But if a spec is missing stable operation names, clear operation descriptions, or documented error behavior, generated SDKs, docs, and agent tools can become harder to use.

This tool solves a small version of that problem. It fetches an OpenAPI spec from GitHub and checks for a few high-signal issues that affect integration quality:

* Are operations named clearly and stably?
* Are operations understandable to a developer or agent?
* Is failure behavior documented?

The output is intended to be useful for a customer-facing technical conversation, not just a raw validation dump.

---

## What the tool does

The CLI:

* Fetches an OpenAPI/Swagger file from GitHub using the GitHub Contents API.
* Supports optional GitHub authentication through `GITHUB_TOKEN`.
* Supports an optional GitHub `ref` for auditing a specific branch, tag, or commit.
* Decodes the GitHub API response from base64 into text.
* Parses the file as YAML/JSON.
* Checks that the file looks like an OpenAPI/Swagger spec.
* Extracts operations from the OpenAPI `paths` object.
* Runs deterministic audit rules.
* Prints a terminal report.
* Writes a JSONL audit log for lightweight observability.
* Optionally calls Claude to generate a plain-English integration-readiness summary.

---

## Prerequisites

Required:

* Python 3.10 or newer
* `pip`
* Internet connection
* Access to a GitHub repository containing an OpenAPI or Swagger spec
* Dependencies listed in `requirements.txt`

For the default public-repository demo, no API keys are required.

Optional environment variables:

```bash
export GITHUB_TOKEN="your_github_token_here"
```

`GITHUB_TOKEN` is optional. The tool can fetch public GitHub files without it, but setting a token enables authenticated GitHub API requests, which can help with rate limits or private repository access.

```bash
export ANTHROPIC_API_KEY="your_anthropic_api_key_here"
```

`ANTHROPIC_API_KEY` is only required when using the optional `--ai-summary` flag. The main audit works without it.

Do not commit real API keys or tokens to the repository. Set them locally as environment variables instead.

---

## Installation

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## How to run

Run against a public OpenAPI spec in GitHub:

```bash
python -m api_auditor.main \
  --owner OAI \
  --repo learn.openapis.org \
  --path examples/v3.0/petstore.yaml
```

Run against a specific branch, tag, or commit:

```bash
python -m api_auditor.main \
  --owner OAI \
  --repo learn.openapis.org \
  --path examples/v3.0/petstore.yaml \
  --ref main
```

Run with optional AI summary:

```bash
python -m api_auditor.main \
  --owner OAI \
  --repo learn.openapis.org \
  --path examples/v3.0/petstore.yaml \
  --ai-summary
```

---

## Example output

```text
Success: GitHub returned the file metadata.

API Operations Readiness Report

Source: OAI/learn.openapis.org/examples/v3.0/petstore.yaml
API title: Swagger Petstore
API version: 1.0.0
Spec version: 3.0.0

Operations checked: 3
Findings: 0

No issues found.
```

With `--ai-summary`, the tool also prints a concise customer-readable summary of the deterministic findings.

---

## Example specs

The `examples/` directory contains demo inputs for testing and review.

```text
examples/
  success_openapi.yaml
  partial_issues_openapi.yaml
  not_openapi.yaml
```

### 1. Success example

`examples/success_openapi.yaml`

A clean OpenAPI spec that should pass the current audit rules.

Expected result:

```text
Operations checked: 2
Findings: 0

No issues found.
```

### 2. Partial issues example

`examples/partial_issues_openapi.yaml`

A valid OpenAPI-shaped spec with missing operation IDs, missing operation explanations, and missing error responses.

Expected result:

```text
Findings: several issues detected
```

This is useful for demonstrating that the tool does more than pass the happy path.

### 3. Failure example

`examples/not_openapi.yaml`

A valid YAML file that is not an OpenAPI/Swagger spec.

Expected result:

```text
Error: File does not look like an OpenAPI/Swagger spec.
Audit failed because the OpenAPI spec could not be retrieved.
```

After pushing this repository to GitHub, you can run the tool against your own examples:

```bash
python -m api_auditor.main \
  --owner YOUR_USERNAME \
  --repo API-readiness-auditor \
  --path examples/partial_issues_openapi.yaml
```

---

## Architecture

Project structure:

```text
api_auditor/
  __init__.py
  main.py          CLI orchestration
  fetchers.py      GitHub API fetching, auth, decoding, and parsing
  openapi.py       OpenAPI metadata and operation extraction
  rules.py         Deterministic audit rules
  report.py        Terminal report formatting
  logger.py        JSONL audit logging
  ai_summary.py    Optional Claude-generated summary
```

High-level flow:

```text
CLI arguments
  ↓
Build GitHub Contents API URL
  ↓
Call GitHub REST API
  ↓
Receive JSON metadata and base64-encoded file content
  ↓
Decode file content into YAML/JSON text
  ↓
Parse into a Python dictionary
  ↓
Validate that it looks like OpenAPI/Swagger
  ↓
Extract operations from paths
  ↓
Run deterministic audit rules
  ↓
Print report
  ↓
Write JSONL audit log
  ↓
Optionally generate AI summary
```

---

## Why the tool asks for owner, repo, path, and ref

The current CLI accepts:

```text
owner
repo
path
optional ref
```

Example:

```bash
--owner OAI \
--repo learn.openapis.org \
--path examples/v3.0/petstore.yaml \
--ref main
```

This maps directly to the GitHub Contents API:

```text
https://api.github.com/repos/{owner}/{repo}/contents/{path}
```

This was an intentional MVP design choice. Asking for structured GitHub fields makes the GitHub API integration explicit and avoids adding URL parsing complexity in the first version.

A more user-friendly future version would also accept a normal GitHub browser URL, such as:

```text
https://github.com/OAI/learn.openapis.org/blob/main/examples/v3.0/petstore.yaml
```

and internally parse it into:

```text
owner = OAI
repo = learn.openapis.org
ref = main
path = examples/v3.0/petstore.yaml
```

For this MVP, I chose the explicit version because it is simpler, reliable, and directly reflects how the GitHub API is called.

---

## How the GitHub file is read

The tool does not scrape or visually read a GitHub webpage. It calls GitHub’s REST API programmatically.

The flow is:

```text
Build GitHub API URL
  ↓
Send HTTP GET request
  ↓
GitHub returns JSON metadata
  ↓
The file content is returned as base64-encoded text
  ↓
The tool decodes base64 into UTF-8 text
  ↓
The text is parsed as YAML/JSON
```

So the tool is closer to downloading the file through an API than viewing a website.

The browser URL and API URL are different:

```text
Browser URL:
https://github.com/OAI/learn.openapis.org/blob/main/examples/v3.0/petstore.yaml

API URL:
https://api.github.com/repos/OAI/learn.openapis.org/contents/examples/v3.0/petstore.yaml
```

---

## Audit rules

The current version includes three deterministic audit rules.

### 1. Missing `operationId`

`operationId` is important because generated SDKs and agent tools often use it to create stable function or method names.

Example:

```yaml
paths:
  /payments:
    get:
      operationId: listPayments
```

This can become a generated method such as:

```python
client.list_payments()
```

Without `operationId`, tooling may need to invent names from HTTP methods and paths, which can lead to unclear or unstable generated interfaces.

This rule checks:

```text
Does each operation have operationId?
```

### 2. Missing operation explanation

This rule checks whether an operation has either:

```text
summary
description
```

at the operation level.

Example:

```yaml
post:
  operationId: createPayment
  summary: Create a payment
  description: Creates a new payment for a customer.
```

This matters because a developer or agent needs to understand when and why to use the operation.

The tool intentionally checks operation-level `summary` and `description`, not response-level descriptions. A response description like `"200": "OK"` does not explain what the operation itself does.

### 3. Missing error response documentation

This rule checks whether each operation documents at least one of:

```text
4xx response
5xx response
default response
```

This matters because real integrations need to handle failure cases. A spec that only documents a success response may not give enough information for SDKs, docs, or customer implementations.

Example of documented failure behavior:

```yaml
responses:
  "200":
    description: OK
  "400":
    description: Invalid request
  "500":
    description: Internal server error
```

For the MVP, the rule checks whether an error-response slot exists. A future version could check the quality and consistency of those error schemas.

---

## Why these rules were chosen

OpenAPI specs contain many fields, including schemas, parameters, request bodies, tags, examples, auth schemes, servers, and components.

I intentionally chose three operation-level checks because they are small, explainable, and high-impact for integration readiness:

```text
operationId
  → Can the operation become a stable SDK method or agent tool?

summary / description
  → Can a developer or agent understand what the operation does?

error responses
  → Can an integration understand what happens when something fails?
```

This project is a pre-flight readiness check, not a full OpenAPI validator. The goal is to identify obvious issues that would matter before generating SDKs, docs, or agent-facing tools.

---

## Error handling

The tool handles several failure cases:

* GitHub file not found
* GitHub forbidden or rate-limited response
* Other non-success GitHub API responses
* Network timeout
* Invalid YAML/JSON
* Parsed content that is not a dictionary/object
* YAML/JSON that does not look like OpenAPI/Swagger
* Missing or invalid `paths` object
* Optional AI summary failure

The audit is designed to fail clearly rather than continue with invalid data.

---

## Large file limitations

The current implementation expects the GitHub Contents API to return base64-encoded file content. This is appropriate for normal small OpenAPI specs.

For very large files, this MVP has limitations:

* The full file is loaded into memory.
* The full YAML/JSON content is parsed at once.
* Larger GitHub files may require a raw-content fallback.
* Extremely large files should have a maximum supported size to avoid memory issues.

A production version would improve this by:

* Checking GitHub file size metadata before decoding.
* Rejecting or warning on very large files.
* Adding a raw download fallback for larger files.
* Streaming content where appropriate.
* Avoiding sending large specs to an LLM.
* Keeping the LLM summary based only on deterministic findings, not the full spec.

---

## Authentication design

For this local CLI, authentication is handled through environment variables.

### GitHub

The tool optionally reads:

```bash
export GITHUB_TOKEN="your_github_token_here"
```

If present, it sends the token in the GitHub API request headers. If not present, it makes unauthenticated requests, which are sufficient for the default public-repository demo.

I chose this because it is simple, secure enough for a local CLI, and avoids hardcoding secrets.

### Anthropic

The optional AI summary uses the Anthropic Python SDK, which reads:

```bash
export ANTHROPIC_API_KEY="your_anthropic_api_key_here"
```

The key is only needed when using:

```bash
--ai-summary
```

The main audit does not require Anthropic credentials.

### Why not OAuth?

OAuth would be more appropriate for a hosted multi-user product where each user connects their own GitHub account.

For this CLI, OAuth would add unnecessary complexity:

* OAuth app setup
* Browser login flow
* Callback URL
* Token exchange
* Token storage
* Refresh/revocation behavior
* User sessions

For the MVP, environment variables are simpler and easier to explain.

---

## Hosted product design

If this were turned into a hosted web app, I would change the auth model.

A hosted version would likely use:

```text
User logs into the web app
  ↓
User connects GitHub through OAuth
  ↓
Backend receives a scoped GitHub access token
  ↓
Token is encrypted at rest
  ↓
User selects repo/spec path
  ↓
Backend fetches the OpenAPI spec
  ↓
Audit runs on backend
  ↓
Report is shown in UI
```

For AI summaries, there are two possible models:

### Platform-owned Anthropic key

The app uses its own Anthropic key on the backend.

Pros:

* Better user experience
* Users do not need to bring their own key
* Easier to control model/version behavior

Cons:

* The platform pays the LLM cost
* Requires usage limits and abuse prevention

### Bring-your-own-key

Each user provides their own Anthropic key.

Pros:

* User pays their own LLM bill
* Less platform cost risk

Cons:

* Worse user experience
* Requires careful encrypted secret storage
* Users may not trust the app with their keys

For a production SaaS version, I would likely use GitHub OAuth for repo access and a platform-owned Anthropic key for summaries, with per-user quotas, rate limits, and audit logging.

---

## Observability

Each run appends one JSON object to:

```text
logs/audit_runs.jsonl
```

Example:

```json
{"timestamp": "2026-06-29T04:46:05.153904+00:00", "source": "OAI/learn.openapis.org/examples/v3.0/petstore.yaml", "status": "success", "operations_checked": 3, "findings_count": 0, "ai_summary_requested": false}
```

I chose JSONL instead of a database because this is a small proof of concept. JSONL is:

* Simple
* Append-only
* Easy to inspect
* Easy to process later
* Enough to demonstrate lightweight observability

A production version could store audit runs in a database and provide a dashboard.

---

## AI summary design

The optional AI summary is intentionally not part of the correctness path.

The deterministic Python rules produce the findings. Claude only turns those structured findings into a customer-readable summary.

The design is:

```text
OpenAPI spec
  ↓
Deterministic audit rules
  ↓
Structured findings
  ↓
Optional Claude summary
  ↓
Plain-English explanation
```

This separation is intentional.

The LLM does not decide whether the spec is correct. It only helps communicate the result more clearly.

If the Claude call fails, the audit should still succeed. The LLM feature is optional and non-blocking.

---


## AI usage while building

I used AI as a learning, debugging, and code-review assistant while building this project.

AI helped me with:

* Understanding the problem space and narrowing the project scope
* Thinking through how this tool could be useful in a Forward Deployed Engineer workflow
* Explaining OpenAPI concepts such as `paths`, operations, `operationId`, responses, and operation-level descriptions
* Reviewing my implementation choices and identifying flaws in the logic
* Improving the structure of the code by separating fetching, OpenAPI parsing, rules, reporting, logging, and AI summarization into different modules
* Debugging issues around GitHub file fetching, YAML parsing, CLI arguments, and rule behavior
* Stress-testing the design by asking interview-style questions about failure modes, authentication, large files, and hosted-product design
* Improving README explanations so the architecture, tradeoffs, and reasoning are clear

I did not use AI as the source of truth for the audit results. The core audit logic is deterministic Python code that checks the OpenAPI spec directly.

The optional Claude integration inside the project is also intentionally limited. Claude does not decide whether the spec passes or fails. The Python rules generate the findings first, and Claude only turns those findings into a more customer-readable summary.

This separation was intentional: AI helped improve the code, reasoning, and communication, but the correctness of the audit comes from explicit, inspectable rules.


---

## Tradeoffs

### Why a CLI?

I chose a CLI because the exercise is time-boxed and the core value is API integration and technical judgment, not UI polish.

A CLI is:

* Easy to run locally
* Easy to demo
* Easy to explain
* Appropriate for developer tooling

### Why GitHub first?

Many API specs are stored in GitHub. Using GitHub also gives the project a real external API integration with authentication, rate limits, refs, errors, and file metadata.

### Why explicit owner/repo/path instead of URL parsing?

Explicit arguments map directly to the GitHub Contents API. This reduced scope and made the API interaction easier to understand.

A future version should accept normal GitHub browser URLs for better usability.

### Why only three audit rules?

The goal was not to build a complete OpenAPI validator. I chose three high-signal rules that directly affect SDKs, docs, and agent tooling.

### Why JSONL instead of a database?

A database would be unnecessary for the MVP. JSONL provides simple local observability without adding infrastructure.

### Why optional AI?

The AI feature improves communication, but it should not be required for correctness. The audit should still work without any LLM access.

---

## What I would improve with more time

With more time, I would add:

* Support for normal GitHub browser URLs
* Support for local files
* Support for direct raw URLs
* More OpenAPI validation rules
* Duplicate `operationId` detection
* Auth/security scheme checks
* Request body and parameter quality checks
* Schema completeness checks
* Example coverage checks
* Pagination pattern checks
* Severity levels for findings
* A readiness score
* Markdown or JSON report export
* Unit tests for each rule
* Better handling for very large specs
* A small web UI
* Database-backed audit history
* GitHub OAuth for hosted usage
* Team/workspace support for a hosted version

---

## Security notes

Do not commit real API keys or tokens.

The repository should not include:

```text
.env
real GitHub tokens
real Anthropic API keys
private customer specs
```

Use environment variables locally instead.

Recommended `.gitignore` entries:

```text
.venv/
__pycache__/
*.pyc
.env
.DS_Store
logs/audit_runs.jsonl
```
