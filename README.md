# Compilador de COOL — Análise Léxica

Etapa 1 do compilador da linguagem **COOL** (*Classroom Object Oriented
Language*), para a disciplina de Compiladores.

Este repositório contém um analisador léxico construído com **PLY (Python
Lex-Yacc)**, a versão em Python das ferramentas clássicas lex/yacc citadas
no enunciado: em vez de escrever o loop de leitura na mão, cada token é
*declarado* como uma expressão regular e o PLY monta o tokenizer sozinho.

## Como rodar

Requer Python 3 e a dependência `ply` (única dependência do projeto).

```bash
pip install -r requirements.txt
python main.py examples/hello_world.cl
```

Saída (formato `#linha TOKEN valor`):

```
#2 CLASS
#2 TYPEID Main
#2 INHERITS
#2 TYPEID IO
#2 '{'
#3 OBJECTID main
#3 '('
#3 ')'
#3 ':'
#3 TYPEID Object
#3 '{'
#4 OBJECTID out_string
#4 '('
#4 STR_CONST "Hello, World.\n"
#4 ')'
#5 '}'
#5 ';'
#6 '}'
#6 ';'
```

## Estrutura do projeto

```
lexer.py            # regras de tokens do PLY + wrapper tokenize(source)
main.py              # CLI: le um arquivo .cl e imprime os tokens
requirements.txt     # dependência única: ply
examples/            # programas COOL de exemplo
  hello_world.cl
  fibonacci.cl
  erros.cl           # exemplos de erros léxicos, para testar o tratamento de erros
tests/
  test_lexer.py       # testes unitários (unittest)
```

## Como o PLY é usado

O PLY funciona por convenção de nomes: cada função/variável `t_NOME` no
módulo é uma regra de token, e o PLY as combina numa única máquina de
reconhecimento (`lex.lex()` em [lexer.py](lexer.py)).

- **Palavras-chave e identificadores**: uma única regra `t_TYPEID` (letra
  maiúscula) e outra `t_OBJECTID` (letra minúscula) casam o identificador
  inteiro; dentro da função, o valor é comparado com o dicionário
  `reserved` para decidir se é uma palavra-chave (`class`, `if`, ...) ou um
  identificador de verdade. É o padrão usual do PLY para reservar palavras
  sem precisar de uma regra para cada uma.
- **Símbolos de 1 caractere** (`{ } ( ) : ; , . @ ~ * / + - < =`): declarados
  em `literals`, o PLY cria o token sozinho.
- **Símbolos de 2 caracteres** (`<- <= =>`): regras simples `t_ASSIGN`,
  `t_LE`, `t_DARROW`.
- **Comentários de bloco aninhados `(* ... *)`** e **strings `"..."`**:
  usam *estados exclusivos* do PLY (`states`), o equivalente aos "start
  conditions" do flex — ao encontrar `(*` ou `"`, o lexer "entra" num modo
  próprio (`comment` / `string`) onde só as regras `t_comment_*` /
  `t_string_*` valem, o que permite contar profundidade de aninhamento e
  tratar escapes sem interferir com o resto da gramática.

## Tokens reconhecidos

- **Palavras-chave** (case-insensitive): `class else fi if in inherits
  isvoid let loop pool then while case esac new of not`
- **Booleanos**: `true` / `false` (a primeira letra precisa ser minúscula,
  conforme a especificação de COOL)
- **TYPEID**: identificador iniciado com letra maiúscula (`Main`, `Int`, `IO`)
- **OBJECTID**: identificador iniciado com letra minúscula (`main`, `out_int`)
- **INT_CONST**: sequência de dígitos
- **STR_CONST**: string entre aspas duplas, com escapes (`\n \t \b \f \" \\`)
- **Símbolos**: `{ } ( ) : ; , . @ ~ * / + - < =` e os de dois caracteres
  `<- <= =>`
- **Comentários**: de linha (`-- ...`) e de bloco (`(* ... *)`, podendo ser
  aninhados) — ambos são descartados, não geram token

## Tratamento de erros léxicos

Erros também viram um token (`ERROR`), com a linha onde ocorreram, para que
o analisador nunca pare no meio do arquivo. Cada estado (`comment`,
`string`) tem sua própria regra `t_<estado>_eof`/`t_<estado>_error` que
fabrica o token `ERROR` correspondente e devolve o lexer ao estado inicial:

- caractere desconhecido
- string não terminada (quebra de linha ou fim de arquivo dentro da string)
- string contendo caractere nulo
- string com mais de 1024 caracteres
- comentário de bloco não fechado (EOF dentro do comentário)
- `*)` sem `(*` correspondente

Exemplo em `examples/erros.cl`:

```bash
python main.py examples/erros.cl
```

## Testes

```bash
python -m unittest discover -s tests -v
```

## Próximas etapas

Análise sintática (parser), análise semântica e geração de código,
reutilizando os tokens produzidos por este analisador léxico.
