import base64
import os

import requests
import yaml

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
