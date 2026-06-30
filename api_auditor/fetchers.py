import base64
import os
from urllib.parse import urlparse

import requests
import yaml


def create_github_api_url(owner, repo, path):
    github_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    return github_url


def parse_github_browser_url(github_url):
    parsed_url = urlparse(github_url)

    if parsed_url.netloc != "github.com":
        print("Error: Only github.com browser URLs are supported.")
        return
    parts = parsed_url.path.strip("/").split("/")

    # Expected format:
    # /{owner}/{repo}/blob/{ref}/{path}
    if len(parts) < 5:
        print("Error: GitHub URL is too short.")
        return None

    owner = parts[0]
    repo = parts[1]
    url_type = parts[2]
    ref = parts[3]
    path = "/".join(parts[4:])

    if url_type != "blob":
        print("Error: Expected a GitHub file URL containing '/blob/'.")
        return None

    if not path:
        print("Error: GitHub URL does not include a file path.")
        return None

    return {
        "owner": owner,
        "repo": repo,
        "ref": ref,
        "path": path,
    }


def retrieve_github_api_spec(github_url, ref=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "api-readiness-auditor",
    }
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
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
