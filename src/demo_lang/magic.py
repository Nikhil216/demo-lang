from IPython.core.magic import Magics, magics_class, cell_magic
from .compile import ModelGenerator


@magics_class
class DemoMagics(Magics):

    @cell_magic
    def demo(self, line, cell):
        model_name = line.strip()
        source = cell.strip()
        ns = self.shell.user_ns
        gen = ModelGenerator(model_name, source, ns)
        scope = gen.generate()
        gen.model.optimize()
        ns.update(scope)
        return gen.model
