# 25-26-PL-G06

## Grupo 06

* Ricardo Veloso
* Ana Leite
* Jose Pereira

## Objetivo

Compilador em Python para um subconjunto de Fortran 77, seguindo a pipeline classica de Processamento de Linguagens:

1. analise lexica com `ply.lex`
2. analise sintatica com `ply.yacc`
3. representacao intermedia/AST simples
4. analise semantica sobre a AST
5. geracao de codigo para uma VM de pilha simples, aproximada ao estilo da EWVM

## Subconjunto suportado

* `PROGRAM ... END`
* `INTEGER`, `REAL`, `LOGICAL`
* variaveis simples
* arrays simples com dimensao declarada e acessos indexados
* atribuicoes
* expressoes aritmeticas
* expressoes relacionais
* expressoes logicas
* `IF ... THEN ... ELSE ... ENDIF`
* `DO label var = expr, expr`
* `CONTINUE`
* `GOTO`
* `READ *, ...`
* `PRINT *, ...`

Funcionalidade extra suportada:

* `WRITE *, ...`, tratado como equivalente a `PRINT *, ...` para listas de saida

## Geracao de codigo

O ficheiro `codegen.py` gera codigo textual final para uma VM de pilha simples, aproximada ao estilo da EWVM usada na cadeira.

As instrucoes `PRINT` e `WRITE` do subconjunto suportado seguem o mesmo caminho interno e geram as mesmas instrucoes de escrita da VM.

Valores `LOGICAL` sao representados no codigo gerado como inteiros `0` e `1`.

Instrucoes usadas:

* `PUSHN n`
* `PUSHI valor`
* `PUSHF valor`
* `PUSHS texto`
* `PUSHG endereco`
* `STOREG endereco`
* `PUSHGP`
* `PADD`
* `LOADN`
* `STOREN`
* `ADD`, `SUB`, `MUL`, `DIV`, `NEG`
* `EQUAL`, `INF`, `INFEQ`, `SUP`, `SUPEQ`
* `AND`, `OR`, `NOT`
* `label:`
* `JUMP label`
* `JZ label`
* `READ`
* `ATOI`, `ATOF`
* `WRITEI`, `WRITEF`, `WRITES`
* `STOP`

As variaveis globais sao mapeadas para enderecos numericos. Arrays ocupam blocos contiguos de memoria global e usam acesso indireto simplificado com `PUSHGP`, `PADD`, `LOADN` e `STOREN`.

Este output segue convencoes proximas da EWVM, mas nao foi validado contra um interpretador EWVM externo especifico.

## Limitacoes assumidas

* O codigo fonte e tratado em formato free-form.
* A linguagem e case-insensitive; os identificadores sao normalizados internamente em maiusculas.
* Nao ha suporte a fixed columns de Fortran 77.
* Arrays simples sao suportados, mas nao ha bounds checking dos indices.
* O backend gera codigo aproximado ao estilo da EWVM, mas nao foi validado externamente num interpretador EWVM oficial.

## Como executar

```powershell
python fcompiler.py examples\hello.f
```

## Como correr os testes

```powershell
python -m unittest -v
```
