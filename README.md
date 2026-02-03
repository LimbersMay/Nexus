# AutomateDownloadsFolder
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/LimbersMay/AutomateDownloadsFolder)](https://github.com/LimbersMay/AutomateDownloadsFolder/releases)

> A Python script to automate your file organization with a powerful rules engine.

## Table of contents
* [General Info](#general-info)
* [Key Features (v3.0)](#key-features-v30)
* [Technologies](#technologies)
* [Prerequisites](#prerequisites)
* [Setup](#setup)
* [Usage](#usage)
* [Settings (v3.0)](#settings-v30)
* [Future Features](#future-features)

## General Info
This project is a Python script to automate the cleaning of your Downloads folder (or any other folder). In my daily life, I download a lot of files and my Downloads folder is always a mess, so I decided to start this project.

This is not just a simple script; it's a powerful automation tool with customizable features:
* Define sorting rules for **files** based on extension or regex.
* **New in v3.0:** Define powerful rules for **folders** based on `glob` or `regex` patterns.
* **New in v3.0:** Set custom lifecycle policies (delete or trash after X days) on a **per-rule basis**.
* **New in v3.0:** Disable lifecycles for specific rules (e.g., keep movies forever).
* Set a maximum file size to ignore large files.
* Get desktop notifications when files are organized or cleaned up.

## Key Features (v3.0)

### 🚀 Folder Rules Engine
Version 3.0 introduces a complete rules engine for **folders**. While file rules move individual files, folder rules act on the folders themselves.

* **Match By:** Use simple `glob` patterns (`Project_*`) or complex `regex` (`.*S\d{2}E\d{2}.*`).
* **Actions:**
    * `move_folder`: Moves the entire folder (and its contents) to a new directory. Perfect for movies, series, or project backups.
    * `process_contents`: Dives *into* the folder, moves all files to a specified directory, and then optionally deletes the now-empty source folder.
    * `ignore`: Skips the folder entirely (e.g., for `node_modules`).

### ⏱️ Per-Rule Lifecycles
The global `daysToKeep` setting is gone. Now, you have fine-grained control over how long to keep items:
* **`defaultLifecycle`:** Set a default policy for any file or folder that doesn't have a specific rule.
* **Override Per Rule:** Add an optional `lifecycle` block to any file rule (`sortingRules`) or folder rule (`folderRules`) to give it a custom expiration.
* **Disable Policy:** Keep items forever by adding `"lifecycle": { "enabled": false }` to the rule.

### 🏗️ Pydantic Validation
The entire `settings.json` file is now loaded and validated by Pydantic. This provides:
* **Robust Error Handling:** The script will fail on launch with a clear error message if your `settings.json` is misconfigured.
* **Automatic `camelCase`:** You can keep using `camelCase` in your JSON, and it will be automatically mapped to `snake_case` in Python.

## Technologies
* Python 3.x
* [Pydantic](https://docs.pydantic.dev/) - For robust data validation and settings management.
* [Send2Trash](https://github.com/hsoft/send2trash) - For safely sending files to the system's trash bin.
* [Plyer](https://github.com/kivy/plyer) - For cross-platform desktop notifications.

## Prerequisites
* Python 3.x
* pip

## Setup
1.  Clone the repository:
    ```sh
    git clone https://github.com/LimbersMay/AutomateDownloadsFolder.git
    ```

2.  Navigate to the project directory:
    ```sh
    cd AutomateDownloadsFolder
    ```

3.  Create a virtual environment (recommended):
    ```sh
    python -m venv venv
    ```

4.  Activate the virtual environment (Linux/macOS):
    ```sh
    source venv/bin/activate
    ```
    Activate the virtual environment (Windows):
    ```sh
    venv\Scripts\activate
    ```

5.  Install the requirements:
    ```sh
    pip install -r requirements.txt
    ```

6.  Rename the `settings.example.json` file to `settings.json` in the `data` folder and configure it (see [Settings](#settings-v30) below).

## Usage
You can run the script manually, create a cron job, or start the script on boot.

### Run Manually
```sh
python main.py
```

### Autorun on Windows (via .exe)
1.  Install PyInstaller:
    ```sh
    pip install pyinstaller
    ```

2.  Create the executable:
    ```sh
    pyinstaller --noconfirm --onefile --windowed --icon "./assets/work.ico" --hidden-import "plyer.platforms.win.notification"  "./main.py"
    ```

3.  Move the `.exe` file from the `dist` folder to the root folder.
4.  Press `Win + R` and type `shell:startup` to open the startup folder.
5.  Create a shortcut to the `.exe` and paste it into the startup folder.
6.  Restart your computer.

### Autorun on Linux (via systemd)
1.  Create a new systemd user service file:
    ```sh
    nano ~/.config/systemd/user/automate_downloads.service
    ```

2.  Paste the following configuration, **updating the paths** to match your system (especially `ExecStart` and `WorkingDirectory`):
    ```ini
    [Unit]
    Description=Automate Downloads Folder Script
    After=network.target

    [Service]
    Type=simple
    # IMPORTANT: Use the Python executable INSIDE your venv
    ExecStart=/home/YOUR_USER/projects/AutomateDownloadsFolder/venv/bin/python /home/YOUR_USER/projects/AutomateDownloadsFolder/main.py
    WorkingDirectory=/home/YOUR_USER/projects/AutomateDownloadsFolder
    Restart=on-failure

    [Install]
    WantedBy=default.target
    ```

3.  Reload the systemd daemon, enable, and start the service:
    ```sh
    systemctl --user daemon-reload
    systemctl --user enable automate_downloads.service
    systemctl --user start automate_downloads.service
    ```

## Settings (v3.0)
The settings are defined in `data/settings.example.json`. The structure has been updated for v3.0.

### Example `settings.example.json`
```json
{
  "paths": {
    "sourcePath": "C:\\Users\\UserName\\Downloads",
    "destinationPath": "C:\\Users\\UserName\\Downloads\\Organized"
  },
  "settings": {
    "maxSizeInMb": 5000
  },
  "fileRules": [
    {
      "patterns": [".pdf"],
      "destinationFolder": "PDF",
      "matchBy": "extension",
      "lifecycle": {
        "enabled": true,
        "action": "trash",
        "daysToKeep": 2
      }
    }
  ],
  "defaultFolder": "Other",
  "folderRules": [
    {
      "ruleName": "Move Series",
      "matchBy": "regex",
      "patterns": [".*S\\d{2}E\\d{2}.*"],
      "action": "process_contents",
      "destinationFolder": "TV/Series",
      "deleteEmptyAfterProcessing": true,
      "lifecycle": {
        "enabled": false
      }
    },
    {
      "ruleName": "Organized",
      "matchBy": "regex",
      "patterns": ["^Organized$"],
      "action": "ignore"
    }
  ],
  "orderedFiles": []
}
```

### Settings Explained

* **`paths`**: Core directories.
    * `sourcePath`: The folder to scan (e.g., your Downloads folder).
    * `destinationPath`: The root folder where organized files/folders will be moved.
* **`settings`**: Global script settings.
    * `maxSizeInMb`: Files larger than this (in MB) will be ignored by the file sorter.
* **`fileRules` (For Files)**: A list of rules for individual files.
    * `patterns`: A list of patterns to match (e.g., `[".pdf"]` or `[".*Gemini.*"]`).
    * `destinationFolder`: The subfolder in `destinationPath` to move files to (e.g., "PDF").
    * `matchBy`: `extension` or `regex`.
    * `lifecycle` (Optional): A policy block to override the default for this rule.
        * `enabled`: `true` or `false`.
        * `action`: `trash` or `delete`.
        * `daysToKeep`: Number of days before action is applied.
* **`defaultFolder`**: The folder name for files that don't match any `fileRules`.
* **`folderRules` (For Folders)**: A list of rules for folders found in `sourcePath`.
    * `ruleName`: A unique name for this rule.
    * `matchBy`: `glob` or `regex`.
    * `patterns`: A list of patterns to match.
    * `action`: `move_folder`, `process_contents`, or `ignore`.
    * `destinationFolder` (Optional): The subfolder in `destinationPath`.
    * `deleteEmptyAfterProcessing` (Optional): If `true`, deletes the original folder after `process_contents`.
    * `lifecycle` (Optional): A policy block to apply to the item.
* **`orderedFiles`**: The audit log/registry of moved items.

## Future Features
* Support for multiple source folders.
* Support for multiple destination folders.
* Migrate data persistence from JSON to SQLite. (This is made easier by the Repository Pattern already in place—just need to create a new repository implementation).