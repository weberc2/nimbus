load("std/command", "bash")
load("std/python", "py_source_library")
load("3rdParty", black = "black_bin")
load("codegen", nimbus_codegen="bin")
load("core", nimbus_core="lib")

src = bash(
    name = "src",
    environment = {
        "NIMBUS_CODEGEN": nimbus_codegen,
        "BLACK": black,
    },
    script = "$NIMBUS_CODEGEN $OUTPUT && $BLACK $OUTPUT",
)

lib = py_source_library(
    name = "lib",
    sources = src,
    dependencies = [ nimbus_core ],
)