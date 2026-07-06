'''
CLASSE: TCB 

É a estrutura de dados que representa um modelo das tarefas no sistema operacional.] O motor do simulador e os escalonadores consultam 
essas informações a cada tick para tomar decisões de troca de contexto e atualizar o gráfico.
'''

from Estados import EstadosTarefa
from dataclasses import dataclass, field

@dataclass(frozen=True)
class EventoTarefa:
    tipo: str        # ML(Solicitação) ou MU(Liberação)
    tempo: int       # tempo relativo a execução da tarefa
    ordem: int       # posição no arquivo
    duracao: int | None = None # Duração do E/S
    mutex_id: int | None = None # id do mutex

@dataclass
class TCB:
    tempoDeIngresso: int #tempo de tick de chegada da tarefa
    tempoTotal: int #tempo total da tarefa
    tempoCorrido: int #tempo restante até a tarefa terminar
    prioridadeEstatica: int #prioridade estática positiva
    
    id: int = -1 #id da tarefa
    cor: str = "FFFFFF" #pode alterar por causa do matplotlip
    estado: EstadosTarefa = EstadosTarefa.NOVO  #guardar o estado da tarefa, incia como novo, que é quando ela entrou no sistema 
    idCpu: int = -1 #cpu associada com o processo
    listaEvento : list[EventoTarefa] = field(default_factory=list) # guarda uma lista de evento para Mutex e E/S
    estavaRodando: bool = False # Atributo para desempate no escalonamento
    sofreu_sorteio: bool = False # Atributo para determinar se a tarefa foi escolhida com base no sorteio
    quatum_dado: int = 0
    tempoEspera: int = 0 # Tempo que a tarefa passou na fila de prontos
    eventosExecutados: set[int] = field(default_factory=set) # Para não ficar executando o mutex
    motivoBloqueio: str = "" # Mutex ou IO
    idMutexAtual: int | None = None # Id do mutex que bloqueou a tarefa
    ioTempoTermina: int | None = None # Tick global em que a operação de E/S termina e gera IRQ