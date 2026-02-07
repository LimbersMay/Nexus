from typing import List

from pydantic import Field

from models.base import CamelCaseModel
from models.models import (
    GlobalSettings,
    OrderedFile,
    PathConfig, SortingRule,
)


class ZoneConfig(CamelCaseModel):
    """
    Represents the entire application configuration for a zone (example: Downloads, Desktop).
    """

    zone_name: str

    paths: PathConfig
    settings: GlobalSettings

    # --- Sorting rules ---
    rules: List[SortingRule]

    # --- Register of ordered files ---
    ordered_files: List[OrderedFile] = []

class RootConfig(CamelCaseModel):
    """
    Represents the root configuration containing multiple zone configurations.
    """
    zones: List[ZoneConfig] = []
