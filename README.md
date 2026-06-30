# API Readiness Auditor

API Readiness Auditor is a CLI tool that fetches an OpenAPI/Swagger spec from GitHub, audits it for integration-readiness issues, prints a readable report, writes a JSONL audit log, and optionally generates an AI summary of the deterministic findings.

The goal is not to build a full OpenAPI validator. The goal is to provide a practical first-pass readiness check that helps an API-facing engineer understand whether a spec is ready for SDK generation, documentation, or agent-facing tooling.

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
* Supports two GitHub input styles:

  * explicit `--owner`, `--repo`, `--path`, and optional `--ref`
  * normal GitHub browser file URLs through `--github-url`
* Supports optional GitHub authentication through `GITHUB_TOKEN`.
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

Clone the repository:

```bash
git clone https://github.com/Leilanaz/api_readiness_auditor
cd api_readiness_auditor
```

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

The tool supports two ways to identify a GitHub OpenAPI spec.

---

### Option 1: Use explicit GitHub fields

This was the original MVP interface:

```bash
python -m api_auditor.main \
  --owner OAI \
  --repo learn.openapis.org \
  --path examples/v3.0/petstore.yaml \
  --ref main
```

The fields are:

```text
--owner   GitHub repository owner or organization
--repo    GitHub repository name
--path    Path to the OpenAPI/Swagger file inside the repository
--ref     Optional branch, tag, or commit SHA
```

---

### Option 2: Use a normal GitHub browser URL

The tool also supports a normal GitHub file URL:

```bash
python -m api_auditor.main \
  --github-url https://github.com/OAI/learn.openapis.org/blob/main/examples/v3.0/petstore.yaml
```

This is more user-friendly because a customer is more likely to paste a GitHub URL than manually separate the owner, repo, branch, and file path.

The supported URL format is:

```text
https://github.com/{owner}/{repo}/blob/{ref}/{path}
```

For example:

```text
https://github.com/OAI/learn.openapis.org/blob/main/examples/v3.0/petstore.yaml
```

is parsed into:

```text
owner = OAI
repo = learn.openapis.org
ref = main
path = examples/v3.0/petstore.yaml
```

After parsing the URL, the rest of the audit pipeline stays the same.

---

### Run with optional AI summary

```bash
python -m api_auditor.main \
  --github-url https://github.com/OAI/learn.openapis.org/blob/main/examples/v3.0/petstore.yaml \
  --ai-summary
```

`--ai-summary` requires:

```bash
export ANTHROPIC_API_KEY="your_anthropic_api_key_here"
```

The main audit works without an Anthropic API key.

---

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

With `--ai-summary`, the tool also prints a concise customer-readable summary of the deterministic findings.

---

## Example specs

This repository includes an `examples/` directory with sample files that can be used to test and demo the tool.

```text
examples/
  success_openapi.yaml
  partial_issues_openapi.yaml
  not_openapi.yaml
```

These files are intentionally small so the behavior of the audit rules is easy to understand.



---

### 1. Success case

File:

```text
examples/success_openapi.yaml
```

This file contains a clean OpenAPI spec. Each operation includes:

* `operationId`
* operation-level `summary` and `description`
* documented success responses
* documented error responses

Run with explicit fields:

```bash
python -m api_auditor.main \
  --owner Leilanaz \
  --repo api_readiness_auditor \
  --path examples/success_openapi.yaml
```

Run with GitHub URL:

```bash
python -m api_auditor.main \
  --github-url https://github.com/Leilanaz/api_readiness_auditor/blob/main/examples/success_openapi.yaml
```

Expected result:

```text
API Operations Readiness Report

Source: Leilanaz/api_readiness_auditor/examples/success_openapi.yaml
API title: Clean Payments API
API version: 1.0.0
Spec version: 3.0.0

Operations checked: 2
Findings: 0

No issues found.
```

This shows the happy path: the file is fetched successfully, parsed as OpenAPI, audited, and no issues are found.

---

### 2. Partial issues case

File:

```text
examples/partial_issues_openapi.yaml
```

This file is still shaped like an OpenAPI spec, but it intentionally has integration-readiness issues:

* some operations are missing `operationId`
* some operations are missing operation-level `summary` or `description`
* some operations only document success responses and do not document any `4xx`, `5xx`, or `default` error response

Run with explicit fields:

```bash
python -m api_auditor.main \
  --owner Leilanaz \
  --repo api_readiness_auditor \
  --path examples/partial_issues_openapi.yaml
```

Run with GitHub URL:

```bash
python -m api_auditor.main \
  --github-url https://github.com/Leilanaz/api_readiness_auditor/blob/main/examples/partial_issues_openapi.yaml
```

Expected result, assuming the example file matches the sample version created for this project:

