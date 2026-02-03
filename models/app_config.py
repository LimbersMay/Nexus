from typing import List, Literal

from pydantic import Field

from models.base import CamelCaseModel
from models.models import (
    FolderSortingRule,
    GlobalSettings,
    LifecyclePolicy,
    OrderedFile,
    PathConfig,
    FileSortingRule,
)


class AppConfig(CamelCaseModel):
    """Application configuration model."""

    paths: PathConfig
    settings: GlobalSettings = Field(alias='settings')

    # --- Rules for files ---
    file_rules: List[FileSortingRule]
    default_folder: str = "Other"

    # --- Rules for folders ---
    folder_rules: List[FolderSortingRule] = []

    # --- Register of ordered files ---
    ordered_files: List[OrderedFile] = []
