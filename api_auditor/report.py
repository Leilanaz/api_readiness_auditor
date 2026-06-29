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