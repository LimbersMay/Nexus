# Technical README - AutomateDownloadsFolder

## 📖 Descripción
Sistema automatizado de organización de archivos con arquitectura basada en Repository Pattern y Dependency Injection. Clasifica archivos por extensión o regex, gestiona ciclos de vida y envía notificaciones.

---

## 🏗️ Estructura del Código

### **Entidades (models/)**

#### `OrderedFile` - models/models.py
```python
import datetime

class OrderedFile:
    def __init__(self, name: str, ordered_date: datetime.date, path: str):
        self.name = name              # Nombre del archivo
        self.ordered_date = ordered_date  # Fecha de organización
        self.path = path              # Ruta absoluta del archivo
```
**Descripción**: Representa un archivo organizado por el sistema. Almacena metadatos para tracking y auditoría.

---

#### `PathConfig` - models/models.py
```python
class PathConfig:
    def __init__(self, name: str):
        self.name = name  # Ruta del sistema de archivos
```
**Descripción**: Wrapper simple para encapsular rutas del sistema.

---

#### `GlobalSettings` - models/models.py

```python
from typing import List
from models.models import FileSortingRule


class GlobalSettings:
    def __init__(self, days_to_keep: int, send_to_trash: bool,
                 max_size: int, sorting_rules: List[FileSortingRule]):
        self.days_to_keep = days_to_keep  # Días antes de eliminar
        self.send_to_trash = send_to_trash  # True: papelera, False: borrar
        self.max_size = max_size  # Tamaño máximo en bytes
        self.sorting_rules = sorting_rules  # Reglas de clasificación
```
**Descripción**: Contenedor de configuración del sistema. Agrupa todas las settings necesarias para el funcionamiento.

---

#### `SortingRule` - models/models.py
```python
class SortingRule:
    def __init__(self, folder_name: str, match_by: str, patterns: list[str]):
        self.folder_name = folder_name  # Carpeta destino
        self.match_by = match_by        # "extension" o "regex"
        self.patterns = patterns        # Patrones a evaluar
```
**Descripción**: Define una regla de clasificación. Puede coincidir por extensión (`.pdf`) o por regex (`.*Gemini.*`).

---

### **Servicios (services/)**

#### `NotificationService` - services/notification_service.py
```python
from abc import ABC, abstractmethod
from plyer import notification

class NotificationService(ABC):
    @abstractmethod
    def send_notification(self, message: str):
        pass

class PlyerNotificationService(NotificationService):
    def send_notification(self, message: str):
        notification.notify(
            title="Assistant",
            message=message,
            app_icon="assets/work.ico",
            timeout=8
        )
```
**Descripción**: 
- **`NotificationService`**: Interfaz abstracta para notificaciones
- **`PlyerNotificationService`**: Implementación usando la librería `plyer` para notificaciones del sistema operativo

---

#### `OrderedFilesRepository` - services/ordered_files_repository.py
```python
import datetime
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List
from models.models import OrderedFile

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


class JsonOrderedFilesRepository(OrderedFilesRepository):
    def __init__(self, json_file_path: str):
        self.json_file_path = json_file_path

    def get_ordered_files(self) -> List[OrderedFile]:
        with open(self.json_file_path, 'r') as json_file:
            json_data = json.load(json_file)["orderedFiles"]
            ordered_files = []
            
            for fileObject in json_data:
                name = fileObject["name"]
                ordered_date = fileObject["ordered_date"]
                path = fileObject["path"]
                ordered_date = datetime.strptime(ordered_date, "%Y-%m-%d").date()
                ordered_files.append(OrderedFile(name, ordered_date, path))
            
            return ordered_files

    def get_files_to_delete(self, days_to_keep: int) -> List[OrderedFile]:
        ordered_files = self.get_ordered_files()
        files_to_delete = []
        
        for ordered_file in ordered_files:
            current_date = datetime.now().date()
            if (current_date - ordered_file.ordered_date).days > days_to_keep:
                files_to_delete.append(ordered_file)
        
        return files_to_delete

    def save_ordered_files(self, new_ordered_files: List[OrderedFile]) -> None:
        ordered_files = self.get_ordered_files()
        ordered_files.extend(new_ordered_files)
        
        # Convertir fechas a ISO format
        for i in range(len(ordered_files)):
            ordered_files[i].ordered_date = ordered_files[i].ordered_date.isoformat()
        
        with open(self.json_file_path, "r") as json_file:
            data = json.load(json_file)
        
        data["orderedFiles"] = [obj.__dict__ for obj in ordered_files]
        
        with open(self.json_file_path, "w") as json_file:
            json_file.write(json.dumps(data, indent=4))

    def find(self, file_name: str) -> OrderedFile or None:
        ordered_files = self.get_ordered_files()
        
        for ordered_file in ordered_files:
            if ordered_file.name == file_name:
                return ordered_file
        
        return None

    def delete(self, file_name: str) -> None:
        with open(self.json_file_path, "r") as json_file:
            data = json.load(json_file)
            ordered_files = data["orderedFiles"]
            
            for file in ordered_files:
                if file["name"] == file_name:
                    ordered_files.remove(file)
                    break
        
        with open(self.json_file_path, "w") as json_file:
            json_file.write(json.dumps(data, indent=4))
```
**Descripción**:
- **`OrderedFilesRepository`**: Interfaz abstracta que define operaciones CRUD sobre archivos organizados
- **`JsonOrderedFilesRepository`**: Implementación con persistencia en JSON
  - `get_ordered_files()`: Lee todos los archivos del JSON
  - `get_files_to_delete()`: Filtra archivos que exceden el límite de días
  - `save_ordered_files()`: Persiste nuevos archivos (append)
  - `find()`: Busca un archivo por nombre
  - `delete()`: Elimina un archivo del registro

