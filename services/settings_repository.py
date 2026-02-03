import json
from abc import ABC, abstractmethod
from typing import List

from models.app_config import AppConfig
from models.models import FolderSortingRule, GlobalSettings, FileSortingRule


class SettingsRepository(ABC):

    @abstractmethod
    def get_settings(self) -> GlobalSettings:
        pass

    @abstractmethod
    def get_sorting_rules(self) -> List[FileSortingRule]:
        pass

    @abstractmethod
    def get_default_folder(self) -> str:
        pass

    @abstractmethod
    def get_folder_rules(self) -> List[FolderSortingRule]:
        pass

    @abstractmethod
    def get_app_config(self) -> AppConfig:
        pass

class ConfigSettingsRepository(SettingsRepository):

    def __init__(self, config: AppConfig):
        self.__config = config

    def get_settings(self) -> GlobalSettings:
        return self.__config.settings

    def get_sorting_rules(self) -> List[FileSortingRule]:
        return self.__config.file_rules

    def get_default_folder(self) -> str:
        return self.__config.default_folder

    def get_folder_rules(self) -> List[FolderSortingRule]:
        return self.__config.folder_rules

    def get_app_config(self) -> AppConfig:
        return self.__config