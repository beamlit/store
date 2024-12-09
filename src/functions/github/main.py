import os
from typing import Any, Dict

from fastapi import BackgroundTasks, Request
from github import Auth, Github
from langchain_community.utilities.github import GitHubAPIWrapper

import functions.github.kit as kit


async def main(request: Request, body: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    display_name: Github
    description: This function kit is used to perform actions on Github.
    configuration:
    - name: github_token
      display_name: Github Token
      description: Github token
      required: true
    - name: github_repository
      display_name: Repository
      description: Github repository name
      required: false
    """
    github_token = os.getenv("GITHUB_TOKEN", os.getenv("BL_GITHUB_TOKEN_DEV"))
    if not github_token:
        raise ValueError("github_token missing from configuration.")

    mode = body.pop("name")
    modes = {}

    for func_name in dir(kit):
        if not func_name.startswith('_'):
            modes[func_name] = getattr(kit, func_name)
    auth = Auth.Token(github_token)
    gh = Github(auth=auth)
    if mode not in modes:
        raise ValueError(f"Invalid mode: {mode}")
    return await modes[mode](gh, **body)
