import requests

def rgb_to_hex(rgb_str):
    """
    Convert an RGB string "R,G,B" into a 6-digit hex string.
    Example: "255,0,0" -> "ff0000"
    """
    try:
        # Split the string and convert each part to an integer
        parts = [int(x.strip()) for x in rgb_str.split(',')]
        if len(parts) != 3 or any(not (0 <= x <= 255) for x in parts):
            raise ValueError("RGB values must be three numbers between 0 and 255.")
        # Format to hex (without the leading '#')
        return "{:02x}{:02x}{:02x}".format(*parts)
    except Exception as e:
        print("Invalid RGB input:", e)
        return None

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
        if ',' in color:
            hex_color = rgb_to_hex(color)
            if not hex_color:
                print("Using default color: 'ffffff'")
                hex_color = "ffffff"
        else:
            hex_color = color
        
        url = f"{self.api_url}/repos/{owner}/{repo}/labels"
        data = {
            "name": name,
            "color": hex_color,
            "description": description
        }
        return requests.post(url, headers=self.headers, json=data)
    
    def get_label(self, owner, repo, name):
        url = f"{self.api_url}/repos/{owner}/{repo}/labels/{name}"
        return requests.get(url, headers=self.headers)
    
    def update_label(self, owner, repo, current_name, new_name=None, color=None, description=None):
        data = {}
        if new_name:
            data["new_name"] = new_name
        if color:
            if ',' in color:
                hex_color = rgb_to_hex(color)
                if not hex_color:
                    print("Using current color unchanged")
                else:
                    data["color"] = hex_color
            else:
                data["color"] = color
        if description is not None:
            data["description"] = description
        url = f"{self.api_url}/repos/{owner}/{repo}/labels/{current_name}"
        return requests.patch(url, headers=self.headers, json=data)
    
    def delete_label(self, owner, repo, name):
        url = f"{self.api_url}/repos/{owner}/{repo}/labels/{name}"
        return requests.delete(url, headers=self.headers)