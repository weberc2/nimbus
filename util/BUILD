load("std/python", "py_source_library")
load("//core", nimbus_core = "lib")

lib = py_source_library(
    name = "lib",
    package_name = "nimbus-util",
    sources = glob("setup.py", "src/nimbus_util/**.py"),
    dependencies = [ nimbus_core ],
)