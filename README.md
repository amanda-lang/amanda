# Amanda
![tests](https://github.com/stackswithans/amanda/workflows/tests/badge.svg)

Amanda is a statically typed programming language with portuguese constructs. 
It is implemented using a Python backend (The source code is compiled/translated to Python and then executed) and was mainly made to help me get a feel for progamming language design and implementation. 
You can't do much with it due to it's lacklustre perfomance and lack of serious features.

## Usage

~~TODO: Make instructions better~~ 
~~TODO: Add Portuguese version of this lool~~

**On Windows**


To run the interpreter on Windows, download python 3.0 or higher from [here](https://www.python.org/downloads/windows/), run the installer and make sure the install to PATH option is selected, wait for the installation to finish and run the following command in the project folder (using CMD):

```
python -m amanda FILE 
```

Replace 'FILE' with the path to an amanda file. You can run the "hello_world.ama" example with the following command:

```
python -m amanda examples/hello_world.ama 
```

**On Linux** 

You probably already have python installed so just run the same command as in windows replacing 'python' with your python 3 binary
(usually python3):

```
python3 -m amanda FILE
```

Replace 'FILE' with the path to an amanda file. You can run the "hello_world.ama" with the following command:

```
python3 -m examples/hello_word.ama 
```

**On Mac**
Can't help you, i'm sorry :cry: .



## Language Tour

~~TODO: Improve the tour~~

#### Syntax

```python

# Comentário simples



# Instruções são delimitadas por uma nova linha
# ou por ';'

a : int = 1 # o ';' não é necessário
b : int = 2


# Mas pode ser usado
a : int = 1; 
b : int = 2;



func soma(a:int,b:int):int
    retorna a+b
fim # a palavra 'fim' indica o fim de corpo de uma função, classe e e.t.c
```

#### Variables

```python

# Declaração simples
a : int # variável 'a' do tipo int

b : int = 10 # declaração e atribuição

#Variáveis do mesmo tipo podem ser declaradas na mesma linha
a,b : int
a = 10
b = 50
```

#### Types

| Types         | Values                | 
| ------------- |:----------------------|
| int           | 2, 4, -2, 0           |
| real          | 2.0, 3.15, -8.2       |
| bool          | verdadeiro, falso     |
| texto         | "eu", 'meu'           |

#### Operators

```python

# Operadores aritméticos

2 + 2 # Soma: 4
2 - 2 # Soma: 4
2 * 3 # multiplicação: 6
1 // 2 # divisão inteira: 0
1 / 2 # divisão real :  0.5
2 % 2 # resto: 0

# Operadores relacionais

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

"ama" + "nda" # concatenação : amanda

"ama" == "nda" # comparação : falso

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

i : int

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

i : int = leia_int("Digite um inteiro: ") # Exibe a mensagem e lê um inteiro do teclado


r : real = leia_real("Digite um real: ") # Exibe a mensagem e lê um real do teclado


s : texto = leia("Digite uma string: ") # Exibe a mensagem e lê uma cadeia de caracteres do teclado
```

#### Output

```python
mostra 1 # exibe 1 
mostra 2.1 # exibe 2.1
mostra verdadeiro # exibe verdadeiro
mostra "texto" # exibe texto

s : texto = "carro"
mostra s # exibe carro

```

#### Functions

```python
#Função que recebe dois inteiros e retorna a soma deles
func soma (a:int,b:int): int # retorna um inteiro
    retorna a + b
fim

 
# Função sem tipo de retorno indica que
# a função não retorna nenhum valor
func mostra_soma(a:int,b:int) # sem tipo de retorno
    mostra a + b
fim
```

### Lists (Arrays)
```python

# Uma lista serve para armazenar vários valores
#do mesmo tipo
#Para criar a lista use a 'função' lista

minha_lista : [] int = lista(int,4) # tipo e o tamanho

# Preencher a lista

para i de 0..tamanho(minha_lista) faca
    minha_lista[i] = i*i
fim

# Imprimir todos elementos da lista

para i de 0..tamanho(minha_lista) faca
    mostra minha_lista[i]
fim
```


#### Classes
```python

classe Ponto # Uma classe agrega campos e funções

    x : real
    y : real

    func e_origem():bool
        retorna (x == 0) e (y == 0)
    fim


    func distancia(p2 : Ponto):real
        dist : real =  (x - p2.x) + (y - p2.y)
        se dist < 0 entao
            retorna dist * (-1)
        fim
        retorna dist
    fim

    func e_igual(p2 : Ponto) : bool

        retorna (eu.x == p2.x) e (eu.y == p2.y)

    fim

fim


p : Ponto = Ponto(0,0) # inicializa um ponto com x = 0  e y = 0 

mostra p.x # 0
mostra p.y # 0

mostra p.e_origem() # verdadeiro

p1 : Ponto = Ponto(1,3.4)
mostra p.e_igual(p1) # falso
```

