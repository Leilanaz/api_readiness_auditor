from datetime import datetime, timezone
from pathlib import Path
import json


def write_audit_log(
    owner, repo, path, operations, findings, status, ai_summary_requested=False
):
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    log_file = logs_dir / "audit_runs.jsonl"

    log_record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": f"{owner}/{repo}/{path}",
        "status": status,
        "operations_checked": len(operations),
        "findings_count": len(findings),
        "ai_summary_requested": ai_summary_requested,
    }

    with open(log_file, "a") as file:
        file.write(json.dumps(log_record) + "\n")
