from github import Github
from pydantic import Field

from functions.github.models import RepositoryBranchInput


async def create_file(gh: Github, **kwargs):
    """
    This function will create a file in the repository.
    """
    class CreateFileInput(RepositoryBranchInput):
        path: str = Field(description="The path to the file to be created, e.g. `src/my_file.py`")
        content: str = Field(description="The content of the file to be created")
        message: str = Field(description="The commit message to be used for the file creation")
    input = CreateFileInput(**kwargs)
    repo = gh.get_repo(input.repository)
    try:
        file = repo.get_contents(input.path, ref=input.branch)
        if file:
            return (
                f"File already exists at `{input.path}` "
                f"on branch `{input.branch}`. You must use "
                "`update_file` to modify it."
            )
    except Exception:
        pass

    repo.create_file(input.path, input.message, input.content, branch=input.branch)
    return f"Created file {input.path} with message: {input.message} on branch {input.branch}"

async def read_file(gh: Github, **kwargs):
    """
    This function will read a file from the repository.
    """
    class ReadFileInput(RepositoryBranchInput):
        path: str = Field(description="The full file path of the file you would like to read where the path must NOT start with a slash, e.g. `some_dir/my_file.py`.")

    input = ReadFileInput(**kwargs)
    repo = gh.get_repo(input.repository)
    file = repo.get_contents(input.path, ref=input.branch)
    return file.decoded_content.decode("utf-8")

async def update_file(gh: Github, **kwargs):
    """
    This function updates the contents of a file in a GitHub repository.
    """
    class UpdateFileInput(RepositoryBranchInput):
        path: str = Field(description="The full file path of the file you would like to update where the path must NOT start with a slash, e.g. `some_dir/my_file.py`.")
        content: str = Field(description="The new content of the file to be updated")
        message: str = Field(description="The commit message to be used for the file update")
    input = UpdateFileInput(**kwargs)
    repo = gh.get_repo(input.repository)
    file = repo.get_contents(input.path, ref=input.branch)
    if not file:
        return f"File does not exist at `{input.path}` on branch `{input.branch}`"
    repo.update_file(input.path, input.message, input.content, file.sha, branch=input.branch)
    return f"Updated file {input.path} with message: {input.message} on branch {input.branch}"

async def delete_file(gh: Github, **kwargs):
    """
    This function deletes a file from a GitHub repository.
    """
    class DeleteFileInput(RepositoryBranchInput):
        path: str = Field(description="The full file path of the file you would like to delete where the path must NOT start with a slash, e.g. `some_dir/my_file.py`.")
    input = DeleteFileInput(**kwargs)
    repo = gh.get_repo(input.repository)
    repo.delete_file(input.path, branch=input.branch)
    return f"Deleted file {input.path} from branch {input.branch}"

async def list_files(gh: Github, **kwargs):
    """
    This function lists all files in a GitHub repository.
    """
    class ListFilesInput(RepositoryBranchInput):
        path: str = Field(default="", description="The path to the directory to list the files from, e.g. `some_dir`")
    input = ListFilesInput(**kwargs)
    repo = gh.get_repo(input.repository)
    files = repo.get_contents(path=input.path, ref=input.branch)
    return [file.path for file in files]