```text
API Operations Readiness Report

Source: Leilanaz/api_readiness_auditor/examples/partial_issues_openapi.yaml
API title: Problematic Payments API
API version: 1.0.0
Spec version: 3.0.0

Operations checked: 3
Findings: 7

missing_operation_id GET /payments
Operation is missing operationId

missing_operation_id POST /refunds
Operation is missing operationId

missing_operation_explanation POST /payments
Operation is missing both summary and operation-level description

missing_operation_explanation POST /refunds
Operation is missing both summary and operation-level description

missing_error_response GET /payments
Operation does not document any 4xx, 5xx, or default error response

missing_error_response POST /payments
Operation does not document any 4xx, 5xx, or default error response

missing_error_response POST /refunds
Operation does not document any 4xx, 5xx, or default error response
```

This is the best demo file because it shows that the tool can find real issues, not just pass a clean spec.

The exact order of findings depends on the order the rules are run in `main.py`. The expected finding count and finding types should match.

---

### 3. Failure case

File:

```text
examples/not_openapi.yaml
```

This file is valid YAML, but it is not an OpenAPI or Swagger spec. It is used to demonstrate graceful failure handling.

Run with explicit fields:

```bash
python -m api_auditor.main \
  --owner Leilanaz \
  --repo api_readiness_auditor \
  --path examples/not_openapi.yaml
```

Run with GitHub URL:

```bash
python -m api_auditor.main \
  --github-url https://github.com/Leilanaz/api_readiness_auditor/blob/main/examples/not_openapi.yaml
```

Expected result:

```text
Error: File does not look like an OpenAPI/Swagger spec.
```

This shows that the tool does not blindly audit any YAML file. It checks whether the parsed content looks like an OpenAPI/Swagger document before continuing.

---

## Testing commands used during development

These are the main commands used to test the tool.

---

### Public GitHub OpenAPI spec with explicit fields

```bash
python -m api_auditor.main \
  --owner OAI \
  --repo learn.openapis.org \
  --path examples/v3.0/petstore.yaml \
  --ref main
```

Expected result:

```text
Operations checked: 3
Findings: 0

No issues found.
```

---

### Public GitHub OpenAPI spec with browser URL

```bash
python -m api_auditor.main \
  --github-url https://github.com/OAI/learn.openapis.org/blob/main/examples/v3.0/petstore.yaml
```

Expected result:

```text
Operations checked: 3
Findings: 0

No issues found.
```

---

### Public GitHub OpenAPI spec with AI summary

```bash
python -m api_auditor.main \
  --github-url https://github.com/OAI/learn.openapis.org/blob/main/examples/v3.0/petstore.yaml \
  --ai-summary
```

Expected result:

```text
Operations checked: 3
Findings: 0

No issues found.

AI Summary

...
```

The exact AI summary text may vary because it is generated by Claude. The audit findings should remain deterministic.

---

### Bad GitHub URL shape

```bash
python -m api_auditor.main \
  --github-url https://github.com/OAI/learn.openapis.org
```

Expected result:

```text
Error: GitHub URL is too short.
```

or a similar clear parsing error.

---

### Nonexistent GitHub file

```bash
python -m api_auditor.main \
  --owner OAI \
  --repo learn.openapis.org \
  --path examples/v3.0/does-not-exist.yaml
```

Expected result:

```text
Error: GitHub file not found.
Audit failed because the OpenAPI spec could not be retrieved.
```

This tests that the tool handles GitHub 404 responses gracefully.

---

## Architecture

Project structure:

```text
api_auditor/
  __init__.py
  main.py          CLI orchestration
  fetchers.py      GitHub API fetching, auth, decoding, parsing, URL parsing
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
Resolve GitHub input
  ↓
If --github-url is provided, parse owner/repo/ref/path from URL
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

## GitHub input design

The first version of the tool accepted:

```text
owner
repo
path
optional ref
```

This was intentional because those fields map directly to the GitHub Contents API:

```text
https://api.github.com/repos/{owner}/{repo}/contents/{path}
```

That made the GitHub API integration simple and explicit.

However, a real customer is more likely to provide a normal GitHub browser URL, such as:

```text
https://github.com/OAI/learn.openapis.org/blob/main/examples/v3.0/petstore.yaml
```

So the tool now supports `--github-url` as a more user-friendly input.

The current design supports both:

```text
Developer/API-friendly input:
--owner OAI --repo learn.openapis.org --path examples/v3.0/petstore.yaml --ref main

