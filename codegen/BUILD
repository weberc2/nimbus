load("std/python", "py_source_library", "py_source_binary", "pypi")

black = pypi(
    name = "black",
    constraint = "==19.10b0",
    dependencies = [
        pypi(name = "appdirs", constraint = "==1.4.3"), # black: Any
        pypi(name = "attrs", constraint = "==19.3.0"), # black: >=18.1.0
        pypi(name = "click", constraint = "==7.0"), # black: >=6.5
        pypi(name = "pathspec", constraint = "==0.6.0"), # black: >=0.6,<1
        pypi(name = "regex", constraint = "==2019.11.1"), # black: Any
        pypi(name = "toml", constraint = "==0.10.0"), # black: >=0.9.4
        pypi(name = "typed-ast", constraint = "==1.4.0"), # black: >=1.4.0
    ],
)

lib = py_source_library(
    name = "lib",
    package_name = "nimbus-codegen",
    sources = glob("setup.py", "src/nimbus_codegen/**.py"),
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