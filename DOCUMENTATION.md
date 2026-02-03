# Documentación del Proyecto: AutomateDownloadsFolder

## 📋 Índice
1. [Visión General](#visión-general)
2. [Arquitectura del Proyecto](#arquitectura-del-proyecto)
3. [Entidades (Modelo de Datos)](#entidades-modelo-de-datos)
4. [Servicios (Capa de Datos)](#servicios-capa-de-datos)
5. [Helpers (Utilidades)](#helpers-utilidades)
6. [Componentes Principales](#componentes-principales)
7. [Flujo de Ejecución](#flujo-de-ejecución)
8. [Configuración](#configuración)
9. [Dependencias](#dependencias)

---

## Visión General

**AutomateDownloadsFolder** es un sistema automatizado de organización de archivos diseñado para mantener limpia la carpeta de descargas (o cualquier carpeta configurada). El sistema clasifica archivos según reglas personalizables, gestiona su ciclo de vida y envía notificaciones al usuario.

### Características Principales:
- Clasificación automática de archivos por extensión o expresiones regulares
- Gestión del ciclo de vida de archivos con límite de días
- Opción de enviar archivos eliminados a la papelera o eliminarlos permanentemente
- Sistema de notificaciones para informar acciones realizadas
- Registro persistente de archivos organizados
- Límite de tamaño configurable para archivos a organizar

### Tecnologías:
- **Lenguaje**: Python 3.x
- **Patrón de diseño**: Repository Pattern + Dependency Injection
- **Persistencia**: JSON
- **Notificaciones**: Plyer

---

## Arquitectura del Proyecto

El proyecto sigue una arquitectura en capas con separación de responsabilidades:

```
AutomateDownloadsFolder/
│
├── entities/           # Modelos de dominio (POJOs/DTOs)
│   ├── ordered_file.py
│   ├── path.py
│   ├── settings.py
│   └── sorting_rule.py
│
├── services/          # Repositorios y servicios (Capa de datos)
│   ├── notification_service.py
│   ├── ordered_files_repository.py
│   ├── path_repository.py
│   └── settings_repository.py
│
├── helpers/           # Utilidades y helpers
│   └── directory_creator.py
│
├── data/              # Almacenamiento de configuración y datos
│   ├── settings.json
│   └── settings.example.json
│
├── main.py            # Punto de entrada del programa
├── file_sorter.py     # Lógica de clasificación de archivos
├── registry_checker.py # Auditoría y limpieza de archivos
└── requirements.txt   # Dependencias del proyecto
```

### Patrones de Diseño Utilizados:

1. **Repository Pattern**: Abstracción de la capa de datos mediante interfaces
2. **Dependency Injection**: Inyección de dependencias en constructores
3. **Abstract Base Classes (ABC)**: Interfaces para garantizar implementaciones consistentes
4. **Single Responsibility Principle**: Cada clase tiene una única responsabilidad

---

## Entidades (Modelo de Datos)

Las entidades representan los modelos de dominio del sistema.

### 1. `OrderedFile`
**Archivo**: `entities/ordered_file.py`

Representa un archivo que ha sido organizado por el sistema.

```python
class OrderedFile:
    def __init__(self, name: str, ordered_date: datetime.date, path: str):
        self.name = name              # Nombre del archivo con extensión
        self.ordered_date = ordered_date  # Fecha de organización
        self.path = path              # Ruta absoluta donde fue movido
```

**Atributos**:
- `name` (str): Nombre del archivo incluida la extensión (ej: "documento.pdf")
- `ordered_date` (datetime.date): Fecha en que el archivo fue organizado
- `path` (str): Ruta completa donde se encuentra el archivo organizado

**Uso**: Trackear archivos organizados para su posterior auditoría y eliminación basada en tiempo.

---

### 2. `Path`
**Archivo**: `entities/path.py`

Encapsula una ruta del sistema de archivos.

```python
class Path:
    def __init__(self, name: str):
        self.name = name  # Ruta del sistema de archivos
```

**Atributos**:
- `name` (str): Ruta completa del sistema de archivos

**Uso**: Wrapper simple para representar rutas de origen y destino.

---

### 3. `Settings`
**Archivo**: `entities/settings.py`

Contiene toda la configuración del sistema.

```python
class Settings:
    def __init__(self, days_to_keep: int, send_to_trash: bool, 
                 max_size: int, sorting_rules: List[SortingRule]):
        self.days_to_keep = days_to_keep      # Días antes de eliminar
        self.send_to_trash = send_to_trash    # True: papelera, False: borrado permanente
        self.max_size = max_size              # Tamaño máximo en bytes
        self.sorting_rules = sorting_rules    # Lista de reglas de clasificación
```

**Atributos**:
- `days_to_keep` (int): Número de días que un archivo permanece antes de ser eliminado
- `send_to_trash` (bool): Si es True, envía archivos a la papelera; si es False, los elimina permanentemente
- `max_size` (int): Tamaño máximo en bytes de archivos a organizar
- `sorting_rules` (List[SortingRule]): Lista de reglas para clasificar archivos

**Conversiones**: En el repositorio, `maxSizeInMb` se convierte a bytes multiplicando por `1024 * 1024`.

---

### 4. `SortingRule`
**Archivo**: `entities/sorting_rule.py`

Define una regla para clasificar archivos.

```python
class SortingRule:
    def __init__(self, folder_name: str, match_by: str, patterns: list[str]):
        self.folder_name = folder_name  # Carpeta destino
        self.match_by = match_by        # "extension" o "regex"
        self.patterns = patterns        # Lista de patrones a coincidir
```

**Atributos**:
- `folder_name` (str): Nombre de la carpeta donde se moverán los archivos que coincidan
- `match_by` (str): Tipo de coincidencia - `"extension"` o `"regex"`
- `patterns` (list[str]): Lista de patrones:
  - Si `match_by == "extension"`: extensiones como `[".pdf", ".docx"]`
  - Si `match_by == "regex"`: expresiones regulares como `[".*Gemini.*"]`

**Ejemplo de uso**:
```python
# Regla por extensión
SortingRule("PDF", "extension", [".pdf"])

# Regla por regex
SortingRule("Gemini", "regex", [".*Gemini.*"])
```

---

## Servicios (Capa de Datos)

Los servicios implementan el patrón Repository para abstraer el acceso a datos.

### 1. `NotificationService`
**Archivo**: `services/notification_service.py`

Servicio abstracto para enviar notificaciones al usuario.

#### Clase Abstracta: `NotificationService`
```python
class NotificationService(ABC):
    @abstractmethod
    def send_notification(self, message: str):
        pass
```

#### Implementación: `PlyerNotificationService`
```python
class PlyerNotificationService(NotificationService):
    def send_notification(self, message: str):
        notification.notify(
            title="Assistant",
            message=message,
            app_icon="assets/work.ico",
            timeout=8
        )
```

**Métodos**:
- `send_notification(message: str)`: Envía una notificación del sistema con el mensaje dado

**Parámetros de la notificación**:
- `title`: "Assistant"
- `message`: Mensaje dinámico
- `app_icon`: Ícono de la aplicación (assets/work.ico)
- `timeout`: 8 segundos de duración

**Uso**: Informar al usuario sobre acciones completadas (archivos organizados, archivos eliminados).

---

### 2. `OrderedFilesRepository`
**Archivo**: `services/ordered_files_repository.py`

Gestiona la persistencia de archivos organizados.

#### Clase Abstracta: `OrderedFilesRepository`
```python
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
    def find(self, file_name: str) -> OrderedFile or None:
        pass

    @abstractmethod
    def delete(self, file_name: str) -> None:
        pass
```

#### Implementación: `JsonOrderedFilesRepository`
```python
class JsonOrderedFilesRepository(OrderedFilesRepository):
    def __init__(self, json_file_path: str):
        self.json_file_path = json_file_path
```

**Métodos**:

1. **`get_ordered_files() -> List[OrderedFile]`**
   - Retorna todos los archivos organizados registrados
   - Lee desde `settings.json["orderedFiles"]`
   - Convierte fechas ISO format a `datetime.date`

2. **`get_files_to_delete(days_to_keep: int) -> List[OrderedFile]`**
   - Retorna archivos cuya fecha de organización excede `days_to_keep`
   - Calcula: `(fecha_actual - ordered_date).days > days_to_keep`

3. **`save_ordered_files(new_ordered_files: List[OrderedFile]) -> None`**
   - Agrega nuevos archivos al registro existente
   - Convierte fechas a ISO format (`isoformat()`)
   - Actualiza `settings.json["orderedFiles"]`

4. **`find(file_name: str) -> OrderedFile | None`**
   - Busca un archivo por nombre
   - Retorna el `OrderedFile` si existe, `None` en caso contrario

5. **`delete(file_name: str) -> None`**
   - Elimina un archivo del registro JSON
   - Busca por nombre y lo remueve de `orderedFiles`

**Estructura JSON**:
```json
{
  "orderedFiles": [
    {
      "name": "documento.pdf",
      "ordered_date": "2025-11-08",
      "path": "C:\\Downloads\\Organized\\PDF\\documento.pdf"
    }
  ]
}
```

---

### 3. `PathRepository`
**Archivo**: `services/path_repository.py`

Gestiona las rutas de origen y destino.

#### Clase Abstracta: `PathRepository`
```python
class PathRepository(ABC):
    @abstractmethod
    def get_source_path(self) -> Path:
        pass

    @abstractmethod
    def get_destination_path(self) -> Path:
        pass
```

#### Implementación: `JsonPathRepository`
```python
class JsonPathRepository(PathRepository):
    def __init__(self, json_file_path: str):
        self.json_file_path = json_file_path
```

**Métodos**:

1. **`get_source_path() -> Path`**
   - Retorna la ruta de origen (donde buscar archivos)
   - Lee desde `settings.json["paths"]["sourcePath"]`

2. **`get_destination_path() -> Path`**
   - Retorna la ruta de destino (donde organizar archivos)
   - Lee desde `settings.json["paths"]["destinationPath"]`

**Estructura JSON**:
```json
{
  "paths": {
    "sourcePath": "C:\\Users\\Usuario\\Downloads",
    "destinationPath": "C:\\Users\\Usuario\\Downloads\\Organized"
  }
}
```

---

### 4. `SettingsRepository`
**Archivo**: `services/settings_repository.py`

Gestiona la configuración del sistema.

#### Clase Abstracta: `SettingsRepository`
```python
class SettingsRepository(ABC):
    @abstractmethod
    def get_settings(self) -> Settings:
        pass

    @abstractmethod
    def get_sorting_rules(self) -> List[SortingRule]:
        pass

    @abstractmethod
    def get_default_folder(self) -> str:
        pass
```

#### Implementación: `JsonSettingsRepository`
```python
class JsonSettingsRepository(SettingsRepository):
    def __init__(self, json_file_path: str):
        self.json_file_path = json_file_path
```

**Métodos**:

1. **`get_settings() -> Settings`**
   - Retorna objeto `Settings` completo
   - Convierte `maxSizeInMb` a bytes: `maxSizeInMb * (1024 * 1024)`
   - Incluye las reglas de clasificación

2. **`get_sorting_rules() -> List[SortingRule]`**
   - Retorna lista de reglas de clasificación
   - Convierte JSON a objetos `SortingRule`

3. **`get_default_folder() -> str`**
   - Retorna el nombre de la carpeta por defecto
   - Usada para archivos que no coinciden con ninguna regla

**Estructura JSON**:
```json
{
  "settings": {
    "daysToKeep": 2,
    "sendToTrash": true,
    "maxSizeInMb": 500
  },
  "sortingRules": [
    {
      "folderName": "PDF",
      "matchBy": "extension",
      "patterns": [".pdf"]
    }
  ],
  "defaultFolder": "Other"
}
```

---

## Helpers (Utilidades)

### `DirectoryCreator`
**Archivo**: `helpers/directory_creator.py`

Crea la estructura de carpetas necesaria basándose en las reglas de clasificación.

```python
class DirectoryCreator:
    def __init__(self, path_repository: PathRepository,
                 settings_repository: SettingsRepository):
        self.__path_repository = path_repository
        self.__settings_repository = settings_repository

    def execute(self) -> None:
        destination_path = self.__path_repository.get_destination_path().name
        sorting_rules = self.__settings_repository.get_sorting_rules()

        for rule in sorting_rules:
            os.makedirs(os.path.join(destination_path, rule.destination_folder),
                        exist_ok=True)
```

**Dependencias**:
- `PathRepository`: Para obtener la ruta de destino
- `SettingsRepository`: Para obtener las reglas de clasificación

**Método**:
- **`execute() -> None`**
  - Crea todas las carpetas definidas en `sortingRules`
  - Usa `os.makedirs(..., exist_ok=True)` para evitar errores si ya existen
  - Ruta creada: `destinationPath/folderName`

**Ejemplo**:
Si `destinationPath = "C:\Downloads\Organized"` y las reglas definen carpetas `["PDF", "Image", "Video"]`, se crean:
- `C:\Downloads\Organized\PDF`
- `C:\Downloads\Organized\Image`
- `C:\Downloads\Organized\Video`

---

## Componentes Principales

### 1. `FileSorter`
**Archivo**: `file_sorter.py`

Responsable de clasificar y mover archivos desde la carpeta de origen a las carpetas de destino.

```python
class FileSorter:
    def __init__(self, path_repository: PathRepository,
                 settings_repository: SettingsRepository,
                 ordered_files_repository: OrderedFilesRepository,
                 notificator_service: NotificationService):
        self.__path_repository = path_repository
        self.__settings_repository = settings_repository
        self.__ordered_files_repository = ordered_files_repository
        self.__notification_service = notificator_service
```

**Dependencias**:
- `PathRepository`: Rutas de origen/destino
- `SettingsRepository`: Configuración y reglas
- `OrderedFilesRepository`: Registro de archivos organizados
- `NotificationService`: Notificaciones al usuario

#### Métodos:

**1. `__find_destination_folder(file_name: str, rules: List[SortingRule], default_folder: str) -> str`** (privado)

Determina a qué carpeta debe ir un archivo basándose en las reglas.

**Parámetros**:
- `file_name`: Nombre del archivo con extensión
- `rules`: Lista de reglas de clasificación
- `default_folder`: Carpeta por defecto si ninguna regla coincide

**Retorna**: Nombre de la carpeta destino

**Lógica**:
1. Extrae la extensión del archivo usando `os.path.splitext()`
2. Itera sobre las reglas en orden
3. **Si `match_by == "extension"`**:
   - Compara la extensión (case-insensitive) con los patrones
   - Si coincide, retorna `folder_name`
4. **Si `match_by == "regex"`**:
   - Aplica `re.match()` a cada patrón
   - Si coincide, retorna `folder_name`
5. Si ninguna regla coincide, retorna `default_folder`

**Ejemplo**:
```python
# Archivo: "documento.pdf"
# Regla: {"folderName": "PDF", "matchBy": "extension", "patterns": [".pdf"]}
# Resultado: "PDF"

# Archivo: "Gemini_Generated_Image.png"
# Regla: {"folderName": "Gemini", "matchBy": "regex", "patterns": [".*Gemini.*"]}
# Resultado: "Gemini"
```

---

**2. `sort() -> None`**

Método principal que organiza los archivos.

**Flujo de ejecución**:

1. **Obtener configuración**:
   ```python
   source_path = self.__path_repository.get_source_path().name
   destination_path = self.__path_repository.get_destination_path().name
   size_limit = self.__settings_repository.get_settings().max_size
   sorting_rules = self.__settings_repository.get_sorting_rules()
   default_folder = self.__settings_repository.get_default_folder()
   ```

2. **Escanear archivos en la carpeta de origen**:
   ```python
   with os.scandir(source_path) as it:
       full_paths = [entry.path for entry in it if entry.is_file()]
   ```

3. **Filtrar archivos por tamaño**:
   ```python
   files_to_organize = [file for file in full_paths 
                       if os.path.getsize(file) < size_limit]
   ```
   Solo organiza archivos menores al límite configurado.

4. **Procesar cada archivo**:
   ```python
   for current_file_path in files_to_organize:
       name_with_extension = pathlib.Path(current_file_path).name
       destination_folder_name = self.__find_destination_folder(
           name_with_extension, sorting_rules, default_folder)
       
       # Crear carpeta destino si no existe
       destination_folder_path = os.path.join(destination_path, destination_folder_name)
       os.makedirs(destination_folder_path, exist_ok=True)
       
       # Mover archivo
       destination_file_path = os.path.join(destination_folder_path, name_with_extension)
       shutil.move(current_file_path, destination_file_path)
       
       # Registrar archivo organizado
       current_date = datetime.datetime.now().date()
       ordered_files.append(OrderedFile(name_with_extension, current_date, destination_file_path))
   ```

5. **Persistir registros**:
   ```python
   if ordered_files:
       self.__ordered_files_repository.save_ordered_files(ordered_files)
   ```

6. **Enviar notificación**:
   ```python
   if len(files_to_organize) > 0:
       self.__notification_service.send_notification(
           f"{len(files_to_organize)} files were sorted")
   ```

**Características importantes**:
- Crea carpetas dinámicamente si no existen
- Registra la fecha de organización
- Solo notifica si se organizó al menos un archivo
- Respeta el límite de tamaño configurado

---

### 2. `Auditor` (Registry Checker)
**Archivo**: `registry_checker.py`

Audita archivos organizados y gestiona su ciclo de vida.

```python
class Auditor:
    def __init__(self, path_repository: PathRepository,
                 ordered_files_repository: OrderedFilesRepository,
                 settings_repository: SettingsRepository,
                 notificator_service: NotificationService):
        self.__path_repository = path_repository
        self.__ordered_files_repository = ordered_files_repository
        self.__settings_repository = settings_repository
        self.__notification_service = notificator_service
```

**Dependencias**:
- `PathRepository`: Ruta de destino
- `OrderedFilesRepository`: Registro de archivos
- `SettingsRepository`: Configuración de días y modo de eliminación
- `NotificationService`: Notificaciones

#### Método: `check_files() -> None`

Realiza tres tareas principales:

**1. Eliminar archivos antiguos**:
```python
# Configuración
destination_path = self.__path_repository.get_destination_path().name
limit_days = self.__settings_repository.get_settings().days_to_keep
send_to_trash = self.__settings_repository.get_settings().send_to_trash

# Obtener archivos a eliminar
files_to_delete = self.__ordered_files_repository.get_files_to_delete(limit_days)

for file_to_delete in files_to_delete:
    # Verificar si el archivo existe físicamente
    if not os.path.exists(file_to_delete.path):
        self.__ordered_files_repository.delete(file_to_delete.name)
        continue

    # Eliminar según configuración
    if send_to_trash:
        send2trash(file_to_delete.path)  # A la papelera
    else:
        os.remove(file_to_delete.path)   # Borrado permanente

    # Eliminar del registro
    self.__ordered_files_repository.delete(file_to_delete.name)
```

**Lógica de eliminación**:
- Si el archivo no existe físicamente, solo lo elimina del registro
- Si `send_to_trash == True`: usa `send2trash()` (papelera del sistema)
- Si `send_to_trash == False`: usa `os.remove()` (eliminación permanente)

---

**2. Registrar archivos no registrados**:
```python
# Buscar todos los archivos en carpetas de destino
destination_paths = glob.glob(destination_path + "/**/*.*", recursive=True)
destination_path_files = [os.path.basename(file) for file in destination_paths]

not_registered_files: List[OrderedFile] = []

for file, file_path in zip(destination_path_files, destination_paths):
    current_date = datetime.now().date()

    # Si no está registrado, agregarlo
    if not self.__ordered_files_repository.find(file):
        not_registered_files.append(OrderedFile(file, current_date, file_path))

# Guardar archivos no registrados
self.__ordered_files_repository.save_ordered_files(not_registered_files)
```

**Propósito**: Registra archivos que fueron movidos manualmente o por otros medios a las carpetas organizadas.

---

**3. Notificar eliminaciones**:
```python
if len(files_to_delete) > 0:
    self.__notification_service.send_notification(
        f"{len(files_to_delete)} files were deleted.")
```

**Resumen de responsabilidades**:
- ✅ Eliminar archivos que exceden el límite de días
- ✅ Limpiar registros huérfanos (archivos eliminados externamente)
- ✅ Registrar archivos existentes no registrados
- ✅ Notificar acciones al usuario

---

### 3. `main.py`
**Archivo**: `main.py`

Punto de entrada del programa. Orquesta todo el flujo de ejecución.

```python
def main():
    json_path = "data/settings.json"

    # 1. Inicializar repositorios y servicios
    path_repository = JsonPathRepository(json_path)
    settings_repository = JsonSettingsRepository(json_path)
    ordered_files_repository = JsonOrderedFilesRepository(json_path)
    notification_service = PlyerNotificationService()

    # 2. Crear directorios necesarios
    directory_creator = DirectoryCreator(path_repository, settings_repository)
    directory_creator.execute()

    # 3. Auditar archivos existentes
    auditor = Auditor(path_repository, ordered_files_repository, 
                     settings_repository, notification_service)
    auditor.check_files()

    # 4. Organizar nuevos archivos
    file_organizer = FileSorter(path_repository, settings_repository, 
                                ordered_files_repository, notification_service)
    file_organizer.sort()


if __name__ == "__main__":
    main()
```

**Flujo de ejecución**:
1. **Configuración**: Lee `data/settings.json`
2. **Inyección de dependencias**: Inicializa todos los repositorios y servicios
3. **Crear estructura de carpetas**: Asegura que todas las carpetas existan
4. **Auditoría**: Elimina archivos antiguos y registra archivos existentes
5. **Organización**: Clasifica y mueve archivos nuevos

**Orden de operaciones**:
```
main()
  ├─> DirectoryCreator.execute()    # Crear carpetas
  ├─> Auditor.check_files()         # Limpiar archivos antiguos
  └─> FileSorter.sort()              # Organizar archivos nuevos
```

---

## Flujo de Ejecución

### Diagrama de Flujo Completo

```
┌─────────────────────────────────────────────────────────────┐
│                         INICIO                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  1. INICIALIZACIÓN (main.py)                                │
│  - Cargar settings.json                                     │
│  - Crear repositorios (Path, Settings, OrderedFiles)       │
│  - Crear servicios (Notification)                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  2. CREAR DIRECTORIOS (DirectoryCreator)                    │
│  - Leer sortingRules                                        │
│  - Crear carpeta para cada folderName                       │
│    Ej: destinationPath/PDF, destinationPath/Image, etc.     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  3. AUDITORÍA (Auditor.check_files)                         │
│                                                             │
│  3.1 Eliminar archivos antiguos:                            │
│      - Obtener archivos > daysToKeep                        │
│      - Si sendToTrash: enviar a papelera                    │
│      - Si no: eliminar permanentemente                      │
│      - Eliminar del registro JSON                           │
│                                                             │
│  3.2 Registrar archivos no registrados:                     │
│      - Escanear destinationPath recursivamente              │
│      - Si archivo existe pero no está en orderedFiles:      │
│        → Registrarlo con fecha actual                       │
│                                                             │
│  3.3 Notificar eliminaciones                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  4. ORGANIZAR ARCHIVOS (FileSorter.sort)                    │
│                                                             │
│  4.1 Escanear sourcePath:                                   │
│      - Obtener lista de archivos                            │
│      - Filtrar por tamaño < maxSizeInMb                     │
│                                                             │
│  4.2 Por cada archivo:                                      │
│      - Determinar carpeta destino:                          │
│        a) Intentar coincidir con reglas (extension/regex)   │
│        b) Si no coincide: usar defaultFolder                │
│      - Crear carpeta destino si no existe                   │
│      - Mover archivo: shutil.move()                         │
│      - Registrar en OrderedFile con fecha actual            │
│                                                             │
│  4.3 Persistir registros:                                   │
│      - Guardar en orderedFiles JSON                         │
│                                                             │
│  4.4 Notificar organización                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                          FIN                                │
└─────────────────────────────────────────────────────────────┘
```

### Ejemplo Práctico

**Configuración**:
```json
{
  "settings": {
    "daysToKeep": 2,
    "sendToTrash": true,
    "maxSizeInMb": 500
  },
  "paths": {
    "sourcePath": "C:\\Downloads",
    "destinationPath": "C:\\Downloads\\Organized"
  },
  "sortingRules": [
    {"folderName": "PDF", "matchBy": "extension", "patterns": [".pdf"]},
    {"folderName": "Image", "matchBy": "extension", "patterns": [".jpg", ".png"]}
  ],
  "defaultFolder": "Other"
}
```

**Ejecución**:

1. **Crear carpetas**:
   - `C:\Downloads\Organized\PDF`
   - `C:\Downloads\Organized\Image`

2. **Auditoría** (día 08/11/2025):
   - Archivo registrado el 05/11/2025 → Más de 2 días → **Eliminar**
   - Archivo `manual.txt` existe en `Organized/Other` pero no registrado → **Registrar**

3. **Organizar**:
   - `documento.pdf` (100 KB) en `C:\Downloads`:
     - Tamaño < 500 MB ✅
     - Extensión `.pdf` → Coincide con regla PDF
     - Mover a `C:\Downloads\Organized\PDF\documento.pdf`
     - Registrar: `{"name": "documento.pdf", "ordered_date": "2025-11-08", "path": "..."}`
   
   - `foto.jpg` (200 KB) en `C:\Downloads`:
     - Tamaño < 500 MB ✅
     - Extensión `.jpg` → Coincide con regla Image
     - Mover a `C:\Downloads\Organized\Image\foto.jpg`
     - Registrar: `{"name": "foto.jpg", "ordered_date": "2025-11-08", "path": "..."}`
   
   - `archivo.xyz` (50 KB) en `C:\Downloads`:
     - Tamaño < 500 MB ✅
     - Extensión `.xyz` → No coincide con ninguna regla
     - Mover a `C:\Downloads\Organized\Other\archivo.xyz`
     - Registrar: `{"name": "archivo.xyz", "ordered_date": "2025-11-08", "path": "..."}`

4. **Notificación**: "3 files were sorted"

---

## Configuración

### Archivo: `data/settings.json`

**Estructura completa**:
```json
{
  "settings": {
    "daysToKeep": 2,
    "sendToTrash": true,
    "maxSizeInMb": 500
  },
  "orderedFiles": [
    {
      "name": "ejemplo.pdf",
      "ordered_date": "2025-11-08",
      "path": "C:\\Downloads\\Organized\\PDF\\ejemplo.pdf"
    }
  ],
  "paths": {
    "sourcePath": "C:\\User\\Windows\\Downloads",
    "destinationPath": "C:\\User\\Windows\\Downloads\\Organized"
  },
  "sortingRules": [
    {
      "folderName": "Gemini",
      "matchBy": "regex",
      "patterns": [".*Gemini.*"]
    },
    {
      "folderName": "Word",
      "matchBy": "extension",
      "patterns": [".doc", ".docx", ".dot"]
    },
    {
      "folderName": "PDF",
      "matchBy": "extension",
      "patterns": [".pdf"]
    }
  ],
  "defaultFolder": "Other"
}
```

### Campos de Configuración:

#### `settings`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `daysToKeep` | int | Días antes de eliminar archivos organizados |
| `sendToTrash` | bool | `true`: papelera, `false`: eliminación permanente |
| `maxSizeInMb` | int | Tamaño máximo en MB de archivos a organizar |

#### `orderedFiles`
Array de objetos con archivos organizados:
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `name` | str | Nombre del archivo con extensión |
| `ordered_date` | str | Fecha de organización (formato ISO: YYYY-MM-DD) |
| `path` | str | Ruta absoluta del archivo organizado |

#### `paths`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `sourcePath` | str | Carpeta donde buscar archivos a organizar |
| `destinationPath` | str | Carpeta base donde organizar archivos |

#### `sortingRules`
Array de objetos con reglas de clasificación:
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `folderName` | str | Nombre de la carpeta destino |
| `matchBy` | str | `"extension"` o `"regex"` |
| `patterns` | array[str] | Patrones a coincidir |

**Tipos de reglas**:
- **Por extensión**: `"matchBy": "extension"`, `"patterns": [".pdf", ".docx"]`
- **Por regex**: `"matchBy": "regex"`, `"patterns": [".*Gemini.*", "^IMG_.*"]`

#### `defaultFolder`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `defaultFolder` | str | Carpeta para archivos sin coincidencia |

---

## Dependencias

### `requirements.txt`
```
dbus-python==1.3.2; sys_platform=='linux'
plyer==2.1.0
Send2Trash==1.8.2
```

### Descripción de Dependencias:

1. **`dbus-python==1.3.2`** (solo Linux)
   - Sistema de comunicación entre procesos
   - Requerido por `plyer` para notificaciones en Linux
   - Condicional: solo se instala en sistemas Linux

2. **`plyer==2.1.0`**
   - API multiplataforma para acceder a características del sistema
   - Usado para: Notificaciones del sistema
   - Plataformas: Windows, Linux, macOS

3. **`Send2Trash==1.8.2`**
   - Envía archivos a la papelera del sistema operativo
   - Multiplataforma (Windows Recycle Bin, macOS Trash, Linux Trash)
   - Usado cuando `sendToTrash == true`

### Módulos estándar de Python utilizados:
- `datetime`: Manejo de fechas
- `os`: Operaciones del sistema de archivos
- `pathlib`: Manipulación de rutas
- `re`: Expresiones regulares
- `shutil`: Operaciones de alto nivel con archivos
- `json`: Lectura/escritura de JSON
- `glob`: Búsqueda de archivos con patrones
- `abc`: Clases abstractas

---

## Resumen de Tipos y Relaciones

### Diagrama de Dependencias:

```
main.py
  ├─> DirectoryCreator
  │     ├─> PathRepository
  │     └─> SettingsRepository
  │
  ├─> Auditor
  │     ├─> PathRepository
  │     ├─> OrderedFilesRepository
  │     ├─> SettingsRepository
  │     └─> NotificationService
  │
  └─> FileSorter
        ├─> PathRepository
        ├─> SettingsRepository
        ├─> OrderedFilesRepository
        └─> NotificationService

Repositorios:
  ├─> PathRepository → Path
  ├─> SettingsRepository → Settings, SortingRule
  └─> OrderedFilesRepository → OrderedFile

Servicios:
  └─> NotificationService (interfaz)
        └─> PlyerNotificationService (implementación)
```

### Tabla de Tipos:

| Componente | Tipo | Retorno/Tipado |
|------------|------|----------------|
| `OrderedFile.__init__` | Constructor | `(str, datetime.date, str) -> None` |
| `Path.__init__` | Constructor | `(str) -> None` |
| `Settings.__init__` | Constructor | `(int, bool, int, List[SortingRule]) -> None` |
| `SortingRule.__init__` | Constructor | `(str, str, list[str]) -> None` |
| `PathRepository.get_source_path` | Método abstracto | `() -> Path` |
| `PathRepository.get_destination_path` | Método abstracto | `() -> Path` |
| `SettingsRepository.get_settings` | Método abstracto | `() -> Settings` |
| `SettingsRepository.get_sorting_rules` | Método abstracto | `() -> List[SortingRule]` |
| `SettingsRepository.get_default_folder` | Método abstracto | `() -> str` |
| `OrderedFilesRepository.get_ordered_files` | Método abstracto | `() -> List[OrderedFile]` |
| `OrderedFilesRepository.get_files_to_delete` | Método abstracto | `(int) -> List[OrderedFile]` |
| `OrderedFilesRepository.save_ordered_files` | Método abstracto | `(List[OrderedFile]) -> None` |
| `OrderedFilesRepository.find` | Método abstracto | `(str) -> OrderedFile \| None` |
| `OrderedFilesRepository.delete` | Método abstracto | `(str) -> None` |
| `NotificationService.send_notification` | Método abstracto | `(str) -> None` |
| `DirectoryCreator.execute` | Método público | `() -> None` |
| `FileSorter.sort` | Método público | `() -> None` |
| `FileSorter.__find_destination_folder` | Método privado | `(str, List[SortingRule], str) -> str` |
| `Auditor.check_files` | Método público | `() -> None` |

---

## Notas Adicionales

### Buenas Prácticas Implementadas:
1. ✅ **Separación de responsabilidades**: Cada clase tiene un propósito único
2. ✅ **Inversión de dependencias**: Se depende de abstracciones (interfaces), no de implementaciones concretas
3. ✅ **Patrón Repository**: Abstracción de la capa de datos
4. ✅ **Naming privado**: Métodos privados usan `__` (name mangling)
5. ✅ **Type hints**: Anotaciones de tipo en firmas de métodos
6. ✅ **Configuración externa**: Toda la configuración está en JSON
7. ✅ **Modularidad**: Fácil cambiar implementaciones (ej: JSON → SQLite)

### Posibles Mejoras Futuras:
- Múltiples carpetas de origen
- Múltiples carpetas de destino
- Migración de JSON a SQLite
- Manejo de conflictos de nombres de archivos
- Logging estructurado
- Tests unitarios
- Interfaz gráfica (GUI)

---

**Autor**: LimbersMay  
**Repositorio**: [AutomateDownloadsFolder](https://github.com/LimbersMay/AutomateDownloadsFolder)  
**Licencia**: Ver archivo LICENSE
