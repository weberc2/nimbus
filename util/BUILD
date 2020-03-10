load("std/python", "py_source_library")
load("3rdParty", "black_check")
load("//core", nimbus_core = "lib")

src = glob("setup.py", "src/nimbus_util/**.py")

lib = py_source_library(
    name = "lib",
    package_name = "nimbus-util",
    sources = src,
    dependencies = [ nimbus_core ],
)

util_black = black_check(name = "util_black", sources = [ src ])