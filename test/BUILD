load("std/python", "pytest")
load("3rdParty", "black_check")
load("core", nimbus_core = "lib")
load("resources", nimbus_resources = "lib")

src = glob("**.py")

smoke = pytest(
    name = "smoke",
    sources = src,
    dependencies = [ nimbus_core, nimbus_resources ],
)

test_black = black_check(name = "test_black", sources = [ src ])