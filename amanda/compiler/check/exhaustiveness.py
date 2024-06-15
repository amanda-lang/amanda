from __future__ import annotations

# An implementation of the algorithm described at
# <https://julesjacobs.com/notes/patternmatching/patternmatching.pdf>.
#
# Adapted from Yorick Peterse's implementation at
# <https://github.com/yorickpeterse/pattern-matching-in-rust>. Thank you Yorick!
from dataclasses import dataclass
from amanda.compiler.check.checker import Checker
from amanda.compiler.symbols.base import Constructor, Type
from amanda.compiler.symbols.core import Scope, VariableSymbol
from amanda.compiler.types.builtins import Builtins
import amanda.compiler.ast as ast
from amanda.compiler.types.core import BoolCons, IntCons, VariantCons


@dataclass
class Body:
    # Any variables to bind before running the code.
    # The tuples are in the form `(name, source)` (i.e `bla = source`).
    bindings: list[tuple[str, VariableSymbol]]
    # The "code" to run in case of a match.
    #
    # We just use an integer for the sake of simplicity, but normally this
    # would be an AST node, or perhaps an index to an array of AST nodes.
    value: ast.Block


# A column in a pattern matching table.
#
# A column contains a single variable to test, and a pattern to test against
# that variable. A row may contain multiple columns, though this wouldn't be
# exposed to the source language (= it's an implementation detail).
@dataclass
class Column:
    variable: VariableSymbol
    pattern: ast.Pattern


# A single case (or row) in a match expression/table.
@dataclass
class Row:
    columns: list[Column]
    guard: int | None
    body: Body

    def remove_column(self, variable: VariableSymbol) -> Column | None:
        try:
            idx = list(map(lambda c: c.variable, self.columns)).index(variable)
            return self.columns.pop(idx)
        except ValueError:
            return None


@dataclass
class DFailure:
    """A pattern is missing."""

    pass


@dataclass
class DGuard:
    """
    Checks if a guard evaluates to true, running the body if it does.

    The arguments are as follows:

    1. The "condition" to evaluate. We just use a dummy value, but in a real
       compiler this would likely be an AST node of sorts.
    2. The body to evaluate if the guard matches.
    3. The sub tree to evaluate when the guard fails.
    """

    condition: int
    success: Body
    failure: Decision


@dataclass
class DSwitch:
    variable: VariableSymbol
    cases: list[Case]
    fallback: Decision


# A pattern is matched and the right-hand value is to be returned.
@dataclass
class DSuccess:
    body: Body


# A decision tree compiled from a list of match cases.
Decision = DFailure | DGuard | DSuccess | DSwitch


# A case in a decision tree to test against a variable.
@dataclass
class Case:
    # The constructor to test against an input variable.
    constructor: Constructor

    # Variables to introduce to the body of this case.
    #
    # At runtime these would be populated with the values a pattern is matched
    # against. For example this pattern:
    #
    #     case (10, 20, foo) -> ...
    #
    # Would result in three arguments assigned the values `10`, `20` and
    # `foo`.
    #
    # In a real compiler you'd assign these variables in your IR first then
    # generate the code for the sub tree.
    arguments: list[VariableSymbol]

    # The sub tree of this case.
    body: Decision


@dataclass
class Diagnostics:
    missing: bool
    reachable: list[ast.Block]


# Information about a single constructor/value (aka term) being tested, used
# to build a list of names of missing patterns.
@dataclass
class Term:
    variable: VariableSymbol
    name: str
    arguments: list[VariableSymbol]

    def pattern_name(
        self,
        terms: list[Term],
        mapping: dict[int, int],
    ) -> str:
        if not self.arguments:
            return self.name
        args = ", ".join(
            [
                terms[idx].pattern_name(terms, mapping) if idx else "_"
                for idx in [mapping.get(id(arg)) for arg in self.arguments]
            ]
        )
        return f"{self.name}({args})"


