import enum
from amanda.compiler.error import AmandaError


class Indef:
    def __init__(self, value):
        if isinstance(value, Indef):
            value = value.value
        self.value = value

    def __str__(self):
        string = str(self.value)
        value_type = type(self.value)
        if value_type == int:
            string = f"int -> {self.value}"
        elif value_type == float:
            string = f"real -> {self.value}"
        elif value_type == str:
            string = f"texto -> '{self.value}'"
        elif value_type == bool:
            value = "verdadeiro" if self.value else "falso"
            string = f"bool -> {value}"
        return string


# TODO: Allow negative indices
class Lista:
    def __init__(self, subtype, elements=[]):
        self.elements = elements
        self.subtype = subtype

    def __str__(self):
        elements = ", ".join([str(e) for e in self.elements])
        return f"[{elements}]"

    def __getitem__(self, key):
        try:
            return self.elements[key]
        except IndexError:
            raise AmandaError.runtime_err("índice de lista inválido")

    def __setitem__(self, key, value):
        try:
            if key < 0:
                raise IndexError
            self.elements[key] = value
        except IndexError:
            raise AmandaError.runtime_err("índice de lista inválido")


class BaseClass:
    def __init__(self, *args):
        class_dict = self.__class__.__dict__
        for key, value in class_dict.items():
            # Skip special attributes and functions
            if key.startswith("__") or callable(value):
                continue
            setattr(self, key, value)

        instance_dict = self.__dict__
        for key, initializer in zip(instance_dict, args):
            setattr(self, key, initializer)


class Nulo:
    def __getattr__(self, attr):
        raise AmandaError.runtime_err("Não pode aceder uma referência nula")

    def __setattr__(self, attr, value):
        raise AmandaError.runtime_err("Não pode aceder uma referência nula")

    def __str__(self):
        return "nulo"
