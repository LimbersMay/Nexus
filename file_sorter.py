import datetime
import fnmatch
import os
import pathlib
import re
import shutil
from typing import List, Optional

from models.models import FolderSortingRule, OrderedFile, FileSortingRule
from services.ordered_files_repository import OrderedFilesRepository
from services.path_repository import PathRepository
from services.settings_repository import SettingsRepository
from services.notification_service import NotificationService


class FileSorter:
    def __init__(self, path_repository: PathRepository,
                 settings_repository: SettingsRepository,
                 ordered_files_repository: OrderedFilesRepository,
                 notificator_service: NotificationService):

        self.__path_repository = path_repository
        self.__settings_repository = settings_repository
        self.__ordered_files_repository = ordered_files_repository
        self.__notification_service = notificator_service

        settings = settings_repository.get_settings()

        self.__source_path = path_repository.get_source_path()
        self.__destination_path = path_repository.get_destination_path()

        # Files config
        self.__size_limit = settings.max_size_in_mb
        self.__file_rules = settings_repository.get_sorting_rules()
        self.__default_folder = settings_repository.get_default_folder()

        # Folder config
        self.__folder_rules = self.__settings_repository.get_folder_rules()

        # Track list
        self.__newly_tracked_items: List[OrderedFile] = []

        # For files/folders moved but not tracked, for notification purposes
        self.__untracked_items_counter = 0


    def sort(self):
        # 1. Clean up the newly tracked items list
        self.__newly_tracked_items = []
        self.__untracked_items_counter = 0

        source_path = self.__path_repository.get_source_path()

        # 2. Iterate through items in the source path
        for item in source_path.iterdir():
            if item.is_file():
                self.__process_file(item)
            elif item.is_dir():
                self.__process_folder(item)

        # 3. Save newly tracked items
        if self.__newly_tracked_items:
            self.__ordered_files_repository.save_ordered_files(self.__newly_tracked_items)
            self.__notification_service.send_notification(f"{len(self.__newly_tracked_items)} files were sorted")

        if self.__untracked_items_counter > 0:
            self.__notification_service.send_notification(f"{self.__untracked_items_counter} items were moved but not tracked")

    def __process_file(self, file_path: pathlib.Path):
        """
        Process a single file: determine its destination folder, move it, and track it.
        1. Check the file size.
        2. Find the rule that matches the file.
        3. Move the file to the destination folder.
        4. Track the file.

        :param file_path: Path of the file to process.
        :return: None

        """

        # 1. Check if file exists
        if not file_path.exists():
            return

        # 2. Check file size
        if file_path.stat().st_size >= (self.__size_limit * 1024 * 1024):
            return

        # 3. Find destination folder and rule
        item_rule = self.__find_matching_file_rule(file_path.name)

        destination_folder_name = item_rule.destination_folder if item_rule else self.__default_folder

        # 4. Create destination path and move file
        destination_folder_path = self.__destination_path / destination_folder_name
        destination_folder_path.mkdir(parents=True, exist_ok=True)
        final_file_path = destination_folder_path / file_path.name

        try:
            shutil.move(str(file_path), str(final_file_path))

            # 5. Track the moved file if lifecycle is enabled
            has_active_lifecycle = item_rule and item_rule.lifecycle and item_rule.lifecycle.enabled

            if not has_active_lifecycle:
                self.__untracked_items_counter += 1
                return

            items_to_track = OrderedFile(
                name=file_path.name,
                ordered_date=datetime.datetime.now().date(),
                path=str(final_file_path),
                rule_name_applied=destination_folder_name,
            )

            self.__newly_tracked_items.append(items_to_track)

        except Exception as e:
            print(f"Error moving file {file_path} to {final_file_path}: {e}")

    def __process_folder(self, folder_path: pathlib.Path):
        rule = self.__find_matching_folder_rule(folder_path.name)
        action = rule.action

        if action == 'ignore':
            return

        elif action == 'process_contents':

            # 1. Validate destination folder
            if not rule or not rule.destination_folder:
                return

            destination_folder_path = self.__destination_path / rule.destination_folder
            destination_folder_path.mkdir(parents=True, exist_ok=True)

            # 2. Process each file in the folder
            for sub_item in folder_path.rglob('*'):
                if sub_item.is_file():
                    final_file_path = destination_folder_path / sub_item.name
                    try:
                        shutil.move(str(sub_item), str(final_file_path))

                        # Track the moved file if lifecycle is enabled
                        if rule.lifecycle and rule.lifecycle.enabled:
                            items_to_track = OrderedFile(
                                name=sub_item.name,
                                ordered_date=datetime.datetime.now().date(),
                                path=str(final_file_path),
                                rule_name_applied=rule.rule_name,
                            )

                            self.__newly_tracked_items.append(items_to_track)

                        else:
                            self.__untracked_items_counter += 1

                    except Exception as e:
                        print(f"Error moving file {sub_item} to {final_file_path}: {e}")

            # 3. Delete the empty folder if specified
            if rule and rule.delete_empty_after_processing:
                try:
                    shutil.rmtree(folder_path)
                except Exception as e:
                    print(f"Error deleting non-empty folder {folder_path}: {e}")

        elif action == 'move':
            destination_base = self.__path_repository.get_destination_path()
            destination_folder = rule.destination_folder if rule.destination_folder else 'Folders'

            final_destination_path = destination_base / destination_folder / folder_path.name

            # Ensure the destination folder exists
            (destination_base / destination_folder).mkdir(exist_ok=True, parents=True)

            folder_path.rename(final_destination_path)

            try:
                shutil.move(str(folder_path), str(final_destination_path))
                if rule and rule.lifecycle and rule.lifecycle.enabled:
                    items_to_track = OrderedFile(
                        name=folder_path.name,
                        ordered_date=datetime.datetime.now().date(),
                        path=str(final_destination_path),
                        rule_name_applied=action,
                    )
                    self.__newly_tracked_items.append(items_to_track)

                else:
                    self.__untracked_items_counter += 1
            except Exception as e:
                print(f"Error moving folder {folder_path} to {final_destination_path}: {e}")


    def __find_matching_file_rule(self, file_name: str) -> Optional[FileSortingRule]:
        """
        Find the sorting rule that matches the given file name.
        """
        _, extension = os.path.splitext(file_name)

        for rule in self.__file_rules:
            if rule.match_by == "extension":
                if extension.lower() in [p.lower() for p in rule.patterns]:
                    return rule
            elif rule.match_by == "regex":
                for pattern in rule.patterns:
                    if re.match(pattern, file_name):
                        return rule
        return None

    def __find_matching_folder_rule(self, folder_name: str) -> FolderSortingRule | None:
        for rule in self.__folder_rules:
            for pattern in rule.patterns:
                if rule.match_by == 'glob':
                    if fnmatch.fnmatch(folder_name, pattern):
                        return rule
                elif rule.match_by == 'regex':
                    if re.match(pattern, folder_name):
                        return rule
        return None