from Estados import EstadosTarefa
from dataclasses import dataclass, field


@dataclass
class TCB:
    
    temp_chegada: int #tempo de tick de chegada da tarefa
    temp_total: int #tempo total da tarefa
    temp_corrido: int #tempo restante até a tarefa terminar
    prioridade_estatica: int #prioridade estática positiva
    
    id: int = -1 #id da tarefa
    cor: str = "FFFFFF" #pode alterar por causa do matplotlip
    estado: EstadosTarefa = EstadosTarefa.NOVO  #guardar o estado da tarefa?
    id_cpu: int = -1 #cpu associada com o processo
    listaEvento : list[int] = field(default_factory=list) #guarda uma lista de evento para o projeto B
    historico: list[tuple[int,int,EstadosTarefa]] = field(default_factory=list) # guarda o histórico de tempo e o estado da tarefa(inicio,fim,qual_estado)
    


    
    




    