import sys

from .codegen import write_resources_package, FORMATTER_BLACK, FORMATTER_NONE
from .spec import load


def main():
    write_resources_package(
        load(),
        "/tmp/nimbus-resources",
        formatter=FORMATTER_BLACK
        if len(sys.argv) > 1 and sys.argv[1] == "black"
        else FORMATTER_NONE,
    )


if __name__ == "__main__":
    main()
