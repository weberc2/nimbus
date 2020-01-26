from .codegen import write_resources_package, FORMATTER_BLACK
from .spec import load

if __name__ == "__main__":
    write_resources_package(load(), "/tmp/nimbus-resources", formatter=FORMATTER_BLACK)
