'''
CLASSE: Mutex

Representa um mutex.
Um mutex pode estar livre, quando não possui dono, ou ocupado, quando uma tarefa
detém o acesso ao recurso protegido.
'''

from dataclasses import dataclass, field

from TCB import TCB


@dataclass
class Mutex:
    id: int # número do mutex, exemplo ML01 usa mutex id 1
    dono: TCB | None = None # tarefa que atualmente possui o mutex
    fila_espera: list[TCB] = field(default_factory=list) # tarefas bloqueadas esperando esse mutex, em ordem FIFO