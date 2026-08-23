# Compilador de COOL — Análise Léxica

Etapa 1 do compilador da linguagem **COOL** (*Classroom Object Oriented
Language*), para a disciplina de Compiladores.

Este repositório contém um analisador léxico escrito **manualmente em
Python puro** (sem `ply`/`lex` nem outras dependências): o código-fonte é
percorrido caractere a caractere reconhecendo os tokens da linguagem.

## Como rodar

Requer apenas Python 3 (sem dependências externas).

```bash
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
lexer.py            # o analisador léxico (classe Lexer + função tokenize)
main.py              # CLI: le um arquivo .cl e imprime os tokens
examples/            # programas COOL de exemplo
  hello_world.cl
  fibonacci.cl
  erros.cl           # exemplos de erros léxicos, para testar o tratamento de erros
tests/
  test_lexer.py       # testes unitários (unittest)
```

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
o analisador nunca pare no meio do arquivo:

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
