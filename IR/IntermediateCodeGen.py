from llvmlite import ir
import os

class IntermediateCodeGen:
    def __init__(self):
        self.module = ir.Module(name="logotec_module")
        self.builder = None
        self.symbol_table = {}
        self.func_table = {}
        self._create_main_function()
        self._declare_runtime_functions()

    def _create_main_function(self):
        func_type = ir.FunctionType(ir.VoidType(), [])
        main_func = ir.Function(self.module, func_type, name="main")
        block = main_func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)
        self.func_table["main"] = main_func

    def _declare_runtime_functions(self):
        azar_type = ir.FunctionType(ir.IntType(32), [ir.IntType(32)])
        ponpos_type = ir.FunctionType(ir.VoidType(), [ir.IntType(32), ir.IntType(32)])
        self.func_table["AZAR"] = ir.Function(self.module, azar_type, name="AZAR")
        self.func_table["PONPOS"] = ir.Function(self.module, ponpos_type, name="PONPOS")

    def generate(self, ast_root):
        self._gen_node(ast_root)
        self.builder.ret_void()
        return str(self.module)

    def _gen_node(self, node):
        kind = node.kind

        if kind == "PROGRAM":
            for child in node.children:
                self._gen_node(child)

        elif kind == "CALL":
            func_name = node.value
            args = [self._gen_node(arg) for arg in node.children]
            return self.builder.call(self.func_table[func_name], args)

        elif kind == "PONPOS":
            args = [self._gen_node(arg) for arg in node.children]
            return self.builder.call(self.func_table["PONPOS"], args)

        elif kind == "NUM":
            return ir.Constant(ir.IntType(32), int(node.value))

        else:
            raise NotImplementedError(f"Unknown node kind: {kind}")

    def save_ir_to_file(self, ir_text, output_path="out/output.ll"):
        """Writes IR code to file (creates directory if missing)."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(ir_text)