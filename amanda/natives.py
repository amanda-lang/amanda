from amanda.symbols import *
from amanda.object import NativeClass,NativeInstance

class NativeType:

    @classmethod
    def load_symbol(cls,table):
        name = cls.__name__
        table.define(name,ClassSymbol(name))

    @classmethod
    def get_object(cls):
        return NativeClass(cls.__name__,cls)



    @classmethod
    def define_symbol(cls,table):
        namespace = cls.__dict__
        symbol = table.resolve(cls.__name__)
        for method,fields in namespace.get("methods").items():
            type_s = table.resolve(fields["type"])
            if not type_s:
                raise Exception("Error ocurred, type not found")
            #TODO: FIND OUT WTF IS CAUSING THE GHOST PARAM BUG
            method_symbol = FunctionSymbol(method,type_s,params={})
            #Mark this as a constructor
            if method_symbol.name == "constructor":
                method_symbol.is_constructor = True
            params = fields.get("params")
            if params:
                for name,type_param in params:
                    type_param = table.resolve(type_param)
                    if not type_param:
                        raise Exception("Error ocurred, type not found")
                    method_symbol.params[name] = VariableSymbol(name,type_param)
            symbol.members[method] = method_symbol

        for field,type_field in namespace.get("fields"):
            type_field = table.resolve(type_field)
            if not type_s:
                raise Exception("Error ocurred, type not found")
            symbol.members[name] = VariableSymbol(name,type_field)



class Texto(NativeType):
    methods = {
        "constructor":{
            "type":"Texto",
            "params":[("original","Texto")]
        },
        "cmp":{
            "type":"int",
        },

        "e_palin":{
            "type":"bool",
        },

    }

    fields=[]


    def constructor(self,**args):
        initializer = args["args"][0]
        #Hack to get string from literal
        if isinstance(initializer,NativeInstance):
            initializer = initializer.instance.original
        self.original = initializer
    
    def cmp(self,**args):
        return len(self.original)
    
    def e_palin(self,**args):
        return self.original == self.original[::-1]

    def __str__(self):
        return self.original



builtin_types = {
    "Texto":Texto
}