---

#### `PathRepository` - services/path_repository.py
```python
import json
from abc import ABC, abstractmethod
from models.models import PathConfig

class PathRepository(ABC):
    @abstractmethod
    def get_source_path(self) -> Path:
        pass

    @abstractmethod
    def get_destination_path(self) -> Path:
        pass


class JsonPathRepository(PathRepository):
    def __init__(self, json_file_path: str):
        self.json_file_path = json_file_path

    def get_source_path(self) -> Path:
        with open(self.json_file_path, "r") as json_file:
            destination_path = json.load(json_file)["paths"]["sourcePath"]
            return Path(destination_path)

    def get_destination_path(self) -> Path:
        with open(self.json_file_path, "r") as json_file:
            source_path = json.load(json_file)["paths"]["destinationPath"]
            return Path(source_path)
```
**Descripción**:
- **`PathRepository`**: Interfaz para acceder a rutas configuradas
- **`JsonPathRepository`**: Implementación que lee rutas desde JSON
  - `get_source_path()`: Ruta de origen (donde buscar archivos)
  - `get_destination_path()`: Ruta de destino (donde organizar)

---

#### `SettingsRepository` - services/settings_repository.py

```python
import json
from abc import ABC, abstractmethod
from typing import List
from models.models import GlobalSettings, FileSortingRule


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


class JsonSettingsRepository(SettingsRepository):
    def __init__(self, json_file_path: str):
        self.json_file_path = json_file_path

    def get_settings(self) -> GlobalSettings:
        with open(self.json_file_path, "r") as json_file:
            json_data = json.load(json_file)["settings"]

            days_to_keep = json_data["daysToKeep"]
            send_to_trash = json_data["sendToTrash"]
            max_size = json_data["maxSizeInMb"] * (1024 * 1024)  # MB a bytes
            sorting_rules = self.get_sorting_rules()

            return GlobalSettings(days_to_keep, send_to_trash, max_size, sorting_rules)

    def get_sorting_rules(self) -> List[FileSortingRule]:
        with open(self.json_file_path, "r") as json_file:
            json_data = json.load(json_file)["sortingRules"]
            sorting_rules = []

            for sorting_rule in json_data:
                folder_name = sorting_rule["folderName"]
                match_by = sorting_rule["matchBy"]
                patterns = sorting_rule["patterns"]
                sorting_rules.append(FileSortingRule(folder_name, match_by, patterns))

            return sorting_rules

    def get_default_folder(self) -> str:
        with open(self.json_file_path, "r") as json_file:
            json_data = json.load(json_file)["defaultFolder"]
            return json_data
```
**Descripción**:
- **`SettingsRepository`**: Interfaz para acceder a configuraciones
- **`JsonSettingsRepository`**: Implementación que lee configuración desde JSON
  - `get_settings()`: Retorna objeto `Settings` completo (convierte MB a bytes)
  - `get_sorting_rules()`: Retorna lista de reglas de clasificación
  - `get_default_folder()`: Retorna carpeta por defecto para archivos sin coincidencia

---

### **Helpers (helpers/)**

#### `DirectoryCreator` - helpers/directory_creator.py

