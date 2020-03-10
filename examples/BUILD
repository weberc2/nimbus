load("std/python", "py_source_binary", "pypi")
load("3rdParty", "black_check", "typing_extensions")
load("resources", nimbus_resources="lib")
load("core", nimbus_core="lib")

src = glob("setup.py", "src/nimbus_examples/**.py")

s3bucket = py_source_binary(
    name = "s3bucket",
    package_name = "nimbus_examples",
    sources = src,
    dependencies = [ typing_extensions, nimbus_core, nimbus_resources ],
    entry_point = "s3bucket",
)

examples_black = black_check(name = "examples_black", sources = [ src ])