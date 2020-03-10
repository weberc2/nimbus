load("std/python", "py_source_library", "py_source_binary", "pypi")
load("3rdParty", "black_check", black = "black")

src = glob("setup.py", "src/nimbus_codegen/**.py")

lib = py_source_library(
    name = "lib",
    package_name = "nimbus-codegen",
    sources = src,
    dependencies = [
        black,
        pypi(name = "typing-extensions", constraint = "==3.7.4.1")
    ],
)

bin = py_source_binary(
    name = "bin",
    package_name = "nimbus_codegen",
    sources = glob("setup.py", "src/nimbus_codegen/**.py"),
    dependencies = [ lib ],
    entry_point = "main",
)

codegen_black = black_check(name = "codegen_black", sources = [src])