from .compile import ModelGenerator
from .magic import DemoMagics


def load_ipython_extension(ipython):
    ipython.register_magics(DemoMagics)
