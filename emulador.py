# Matheus Ferreira Unten
# 22450082
import sys

#Dicionário auxiliar para os registradores
rs = {'X0': 0, 'X1': 1, 'X2': 2, 'X3': 3, 'X4': 4, 'X5': 5, 'X6': 6, 'X7': 7, 'X8': 8, 'X9': 9, 'X10': 10, 'X11': 11, 'X12': 12, 'X13': 13, 'X14': 14, 'X15': 15, 'X16': 16, 'X17': 17, 'X18': 18, 'X19': 19, 'X20': 20, 'X21': 21, 'X22': 22, 'X23': 23, 'X24': 24, 'X25': 25, 'X26': 26, 'X27': 27, 'X28': 28, 'X29': 29, 'X30': 30, 'X31': 31, 'ZERO': 0, 'RA': 1, 'SP': 2, 'GP': 3, 'TP': 4, 'T0': 5, 'T1': 6, 'T2': 7, 'S0': 8, 'FP': 8, 'S1': 9, 'A0': 10, 'A1': 11, 'A2': 12, 'A3': 13, 'A4': 14, 'A5': 15, 'A6': 16, 'A7': 17, 'S2': 18, 'S3': 19, 'S4': 20, 'S5': 21, 'S6': 22, 'S7': 23, 'S8': 24, 'S9': 25, 'S10': 26, 'S11': 27, 'T3': 28, 'T4': 29, 'T5': 30, 'T6': 31}
TEXT_BASE = 0x00000000 #Endereço-base do segmento de código (.text)
DATA_BASE = 0x00200000 #Endereço-base do segmento de dados (.data)

def number(n): #Função para parse de números
    n = n.strip()
    if not n:
        return 0
    try:
        if n.lower().startswith(('0x', '-0x', '0b', '-0b')):
            return int(n, 0)
        return int(n, 10)
    except ValueError:
        raise ValueError(f"Valor numérico inválido: {n}")


def div_RISCV(a, b): #Divisão do RISC-V, trunca em direção a zero
    if b == 0:
        return -1
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def s32(val): #Garante que o valor seja de 32 bits com sinal
    val &= 0xFFFFFFFF
    if val & 0x80000000:
        val -= 0x100000000
    return val
def u32(val): #Garante que o valor seja de 32 bits sem sinal
    return val & 0xFFFFFFFF


def get_reg(nome): #Valida e padroniza os registradores
    nome = nome.upper()
    if nome not in rs: raise ValueError(f"Registrador inválido: {nome}")
    return f"x{rs[nome]}"


def read_reg(regs, nome): #Lê valores dos registradores
    chave = get_reg(nome)
    if chave not in regs: raise ValueError(f"Registrador inválido: {nome}")
    return regs[chave]


def write_reg(regs, nome, val): #Escreve valores nos registradores
    chave = get_reg(nome)
    if chave == 'x0':
        return #x0 nao pode ser escrito
    regs[chave] = s32(val)


def write_mem(mem, end, val, bites): #Escreve valores na memória no formato little-endian
    for i in range(bites):
        mem[end + i] = (val >> (i*8)) & 0xFF


def read_mem(mem, end, bites, sinal): #Lê valores na memória no formato little-endian
    val = 0
    for i in range(bites):
        val |= mem.get(end + i, 0) << (i*8)
    if sinal: #Se o bit mais significativo estiver ligado, o valor é negativo
        if val & (1 << (bites*8 - 1)):
            val -= 1 << (bites*8)
    return val


def check_args(inst, qtd_esperada): #Verifica se a instrução tem o número correto de operandos
    if len(inst) - 1 != qtd_esperada:
        raise ValueError(f"A instrução {inst[0]} esperava {qtd_esperada} operandos, recebeu {len(inst)-1}")


