from typing import Any, Dict

from langchain_community.utilities.github import GitHubAPIWrapper

from common.bl_config import BL_CONFIG


async def main(body: Dict[str, Any]):
    if "github_repository" not in BL_CONFIG:
        raise ValueError("github_repository missing from configuration.")
    if "github_app_id" not in BL_CONFIG:
        raise ValueError("github_app_id missing from configuration.")
    if "github_app_private_key" not in BL_CONFIG:
        raise ValueError("github_app_private_key missing from configuration.")

    config = {
        "github_repository": BL_CONFIG["github_repository"],
        "github_app_id": BL_CONFIG["github_app_id"],
        "github_app_private_key": BL_CONFIG["github_app_private_key"],
        "github_base_branch": BL_CONFIG.get("github_base_branch", None),
        "active_branch": BL_CONFIG.get("active_branch", None),
    }

    api = GitHubAPIWrapper(**config)
    mode = body.pop("name")
    if len(body.keys()) > 1 or len(body.keys()) == 0:
        raise ValueError(f"Expected one argument in function schema, got {body.keys()}.")
    query = str(list(body.values())[0])
    return api.run(mode, query)
