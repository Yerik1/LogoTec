from frontend.ast import Node
import math

class ASTOptimizer:
    """
    Optimizador de AST para el compilador Logo.
    Implementa múltiples pasadas de optimización:
    - Constant Folding (plegado de constantes)
    - Dead Code Elimination (eliminación de código muerto)
    - Algebraic Simplification (simplificación algebraica)
    - Control Flow Optimization (optimización de flujo de control)
    """
    
    def __init__(self):
        self.optimizations_applied = 0
        
    def optimize(self, node: Node) -> Node:
        """Punto de entrada principal para optimización"""
        if node is None:
            return None
            
        # Aplicar múltiples pasadas hasta que no haya cambios
        previous_optimizations = -1
        optimized_node = node
        
        while self.optimizations_applied != previous_optimizations:
            previous_optimizations = self.optimizations_applied
            optimized_node = self.visit(optimized_node)
            
        return optimized_node
    
    def visit(self, node: Node) -> Node:
        """Dispatcher que decide qué método llamar según el tipo de nodo"""
        if node is None:
            return None
            
        method_name = f"visit_{node.kind}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: Node) -> Node:
        """Visita por defecto: procesa hijos recursivamente"""
        optimized_children = []
        for child in node.children:
            optimized_child = self.visit(child)
            if optimized_child is not None:
                optimized_children.append(optimized_child)
        
        return Node(node.kind, node.value, optimized_children, node.line)

    # =====================================================
    # OPTIMIZACIONES DE EXPRESIONES ARITMÉTICAS
    # =====================================================
    
    def visit_BINOP(self, node: Node) -> Node:
        """Optimiza operaciones binarias (+, -, *, /)"""
        if len(node.children) < 2:
            return self.generic_visit(node)
            
        left = self.visit(node.children[0])
        right = self.visit(node.children[1])
        op = node.value
        
        # Constant Folding
        if left.kind == "NUM" and right.kind == "NUM":
            try:
                if op == '+':
                    result = left.value + right.value
                elif op == '-':
                    result = left.value - right.value
                elif op == '*':
                    result = left.value * right.value
                elif op == '/':
                    if right.value != 0:
                        result = left.value / right.value
                    else:
                        # División por cero - mantener expresión original
                        return Node(node.kind, node.value, [left, right], node.line)
                else:
                    return Node(node.kind, node.value, [left, right], node.line)
                
                self.optimizations_applied += 1
                return Node("NUM", result, [], node.line)
            except:
                return Node(node.kind, node.value, [left, right], node.line)
        
        # Optimizaciones algebraicas
        optimized = self._apply_algebraic_optimizations(op, left, right, node.line)
        if optimized:
            self.optimizations_applied += 1
            return optimized
            
        return Node(node.kind, node.value, [left, right], node.line)

    def _apply_algebraic_optimizations(self, op: str, left: Node, right: Node, line: int) -> Node:
        """Aplica optimizaciones algebraicas comunes"""
        
        # Optimizaciones de suma
        if op == '+':
            # x + 0 = x
            if right.kind == "NUM" and right.value == 0:
                return left
            # 0 + x = x
            if left.kind == "NUM" and left.value == 0:
                return right
                
        # Optimizaciones de resta
        elif op == '-':
            # x - 0 = x
            if right.kind == "NUM" and right.value == 0:
                return right
            # x - x = 0 (solo si es una variable, no expresión compleja)
            if left.kind == "ID" and right.kind == "ID" and left.value == right.value:
                return Node("NUM", 0, [], line)
                
        # Optimizaciones de multiplicación
        elif op == '*':
            # x * 0 = 0
            if (left.kind == "NUM" and left.value == 0) or (right.kind == "NUM" and right.value == 0):
                return Node("NUM", 0, [], line)
            # x * 1 = x
            if right.kind == "NUM" and right.value == 1:
                return left
            # 1 * x = x
            if left.kind == "NUM" and left.value == 1:
                return right
                
        # Optimizaciones de división
        elif op == '/':
            # x / 1 = x
            if right.kind == "NUM" and right.value == 1:
                return left
            # 0 / x = 0 (si x != 0)
            if left.kind == "NUM" and left.value == 0 and not (right.kind == "NUM" and right.value == 0):
                return Node("NUM", 0, [], line)
                
        return None

    def visit_POW(self, node: Node) -> Node:
        """Optimiza operaciones de potencia"""
        if len(node.children) < 2:
            return self.generic_visit(node)
            
        base = self.visit(node.children[0])
        exponent = self.visit(node.children[1])
        
        # Constant Folding
        if base.kind == "NUM" and exponent.kind == "NUM":
            try:
                result = base.value ** exponent.value
                self.optimizations_applied += 1
                return Node("NUM", result, [], node.line)
            except:
                pass
        
        # Optimizaciones algebraicas
        # x^0 = 1
        if exponent.kind == "NUM" and exponent.value == 0:
            self.optimizations_applied += 1
            return Node("NUM", 1, [], node.line)
        # x^1 = x
        if exponent.kind == "NUM" and exponent.value == 1:
            self.optimizations_applied += 1
            return base
        # 0^x = 0 (si x > 0)
        if base.kind == "NUM" and base.value == 0 and exponent.kind == "NUM" and exponent.value > 0:
            self.optimizations_applied += 1
            return Node("NUM", 0, [], node.line)
        # 1^x = 1
        if base.kind == "NUM" and base.value == 1:
            self.optimizations_applied += 1
            return Node("NUM", 1, [], node.line)
            
        return Node(node.kind, node.value, [base, exponent], node.line)

    def visit_NEG(self, node: Node) -> Node:
        """Optimiza negación unaria"""
        if len(node.children) < 1:
            return self.generic_visit(node)
            
        operand = self.visit(node.children[0])
        
        # Constant Folding
        if operand.kind == "NUM":
            self.optimizations_applied += 1
            return Node("NUM", -operand.value, [], node.line)
            
        # Double negation: -(-x) = x
        if operand.kind == "NEG" and len(operand.children) > 0:
            self.optimizations_applied += 1
            return operand.children[0]
            
        return Node(node.kind, node.value, [operand], node.line)

    # =====================================================
    # OPTIMIZACIONES DE EXPRESIONES BOOLEANAS
    # =====================================================
    
    def visit_BOOLBIN(self, node: Node) -> Node:
        """Optimiza operaciones booleanas binarias (Y, O)"""
        if len(node.children) < 2:
            return self.generic_visit(node)
            
        left = self.visit(node.children[0])
        right = self.visit(node.children[1])
        op = node.value
        
        # Constant Folding
        if self._is_boolean_constant(left) and self._is_boolean_constant(right):
            left_val = self._get_boolean_value(left)
            right_val = self._get_boolean_value(right)
            
            if op == 'Y':  # AND
                result = left_val and right_val
            elif op == 'O':  # OR
                result = left_val or right_val
            else:
                return Node(node.kind, node.value, [left, right], node.line)
                
            self.optimizations_applied += 1
            return Node("BOOL", result, [], node.line)
        
        # Optimizaciones de cortocircuito
        if op == 'Y':  # AND
            # false Y x = false
            if self._is_boolean_constant(left) and not self._get_boolean_value(left):
                self.optimizations_applied += 1
                return Node("BOOL", False, [], node.line)
            # x Y false = false
            if self._is_boolean_constant(right) and not self._get_boolean_value(right):
                self.optimizations_applied += 1
                return Node("BOOL", False, [], node.line)
            # true Y x = x
            if self._is_boolean_constant(left) and self._get_boolean_value(left):
                self.optimizations_applied += 1
                return right
            # x Y true = x
            if self._is_boolean_constant(right) and self._get_boolean_value(right):
                self.optimizations_applied += 1
                return left
                
        elif op == 'O':  # OR
            # true O x = true
            if self._is_boolean_constant(left) and self._get_boolean_value(left):
                self.optimizations_applied += 1
                return Node("BOOL", True, [], node.line)
            # x O true = true
            if self._is_boolean_constant(right) and self._get_boolean_value(right):
                self.optimizations_applied += 1
                return Node("BOOL", True, [], node.line)
            # false O x = x
            if self._is_boolean_constant(left) and not self._get_boolean_value(left):
                self.optimizations_applied += 1
                return right
            # x O false = x
            if self._is_boolean_constant(right) and not self._get_boolean_value(right):
                self.optimizations_applied += 1
                return left
                
        return Node(node.kind, node.value, [left, right], node.line)

    def visit_RELOP(self, node: Node) -> Node:
        """Optimiza operaciones relacionales (IGUALES, MENORQ, MAYORQ)"""
        if len(node.children) < 2:
            return self.generic_visit(node)
            
        left = self.visit(node.children[0])
        right = self.visit(node.children[1])
        op = node.value
        
        # Constant Folding
        if left.kind == "NUM" and right.kind == "NUM":
            try:
                if op == 'IGUALES':
                    result = left.value == right.value
                elif op == 'MENORQ':
                    result = left.value < right.value
                elif op == 'MAYORQ':
                    result = left.value > right.value
                else:
                    return Node(node.kind, node.value, [left, right], node.line)
                    
                self.optimizations_applied += 1
                return Node("BOOL", result, [], node.line)
            except:
                pass
        
        # x == x = true (solo para variables simples)
        if op == 'IGUALES' and left.kind == "ID" and right.kind == "ID" and left.value == right.value:
            self.optimizations_applied += 1
            return Node("BOOL", True, [], node.line)
        
        # x < x = false, x > x = false
        if (op == 'MENORQ' or op == 'MAYORQ') and left.kind == "ID" and right.kind == "ID" and left.value == right.value:
            self.optimizations_applied += 1
            return Node("BOOL", False, [], node.line)
            
        return Node(node.kind, node.value, [left, right], node.line)

    # =====================================================
    # OPTIMIZACIONES DE CONTROL DE FLUJO
    # =====================================================
    
    def visit_SI(self, node: Node) -> Node:
        """Optimiza condicionales SI"""
        if len(node.children) < 2:
            return self.generic_visit(node)
            
        condition = self.visit(node.children[0])
        then_branch = self.visit(node.children[1])
        else_branch = self.visit(node.children[2]) if len(node.children) > 2 else None
        
        # Dead Code Elimination
        if self._is_boolean_constant(condition):
            if self._get_boolean_value(condition):
                # Condición siempre verdadera
                self.optimizations_applied += 1
                return then_branch
            else:
                # Condición siempre falsa
                self.optimizations_applied += 1
                return else_branch if else_branch else Node("EMPTY", line=node.line)
        
        # Construir nodo optimizado
        children = [condition, then_branch]
        if else_branch:
            children.append(else_branch)
            
        return Node(node.kind, node.value, children, node.line)

    def visit_MIENTRAS(self, node: Node) -> Node:
        """Optimiza bucles MIENTRAS"""
        if len(node.children) < 2:
            return self.generic_visit(node)
            
        condition = self.visit(node.children[0])
        body = self.visit(node.children[1])
        
        # Dead Code Elimination
        if self._is_boolean_constant(condition):
            if not self._get_boolean_value(condition):
                # Condición siempre falsa - bucle nunca se ejecuta
                self.optimizations_applied += 1
                return Node("EMPTY", line=node.line)
            # Si es siempre verdadera, mantener el bucle (podría ser bucle infinito intencional)
        
        return Node(node.kind, node.value, [condition, body], node.line)

    def visit_REPITE(self, node: Node) -> Node:
        """Optimiza bucles REPITE"""
        if len(node.children) < 2:
            return self.generic_visit(node)
            
        count = self.visit(node.children[0])
        body = self.visit(node.children[1])
        
        # Si el contador es 0, eliminar el bucle
        if count.kind == "NUM" and count.value <= 0:
            self.optimizations_applied += 1
            return Node("EMPTY", line=node.line)
        
        # Si el contador es 1, ejecutar el cuerpo una vez
        if count.kind == "NUM" and count.value == 1:
            self.optimizations_applied += 1
            return body
            
        return Node(node.kind, node.value, [count, body], node.line)

    # =====================================================
    # OPTIMIZACIONES DE COMANDOS LOGO
    # =====================================================
    
    def visit_AV(self, node: Node) -> Node:
        """Optimiza comando AVANZA"""
        if len(node.children) < 1:
            return self.generic_visit(node)
            
        distance = self.visit(node.children[0])
        
        # Si la distancia es 0, eliminar el comando
        if distance.kind == "NUM" and distance.value == 0:
            self.optimizations_applied += 1
            return Node("EMPTY", line=node.line)
            
        return Node(node.kind, node.value, [distance], node.line)

    def visit_RE(self, node: Node) -> Node:
        """Optimiza comando RETROCEDE"""
        if len(node.children) < 1:
            return self.generic_visit(node)
            
        distance = self.visit(node.children[0])
        
        # Si la distancia es 0, eliminar el comando
        if distance.kind == "NUM" and distance.value == 0:
            self.optimizations_applied += 1
            return Node("EMPTY", line=node.line)
            
        # RE x = AV -x
        if distance.kind == "NUM":
            self.optimizations_applied += 1
            return Node("AV", line=node.line).add(Node("NUM", -distance.value, [], distance.line))
            
        return Node(node.kind, node.value, [distance], node.line)

    def visit_GD(self, node: Node) -> Node:
        """Optimiza comando GIRA DERECHA"""
        if len(node.children) < 1:
            return self.generic_visit(node)
            
        angle = self.visit(node.children[0])
        
        # Si el ángulo es 0, eliminar el comando
        if angle.kind == "NUM" and angle.value == 0:
            self.optimizations_applied += 1
            return Node("EMPTY", line=node.line)
        
        # Normalizar ángulos (opcional)
        if angle.kind == "NUM":
            normalized_angle = angle.value % 360
            if normalized_angle != angle.value:
                self.optimizations_applied += 1
                return Node(node.kind, node.value, [Node("NUM", normalized_angle, [], angle.line)], node.line)
            
        return Node(node.kind, node.value, [angle], node.line)

    def visit_GI(self, node: Node) -> Node:
        """Optimiza comando GIRA IZQUIERDA"""
        if len(node.children) < 1:
            return self.generic_visit(node)
            
        angle = self.visit(node.children[0])
        
        # Si el ángulo es 0, eliminar el comando
        if angle.kind == "NUM" and angle.value == 0:
            self.optimizations_applied += 1
            return Node("EMPTY", line=node.line)
        
        # GI x = GD -x
        if angle.kind == "NUM":
            self.optimizations_applied += 1
            return Node("GD", line=node.line).add(Node("NUM", -angle.value, [], angle.line))
            
        return Node(node.kind, node.value, [angle], node.line)

    # =====================================================
    # OPTIMIZACIONES DE LISTAS DE COMANDOS
    # =====================================================
    
    def visit_STMTS(self, node: Node) -> Node:
        """Optimiza listas de comandos, eliminando comandos vacíos"""
        optimized_children = []
        
        for child in node.children:
            optimized_child = self.visit(child)
            # No agregar comandos vacíos
            if optimized_child and optimized_child.kind != "EMPTY":
                optimized_children.append(optimized_child)
        
        # Si no hay hijos después de optimización, retornar comando vacío
        if not optimized_children:
            self.optimizations_applied += 1
            return Node("EMPTY", line=node.line)
            
        # Si solo hay un hijo, retornarlo directamente
        if len(optimized_children) == 1:
            self.optimizations_applied += 1
            return optimized_children[0]
            
        return Node(node.kind, node.value, optimized_children, node.line)

    # =====================================================
    # MÉTODOS AUXILIARES
    # =====================================================
    
    def _is_boolean_constant(self, node: Node) -> bool:
        """Verifica si un nodo representa una constante booleana"""
        return node.kind == "BOOL" or (node.kind == "NUM" and node.value in [0, 1])
    
    def _get_boolean_value(self, node: Node) -> bool:
        """Obtiene el valor booleano de un nodo constante"""
        if node.kind == "BOOL":
            return node.value
        elif node.kind == "NUM":
            return bool(node.value)
        return False

    def get_optimization_stats(self) -> dict:
        """Retorna estadísticas de optimización"""
        return {
            "optimizations_applied": self.optimizations_applied
        }