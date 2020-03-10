import sys

from .codegen import write_resources_package
from .spec import load


def main():
    write_resources_package(load(), sys.argv[1])


if __name__ == "__main__":
    main()
