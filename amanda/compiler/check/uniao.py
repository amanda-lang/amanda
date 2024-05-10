import typing
import amanda.compiler.ast as ast
import amanda.compiler.symbols.core as symbols
from amanda.compiler.check.checker import Checker
from amanda.compiler.error import Errors


def check_uniao(uniao: ast.Uniao, checker: Checker):
    name = uniao.name.lexeme
    reg_scope = symbols.Scope(checker.ctx_scope)
    if typing.cast(symbols.Scope, checker.ctx_scope).get(name):
        checker.error(Errors.ID_IN_USE, name=name)

    generic_params = checker.get_generic_params(uniao)
    generic_params = checker.get_generic_params(uniao)
    checker.enter_ty_ctx(checker.get_generic_ty_ctx(generic_params))

    checker.define_symbol(registo, checker.scope_depth, checker.ctx_scope)
    checker.ctx_reg = registo
    checker.enter_scope(reg_scope)

    for field in uniao.variants:
        check_variant(field, checker)
    checker.leave_scope()

    checker.define_symbol(registo, checker.scope_depth, checker.ctx_scope)
    checker.leave_ty_ctx()
    checker.ctx_reg = None
    pass
