import typing
import amanda.compiler.ast as ast
import amanda.compiler.symbols.core as symbols
from amanda.compiler.check.checker import Checker
from amanda.compiler.error import Errors
from amanda.compiler.types.core import Uniao, Variant


def check_uniao(uniao: ast.Uniao, checker: Checker):
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


def check_variant(uniao: Uniao, variant: ast.UniaoVariant, checker: Checker):
    checker.ctx_node = variant
    variant_name = variant.name.lexeme
    if uniao.contains_variant(variant_name):
        checker.error(
            Errors.VARIANT_ALREADY_DECLARED,
            uniao=uniao.name,
            variant=variant_name,
        )
    params = [checker.get_type(p) for p in variant.params]
    uniao.add_variant(variant_name, params)


def validate_variant_init(
    checker: Checker, variant: Variant, args: list[ast.Expr]
):
    # 1. Check if number of args match variant declaration
    expected = len(variant.params)
    received = len(args)
    if expected != received:
        checker.error(
            f"número incorrecto de argumentos para o constructor da Variante '{variant.uniao.name}::{variant.name}'. Esperava {expected} argumento(s), porém recebeu {received}"
        )

    # 2. Validate if all arg order match param order
    for arg in args:
        checker.visit(arg)
    for i, (arg, param) in enumerate(zip(args, variant.params)):
        arg.prom_type = arg.eval_type.promote_to(param)
        if not checker.types_match(param, arg.eval_type):
            checker.error(
                f"erro no argumento {i + 1}. Esperava-se um argumento do tipo '{param}' mas recebeu o tipo '{arg.eval_type}'"
            )
