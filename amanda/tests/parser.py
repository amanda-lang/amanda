import unittest
from amanda.parser import Parser
from amanda.lexer import Lexer
from amanda.tokens import TokenType,Token
from io import StringIO


#buffer = StringIO("")



class ParserTestCase(unittest.TestCase):
    def setUp(self):
        self.buffer = StringIO()

    def tearDown(self):
        self.buffer = None

    def test_declaration(self):
        phrases = [ "var a: int","var a1: real","var a2: bool",
            "var a3:real", "var troco : real = 3.14", 
        ]
        for phrase in phrases:
            print(phrase,file=self.buffer,end="\n\n\n")
        self.buffer.seek(0)
        parser = Parser(self.buffer)
        parser.parse()

    def test_expression(self):
        phrases = ["2-1","2+1","2/1","2*1","2%1","2+ad",
            "'string'+'op'","2.132+1","'string'*2","string*2",
            "string*5","a+b-c*array%(-a)/(-c)+eval(2+1,5)","+--2---5",
            "'string'/2.241 ","(c*array+soma(1-3))/((2.132+1)*('string'*2))",
            "a","add(1-2)","array","a = b","a = soma(a)",
            "a = a","b = soma(a)","a=b=c=d=a","a=b=c=d=soma(b)","(a+b>a-b)",
            "(((a-b>=a+c)<(a-b))<=(a*2+5)) ou falso != nao verdadeiro","a += 1;a-=2*1;a*=4*(76-2)", "callback(a,b,c)()","string.texo","string.get_texto()","klass()()().stop_please()","string.texto='sss'","numero.value+=1","numero.value().set = 1"
        ]
        for phrase in phrases:
            print(phrase,file=self.buffer)
        #self.buffer.writelines(phrases)
        self.buffer.seek(0)
        parser = Parser(self.buffer)
        parser.parse()

    def test_statement(self):
        phrases = ["mostra 2-1","retorna eval(2*1+((21-1)*12));","retorna a;",
            "retorna a","mostra a+b-c*array%(-a)/(-c)+eval(2+1,5);",'''
            se verdadeiro == falso entao  
                rebenta
            fim

            se  1 < 2 entao
                rouba   
            fim
        
            se  1==2  entao
                devolve   
            senao
                vai_preso   
            fim

            se  0==0  entao 
                rebenta 
            senao
                fecha 
            fim

            se  verdadeiro == falso  entao 
                rebenta   
            senao
                se a == 1 entao
                  a -1
                senao
                   var a: int 
                fim
            fim
            
            enquanto verdadeiro  faca
                rebenta 
            fim

            enquanto verdadeiro  faca
                rebenta 
            fim


            enquanto verdadeiro  faca
                mostra a 
            fim

            para  i de 0..9  faca
                mostra i 
            fim


            para  i de 0..9  faca
                mostra i+1 
                uno 
                0+2 
            fim


            para  i de num..num+3  faca
                mostra i+1 
                uno 
                0+2 
            fim
            
            para  i de num..num+3 inc num-1  faca
                mostra i+1 
                uno 
                0+2 
            fim
            '''
        ]
        for phrase in phrases:
            print(phrase,file=self.buffer)
        #self.buffer.writelines(phrases)
        self.buffer.seek(0)
        parser = Parser(self.buffer)
        parser.parse()

    def test_function_decl(self):
        phrases = ['''
            func test(a:int,b:int): int
                2-1
                var soma : int = a+b
                #mostra a+b-c*array%(-a)/(-c)+eval(2+1,5)
                retorna -soma+(2*2%1)
            fim

            func test(a:int,b:int): int
                2-1;
                var soma : int = a+b;
                #mostra a+b-c*array%(-a)/(-c)+eval(2+1,5);
                retorna -soma+(2*2%1);
            fim
            


            func test(): int 

            fim

            func test(): vazio 

            fim

            func test(a:int,b:int): vazio 

            fim


            #Procedure declaration
        '''
        ]
        for phrase in phrases:
            print(phrase,file=self.buffer)
        #self.buffer.writelines(phrases)
        self.buffer.seek(0)
        parser = Parser(self.buffer)
        parser.parse()


    def test_class_decl(self):
        src = ''' 
        classe Animal
            
            var nome : Texto
            var idade : int

            func constructor(nome:Texto,idade:int)
            fim

        fim

        classe Humano < Animal

        fim
        ''' 
        print(src,file=self.buffer)
        #self.buffer.writelines(phrases)
        self.buffer.seek(0)
        parser = Parser(self.buffer)
        parser.parse()




if __name__=="__main__":
    unittest.main()