```python
import os
from services.path_repository import PathRepository
from services.settings_repository import SettingsRepository


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
**Descripción**: Crea la estructura de carpetas necesaria basándose en las reglas de clasificación. Usa `exist_ok=True` para evitar errores si las carpetas ya existen.

---

### **Componentes Principales**

#### `FileSorter` - file_sorter.py

```python
import datetime
import os
import pathlib
import re
import shutil
from typing import List
from models.models import OrderedFile, FileSortingRule
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

    def __find_destination_folder(self, file_name: str,
                                  rules: List[FileSortingRule],
                                  default_folder: str) -> str:
        """
        Encuentra la carpeta destino para un archivo basándose en reglas.
        
        Args:
            file_name: Nombre del archivo con extensión
            rules: Lista de reglas de clasificación
            default_folder: Carpeta por defecto si no hay coincidencias
        
        Returns:
            Nombre de la carpeta destino
        """
        _, extension = os.path.splitext(file_name)

        for rule in rules:
            print(f"Checking rule: {rule.destination_folder} by {rule.match_by} with patterns {rule.patterns}")

            if rule.match_by == "extension":
                if extension.lower() in [p.lower() for p in rule.patterns]:
                    return rule.destination_folder

            elif rule.match_by == "regex":
                for pattern in rule.patterns:
                    print(f"Matching {file_name} against pattern {pattern}")
                    if re.match(pattern, file_name):
                        print(f"Matched {file_name} against pattern {pattern}")
                        return rule.destination_folder

        return default_folder

    def sort(self):
        """
        Clasifica y mueve archivos desde la carpeta de origen a carpetas organizadas.
        
        Flujo:
        1. Escanear archivos en sourcePath
        2. Filtrar por tamaño < maxSize
        3. Determinar carpeta destino según reglas
        4. Mover archivo
        5. Registrar en OrderedFiles
        6. Notificar usuario
        """
        # Obtener configuración
        source_path = self.__path_repository.get_source_path().name
        destination_path = self.__path_repository.get_destination_path().name
        size_limit = self.__settings_repository.get_settings().maxSizeInMb
        sorting_rules = self.__settings_repository.get_sorting_rules()
        default_folder = self.__settings_repository.get_default_folder()

        # Escanear archivos
        with os.scandir(source_path) as it:
            full_paths = [entry.path for entry in it if entry.is_file()]

        # Filtrar por tamaño
        files_to_organize = [file for file in full_paths
                             if os.path.getsize(file) < size_limit]
        ordered_files: List[OrderedFile] = []

        # Procesar cada archivo
        for current_file_path in files_to_organize:
            name_with_extension = pathlib.Path(current_file_path).name

            # Determinar carpeta destino
            destination_folder_name = self.__find_destination_folder(
                name_with_extension, sorting_rules, default_folder)

            # Crear carpeta si no existe
            destination_folder_path = os.path.join(destination_path,
                                                   destination_folder_name)
            os.makedirs(destination_folder_path, exist_ok=True)

            # Mover archivo
            destination_file_path = os.path.join(destination_folder_path,
                                                 name_with_extension)
            shutil.move(current_file_path, destination_file_path)

            # Registrar archivo organizado
            current_date = datetime.datetime.now().date()
            ordered_files.append(OrderedFile(name_with_extension,
                                             current_date,
                                             destination_file_path))

        # Persistir registros
        if ordered_files:
            self.__ordered_files_repository.save_ordered_files(ordered_files)

        # Notificar
        if len(files_to_organize) > 0:
            self.__notification_service.send_notification(
                f"{len(files_to_organize)} files were sorted")
```
**Descripción**: Componente principal de clasificación de archivos.
- **`__find_destination_folder()`**: Método privado que determina la carpeta destino evaluando reglas en orden. Soporta coincidencia por extensión (case-insensitive) y por regex.
- **`sort()`**: Método público que ejecuta el flujo completo de organización. Escanea, filtra, clasifica, mueve y registra archivos.

---

#### `Auditor` - registry_checker.py
```python
import glob
import os
from datetime import datetime
from typing import List
from send2trash import send2trash
from models.models import OrderedFile
from services.ordered_files_repository import OrderedFilesRepository
from services.path_repository import PathRepository
from services.settings_repository import SettingsRepository
from services.notification_service import NotificationService

