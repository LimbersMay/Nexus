<h1 align="center">Nexus</h1>

<p align="center">
  Motor de organización de archivos basado en reglas para Windows y Linux.<br>
  Define zonas, escribe reglas y deja que la automatización haga el resto.
</p>

<p align="center">
  <a href="https://github.com/LimbersMay/Nexus/releases"><img src="https://img.shields.io/github/v/release/LimbersMay/Nexus?style=flat-square" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/LimbersMay/Nexus?style=flat-square" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square" alt="Python">
</p>

---

## Tabla de Contenidos

- [Visión General](#visión-general)
- [Características Clave](#características-clave)
- [Arquitectura](#arquitectura)
- [Prerequisitos](#prerequisitos)
- [Instalación](#instalación)
- [Inicio Rápido](#inicio-rápido)
- [Referencia de Configuración](#referencia-de-configuración)
  - [Estructura Raíz](#estructura-raíz)
  - [Objeto Zona](#objeto-zona)
  - [Objeto Paths](#objeto-paths)
  - [Objeto Settings](#objeto-settings)
  - [Objeto Rule](#objeto-rule)
  - [Objeto Lifecycle](#objeto-lifecycle)
  - [Ordered Files (Interno)](#ordered-files-interno)
- [Estrategias de Manejo](#estrategias-de-manejo)
  - [`move`](#move)
  - [`process_contents`](#process_contents)
  - [`ignore`](#ignore)
- [Coincidencia de Patrones](#coincidencia-de-patrones)
  - [Por Extensión](#por-extensión)
  - [Por Regex](#por-regex)
  - [Por Glob](#por-glob)
- [Políticas de Ciclo de Vida](#políticas-de-ciclo-de-vida)
- [Ejemplos de Configuración](#ejemplos-de-configuración)
  - [Configuración Mínima de una Zona](#configuración-mínima-de-una-zona)
  - [Configuración Multi-Zona de Producción](#configuración-multi-zona-de-producción)
- [Ejecución de la Aplicación](#ejecución-de-la-aplicación)
  - [Ejecución Manual](#ejecución-manual)
  - [Inicio Automático en Windows (vía .exe)](#inicio-automático-en-windows-vía-exe)
  - [Inicio Automático en Linux (vía systemd)](#inicio-automático-en-linux-vía-systemd)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Tecnologías](#tecnologías)
- [Licencia](#licencia)

---

## Visión General

**Nexus** es un motor de organización basado en reglas que mantiene tus directorios limpios de forma continua. Escanea uno o varios directorios de origen (*zonas*), compara archivos y carpetas contra reglas definidas por el usuario, mueve cada elemento a su destino y, opcionalmente, lo elimina tras un periodo de retención configurable.

Nació para resolver un problema sencillo —una carpeta de Descargas desordenada— y evolucionó hacia una herramienta multi-zona con gestión de ciclo de vida por regla, coincidencia de patrones flexible, configuración validada con Pydantic y una arquitectura orientada a servicios.

## Características Clave

| Característica | Descripción |
| --- | --- |
| **Soporte Multi-Zona** | Supervisa y organiza múltiples directorios de forma independiente (Descargas, Screenshots, Escritorio, etc.). Cada zona tiene sus propias reglas, rutas y políticas de ciclo de vida. |
| **Motor de Reglas Unificado** | Un único modelo gestiona archivos y carpetas. Las reglas controlan coincidencias, destino, estrategia de manejo y ciclo de vida en un solo lugar. |
| **Tres Estrategias de Manejo** | `move` reubica ítems, `process_contents` extrae contenidos de carpetas y `ignore` omite elementos. |
| **Coincidencia de Patrones Flexible** | Coincide por `extension`, `regex` o `glob`. Las reglas se evalúan en orden: la primera coincidencia gana. |
| **Ciclos de Vida por Regla** | Limpieza automática (`trash` o `delete`) con retención personalizada en cada regla. Desactiva el ciclo para conservar elementos indefinidamente. |
| **Validación Pydantic** | Toda la configuración se valida al inicio con Pydantic v2. Los errores fallan rápido con mensajes claros. |
| **Notificaciones de Escritorio** | Recibe notificaciones nativas cuando se organizan o limpian archivos mediante [Plyer](https://github.com/kivy/plyer). |
| **Registro de Auditoría** | Cada ítem movido con ciclo de vida activo se rastrea en `orderedFiles`. El auditor hace cumplir la retención en ejecuciones posteriores. |
| **Patrón Repository** | El acceso a datos se abstrae detrás de repositorios, facilitando migrar de JSON a SQLite u otro backend. |

## Arquitectura

En cada ejecución, la aplicación carga la configuración y procesa cada zona a través de un pipeline de tres etapas:

```
main.py
  │
  ├─ load_config()            → Analiza y valida data/settings.json con Pydantic
  │
  └─ Por cada Zona:
       │
       ├─ 1. DirectoryCreator → Garantiza que existan las carpetas de destino declaradas en las reglas
       │
       ├─ 2. Auditor          → Aplica políticas de ciclo de vida
       │                        ├─ Elimina expirados (papelera o borrado permanente)
       │                        ├─ Limpia entradas huérfanas en el registro
       │                        └─ Registra ítems no rastreados hallados en destino
       │
       └─ 3. FileSorter       → Escanea el directorio origen
                                 ├─ Busca coincidencias de reglas (primera coincidencia gana)
                                 ├─ Aplica la estrategia (move / process_contents / ignore)
                                 ├─ Registra ítems movidos (si el ciclo está activo)
                                 └─ Envía notificaciones con el resumen
```

## Prerequisitos

- **Python** 3.10 o superior
- **pip** (incluido con Python)
- **Git** (para clonar el repositorio)

## Instalación

1. **Clona el repositorio:**

    ```sh
    git clone https://github.com/LimbersMay/Nexus.git
    cd Nexus
    ```

2. **Crea y activa un entorno virtual:**

    ```sh
    # Crear
    python -m venv venv

    # Activar (Windows)
    venv\Scripts\activate

    # Activar (Linux / macOS)
    source venv/bin/activate
    ```

3. **Instala dependencias:**

    ```sh
    pip install -r requirements.txt
    ```

4. **Crea tu archivo de configuración:**

    ```sh
    # Windows
    copy data\settings.example.json data\settings.json

    # Linux / macOS
    cp data/settings.example.json data/settings.json
    ```

5. **Edita `data/settings.json`** para reflejar tus directorios y reglas (ver [Referencia de Configuración](#referencia-de-configuración)).

## Inicio Rápido

Tras instalar, la forma más rápida de empezar es editar el ejemplo con una sola zona apuntando a tu carpeta de Descargas:

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

Luego ejecuta:

```sh
python main.py
```

Los `.pdf` irán a `Downloads\Organized\PDF\`, las imágenes a `Downloads\Organized\Images\`, y tras 7 días se enviarán a la papelera en la siguiente ejecución.

---

## Referencia de Configuración

El archivo de configuración está en `data/settings.json`. Se valida al inicio con Pydantic; cualquier error estructural detiene la aplicación con un mensaje claro.

> **Nota:** El JSON usa claves en `camelCase`. Pydantic las mapea automáticamente a `snake_case`.

### Estructura Raíz

| Clave | Tipo | Requerido | Descripción |
| --- | --- | --- | --- |
| `zones` | `Zone[]` | Sí | Arreglo de zonas. Cada zona es un directorio origen independiente a vigilar. |

```json
{
  "zones": [ ... ]
}
```

### Objeto Zona

Cada zona es una unidad independiente con rutas, configuración, reglas y registro propios.

| Clave | Tipo | Requerido | Descripción |
| --- | --- | --- | --- |
| `zoneName` | `string` | Sí | Identificador legible (ej. `"Downloads"`, `"Screenshots"`). |
| `paths` | `Paths` | Sí | Directorios de origen y destino de la zona. |
| `settings` | `Settings` | Sí | Ajustes globales aplicables a las reglas de la zona. |
| `rules` | `Rule[]` | Sí | Lista ordenada de reglas. Se evalúan de arriba abajo; **la primera coincidencia gana**. |
| `orderedFiles` | `OrderedFile[]` | Sí | Registro interno de auditoría. Inicialízalo como `[]`. Lo gestiona la aplicación. |

### Objeto Paths

| Clave | Tipo | Requerido | Descripción |
| --- | --- | --- | --- |
| `sourcePath` | `string` | Sí | Ruta absoluta a escanear. No debe estar vacía. |
| `destinationPath` | `string` | Sí | Ruta absoluta raíz donde se colocarán los ítems organizados. Se crea automáticamente si no existe. |

```json
"paths": {
  "sourcePath": "C:\\Users\\YourUser\\Downloads",
  "destinationPath": "C:\\Users\\YourUser\\Downloads\\Organized"
}
```

> **Importante:** `destinationPath` (y cualquier subcarpeta) está protegido para evitar bucles de procesamiento.

### Objeto Settings

| Clave | Tipo | Requerido | Default | Descripción |
| --- | --- | --- | --- | --- |
| `maxSizeInMb` | `integer` | Sí | — | Tamaño máximo en MB. Los archivos que lo superan se omiten. Usa un valor alto (ej. `10000`) para desactivar el filtro en la práctica. |

```json
"settings": {
  "maxSizeInMb": 5000
}
```

### Objeto Rule

Las reglas definen **qué** coincidir, **dónde** moverlo, **cómo** manejarlo y **cuándo** limpiarlo.

| Clave | Tipo | Requerido | Default | Descripción |
| --- | --- | --- | --- | --- |
| `ruleName` | `string` | Sí | — | Identificador único. Se usa en el registro para rastrear la regla aplicada. |
| `patterns` | `string[]` | Sí | — | Lista de patrones. El comportamiento depende de `matchBy` (ver [Coincidencia de Patrones](#coincidencia-de-patrones)). |
| `matchBy` | `string` | Sí | — | Estrategia: `"extension"`, `"regex"` o `"glob"`. |
| `handlingStrategy` | `string` | No | `"move"` | Acción: `"move"`, `"process_contents"` o `"ignore"` (ver [Estrategias de Manejo](#estrategias-de-manejo)). |
| `destinationFolder` | `string\|null` | No | `null` | Subcarpeta dentro de `destinationPath`. Requerida para `move` y `process_contents`. Usa `"."` para dejar en la raíz de destino. |
| `lifecycle` | `Lifecycle\|null` | No | `null` | Política de retención. Si es `null` o se omite, no se rastrea el ítem ni se limpia automáticamente. |
| `deleteEmptyAfterProcessing` | `boolean` | No | `false` | Solo para `process_contents`. Si `true`, la carpeta origen se envía a la papelera tras extraer los contenidos. |

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

> **El orden importa.** Coloca reglas específicas antes que las generales. La primera coincidencia se aplica.

### Objeto Lifecycle

| Clave | Tipo | Requerido | Default | Descripción |
| --- | --- | --- | --- | --- |
| `enabled` | `boolean` | No | `true` | Activa o desactiva el ciclo de vida para la regla. |
| `action` | `string` | No | `"trash"` | Acción al expirar: `"trash"` (papelera) o `"delete"` (borrado permanente). |
| `daysToKeep` | `integer` | No | `30` | Días antes de ejecutar la acción. |

### Ordered Files (Interno)

`orderedFiles` es el registro de auditoría. Lo gestiona la aplicación; no lo edites. Cuando un archivo se mueve y la regla tiene ciclo de vida activo, se añade una entrada:

```json
{
  "name": "report.pdf",
  "orderedDate": "2026-02-07",
  "path": "C:\\Users\\TuUsuario\\Downloads\\Organized\\PDF\\report.pdf",
  "ruleNameApplied": "PDF"
}
```

En cada ejecución, el **Auditor** compara fechas contra la política de la regla aplicada y elimina los expirados. También limpia entradas de archivos que ya no existen en disco.

---

## Estrategias de Manejo

### `move`

Mueve el ítem (archivo **o** carpeta) a `destinationPath/destinationFolder/`, conservando su nombre.

```
Origen:  Downloads/report.pdf
Regla:   destinationFolder = "PDF", handlingStrategy = "move"
Resultado: Downloads/Organized/PDF/report.pdf
```

### `process_contents`

Pensado para carpetas. Extrae recursivamente los archivos de la carpeta coincidente, procesa cada uno con el motor de reglas y opcionalmente elimina la carpeta vacía. Cada archivo se evalúa por separado: los que no cumplen la regla de la carpeta siguen evaluándose contra las demás reglas (normalmente terminan en la regla catch-all, por ejemplo `Other`).

Ideal para descargas que se expanden en carpetas (series, películas, backups). Ejemplo con mezcla de video y subtítulos:

```
Origen:  Downloads/Breaking.Bad.S01E01.720p/
           ├─ Breaking.Bad.S01E01.720p.mkv
           └─ subtitles.srt
Regla:   destinationFolder = "TV/Series", handlingStrategy = "process_contents",
         deleteEmptyAfterProcessing = true
Resultado: Downloads/Organized/TV/Series/Breaking.Bad.S01E01.720p.mkv
           Downloads/Organized/Other/subtitles.srt
           (la carpeta de origen se envía a la papelera)
```

### `ignore`

Se omite el ítem. No se mueve, no se rastrea y no aplica ciclo de vida. Útil para:

- Carpetas que quieras preservar (ej. `Temporal`, `node_modules`)
- Descargas en progreso (`.crdownload`, `.part`, `.tmp`)
- Cualquier elemento que no deba tocarse

```json
{
  "ruleName": "IgnoreUnfinishedDownloads",
  "patterns": ["(?i).*\\.crdownload$", "(?i).*\\.part$", "(?i).*\\.tmp$"],
  "matchBy": "regex",
  "handlingStrategy": "ignore"
}
```

---

## Coincidencia de Patrones

`matchBy` determina cómo se interpretan los `patterns`. Siempre se compara contra el nombre del ítem (archivo con extensión o nombre de carpeta).

### Por Extensión

Coincide por extensión (incluido el punto). No distingue mayúsculas/minúsculas.

```json
{
  "matchBy": "extension",
  "patterns": [".pdf", ".doc", ".docx"]
}
```

> Solo aplica a archivos. Las carpetas no tienen extensión.

### Por Regex

Usa expresiones regulares compatibles con Python mediante `re.match()` (ancladas al inicio del nombre).

```json
{
  "matchBy": "regex",
  "patterns": ["(?i).*Gemini.*", ".*S\\d{2}E\\d{2}.*"]
}
```

Patrones comunes:

| Patrón | Coincide |
| --- | --- |
| `".*"` | Todo (catch-all) |
| `"^Temporal$"` | Exactamente `Temporal` |
| `"(?i).*\\.crdownload$"` | Cualquier `.crdownload` (insensible a mayúsculas) |
| `".*S\\d{2}E\\d{2}.*"` | Episodios de series (ej. `Show.S01E05.mkv`) |
| `"(?i).*[\\. _\\-](19\|20)\\d{2}[\\. _\\-].*(1080p\|720p).*"` | Películas con año y calidad |

### Por Glob

Usa comodines estilo shell con `fnmatch`.

```json
{
  "matchBy": "glob",
  "patterns": ["Project_*", "backup_????-??-??"]
}
```

| Patrón | Coincide |
| --- | --- |
| `"*"` | Todo |
| `"Project_*"` | Nombres que empiezan con `Project_` |
| `"*.log"` | Terminan en `.log` |
| `"backup_????-??-??"` | Ej. `backup_2026-02-07` |

---

## Políticas de Ciclo de Vida

Automatizan la limpieza de ítems organizados y se configuran **por regla**.

**Cómo funciona:**

1. Cuando se mueve un archivo y `lifecycle.enabled = true`, se registra en `orderedFiles` con la fecha actual y la regla aplicada.
2. En ejecuciones posteriores, el **Auditor** compara cada registro con la política de la regla aplicada.
3. Si `(hoy - orderedDate) > daysToKeep`, se ejecuta la acción configurada:
   - `"trash"`: envía a la papelera (recuperable).
   - `"delete"`: elimina de forma permanente.

**Desactivar ciclo de vida:**

Para conservar ítems indefinidamente:

- Establece `"lifecycle": { "enabled": false }`; los ítems se moverán pero no se limpiarán.
- O bien deja `lifecycle` en `null`/omitido para el mismo efecto.

**Ítems no rastreados en destino:**

El Auditor escanea destino en busca de ítems existentes que no estén en el registro. Si pertenecen a una carpeta asociada a una regla con ciclo activo, se registran automáticamente con la fecha de hoy, quedando bajo la política de retención.

---

## Ejemplos de Configuración

### Configuración Mínima de una Zona

Organiza Descargas en categorías con retención de 7 días:

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

### Configuración Multi-Zona de Producción

Supervisa tres directorios con reglas especializadas:

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

> **Tip:** Coloca la regla `CatchAll` al final para que nada quede en el origen.

---

## Ejecución de la Aplicación

### Ejecución Manual

```sh
python main.py
```

Ejecuta todas las zonas una vez y termina. Útil para probar tu configuración o programar con tareas.

### Inicio Automático en Windows (vía .exe)

1. **Instala PyInstaller:**

    ```sh
    pip install pyinstaller
    ```

2. **Construye el ejecutable:**

    ```sh
    pyinstaller --noconfirm --onefile --windowed --icon "./assets/work.ico" --hidden-import "plyer.platforms.win.notification" "./main.py"
    ```

3. **Mueve** `dist/main.exe` a la raíz del proyecto.

4. **Crea el acceso directo de arranque:**
   - Pulsa <kbd>Win</kbd> + <kbd>R</kbd>, escribe `shell:startup` y pulsa Enter.
   - Crea un acceso directo a `main.exe` y colócalo en la carpeta de inicio.

5. **Reinicia**. La aplicación correrá en cada inicio de sesión.

> **Alternativa:** Usa el Programador de Tareas de Windows para mayor control.

### Inicio Automático en Linux (vía systemd)

1. **Crea un servicio de usuario systemd:**

    ```sh
    mkdir -p ~/.config/systemd/user
    nano ~/.config/systemd/user/automate_downloads.service
    ```

2. **Pega lo siguiente** (ajusta rutas):

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

3. **Activa y arranca el servicio:**

    ```sh
    systemctl --user daemon-reload
    systemctl --user enable automate_downloads.service
    systemctl --user start automate_downloads.service
    ```

4. **Verifica estado:**

    ```sh
    systemctl --user status automate_downloads.service
    ```

---

## Estructura del Proyecto

```
Nexus/
├── main.py                         # Punto de entrada — carga config y ejecuta el pipeline
├── file_sorter.py                  # FileSorter — escanea origen, coincide reglas, mueve ítems
├── registry_checker.py             # Auditor — aplica ciclo de vida y limpia registro
├── requirements.txt                # Dependencias
├── main.spec                       # Especificación PyInstaller
│
├── data/
│   ├── settings.example.json       # Config de ejemplo (copiar a settings.json)
│   └── settings.json               # Config activa (no versionada)
│
├── models/
│   ├── base.py                     # CamelCaseModel — base Pydantic con alias camelCase
│   ├── models.py                   # Modelos de dominio (SortingRule, LifecyclePolicy, PathConfig, etc.)
│   └── app_config.py               # ZoneConfig y RootConfig (modelos de configuración)
│
├── services/
│   ├── path_repository.py          # PathRepository + implementación de configuración
│   ├── settings_repository.py      # SettingsRepository + implementación de configuración
│   ├── ordered_files_repository.py # OrderedFilesRepository + implementación de configuración
│   ├── json_config_persister.py    # JsonConfigPersister — serializa config a JSON
│   └── notification_service.py     # NotificationService + implementación Plyer
│
├── helpers/
│   ├── config_loader.py            # load_config() — lee y valida settings.json
│   └── directory_creator.py        # DirectoryCreator — asegura carpetas destino
│
└── assets/
    └── work.ico                    # Icono de la aplicación
```

## Tecnologías

| Dependencia | Versión | Propósito |
| --- | --- | --- |
| [Pydantic](https://docs.pydantic.dev/) | 2.12+ | Validación y serialización de configuración con alias camelCase |
| [Send2Trash](https://github.com/hsoft/send2trash) | 1.8+ | Envío seguro a la papelera | 
| [Plyer](https://github.com/kivy/plyer) | 2.1+ | Notificaciones de escritorio multiplataforma |
| [dbus-python](https://dbus.freedesktop.org/doc/dbus-python/) | 1.3+ | Bindings D-Bus para notificaciones en Linux |

## Licencia

Este proyecto está bajo la [Licencia MIT](LICENSE).

---

<p align="center">
  Hecho por <a href="https://github.com/LimbersMay">LimbersMay</a>
</p>