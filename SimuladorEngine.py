import random

from SimuladorConfig import SimuladorConfig
from SimuladorEstado import SimuladorEstado
from TCB import TCB
from Estados import EstadosTarefa
from CPU import CPU

class SimuladorEngine:
    config : SimuladorConfig # Configuração do sistema
    estado_atual: SimuladorEstado # Estado atual
    historico_estados: list[SimuladorEstado] # Lista para guardar todos os estados para retroceder no tempo

    def __init__(self, config: SimuladorConfig, estado_inicial: SimuladorEstado):
        self.config = config # Salva configuração
        self.estado_atual = estado_inicial # Salva o estado inicial
        self.historico_estados = [] # Inicia como lista vazia
    
    def verificar_nascimento(self) -> None: # Método que percorre a lista de tarefas futuras e coloca na fila de prontos as que entram agora no sistema
        for tarefa_futura in self.estado_atual.tarefas_futuras.copy(): # O copy serve para evitar problemas com o remove() dentro do método ingressar_tarefa
            if tarefa_futura.tempoDeIngresso == self.estado_atual.relogio_global:
                self.estado_atual.ingressar_tarefa(tarefa_futura)

    def processar_cpus(self) -> None: # Método que verifica todas as tarefas da cpu, diminui o tempo delas e verifica se elas finalizaram
        for cpu in self.estado_atual.cpus:
            if cpu.atualTarefa is not None:
                cpu.atualTarefa.tempoCorrido = cpu.atualTarefa.tempoCorrido - 1

                if cpu.atualTarefa.tempoCorrido == 0: # Verifica se a tarefa finalizou
                    self.estado_atual.finalizar_tarefa(cpu.atualTarefa, cpu)
 
    def chamar_escalonador(self) -> None: # Método para definir quais tarefas vão rodar em cada cpu
        candidatos: list[TCB] = []

        for tarefa_pronta in self.estado_atual.fila_prontos: # Pega todas as tarefas da filas de pronto
            tarefa_pronta.estavaRodando = False # Atributo temporário para desempate
            candidatos.append(tarefa_pronta)
        
        for cpu in self.estado_atual.cpus: # Pega todas as tarefas rodando em cada cpu
            if cpu.atualTarefa is not None:
                cpu.atualTarefa.estavaRodando = True # Atributo temporário para desempate
                candidatos.append(cpu.atualTarefa)
                cpu.atualTarefa = None

        if not candidatos: # Se não houver nenhum candido só retornar
            return
        
        if self.config.algoritmoEscalomento == "SRTF": # Ordena a lita de candidados conforme parâmetros de desampate do algoritmo SRTF
            candidatos.sort(key=lambda t: (
                t.tempoCorrido,
                not t.estavaRodando,
                t.tempoDeIngresso,
                t.tempoTotal,
                random.random()
            ))

        elif self.config.algoritmoEscalomento == "PRIOP": # Ordena a lita de candidados conforme parâmetros de desampate do algoritmo PRIOP
            candidatos.sort(key=lambda t: (
                -t.prioridadeEstatica,
                not t.estavaRodando,
                t.tempoDeIngresso,
                t.tempoTotal,
                random.random()
            ))

        self.estado_atual.fila_prontos.clear()

        for candidato in candidatos:
            cpu_livre: CPU = next((c for c in self.estado_atual.cpus if c.atualTarefa is None), None) # Procura primeira CPU livre

            if cpu_livre is not None:
                # A tarefa do topo da lista de candidatos foi selecionada para essa cpu
                cpu_livre.atualTarefa = candidato
                candidato.estado = EstadosTarefa.EXECUTANDO
            else:
                # Não tem mais vaga, o candidato volta para a fila de prontos
                self.estado_atual.fila_prontos.append(candidato)
                candidato.estado = EstadosTarefa.PRONTO

    def avancar_tick(self) -> None: # Método que controla o fluxo de avançar o tempo do sistema
        self.historico_estados.append(self.estado_atual.clonar_estado())
        self.verificar_nascimento()
        self.processar_cpus()
        self.chamar_escalonador()
        self.estado_atual.relogio_global = self.estado_atual.relogio_global + 1

    def retroceder_tick(self) -> None: # Método que controla o fluxo de retroceder o tempo do sistema
        if len(self.historico_estados) > 0:
            self.estado_atual = self.historico_estados.pop()
        else:
            print("Não é possível retroceder!")

    def executar_tudo(self) -> None: # Executa a simulação inteira de uma vez
        while not self.estado_atual.simulacao_finalizada():
            self.avancar_tick()