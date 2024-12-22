import os

from pydantic import BaseModel, Field, field_validator

repository = os.getenv("GITHUB_REPOSITORY", os.getenv("BL_GITHUB_REPOSITORY"))

class RepositoryInput(BaseModel):
    repository: str = Field(
        default=repository,
        description="The name of the repository to fetch issues from.",
        validate_default=True,
    )

    @field_validator("repository", mode="before")
    @classmethod
    def repository_not_null(cls, v):
        if not v:
            raise ValueError("Repository is required")
        return v


class RepositoryBranchInput(RepositoryInput):
    branch: str = Field(
        default="main",
        description="The branch to perform the action on.",
    )
