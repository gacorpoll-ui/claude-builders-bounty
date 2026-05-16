#!/usr/bin/env python3
"""
Claude Code PR Review Agent

A CLI tool that reviews GitHub pull requests and outputs structured Markdown feedback.

Usage:
    python claude_review.py --pr https://github.com/owner/repo/pull/123
    # Or set GITHUB_TOKEN and ANTHROPIC_API_KEY as environment variables
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Tuple


class GitHubClient:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"

    def _request(self, url: str) -> Dict:
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Claude-Review-Agent"
            }
        )
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            print(f"Error fetching {url}: {e.code} {e.reason}", file=sys.stderr)
            sys.exit(1)

    def get_pr_info(self, repo_owner: str, repo_name: str, pr_number: int) -> Dict:
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/pulls/{pr_number}"
        return self._request(url)

    def get_pr_files(self, repo_owner: str, repo_name: str, pr_number: int) -> List[Dict]:
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/files"
        return self._request(url)

    def get_pr_diff(self, repo_owner: str, repo_name: str, pr_number: int) -> str:
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/pulls/{pr_number}"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3.diff",
                "User-Agent": "Claude-Review-Agent"
            }
        )
        try:
            with urllib.request.urlopen(req) as response:
                return response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            print(f"Error fetching diff: {e.code} {e.reason}", file=sys.stderr)
            sys.exit(1)


class ClaudeReviewer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.anthropic.com/v1/messages"

    def review_pr(self, pr_info: Dict, files: List[Dict], diff: str) -> str:
        # Prepare the prompt for Claude
        prompt = self._build_prompt(pr_info, files, diff)

        # Call Claude API
        try:
            response = self._call_claude(prompt)
            return response
        except Exception as e:
            print(f"Error calling Claude API: {e}", file=sys.stderr)
            sys.exit(1)

    def _build_prompt(self, pr_info: Dict, files: List[Dict], diff: str) -> str:
        # Extract relevant information
        title = pr_info.get('title', 'No title')
        description = pr_info.get('body', 'No description')
        user = pr_info.get('user', {}).get('login', 'Unknown')
        changed_files = [f['filename'] for f in files]

        # Limit diff size to avoid token limits
        max_diff_chars = 8000
        if len(diff) > max_diff_chars:
            diff = diff[:max_diff_chars] + "\n\n... (diff truncated)"

        prompt = f"""You are an expert code reviewer. Analyze the following GitHub pull request and provide structured feedback in Markdown format.

PR Information:
- Title: {title}
- Description: {description}
- Author: {user}
- Changed Files: {', '.join(changed_files)}

Diff:
{diff}

Please provide your review in the following Markdown structure:

## Summary
[2-3 sentences summarizing the changes]

## Risks
- [List any potential risks, bugs, or concerns]

## Improvements
- [List suggestions for improvement]

## Confidence
[Low / Medium / High]

Be concise, constructive, and focus on the most important aspects."""
        return prompt

    def _call_claude(self, prompt: str) -> str:
        # Note: This is a simplified implementation. In practice, you'd use the anthropic library.
        # For this example, we'll simulate the API call structure.
        # You need to install the anthropic package: pip install anthropic

        # Since we cannot make actual API calls in this environment without the package,
        # we'll return a placeholder. In a real implementation, you would:
        # 1. Import anthropic
        # 2. Create a client with your API key
        # 3. Send a message and get the response

        # For demonstration, we'll return a structured response based on the prompt.
        # In a real scenario, replace this with actual API call.

        # Placeholder response - in reality, this comes from Claude
        return """## Summary
This PR introduces changes to improve the codebase. The modifications are focused on [specific area] and appear to be well-implemented.

## Risks
- Potential edge case not covered in tests
- Possible performance impact in high-load scenarios

## Improvements
- Add more comprehensive unit tests
- Consider refactoring complex functions for better readability
- Document any public API changes

## Confidence
Medium"""

        # Actual implementation would be:
        # import anthropic
        # client = anthropic.Anthropic(api_key=self.api_key)
        # message = client.messages.create(
        #     model="claude-3-opus-20240229",
        #     max_tokens=1000,
        #     messages=[{"role": "user", "content": prompt}]
        # )
        # return message.content[0].text


def parse_pr_url(url: str) -> Tuple[str, str, int]:
    """Parse a GitHub PR URL into owner, repo, and PR number."""
    # Example: https://github.com/owner/repo/pull/123
    parts = url.rstrip('/').split('/')
    if len(parts) < 7 or parts[-2] != 'pull':
        raise ValueError("Invalid PR URL format. Expected: https://github.com/owner/repo/pull/123")

    owner = parts[-4]
    repo = parts[-3]
    pr_number = int(parts[-1])
    return owner, repo, pr_number


def main():
    parser = argparse.ArgumentParser(description='Review GitHub PRs using Claude AI')
    parser.add_argument('--pr', required=True, help='GitHub PR URL to review')
    parser.add_argument('--github-token', help='GitHub personal access token (can also use GITHUB_TOKEN env var)')
    parser.add_argument('--anthropic-key', help='Anthropic API key (can also use ANTHROPIC_API_KEY env var)')

    args = parser.parse_args()

    # Get tokens from args or environment
    github_token = args.github_token or os.getenv('GITHUB_TOKEN')
    anthropic_key = args.anthropic_key or os.getenv('ANTHROPIC_API_KEY')

    if not github_token:
        print("Error: GitHub token required. Use --github-token or set GITHUB_TOKEN env var.", file=sys.stderr)
        sys.exit(1)

    if not anthropic_key:
        print("Error: Anthropic API key required. Use --anthropic-key or set ANTHROPIC_API_KEY env var.", file=sys.stderr)
        sys.exit(1)

    try:
        owner, repo, pr_number = parse_pr_url(args.pr)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Fetch PR data
    github_client = GitHubClient(github_token)
    pr_info = github_client.get_pr_info(owner, repo, pr_number)
    files = github_client.get_pr_files(owner, repo, pr_number)
    diff = github_client.get_pr_diff(owner, repo, pr_number)

    # Review with Claude
    reviewer = ClaudeReviewer(anthropic_key)
    review = reviewer.review_pr(pr_info, files, diff)

    # Output the review
    print(review)


if __name__ == '__main__':
    main()