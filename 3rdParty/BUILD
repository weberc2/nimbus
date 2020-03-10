load("std/python", "pypi", "pex")
load("std/command", "bash")

typing_extensions = pypi(name = "typing_extensions")

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

black_bin = pex(
    name = "black_bin",
    entry_point = "main",
    bin_package = black,
    bin_package_name = "black",
)

def black_check(name, sources):
    environment = {
        "SOURCE_{}".format(i): source for i, source in enumerate(sources)
    }
    environment["BLACK"] = black_bin

    return bash(
        name = name,
        environment = environment,
        script = "\n".join([
            "$BLACK --check $SOURCE_{} >> $OUTPUT".format(i)
            for i, _ in enumerate(sources)
        ]),
    )