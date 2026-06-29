import argparse


from api_auditor.fetchers import create_github_api_url, retrieve_github_api_spec
from api_auditor.openapi import extract_operations, get_spec_metadata
from api_auditor.rules import (
    find_missing_error_responses,
    find_missing_operation_explanation,
    find_missing_operation_ids,
)
from api_auditor.report import print_report
from api_auditor.logger import write_audit_log
from api_auditor.ai_summary import generate_ai_summary




def main():
    parser = argparse.ArgumentParser(
        description="Audit an OpenAPI spec from GitHub for integration-readiness issues."
        )
    parser.add_argument("--owner", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--path", required=True)
    parser.add_argument("--ref", required=False)
    parser.add_argument("--ai-summary", action="store_true")

    args = parser.parse_args()
    owner = args.owner
    repo = args.repo
    path = args.path
    ref = args.ref
    ai_summary = args.ai_summary
    
    github_url = create_github_api_url(owner, repo, path)
    spec = retrieve_github_api_spec(github_url, ref=ref)


    if spec is None:
        print("Audit failed because the OpenAPI spec could not be retrieved.")
        write_audit_log(owner, repo, path, [], [], status="failed", ai_summary_requested=ai_summary )
        return 
    if not isinstance(spec, dict):
        print("Error: Parsed file is not a valid OpenAPI object.")
        write_audit_log(owner, repo, path, [], [], status="failed", ai_summary_requested=ai_summary)
        return 
    if "openapi" not in spec and "swagger" not in spec:
        print("Error: File does not look like an OpenAPI/Swagger spec.")
        write_audit_log(owner, repo, path, [], [], status="failed", ai_summary_requested=ai_summary)
        return 
    
    paths = spec.get("paths")
    if not isinstance(paths, dict):
        print("Error: OpenAPI spec is missing a valid paths object.")
        return
    metadata = get_spec_metadata(spec)
    source = f"{owner}/{repo}/{path}"
    operations = extract_operations(paths)
    
    findings = []
    findings.extend(find_missing_operation_ids(operations))
    findings.extend(find_missing_operation_explanation(operations))
    findings.extend(find_missing_error_responses(operations))
    
    print_report(source, metadata, operations, findings)

    write_audit_log(
        owner, 
        repo, 
        path, 
        operations, 
        findings, 
        status="success", 
        ai_summary_requested=ai_summary,
        )
    
    if ai_summary:
        print()
        print("AI summary")
        print()
        summary = generate_ai_summary(metadata, operations, findings)
        print(summary)

        

if __name__ == "__main__":
    main()