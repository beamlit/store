from typing import Any, Dict

from github import Auth, Github
from langchain_community.utilities.github import GitHubAPIWrapper

import functions.github.kit as kit
from common.bl_config import BL_CONFIG


async def main(body: Dict[str, Any]):
    """
    name: github
    display_name: Github
    kit: true
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
