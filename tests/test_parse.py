import unittest
import os
import sys
from io import StringIO
from amanda.compiler.tokens import TokenType, Token
from amanda.compiler.parse import Parser, Lexer
from amanda.compiler.error import AmandaError


class LexerTestCase(unittest.TestCase):
    def setUp(self):
        self.buffer = StringIO()
        self.lexer = Lexer("", self.buffer)

    def test_logic_operators(self):
        self.buffer.write("> < <= >= != == = e ou nao")
        self.buffer.seek(0)
        self.assertEqual(
            self.lexer.get_token().token,
            TokenType.GREATER,
            msg="GREATER Test Failed",
        )
        self.assertEqual(
            self.lexer.get_token().token, TokenType.LESS, msg="LESS Test Failed"
        )
        self.assertEqual(
            self.lexer.get_token().token,
            TokenType.LESSEQ,
            msg="LESSEQ Test Failed",
        )
        self.assertEqual(
            self.lexer.get_token().token,
            TokenType.GREATEREQ,
            msg="GREATEREQ Test Failed",
        )
        self.assertEqual(
            self.lexer.get_token().token,
            TokenType.NOTEQUAL,
            msg="NOTEQUAL Test Failed",
        )
        self.assertEqual(
            self.lexer.get_token().token,
            TokenType.DOUBLEEQUAL,
            msg="DOUBLEEQUAL Test Failed",
        )
        self.assertEqual(
            self.lexer.get_token().token,
            TokenType.EQUAL,
            msg="EQUAL Test Failed",
        )
        self.assertEqual(
            self.lexer.get_token().token, TokenType.E, msg="E Test Failed"
        )
        self.assertEqual(
            self.lexer.get_token().token, TokenType.OU, msg="OU Test Failed"
        )
        self.assertEqual(
            self.lexer.get_token().token, TokenType.NAO, msg="NAO Test Failed"
        )

    def test_arit_operators(self):
        self.buffer.write("+ - * / // % += -= *= /=")
        self.buffer.seek(0)

        self.assertEqual(
            self.lexer.get_token().token, TokenType.PLUS, msg="PLUS Test Failed"
        )
        self.assertEqual(
            self.lexer.get_token().token,
            TokenType.MINUS,
            msg="MINUS Test Failed",
        )
        self.assertEqual(
            self.lexer.get_token().token, TokenType.STAR, msg="STAR Test Failed"
        )
        self.assertEqual(
            self.lexer.get_token().token,
            TokenType.SLASH,
            msg="SLASH Test Failed",
        )
        self.assertEqual(
            self.lexer.get_token().token,
            TokenType.DOUBLESLASH,
            msg="DOUBLESLASH Test Failed",
        )
        self.assertEqual(
            self.lexer.get_token().token,
            TokenType.MODULO,
            msg="MODULO Test Failed",
        )
        self.assertEqual(
            self.lexer.get_token().token,
            TokenType.PLUSEQ,
            msg="PLUSEQ Test Failed",
        )
        self.assertEqual(
            self.lexer.get_token().token,
            TokenType.MINUSEQ,
            msg="MINUSEQ Test Failed",
        )
        self.assertEqual(
            self.lexer.get_token().token,
            TokenType.STAREQ,
            msg="STAREQ Test Failed",
        )
        self.assertEqual(
            self.lexer.get_token().token,
            TokenType.SLASHEQ,
            msg="SLASHEQ Test Failed",
        )

    def test_number(self):
        self.buffer.write("3242131 234.21234")
        self.buffer.seek(0)

        token = self.lexer.get_token()
        self.assertEqual(
            token.token, TokenType.INTEGER, msg="INTEGER Test Failed"
        )
        self.assertEqual(int(token.lexeme), 3242131, msg="INTEGER Test Failed")
        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.REAL, msg="REAL Test Failed")
        self.assertEqual(float(token.lexeme), 234.21234, msg="REAL Test Failed")

    def test_string(self):
        self.buffer.write("'Rambo jndjnsjndnsjns' ")
        self.buffer.write('"Ramboeiro" ')
        self.buffer.seek(0)

        token = self.lexer.get_token()
        self.assertEqual(
            token.token, TokenType.STRING, msg="STRING Test Failed"
        )
        self.assertEqual(
            token.lexeme,
            "'Rambo jndjnsjndnsjns'",
            msg="STRING value test Failed",
        )
        token = self.lexer.get_token()
        self.assertEqual(
            token.token, TokenType.STRING, msg="STRING Test Failed"
        )
        self.assertEqual(
            token.lexeme, '"Ramboeiro"', msg="STRING value Test Failed"
        )

    def test_format_str(self):
        self.buffer.write("f'Rambo jndjnsjndnsjns' ")
        self.buffer.write('f"Ramboeiro" ')
        self.buffer.seek(0)

        token = self.lexer.get_token()
        self.assertEqual(
            token.token, TokenType.FORMAT_STR, msg="FORMAT_STR Test Failed"
        )
        self.assertEqual(
            token.lexeme,
            "'Rambo jndjnsjndnsjns'",
            msg="FORMAT_STR value test Failed",
        )
        token = self.lexer.get_token()
        self.assertEqual(
            token.token, TokenType.FORMAT_STR, msg="FORMAT_STR Test Failed"
        )
        self.assertEqual(
            token.lexeme, '"Ramboeiro"', msg="FORMAT_STR value Test Failed"
        )

    def test_identifier(self):
        self.buffer.write(
            "_test1 test test2 __test3 nulo var mostra verdadeiro falso retorna se senao senaose enquanto entao inc para faca de fim func classe eu usa super vazio escolha caso como nativa quebra continua"
        )
        self.buffer.seek(0)

        token = self.lexer.get_token()
        self.assertEqual(
            token.token, TokenType.IDENTIFIER, msg="ID Test Failed"
        )
        self.assertEqual(token.lexeme, "_test1", msg="ID value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(
            token.token, TokenType.IDENTIFIER, msg="ID Test Failed"
        )
        self.assertEqual(token.lexeme, "test", msg="ID value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(
            token.token, TokenType.IDENTIFIER, msg="ID Test Failed"
        )
        self.assertEqual(token.lexeme, "test2", msg="ID value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(
            token.token, TokenType.IDENTIFIER, msg="ID Test Failed"
        )
        self.assertEqual(token.lexeme, "__test3", msg="ID value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.NULO, msg="ID Test Failed")
        self.assertEqual(token.lexeme, "nulo", msg="ID value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(
            token.token, TokenType.IDENTIFIER, msg="ID Test Failed"
        )
        self.assertEqual(token.lexeme, "var", msg="ID value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.MOSTRA, msg="ID Test Failed")
        self.assertEqual(token.lexeme, "mostra", msg="MOSTRA value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(
            token.token, TokenType.VERDADEIRO, msg="VERDADEIRO Test Failed"
        )
        self.assertEqual(
            token.lexeme, "verdadeiro", msg="VERDADEIRO value test Failed"
        )
        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.FALSO, msg="FALSO Test Failed")
        self.assertEqual(token.lexeme, "falso", msg="FALSO value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(
            token.token, TokenType.RETORNA, msg="RETORNA Test Failed"
        )
        self.assertEqual(
            token.lexeme, "retorna", msg="RETORNA value test Failed"
        )
        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.SE, msg="SE Test Failed")
        self.assertEqual(token.lexeme, "se", msg="SE value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.SENAO, msg="SENAO Test Failed")
        self.assertEqual(token.lexeme, "senao", msg="SENAO value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(
            token.token, TokenType.SENAOSE, msg="SENAOSE Test Failed"
        )
        self.assertEqual(
            token.lexeme, "senaose", msg="SENAOSE value test Failed"
        )
        token = self.lexer.get_token()
        self.assertEqual(
            token.token, TokenType.ENQUANTO, msg="ENQUANTO Test Failed"
        )
        self.assertEqual(
            token.lexeme, "enquanto", msg="ENQUANTO value test Failed"
        )
        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.ENTAO, msg="ENTAO Test Failed")
        self.assertEqual(token.lexeme, "entao", msg="ENTAO value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.INC, msg="INC Test Failed")
        self.assertEqual(token.lexeme, "inc", msg="INC value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.PARA, msg="PARA Test Failed")
        self.assertEqual(token.lexeme, "para", msg="PARA value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.FACA, msg="FACA Test Failed")
        self.assertEqual(token.lexeme, "faca", msg="FACA value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.DE, msg="DE Test Failed")
        self.assertEqual(token.lexeme, "de", msg="DE value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.FIM, msg="FIM Test Failed")
        self.assertEqual(token.lexeme, "fim", msg="FIM value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.FUNC, msg="FUNC Test Failed")
        self.assertEqual(token.lexeme, "func", msg="FUNC value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(
            token.token, TokenType.CLASSE, msg="CLASSE Test Failed"
        )
        self.assertEqual(token.lexeme, "classe", msg="CLASSE value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.EU, msg="EU Test Failed")
        self.assertEqual(token.lexeme, "eu", msg="EU value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.USA, msg="USA Test Failed")
        self.assertEqual(token.lexeme, "usa", msg="USA value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.SUPER, msg="SUPER Test Failed")
        self.assertEqual(token.lexeme, "super", msg="SUPER value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.VAZIO, msg="VAZIO Test Failed")
        self.assertEqual(token.lexeme, "vazio", msg="VAZIO value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(
            token.token, TokenType.ESCOLHA, msg="ESCOLHA Test Failed"
        )
        self.assertEqual(
            token.lexeme, "escolha", msg="ESCOLHA value test Failed"
        )
        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.CASO, msg="CASO Test Failed")
        self.assertEqual(token.lexeme, "caso", msg="CASO value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.COMO, msg="COMO Test Failed")
        self.assertEqual(token.lexeme, "como", msg="COMO value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(
            token.token, TokenType.NATIVA, msg="nativa Test Failed"
        )
        self.assertEqual(token.lexeme, "nativa", msg="nativa value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(
            token.token, TokenType.QUEBRA, msg="quebra Test Failed"
        )
        self.assertEqual(token.lexeme, "quebra", msg="quebra value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(
            token.token, TokenType.CONTINUA, msg="continua Test Failed"
        )
        self.assertEqual(
            token.lexeme, "continua", msg="continua value test Failed"
        )

    def test_delimeters(self):
        self.buffer.write(". , ; ) ( { } [ ] : .. ::")
        self.buffer.seek(0)

        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.DOT, msg="PONTO Test Failed")
        self.assertEqual(token.lexeme, ".", msg="DOT value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.COMMA, msg="COMMA Test Failed")
        self.assertEqual(token.lexeme, ",", msg="COMMA value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.SEMI, msg="SEMI Test Failed")
        self.assertEqual(token.lexeme, ";", msg="SEMI value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.RPAR, msg="RPAR Test Failed")
        self.assertEqual(token.lexeme, ")", msg="RPAR value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.LPAR, msg="LPAR Test Failed")
        self.assertEqual(token.lexeme, "(", msg="LPAR value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(
            token.token, TokenType.LBRACE, msg="LBRACE Test Failed"
        )
        self.assertEqual(token.lexeme, "{", msg="LBRACE value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(
            token.token, TokenType.RBRACE, msg="RBRACE Test Failed"
        )
        self.assertEqual(token.lexeme, "}", msg="RBRACE value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(
            token.token, TokenType.LBRACKET, msg="LBRACKET Test Failed"
        )
        self.assertEqual(token.lexeme, "[", msg="LBRACKET value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(
            token.token, TokenType.RBRACKET, msg="RBRACKET Test Failed"
        )
        self.assertEqual(token.lexeme, "]", msg="RBRACKET value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.COLON, msg="COLON Test Failed")
        self.assertEqual(token.lexeme, ":", msg="COLON value test Failed")
        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.DDOT, msg="DDOT Test Failed")
        self.assertEqual(token.lexeme, "..", msg="DDOT value test Failed")

        token = self.lexer.get_token()
        self.assertEqual(
            token.token, TokenType.DOUBLECOLON, msg="DOUBLECOLON Test Failed"
        )
        self.assertEqual(
            token.lexeme, "::", msg="DOUBLECOLON value test Failed"
        )

    def test_line_count(self):
        self.buffer.write("\n\n\n\n\n")
        self.buffer.seek(0)

        token = self.lexer.get_token()
        while token.token != Lexer.EOF:
            token = self.lexer.get_token()
        self.assertEqual(self.lexer.line, 6)
        self.assertEqual(self.lexer.pos, 1)

    def test_token_line(self):
        load = ["retorna", "retorna"]
        for text in load:
            print(text, file=self.buffer)
        self.buffer.seek(0)

        token = self.lexer.get_token()
        self.assertEqual(token.line, 1)
        token = self.lexer.get_token()
        token = self.lexer.get_token()
        self.assertEqual(token.line, 2)

    def test_whitespace(self):
        self.buffer.write("#This is a one line comment\n#Another linecomment ")
        self.buffer.seek(0)

        token = self.lexer.get_token()
        self.assertEqual(token.token, TokenType.NEWLINE)
        token = self.lexer.get_token()
        self.assertEqual(token.token, Lexer.EOF)

    def test_invalid_symbol(self):
        self.buffer.write("$")
        self.buffer.seek(0)
        self.assertRaises(AmandaError, self.lexer.get_token)

    def test_invalid_string(self):
        self.buffer.write(" 'I am a string without a closing delimeter")
        self.buffer.seek(0)
        self.assertRaises(AmandaError, self.lexer.get_token)


class ParserTestCase(unittest.TestCase):
    def setUp(self):
        self.buffer = StringIO()
        self.parser = Parser("", self.buffer)

    def tearDown(self):
        self.buffer = None

    def test_parse_one_line_eof(self):
        phrases = ["mostra 1"]
        for phrase in phrases:
            print(phrase, file=self.buffer, end="")
        # self.buffer.writelines(phrases)
        self.buffer.seek(0)
        self.parser.parse()

    def test_parse_two_line_eof(self):
        phrases = ["mostra 1\n", "mostra 2"]
        for phrase in phrases:
            print(phrase, file=self.buffer, end="")
        # self.buffer.writelines(phrases)
        self.buffer.seek(0)
        self.parser.parse()

    def test_new_declaration(self):
        phrases = [
            " a: int",
            " a1: real",
            " a2: bool",
            " a3:real",
            " troco : real = 3.14",
            "p1,p2,p3 : real",
            "array : []int",
            "array1 : []bool",
            "array2 : []texto",
            "array : []real",
        ]
        for phrase in phrases:
            print(phrase, file=self.buffer, end="\n\n\n")
        self.buffer.seek(0)
        self.parser.parse()

    def test_expression(self):
        phrases = [
            "2-1",
            "2+1",
            "2/1",
            "2//1",
            "2*1//2*1",
            "2*1",
            "2%1",
            "2+ad",
            "'string'+'op'",
            "2.132+1",
            "'string'*2",
            "string*2",
            "string*5",
            "a+b-c*array%(-a)/(-c)+eval(2+1,5)",
            "+--2---5",
            "'string'/2.241 ",
            "(c*array+soma(1-3))/((2.132+1)*('string'*2))",
            "a",
            "add(1-2)",
            "array",
            "a = b",
            "a = soma(a)",
            "a = a",
            "b = soma(a)",
            "a=b=c=d=a",
            "a=b=c=d=soma(b)",
            "(a+b>a-b)",
            "(((a-b>=a+c)<(a-b))<=(a*2+5)) ou falso != nao verdadeiro",
            "a += 1;a-=2*1;a*=4*(76-2)",
            "callback(a,b,c)()",
            "string.texo",
            "string.get_texto()",
            "klass()()().stop_please()",
            "string.texto='sss'",
            "numero.value+=1",
            "numero.value().set = 1",
            "array[0]",
            "(array[i] - array[i-u])*array[m]",
            "lista(int,3)",
            "lista(int,3 + a);lista(nulo,3)",
        ]
        for phrase in phrases:
            print(phrase, file=self.buffer)
        # self.buffer.writelines(phrases)
        self.buffer.seek(0)
        self.parser.parse()

    def test_usa(self):
        phrases = [
            "\n\nusa 'calc'",
            "\nusa 'calc'",
            "usa 'calc' como calculo\n\n",
            'usa "calc.ama" como calculo\n',
        ]
        for phrase in phrases:
            print(phrase, file=self.buffer)
        # self.buffer.writelines(phrases)
        self.buffer.seek(0)
        self.parser.parse()

    def test_cast(self):
        phrases = [
            "(2+2)::int",
            "8::real - 8.8 * 1 - 8",
            "1::bool == verdadeiro",
            "1::[]int == verdadeiro",
        ]
        for phrase in phrases:
            print(phrase, file=self.buffer)
        # self.buffer.writelines(phrases)
        self.buffer.seek(0)
        self.parser.parse()

    def test_statement(self):
        phrases = [
            "mostra 2-1",
            "retorna eval(2*1+((21-1)*12));",
            "retorna a;",
            "retorna a",
            "mostra a+b-c*array%(-a)/(-c)+eval(2+1,5);",
            """
            se verdadeiro == falso entao  
                rebenta
            fim

            se  1 < 2 entao
                rouba   
                nulo
            fim
        
            se  1==2  entao
                devolve   
            senao
                vai_preso   
            fim

            se  0==0  entao 
                rebenta 
            senaose 1==1 entao
                cria_algo
            senaose 2-1 > 0 entao
                a = 0
            senaose 2-1 > 0 entao
                a = 0
            senao
                fecha 
            fim

            se  verdadeiro == falso  entao 
                rebenta   
            senao
                se a == 1 entao
                  a -1
                senao
                    a: int 
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


            escolha num_int:
                caso 1: 
                    mostra 1



                caso 2:
                    mostra 2
                caso 3: 
                    mostra 3

                caso 4: 
                    mostra 4

                senao:
                    mostra "erro"
            fim
            """,
        ]
        for phrase in phrases:
            print(phrase, file=self.buffer)
        # self.buffer.writelines(phrases)
        self.buffer.seek(0)
        self.parser.parse()

    def test_function_decl(self):
        phrases = [
            """
            func test(a:int,b:int): int
                2-1
                 soma : int = a+b
                #mostra a+b-c*array%(-a)/(-c)+eval(2+1,5)
                retorna -soma+(2*2%1)
            fim

            func test(a:int,b:int): int
                2-1;
                 soma : int = a+b;
                #mostra a+b-c*array%(-a)/(-c)+eval(2+1,5);
                retorna -soma+(2*2%1);
            fim
            


            func test(): int 

            fim

            func test(): vazio 

            fim

            func test(a:int,b:int): vazio 

            fim

            func test(a: []real,b: []int)  

            fim

            func test(a: []real,b: []int) : []int  

            fim
        """
        ]
        for phrase in phrases:
            print(phrase, file=self.buffer)
        # self.buffer.writelines(phrases)
        self.buffer.seek(0)
        self.parser.parse()

    def test_multidim_arrays(self):
        phrases = [
            """
            array : [][]int 
            array : [][]int = [[][]int: ] 
            array : [][][][]texto = [[][][]int: ] 
            [[]int:
                [int:],
                [int:],
                [int:]
            ]
        """
        ]
        for phrase in phrases:
            print(phrase, file=self.buffer)
        # self.buffer.writelines(phrases)
        self.buffer.seek(0)
        self.parser.parse()

    def test_list_literals(self):
        phrases = [
            """
            
            array : []int = [int:]
            array : []int = [int: 1]
            array : []int = [texto:1, 2, 3, 4]
            array : []texto = [real: "1", "2", "3", "4"]
            array : []texto = [[]int: 1 + 2, print(), Loum, 2 == 3]
            array : []texto = [texto: 1 + 2, 1 - 2 + 1 - 7 , 2/5, 2//7]
            array : []texto = [real: 1 > 2, print() > 9, Loum < 2, 2 == 3]
            array : []real = [[]real: [real: ], [real: ], [real: ]]
            print([int: ])

            [int: 1, 2] + [int: 4, 5]
            [int: 
                1, 2,
                3, 4
            ]

            se [real: 
                1, 2, 3, 4, 5
            ][0] > 1 entao
            fim
        """
        ]
        for phrase in phrases:
            print(phrase, file=self.buffer)
        # self.buffer.writelines(phrases)
        self.buffer.seek(0)
        self.parser.parse()

    def test_class_decl(self):
        phrases = [
            """
             classe Ponto
                x : int
                y : int

                func e_origem():bool
                    retorna falso
                fim

                func e_origem():bool
                    eu.x = "lool"
                fim
             fim

        """
        ]
        for phrase in phrases:
            print(phrase, file=self.buffer)
        # self.buffer.writelines(phrases)
        self.buffer.seek(0)
        self.parser.parse()
