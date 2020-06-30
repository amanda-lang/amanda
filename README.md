# Amanda

Amanda is a statically typed programming language with portuguese constructs. 
It is implemented using a tree walk intepreter and was mainly made to help me get a feel for progamming language design and implementation. 
You can't do much with it due to it's slowness and lack of more expressive features.

## Usage

*TODO: Make instructions better*

*TODO: Add Portuguese version of this lool*

**On Windows**

To run the interpreter on Windows, download and install python 3.0 or higher from [here](https://www.python.org/downloads/windows/) and
then run the following command in the project folder (using CMD):

```
python -m amanda FILE 
```

Replace 'FILE' with the path to an amanda file. You can run the "hello world.ama" example with the following command:

```
python -m amanda examples/hello_word.ama 
```

**On Linux** 

You probably already have python installed so just run the pyamanda script in the main directory of the project
with the following command:

```
pyamanda FILE
```

Replace 'FILE' with the path to an amanda file. You can run the "hello world.ama" with the following command:

```
pyamanda examples/hello_word.ama 
```

If the script doesn't work just run the same command as in windows replacing 'python' with your python 3 binary
(usually python3).

**On Mac**

Just install python and use the same command used in windows.



## Language Tour

*TODO: Just make this better*

#### Syntax

```python

# Comentário simples

var a : int = 1 # o ';' não é necessário
var b : int = 2; # Mas pode ser usado 

func soma(a:int,b:int):int

    retorna a+b


# a palavra 'fim' indica o fim de corpo de uma função, classe e e.t.c
fim 
```

#### Variables

```python

# Variáveis são declaradas com palavra reservada 'var'
var a : int # variável 'a' do tipo int

var b : int = 10 # declaração e atribuição
```

#### Types

| Types         | Values                | 
| ------------- |:----------------------|
| int           | 2,4,-2,0              |
| real          | 2.0,3.15,8.2          |
| bool          | verdadeiro,falso      |
| Texto         | "eu", 'meu'           |

#### Operators

```python

# Operadores aritméticos

2 + 2 # Soma: 4
2 - 2 # Soma: 4
2 * 3 # multiplicação: 6
2 / 2 # divisão inteira: 1
2.1 / 4 # divisão real :  0.525
2 % 2 # resto: 0

# Operadores relacionas

2 > 3 # maior: falso
2 < 3 # menor: verdadeiro
2 >= 3 # maior ou igual : falso
2 <= 3 # maior ou igual : verdadeiro

verdadeiro == falso # igual : falso
verdadeiro != falso # diferente : verdadeiro

#Operadores lógicos

verdadeiro e falso # e lógico : falso
verdadeiro ou falso # ou lógico : verdadeiro
nao verdadeiro # negação : falso
```

#### Strings

```python

# O tipo Texto tem alguns métodos que permitem operações
# entre strings.

"ama".concat("nda") # concatenação : amanda

"amanda".cmp() # tamanho de string : 6 
```

#### Control flow

```python
# se

se 2/6 > 1 entao
    mostra "maior que 1" 
senao
    mostra "menor que 1"
fim

# repetição: enquanto

var i : int

enquanto i < 10 faca
    mostra i
    i += 1
fim

# repetição: para 

para i de 0..11 faca # começa no 0 e termina no 10
    mostra i
fim

```

#### Input

```python

var i : int = leia_int("Digite um inteiro: ") # Exibe a mensagem e lê um inteiro do teclado


var r : real = leia_real("Digite um real: ") # Exibe a mensagem e lê um real do teclado


var s : Texto = leia_real("Digite uma string: ") # Exibe a mensagem e lê uma cadeia de caracteres do teclado
```

#### Output

```python
mostra 1 # exibe 1 
mostra 2.1 # exibe 2.1
mostra verdadeiro # exibe verdadeiro
mostra "texto" # exibe texto

var s : texto = "carro"
mostra s # exibe carro

```

#### Functions

```python
#Função que recebe dois inteiros e retorna a soma deles
func soma (a:int,b:int): int 
    retorna a + b
fim

 
# Função sem tipo de retorno indica que
# a função não retorna nenhum valor
func mostra_soma(a:int,b:int)
    mostra a + b
fim
```

#### Classes


#### Other stuff



