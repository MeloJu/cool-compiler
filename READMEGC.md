# Etapa 4 — Geração de Código

Nesta etapa, o compilador recebe um programa em **COOL**, verifica a sintaxe e
a semântica e gera um programa equivalente em **Bril**. Bril é uma linguagem
intermediária de baixo nível, baseada em instruções, registradores, saltos e
funções.

O resultado é um arquivo JSON que pode ser executado pelo interpretador
[brilirs].

## Fluxo da compilação

~~~text
Arquivo .cl
   ↓
Analisador léxico
   ↓
Analisador sintático (AST)
   ↓
Analisador semântico
   ↓
Gerador de código
   ↓
Arquivo .bril.json
   ↓
brilirs
~~~

O código Bril é gerado apenas quando o programa COOL é sintática e
semanticamente válido. Por exemplo, uma variável não declarada ou uma chamada
de método inválida interrompe o processo antes da geração.

## Arquivos principais

~~~text
codegen.py             # traduz a AST de COOL para instruções Bril
main.py                # disponibiliza o modo codegen na linha de comando
run_bril.py            # executa um arquivo .bril.json usando brilirs
tests/test_codegen.py  # testes unitários do gerador
tests/test_run_bril.py # testes do executor
examples/              # exemplos COOL e programas Bril
~~~

## Requisitos

Além do Python e das dependências do projeto, são necessários:

- **brilirs**: interpreta programas Bril no formato JSON;
- **bril2json**: converte Bril textual (.bril) para JSON.

No PowerShell, confirme a instalação:

~~~powershell
cargo --version
brilirs --version
bril2json --help
~~~

Se [bril2json] não for reconhecido, execute uma vez e depois reinicie o
PowerShell:

~~~powershell
uv tool update-shell
~~~

## Como gerar código Bril

Dentro da pasta do projeto:

~~~powershell
python main.py codegen examples/hello_world.cl programa.bril.json
~~~

O comando salva o programa Bril em [programa.bril.json]. Sem o terceiro
argumento, o JSON é exibido no terminal:

~~~powershell
python main.py codegen examples/hello_world.cl
~~~

## Como executar o código gerado

Depois de gerar o arquivo:

~~~powershell
python run_bril.py programa.bril.json
~~~

Ou envie o conteúdo diretamente ao interpretador:

~~~powershell
Get-Content -Raw .\programa.bril.json | brilirs
~~~

## Formatos Bril usados nos exemplos

| Formato | Descrição | Como executar |
| --- | --- | --- |
| .bril | Código Bril textual. | Get-Content -Raw .\examples\arquivo.bril \| bril2json \| brilirs |
| .json | Programa Bril já em JSON. | Get-Content -Raw .\examples\arquivo.json \| brilirs |
| .bril.json | JSON Bril, extensão usada pela saída do compilador. | python run_bril.py .\examples\arquivo.bril.json |

Exemplos disponíveis:

~~~text
examples/book.bril                 # objetos, memória e chamadas de função
examples/soma.bril                 # soma em Bril textual
examples/soma.json                 # soma em JSON
examples/condicional.json          # desvio condicional
examples/multiplicacao.bril.json   # multiplicação
examples/string_ola.bril           # string armazenada na memória
examples/string_ola.json           # string em JSON
examples/string_z.bril.json        # string em .bril.json
~~~

## Recursos traduzidos

O gerador produz Bril para:

- literais Int, Bool e String;
- operadores +, -, *, /, <, <=, =, not, ~ e isvoid;
- blocos, atribuições e escopos let;
- if, while e case;
- criação de objetos com new;
- atributos Int e Bool;
- métodos, parâmetros, retorno e chamadas;
- herança, despacho estático e despacho dinâmico;
- IO.out_int, IO.out_string, String.length, String.concat e String.substr.

## Objetos e strings

Objetos COOL são vetores na memória do Bril. A primeira posição armazena uma
*tag* da classe dinâmica; as posições seguintes armazenam atributos. As tags
são usadas para despacho dinâmico e para selecionar o ramo mais específico de
case.

Uma String é um ponteiro para códigos inteiros de caracteres e termina no valor
0. O programa gerado inclui um runtime para tamanho, concatenação, substring e
impressão de strings. A impressão usa a extensão char do Bril; como cada
instrução print escreve uma linha, os caracteres podem aparecer em linhas
separadas no interpretador.

## Limitações conhecidas

A implementação é didática e ainda não gera código completo para:

- in_int, in_string, abort, type_name e copy;
- atributos de tipo String ou de classes definidas pelo usuário;
- valor padrão de let para objetos definidos pelo usuário;
- semântica completa de isvoid para referências de objetos.

Nesses casos, o compilador mostra [Erro na geracao de codigo:] em vez de gerar
um programa incompleto.

## Testes

Todos os testes:

~~~powershell
python -m unittest discover -s tests -v
~~~

Somente os testes da geração:

~~~powershell
python -m unittest tests.test_codegen -v
python -m unittest tests.test_run_bril -v
~~~

## Resumo para apresentação

> O gerador percorre a AST já validada e traduz cada expressão COOL para Bril.
> Variáveis viram registradores; condicionais e laços viram rótulos e saltos;
> métodos viram funções; e objetos são armazenados na memória. Para String,
> criamos um runtime que trabalha com vetores de códigos de caracteres
> terminados em zero.

