load("std/python", "pex")
load("std/command", "bash")
load("codegen", "codegen_black")
load("core", "core_black")
load("util", "util_black")
load("examples", "examples_black")
load("test", "test_black", "smoke")

def meta(name, dependencies):
    return mktarget(
        name = name,
        type = "noop",
        args = {"dependencies": dependencies},
    )

black = meta(
    name = "black",
    dependencies = [
        codegen_black,
        core_black,
        examples_black,
        test_black,
        util_black,
    ],
)

tests = meta(name = "tests", dependencies = [ smoke ])

checks = meta(name = "checks", dependencies = [smoke, black])