import httpx
from datetime import date

def fetch_issues(base_url: str, api_key: str, params: dict) -> list[dict]:
    headers = {"X-Redmine-API-Key": api_key}
    
    # Extract the base URL (protocol + host)
    from urllib.parse import urlparse
    parsed = urlparse(base_url)
    base_domain = f"{parsed.scheme}://{parsed.netloc}"
    
    url = f"{base_domain}/issues.json"
    
    try:
        with httpx.Client(timeout=15, verify=False) as client:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json().get("issues", [])
    except Exception as e:
        print(f"Redmine Error: {e}")
        return None

def get_today_issues(url: str, key: str):
    return fetch_issues(url, key, {"assigned_to_id": "me", "due_date": date.today().isoformat()})

def get_overdue_issues(url: str, key: str):
    return fetch_issues(url, key, {"assigned_to_id": "me", "due_date": f"<={date.today().isoformat()}"})

def get_all_issues(url: str, key: str):
    return fetch_issues(url, key, {"status_id": "open"})

def get_my_open_issues(url: str, key: str):
    """Fetch all open issues assigned to the current user."""
    return fetch_issues(url, key, {"assigned_to_id": "me", "status_id": "open"})

def get_issue(base_url: str, key: str, issue_id: int) -> dict | None:
    """Fetch a single issue by ID."""
    from urllib.parse import urlparse
    parsed = urlparse(base_url)
    base_domain = f"{parsed.scheme}://{parsed.netloc}"
    url = f"{base_domain}/issues/{issue_id}.json"
    headers = {"X-Redmine-API-Key": key}
    try:
        with httpx.Client(timeout=15, verify=False) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get("issue")
    except Exception as e:
        print(f"Redmine Error: {e}")
        return None

def get_allowed_statuses(base_url: str, key: str, issue_id: int) -> list[dict] | None:
    """Fetch the list of statuses the current user is allowed to set on an issue."""
    from urllib.parse import urlparse
    parsed = urlparse(base_url)
    base_domain = f"{parsed.scheme}://{parsed.netloc}"
    
    url = f"{base_domain}/issues/{issue_id}.json"
    headers = {"X-Redmine-API-Key": key}
    params = {"include": "allowed_statuses"}
    try:
        with httpx.Client(timeout=15, verify=False) as client:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()
            issue = response.json().get("issue", {})
            # If the API doesn't return allowed_statuses, it means no transitions are allowed
            return issue.get("allowed_statuses", [])
    except Exception as e:
        print(f"Redmine Error: {e}")
        return None

def update_issue_status(base_url: str, key: str, issue_id: int, new_status_id: int) -> bool:
    """Update the status of an issue. Returns True on success."""
    from urllib.parse import urlparse
    parsed = urlparse(base_url)
    base_domain = f"{parsed.scheme}://{parsed.netloc}"
    url = f"{base_domain}/issues/{issue_id}.json"
    headers = {
        "X-Redmine-API-Key": key,
        "Content-Type": "application/json",
    }
    payload = {"issue": {"status_id": new_status_id}}
    try:
        with httpx.Client(timeout=15, verify=False) as client:
            response = client.put(url, headers=headers, json=payload)
            response.raise_for_status()
            return True
    except Exception as e:
        print(f"Redmine Error: {e}")
        return False