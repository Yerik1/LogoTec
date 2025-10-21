from llvmlite import ir
import os
from frontend.parser import Node

INT = ir.IntType(32)
FLOAT = ir.FloatType()

class IntermediateCodeGen:
    def __init__(self):
        self.module = ir.Module(name="logotec_module")
        self.builder = None

        # define int types
        self.INT = ir.IntType(32)
        self.int_typeType = ir.IntType  # Used for isinstance checks

        # symbol tables: stack per function to support locals
        self.symstack = []  # list of dicts: name -> alloca
        self.func_table = {}  # name -> ir.Function
        self.current_function = None

        # declare main and runtime stubs
        self._declare_runtime_functions()
        self._create_main_function()

    # ----------------------
    # Module / runtime setup
    # ----------------------
    def _declare_runtime_functions(self):
        # Turtle/hardware and helpers. All take/return ints where sensible.
        funcs = {
            "AV": ("move_forward", ir.FunctionType(ir.VoidType(), [INT])),
            "RE": ("move_backward", ir.FunctionType(ir.VoidType(), [INT])),
            "GD": ("turn_right", ir.FunctionType(ir.VoidType(), [INT])),
            "GI": ("turn_left", ir.FunctionType(ir.VoidType(), [INT])),
            "PONPOS": ("set_position", ir.FunctionType(ir.VoidType(), [INT, INT])),
            "PONXY": ("set_xy", ir.FunctionType(ir.VoidType(), [INT, INT])),
            "PONX": ("set_x", ir.FunctionType(ir.VoidType(), [INT])),
            "PONY": ("set_y", ir.FunctionType(ir.VoidType(), [INT])),
            "PONRUMBO": ("set_heading", ir.FunctionType(ir.VoidType(), [INT])),
            "RUMBO": ("get_heading", ir.FunctionType(INT, [])),
            "BL": ("pen_up", ir.FunctionType(ir.VoidType(), [])),
            "SB": ("pen_down", ir.FunctionType(ir.VoidType(), [])),
            "OT": ("hide_turtle", ir.FunctionType(ir.VoidType(), [])),
            "PONCL": ("set_color", ir.FunctionType(ir.VoidType(), [INT])),  # or string handling
            "ESPERA": ("sleep_ms", ir.FunctionType(ir.VoidType(), [INT])),
            "AZAR": ("rand_int", ir.FunctionType(INT, [INT])),
            "CENTRO": ("center_turtle", ir.FunctionType(ir.VoidType(), [])),
            # helpers:
            "POW": ("pow_int", ir.FunctionType(INT, [INT, INT])),  # integer pow
        }
        for key, (name, ftype) in funcs.items():
            fn = ir.Function(self.module, ftype, name=name)
            self.func_table[key] = fn
            # Also map by runtime name in case callees use runtime symbol
            self.func_table[name] = fn

    def _create_main_function(self):
        # main returns void; entry block set as current builder context
        fnty = ir.FunctionType(ir.VoidType(), [])
        f = ir.Function(self.module, fnty, name="main")
        block = f.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)
        self.current_function = f
        self.symstack.append({})  # push global/local table for main
        self.func_table["main_func"] = f

    def generate(self, ast_root):
        self._gen_node(ast_root)
        # ensure main returns
        if not self.builder.block.is_terminated:
            self.builder.ret_void()
        return str(self.module)

    # ----------------------
    # Helpers
    # ----------------------
    def _push_scope(self):
        self.symstack.append({})

    def _pop_scope(self):
        self.symstack.pop()

    def _current_symtab(self):
        return self.symstack[-1]

    def _get_var_alloca(self, name):
        # search from top scope downwards
        for st in reversed(self.symstack):
            if name in st:
                return st[name]
        return None

    def _create_var_alloca(self, name, llvm_type=INT):
        # create alloca in function entry block (standard practice)
        func = self.current_function
        entry_block = func.entry_basic_block
        builder_save = self.builder

        # place temporary IRBuilder at entry to emit alloca there
        tmpb = ir.IRBuilder(entry_block)
        # If existing first non-alloca instr exists, alloca inserted at top anyway
        alloca = tmpb.alloca(llvm_type, name=name)
        self._current_symtab()[name] = alloca

        # restore builder
        self.builder = builder_save
        return alloca

    def _ensure_var(self, name):
        a = self._get_var_alloca(name)
        if a is None:
            a = self._create_var_alloca(name, INT)
        return a

    def _is_true(self, val):
        # take an i1 or an int32 where non-zero means true
        if isinstance(val.type, self.int_typeType) and val.type.width == 1:
            return val
        # construct i1: icmp with zero
        return self.builder.icmp_signed("!=", val, ir.Constant(INT, 0))

    def _ensure_i1(self, val):
        # return i1 from val (val may already be i1 or i32)
        if isinstance(val.type, self.int_typeType) and val.type.width == 1:
            return val
        return self.builder.icmp_signed("!=", val, ir.Constant(INT, 0))

    # evaluate boolean expression nodes into i1
    def _eval_bexpr(self, node):
        kind = node.kind
        if kind == "RELOP":
            left = self._gen_node(node.children[0])
            right = self._gen_node(node.children[1])
            op = node.value
            if op in ("IGUALES", "==", "="):
                return self.builder.icmp_signed("==", left, right)
            if op in ("MENORQ", "<"):
                return self.builder.icmp_signed("<", left, right)
            if op in ("MAYORQ", ">"):
                return self.builder.icmp_signed(">", left, right)
            raise NotImplementedError(f"RELOP operator {op}")

        if kind == "BOOLBIN":
            left = self._eval_bexpr(node.children[0])
            right = self._eval_bexpr(node.children[1])
            op = node.value
            if op == "Y":  # logical and
                # i1 and i1
                return self.builder.and_(left, right)
            if op == "O":  # logical or
                return self.builder.or_(left, right)
            raise NotImplementedError(f"BOOLBIN operator {op}")

        # parenthesized boolexpr or raw expr treated as truthy numeric
        if kind in ("expr", "NUM", "BINOP", "NEG", "ID", "CALL", "POW"):
            v = self._gen_node(node)
            return self._ensure_i1(v)

        raise NotImplementedError(f"Unhandled boolean node kind: {kind}")

    # ----------------------
    # Main generator: parses the AST and return an IR
    # ----------------------
    def _gen_node(self, node):
        # If it's not an AST Node, assume it's a literal/LLVM value and return as-is
        if not isinstance(node, Node):
            return node

        kind = node.kind.upper()

        # ----- Containers / program -----
        if kind == "PROGRAM":
            for c in node.children:
                self._gen_node(c)
            return None

        if kind in ("STMTS", "PARAMS", "ARGS"):
            results = []
            for c in node.children:
                results.append(self._gen_node(c))
            return results

        # ----- Literals / identifiers -----
        if kind == "NUM":
            return ir.Constant(self.INT, int(node.value))

        if kind == "STR":
            s = node.value or ""
            name = f".str{len([g for g in self.module.global_values])}"
            arr_ty = ir.ArrayType(ir.IntType(8), len(s.encode("utf8")) + 1)
            gv = ir.GlobalVariable(self.module, arr_ty, name=name)
            gv.global_constant = True
            gv.initializer = ir.Constant(arr_ty, bytearray(s.encode("utf8") + b"\0"))
            return gv.bitcast(ir.IntType(8).as_pointer())

        if kind == "ID":
            varname = node.value
            alloca = self._get_var_alloca(varname) if hasattr(self, "_get_var_alloca") else None
            if alloca is None:
                raise NameError(f"Variable '{varname}' not declared or in scope")
            return self.builder.load(alloca, name=f"{varname}_val")

        # ----- Declarations / assignments -----
        if kind == "INIC":
            name_node = node.children[0]
            expr_node = node.children[1]
            name = name_node.value
            val = self._gen_node(expr_node)
            alloca = self._create_var_alloca(name, self.INT)
            self.builder.store(val, alloca)
            return None

        if kind == "ASSIGN":
            name = node.children[0].value
            val = self._gen_node(node.children[1])
            alloca = getattr(self, "_ensure_var")(name)
            self.builder.store(val, alloca)
            return None

        if kind == "INC":
            idnode = node.children[0]
            name = idnode.value
            alloca = getattr(self, "_ensure_var")(name)
            cur = self.builder.load(alloca)
            if len(node.children) == 1:
                inc_val = ir.Constant(self.INT, 1)
            else:
                inc_val = self._gen_node(node.children[1])
            res = self.builder.add(cur, inc_val)
            self.builder.store(res, alloca)
            return None

        # ----- Arithmetic -----
        if kind == "BINOP":
            left = self._gen_node(node.children[0])
            right = self._gen_node(node.children[1])
            op = node.value
            if op == '+':
                return self.builder.add(left, right)
            if op == '-':
                return self.builder.sub(left, right)
            if op == '*':
                return self.builder.mul(left, right)
            if op == '/':
                return self.builder.sdiv(left, right)
            raise NotImplementedError(f"BINOP operator {op}")

        if kind == "NEG":
            v = self._gen_node(node.children[0])
            return self.builder.sub(ir.Constant(self.INT, 0), v)

        if kind == "POW":
            base = self._gen_node(node.children[0])
            exp = self._gen_node(node.children[1])
            fn = self.func_table.get("POW") or self.func_table.get("pow_int")
            if fn is None:
                raise NameError("pow_int runtime function not declared")
            return self.builder.call(fn, [base, exp], name="powtmp")

        # ----- Calls (user procedures or builtins) -----
        if kind == "CALL":
            fn_name = node.value
            args = [self._gen_node(c) for c in node.children]
            if isinstance(fn_name, int):
                fn_name = str(fn_name)
            fn = self.func_table.get(fn_name.upper() if fn_name else None)
            if fn is None:
                raise NameError(f"Runtime function {fn_name} not declared")
            return self.builder.call(fn, args)

        # ----- Turtle / primitives -----
        if kind in ("AV", "RE", "GD", "GI"):
            arg = self._gen_node(node.children[0])
            fn = self.func_table.get(kind) or self.func_table.get(kind.upper())
            if fn is None:
                raise NameError(f"Runtime function for {kind} not declared")
            self.builder.call(fn, [arg])
            return None

        if kind == "PONPOS":
            x = self._gen_node(node.children[0])
            y = self._gen_node(node.children[1])
            fn = self.func_table["PONPOS"]
            self.builder.call(fn, [x, y])
            return None

        if kind == "PONXY":
            x = self._gen_node(node.children[0])
            y = self._gen_node(node.children[1])
            fn = self.func_table["PONXY"]
            self.builder.call(fn, [x, y])
            return None

        if kind == "PONX":
            x = self._gen_node(node.children[0])
            fn = self.func_table.get("PONX") or self.func_table.get("set_x")
            self.builder.call(fn, [x])
            return None

        if kind == "PONY":
            y = self._gen_node(node.children[0])
            fn = self.func_table.get("PONY") or self.func_table.get("set_y")
            self.builder.call(fn, [y])
            return None

        if kind == "PONRUMBO":
            v = self._gen_node(node.children[0])
            fn = self.func_table.get("PONRUMBO") or self.func_table.get("set_heading")
            self.builder.call(fn, [v])
            return None

        if kind == "RUMBO":
            fn = self.func_table.get("RUMBO") or self.func_table.get("get_heading")
            return self.builder.call(fn, [])

        if kind in ("BL", "SB", "OT", "CENTRO"):
            fn = self.func_table.get(kind) or self.func_table.get(kind.lower())
            self.builder.call(fn, [])
            return None

        if kind == "PONCL":
            arg = node.children[0]
            if isinstance(arg, Node) and arg.kind.upper() == "STR":
                color_val = ir.Constant(self.INT, 0)
            else:
                color_val = self._gen_node(arg)
            fn = self.func_table.get("PONCL") or self.func_table.get("set_color")
            self.builder.call(fn, [color_val])
            return None

        if kind == "ESPERA":
            t = self._gen_node(node.children[0])
            fn = self.func_table.get("ESPERA") or self.func_table.get("sleep_ms")
            self.builder.call(fn, [t])
            return None

        # ----- Procedure definition -----
        if kind == "PARA":
            name_node, params_node, body_node = node.children
            fname = name_node.value
            param_count = len(params_node.children)
            fnty = ir.FunctionType(ir.VoidType(), [self.INT] * param_count)
            fn = ir.Function(self.module, fnty, name=fname)
            self.func_table[fname] = fn

            entry = fn.append_basic_block(name="entry")
            save_builder, save_current = self.builder, self.current_function
            self.builder = ir.IRBuilder(entry)
            self.current_function = fn

            self._push_scope()
            for i, pname_node in enumerate(params_node.children):
                alloca = self._create_var_alloca(pname_node.value, self.INT)
                self.builder.store(fn.args[i], alloca)
            self._gen_node(body_node)
            if not self.builder.block.is_terminated:
                self.builder.ret_void()
            self._pop_scope()
            self.builder = save_builder
            self.current_function = save_current
            return None

        # ----- Control / loops -----
        if kind == "EJECUTA":
            self._gen_node(node.children[0])
            return None

        if kind == "REPITE":
            count_val = self._gen_node(node.children[0])
            body = node.children[1]

            fn = self.current_function
            start_bb = fn.append_basic_block(name="rep_start")
            loop_bb = fn.append_basic_block(name="rep_loop")
            end_bb = fn.append_basic_block(name="rep_end")

            counter_alloca = self._create_var_alloca("__rep_counter", self.INT)
            self.builder.store(ir.Constant(self.INT, 0), counter_alloca)
            self.builder.branch(start_bb)

            self.builder.position_at_end(start_bb)
            counter = self.builder.load(counter_alloca)
            cond = self.builder.icmp_signed("<", counter, count_val)
            self.builder.cbranch(cond, loop_bb, end_bb)

            self.builder.position_at_end(loop_bb)
            self._gen_node(body)
            counter = self.builder.load(counter_alloca)
            self.builder.store(self.builder.add(counter, ir.Constant(self.INT, 1)), counter_alloca)
            self.builder.branch(start_bb)

            self.builder.position_at_end(end_bb)
            return None

        if kind == "SI":
            cond_node, then_node = node.children[:2]
            cond_i1 = self._eval_bexpr(cond_node) if hasattr(self, "_eval_bexpr") else self._ensure_i1(
                self._gen_node(cond_node))
            fn = self.current_function
            then_bb, else_bb, end_bb = fn.append_basic_block(name="if_then"), fn.append_basic_block(
                name="if_else"), fn.append_basic_block(name="if_end")

            self.builder.cbranch(cond_i1, then_bb, else_bb)
            self.builder.position_at_end(then_bb)
            self._gen_node(then_node)
            if not self.builder.block.is_terminated:
                self.builder.branch(end_bb)

            self.builder.position_at_end(else_bb)
            if len(node.children) > 2:
                self._gen_node(node.children[2])
            if not self.builder.block.is_terminated:
                self.builder.branch(end_bb)

            self.builder.position_at_end(end_bb)
            return None

        if kind == "MIENTRAS":
            cond_node, body_node = node.children
            fn = self.current_function
            cond_bb, body_bb, end_bb = fn.append_basic_block("while_cond"), fn.append_basic_block(
                "while_body"), fn.append_basic_block("while_end")

            self.builder.branch(cond_bb)
            self.builder.position_at_end(cond_bb)
            cond_i1 = self._eval_bexpr(cond_node) if hasattr(self, "_eval_bexpr") else self._ensure_i1(
                self._gen_node(cond_node))
            self.builder.cbranch(cond_i1, body_bb, end_bb)

            self.builder.position_at_end(body_bb)
            self._gen_node(body_node)
            if not self.builder.block.is_terminated:
                self.builder.branch(cond_bb)

            self.builder.position_at_end(end_bb)
            return None

        if kind == "HAZ_HASTA":
            body_node, cond_node = node.children
            fn = self.current_function
            loop_bb, cond_bb, end_bb = fn.append_basic_block("do_loop"), fn.append_basic_block(
                "do_cond"), fn.append_basic_block("do_end")

            self.builder.branch(loop_bb)
            self.builder.position_at_end(loop_bb)
            self._gen_node(body_node)
            if not self.builder.block.is_terminated:
                self.builder.branch(cond_bb)

            self.builder.position_at_end(cond_bb)
            cond_i1 = self._eval_bexpr(cond_node) if hasattr(self, "_eval_bexpr") else self._ensure_i1(
                self._gen_node(cond_node))
            self.builder.cbranch(cond_i1, end_bb, loop_bb)
            self.builder.position_at_end(end_bb)
            return None

        if kind == "HAZ_MIENTRAS":
            body_node, cond_node = node.children
            fn = self.current_function
            loop_bb, cond_bb, end_bb = fn.append_basic_block("dowhile_loop"), fn.append_basic_block(
                "dowhile_cond"), fn.append_basic_block("dowhile_end")

            self.builder.branch(loop_bb)
            self.builder.position_at_end(loop_bb)
            self._gen_node(body_node)
            if not self.builder.block.is_terminated:
                self.builder.branch(cond_bb)

            self.builder.position_at_end(cond_bb)
            cond_i1 = self._eval_bexpr(cond_node) if hasattr(self, "_eval_bexpr") else self._ensure_i1(
                self._gen_node(cond_node))
            self.builder.cbranch(cond_i1, loop_bb, end_bb)
            self.builder.position_at_end(end_bb)
            return None

        if kind == "HAZ":
            return None

        # ----- Default: not handled -----
        raise NotImplementedError(f"Unhandled node kind in IR generator: {kind}")

    def save_ir_to_file(self, ir_text, output_path="out/output.ll"):
        """Writes IR code to file (creates directory if missing)."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(ir_text)