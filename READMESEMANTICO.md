# Etapa 3 - Analisador Semantico

O analisador semantico recebe a AST produzida pelo parser e verifica se o
programa, alem de estar bem escrito, faz sentido para as regras da linguagem
COOL.

## O que e verificado

- classes duplicadas, tipos nativos redefinidos, pais inexistentes e ciclos de
  heranca;
- proibicao de herdar de `Int`, `Bool` e `String`;
- declaracoes de atributos, metodos e parametros;
- tipos declarados, atributos herdados e sobrescrita de metodos;
- identificadores, atribuicoes, operadores e retorno de metodo;
- expressoes `if`, `while`, bloco, `let`, `new`, `case` e chamadas de metodo.

As classes nativas `Object`, `IO`, `Int`, `Bool` e `String` ja fazem parte da
tabela de classes. Os metodos padrao, como `out_int`, `length` e `concat`,
tambem sao conhecidos pela analise.

## Como executar

Para analisar um arquivo COOL semanticamente:

```bash
python main.py semantic exemplos/arquivo.cl
```

Se o programa estiver correto, a saida sera:

```text
Analise semantica concluida com sucesso.
```

Se houver erros, cada um e exibido com o prefixo `Erro semantico:` e o comando
termina com codigo de falha.

## Arquivos principais

```text
semantic.py              # tabela de tipos, escopos e regras semanticas
ast_nodes.py             # nos da AST analisados por semantic.py
main.py                  # modo semantic da linha de comando
tests/test_semantic.py   # testes das regras semanticas
tests/test_main.py       # testes da integracao com a CLI
```

## Como explicar a etapa

> O lexer separa o codigo em tokens e o parser monta a AST. O analisador
> semantico usa essa AST para verificar nomes, heranca, escopos e tipos. Por
> exemplo, ele detecta uma variavel nao declarada, uma chamada de metodo com
> argumento errado ou um `if` cuja condicao nao e booleana.
