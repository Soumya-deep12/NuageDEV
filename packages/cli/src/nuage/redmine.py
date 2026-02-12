import httpx
from datetime import date

def fetch_issues(base_url: str, api_key: str, params: dict) -> list[dict]:
    headers = {"X-Redmine-API-Key": api_key}
    url = f"{base_url.rstrip('/')}/issues.json"
    try:
        with httpx.Client(timeout=5) as client:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json().get("issues", [])
    except Exception as e:
        print(f"⚠️ Redmine Error: {e}")
        return []

def get_today_issues(url: str, key: str):
    return fetch_issues(url, key, {"assigned_to_id": "me", "due_date": date.today().isoformat()})

def get_overdue_issues(url: str, key: str):
    return fetch_issues(url, key, {"assigned_to_id": "me", "due_date": f"<{date.today().isoformat()}"})