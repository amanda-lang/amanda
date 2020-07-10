import unittest
import os
import sys
from io import StringIO
from amanda.lexer import Lexer
from amanda.tokens import TokenType,Token
from amanda.parser import Parser
from amanda.error import AmandaError



class LexerTestCase(unittest.TestCase):

    def setUp(self):
        self.buffer = StringIO()

    def test_logic_operators(self):
        self.buffer.write("> < <= >= != == = e ou nao")
        self.buffer.seek(0)
        lexer = Lexer(self.buffer)
        self.assertEqual(lexer.get_token().token,TokenType.GREATER,msg="GREATER Test Failed")
        self.assertEqual(lexer.get_token().token,TokenType.LESS,msg="LESS Test Failed")
        self.assertEqual(lexer.get_token().token,TokenType.LESSEQ,msg="LESSEQ Test Failed")
        self.assertEqual(lexer.get_token().token,TokenType.GREATEREQ,msg="GREATEREQ Test Failed")
        self.assertEqual(lexer.get_token().token,TokenType.NOTEQUAL,msg="NOTEQUAL Test Failed")
        self.assertEqual(lexer.get_token().token,TokenType.DOUBLEEQUAL,msg="DOUBLEEQUAL Test Failed")
        self.assertEqual(lexer.get_token().token,TokenType.EQUAL,msg="EQUAL Test Failed")
        self.assertEqual(lexer.get_token().token,TokenType.E,msg="E Test Failed")
        self.assertEqual(lexer.get_token().token,TokenType.OU,msg="OU Test Failed")
        self.assertEqual(lexer.get_token().token,TokenType.NAO,msg="NAO Test Failed")

    def test_arit_operators(self):
        self.buffer.write("+ - * / % += -= *= /=")
        self.buffer.seek(0)
        lexer = Lexer(self.buffer)
        self.assertEqual(lexer.get_token().token,TokenType.PLUS,msg="PLUS Test Failed")
        self.assertEqual(lexer.get_token().token,TokenType.MINUS,msg="MINUS Test Failed")
        self.assertEqual(lexer.get_token().token,TokenType.STAR,msg="STAR Test Failed")
        self.assertEqual(lexer.get_token().token,TokenType.SLASH,msg="SLASH Test Failed")
        self.assertEqual(lexer.get_token().token,TokenType.MODULO,msg="MODULO Test Failed")
        self.assertEqual(lexer.get_token().token,TokenType.PLUSEQ,msg="PLUSEQ Test Failed")
        self.assertEqual(lexer.get_token().token,TokenType.MINUSEQ,msg="MINUSEQ Test Failed")
        self.assertEqual(lexer.get_token().token,TokenType.STAREQ,msg="STAREQ Test Failed")
        self.assertEqual(lexer.get_token().token,TokenType.SLASHEQ,msg="SLASHEQ Test Failed")


    def test_number(self):
        self.buffer.write("3242131 234.21234")
        self.buffer.seek(0)
        lexer = Lexer(self.buffer)
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.INTEGER,msg="INTEGER Test Failed")
        self.assertEqual(int(token.lexeme),3242131,msg="INTEGER Test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.REAL,msg="REAL Test Failed")
        self.assertEqual(float(token.lexeme),234.21234,msg="REAL Test Failed")


    def test_string(self):
        self.buffer.write("'Rambo jndjnsjndnsjns' ")
        self.buffer.write('"Ramboeiro" ')
        self.buffer.seek(0)
        lexer = Lexer(self.buffer)
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.STRING,msg="STRING Test Failed")
        self.assertEqual(token.lexeme,"'Rambo jndjnsjndnsjns'",msg="STRING value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.STRING,msg="STRING Test Failed")
        self.assertEqual(token.lexeme,'"Ramboeiro"',msg="STRING value Test Failed")

    def test_identifier(self):
        self.buffer.write("_test1 test test2 __test3 var mostra verdadeiro falso retorna se senao enquanto entao inc para faca de fim func classe eu super vazio")
        self.buffer.seek(0)
        lexer = Lexer(self.buffer)
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.IDENTIFIER,msg="ID Test Failed")
        self.assertEqual(token.lexeme,"_test1",msg="ID value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.IDENTIFIER,msg="ID Test Failed")
        self.assertEqual(token.lexeme,"test",msg="ID value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.IDENTIFIER,msg="ID Test Failed")
        self.assertEqual(token.lexeme,"test2",msg="ID value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.IDENTIFIER,msg="ID Test Failed")
        self.assertEqual(token.lexeme,"__test3",msg="ID value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.VAR,msg="VAR Test Failed")
        self.assertEqual(token.lexeme,"var",msg="VAR value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.MOSTRA,msg="ID Test Failed")
        self.assertEqual(token.lexeme,"mostra",msg="MOSTRA value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.VERDADEIRO,msg="VERDADEIRO Test Failed")
        self.assertEqual(token.lexeme,"verdadeiro",msg="VERDADEIRO value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.FALSO,msg="FALSO Test Failed")
        self.assertEqual(token.lexeme,"falso",msg="FALSO value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.RETORNA,msg="RETORNA Test Failed")
        self.assertEqual(token.lexeme,"retorna",msg="RETORNA value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.SE,msg="SE Test Failed")
        self.assertEqual(token.lexeme,"se",msg="SE value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.SENAO,msg="SENAO Test Failed")
        self.assertEqual(token.lexeme,"senao",msg="SENAO value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.ENQUANTO,msg="ENQUANTO Test Failed")
        self.assertEqual(token.lexeme,"enquanto",msg="ENQUANTO value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.ENTAO,msg="ENTAO Test Failed")
        self.assertEqual(token.lexeme,"entao",msg="ENTAO value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.INC,msg="INC Test Failed")
        self.assertEqual(token.lexeme,"inc",msg="INC value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.PARA,msg="PARA Test Failed")
        self.assertEqual(token.lexeme,"para",msg="PARA value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.FACA,msg="FACA Test Failed")
        self.assertEqual(token.lexeme,"faca",msg="FACA value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.DE,msg="DE Test Failed")
        self.assertEqual(token.lexeme,"de",msg="DE value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.FIM,msg="FIM Test Failed")
        self.assertEqual(token.lexeme,"fim",msg="FIM value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.FUNC,msg="FUNC Test Failed")
        self.assertEqual(token.lexeme,"func",msg="FUNC value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.CLASSE,msg="CLASSE Test Failed")
        self.assertEqual(token.lexeme,"classe",msg="CLASSE value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.EU,msg="EU Test Failed")
        self.assertEqual(token.lexeme,"eu",msg="EU value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.SUPER,msg="SUPER Test Failed")
        self.assertEqual(token.lexeme,"super",msg="SUPER value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.VAZIO,msg="VAZIO Test Failed")
        self.assertEqual(token.lexeme,"vazio",msg="VAZIO value test Failed")
        
        

        
    def test_delimeters(self):
        self.buffer.write(". , ; ) ( { } [ ] : ..")
        self.buffer.seek(0)
        lexer = Lexer(self.buffer)
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.DOT,msg="PONTO Test Failed")
        self.assertEqual(token.lexeme,".",msg="DOT value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.COMMA,msg="COMMA Test Failed")
        self.assertEqual(token.lexeme,",",msg="COMMA value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.SEMI,msg="SEMI Test Failed")
        self.assertEqual(token.lexeme,";",msg="SEMI value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.RPAR,msg="RPAR Test Failed")
        self.assertEqual(token.lexeme,")",msg="RPAR value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.LPAR,msg="LPAR Test Failed")
        self.assertEqual(token.lexeme,"(",msg="LPAR value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.LBRACE,msg="LBRACE Test Failed")
        self.assertEqual(token.lexeme,"{",msg="LBRACE value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.RBRACE,msg="RBRACE Test Failed")
        self.assertEqual(token.lexeme,"}",msg="RBRACE value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.LBRACKET,msg="LBRACKET Test Failed")
        self.assertEqual(token.lexeme,"[",msg="LBRACKET value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.RBRACKET,msg="RBRACKET Test Failed")
        self.assertEqual(token.lexeme,"]",msg="RBRACKET value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.COLON,msg="COLON Test Failed")
        self.assertEqual(token.lexeme,":",msg="COLON value test Failed")
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.DDOT,msg="DDOT Test Failed")
        self.assertEqual(token.lexeme,"..",msg="DDOT value test Failed")

    def test_line_count(self):
        self.buffer.write("\n\n\n\n\n")
        self.buffer.seek(0)
        lexer = Lexer(self.buffer)
        token = lexer.get_token()
        while token.token != Lexer.EOF:
            token = lexer.get_token()
        self.assertEqual(lexer.line,6)
        self.assertEqual(lexer.pos,1)

    def test_token_line(self):
        load = ["retorna","retorna"]
        for text in load:
            print(text,file=self.buffer)
        self.buffer.seek(0)
        lexer = Lexer(self.buffer)
        token = lexer.get_token()
        self.assertEqual(token.line,1)
        token = lexer.get_token()
        token = lexer.get_token()
        self.assertEqual(token.line,2)

    def test_whitespace(self):
        self.buffer.write("#This is a one line comment\n#Another linecomment ")
        self.buffer.seek(0)
        lexer = Lexer(self.buffer)
        token = lexer.get_token()
        self.assertEqual(token.token,TokenType.NEWLINE)
        token = lexer.get_token()
        self.assertEqual(token.token,Lexer.EOF)

    def test_invalid_symbol(self):
        self.buffer.write("$")
        self.buffer.seek(0)
        lexer = Lexer(self.buffer)
        self.assertRaises(AmandaError,lexer.get_token)

    def test_invalid_string(self):
        self.buffer.write(" 'I am a string without a closing delimeter")
        self.buffer.seek(0)
        lexer = Lexer(self.buffer)
        self.assertRaises(AmandaError,lexer.get_token)



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

    def test_new_declaration(self):
        phrases = [ " a: int"," a1: real"," a2: bool",
                " a3:real", " troco : real = 3.14","p1,p2,p3 : real", 
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
                eu.nome = nome
                super()
                super(minha,idade)
                eu.idade = idade
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