class Auditor:
    def __init__(self, path_repository: PathRepository,
                 ordered_files_repository: OrderedFilesRepository,
                 settings_repository: SettingsRepository,
                 notificator_service: NotificationService):
        self.__path_repository = path_repository
        self.__ordered_files_repository = ordered_files_repository
        self.__settings_repository = settings_repository
        self.__notification_service = notificator_service

    def check_files(self):
        """
        Audita archivos organizados:
        1. Elimina archivos que exceden el límite de días
        2. Registra archivos existentes no registrados
        3. Limpia registros huérfanos
        4. Notifica eliminaciones
        """
        # Configuración
        destination_path = self.__path_repository.get_destination_path().name
        limit_days = self.__settings_repository.get_settings().days_to_keep
        send_to_trash = self.__settings_repository.get_settings().send_to_trash
        
        # 1. Eliminar archivos antiguos
        files_to_delete = self.__ordered_files_repository.get_files_to_delete(limit_days)
        
        for file_to_delete in files_to_delete:
            # Si el archivo no existe físicamente, solo eliminarlo del registro
            if not os.path.exists(file_to_delete.path):
                self.__ordered_files_repository.delete(file_to_delete.name)
                continue
            
            # Eliminar archivo según configuración
            if send_to_trash:
                send2trash(file_to_delete.path)  # A la papelera
            else:
                os.remove(file_to_delete.path)   # Eliminación permanente
            
            # Eliminar del registro
            self.__ordered_files_repository.delete(file_to_delete.name)
        
        # 2. Registrar archivos no registrados
        destination_paths = glob.glob(destination_path + "/**/*.*", recursive=True)
        destination_path_files = [os.path.basename(file) for file in destination_paths]
        
        not_registered_files: List[OrderedFile] = []
        
        for file, file_path in zip(destination_path_files, destination_paths):
            current_date = datetime.now().date()
            
            if not self.__ordered_files_repository.find(file):
                not_registered_files.append(OrderedFile(file, current_date, file_path))
        
        self.__ordered_files_repository.save_ordered_files(not_registered_files)
        
        # 3. Notificar eliminaciones
        if len(files_to_delete) > 0:
            self.__notification_service.send_notification(
                f"{len(files_to_delete)} files were deleted.")
```
**Descripción**: Componente de auditoría y limpieza.
- **Tarea 1**: Elimina archivos cuya fecha de organización supera el límite configurado
- **Tarea 2**: Detecta y registra archivos que existen físicamente pero no están en el registro (ej: movidos manualmente)
- **Tarea 3**: Limpia registros de archivos que ya no existen físicamente
- **Notificación**: Informa al usuario sobre archivos eliminados

---

#### `main.py` - Punto de Entrada
```python
from file_sorter import FileSorter
from helpers.directory_creator import DirectoryCreator
from registry_checker import Auditor
from services.ordered_files_repository import JsonOrderedFilesRepository
from services.path_repository import JsonPathRepository
from services.settings_repository import JsonSettingsRepository
from services.notification_service import PlyerNotificationService

def main():
    json_path = "data/settings.json"
    
    # Inicializar repositorios y servicios (Dependency Injection)
    path_repository = JsonPathRepository(json_path)
    settings_repository = JsonSettingsRepository(json_path)
    ordered_files_repository = JsonOrderedFilesRepository(json_path)
    notification_service = PlyerNotificationService()
    
    # 1. Crear directorios necesarios
    directory_creator = DirectoryCreator(path_repository, settings_repository)
    directory_creator.execute()
    
    # 2. Auditar archivos existentes
    auditor = Auditor(path_repository, ordered_files_repository, 
                     settings_repository, notification_service)
    auditor.check_files()
    
    # 3. Organizar nuevos archivos
    file_organizer = FileSorter(path_repository, settings_repository, 
                                ordered_files_repository, notification_service)
    file_organizer.sort()


if __name__ == "__main__":
    main()
```
**Descripción**: Orquestador principal del sistema.
1. **Inicialización**: Crea instancias de repositorios y servicios (inyección de dependencias manual)
2. **Preparación**: Crea estructura de carpetas
3. **Auditoría**: Limpia archivos antiguos y sincroniza registro
4. **Organización**: Clasifica y mueve archivos nuevos

---

## 🔄 Flujo de Ejecución

```
main()
  │
  ├─> JsonPathRepository(json_path)
  ├─> JsonSettingsRepository(json_path)
  ├─> JsonOrderedFilesRepository(json_path)
  └─> PlyerNotificationService()
  │
  ├─> DirectoryCreator.execute()
  │     └─> Crea carpetas: destinationPath/folderName
  │
  ├─> Auditor.check_files()
  │     ├─> Elimina archivos > daysToKeep
  │     ├─> Registra archivos no registrados
  │     └─> Notifica: "X files were deleted"
  │
  └─> FileSorter.sort()
        ├─> Escanea sourcePath
        ├─> Filtra por tamaño < maxSize
        ├─> Por cada archivo:
        │     ├─> Determina carpeta (extension/regex)
        │     ├─> Mueve archivo: shutil.move()
        │     └─> Registra: OrderedFile
        └─> Notifica: "X files were sorted"