# The result of compiling a pattern match expression.
@dataclass
class Match:
    scope: Scope
    tree: Decision
    diagnostics: Diagnostics

    def missing_patterns(self) -> list[str]:
        names = set()
        steps = []

        self.add_missing_patterns(self.tree, steps, names)

        return list(names)

    def add_missing_patterns(
        self,
        node: Decision,
        terms: list[Term],
        missing: set[str],
    ):
        match node:
            case DSuccess():
                pass
            case DFailure():
                mapping = {}
                # At this point the terms stack looks something like this:
                # `[term, term + arguments, term, ...]`. To construct a pattern
                # name from this stack, we first map all variables to their
                # term indexes. This is needed because when a term defines
                # arguments, the terms for those arguments don't necessarily
                # appear in order in the term stack.
                #
                # This mapping is then used when (recursively) generating a
                # pattern name.
                #
                # This approach could probably be done more efficiently, so if
                # you're reading this and happen to know of a way, please
                # submit a merge request :)
                for index, step in enumerate(terms):
                    mapping[id(step.variable)] = index

                name = terms[0].pattern_name(terms, mapping) if terms else "_"
                missing.add(name)
            case DGuard(failure=fallback):
                self.add_missing_patterns(fallback, terms, missing)
            case DSwitch(variable=var, cases=cases, fallback=fallback):
                for case in cases:
                    match case.constructor:
                        case BoolCons(val):
                            terms.append(
                                Term(var, "true" if val == 1 else "false", [])
                            )
                        case IntCons():
                            terms.append(Term(var, "_", []))
                        case VariantCons(name=name):
                            args = case.arguments
                            terms.append(Term(var, name, args))
                        case _:
                            raise NotImplementedError("Unknown constructor")

                    self.add_missing_patterns(case.body, terms, missing)
                    terms.pop()

                if node := fallback:
                    self.add_missing_patterns(node, terms, missing)


"""
"""


