from github import Github
from pydantic import Field
from pydash import pick

from functions.github.models import RepositoryInput


async def get_issues(gh: Github, **kwargs):
    """
    This function will fetch a list of the repository's issues. It will return the title, and issue
    number of 5 issues.
    """

    class GetIssuesInput(RepositoryInput):
        pass

    input = GetIssuesInput(**kwargs)
    repo = gh.get_repo(input.repository)
    issues = repo.get_issues(sort="created", direction="desc")
    return [{"title": issue.title, "number": issue.number} for issue in issues[:5]]


async def get_issue(gh: Github, **kwargs):
    """
    This function will fetch the title, body, and comment thread of a specific issue.
    """

    class GetIssueInput(RepositoryInput):
        issue_number: int = Field(description="Issue number as an integer, e.g. `42`")

    input = GetIssueInput(**kwargs)
    repo = gh.get_repo(input.repository)
    issue = repo.get_issue(input.issue_number)
    comments = [
        pick(comment.raw_data, ["body", "url", "user.login", "created_at"])
        for comment in issue.get_comments()
    ]
    return {"title": issue.title, "body": issue.body, "comments": comments}


async def comment_on_issue(gh: Github, **kwargs):
    """
    This function is useful when you need to comment on a GitHub issue. Simply pass in the issue number
    and the comment you would like to make. Please use this sparingly as we don't want to clutter
    the comment threads.
    """

    class CommentOnIssueInput(RepositoryInput):
        issue_number: int = Field(description="Issue number as an integer, e.g. `42`")
        comment: str = Field(description="The comment to add to the issue")

    input = CommentOnIssueInput(**kwargs)
    repo = gh.get_repo(input.repository)
    issue = repo.get_issue(input.issue_number)
    issue.create_comment(input.comment)
    return {"status": "success"}
