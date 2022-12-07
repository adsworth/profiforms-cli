from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
import typing

from pfcli import config

Destination = str


@dataclass
class Source:
    type: str
    destination: str
    paths: typing.List[str]


@dataclass
class RuntimeEnvironment:
    name: str
    platform: str
    command_line: str

    program_version: str

    program_result_log: str
    program_result_preview: str
    program_result_type: str
    program_result_value: int


@dataclass
class TestdataFile:
    name: str
    description: str
    path: Path

    def __post_init__(self):
        self.path = Path(self.path)


@dataclass
class Testdata:
    destination: str
    files: typing.List[TestdataFile]


@dataclass
class TransactionFormPageBackgroundFile:
    page_name: str
    path: Path

    def __post_init__(self):
        self.path = Path(self.path)


@dataclass
class TransactionFormPageBackground:
    destination: str
    files: typing.List[TransactionFormPageBackgroundFile]


@dataclass
class TransactionFormMaterial:
    name: str
    description: str
    width: str
    height: str
    thickness: str
    weight: str


class Package:
    def __init__(self, basepath: Path, config: dict):
        self.includes = []

        self.basepath: Path = basepath.resolve()
        self.config: config.Config = config

    @property
    def name(self) -> str:
        try:
            return self.config["name"]
        except KeyError:
            return f"{ self.basepath.stem }"

    @property
    def description(self):
        try:
            return self.config["description"]
        except KeyError:
            return f"{ self.name }"

    @property
    def archive_name(self):
        try:
            return self.config["archive_name"]
        except KeyError:
            return f"{ self.name }"

    @property
    def transaction_form(self) -> Path:
        return Path(self.config["transaction_form"])

    def append_include(self, package: "Package"):
        self.includes.append(package)

    def get_destinations(self) -> typing.List[Destination]:
        destinations = (
            self.config["destination"] if "destination" in self.config else []
        )
        return [d["name"] for d in destinations]

    def get_destination_path(self, destination: Destination) -> Path:
        try:
            destinations = (
                self.config["destination"] if "destination" in self.config else []
            )
            _d = [d["path"] for d in destinations if d["name"] == destination]
            return Path(next(iter(_d)))
        except StopIteration:
            raise KeyError((f"Unknown destination '{destination}'"))

    def get_all_sources(self) -> typing.List[Source]:
        _sources = self.config["source"] if "source" in self.config else []
        return [Source(**s) for s in _sources]

    def get_sources(
        self, destination: typing.Optional[Destination] = None
    ) -> typing.List[dict]:
        sources = self.get_all_sources()
        sources = [source for source in sources if source.destination == destination]
        paths = self._get_list_extended(sources, "paths")
        return paths

    def _get_list_extended(self, _list: typing.List[dict], _key):
        values = []

        for _item in _list:
            if hasattr(_item, _key):
                values.extend(getattr(_item, _key))
            elif _key in _item:
                values.extend(_item[_key])

        return values

    def get_source_files(self, destination: Path) -> typing.List[Path]:
        sources = self.get_sources(destination)
        files = self._expand_patterns(sources)
        return files

    def _expand_patterns(self, patterns: typing.List[str]) -> typing.List[Path]:
        files = []

        path = Path(self.basepath)
        for pattern in patterns:
            pattern_path = Path(pattern)
            pattern_base = (
                self.basepath
                if pattern_path.parent == "."
                else self.basepath.joinpath(*pattern_path.parts[:1])
            )
            pattern_files = list(path.glob(pattern))
            files.extend(f.relative_to(self.basepath) for f in pattern_files)

        return files

    def get_test_data(self) -> Testdata:
        testdata = self.config["testdata"]

        if "destination" not in testdata:
            raise ValueError(
                f"No destination in section testdata of package {self.name}.\n"
                "The section testdata has to have a destination"
            )

        if "file" not in testdata:
            raise ValueError(
                f"No file define for section testdata of package {self.name}.\n"
                "The section testdata has to have at least one file."
            )

        files = [TestdataFile(**tf) for tf in testdata["file"]]
        testdata = Testdata(testdata["destination"], files)
        return testdata

    def get_font_definition(self) -> dict:
        fontdefinition = self.config["fontdefinition"]
        fontdefinition["path"] = Path(fontdefinition["path"])
        return fontdefinition

    def get_transaction_form_page_background(self) -> TransactionFormPageBackground:
        backgrounds = self.config["transaction_form_page_background"]

        if "destination" not in backgrounds:
            raise ValueError(
                f"No destination in section transaction_form_page_background of package {self.name}.\n"
                "The section transaction_form_page_background has to have a destination"
            )

        if "file" not in backgrounds:
            raise ValueError(
                f"No file define for section transaction_form_page_background of package {self.name}.\n"
                "The section transaction_form_page_background has to have at least one file."
            )

        files = [TransactionFormPageBackgroundFile(**bf) for bf in backgrounds["file"]]
        transaction_forms = TransactionFormPageBackground(
            backgrounds["destination"], files
        )
        return transaction_forms

    def get_supplement_logical(self) -> dict:
        return self.config["supplement"]["logical"]

    def get_supplement_physical(self) -> dict:
        return self.config["supplement"]["physical"]

    def get_shipment_postage(self) -> dict:
        return self.config["shipment"]["postage"]

    def get_whitespace(self) -> dict:
        return self.config["whitespace"]

    def get_transaction_form_materials(self) -> typing.List[TransactionFormMaterial]:
        materials = self.config["transaction_form_material"]
        try:
            materials = [TransactionFormMaterial(**material) for material in materials]
        except TypeError as err:
            raise ValueError(
                f"Invalid section transaction_form_material in package {self.name}.\n"
                "The section transaction_form_material has to be of type list and\n!"
                "have the correct properties."
            )

        return materials

    def get_input_variables(self) -> typing.List[dict]:
        return self.config["input_variable"]

    def get_runtime_environments(self) -> typing.List[RuntimeEnvironment]:
        envs = self.config["runtime_environment"]
        return [RuntimeEnvironment(**e) for e in envs]


def load_package(path: Path) -> Package:

    if path in _packages:
        return _packages[path]

    conf = config.load(path)
    package = Package(path, conf)
    _packages[path] = package

    if "include" in package.config:
        for inc in package.config["include"]:
            inc_path = Path(inc)
            if inc_path.is_absolute():
                raise ValueError(
                    f"Include '{inc}' in package '{package.name}' is not relative. "
                    "Include paths for packages have to be relative to the package that is including them."
                )
            package_path = path.joinpath(inc_path).resolve()
            if package_path.is_relative_to(package.basepath):
                raise ValueError1(
                    f"Include '{inc}' in package '{package.name}' is subpath of the package. "
                    "Include paths for packages outside of the package that is including them."
                )

            p = load_package(package_path)
            package.append_include(p)

    return package


# a dict of processed packages.
_packages: typing.OrderedDict[Path, Package] = OrderedDict()
