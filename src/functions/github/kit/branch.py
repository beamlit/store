from github import Github
from pydantic import Field

from functions.github.models import RepositoryBranchInput, RepositoryInput


async def search_code(gh: Github, **kwargs):
    """
    This function will search for code in the repository.
    """

    class SearchCodeInput(RepositoryBranchInput):
        query: str = Field(
            description="A keyword-focused natural language search query for code, e.g. `MyFunctionName()`."
        )

    input = SearchCodeInput(**kwargs)
    search_results = gh.search_code(
        query=input.query, repo=input.repository, ref=input.branch
    )
    if search_results.totalCount == 0:
        return "0 results found."
    max_results = min(5, search_results.totalCount)
    results = [f"Showing top {max_results} of {search_results.totalCount} results:"]
    count = 0
    repo = gh.get_repo(input.repository)
    for code in search_results:
        if count >= max_results:
            break
        # Get the file content using the PyGithub get_contents method
        file_content = repo.get_contents(
            code.path, ref=input.branch
        ).decoded_content.decode()
        results.append(
            f"Filepath: `{code.path}`\nFile contents: " f"{file_content}\n<END OF FILE>"
        )
        count += 1
    return "\n".join(results)


async def list_branches(gh: Github, **kwargs):
    """
    This function will list all branches in the repository.
    """

    class ListBranchesInput(RepositoryInput):
        pass

    input = ListBranchesInput(**kwargs)
    repo = gh.get_repo(input.repository)
    branches = [branch.raw_data for branch in repo.get_branches()]
    if branches:
        return branches
    else:
        return "No branches found in the repository"


async def create_branch(gh: Github, **kwargs):
    """
    This function will create a new branch in the repository.
    """

    class CreateBranchInput(RepositoryInput):
        branch: str = Field(
            description="The name of the branch to create, e.g. `my_branch`"
        )

    input = CreateBranchInput(**kwargs)
    repo = gh.get_repo(input.repository)
    repo.create_git_ref(
        ref=f"refs/heads/{input.branch}", sha=repo.get_branch("main").commit.sha
    )
    return f"Created branch {input.branch}"


async def delete_branch(gh: Github, **kwargs):
    """
    This function will delete a branch in the repository.
    """

    class DeleteBranchInput(RepositoryInput):
        branch: str = Field(
            description="The name of the branch to delete, e.g. `my_branch` **IMPORTANT**: only send the name of the branch, not heads/my_branch"
        )

    input = DeleteBranchInput(**kwargs)
    repo = gh.get_repo(input.repository)
    ref = repo.get_git_ref(f"heads/{input.branch}")
    ref.delete()
    return f"Deleted branch {input.branch}"
