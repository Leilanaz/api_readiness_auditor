HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}


def get_spec_metadata(spec):
    info = spec.get("info", {})

    return {
        "title": info.get("title", "Unknown API"),
        "version": info.get("version", "Unknown version"),
        "openapi_version": spec.get("openapi")
        or spec.get("swagger")
        or "Unknown spec version",
    }


def extract_operations(paths):
    if len(paths.keys()) == 0:
        return []
    operations = []
    for path, path_item in paths.items():
        for method, operation in path_item.items():
            method_lower = method.lower()

            if method_lower not in HTTP_METHODS:
                continue

            operations.append(
                {"method": method.upper(), "path": path, "operation": operation}
            )
    return operations