Customer-friendly input:
--github-url https://github.com/OAI/learn.openapis.org/blob/main/examples/v3.0/petstore.yaml
```

The user should provide either `--github-url` or `--owner/--repo/--path`, not both.

This design keeps the original simple API-shaped interface while adding a better customer-facing input path.

---

## Current limitations of GitHub URL support

The current `--github-url` support is intentionally limited to normal GitHub file URLs in this format:

```text
https://github.com/{owner}/{repo}/blob/{ref}/{path}
```

It does not yet support every possible GitHub URL format, such as:

```text
raw.githubusercontent.com URLs
GitHub directory URLs containing /tree/
GitHub pull request URLs
GitHub gist URLs
non-GitHub URLs
```

A future version could support those formats by adding more URL parsing logic or by adding a separate raw URL fetcher.

---

## How the GitHub file is read

The tool does not scrape or visually read a GitHub webpage.

It calls GitHub’s REST API programmatically.

The flow is:

```text
User provides GitHub URL or owner/repo/path
  ↓
Tool extracts owner, repo, path, and optional ref
  ↓
Tool builds the GitHub Contents API URL
  ↓
Tool sends an HTTP GET request to GitHub
  ↓
GitHub returns JSON metadata and base64-encoded file content
  ↓
Tool decodes the content into UTF-8 text
  ↓
Tool parses the text as YAML/JSON
  ↓
Tool audits the parsed OpenAPI structure
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

---

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

---

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

---

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

---

### GitHub

The tool optionally reads:

```bash
export GITHUB_TOKEN="your_github_token_here"
```

If present, it sends the token in the GitHub API request headers. If not present, it makes unauthenticated requests, which are sufficient for the default public-repository demo.

I chose this because it is simple, secure enough for a local CLI, and avoids hardcoding secrets.

---

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

---

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

For AI summaries, there are two possible models.

---

### Platform-owned Anthropic key

The app uses its own Anthropic key on the backend.

Pros:

* Better user experience
* Users do not need to bring their own key
* Easier to control model/version behavior

Cons:

* The platform pays the LLM cost
* Requires usage limits and abuse prevention

---

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

---

### Why a CLI?

I chose a CLI because the exercise is time-boxed and the core value is API integration and technical judgment, not UI polish.

A CLI is:

* Easy to run locally
* Easy to demo
* Easy to explain
* Appropriate for developer tooling

---

### Why GitHub first?

Many API specs are stored in GitHub. Using GitHub also gives the project a real external API integration with authentication, rate limits, refs, errors, and file metadata.

---

### Why explicit owner/repo/path first?

Explicit arguments map directly to the GitHub Contents API. This reduced the initial scope and made the API interaction easier to understand.

After the MVP worked, I added support for normal GitHub browser URLs to improve customer ergonomics.

---

### Why only three audit rules?

The goal was not to build a complete OpenAPI validator. I chose three high-signal rules that directly affect SDKs, docs, and agent tooling.

---

### Why JSONL instead of a database?

A database would be unnecessary for the MVP. JSONL provides simple local observability without adding infrastructure.

---

### Why optional AI?

The AI feature improves communication, but it should not be required for correctness. The audit should still work without any LLM access.

---

## What I would improve with more time

With more time, I would add:

* Support for local files
* Support for direct raw URLs
* Support for more GitHub URL formats
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
runtime logs with sensitive repo information
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

---

## Quick demo script

A simple demo flow:

1. Run the clean example and show that it passes.

```bash
python -m api_auditor.main \
  --github-url https://github.com/Leilanaz/api_readiness_auditor/blob/main/examples/success_openapi.yaml
```

2. Run the partial issues example and show that the tool finds problems.

```bash
python -m api_auditor.main \
  --github-url https://github.com/Leilanaz/api_readiness_auditor/blob/main/examples/partial_issues_openapi.yaml
```

3. Run the non-OpenAPI example and show graceful failure.

```bash
python -m api_auditor.main \
  --github-url https://github.com/Leilanaz/api_readiness_auditor/blob/main/examples/not_openapi.yaml
```

4. Run a public third-party OpenAPI spec.

```bash
python -m api_auditor.main \
  --github-url https://github.com/OAI/learn.openapis.org/blob/main/examples/v3.0/petstore.yaml
```

5. Optionally run with AI summary.

```bash
python -m api_auditor.main \
  --github-url https://github.com/OAI/learn.openapis.org/blob/main/examples/v3.0/petstore.yaml \
  --ai-summary
```

---

## Project summary

This project is a small, focused API readiness tool. It demonstrates:

* External API integration with GitHub
* OpenAPI parsing and operation extraction
* Deterministic audit logic
* Clear terminal reporting
* Lightweight observability through JSONL logs
* Optional AI-assisted communication
* Practical error handling
* Clear design tradeoffs

The main design principle is that the core audit should be deterministic, explainable, and easy to defend. The AI feature is optional and only helps communicate the results.
