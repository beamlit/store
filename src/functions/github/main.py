import os
from typing import Any, Dict

from beamlit.common.instrumentation import get_tracer
from github import Auth, Github

import functions.github.kit as kit


async def main(
    body: Dict[str, Any],
    headers=None,
    query_params=None,
    **_
):
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
    with get_tracer().start_as_current_span("github") as span:
        mode = body.pop("name")
        modes = {}
        span.set_attribute("name", mode)

        github_token = os.getenv("GITHUB_TOKEN", os.getenv("BL_GITHUB_TOKEN_DEV"))
        if not github_token:
            raise ValueError("github_token missing from configuration.")

        for func_name in dir(kit):
            if not func_name.startswith('_'):
                modes[func_name] = getattr(kit, func_name)
        auth = Auth.Token(github_token)
        gh = Github(auth=auth)
        if mode not in modes:
            raise ValueError(f"Invalid mode: {mode}")
        return await modes[mode](gh, **body)
