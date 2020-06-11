from amanda.symbols import *

class NativeType:

    @classmethod
    def load_symbol(cls,table):
        name = cls.__name__
        table.define(name,ClassSymbol(name))


    @classmethod
    def define_symbol(cls,table):
        namespace = cls.__dict__
        symbol = table.resolve(cls.__name__)
        for method,fields in namespace.get("methods").items():
            type_s = table.resolve(fields["type"])
            if not type_s:
                raise Exception("Error ocurred, type not found")
            method_symbol = FunctionSymbol(method,type_s)
            params = fields.get("params")
            if params:
                for name,type_s in params:
                    type_s = table.resolve(type_s)
                    if not type_s:
                        raise Exception("Error ocurred, type not found")
                    method_symbol.params[name] = VariableSymbol(name,type_s)
            symbol.members[method] = method_symbol

        for field,type_s in namespace.get("fields"):
            type_s = table.resolve(type_s)
            if not type_s:
                raise Exception("Error ocurred, type not found")
            symbol.members[name] = VariableSymbol(name,type_s)



class Texto(NativeType):
    methods = {
        "constroi":{
            "type":"Texto",
            "params":[("texto","Texto")]
        },
        "cmp":{
            "type":"int",
        },

        "e_palin":{
            "type":"int",
        },

    }

    fields=[("texto","Texto")]


    def constroi(self,texto):
        self.texto = initial
    
    def cmp(self):
        return len(self.content)
    
    def e_palin(self):
        return self.content == self.content[::-1]





builtin_types ={
    "Texto" : Texto,
}


