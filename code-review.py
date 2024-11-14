import os
import re
import requests
import subprocess
from typing import List
from sklearn.linear_model import LogisticRegression
import json
from nltk.tokenize import word_tokenize

# Set your GitHub token as an environment variable for security
# print(os.getenv("GITHUB_TOKEN"))
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


# Basic configurations
REPO_OWNER = "[Repo Owner]"
REPO_NAME = "[Repo Name]"
GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

class CodeReviewBot:
    def __init__(self):
        self.model = LogisticRegression()  # Placeholder for more advanced models

    def fetch_pull_requests(self) -> list:
        """Fetch open pull requests."""
        response = requests.get(f"{GITHUB_API_URL}/pulls", headers=HEADERS)
        try:
            pull_requests = response.json()
            if not isinstance(pull_requests, list):
                print("Unexpected response format:", pull_requests)
                return []
            return pull_requests
        except json.JSONDecodeError:
            print("Failed to parse JSON response:", response.text)
            return []

    def analyze_code(self, files: List[str]):
        """Run style and lint checks on each file in the PR."""
        results = {}
        for file_path in files:
            # Example with pylint
            lint_result = subprocess.run(
                ["pylint", file_path],
                capture_output=True,
                text=True
            )
            results[file_path] = lint_result.stdout
        return results

    def detect_common_issues(self, code: str) -> List[str]:
        """Run regex-based checks for common issues."""
        issues = []
        patterns = {
            "unused_import": r"import .+  # unused import",
            "print_statements": r"\bprint\(",
            "debug_statements": r"\bdebug\b"
        }
        for issue, pattern in patterns.items():
            if re.search(pattern, code):
                issues.append(issue)
        return issues

    def predict_code_issues(self, code: str) -> List[str]:
        """Use a basic ML model to predict more advanced issues."""
        tokens = word_tokenize(code)
        # Example: vectorize and classify; using a placeholder model here
        features = [len(tokens), sum(1 for t in tokens if t.isdigit())]
        prediction = self.model.predict([features])
        if prediction[0] == 1:
            return ["Potential issue identified"]
        return []

    def review_pull_request(self, pull_request):
        """Perform a code review on a given pull request."""
        pr_number = pull_request["number"]
        files_url = pull_request["_links"]["self"]["href"] + "/files"
        files_response = requests.get(files_url, headers=HEADERS)
        files = files_response.json()
        
        # Collect code review comments
        comments = []
        for file in files:
            if file["filename"].endswith(".py"):
                file_content = requests.get(file["raw_url"], headers=HEADERS).text
                lint_results = self.analyze_code([file["filename"]])
                common_issues = self.detect_common_issues(file_content)
                ml_issues = self.predict_code_issues(file_content)
                
                # Summarize issues found
                if lint_results.get(file["filename"]):
                    comments.append(f"Linting issues in {file['filename']}:\n{lint_results[file['filename']]}")
                if common_issues:
                    comments.append(f"Common issues in {file['filename']}: {', '.join(common_issues)}")
                if ml_issues:
                    comments.append(f"ML-detected issues in {file['filename']}: {', '.join(ml_issues)}")

        # Post comments to PR
        self.post_review_comment(pr_number, "\n\n".join(comments))

    def post_review_comment(self, pr_number, comment):
        """Post a review comment on the pull request."""
        comment_url = f"{GITHUB_API_URL}/issues/{pr_number}/comments"
        payload = {
            "body": comment
        }
        response = requests.post(comment_url, headers=HEADERS, json=payload)
        if response.status_code == 201:
            print(f"Posted review comment to PR #{pr_number}")
        else:
            print(f"Failed to post review comment to PR #{pr_number}: {response.status_code}")

    def start(self):
        """Start the code review process."""
        pull_requests = self.fetch_pull_requests()
        for pr in pull_requests:
            print(f"Reviewing PR #{pr['number']} by {pr['user']['login']}")
            self.review_pull_request(pr)

# Run the bot
if __name__ == "__main__":
    print('Program starting')
    print(os.getenv("GITHUB_TOKEN"))
    bot = CodeReviewBot()
    bot.start()
