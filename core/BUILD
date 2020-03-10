load("std/python", "py_source_library")
load("3rdParty", "black_check", "typing_extensions")

src = glob("setup.py", "src/nimbus_core/**.py")

lib = py_source_library(
    name = "lib",
    package_name = "nimbus-core",
    sources = src,
    dependencies = [ typing_extensions ],
)

core_black = black_check(name = "core_black", sources = [ src ])