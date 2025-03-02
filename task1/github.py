import requests

class GitHubClient:
    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json"
        }

    def create_repo(self, name, description="", private=False):
        url = f"{self.api_url}/user/repos"
        data = {
            "name": name,
            "description": description,
            "private": private
        }
        response = requests.post(url, headers=self.headers, json=data)
        return response

    def get_repo(self, owner, repo):
        url = f"{self.api_url}/repos/{owner}/{repo}"
        response = requests.get(url, headers=self.headers)
        return response

    def update_repo(self, owner, repo, new_name=None, description=None, private=None):
        url = f"{self.api_url}/repos/{owner}/{repo}"
        data = {}
        if new_name:
            data["name"] = new_name
        if description is not None:
            data["description"] = description
        if private is not None:
            data["private"] = private
        response = requests.patch(url, headers=self.headers, json=data)
        return response

    def delete_repo(self, owner, repo):
        url = f"{self.api_url}/repos/{owner}/{repo}"
        response = requests.delete(url, headers=self.headers)
        return response