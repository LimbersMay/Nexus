import datetime
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from models.app_config import ZoneConfig
from models.models import OrderedFile
from services.json_config_persister import JsonConfigPersister


class OrderedFilesRepository(ABC):
    @abstractmethod
    def get_ordered_files(self) -> List[OrderedFile]:
        pass

    @abstractmethod
    def get_files_to_delete(self, days_to_keep: int) -> List[OrderedFile]:
        pass

    @abstractmethod
    def save_ordered_files(self, new_ordered_files: List[OrderedFile]) -> None:
        pass

    @abstractmethod
    def find(self, file_name: str) -> Optional[OrderedFile]:
        pass

    @abstractmethod
    def delete(self, file_name: str) -> None:
        pass

class ConfigOrderedFilesRepository(OrderedFilesRepository):
    def __init__(self, zone_config: ZoneConfig, persister: JsonConfigPersister):
        self.__zone_config = zone_config
        self.__persister = persister

        self.__ordered_files = zone_config.ordered_files

    def get_ordered_files(self) -> List[OrderedFile]:
        return self.__ordered_files

    def save_ordered_files(self, new_ordered_files: List[OrderedFile]) -> None:
        self.__ordered_files.extend(new_ordered_files)
        self.__zone_config.ordered_files = self.__ordered_files
        self.__persister.save()

    def find(self, file_name: str) -> OrderedFile | None:
        for ordered_file in self.__ordered_files:
            if ordered_file.name == file_name:
                return ordered_file
        return None

    def delete(self, file_name: str) -> None:
        file_to_remove = self.find(file_name)
        if file_to_remove:
            self.__ordered_files.remove(file_to_remove)
            self.__zone_config.ordered_files = self.__ordered_files
            self.__persister.save()

    def get_files_to_delete(self, days_to_keep: int) -> List[OrderedFile]:
        files_to_delete = []
        current_date = datetime.now().date()

        for ordered_file in self.__ordered_files:
            if (current_date - ordered_file.ordered_date).days > days_to_keep:
                files_to_delete.append(ordered_file)

        return files_to_delete
