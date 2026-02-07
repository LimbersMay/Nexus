from models.app_config import ZoneConfig, RootConfig
from file_sorter import FileSorter
from helpers.config_loader import load_config
from helpers.directory_creator import DirectoryCreator
from registry_checker import Auditor
from services.json_config_persister import JsonConfigPersister
from services.notification_service import PlyerNotificationService
from services.ordered_files_repository import ConfigOrderedFilesRepository
from services.path_repository import ConfigPathRepository
from services.settings_repository import ConfigSettingsRepository


def main():
    json_path = "data/settings.json"

    try:
        root_config: RootConfig = load_config(json_path)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return

    global_persister = JsonConfigPersister(json_path, root_config)
    notification_service = PlyerNotificationService()

    for zone_config in root_config.zones:
        path_repository = ConfigPathRepository(zone_config.paths)
        settings_repository = ConfigSettingsRepository(zone_config)
        ordered_files_repository = ConfigOrderedFilesRepository(zone_config, global_persister)

        # 1. Create the directories if they do not exist
        directory_creator = DirectoryCreator(path_repository, settings_repository)
        directory_creator.execute()

        # 2. Check the files
        auditor = Auditor(path_repository, ordered_files_repository, settings_repository, notification_service)
        auditor.check_files()

        # 3. Sort the files
        file_organizer = FileSorter(path_repository, settings_repository, ordered_files_repository,
                                    notification_service)
        file_organizer.sort()


if __name__ == "__main__":
    main()
