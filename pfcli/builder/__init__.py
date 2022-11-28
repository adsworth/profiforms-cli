from functools import cached_property
from pathlib import Path
from pprint import pformat
from shutil import rmtree, copy2, make_archive
import typing

from pfcli.package import Package, Destination, RuntimeEnvironment
from pfcli.config import decho, BUILD_DIR, BUILD_DIR_FILE, RS_PACKAGE_CONFIGURATION
from .xml_generator import get_rs_package_xml_generator


class Builder:
    def __init__(self, package: Package):
        self.packages: typing.List[Package] = []
        self.build_package = package
        self.packages.append(package)
        self.packages.extend(self._resolve_includes(package))
        self.packages = list(reversed(self.packages))

    @cached_property
    def build_path(self) -> Path:
        return self.build_package.basepath.joinpath(BUILD_DIR)

    @cached_property
    def available_destinations(self) -> typing.List[Destination]:
        """Retrieve the list of all configured destinations
        from the package and it's includes.
        """
        destinations = []

        for package in self.packages:
            decho(f"package {package.name}")
            _destinations = package.get_destinations()

            for destination in _destinations:
                if destination in destinations:
                    raise ValueError(
                        f"Destination '{destination}' from package '{package.name}' has already been defined.\n"
                        "Redefinition of destinations is not allowed"
                    )

            destinations.extend(_destinations)

        return destinations

    @cached_property
    def required_destinations(self) -> typing.List[Destination]:
        destinations = []

        try:
            for package in self.packages:
                sources = package.get_all_sources()
                for source in sources:
                    destinations.append(source["destination"])
        except KeyError:
            raise KeyError(
                f"No destination defined in source '{source}' in package '{package}'"
            )

        return destinations

    def _resolve_includes(self, package):
        includes = []
        for include in package.includes:
            includes.append(include)
            includes.extend(self._resolve_includes(include))
        return includes

    def initialise_build_path(self):
        build_dir_file = self.build_path.joinpath(BUILD_DIR_FILE)
        if self.build_path.exists():
            if not self.build_path.is_dir():
                raise ValueError(
                    f"build dir '{BUILD_DIR}' exists, but is not a directory."
                )

            if not build_dir_file.exists():
                raise ValueError(
                    f"directory '{BUILD_DIR}' exists, but is not a build directory."
                    f"It is missing the { BUILD_DIR_FILE } file."
                )

        # make sure build dir is emtpy
        rmtree(self.build_path, ignore_errors=True)
        self.build_path.mkdir()
        build_dir_file.touch()

    def get_destination_path(self, destination: Destination) -> Path:
        for package in self.packages:
            try:
                dest_path = package.get_destination_path(destination)

                p = self.build_path.joinpath(dest_path).resolve()

                path_valid = not (
                    not p.is_relative_to(self.build_path) or dest_path.is_absolute()
                )

                if not path_valid:
                    raise ValueError(
                        f"Destination path '{dest_path}' for destination '{destination}' is invalid.\n"
                        f"Destination paths can't be absolute or traverse out of the build directory."
                    )
                return dest_path
            except KeyError:
                pass  # we just continue with the net package

        raise ValueError(
            f"Unknown destination '{destination}'.\n"
            f"Destination '{destination}' isn't defined in any of the processed packages '{ *[p.name for p in self.packages],}'."
        )

    def get_font_definition(self):
        for package in reversed(self.packages):
            try:
                return package.get_font_definition()
            except KeyError:
                pass  # we just continue with the next package

        raise ValueError(
            f"No section fontdefinition.\n"
            f"The section fontdefinition isn't defined in any of the processed packages '{ *[p.name for p in self.packages],}'."
        )

    def get_supplement_logical(self):
        for package in reversed(self.packages):
            try:
                return package.get_supplement_logical()
            except KeyError:
                pass  # we just continue with the next package

        raise ValueError(
            f"No section supplement.logical.\n"
            f"The section supplement.logical isn't defined in any of the processed packages '{ *[p.name for p in self.packages],}'."
        )

    def get_supplement_physical(self):
        for package in reversed(self.packages):
            try:
                return package.get_supplement_physical()
            except KeyError:
                pass  # we just continue with the next package

        raise ValueError(
            f"No section supplement.physical.\n"
            f"The section supplement.physical isn't defined in any of the processed packages '{ *[p.name for p in self.packages],}'."
        )

    def get_shipment_postage(self):
        for package in reversed(self.packages):
            try:
                return package.get_shipment_postage()
            except KeyError:
                pass  # we just continue with the next package

        raise ValueError(
            f"No section shipment.postage.\n"
            f"The section shipment.postage isn't defined in any of the processed packages '{ *[p.name for p in self.packages],}'."
        )

    def get_whitespace(self):
        for package in reversed(self.packages):
            try:
                return package.get_whitespace()
            except KeyError:
                pass  # we just continue with the next package

        raise ValueError(
            f"No section whitespace.\n"
            f"The section whitespace isn't defined in any of the processed packages '{ *[p.name for p in self.packages],}'."
        )

    def get_transaction_form_page_background(self) -> dict:
        for package in reversed(self.packages):
            try:
                return package.get_transaction_form_page_background()
            except KeyError:
                pass  # we just continue with the next package

        raise ValueError(
            f"No section transaction_form_page_background.\n"
            f"The section transaction_form_page_background isn't defined in any of the processed packages '{ *[p.name for p in self.packages],}'."
        )

    def get_input_variables(self) -> typing.List:
        for package in reversed(self.packages):
            try:
                return package.get_input_variables()
            except KeyError:
                pass  # we just continue with the next package
        return []

    def get_transaction_form_materials(self) -> typing.List:
        for package in reversed(self.packages):
            try:
                return package.get_transaction_form_materials()
            except KeyError:
                pass  # not all package have to have materials defined
        raise KeyError(
            f"no material defined.\n"
            f"At least one material has to be defined in one of the processed packages '{ *[p.name for p in self.packages],}'."
        )

    def get_runtime_environments(self) -> typing.List[RuntimeEnvironment]:
        runtimes = []
        for package in reversed(self.packages):
            try:
                _re = package.get_runtime_environments()
                runtimes.extend(_re)
            except KeyError:
                pass  # not all package have to have runtime environments defined
        if not runtimes:
            raise KeyError(
                f"no runtime_environment defined.\n"
                f"At least one runtime_environment has to be defined in one of the processed packages '{ *[p.name for p in self.packages],}'."
            )

        return runtimes

    def get_test_data(self) -> dict:
        for package in reversed(self.packages):
            try:
                return package.get_test_data()
            except KeyError:
                pass  # we just continue with the next package
        return {}

    def copy_files(self):
        dests_in_sources = self.required_destinations

        for source_destination in dests_in_sources:
            if source_destination not in self.available_destinations:
                raise KeyError(
                    f"Destination '{source_destination}' not defined. Available destinations '{ *self.available_destinations, }'."
                )

        decho(pformat(self.available_destinations))

        package_files = []
        for package in self.packages:
            decho(f"Package basepath:{package.basepath}")
            for destination in self.available_destinations:
                decho(f"Destination:{destination}")
                files = package.get_source_files(destination)
                dest_path = self.get_destination_path(destination)
                for f in files:
                    source = package.basepath.joinpath(f).resolve()
                    # if the source file is in a subdirectory pop of
                    # the first subdirectory.
                    if len(f.parents) > 1:
                        f = f.relative_to(f.parents[0])

                    dest = self.build_path.joinpath(dest_path, f).resolve()
                    decho(f"copy from '{source}' to '{dest}'")
                    package_files.append({"source": source, "dest": dest})

            # copy the test data
            # test data isn't required so we catch KeyError"
            try:
                testdata = package.get_test_data()
                try:
                    dest_path = self.get_destination_path(testdata["destination"])
                except KeyError:
                    raise ValueError(
                        f"destination missing.\n"
                        f"testdata section in package {package.name} must have a destination."
                    )

                for testdata_file in testdata["file"]:
                    testfile = testdata_file["path"]
                    source = package.basepath.joinpath(testfile).resolve()
                    # if the source file is in a subdirectory pop of
                    # the first subdirectory.
                    if len(testfile.parents) > 1:
                        testfile = testfile.relative_to(testfile.parents[0])

                    dest = self.build_path.joinpath(dest_path, testfile).resolve()

                    decho(f"copy testdata from '{source}' to '{dest}'")
                    package_files.append({"source": source, "dest": dest})
            except KeyError:
                pass

            # copy the backgrounds
            # backgrounds aren't required so we catch KeyError"
            try:
                backgrounds = package.get_transaction_form_page_backgrounds()
                try:
                    dest_path = self.get_destination_path(backgrounds["destination"])
                except KeyError:
                    raise ValueError(
                        f"destination missing.\n"
                        f"transactionformpagebackgrounds section in package {package.name} must have a destination."
                    )

                for background_file in backgrounds["file"]:
                    _file = background_file["path"]
                    source = package.basepath.joinpath(_file).resolve()
                    # if the source file is in a subdirectory pop of
                    # the first subdirectory.
                    if len(_file.parents) > 1:
                        _file = _file.relative_to(_file.parents[0])

                    dest = self.build_path.joinpath(dest_path, _file).resolve()

                    decho(f"copy background from '{source}' to '{dest}'")
                    package_files.append({"source": source, "dest": dest})
            except KeyError:
                pass

            # copy the font definition fonts.ini
            # a font definition is required in at least one package"
            try:
                fontdef = package.get_font_definition()
                try:
                    dest_path = self.get_destination_path(fontdef["destination"])
                except KeyError:
                    raise ValueError(
                        f"destination missing.\n"
                        f"fontdefinition section in package {package.name} must have a destination."
                    )

                font_ini = fontdef["path"]
                source = package.basepath.joinpath(font_ini).resolve()
                # if the source file is in a subdirectory pop of
                # the first subdirectory.
                if len(font_ini.parents) > 1:
                    font_ini = font_ini.relative_to(font_ini.parents[0])

                dest = self.build_path.joinpath(dest_path, font_ini).resolve()

                decho(f"copy testdata from '{source}' to '{dest}'")
                package_files.append({"source": source, "dest": dest})
            except KeyError:
                pass

        for package_file in package_files:
            package_file["dest"].parent.mkdir(parents=True, exist_ok=True)
            copy2(package_file["source"], package_file["dest"])

    def generate_package_file(self):
        rs_package_file = self.build_path.joinpath(RS_PACKAGE_CONFIGURATION)
        with open(rs_package_file, "w") as conf_file:
            generator = get_rs_package_xml_generator(self)
            _xml = generator.get_xml()
            conf_file.write(_xml)

    def zip_package(self):
        _basename = self.build_package.archive_name
        make_archive(base_name=_basename, format="zip", root_dir=self.build_path)
        pass
