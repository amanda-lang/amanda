import sys
''' Base class for all PTScript errors '''
class Error(Exception):

    def __init__(self,message,line,col):
        self.message = message
        self.line = line
        self.col = col


''' Errors that happens during lexing or parsing'''

class Syntax(Error):
    INVALID_SYMBOL = "O símbolo '{symbol}' não foi reconhecido"
    INVALID_STRING = "A sequência de caracteres não foi delimitada"
    MISSING_TERM = "as instruções devem ser delimitadas por ';' ou por uma nova linha"
    ILLEGAL_EXPRESSION = "início inválido de expressão"
    EXPECTED_ID = "era esperado um identificador depois do símbolo '{symbol}'"
    EXPECTED_TYPE = "era esperado um tipo depois do símbolo '{symbol}'"
    ILLEGAL_ASSIGN = "alvo inválido para atribuição"

    def __str__(self):
        return f"\nErro sintático na linha {self.line}: {self.message}.\n"


class Analysis(Error):

    UNDEFINED_TYPE = "o tipo de dados '{type}' não foi definido"
    ID_IN_USE = "O identificador '{name}' já foi declarado neste escopo"
    NO_RETURN_STMT = "a função '{name}' não possui a instrução 'retorna'"
    REPEAT_PARAM = "o parâmetro '{name}' já foi especificado nesta função"
    UNDECLARED_ID ="o identificador '{name}' não foi declarado"
    INVALID_REF = "o identificador '{name}' não é uma referência válida"
    INVALID_OP = "os tipos '{t1}' e '{t2}' não suportam operações com o operador '{operator}'"
    INVALID_UOP = "o operador unário {operator} não pode ser usado com o tipo '{type}' "
    BAD_STR_OP = "o tipo 'texto' não suporta operações com o operador '{operator}'"
    



    def __str__(self):
        return f"\n\nErro na linha {self.line}: {self.message}.\n\n"


class RunTime(Error):
    def __str__(self):
        return f"\n\nErro na linha {self.line}: {self.message}.\n\n"



class ErrorHandler:

    handler = None

    @classmethod
    def get_handler(cls):
        if not cls.handler:
            cls.handler = cls()
        return cls.handler
            
    def get_context(self,error,source):
        '''
        Method that gets the context of an error. the context
        is just just an array with a certain number of lines
        from the source file.
        '''
        if not source.readable():
            raise Exception("Unable to get context for error reporting")
        context = []
        source.seek(0)
        #number of lines to use as context
        n_lines = 2 
        #range to get
        lower_bound = error.line - n_lines 
        upper_bound = error.line

        for count,line in enumerate(source):
            #get lines that are within context range
            if count+1 >= lower_bound:
                fmt_line = "| ".join([str(count+1),line.strip()])
                context.append(fmt_line)
                if count + 1 == upper_bound:
                    source.close()
                    break
        return context

    def fmt_error(self,context,error):
        '''
        Formats the error message using the error
        object and the context.
        
        Ex:

        Erro sintático na linha 5: alguma mensagem aqui
        ------------------------------------------------

        3| var char : texto
        4| var lobo : Animal
        5| var cao : Animal func
                            ^^^^
        '''
        err_marker = "^"
        message = str(error)
        fmt_message = "\n".join([message,"-"*len(message)])
        fmt_context = "\n".join(context)

        # Doing this weird stuff to get the indicator '^' under the loc
        err_line = context[len(context)-1].split("|") 
        code_len = len(err_line[1].strip())
        padding = len(err_line[0]) + 2


        #find the size and create the error indicator
        indicator = err_marker * code_len 
        indicator = indicator.rjust(padding + code_len) 

        return f"{fmt_message}\n{fmt_context}\n{indicator}"




    def throw_error(self,error,source):
        '''
        Method that deals with errors thrown at different stages of the program.
        In theory it's supposed to show the error message and print some context 
        (Lines around the error)

        param: source - io object where the program is being read from
        Ex:
        
        Erro sintático na linha 5: alguma mensagem aqui
        ------------------------------------------------

        3| var char : texto
        4| var lobo : Animal
        5| var cao : Animal func
        '''
        #get context
        context = self.get_context(error,source)
        #print out formatted error message
        print(self.fmt_error(context,error))
        #exit gracefully (i think this is graceful)
        sys.exit() 





if __name__=="__main__":
    error = Syntax(Error.INVALID_STRING,symbol="lool",line=3)
    print(error)
