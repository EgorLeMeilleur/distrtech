import json
from token_work import load_key, load_token, save_token, delete_token_files
from github import GitHubClient
from authentication import get_github_access_token

def run():
    key = load_key()
    token = load_token(key)

    if not token:
        token = get_github_access_token()
        save_token(token, key)
    client = GitHubClient(token)

    while True:
        print("\nGitHub Client Application with OAuth2")
        print("1. Create repository")
        print("2. Get repository info")
        print("3. Update repository")
        print("4. Delete repository")
        print("5. Logout (delete saved token)")
        print("6. Exit")
        choice = input("Enter your choice (1-6): ")

        if choice == "1":
            name = input("Enter repository name: ")
            description = input("Enter repository description: ")
            private_input = input("Private repository? (y/n): ")
            private = private_input.lower() == "y"
            resp = client.create_repo(name, description, private)
            print("Status:", resp.status_code)
            try:
                print("Response:", json.dumps(resp.json(), indent=4))
            except Exception:
                print("No response body.")

        elif choice == "2":
            owner = input("Enter repository owner name: ")
            repo = input("Enter repository name: ")
            resp = client.get_repo(owner, repo)
            print("Status:", resp.status_code)
            try:
                print("Response:", json.dumps(resp.json(), indent=4))
            except Exception:
                print("No response body.")

        elif choice == "3":
            owner = input("Enter repository owner name: ")
            repo = input("Enter repository name: ")
            new_name = input("Enter new repository name (or leave blank): ")
            description = input("Enter new description (or leave blank): ")
            private_input = input("Make repository private? (y/n or leave blank for no change): ")
            private = None
            if private_input.lower() == "y":
                private = True
            elif private_input.lower() == "n":
                private = False
            resp = client.update_repo(owner, repo,
                                        new_name if new_name else None,
                                        description if description else None,
                                        private)
            print("Status:", resp.status_code)
            try:
                print("Response:", json.dumps(resp.json(), indent=4))
            except Exception:
                print("No response body.")

        elif choice == "4":
            owner = input("Enter repository owner name: ")
            repo = input("Enter repository name: ")
            confirm = input(f"Are you sure you want to delete {owner}/{repo}? This action is irreversible (y/n): ")
            if confirm.lower() == "y":
                resp = client.delete_repo(owner, repo)
                print("Status:", resp.status_code)
                if resp.status_code == 204:
                    print("Repository deleted successfully.")
                else:
                    try:
                        print("Response:", json.dumps(resp.json(), indent=4))
                    except Exception:
                        print("No response body.")
            else:
                print("Deletion cancelled.")

        elif choice == "5":
            delete_token_files()
            print("Logged out. Please restart the application to log in again.")
            break

        elif choice == "6":
            print("Exiting application.")
            break

        else:
            print("Invalid choice. Please select an option from 1 to 6.")

if __name__ == "__main__":
    run()