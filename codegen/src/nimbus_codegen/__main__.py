from nimbus_codegen.codegen import write_resources_package
from nimbus_codegen.spec import load

if __name__ == "__main__":
    write_resources_package(load(), "/tmp/nimbus-resources")
