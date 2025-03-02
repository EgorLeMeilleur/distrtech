import requests

class GitHubClient:
    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    # ---------------- Repository CRUD Operations ----------------
    
    def create_repo(self, name, description="", private=False):
        url = f"{self.api_url}/user/repos"
        data = {
            "name": name,
            "description": description,
            "private": private
        }
        return requests.post(url, headers=self.headers, json=data)

    def get_repo(self, owner, repo):
        url = f"{self.api_url}/repos/{owner}/{repo}"
        return requests.get(url, headers=self.headers)

    def update_repo(self, owner, repo, new_name=None, description=None, private=None):
        url = f"{self.api_url}/repos/{owner}/{repo}"
        data = {}
        if new_name:
            data["name"] = new_name
        if description is not None:
            data["description"] = description
        if private is not None:
            data["private"] = private
        return requests.patch(url, headers=self.headers, json=data)

    def delete_repo(self, owner, repo):
        url = f"{self.api_url}/repos/{owner}/{repo}"
        return requests.delete(url, headers=self.headers)
    
    # ---------------- Label CRUD Operations ----------------
    
    def create_label(self, owner, repo, name, color, description=""):
        url = f"{self.api_url}/repos/{owner}/{repo}/labels"
        data = {
            "name": name,
            "color": color,
            "description": description
        }
        return requests.post(url, headers=self.headers, json=data)
    
    def get_label(self, owner, repo, name):
        url = f"{self.api_url}/repos/{owner}/{repo}/labels/{name}"
        return requests.get(url, headers=self.headers)
    
    def update_label(self, owner, repo, current_name, new_name=None, color=None, description=None):
        url = f"{self.api_url}/repos/{owner}/{repo}/labels/{current_name}"
        data = {}
        if new_name:
            data["new_name"] = new_name
        if color:
            data["color"] = color
        if description is not None:
            data["description"] = description
        return requests.patch(url, headers=self.headers, json=data)
    
    def delete_label(self, owner, repo, name):
        url = f"{self.api_url}/repos/{owner}/{repo}/labels/{name}"
        return requests.delete(url, headers=self.headers)