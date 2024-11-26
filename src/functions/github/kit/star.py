from github import Github

from functions.github.models import RepositoryInput


async def set_star(gh: Github, **kwargs):
    """
    Stars a GitHub repository.
    """
    class StarInput(RepositoryInput):
        pass

    input = StarInput(**kwargs)
    repo = gh.get_repo(input.repository)
    gh.get_user().add_to_starred(repo)
    return f"Successfully starred repository {input.repository}"


async def get_star(gh: Github, **kwargs):
    """
    Get the star count for a GitHub repository.
    """
    class StarInput(RepositoryInput):
        pass

    input = StarInput(**kwargs)
    repo = gh.get_repo(input.repository)
    return f"Star count for repository: {repo.stargazers_count}"
