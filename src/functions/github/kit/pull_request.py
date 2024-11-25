import json

import requests
import tiktoken
from github import Github, PullRequest
from pydantic import Field
from pydash import pick

from ..utils.models import RepositoryInput


def _format_pull_request(pr: PullRequest):
    raw_data = pr.raw_data
    raw_data["reviewers"] = [reviewer["login"] for reviewer in raw_data["requested_reviewers"]]
    raw_data["assignees"] = [assignee["login"] for assignee in raw_data["assignees"]]

    return pick(raw_data, [
        "id",
        "title",
        "labels",
        "number",
        "html_url",
        "diff_url",
        "patch_url",
        "commits",
        "additions",
        "deletions",
        "changed_files",
        "comments",
        "state",
        "user.login",
        "assignees",
        "reviewers",
        "created_at",
        "updated_at"
    ])

async def create_pull_request(gh: Github, **kwargs):
    """
        This function is useful when you need to create a new pull request in a GitHub repository.
    """
    class CreatePullRequestInput(RepositoryInput):
        title: str = Field(description="The title of the pull request.")
        source_branch: str = Field(description="The source branch to create the pull request from, e.g. `main`")
        destination_branch: str = Field(description="The destination branch to create the pull request to, e.g. `main`")
        input: str = Field(description="The body or description of the pull request.")

    input = CreatePullRequestInput(**kwargs)
    repo = gh.get_repo(input.repository)
    repo.create_pull(input.destination_branch, input.source_branch, title=input.title, body=input.input)

async def close_pull_request(gh: Github, **kwargs):
    """
    This function will close a pull request in the repository.
    """
    class ClosePullRequestInput(RepositoryInput):
        pr_number: int = Field(description="The PR number as an integer, e.g. `12`")

    input = ClosePullRequestInput(**kwargs)
    repo = gh.get_repo(input.repository)
    pr = repo.get_pull(input.pr_number)
    pr.edit(state="closed")
    return f"Closed PR #{input.pr_number}"

async def open_pull_request(gh: Github, **kwargs):
    """
    This function will open a pull request in the repository.
    """
    class OpenPullRequestInput(RepositoryInput):
        pr_number: int = Field(description="The PR number as an integer, e.g. `12`")

    input = OpenPullRequestInput(**kwargs)
    repo = gh.get_repo(input.repository)
    pr = repo.get_pull(input.pr_number)
    pr.edit(state="open")
    return f"Opened PR #{input.pr_number}"

async def list_open_pull_requests(gh: Github, **kwargs):
    """
      This function will fetch a list of the repository's Pull Requests (PRs). It will return the title,
      and PR number of 5 PRs.
    """
    class ListOpenPullRequestsInput(RepositoryInput):
        pass

    input = ListOpenPullRequestsInput(**kwargs)
    repo = gh.get_repo(input.repository)
    return [_format_pull_request(pr) for pr in repo.get_pulls(state="open")[:5]]

async def get_pull_request(gh: Github, **kwargs):
    """
      This function will fetch the title, body, comment thread and commit history of a specific Pull
      Request (by PR number).
    """
    class GetPullRequestInput(RepositoryInput):
        pr_number: int = Field(description="The PR number as an integer, e.g. `12`")

    input = GetPullRequestInput(**kwargs)
    repo = gh.get_repo(input.repository)
    return _format_pull_request(repo.get_pull(input.pr_number))

async def list_pull_request_files(gh: Github, **kwargs):
    """
      This function will fetch the full text of all files in a pull request (PR) given the PR number as
      an input. This is useful for understanding the code changes in a PR or contributing to it.
    """
    class ListPullRequestFilesInput(RepositoryInput):
        pr_number: int = Field(description="The PR number as an integer, e.g. `12`")

    input = ListPullRequestFilesInput(**kwargs)
    repo = gh.get_repo(input.repository)
    pr_files = []
    MAX_TOKENS_FOR_FILES = 3_000

    pr = repo.get_pull(input.pr_number)
    paginated_files = pr.get_files()
    number_of_page = paginated_files.totalCount
    total_tokens = 0
    for i in range(number_of_page):
        files = paginated_files.get_page(i)
        if len(files) == 0:
            break

        for file in files:
            if total_tokens <= MAX_TOKENS_FOR_FILES:
                try:
                    content = repo.get_contents(file.filename, ref=pr.head.sha).decoded_content.decode("utf-8")
                except Exception as e:
                    print(f"Failed downloading file content (Error {file.filename}). Skipping")
                    continue

                file_tokens = len(
                    tiktoken.get_encoding("cl100k_base").encode(
                        content + file.filename + "file_name file_contents"
                    )
                )
                if total_tokens < MAX_TOKENS_FOR_FILES:
                    pr_files.append(
                        {
                            "filename": file.filename,
                            "contents": content,
                            "additions": file.additions,
                            "deletions": file.deletions,
                        }
                    )
                    total_tokens += file_tokens
            else:
                pr_files.append(
                    {
                        "filename": file.filename,
                        "contents": None,
                        "additions": file.additions,
                        "deletions": file.deletions,
                    }
                )

    return pr_files

async def search_issues_and_prs(gh: Github, **kwargs):
    """
      This function will search for issues and pull requests in the repository. **VERY IMPORTANT**: You
      must specify the search query as a string input parameter. It will return the five last
      issues or PRs that match the search query.
    """
    class SearchIssuesAndPRsInput(RepositoryInput):
        search_query: str = Field(description="The search query as a string, e.g. `My issue title or topic`")

    input = SearchIssuesAndPRsInput(**kwargs)
    search_result = gh.search_issues(input.search_query, repo=input.repository)
    max_items = min(5, search_result.totalCount)
    results = [f"Top {max_items} results:"]
    for issue in search_result[:max_items]:
        results.append(
            f"Title: {issue.title}, Number: {issue.number}, State: {issue.state}"
        )
    return "\n".join(results)

async def create_review_request(gh: Github, **kwargs):
    """
      This function will create a review request on the open pull request that matches the current active
      branch.
    """
    class CreateReviewRequestInput(RepositoryInput):
        username: str = Field(description="The GitHub username of the user being requested, e.g. `my_username`")
        pr_number: int = Field(description="The PR number as an integer, e.g. `12`")

    input = CreateReviewRequestInput(**kwargs)
    pull_request = gh.get_repo(input.repository).get_pull(input.pr_number)
    try:
        pull_request.create_review_request(reviewers=[input.username])
        return (
            f"Review request created for user {input.username} "
            f"on PR #{pull_request.number}"
        )
    except Exception as e:
        return f"Failed to create a review request with error {e}"