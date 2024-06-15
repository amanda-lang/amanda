import typing
import amanda.compiler.ast as ast
import amanda.compiler.symbols.core as symbols
from amanda.compiler.check.checker import Checker
from amanda.compiler.error import Errors


def check_iguala(checker: Checker, iguala: ast.Iguala):
    raise NotImplementedError("no code yet")
    name = uniao.name.lexeme
    reg_scope = symbols.Scope(checker.ctx_scope)
    if typing.cast(symbols.Scope, checker.ctx_scope).get(name):
        checker.error(Errors.ID_IN_USE, name=name)

    generic_params = checker.get_generic_params(uniao)
    checker.enter_ty_ctx(checker.get_generic_ty_ctx(generic_params))

    uniao_sym = Uniao(name, checker.ctx_module, {}, ty_params=generic_params)

    checker.define_symbol(uniao_sym, checker.scope_depth, checker.ctx_scope)
    checker.enter_scope(reg_scope)

    for field in uniao.variants:
        check_variant(uniao_sym, field, checker)

    checker.leave_scope()
    checker.leave_ty_ctx()
