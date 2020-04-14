from parser.lexer import Lexer
TEST_FILE = "./parser/test.pts"

if __name__ == "__main__":
    lexer = Lexer(TEST_FILE)
    token = lexer.get_next_token()
    while token.token != Lexer.EOF:
        print(token)
        token = lexer.get_next_token()
