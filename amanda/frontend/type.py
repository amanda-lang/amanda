from amanda.frontend.symbols import Symbol
from enum import IntEnum

#Describes the kind of a type
class OType(IntEnum):
    TINT = 1
    TREAL = 2
    TBOOL = 3
    TTEXTO = 4
    TINDEF = 5
    TVAZIO = 6
    TLISTA = 7
    TKLASS = 8

    def __str__(self):
       return self.name.lower()[1:]


class Type(Symbol):
   def __init__(self,otype):
       super().__init__(str(otype),None)
       self.otype = otype

   def __eq__(self,other):
       if not isinstance(other,Type):
           return False
       return self.otype == other.otype


   def is_numeric(self):
       return self.otype == OType.TINT or self.otype == OType.TREAL

   def is_type(self):
       return True

   def __str__(self):
       return str(self.otype)

   def is_operable(self):
       return self.otype != OType.TVAZIO and self.otype != OType.TINDEF

   def promote_to(self,other):
       otype = self.otype
       other_kind = other.otype

       auto_cast_table = {
            OType.TINT : (OType.TREAL,OType.TINDEF),
            OType.TREAL : (OType.TINDEF,),
            OType.TBOOL : (OType.TINDEF,),
            OType.TTEXTO : (OType.TINDEF,),
            OType.TLISTA : (OType.TINDEF,),
            OType.TKLASS : (OType.TINDEF,),
       }
       auto_cast_types = auto_cast_table.get(otype)

       if not auto_cast_types or other_kind not in auto_cast_types:
           return None

       return other 

class Lista(Type):

   def __init__(self,subtype):
       super().__init__(OType.TLISTA)
       self.subtype = subtype

   def __str__(self):
       return f"[]{self.subtype}"

   def __eq__(self,other):
       if type(other) != Lista:
           return False
       return self.subtype == other.subtype

class Klass(Type):

   def __init__(self,name,members):
       super().__init__(OType.TKLASS)
       self.name = name 
       self.out_id = name 
       self.members = members
       self.constructor = None

   def __str__(self):
       return self.name
