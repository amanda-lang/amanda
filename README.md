# Amanda
![tests](https://github.com/stackswithans/amanda/workflows/tests/badge.svg)

Amanda is a statically typed programming language with portuguese constructs. 
It is implemented using a Python compiler and a Rust VM.
It's specifically designed to be used by portuguese speakers who are just getting started with programming.

## Build Instructions

To build the project on your machine you need following:
- Python 3.8+
- Rust and Cargo v1.59.0+ 

**On Windows**

Run the following commands at the root folder of the repo using CMD:

```
pip install -r requirements.txt 
python setup.py
```
Test the installation by running the following command on CMD:

```
dist\amanda examples\hello_world.ama 
```

**On Linux/Mac** 

Run the following commands at the root folder of the repo:

```
pip3 install -r requirements.txt 
python3 setup.py
```
Test the installation by running:

```
dist/amanda examples/hello_world.ama 
```

## Tour of Amanda

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

num : real = 5 // 3

se  num > 1 entao
    mostra "maior que 1" 
senaose num == 1 entao
    mostra "igual à 1"
senao
    mostrar "menor que 1"
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

# Também é possível criar uma lista de forma directa
minha_lista = [int: 1, 2, 3]

# Preencher a lista

para i de 0..tamanho(minha_lista) faca
    minha_lista[i] = i*i
fim

# Imprimir todos elementos da lista
para i de 0..tamanho(minha_lista) faca
    mostra minha_lista[i]
fim

#Criar uma matriz 3 x 2
minha_matriz : [][]int = matriz(int, 3, 2)
minha_matriz[0][0] = 1

mostra minha_matriz[0][0]
```


#### Classes
```python

classe Ponto # Uma classe agrega campos e funções

    x : real
    y : real

    func e_origem():bool
        retorna (x == 0) e (y == 0)
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

