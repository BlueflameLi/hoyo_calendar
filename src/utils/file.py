import json
import aiofiles
import tomllib

from pathlib import Path
from abc import abstractmethod
from icalendar import Calendar


class File:
    def __init__(self, path: Path):
        self.path = path
        if not self.path.is_file:
            raise TypeError(f"{path} is not a file")
        directory_path = self.path.parent
        if not directory_path.exists():
            directory_path.mkdir(parents=True)

    @abstractmethod
    def write(self, content: str | int | bytes | dict):
        pass

    @abstractmethod
    def read(self, encoding: str = "utf-8") -> dict:
        pass

    @abstractmethod
    async def write_async(self, content: str | int | bytes | dict) -> None:
        pass

    @abstractmethod
    async def read_async(self, encoding: str = "utf-8") -> dict:
        pass


class TomlFile(File):
    def __init__(self, path: Path):
        super().__init__(path)
        if not self.path.suffix == ".toml":
            raise TypeError(f"{path} is not a toml file")

    def read(self, encoding: str = "utf-8") -> dict:
        with open(self.path, "r", encoding=encoding) as f:
            content = f.read()
            return tomllib.loads(content)

    async def read_async(self, encoding: str = "utf-8") -> dict:
        async with aiofiles.open(self.path, "r", encoding=encoding) as f:
            content = await f.read()
            return tomllib.loads(content)


class JsonFile(File):
    def __init__(self, path: Path):
        super().__init__(path)
        if not self.path.suffix == ".json":
            raise TypeError(f"{path} is not a json file")

    def read(self, encoding: str = "utf-8") -> dict:
        try:
            with open(self.path, "r", encoding=encoding) as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    async def read_async(self, encoding: str = "utf-8") -> dict:
        async with aiofiles.open(self.path, "r", encoding=encoding) as f:
            content = await f.read()
            if not content.strip():
                return {}
            return json.loads(content)

    def write(self, content: str | int | bytes | dict) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(json.dumps(content, ensure_ascii=False))

    async def write_async(self, content: str | int | bytes | dict) -> None:
        async with aiofiles.open(self.path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(content, ensure_ascii=False))


class ICS_File(File):
    def __init__(self, path: Path):
        super().__init__(path)
        if not self.path.suffix == ".ics":
            raise TypeError(f"{path} is not a ics file")

    async def write_async(self, calendar: Calendar) -> None:
        async with aiofiles.open(self.path, "wb") as ics_file:
            await ics_file.write(calendar.to_ical())
