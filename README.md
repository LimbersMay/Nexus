<h1 align="center">Nexus</h1>

<p align="center">
  A rule-based file organization engine for Windows and Linux.<br>
  Define zones, write rules, and let the automation handle the rest.
</p>

<p align="center">
  <a href="https://github.com/LimbersMay/Nexus/releases"><img src="https://img.shields.io/github/v/release/LimbersMay/Nexus?style=flat-square" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/LimbersMay/Nexus?style=flat-square" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square" alt="Python">
</p>

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration Reference](#configuration-reference)
  - [Root Structure](#root-structure)
  - [Zone Object](#zone-object)
  - [Paths Object](#paths-object)
  - [Settings Object](#settings-object)
  - [Rule Object](#rule-object)
  - [Lifecycle Object](#lifecycle-object)
  - [Ordered Files (Internal)](#ordered-files-internal)
- [Handling Strategies](#handling-strategies)
  - [`move`](#move)
  - [`process_contents`](#process_contents)
  - [`ignore`](#ignore)
- [Pattern Matching](#pattern-matching)
  - [By Extension](#by-extension)
  - [By Regex](#by-regex)
  - [By Glob](#by-glob)
- [Lifecycle Policies](#lifecycle-policies)
- [Configuration Examples](#configuration-examples)
  - [Minimal Single-Zone Setup](#minimal-single-zone-setup)
  - [Multi-Zone Production Setup](#multi-zone-production-setup)
- [Running the Application](#running-the-application)
  - [Manual Execution](#manual-execution)
  - [Autorun on Windows (via .exe)](#autorun-on-windows-via-exe)
  - [Autorun on Linux (via systemd)](#autorun-on-linux-via-systemd)
- [Project Structure](#project-structure)
- [Technologies](#technologies)
- [License](#license)

---

## Overview

**Nexus** is a rule-based file organization engine that continuously keeps your directories clean. It scans one or more source directories (*zones*), matches files and folders against user-defined rules, moves them to their designated destinations, and optionally removes them after a configurable retention period.

It was built to solve a simple problem — a messy Downloads folder — but has evolved into a multi-zone automation tool with per-rule lifecycle management, unified pattern matching, Pydantic-validated configuration, and a clean service-oriented architecture.

## Key Features

| Feature | Description |
| --- | --- |
| **Multi-Zone Support** | Monitor and organize multiple directories independently (Downloads, Screenshots, Desktop, etc.). Each zone has its own rules, paths, and lifecycle policies. |
| **Unified Rules Engine** | A single, consistent rule model handles both files and folders. Rules control matching, destination, handling strategy, and lifecycle — all in one place. |
| **Three Handling Strategies** | `move` relocates items, `process_contents` extracts files from folders, and `ignore` skips items entirely. |
| **Flexible Pattern Matching** | Match items by file `extension`, `regex` pattern, or `glob` pattern. Rules are evaluated in declaration order — the first match wins. |
| **Per-Rule Lifecycle Policies** | Configure automatic cleanup (`trash` or `delete`) with custom retention periods on each rule. Disable lifecycle to keep items forever. |
| **Pydantic Validation** | The entire configuration file is validated at startup using Pydantic v2. Misconfigured settings fail fast with clear error messages. |
| **Desktop Notifications** | Receive native OS notifications when files are organized or cleaned up via [Plyer](https://github.com/kivy/plyer). |
| **Audit Registry** | Every moved item with an active lifecycle is tracked in an internal registry (`orderedFiles`). The auditor uses this registry to enforce retention policies on subsequent runs. |
| **Repository Pattern** | All data access is abstracted behind repository interfaces, making it straightforward to swap JSON persistence for SQLite or any other backend. |

## Architecture

On each execution, the application loads the configuration, then processes every zone through a three-stage pipeline:

```
main.py
  │
  ├─ load_config()            → Parses and validates data/settings.json via Pydantic
  │
  └─ For each Zone:
       │
       ├─ 1. DirectoryCreator → Ensures all destination folders declared in rules exist
       │
       ├─ 2. Auditor          → Checks the registry against lifecycle policies
       │                        ├─ Removes expired items (trash or permanent delete)
       │                        ├─ Cleans up stale registry entries (files no longer on disk)
       │                        └─ Registers untracked items found in destination folders
       │
       └─ 3. FileSorter       → Scans the source directory
                                 ├─ Matches each item against rules (first-match wins)
                                 ├─ Applies the handling strategy (move / process_contents / ignore)
                                 ├─ Tracks moved items in the registry (if lifecycle is enabled)
                                 └─ Sends desktop notifications with a summary
```

## Prerequisites

- **Python** 3.10 or higher
- **pip** (included with Python)
- **Git** (to clone the repository)

## Installation

1. **Clone the repository:**

    ```sh
    git clone https://github.com/LimbersMay/Nexus.git
    cd Nexus
    ```

2. **Create and activate a virtual environment:**

    ```sh
    # Create
    python -m venv venv

    # Activate (Windows)
    venv\Scripts\activate

    # Activate (Linux / macOS)
    source venv/bin/activate
    ```

3. **Install dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

4. **Create your configuration file:**

    ```sh
    # Windows
    copy data\settings.example.json data\settings.json

    # Linux / macOS
    cp data/settings.example.json data/settings.json
    ```

5. **Edit `data/settings.json`** to match your directories and desired rules (see [Configuration Reference](#configuration-reference)).

## Quick Start

After installation, the fastest way to get started is to edit the example config with a single zone pointing to your Downloads folder:

```json
{
  "zones": [
    {
      "zoneName": "Downloads",
      "paths": {
        "sourcePath": "C:\\Users\\YourUser\\Downloads",
        "destinationPath": "C:\\Users\\YourUser\\Downloads\\Organized"
      },
      "settings": {
        "maxSizeInMb": 5000
      },
      "rules": [
        {
          "ruleName": "PDF",
          "patterns": [".pdf"],
          "matchBy": "extension",
          "handlingStrategy": "move",
          "destinationFolder": "PDF",
          "lifecycle": {
            "enabled": true,
            "action": "trash",
            "daysToKeep": 7
          }
        },
        {
          "ruleName": "Images",
          "patterns": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
          "matchBy": "extension",
          "handlingStrategy": "move",
          "destinationFolder": "Images",
          "lifecycle": {
            "enabled": true,
            "action": "trash",
            "daysToKeep": 7
          }
        }
      ],
      "orderedFiles": []
    }
  ]
}
```

Then run:

```sh
python main.py
```

All `.pdf` files will be moved to `Downloads\Organized\PDF\`, all images to `Downloads\Organized\Images\`, and after 7 days they will be sent to the trash automatically on the next run.

---

## Configuration Reference

The configuration file is located at `data/settings.json`. It is validated at startup by Pydantic — any structural error will produce a clear and descriptive error message before the application starts.

> **Note:** The JSON file uses `camelCase` keys. Pydantic automatically maps them to `snake_case` internally.

### Root Structure

| Key | Type | Required | Description |
| --- | --- | --- | --- |
| `zones` | `Zone[]` | Yes | An array of zone configurations. Each zone represents an independent source directory to monitor. |

```json
{
  "zones": [ ... ]
}
```

### Zone Object

Each zone is a self-contained unit with its own paths, settings, rules, and audit registry.

| Key | Type | Required | Description |
| --- | --- | --- | --- |
| `zoneName` | `string` | Yes | A unique, human-readable identifier for this zone (e.g., `"Downloads"`, `"Screenshots"`). |
| `paths` | `Paths` | Yes | Source and destination directories for this zone. |
| `settings` | `Settings` | Yes | Global settings that apply to all rules within this zone. |
| `rules` | `Rule[]` | Yes | Ordered list of sorting rules. Evaluated top-to-bottom; **first match wins**. |
| `orderedFiles` | `OrderedFile[]` | Yes | Internal audit registry. Initialize as `[]`. Managed automatically by the application. |

### Paths Object

| Key | Type | Required | Description |
| --- | --- | --- | --- |
| `sourcePath` | `string` | Yes | Absolute path to the directory to scan. Must not be empty. |
| `destinationPath` | `string` | Yes | Absolute path to the root directory where organized items will be placed. Created automatically if it doesn't exist. |

```json
"paths": {
  "sourcePath": "C:\\Users\\YourUser\\Downloads",
  "destinationPath": "C:\\Users\\YourUser\\Downloads\\Organized"
}
```

> **Important:** The `destinationPath` (and any subdirectory of it) is automatically protected from being processed by the sorter to prevent recursive loops.

### Settings Object

| Key | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `maxSizeInMb` | `integer` | Yes | — | Maximum file size in megabytes. Files exceeding this limit are skipped entirely by the file sorter. Set a high value (e.g., `10000`) to effectively disable this filter. |

```json
"settings": {
  "maxSizeInMb": 5000
}
```

### Rule Object

Rules are the core of the configuration. Each rule defines **what** to match, **where** to put it, **how** to handle it, and **when** to clean it up.

| Key | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `ruleName` | `string` | Yes | — | A unique identifier for this rule. Used in the audit registry to track which rule was applied to each item. |
| `patterns` | `string[]` | Yes | — | A list of patterns to try. Behavior depends on the `matchBy` strategy (see [Pattern Matching](#pattern-matching)). |
| `matchBy` | `string` | Yes | — | Pattern matching strategy: `"extension"`, `"regex"`, or `"glob"`. |
| `handlingStrategy` | `string` | No | `"move"` | What to do with matched items: `"move"`, `"process_contents"`, or `"ignore"` (see [Handling Strategies](#handling-strategies)). |
| `destinationFolder` | `string\|null` | No | `null` | Subfolder within `destinationPath` to place matched items. Supports nested paths (e.g., `"TV\\Series"`). Required for `move` and `process_contents` strategies. Use `"."` to place items directly in the destination root. |
| `lifecycle` | `Lifecycle\|null` | No | `null` | Retention policy for matched items. If `null` or omitted, no lifecycle tracking is applied — items are moved but never automatically cleaned up. |
| `deleteEmptyAfterProcessing` | `boolean` | No | `false` | Only applies to `process_contents` strategy. If `true`, the original folder is sent to the trash after its contents are extracted. |

```json
{
  "ruleName": "PDF",
  "patterns": [".pdf"],
  "matchBy": "extension",
  "handlingStrategy": "move",
  "destinationFolder": "PDF",
  "lifecycle": {
    "enabled": true,
    "action": "trash",
    "daysToKeep": 7
  }
}
```

> **Rule evaluation order matters.** Rules are evaluated top-to-bottom. The first rule whose pattern matches the item name is applied. Place more specific rules (like ignore rules or regex-based rules) **before** broader catch-all rules.

### Lifecycle Object

| Key | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `enabled` | `boolean` | No | `true` | Whether lifecycle management is active for this rule. Set to `false` to keep matched items forever. |
| `action` | `string` | No | `"trash"` | Action to perform when the retention period expires: `"trash"` (send to recycle bin via Send2Trash) or `"delete"` (permanent deletion). |
| `daysToKeep` | `integer` | No | `30` | Number of days after organization before the item is cleaned up. |

### Ordered Files (Internal)

The `orderedFiles` array in each zone is the **audit registry**. It is managed entirely by the application — you should not edit it manually. When a file is moved and its associated rule has an active lifecycle, an entry is added:

```json
{
  "name": "report.pdf",
  "orderedDate": "2026-02-07",
  "path": "C:\\Users\\YourUser\\Downloads\\Organized\\PDF\\report.pdf",
  "ruleNameApplied": "PDF"
}
```

On each run, the **Auditor** reads this registry, compares dates against the lifecycle policy of the applied rule, and removes expired items. Entries for files that no longer exist on disk are automatically cleaned from the registry.

---

## Handling Strategies

### `move`

Moves the matched item (file **or** folder) directly into `destinationPath/destinationFolder/`. The item retains its original name.

```
Source:  Downloads/report.pdf
Rule:    destinationFolder = "PDF", handlingStrategy = "move"
Result:  Downloads/Organized/PDF/report.pdf
```

### `process_contents`

Designed for folders. Recursively extracts all files from the matched folder, processes each one individually through the rule engine, and optionally deletes the now-empty source folder.

This is ideal for downloaded archives that extract into named folders (e.g., TV series or movie torrents):

```
Source:  Downloads/Breaking.Bad.S01E01.720p/
           ├─ Breaking.Bad.S01E01.720p.mkv
           └─ subtitles.srt
Rule:    destinationFolder = "TV/Series", handlingStrategy = "process_contents",
         deleteEmptyAfterProcessing = true
Result:  Downloads/Organized/TV/Series/episode.mkv
         Downloads/Organized/Other/subtitles.srt
         (source folder is sent to trash)
```

### `ignore`

The item is skipped entirely. No movement, no tracking, no lifecycle. Useful for:

- Folders you want to preserve in the source directory (e.g., `Temporal`, `node_modules`)
- Files currently being downloaded (`.crdownload`, `.part`, `.tmp`)
- Any item that should never be touched by the automation

```json
{
  "ruleName": "IgnoreUnfinishedDownloads",
  "patterns": ["(?i).*\\.crdownload$", "(?i).*\\.part$", "(?i).*\\.tmp$"],
  "matchBy": "regex",
  "handlingStrategy": "ignore"
}
```

---

## Pattern Matching

The `matchBy` field determines how the `patterns` array is interpreted. Matching is always performed against the **item's name** (file name with extension, or folder name).

### By Extension

Matches the file extension (including the leading dot). Case-insensitive comparison.

```json
{
  "matchBy": "extension",
  "patterns": [".pdf", ".doc", ".docx"]
}
```

> Extension matching only applies to files. Folders don't have extensions.

### By Regex

Matches the full item name against a Python-compatible regular expression using `re.match()` (anchored to the start of the name).

```json
{
  "matchBy": "regex",
  "patterns": ["(?i).*Gemini.*", ".*S\\d{2}E\\d{2}.*"]
}
```

Common regex patterns:

| Pattern | Matches |
| --- | --- |
| `".*"` | Everything (catch-all) |
| `"^Temporal$"` | Exactly the name `Temporal` |
| `"(?i).*\\.crdownload$"` | Any `.crdownload` file (case-insensitive) |
| `".*S\\d{2}E\\d{2}.*"` | TV series episodes (e.g., `Show.S01E05.mkv`) |
| `"(?i).*[\\. _\\-](19\|20)\\d{2}[\\. _\\-].*(1080p\|720p).*"` | Movies with year and quality tags |

### By Glob

Matches the item name using shell-style wildcards via Python's `fnmatch`.

```json
{
  "matchBy": "glob",
  "patterns": ["Project_*", "backup_????-??-??"]
}
```

| Pattern | Matches |
| --- | --- |
| `"*"` | Everything |
| `"Project_*"` | Any name starting with `Project_` |
| `"*.log"` | Any name ending with `.log` |
| `"backup_????-??-??"` | Names like `backup_2026-02-07` |

---

## Lifecycle Policies

Lifecycle policies automate the cleanup of organized items. They are configured **per rule**, giving you complete control over retention periods.

**How it works:**

1. When a file is moved and its rule has `lifecycle.enabled = true`, the application records the item in the zone's `orderedFiles` registry along with the current date and the rule name.
2. On subsequent runs, the **Auditor** checks every registered item against the lifecycle policy of its applied rule.
3. If `(today - orderedDate) > daysToKeep`, the configured action is executed:
   - `"trash"` — Sends the item to the system's recycle bin (recoverable).
   - `"delete"` — Permanently removes the item from disk.

**Disabling lifecycle for a rule:**

To keep matched items forever (e.g., movies, important archives), either:

- Set `"lifecycle": { "enabled": false }` — Items are moved but never cleaned up.
- Set `"lifecycle": null` or omit the field entirely — Same behavior; items are not tracked.

**Untracked items in destination folders:**

The Auditor also scans destination folders for items that exist on disk but are not yet in the registry. If those items belong to a folder associated with a rule that has an active lifecycle, they are automatically registered with today's date. This ensures that items placed in destination folders by external means are still subject to cleanup.

---

## Configuration Examples

### Minimal Single-Zone Setup

A basic configuration that organizes Downloads into categories with 7-day retention:

```json
{
  "zones": [
    {
      "zoneName": "Downloads",
      "paths": {
        "sourcePath": "C:\\Users\\YourUser\\Downloads",
        "destinationPath": "C:\\Users\\YourUser\\Downloads\\Organized"
      },
      "settings": {
        "maxSizeInMb": 5000
      },
      "rules": [
        {
          "ruleName": "Images",
          "patterns": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"],
          "matchBy": "extension",
          "handlingStrategy": "move",
          "destinationFolder": "Images",
          "lifecycle": { "enabled": true, "action": "trash", "daysToKeep": 7 }
        },
        {
          "ruleName": "Documents",
          "patterns": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"],
          "matchBy": "extension",
          "handlingStrategy": "move",
          "destinationFolder": "Documents",
          "lifecycle": { "enabled": true, "action": "trash", "daysToKeep": 14 }
        },
        {
          "ruleName": "CatchAll",
          "patterns": [".*"],
          "matchBy": "regex",
          "handlingStrategy": "move",
          "destinationFolder": "Other",
          "lifecycle": { "enabled": true, "action": "trash", "daysToKeep": 3 }
        }
      ],
      "orderedFiles": []
    }
  ]
}
```

### Multi-Zone Production Setup

An advanced configuration monitoring three separate directories, each with specialized rules:

```json
{
  "zones": [
    {
      "zoneName": "Screenshots",
      "paths": {
        "sourcePath": "C:\\Users\\YourUser\\Pictures\\Screenshots",
        "destinationPath": "C:\\Users\\YourUser\\Downloads\\Organized\\Screenshots"
      },
      "settings": { "maxSizeInMb": 5000 },
      "rules": [
        {
          "ruleName": "Default",
          "patterns": [".*"],
          "matchBy": "regex",
          "handlingStrategy": "move",
          "destinationFolder": "Archive",
          "lifecycle": { "enabled": true, "action": "trash", "daysToKeep": 7 }
        }
      ],
      "orderedFiles": []
    },
    {
            "zoneName": "ClipboardInbox",
            "paths": {
                "sourcePath": "C:\\Users\\UserName\\Documents\\ClipboardImageAutomaticSaver\\Clipboard_Inbox",
                "destinationPath": "C:\\Users\\UserName\\Downloads\\Organized\\ClipboardInbox"
            },
            "settings": {
                "maxSizeInMb": 5000
            },
            "rules": [
                {
                    "ruleName": "SocialMedia",
                    "patterns": [
                        "(?i).*\\[.*Facebook.*\\].*",
                        "(?i).*\\[.*Twitter.*\\].*",
                        "(?i).*\\[.*Reddit.*\\].*"
                    ],
                    "lifecycle": {
                        "enabled": true,
                        "action": "trash",
                        "daysToKeep": 7
                    },
                    "destinationFolder": "SocialMedia",
                    "matchBy": "regex",
                    "handlingStrategy": "move",
                    "deleteEmptyAfterProcessing": false
                },
                {
                    "ruleName": "Default",
                    "patterns": [
                        ".*"
                    ],
                    "lifecycle": {
                        "enabled": true,
                        "action": "trash",
                        "daysToKeep": 7
                    },
                    "destinationFolder": "Other",
                    "matchBy": "regex",
                    "handlingStrategy": "move",
                    "deleteEmptyAfterProcessing": false
                }
            ],
            "orderedFiles": []
        },
    {
      "zoneName": "Downloads",
      "paths": {
        "sourcePath": "C:\\Users\\YourUser\\Downloads",
        "destinationPath": "C:\\Users\\YourUser\\Downloads\\Organized\\Downloads"
      },
      "settings": { "maxSizeInMb": 10000 },
      "rules": [
        {
          "ruleName": "IgnoreUnfinishedDownloads",
          "patterns": ["(?i).*\\.crdownload$", "(?i).*\\.part$", "(?i).*\\.tmp$"],
          "matchBy": "regex",
          "handlingStrategy": "ignore"
        },
        {
          "ruleName": "IgnoreTemporal",
          "patterns": ["^Temporal$"],
          "matchBy": "regex",
          "handlingStrategy": "ignore"
        },
        {
          "ruleName": "TvSeries",
          "patterns": [".*S\\d{2}E\\d{2}.*"],
          "matchBy": "regex",
          "handlingStrategy": "process_contents",
          "destinationFolder": "TV\\Series",
          "deleteEmptyAfterProcessing": true,
          "lifecycle": { "enabled": false }
        },
        {
          "ruleName": "TvMovies",
          "patterns": ["(?i).*[\\. _\\-\\(\\[](19|20)\\d{2}[\\. _\\-\\)\\]].*(1080p|720p|2160p|4k).*"],
          "matchBy": "regex",
          "handlingStrategy": "process_contents",
          "destinationFolder": "TV\\Movies",
          "deleteEmptyAfterProcessing": true,
          "lifecycle": { "enabled": false }
        },
        {
          "ruleName": "PDF",
          "patterns": [".pdf"],
          "matchBy": "extension",
          "handlingStrategy": "move",
          "destinationFolder": "PDF",
          "lifecycle": { "enabled": true, "action": "trash", "daysToKeep": 7 }
        },
        {
          "ruleName": "Images",
          "patterns": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp"],
          "matchBy": "extension",
          "handlingStrategy": "move",
          "destinationFolder": "Images",
          "lifecycle": { "enabled": true, "action": "trash", "daysToKeep": 7 }
        },
        {
          "ruleName": "Video",
          "patterns": [".mp4", ".mkv", ".avi", ".mov", ".wmv"],
          "matchBy": "extension",
          "handlingStrategy": "move",
          "destinationFolder": "Video",
          "lifecycle": { "enabled": true, "action": "trash", "daysToKeep": 3 }
        },
        {
          "ruleName": "CatchAll",
          "patterns": [".*"],
          "matchBy": "regex",
          "handlingStrategy": "process_contents",
          "destinationFolder": "Other",
          "deleteEmptyAfterProcessing": true,
          "lifecycle": { "enabled": true, "action": "trash", "daysToKeep": 3 }
        }
      ],
      "orderedFiles": []
    }
  ]
}
```

> **Tip:** The `CatchAll` rule at the bottom ensures that nothing is left behind in the source directory. Place it always as the **last** rule.

---

## Running the Application

### Manual Execution

```sh
python main.py
```

The application runs once through all zones and exits. Ideal for testing your configuration or running via a scheduled task.

### Autorun on Windows (via .exe)

1. **Install PyInstaller:**

    ```sh
    pip install pyinstaller
    ```

2. **Build the executable:**

    ```sh
    pyinstaller --noconfirm --onefile --windowed --icon "./assets/work.ico" --hidden-import "plyer.platforms.win.notification" "./main.py"
    ```

3. **Move** the generated `dist/main.exe` to the project root folder.

4. **Create a startup shortcut:**
   - Press <kbd>Win</kbd> + <kbd>R</kbd>, type `shell:startup`, and press Enter.
   - Create a shortcut to `main.exe` and place it in the startup folder.

5. **Restart** your computer. The application will run silently on every login.

> **Alternatively**, you can use Windows Task Scheduler for more control over execution frequency and conditions.

### Autorun on Linux (via systemd)

1. **Create a systemd user service:**

    ```sh
    mkdir -p ~/.config/systemd/user
    nano ~/.config/systemd/user/automate_downloads.service
    ```

2. **Paste the following** (update paths to match your system):

    ```ini
    [Unit]
    Description=Automate Downloads Folder
    After=network.target

    [Service]
    Type=simple
    ExecStart=/home/YOUR_USER/Nexus/venv/bin/python /home/YOUR_USER/Nexus/main.py
    WorkingDirectory=/home/YOUR_USER/Nexus
    Restart=on-failure

    [Install]
    WantedBy=default.target
    ```

3. **Enable and start the service:**

    ```sh
    systemctl --user daemon-reload
    systemctl --user enable automate_downloads.service
    systemctl --user start automate_downloads.service
    ```

4. **Check status:**

    ```sh
    systemctl --user status automate_downloads.service
    ```

---

## Project Structure

```
Nexus/
├── main.py                         # Entry point — loads config and runs the pipeline
├── file_sorter.py                  # FileSorter — scans source, matches rules, moves items
├── registry_checker.py             # Auditor — enforces lifecycle policies and cleans registry
├── requirements.txt                # Python dependencies
├── main.spec                       # PyInstaller build specification
│
├── data/
│   ├── settings.example.json       # Example configuration (copy to settings.json)
│   └── settings.json               # Your active configuration (git-ignored)
│
├── models/
│   ├── base.py                     # CamelCaseModel — Pydantic base with camelCase aliasing
│   ├── models.py                   # Domain models (SortingRule, LifecyclePolicy, PathConfig, etc.)
│   └── app_config.py               # ZoneConfig and RootConfig (top-level config models)
│
├── services/
│   ├── path_repository.py          # PathRepository interface + Config implementation
│   ├── settings_repository.py      # SettingsRepository interface + Config implementation
│   ├── ordered_files_repository.py # OrderedFilesRepository interface + Config implementation
│   ├── json_config_persister.py    # JsonConfigPersister — serializes config back to JSON
│   └── notification_service.py     # NotificationService interface + Plyer implementation
│
├── helpers/
│   ├── config_loader.py            # load_config() — reads and validates settings.json
│   └── directory_creator.py        # DirectoryCreator — ensures destination folders exist
│
└── assets/
    └── work.ico                    # Application icon
```

## Technologies

| Dependency | Version | Purpose |
| --- | --- | --- |
| [Pydantic](https://docs.pydantic.dev/) | 2.12+ | Configuration validation, serialization, and camelCase aliasing |
| [Send2Trash](https://github.com/hsoft/send2trash) | 1.8+ | Safe file deletion via the system's recycle bin |
| [Plyer](https://github.com/kivy/plyer) | 2.1+ | Cross-platform desktop notifications |
| [dbus-python](https://dbus.freedesktop.org/doc/dbus-python/) | 1.3+ | D-Bus bindings for Linux notifications (Linux only) |

## License

This project is licensed under the [MIT License](LICENSE).

---

<p align="center">
  Made by <a href="https://github.com/LimbersMay">LimbersMay</a>
</p>