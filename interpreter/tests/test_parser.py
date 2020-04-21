import unittest
from interpreter.parser import Parser
from interpreter.lexer import Lexer
from interpreter.tokens import TokenType,Token
from io import StringIO


#buffer = StringIO("")



class ParserTestCase(unittest.TestCase):
    def setUp(self):
        self.buffer = StringIO()

    def tearDown(self):
        self.buffer = None

    def test_declaration(self):
        phrases = [ "decl int a;","declara real a1;","declara bool a2;",
            "declara real a3;", "decl real troco = 3.14;", "vector int array[2];"
            "vector int array[2+1];","vector string array[(-(-2))+2];"
        ]
        for phrase in phrases:
            print(phrase,file=self.buffer,end="\n")
        print(self.buffer.getvalue())
        self.buffer.seek(0)
        parser = Parser(Lexer(self.buffer))
        parser.parse()

    def test_expression(self):
        phrases = ["2-1;","2+1;","2/1;","2*1;","2%1;","2+ad;",
            "'string'+'op';","2.132+1;","'string'*2;","string*2;",
            "string[0]*5;","a+b-c*array[1]%(-a)/(-c)+eval(2+1,5);","+--2---5;"
            "'string'/2.241;","(c*array[1]+soma(1-3))/((2.132+1)*('string'*2));",
            "a;","add(1-2);","array[1];","a = b;","a = func(a);",
            "a[0] = a;","b[0] = func(a);","a=b=c=d=a[0];","a=b=c=d=func(b);","(a+b>a-b);",
            "(((a-b>=a+c)<(a-b))<=(a*2+5)) ou falso != !verdadeiro;"
        ]
        for phrase in phrases:
            print(phrase,file=self.buffer)
        #self.buffer.writelines(phrases)
        self.buffer.seek(0)
        parser = Parser(Lexer(self.buffer))
        parser.parse()

    def test_statement(self):
        phrases = ["mostra 2-1;","retorna eval(2*1+((21-1)*12));","retorna a[0];",
            "retorna a[0];","mostra a+b-c*array[1]%(-a)/(-c)+eval(2+1,5);",'''
            se (verdadeiro == falso) decl int rebenta;
            se (0==0) {
                rebenta;
            }
            senao{
                fecha;
            }
            se (verdadeiro == falso) rebenta; senao fecha;
            {
                decl int a;
            }
            '''
        ]
        for phrase in phrases:
            print(phrase,file=self.buffer)
        #self.buffer.writelines(phrases)
        self.buffer.seek(0)
        parser = Parser(Lexer(self.buffer))
        parser.parse()

    def test_function_decl(self):
        phrases = ['''
            defina test(int a,int b): int{
                2-1;
                decl int soma = a+b;
                mostra a+b-c*array[1]%(-a)/(-c)+eval(2+1,5);
                retorna -soma+(2*2%1);
            }
            def test(int a,int b): int{
                2-1;
                decl int soma = a+b;
                mostra a+b-c*array[1]%(-a)/(-c)+eval(2+1,5);
                retorna -soma+(2*2%1);
            }
            defina test(int a,int b): int{
            }
            defina test(): int{
            }
            defina test(){
            }
            def test(int a,int b){
            }
            def test(int a,int b,real c,string c){

            }
            def copier(int a,int [] b){

            }
        '''
        ]
        for phrase in phrases:
            print(phrase,file=self.buffer)
        #self.buffer.writelines(phrases)
        self.buffer.seek(0)
        parser = Parser(Lexer(self.buffer))
        parser.parse()




if __name__=="__main__":
    unittest.main()
