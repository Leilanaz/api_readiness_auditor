import requests
import base64
import yaml
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import os


def create_github_api_url(owner, repo, path):
    github_url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'
    return github_url

def retrieve_github_api_spec(github_url, ref=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "api-readiness-auditor",
    }
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f'Bearer {github_token}'
    params = {}
    if ref:
        params["ref"] = ref
    response = requests.get(github_url, headers=headers, params=params, timeout=10)
    if response.status_code == 404:
        print("Error: GitHub file not found. Check the owner, repo, and path.")
        return
    if response.status_code == 403:
        print("Error: GitHub request was forbidden or rate-limited.")
        return
    if response.status_code != 200:
        print(f"Error: GitHub API returned status {response.status_code}")
        return
    if response.status_code == 200:
        print("Success: GitHub returned the file metadata.")
        data = response.json()
        encoded_content = data["content"]
        decoded_bytes = base64.b64decode(encoded_content)
        decoded_content = decoded_bytes.decode("utf-8")
        try:
            spec = yaml.safe_load(decoded_content)
        except yaml.YAMLError as error:
            print(f"Error: Could not parse the file as YAML or JSON: {error}")
            return 
    return spec

def find_github_api_operations(paths):
    if len(paths.keys()) == 0:
        return []
    operations = []
    for path, path_item in paths.items():
        for method, operation in path_item.items():
            operations.append({"method":method.upper(), 
                               "path":path, 
                               "operation":operation})
    return operations

def find_missing_operation_ids(operations):
    missing_operation_ids = []
    for operation_info in operations:
        operation = operation_info["operation"]
        if not operation.get("operationId"):
            result = {
                        "rule": "missing_operation_id",
                        "method": operation_info["method"],
                        "path": operation_info["path"],
                        "message": "Operation is missing operationId"
                    }
            missing_operation_ids.append(result)
    return missing_operation_ids

def print_report(source, metadata, operations, findings):
    print("API Operations Readiness Report\n")
    print(f"Source: {source}")
    print(f"API title: {metadata['title']}")
    print(f"API version: {metadata['version']}")
    print(f"Spec version: {metadata['openapi_version']}")
    print()
    print(f'Operations checked: {len(operations)}')
    print(f'Findings: {len(findings)}')
    print()
    if len(findings) == 0:
        print("No issues found.")
        return
    for finding in findings:
        print(f'{finding["rule"]} {finding["method"]} {finding["path"]}')
        print(finding["message"])

def find_missing_operation_explanation(operations):
    findings =[]
    for operation_info in operations:
        operation = operation_info["operation"]
        summary = operation.get("summary")
        description = operation.get("description")
        if not summary and not description:
            findings.append({
                "rule": "missing_operation_explanation",
                "method": operation_info["method"],
                "path": operation_info["path"],
                "message": "Operation is missing both summary and operation-level description"
            })
    return findings

def find_missing_error_responses(operations):
    findings = []
    for operation_info in operations:
        operation = operation_info["operation"]
        responses = operation.get("responses", {})
        default = "default" in responses
        any_4xx_status = False
        any_5xx_status = False
        for response_info in responses.keys():
            status_code = str(response_info)
            if status_code.startswith("4"):
                any_4xx_status = True
            if status_code.startswith("5"):
                any_5xx_status = True
        if not (any_4xx_status or any_5xx_status or default):
            finding = {
                        "rule": "missing_responses",
                        "method": operation_info["method"],
                        "path": operation_info["path"],
                        "message": "Operation does not document any 4xx, 5xx, or default error response"
                    }
            findings.append(finding)
    return findings

def get_spec_metadata(spec):
    info = spec.get("info", {})

    return {
        "title": info.get("title", "Unknown API"),
        "version": info.get("version", "Unknown version"),
        "openapi_version": spec.get("openapi") or spec.get("swagger") or "Unknown spec version",
    }

def write_audit_log(owner, repo, path, operations, findings, status):
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    log_file = logs_dir / "audit_runs.jsonl"
    
    log_record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": f"{owner}/{repo}/{path}",
        "status": status,
        "operations_checked": len(operations),
        "findings_count": len(findings),
    }

    with open(log_file, "a") as file:
        file.write(json.dumps(log_record) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--path", required=True)
    parser.add_argument("--ref", required=False)

    args = parser.parse_args()
    owner = args.owner
    repo = args.repo
    path = args.path
    ref = args.ref
    github_url = create_github_api_url(owner, repo, path)
    spec = retrieve_github_api_spec(github_url, ref=ref)


    if spec is None:
        print("Audit failed because the OpenAPI spec could not be retrieved.")
        write_audit_log(owner, repo, path, [], [], status="failed")
        return 
    if not isinstance(spec, dict):
        print("Error: Parsed file is not a valid OpenAPI object.")
        return 
    if "openapi" not in spec and "swagger" not in spec:
        print("Error: File does not look like an OpenAPI/Swagger spec.")
        return 
    
    metadata = get_spec_metadata(spec)
    source = f"{owner}/{repo}/{path}"
    paths = spec.get("paths")
    if not isinstance(paths, dict):
        print("Error: OpenAPI spec is missing a valid paths object.")
        return
    operations = find_github_api_operations(paths)
    
    findings = []
    findings.extend(find_missing_operation_ids(operations))
    findings.extend(find_missing_operation_explanation(operations))
    findings.extend(find_missing_error_responses(operations))
    print_report(source, metadata, operations, findings)

    write_audit_log(owner, repo, path, operations, findings, status="success")
    

        

if __name__ == "__main__":
    main()