def read_archive(arquivo_entrada): #Lê o arquivo e cria uma lista de listas do que foi lido
    with open(arquivo_entrada, 'r', encoding='utf-8') as f:
        content = f.read()
    programa = []
    linhas = content.split('\n') #Separa as linhas
  
    for linha in linhas:
        l = linha.split('#')[0] #Remove os comentários
        if not l.strip():
            continue
    
        if ':' in l: #Localiza os rotulos
            partes = l.split(':', 1)
            rotulo = partes[0].strip() + ':'
            programa.append([rotulo])
            l = partes[1]  
        if not l.strip():
            continue

        l = l.replace('(', ' ').replace(')', ' ')
        l = l.replace(',', ' ')
        tokens = l.split() #Separa a linha em tokens
        if tokens: #Adiciona os tokens ao programa
            programa.append(tokens)

    return programa


def first_pass(s): #Primeira passagem para o mapeamento dos dicionarios
    rotulos = {}; instrucoes = {}; memoria = {}
    text_pc = TEXT_BASE; data_pc = DATA_BASE; segmento = 'TEXT'
    i = 0

    while i < len(s): 
        inst = s[i]
        if inst[0][-1] == ':': #Mapeamento dos rotulos.
            rotulo = inst[0][:-1]
            if rotulo in rotulos: raise ValueError(f"Rotulo duplicado: {rotulo}")
            rotulos[rotulo] = text_pc if segmento == 'TEXT' else data_pc
            i+=1; continue
        
        op = inst[0].upper() 
        match op: #Analise das diretivas e instruçoes
            case '.TEXT': segmento = 'TEXT'
            case '.DATA': segmento = 'DATA'
            case '.GLOBL': pass
            case '.ALIGN':
                n = number(inst[1]); alinhamento = 1 << n
                if segmento == 'TEXT':
                    novo_pc = (text_pc + alinhamento - 1) & ~(alinhamento - 1)
                    while text_pc < novo_pc: #Preenche o espaço com NOPs para garantir o alinhamento
                        instrucoes[text_pc] = ['addi', 'x0', 'x0', '0']
                        text_pc += 4
                else:
                    data_pc = (data_pc + alinhamento - 1) & ~(alinhamento - 1)
            case '.WORD': 
                write_mem(memoria, data_pc, number(inst[1]), 4)
                data_pc += 4
            case '.HALF': 
                write_mem(memoria, data_pc, number(inst[1]), 2)
                data_pc += 2
            case '.BYTE': 
                write_mem(memoria, data_pc, number(inst[1]), 1)
                data_pc += 1
            case '.ZERO' | '.SPACE': 
                val = number(inst[1])
                if val < 0: raise ValueError(f"{op} exige tamanho não negativo")
                write_mem(memoria, data_pc, 0, val) #Preenche os n bytes reservados com zero
                data_pc += val
            case _: #Armazena as instruçoes
                instrucoes[text_pc] = inst
                text_pc += 4
        i+=1

    return rotulos, instrucoes, memoria


def ula(op, a, b): #Operações lógicas e aritméticas compartilhadas pelos formatos R e I
    match op:
        case 'ADD': return a + b
        case 'SUB': return a - b
        case 'SLL': return a << (b & 0x1F)
        case 'SLT': return int(a < b)
        case 'SLTU': return int(u32(a) < u32(b))
        case 'XOR': return a ^ b
        case 'SRL': return u32(a) >> (b & 0x1F)
        case 'SRA': return a >> (b & 0x1F)
        case 'OR': return a | b
        case 'AND': return a & b
        case 'MUL': return a * b
        case 'DIV': return div_RISCV(a, b)
        case 'REM': return a if b == 0 else a - b * div_RISCV(a, b)


def get_addr(inst, regs): #Calcula base + offset de loads e stores
    if len(inst) == 3: #Formato ['lw','t0','t1']
        offset = 0
        base = inst[2]
    else: #Formato ['lw','t0','4','t1']
        offset = number(inst[2])
        base = inst[3]
    return read_reg(regs, base) + offset

def get_label(rotulos, nome): #Obtem o endereço de um rótulo
    if nome not in rotulos:
        raise ValueError(f"Rotulo não encontrado: {nome}")
    return rotulos[nome]


