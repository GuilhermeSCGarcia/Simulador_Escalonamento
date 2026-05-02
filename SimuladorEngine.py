from SimuladorConfig import SimuladorConfig
from SimuladorEstado import SimuladorEstado

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
                cpu.atualTarefa.tempCorrido = cpu.atualTarefa.tempCorrido - 1

                if cpu.atualTarefa.tempCorrido == 0: # Verifica se a tarefa finalizou
                    self.estado_atual.finalizar_tarefa(cpu.atualTarefa, cpu)

    def chamar_escalonador(self) -> None:
        # To Do
        print("Teste")

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