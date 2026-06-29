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
