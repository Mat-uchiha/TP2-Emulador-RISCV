# Emulador RISC-V Simplificado (TP2)

**Disciplina:** ICC062 - Arquitetura de Computadores (2026/2)

**Aluno:** Matheus Ferreira Unten (22450082)


## Como executar

Requisito: **Python 3.10 ou superior** (o código usa `match`/`case`).

```bash
python3 emulador.py codigo.s
```

## Exemplo de execução

Arquivo `caso3.s` (soma de 0 a 9):

```asm
.data
max: .byte 10
.text
main:
la t0, max
lb t0, 0(t0)
li t1, 0
li a0, 0
while: bge t1, t0, end_while
add a0, a0, t1
addi t1, t1, 1
beq zero, zero, while
end_while: li a7, 1
ecall
# return
li a7, 10
ecall
```

Execução:

```bash
$ python3 emulador.py caso3.s
45
```

## Observações


- Valores são mantidos em 32 bits com sinal (complemento de dois), então somas e multiplicações estouram como no hardware real.
- Um `.align` dentro do `.text` preenche o espaço com instruções `addi x0, x0, 0` (nop), para que o `pc` continue andando de 4 em 4 sem cair em um endereço vazio.
- `div` e `rem` seguem o RISC-V: a divisão trunca em direção a zero, divisão por zero dá `-1` e o resto por zero devolve o dividendo.
- O `ecall` de impressão (`a7 = 1`) não adiciona quebra de linha.
- Erros no código-fonte (instrução ou registrador inválido, rótulo inexistente, número errado de operandos, `pc` fora do programa) interrompem a execução com uma mensagem explicando o problema.
