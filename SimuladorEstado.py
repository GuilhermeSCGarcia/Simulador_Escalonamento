from __future__ import annotations
import copy


from TCB import TCB
from CPU import CPU
from Estados import EstadosCPU
from Estados import EstadosTarefa

class SimuladorEstado:
    relogio_global: int = 0 # Relógio do sistema
    relogio_de_processo: int  = 1 
    cpus: list[CPU] # Lista de CPUs
    quantumTotal: int  #representa a quantidade quantum total do sistema
    fila_prontos: list[TCB] # Lista da fila da tarefas prontas para execução 
    fila_suspensas: list[TCB] # Lista da fila de tarefas suspensas
    tarefas_futuras: list[TCB] # Lista de tarefas futuras
    tarefas_finalizadas: list[TCB] # Lista de tarefas finalizadas

    def __init__(self, lista_cpus: list[CPU], lista_tarefas_carregadas: list[TCB],quantumTotal: int):
        self.relogio_global = 0 # Inicia relógio do sistema em zero
        # Usa deepcopy para desvincular da configuração original, desacoplamento
        self.cpus = copy.deepcopy(lista_cpus) # Recebe lista de cpus criada pelo SimuladorConfig
        self.tarefas_futuras = copy.deepcopy(lista_tarefas_carregadas) # Recebe lista de tarefas carregadas, que vão para a lista de futuras, criadas pelo Simulador Config
        self.fila_prontos = [] # Inicia fila de prontos vazia
        self.fila_suspensas = [] # Inicia fila de tarefas suspensas vazia
        self.tarefas_finalizadas = [] # Inicia fila de tarefas finalizadas vazia
        self.quantumTotal = quantumTotal #recebe o quantum total do sistema, criado pelo SimuladorConfig

    def simulacao_finalizada(self) -> bool: # Método que retorna se a simulacao está finalizada
        if self.tarefas_futuras: # Verifiica se ainda existem tarefas futuras
            return False
        
        if self.fila_prontos: # Verifica se ainda existem tarefas na fila de prontos
            return False

        for cpu in self.cpus:
            if cpu.atualTarefa is not None:
                return False # Se existe alguma cpu com tarefa a simução ainda não acabou
        
        for tarefa in self.fila_suspensas:
            if tarefa.estado == EstadosTarefa.BLOQUEADO:
                return False # Se existe alguma tarefa suspensa, a simulação ainda não acabou
            
        return True

    def obter_cpus_livres(self) -> list[CPU]: # Método que retorna as cpus livres do sistema
        cpus_livres: list[CPU] = []
        for cpu in self.cpus:
            if cpu.estado == EstadosCPU.LIGADO and cpu.atualTarefa == None:  # Verifica quais cpus estão ligadas e não tem nenhuma tarefa atribuida a elas
                cpus_livres.append(cpu)

        return cpus_livres

    def ingressar_tarefa(self, tarefa: TCB) -> None: # Método que remove tarefa da fila de futuras, coloca na fila de prontos e seta o estado da tarefa como pronto
        self.tarefas_futuras.remove(tarefa)
        self.fila_prontos.append(tarefa)
        tarefa.estado = EstadosTarefa.PRONTO

    def finalizar_tarefa(self, tarefa: TCB, cpu: CPU) -> None: # Método que libera cpu e seta tarefa como finalizada
        cpu.atualTarefa = None
        tarefa.quatum_dado = 0
        self.tarefas_finalizadas.append(tarefa)
        tarefa.estado = EstadosTarefa.FINALIZADO

    def clonar_estado(self) -> SimuladorEstado: # Método que retorna uma cópia profunda desse estado, ajuuda no histórico
        return copy.deepcopy(self)

    def suspender_tarefa(self, tarefa: TCB) -> None: # Método para suspender uma tarefa manualmente, mantendo sincronização com engine
        # Remove da fila de prontos, se estiver
        print("Suspendendo tarefa T{} na cpu{}...".format(tarefa.id,tarefa.idCpu))
        if tarefa in self.fila_prontos:
            self.fila_prontos.remove(tarefa)
        
        # Remove de qualquer CPU que esteja executando
        for cpu in self.cpus:
            if cpu.atualTarefa == tarefa:
                cpu.atualTarefa = None
        
        
        # Coloca na fila de suspensas e atualiza estado
        if tarefa not in self.fila_suspensas:
            self.fila_suspensas.append(tarefa)
        tarefa.idCpu = -1
        tarefa.estado = EstadosTarefa.BLOQUEADO
        print("informações da tarefa T{}: estado {}, cpu associada {}".format(tarefa.id, tarefa.estado.name, tarefa.idCpu))

    def acordar_tarefa(self, tarefa: TCB) -> None: # Método para acordar uma tarefa suspensa, colocando-a de volta na fila de prontos
        # Remove da fila de suspensas
        if tarefa in self.fila_suspensas:
            self.fila_suspensas.remove(tarefa)
        
        # Coloca na fila de prontos e atualiza estado
        if tarefa not in self.fila_prontos:
            self.fila_prontos.append(tarefa)
        tarefa.estado = EstadosTarefa.PRONTO