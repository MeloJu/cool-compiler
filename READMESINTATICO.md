# Etapa 2 - Analisador Sintatico

Nesta etapa foi implementado o analisador sintatico da linguagem COOL usando
`ply.yacc`, aproveitando o analisador lexico ja existente com `ply.lex`.

O analisador sintatico recebe os tokens produzidos pelo lexer e verifica se eles
formam estruturas validas da linguagem, como classes, atributos, metodos e
expressoes. Alem de validar a sintaxe, ele tambem constroi uma AST simples
(Arvore Sintatica Abstrata), que sera usada futuramente pela analise semantica.

## Commit 1 - Parser Inicial

Foi criada a base do analisador sintatico com `ply.yacc`.

Neste primeiro momento, o parser reconhecia apenas um programa minimo formado
por uma classe vazia:

```cool
class Main {
};
```

Tambem foi adicionada ao lexer a funcao `build_lexer(source)`, usada pelo parser
para consumir os tokens diretamente. Diferente da funcao `tokenize`, que retorna
uma lista pronta de tokens para impressao, `build_lexer` cria uma instancia
limpa do lexer para o `ply.yacc`.

Principais pontos:
- criacao de `parser.py`;
- criacao da funcao `parse(source)`;
- primeira regra gramatical para classe vazia;
- testes iniciais do parser.

## Commit 2 - Classes e Heranca

O parser passou a reconhecer programas com multiplas classes e classes com
heranca usando `inherits`.

Exemplos aceitos:

```cool
class A {
};

class B inherits A {
};
```

Quando uma classe nao declara heranca, o parser assume `Object` como classe pai,
seguindo o comportamento padrao de COOL.

Principais pontos:
- programa passou a ser uma lista de classes;
- suporte a varias classes no mesmo arquivo;
- suporte a `inherits`;
- `ClassNode` passou a armazenar o nome da classe pai.

## Commit 3 - Features: Atributos e Metodos

Nesta etapa o parser passou a reconhecer o conteudo dentro das classes. Em COOL,
os elementos dentro de uma classe sao chamados de `features`, podendo ser
atributos ou metodos.

Atributos aceitos:

```cool
x : Int;
x : Int <- 10;
```

Metodos aceitos:

```cool
main() : Object {
  self
};

soma(a : Int, b : Int) : Int {
  a
};
```

Tambem foram adicionadas expressoes minimas para permitir inicializacoes e
corpos de metodos, como inteiros, strings, booleanos e variaveis.

Principais pontos:
- suporte a atributos simples;
- suporte a atributos com inicializacao;
- suporte a metodos;
- suporte a parametros formais;
- criacao dos nos `AttributeNode`, `MethodNode`, `FormalNode`, `LiteralNode` e
  `VariableNode`.

## Commit 4 - AST Simples

Os nos da arvore sintatica foram separados em um arquivo proprio chamado
`ast_nodes.py`.

Antes disso, os nos estavam definidos dentro do proprio `parser.py`. A separacao
deixa o projeto mais organizado, pois o parser fica responsavel pelas regras
gramaticais, enquanto `ast_nodes.py` representa a estrutura do programa.

Principais pontos:
- criacao de `ast_nodes.py`;
- separacao entre regras do parser e estrutura da AST;
- preparacao para a futura etapa de analise semantica.

## Commit 5 - Expressoes Basicas e Precedencia

Foram adicionadas expressoes aritmeticas, comparacoes, atribuicoes e operadores
unarios.

Exemplos aceitos:

```cool
x <- 1 + 2
1 + 2 * 3
(1 + 2) * 3
a < b
a <= b
a = b
not x
isvoid x
~x
```

A precedencia dos operadores foi definida usando o recurso `precedence` do
`ply.yacc`. Isso garante, por exemplo, que:

```cool
1 + 2 * 3
```

seja interpretado como:

```text
1 + (2 * 3)
```

e nao como:

```text
(1 + 2) * 3
```

Principais pontos:
- suporte a atribuicao;
- suporte a operacoes binarias;
- suporte a operadores unarios;
- suporte a parenteses;
- criacao dos nos `AssignNode`, `BinaryOpNode` e `UnaryOpNode`.

## Commit 6 - Expressoes Compostas

Nesta etapa foram implementadas construcoes maiores da linguagem COOL.

Exemplos aceitos:

```cool
if ok then 1 else 2 fi
```

```cool
while ok loop x <- x + 1 pool
```

```cool
{
  x <- 1;
  x + 2;
}
```

```cool
let x : Int <- 1, y : Int in x + y
```

```cool
new Main
```

```cool
f(1, x)
obj.f(1)
obj@IO.out_string("oi")
```

Cada construcao passou a gerar um no especifico na AST.

Principais pontos:
- suporte a `if then else fi`;
- suporte a `while loop pool`;
- suporte a blocos;
- suporte a `let`;
- suporte a `new`;
- suporte a chamadas de metodo;
- suporte a despacho estatico com `@`.

## Commit 7 - Case, Erros e Testes Finais

Foi adicionada a construcao `case`, uma das principais expressoes restantes de
COOL.

Exemplo aceito:

```cool
case valor of
  x : Int => x + 1;
  y : String => 0;
esac
```

Tambem foram adicionados testes de erro sintatico para garantir que o parser
rejeita estruturas incompletas ou invalidas.

Exemplos rejeitados:
- `if` sem `fi`;
- `let` sem `in`;
- `case` sem `esac`;
- chamada de metodo com virgula inicial, como `f(,x)`.

Principais pontos:
- suporte a `case of esac`;
- criacao de `CaseNode` e `CaseBranchNode`;
- ampliacao dos testes sintaticos;
- fechamento da cobertura principal da etapa sintatica.

## CLI: Modos Lexico e Sintatico

O arquivo `main.py` foi atualizado para permitir rodar tanto o analisador lexico
quanto o sintatico.

Para rodar o lexico:

```bash
python main.py lex examples/hello_world.cl
```

Para rodar o sintatico:

```bash
python main.py parse examples/hello_world.cl
```

No modo `lex`, o programa imprime os tokens encontrados.

No modo `parse`, o programa valida a sintaxe do arquivo. Se a analise for
concluida com sucesso, a saida sera:

```text
Analise sintatica concluida com sucesso.
```

## Testes

Para rodar todos os testes:

```bash
python -m unittest discover -s tests -v
```

A suite cobre tanto o analisador lexico quanto o analisador sintatico.
