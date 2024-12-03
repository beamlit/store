from typing import Any, Dict

import functions.github.kit as kit
from common.bl_config import BL_CONFIG
from fastapi import BackgroundTasks, Request
from github import Auth, Github
from langchain_community.utilities.github import GitHubAPIWrapper


async def main(request: Request, body: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    displayName: Github
    description: This function kit is used to perform actions on Github.
    configuration:
    - name: github_token
      displayName: Github Token
      description: Github token
      required: true
    - name: github_repository
      displayName: Repository
      description: Github repository name
      required: false
    """
    if "github_token" not in BL_CONFIG:
        raise ValueError("github_token missing from configuration.")

    mode = body.pop("name")
    modes = {}

    for func_name in dir(kit):
        if not func_name.startswith('_'):
            modes[func_name] = getattr(kit, func_name)
    auth = Auth.Token(BL_CONFIG["github_token"])
    gh = Github(auth=auth)
    if mode not in modes:
        raise ValueError(f"Invalid mode: {mode}")
    return await modes[mode](gh, **body)
