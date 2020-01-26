import os
from typing import Callable, List

import black

from nimbus_codegen.ast import PythonType
from nimbus_codegen.spec import Specification
from nimbus_codegen.typedef import resource_namespace

Formatter = Callable[[str], str]


def FORMATTER_NONE(s: str) -> str:
    return s


def FORMATTER_BLACK(s: str) -> str:
    return black.format_str(
        s, mode=black.FileMode(target_versions={black.TargetVersion.PY36})
    )


def render_module(module: str, typedefs: List[PythonType]) -> str:
    typedef_output = ""
    import_output = f"from . import {module}"
    imports = {module}
    for typedef in typedefs:
        typedefstr, typedefimports = typedef.serialize_python_type_definition(indent="")
        typedef_output += f"\n\n{typedefstr}"
        for import_ in typedefimports:
            if import_ not in imports:
                import_output += f"\nimport {import_}"
            imports.add(import_)
    return f"{import_output}{typedef_output}"


def write_resources_package(
    spec: Specification, directory: str, formatter: Formatter = FORMATTER_NONE
) -> None:
    known_packages = set()
    for resource_type in spec.ResourceTypes:
        # Compute module name
        idx = resource_type.rfind("::")
        if idx < 0:
            idx = 0
        else:
            idx += len("::")
        module = resource_type[idx + len("::") :].lower()

        # Compute file path
        rt = resource_type
        if rt.startswith("AWS::"):
            rt = rt[len("AWS::") :]
        filepath = os.path.join(
            directory, f"{resource_type.lower().replace('::', '/')}.py"
        )

        # Make it a Python package (not to be confused with a Pypi package,
        # which is what this whole function creates)
        parent_directory = os.path.dirname(filepath)
        if parent_directory not in known_packages:
            os.makedirs(parent_directory, exist_ok=True)
            with open(os.path.join(parent_directory, "__init__.py"), "w") as f:
                f.write("")
            known_packages.add(parent_directory)

        # Render the file
        with open(filepath, "w") as f:
            f.write(
                formatter(
                    render_module(
                        module, resource_namespace(module, spec, resource_type)
                    )
                )
            )

    with open(os.path.join(directory, "setup.py"), "w") as f:
        f.write(
            """import os

import setuptools

setuptools.setup(
    name="nimbus-resources",
    version=os.environ.get("BUILD_VERSION", "0.0.0.dev-1"),
    package_dir={"": "src"},
    packages=setuptools.find_packages("src"),
    provides=setuptools.find_packages("src"),
)"""
        )