```

---

## 📊 Relaciones de Dependencias

```
FileSorter
  ├── PathRepository (get_source_path, get_destination_path)
  ├── SettingsRepository (get_settings, get_sorting_rules, get_default_folder)
  ├── OrderedFilesRepository (save_ordered_files)
  └── NotificationService (send_notification)

Auditor
  ├── PathRepository (get_destination_path)
  ├── SettingsRepository (get_settings)
  ├── OrderedFilesRepository (get_files_to_delete, find, delete, save_ordered_files)
  └── NotificationService (send_notification)

DirectoryCreator
  ├── PathRepository (get_destination_path)
  └── SettingsRepository (get_sorting_rules)
```

---

## 🛠️ Patrones de Diseño

### 1. Repository Pattern
Abstrae la capa de persistencia mediante interfaces:
```python
class OrderedFilesRepository(ABC):  # Interfaz
    @abstractmethod
    def get_ordered_files(self) -> List[OrderedFile]:
        pass

class JsonOrderedFilesRepository(OrderedFilesRepository):  # Implementación
    def get_ordered_files(self) -> List[OrderedFile]:
        # Implementación específica con JSON
```

### 2. Dependency Injection
Las dependencias se inyectan en el constructor:
```python
class FileSorter:
    def __init__(self, path_repository: PathRepository,  # Interfaz, no implementación
                 settings_repository: SettingsRepository,
                 ordered_files_repository: OrderedFilesRepository,
                 notificator_service: NotificationService):
        # ...
```

### 3. Single Responsibility Principle
Cada clase tiene una única responsabilidad:
- `FileSorter`: Solo clasifica archivos
- `Auditor`: Solo audita y limpia
- `DirectoryCreator`: Solo crea carpetas
- Repositorios: Solo acceden a datos

---

## 📦 Dependencias Externas

```python
# Notificaciones del sistema
from plyer import notification

# Enviar archivos a papelera (multiplataforma)
from send2trash import send2trash

# Módulos estándar
import datetime      # Manejo de fechas
import os           # Operaciones de archivos
import pathlib      # Manipulación de rutas
import re           # Expresiones regulares
import shutil       # Mover archivos
import json         # Persistencia
import glob         # Buscar archivos
from abc import ABC, abstractmethod  # Clases abstractas
from typing import List  # Type hints
```

---

## 🔑 Conceptos Clave

### Métodos Privados (Name Mangling)
```python
def __find_destination_folder(self, ...):  # Privado (__)
    pass

def sort(self):  # Público
    pass
```

### Type Hints
```python
def get_ordered_files(self) -> List[OrderedFile]:  # Retorna lista de OrderedFile
    pass

def find(self, file_name: str) -> OrderedFile or None:  # Puede retornar None
    pass
```

### Conversión de Unidades
```python
# MB a bytes
max_size = json_data["maxSizeInMb"] * (1024 * 1024)
```

### Fechas ISO Format
```python
# Guardar: datetime.date -> str
ordered_file.ordered_date.isoformat()  # "2025-11-08"

# Cargar: str -> datetime.date
datetime.strptime(ordered_date, "%Y-%m-%d").date()
```

---

## 🎯 Ejemplo de Uso

```python
# Configuración en settings.json
{
  "sortingRules": [
    {"folderName": "PDF", "matchBy": "extension", "patterns": [".pdf"]},
    {"folderName": "Gemini", "matchBy": "regex", "patterns": [".*Gemini.*"]}
  ],
  "defaultFolder": "Other"
}

# Ejecución
python main.py

# Resultado:
# documento.pdf -> Organized/PDF/documento.pdf
# Gemini_Image.png -> Organized/Gemini/Gemini_Image.png
# archivo.xyz -> Organized/Other/archivo.xyz
```

---

## 📝 Notas Técnicas

- **Persistencia**: JSON con `indent=4` para legibilidad
- **Atomic operations**: Lectura completa, modificación, escritura completa
- **Case-insensitive**: Extensiones se comparan en minúsculas
- **Regex**: Usa `re.match()` (desde el inicio de la cadena)
- **Carpetas dinámicas**: Se crean con `exist_ok=True`
- **Orden de reglas**: Primera coincidencia gana
- **Archivos grandes**: No se organizan si exceden `maxSize`

---

**Lenguaje**: Python 3.x  
**Arquitectura**: Layered Architecture + Repository Pattern  
**Principios**: SOLID, Dependency Injection, Abstraction
