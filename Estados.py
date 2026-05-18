'''
ENUMERAÇÕES: EstadosTarefa e EstadosCPU

Centraliza as constantes de estado do sistema, espelhando o ciclo de vida real de 
processos e processadores em um Sistema Operacional.
'''

from enum import Enum

class EstadosTarefa(Enum):
    NOVO = 0 #Tarefa criada
    PRONTO = 1 #Tarefa pronta na fila de execução
    EXECUTANDO = 2 #Tarefa executando
    BLOQUEADO = 3  #Tarefa bloqueada
    FINALIZADO = 4 #Tarefa finalizada
    
class EstadosCPU(Enum):
    DESLIGADO = 0 # CPU desligada
    LIGADO = 1 # CPU ligada