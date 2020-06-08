from enum import Enum
from amanda.lexer import Lexer
from amanda.tokens import TokenType as TT
from amanda.tokens import Token
import amanda.ast_nodes as AST
import amanda.symtab as SYM
import amanda.error as error


''' Class to represent built in types '''
class Type(Enum):
    INT = 0
    REAL = 1
    BOOL = 2
    
    def __str__(self):
        return self.name.lower()

# results of static type computation
# None means illegal operation
aritop_results = [
#       int       real       bool
    [Type.INT,Type.REAL,None],
    [Type.REAL,Type.REAL,None],
    [None,None,None],
]

#Table for  type for >,<,>=,<=
relop_results = [
#       int       real       bool
    [Type.BOOL,Type.BOOL,None],
    [Type.BOOL,Type.BOOL,None],
    [None,None,None],
]

#table for type results for == !=
eqop_results = [
#       int       real       bool
    [Type.BOOL,Type.BOOL,Type.BOOL],
    [Type.BOOL,Type.BOOL,Type.BOOL],
    [None,None,Type.BOOL],
]

#table for type results for e ou !
logop_results = [
#    int  real  bool
    [None,None,None],
    [None,None,None],
    [None,None,Type.BOOL],
]



# table for type promotions
# VAZIO means should not be promoted
type_promotion= [
#    int  real  bool
    [None,Type.REAL,None],
    [None,None,None],
    [None,None,None],
]


'''
Class that performs semantic analysis on a syntatically valid
amanda program.
'''