@dataclass
class IgualaCompiler:
    scope: Scope
    diagnostics: Diagnostics

    def __init__(self, scope: Scope):
        self.scope = scope
        self.diagnostics = Diagnostics(False, [])

    def compile(self, iguala: ast.Iguala) -> Match:
        rows = self._into_rows(iguala)
        return Match(
            tree=self._compile_rows(rows),
            diagnostics=self.diagnostics,
            scope=self.scope,
        )

    def _into_rows(self, iguala: ast.Iguala) -> list[Row]:
        raise NotImplementedError("To be implemented")

    def _expand_or_patterns(self, rows: list[Row]):
        raise NotImplementedError("To be implemented")

    def _compile_rows(self, rows: list[Row]) -> Decision:
        if not rows:
            self.diagnostics.missing = True
            return DFailure()

        # self._expand_or_patterns(rows)

        for row in rows:
            self.move_variable_patterns(row)

        # There may be multiple rows, but if the first one has no patterns
        # those extra rows are redundant, as a row without columns/patterns
        # always matches.

        if rows and not rows[0].columns:
            row = rows.pop(0)
            self.diagnostics.reachable.append(row.body.value)
            guard = row.guard
            return (
                DGuard(guard, row.body, self._compile_rows(rows))
                if guard
                else DSuccess(row.body)
            )

        branch_var = self.branch_variable(rows)

        if not branch_var.type.has_finite_constructors():
            match branch_var.type:
                case Builtins.Int:
                    (cases, fallback) = self.compile_int_cases(rows, branch_var)
                    return DSwitch(branch_var, cases, fallback)
                case _:
                    raise NotImplementedError(
                        "Unknown infinite constructor type"
                    )

        constructors = branch_var.type.get_constructors()
        cases = list(
            map(
                lambda cons: (cons[0], self.new_variables(cons[1])),
                constructors,
            )
        )

        return DSwitch(
            branch_var,
            self.compile_constructor_cases(rows, branch_var, cases),
            None,
        )

    # Compiles the cases and fallback cases for integer and range patterns.
    #
    # Integers have an infinite number of constructors, so we specialise the
    # compilation of integer and range patterns.
    def compile_int_cases(
        self,
        rows: list[Row],
        branch_var: VariableSymbol,
    ) -> tuple[list[Case], Decision]:
        raw_cases = []
        fallback_rows = []
        tested = {}

        for row in rows:
            if col := row.remove_column(branch_var):
                key = None
                cons = None
                match col.pattern:
                    case ast.IntPattern(val):
                        key = (val, val)
                        cons = IntCons(int(val.lexeme))
                    case _:
                        raise NotImplementedError("Invalid pattern")

                if index := tested.get(key):
                    raw_cases[index][2].append(row)
                    continue

                tested[key] = len(raw_cases)
                raw_cases.append((cons, [], [row]))
            else:
                fallback_rows.append(row)

        for _, _, rows in raw_cases:
            rows.extend(fallback_rows)

        cases = list(
            map(
                lambda case: Case(
                    case[0], case[1], self._compile_rows(case[2])
                ),
                raw_cases,
            )
        )

        return (cases, self._compile_rows(fallback_rows))

    # Compiles the cases and sub cases for the constructor located at the
    # column of the branching variable.
    #
    # What exactly this method does may be a bit hard to understand from the
    # code, as there's simply quite a bit going on. Roughly speaking, it does
    # the following:
    #
    # 1. It takes the column we're branching on (based on the branching
    #    variable) and removes it from every row.
    # 2. We add additional columns to this row, if the constructor takes any
    #    arguments (which we'll handle in a nested match).
    # 3. We turn the resulting list of rows into a list of cases, then compile
    #    those into decision (sub) trees.
    #
    # If a row didn't include the branching variable, we simply copy that row
    # into the list of rows for every constructor to test.
    #
    # For this to work, the `cases` variable must be prepared such that it has
    # a triple for every constructor we need to handle. For an ADT with 10
    # constructors, that means 10 triples. This is needed so this method can
    # assign the correct sub matches to these constructors.
    #
    # Types with infinite constructors (e.g. int and string) are handled
    # separately they don't need most of this work anyway.
    def compile_constructor_cases(
        self,
        rows: list[Row],
        branch_var: VariableSymbol,
        cases: list[tuple[Constructor, list[VariableSymbol], list[Row]]],
    ) -> list[Case]:
        for row in rows:
            if col := row.remove_column(branch_var):
                if isinstance(col.pattern, ast.ADTPattern):
                    pattern = col.pattern
                    cons = pattern.cons
                    args = pattern.args
                    idx = cons.index()
                    cols = row.columns
                    for var, pat in zip(cases[idx][1], args):
                        cols.append(Column(var, pat))
                    cases[idx][2].push(Row(cols, row.guard, row.body))
            else:
                for _, _, rows in cases:
                    rows.append(row)

        return list(
            map(
                lambda case: Case(
                    case[0], case[1], self._compile_rows(case[2])
                ),
                cases,
            )
        )

    # Moves variable-only patterns/tests into the right-hand side/body of a
    # case.
    #
    # This turns cases like this:
    #
    #     case foo -> print(foo)
    #
    # Into this:
    #
    #     case -> {
    #       foo = it
    #       print(foo)
    #     }
    #
    # Where `it` is a variable holding the value `case foo` is compared
    # against, and the case/row has no patterns (i.e. always matches).
    def move_variable_patterns(self, row: Row):
        all_cols = row.columns
        row.columns = []

        for col in all_cols:
            match col.pattern:
                case ast.ast.BindingPattern(var):
                    row.body.bindings.append((var, col.variable))
                case _:
                    row.columns.append(col)

    # Given a row, returns the variable in that row that's referred to the
    # most across all rows.
    def branch_variable(self, rows: list[Row]) -> VariableSymbol:
        counts: dict[int, int] = {}
        for row in rows:
            for col in row.columns:
                old_count = counts.setdefault(id(col.variable), 0)
                counts[id(col.variable)] = old_count + 1
        return max(
            map(lambda col: id(col.variable), rows[0].columns),
            key=lambda var: counts[var],  # type: ignore
        )  # type: ignore

    # Returns a new variable to use in the decision tree.
    #
    # In a real compiler you'd have to ensure these variables don't conflict
    # with other variables.
    def new_variable(self, ty: Type) -> VariableSymbol:
        var = Variable(type_id)
        self.variable_id += 1
        return var

    def new_variables(self, types: list[Type]) -> list[VariableSymbol]:
        return [self.new_variable(t) for t in types]
