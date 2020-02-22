import os

import setuptools

setuptools.setup(
    name="nimbus-codegen",
    version=os.environ.get("BUILD_VERSION", "0.0.0.dev-1"),
    package_dir={"": "src"},
    packages=setuptools.find_packages("src"),
    provides=setuptools.find_packages("src"),
    entrypoints={"console_scripts": ["nimbus_codegen = nimbus_codegen.__main__:main"],},
)
