from Estados import EstadosCPU
import TCB
from dataclasses import dataclass, field


@dataclass
class CPU:
    id: int #número do processador
    estado: EstadosCPU #controle de ativado ou não
    atualTarefa : TCB # qual tarefa está associado aquele processesador
    historico: list[tuple[int,int,EstadosCPU]] = field(default_factory=list) #histórico de tempo que a cpu ficou ligada



