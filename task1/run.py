import json
from token_work import load_key, load_token, save_token, delete_token_files
from github_crud import GitHubClient
from authentication import get_github_access_token
from dotenv import load_dotenv
import os
import argparse

def run():
    parser = argparse.ArgumentParser(description="Token to use")
    parser.add_argument("--pat", action="store_true", help="Use personal access token")
    args = parser.parse_args()
    
    load_dotenv()
    
    if args.pat:
        key = load_key('pat')
        token = load_token(key, 'pat')

        if not token:
            print('Access token obtained.')
            token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
            save_token(token, key, 'pat')
    else:
        key = load_key('oauth2')
        token = load_token(key, 'oauth2')

        if not token:
            token = get_github_access_token()
            save_token(token, key, 'oauth2')

    client = GitHubClient(token)

    while True:
        print("\nGitHub Client Application")
        print("1. Work with repositories")
        print("2. Work with repositories labels")
        print("3. Logout (delete saved tokens)")
        print("4. Exit")
        choice = input("Enter your choice (1-4): ")

        if choice == "1":
            print("Repositories management")
            print("1. Create repository")
            print("2. Get repository info")
            print("3. Update repository")
            print("4. Delete repository (does not work with oauth token)")
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

            else:
                print("Invalid choice. Please select an option from 1 to 4.")

        elif choice == "2":
            print("\nLabels Management:")
            print("1. Create Label")
            print("2. Get Label")
            print("3. Update Label")
            print("4. Delete Label")
            label_choice = input("Enter your choice (1-4): ")

            if label_choice == "1":
                owner = input("Enter repository owner name: ")
                repo = input("Enter repository name: ")
                name = input("Enter label name: ")
                color = input("Enter label color (6-digit hex without # or RGB in format R,G,B): ")
                description = input("Enter label description (optional): ")
                resp = client.create_label(owner, repo, name, color, description)
                print("Status:", resp.status_code)
                try:
                    print("Response:", json.dumps(resp.json(), indent=4))
                except Exception:
                    print("No response body.")

            elif label_choice == "2":
                owner = input("Enter repository owner name: ")
                repo = input("Enter repository name: ")
                name = input("Enter label name: ")
                resp = client.get_label(owner, repo, name)
                print("Status:", resp.status_code)
                try:
                    print("Response:", json.dumps(resp.json(), indent=4))
                except Exception:
                    print("No response body.")

            elif label_choice == "3":
                owner = input("Enter repository owner name: ")
                repo = input("Enter repository name: ")
                current_name = input("Enter current label name: ")
                new_name = input("Enter new label name (or leave blank): ")
                color = input("Enter new label color (6-digit hex without # or RGB in format R,G,B or leave blank): ")
                description = input("Enter new label description (or leave blank): ")
                resp = client.update_label(owner, repo, current_name,
                                           new_name if new_name else None,
                                           color if color else None,
                                           description if description else None)
                print("Status:", resp.status_code)
                try:
                    print("Response:", json.dumps(resp.json(), indent=4))
                except Exception:
                    print("No response body.")

            elif label_choice == "4":
                owner = input("Enter repository owner name: ")
                repo = input("Enter repository name: ")
                name = input("Enter label name to delete: ")
                confirm = input(f"Are you sure you want to delete label '{name}' from {owner}/{repo}? (y/n): ")
                if confirm.lower() == "y":
                    resp = client.delete_label(owner, repo, name)
                    print("Status:", resp.status_code)
                    if resp.status_code == 204:
                        print("Label deleted successfully.")
                    else:
                        try:
                            print("Response:", json.dumps(resp.json(), indent=4))
                        except Exception:
                            print("No response body.")
                else:
                    print("Deletion cancelled.")

            else:
                print("Invalid choice. Please select an option from 1 to 4.")

        elif choice == "3":
            delete_token_files()
            print("Logged out. Please restart the application to log in again.")
            break

        elif choice == "4":
            print("Exiting application.")
            break

        else:
            print("Invalid choice. Please select an option from 1 to 4.")

if __name__ == "__main__":
    run()