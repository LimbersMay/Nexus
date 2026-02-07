import json
from abc import ABC, abstractmethod
from typing import List

from models.app_config import ZoneConfig
from models.models import SortingRule, GlobalSettings


class SettingsRepository(ABC):

    @abstractmethod
    def get_settings(self) -> GlobalSettings:
        pass

    @abstractmethod
    def get_sorting_rules(self) -> List[SortingRule]:
        pass

    @abstractmethod
    def get_app_config(self) -> ZoneConfig:
        pass

class ConfigSettingsRepository(SettingsRepository):

    def __init__(self, config: ZoneConfig):
        self.__config = config

    def get_settings(self) -> GlobalSettings:
        return self.__config.settings

    def get_sorting_rules(self) -> List[SortingRule]:
        return self.__config.rules

    def get_app_config(self) -> ZoneConfig:
        return self.__config