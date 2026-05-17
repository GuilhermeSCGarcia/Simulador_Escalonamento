from Estados import EstadosCPU
from TCB import TCB
from dataclasses import dataclass, field

@dataclass
class CPU:
    id: int = -1 #número do processador
    estado: EstadosCPU = EstadosCPU.DESLIGADO #controle de ativado ou não
    atualTarefa : TCB = None # qual tarefa está associado aquele processesador
    tempoAtivo: int = 0 #tempo que a cpu ficou ativa
