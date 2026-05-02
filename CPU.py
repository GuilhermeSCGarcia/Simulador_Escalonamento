from Estados import EstadosCPU
import TCB
from dataclasses import dataclass, field


@dataclass
class CPU:
    id: int = -1 #número do processador
    estado: EstadosCPU = EstadosCPU.DESLIGADO #controle de ativado ou não
    atualTarefa : TCB = None # qual tarefa está associado aquele processesador
    historico: list[tuple[int,int,EstadosCPU]] = field(default_factory=list) #histórico de tempo que a cpu ficou ligada