def executar(inst, regs, mem, rotulos): #Executa uma instrução e devolve ou o novo pc ou None (pc += 4) ou FIM
    tam = {'LB': 1, 'LH': 2, 'LW': 4, 'LBU': 1, 'LHU': 2, 'SB': 1, 'SH': 2, 'SW': 4} #Bytes acessados por cada load/store
    op = inst[0].upper()

    match op:
        #Formato R (rd = rs1 op rs2)
        case 'ADD' | 'SUB' | 'SLL' | 'SLT' | 'SLTU' | 'XOR' | 'SRL' | 'SRA' | 'OR' | 'AND' | 'MUL' | 'DIV' | 'REM':
            check_args(inst, 3)
            a = read_reg(regs, inst[2])
            b = read_reg(regs, inst[3])
            write_reg(regs, inst[1], ula(op, a, b))

        #Formato I (rd = rs1 op imediato)
        case 'ADDI' | 'SLTI' | 'SLTIU' | 'ORI' | 'ANDI' | 'SLLI' | 'SRLI' | 'SRAI':
            check_args(inst, 3)
            a = read_reg(regs, inst[2])
            imm = number(inst[3])
            if op == 'SLTIU': #SLTIU é o único em que o I não está no final
                op_r = 'SLTU'
            else: #op[:-1] remove o 'I' do final para chamar a ula corretamente
                op_r = op[:-1] 
            write_reg(regs, inst[1], ula(op_r, a, imm))

        #Loads (rd = memória[base + offset])
        case 'LB' | 'LH' | 'LW' | 'LBU' | 'LHU':
            sinal = op in ('LB', 'LH', 'LW')
            write_reg(regs, inst[1], read_mem(mem, get_addr(inst, regs), tam[op], sinal))

        #Stores (memória[base + offset] = rs2)
        case 'SB' | 'SH' | 'SW':
            write_mem(mem, get_addr(inst, regs), read_reg(regs, inst[1]), tam[op])

        #Desvios condicionais
        case 'BEQ' | 'BNE' | 'BLT' | 'BGE' | 'BLTU' | 'BGEU':
            check_args(inst, 3)
            a = read_reg(regs, inst[1])
            b = read_reg(regs, inst[2])
            if op in ('BLTU', 'BGEU'):
                a, b = u32(a), u32(b)
            tomado = {'BEQ': a == b, 'BNE': a != b, 'BLT': a < b, 'BGE': a >= b, 'BLTU': a < b, 'BGEU': a >= b}[op]
            if tomado:
                return get_label(rotulos, inst[3])

        #Pseudoinstruções
        case 'LI':
            check_args(inst, 2)
            write_reg(regs, inst[1], number(inst[2]))
        case 'LA':
            check_args(inst, 2)
            write_reg(regs, inst[1], get_label(rotulos, inst[2]))
        case 'MV':
            check_args(inst, 2)
            write_reg(regs, inst[1], read_reg(regs, inst[2]))
        case 'J':
            check_args(inst, 1)
            return get_label(rotulos, inst[1])
        case 'JR':
            check_args(inst, 1)
            return read_reg(regs, inst[1])

        case 'ECALL': #Chamadas de sistema, o serviço é escolhido por a7
            check_args(inst, 0)
            servico = read_reg(regs, 'a7')
            if servico == 1:
                print(read_reg(regs, 'a0'), end='')
            elif servico == 10:
                return "FIM"
            else:
                raise ValueError(f"ecall não suportado: a7 = {servico}")

        case _:
            raise ValueError(f"Instrução desconhecida ou inválida: {inst[0]}")
    return None

def emular(arquivo): #Monta as estruturas e roda o laço principal
    registradores = {f"x{i}": 0 for i in range(32)}
    rotulos, instrucoes, memoria = first_pass(read_archive(arquivo))

    if 'main' not in rotulos: raise ValueError("Rotulo main não encontrado")
    pc = rotulos['main']
    while True:
        if pc not in instrucoes: 
            raise ValueError(f"PC fora do programa: 0x{pc:08x}")
        novo_pc = executar(instrucoes[pc], registradores, memoria, rotulos)
        if novo_pc == "FIM": #Fim do programa
            break
        if novo_pc is None: #Segue para a próxima instrução, não ocorre desvio
            pc += 4
        else: #Pula para o endereço devolvido, ocorre desvio
            pc = novo_pc
    return registradores, memoria #Para facilitar a visualização dos resultados sem prints


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Uso: python emulador.py codigo.s')
    emular(sys.argv[1])