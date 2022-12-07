from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pfcli.builder import Builder


class RsPackage:
    def __init__(self, builder: Builder):
        self.builder = builder
        self.home = (
            "${home}"  # Profiforms uses {home} in their package xml, so we define home.
        )

    @property
    def runtime_environments(self):
        runtime_envs = self.builder.get_runtime_environments()
        _string = "\n" + "\n".join(
            [
                f"""\t\t<runtimeEnvironment platform="{e.platform}">
                  <program name="{e.name}" version="{e.program_version}" />
                  <cmdLine>{e.command_line}</cmdLine>
                  <programResult>
                    <log>{e.program_result_log}</log>
                    <preview>{e.program_result_preview}</preview>
                    <result type="{e.program_result_type}">{e.program_result_value}</result>
                  </programResult>
                </runtimeEnvironment>"""
                for e in runtime_envs
            ]
        )
        return _string

    @property
    def transaction_form_page_backgrounds(self):
        background = self.builder.get_transaction_form_page_background()
        _string = "\n" + "\n".join(
            [
                f'\t\t<transactionFormPageBackground pageName="{f.page_name}">{self.make_package_home_path(f.path)}</transactionFormPageBackground>'
                for f in background.files
            ]
        )
        return _string

    @property
    def materials(self):
        materials = self.builder.get_transaction_form_materials()
        _string = "\n" + "\n".join(
            [
                f'\t\t<material name="{m.name}" description="{m.description}" width="{m.width}" height="{m.height}" thickness="{m.thickness}" weight="{m.weight}" />'
                for m in materials
            ]
        )
        return _string

    @property
    def test_data(self):
        try:
            test_data = self.builder.get_test_data()
            _string = "\n" + "\n".join(
                [
                    f"\t\t<testData><name>{f.name}</name><description>{f.description}</description><value>{self.make_package_home_path(f.path)}</value></testData>"
                    for f in test_data.files
                ]
            )
            return _string
        except KeyError:
            pass

    @property
    def input_variables(self):
        variables = self.builder.get_input_variables()
        _string = "\n" + "\n".join(
            [
                f'\t\t<inputVariable><name>{v["name"]}</name><description>{v["description"]}</description></inputVariable>'
                for v in variables
            ]
        )
        return _string

    def make_package_home_path(self, path: Path) -> Path:
        _abs = path.absolute()
        _path = _abs.relative_to(Path.cwd())
        return f"{self.home}/{_path}"

    def get_xml(self):
        package = self.builder.build_package
        # FIX: acutally use the path in the package
        font_def_loc = self.builder.get_font_definition()["path"]
        supplement_logical = self.builder.get_supplement_logical()
        supplement_physical = self.builder.get_supplement_physical()
        shipment_postage = self.builder.get_shipment_postage()
        whitespace = self.builder.get_whitespace()

        return f"""<?xml version="1.0" encoding="utf-8"?>
<?pte APIVersion="0.0.02"?>
<package type="transaction" name="{package.name}" description="{package.description}" version="3.1">
  <configurationSet>
    <runtimeEnvironments>{self.runtime_environments}</runtimeEnvironments>
    <transactionForm>{self.make_package_home_path(package.transaction_form)}</transactionForm>
    <transactionFormPageBackgrounds>{self.transaction_form_page_backgrounds}</transactionFormPageBackgrounds>
    <fontDef>
        <location>{self.make_package_home_path(font_def_loc)}</location>
    </fontDef>
    <transactionFormMaterials>{self.materials}</transactionFormMaterials>
    <testDataSet>{self.test_data}</testDataSet>
    <inputVariableSet>{self.input_variables}</inputVariableSet>
  </configurationSet>
  <supplement>
    <logicalSupplement>
      <allowed>{supplement_logical["allowed"]}</allowed>
      <useOnlyTransactionFormPaper>{supplement_logical["use_only_transaction_form_paper"]}</useOnlyTransactionFormPaper>
    </logicalSupplement>
    <physicalSupplement>
      <allowed>{supplement_physical["allowed"]}</allowed>
    </physicalSupplement>
  </supplement>
  <shipment>
    <postage>
      <optionalSupplementCanExceedPostage>{shipment_postage["optional_supplement_can_exceed_postage"]}</optionalSupplementCanExceedPostage>
      <whitespaceCanExceedPostage>{shipment_postage["whitespace_can_exceed_postage"]}</whitespaceCanExceedPostage>
    </postage>
  </shipment>
  <whitespace>
    <allowed>{whitespace["allowed"]}</allowed>
    <maxSpace>{whitespace["max_space"]}</maxSpace>
    <overflow>{whitespace["overflow"]}</overflow>
    <partSet />
  </whitespace>
</package>
"""


class RsPackageAPIVersion_0_0_02(RsPackage):
    pass


def get_rs_package_xml_generator(builder: Builder):
    return RsPackageAPIVersion_0_0_02(builder=builder)