class Analyzer(AST.Visitor):

    def __init__(self,parser):
        self.parser = parser
        self.program = self.parser.parse()
        self.current_scope = SYM.Scope(SYM.Scope.GLOBAL)
        self.init__builtins()

    def init__builtins(self):
        self.current_scope.define("int",SYM.BuiltInType(Type.INT))
        self.current_scope.define("real",SYM.BuiltInType(Type.REAL))
        self.current_scope.define("bool",SYM.BuiltInType(Type.BOOL))
        #remove this from here


    def has_return(self,node):
        node_class = type(node).__name__.lower()
        method_name = f"has_return_{node_class}"
        visitor_method = getattr(self,method_name,self.general_check)
        return visitor_method(node)

    def general_check(self,node):
        return False

    def has_return_block(self,node):
        for child in node.children:
            has_return = self.has_return(child)
            if has_return:
                return True
        return False

    def has_return_se(self,node):
        ''' Method checks for return within
            'se' statements'''
        # If there is no else branch return None immediately
        return False if not node.else_branch else self.has_return(node.else_branch)


    def has_return_retorna(self,node):
        return True


    def error(self,line,col,code,**kwargs):
        message = code.format(**kwargs)
        handler = error.ErrorHandler.get_handler()
        handler.throw_error(
            error.Analysis(message,line,col),
            self.parser.lexer.file
        )


    def check_program(self):
        self.visit_program(self.program)

    #TODO: Fix this block hack
    def visit_program(self,node):
        self.visit(node,self.current_scope)



    def visit_vardecl(self,node):
        name = node.id.lexeme
        line = node.id.line
        col = node.id.col
        var_type = self.current_scope.resolve(node.type.lexeme)
        if not var_type or not var_type.is_type():
            self.error(
                        line,col,
                        error.Analysis.UNDEFINED_TYPE,
                        type=node.type.lexeme
                    )

        if not self.current_scope.symbols.get(name) is None:
            self.error(
                        line,col,
                        error.Analysis.ID_IN_USE,
                        name=name
                    )

        symbol = SYM.VariableSymbol(name,var_type)
        self.current_scope.define(name,symbol,node.id)
        if node.assign is not None:
            if node.assign.right.token.lexeme == name:
                self.error(
                            line,
                            f"Erro ao inicializar variável. Não pode referenciar uma variável durante a sua declaração")

            self.visit(node.assign)


    #TODO: put some of this in the function symbol
    def visit_functiondecl(self,node):
        #Check if id is already in use
        name = node.id.lexeme
        line = node.id.line
        col = node.id.col
        if self.current_scope.resolve(name):
            self.error(line,error.Analysis.ID_IN_USE,name=name)
        #Check if return types exists
        function_type =  self.current_scope.resolve(node.type.lexeme)
        if not function_type or not function_type.is_type():
            self.error(line,col,error.Analysis.UNDEFINED_TYPE,type=node.type.lexeme)
        has_return = self.has_return(node.block)
        if not has_return:
            self.error(line,col,error.Analysis.NO_RETURN_STMT,name=name)
        params = {}
        for param in node.params:
            param_name = param.id.lexeme
            if params.get(param_name):
                self.error(line,col,error.Analysis.REPEAT_PARAM,name=param_name)
            param_symbol = self.visit(param)
            params[param_name] = param_symbol
            #Add params o current_scope
        symbol = SYM.FunctionSymbol(name,function_type,params)
        self.current_scope.define(name,symbol)
        scope = SYM.Scope(name,self.current_scope)
        for name,param in symbol.params.items():
            scope.define(name,param)
        self.visit(node.block,scope)
        #leave_scope

    def visit_block(self,node,scope=None):
        if scope:
            self.current_scope = scope
        else:
            self.current_scope = SYM.Scope(SYM.Scope.LOCAL,self.current_scope)
        for child in node.children:
            self.visit(child)
        #Pop scope
        if self.current_scope.name != SYM.Scope.GLOBAL:
            self.current_scope = self.current_scope.enclosing_scope



    def visit_param(self,node):
        var_type = self.current_scope.resolve(node.type.lexeme)
        if not var_type or not var_type.is_type():
            self.error(
                        node.type.line,
                        node.type.col,
                        error.Analysis.UNDEFINED_TYPE,
                        type=node.type.lexeme
                    )
        name = node.id.lexeme
        return SYM.VariableSymbol(name,var_type)


    def visit_expr(self,node):
        if node.token.token == TT.IDENTIFIER:
            name = node.token.lexeme
            line = node.token.line
            sym = self.current_scope.resolve(name)
            if not sym:
                self.error(line,error.Analysis.UNDECLARED_ID,name=name)
            #Referencing array by name loool
            elif not sym.is_valid_var():
                self.error(line,error.Analysis.INVALID_REF,name=name)
            node.eval_type = sym.type.name
        elif node.token.token == TT.INTEGER:
            node.eval_type = Type.INT
        elif node.token.token == TT.REAL:
            node.eval_type = Type.REAL
        elif node.token.token == TT.STRING:
            raise Exception("Not implemented strings yet")
        elif node.token.token in (TT.VERDADEIRO,TT.FALSO):
            node.eval_type = Type.BOOL

    def visit_binop(self,node):
        self.visit(node.left)
        self.visit(node.right)
        #Evaluate type of binary
        #arithmetic operation
        operator = node.token.token
        if operator in (TT.PLUS,TT.MINUS,TT.STAR,TT.SLASH,TT.MODULO):
            node.eval_type = aritop_results[node.left.eval_type.value][node.right.eval_type.value]
        elif operator in (TT.GREATER,TT.LESS,TT.GREATEREQ,TT.LESSEQ):
            node.eval_type = relop_results[node.left.eval_type.value][node.right.eval_type.value]
        elif operator in (TT.DOUBLEEQUAL,TT.NOTEQUAL):
            node.eval_type = eqop_results[node.left.eval_type.value][node.right.eval_type.value]
        elif operator in (TT.AND,TT.OR):
            node.eval_type = logop_results[node.left.eval_type.value][node.right.eval_type.value]
        #Validate binary ops
        line = node.token.line
        col = node.token.col
        lexeme = node.token.lexeme
        if not node.eval_type:
            self.error(
                line,col,
                error.Analysis.INVALID_OP,
                t1=node.left.eval_type,
                t2=node.right.eval_type,
                operator=lexeme
            )

        node.left.prom_type = type_promotion[node.left.eval_type.value][node.right.eval_type.value]
        node.right.prom_type = type_promotion[node.right.eval_type.value][node.left.eval_type.value]

    def visit_unaryop(self,node):
        self.visit(node.operand)
        operator = node.token.token
        lexeme = node.token.lexeme
        line = node.token.line
        type = node.operand.eval_type
        if operator in (TT.PLUS,TT.MINUS):
            if type != Type.INT and type != Type.REAL:
                self.error(line,error.Analysis.INVALID_UOP,operator=lexeme,type=type)
            node.eval_type = type
        elif operator == TT.NAO:
            node.operand.prom_type = logop_results[type.value][Type.BOOL.value]
            if type != Type.BOOL and not node.operand.prom_type:
                self.error(line,error.Analysis.INVALID_UOP,operator=lexeme,type=type)
            node.eval_type = node.operand.prom_type


    def visit_assign(self,node):
        self.visit(node.right)
        self.visit(node.left)

        #Set node types
        node.eval_type = node.left.eval_type
        node.prom_type = None
        #Set promotion type for right side
        node.right.prom_type = type_promotion[node.right.eval_type.value][node.left.eval_type.value]

        line = node.token.line
        col = node.token.col
        if node.left.eval_type != node.right.eval_type and not node.right.prom_type:
            self.error(
                    line,col,
                    f"atribuição inválida. incompatibilidade entre os operandos da atribuição [{node.left.eval_type} = {node.right.eval_type}]")


    def visit_mostra(self,node):
        self.visit(node.exp)


    def visit_retorna(self,node):
        self.visit(node.exp)
        token = node.token.token
        line = node.token.line
        col = node.token.col
        function = self.current_scope.get_enclosing_func()
        #TODO: Fix return bug inside local scope
        if not function:
            self.error(line,col,f"O comando 'retorna' só pode ser usado dentro de uma função")
        function = self.current_scope.resolve(function.name)
        node.exp.prom_type = type_promotion[node.exp.eval_type.value][function.type.name.value]
        if not function.type:
            self.error(line,col,f"expressão de retorno inválida. Procedimentos não podem retornar valores")
        elif function.type.name != node.exp.eval_type and node.exp.prom_type == None:
            self.error(line,col,f"expressão de retorno inválida. O tipo do valor de retorno é incompatível com o tipo de retorno da função")




    def visit_se(self,node):
        self.visit(node.condition)
        if node.condition.eval_type != Type.BOOL:
            self.error(node.token.line,f"a condição da instrução 'se' deve ser um valor lógico")
        self.visit(node.then_branch)
        if node.else_branch:
            self.visit(node.else_branch)

    def visit_enquanto(self,node):
        self.visit(node.condition)
        if node.condition.eval_type != Type.BOOL:
            self.error(node.token.line,f"a condição da instrução 'enquanto' deve ser um valor lógico")
        self.visit(node.statement)

    def visit_para(self,node):
        self.visit(node.expression)
        id = node.expression.id.lexeme
        sym = SYM.VariableSymbol(id,self.current_scope.resolve("int"))
        scope = SYM.Scope(SYM.Scope.LOCAL,self.current_scope)
        scope.define(id,sym)
        if isinstance(node.statement,AST.Block):
            self.visit(node.statement,scope)
        else:
            self.current_scope = scope
            self.visit(node.statement)
            #pop scope
            self.current_scope = self.current_scope.enclosing_scope

    def visit_paraexpr(self,node):
        self.visit(node.id)
        self.visit(node.range)

    def visit_rangeexpr(self,node):
        self.visit(node.start)
        self.visit(node.end)
        if node.inc:
            self.visit(node.inc)
        for node in (node.start,node.end,node.inc):
            #Skip inc node in case it's empty lool
            if not node:
                continue
            if node.eval_type != Type.INT:
                self.error(node.token.line,"os parâmetros de uma série devem ser do tipo 'int'")

    def visit_call(self,node):
        for arg in node.fargs:
            self.visit(arg)
        id = node.id.lexeme
        sym = self.current_scope.resolve(id)
        line = node.id.line
        col = node.id.col
        if sym == None:
            self.error(line,col,f"função '{id}' não foi definida")
        if not isinstance(sym,SYM.FunctionSymbol):
            self.error(line,col,f"identificador '{id}' não é uma função")
        arg_len = len(node.fargs)
        param_len = len(sym.params)
        if arg_len != param_len:
            self.error(
                        line,col,
                        f"número incorrecto de argumentos para a função {node.id.lexeme}. Esperava {param_len} argumentos, porém recebeu {arg_len}"
                    )
        #Type promotion for parameter
        func_decl = ",".join(["{} {}".format(param.type,param.name) for param in sym.params.values()]) #Get function signature
        for arg,param in zip(node.fargs,sym.params.values()):
            arg.prom_type = type_promotion[arg.eval_type.value][param.type.name.value]
            if param.type.name != arg.eval_type and arg.prom_type == None:
                self.error(line,col,f"argumento inválido. Esperava-se um argumento do tipo '{param.type.name}' mas recebeu o tipo '{arg.eval_type}'.\nassinatura: {id}({func_decl})")
        node.eval_type = sym.type.name


    def visit_index(self,node):
        self.visit(node.index)
        id = node.id.lexeme
        sym = self.current_scope.resolve(id)
        line = node.id.line
        #Semantic checks start here
        if not sym:
            self.error(line,error.Analysis.UNDECLARED_ID,name=id)
        elif not isinstance(sym,SYM.ArraySymbol):
            self.error(line,f"o identificador '{id}' não é um vector")
        #index = node.in
        if node.index.eval_type != Type.INT:
            self.error(line,f"o índice de um vector deve ser um inteiro")
        node.eval_type = sym.type.name
