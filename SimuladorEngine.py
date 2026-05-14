import copy
from SimuladorConfig import SimuladorConfig
from SimuladorEstado import SimuladorEstado
from TCB import TCB
from Estados import EstadosTarefa, EstadosCPU
from CPU import CPU
from Escalonadores import fabrica_de_escalonadores, EscalonadorBase


class SimuladorEngine:
    config : SimuladorConfig # Configuração do sistema
    estado_atual: SimuladorEstado # Estado atual
    historico_estados: list[SimuladorEstado] # Lista para guardar todos os estados para retroceder no tempo
    escalonador: EscalonadorBase # Escalonador escolhido com base no config.txt
    quantumTotal: int #representa a quantidade quantum total do sistema

    def __init__(self, config: SimuladorConfig, estado_inicial: SimuladorEstado):
        self.config = config # Salva configuração
        self.estado_atual = estado_inicial # Salva o estado inicial
        self.historico_estados = [] # Inicia como lista vazia
        self.escalonador = fabrica_de_escalonadores(self.config.algoritmoEscalomento) # Seleciona escalonador
        self.quantumTotal = self.config.quantum # Salva o quantum total do sistema
        self.prepararSimulador() # Prepara o simulador, colocando as tarefas que entram no tempo 0 na fila de prontos e chamando o escalonador para definir quais tarefas vão para cada cpu
    
    def verificar_nascimento(self) -> None: # Método que percorre a lista de tarefas futuras e coloca na fila de prontos as que entram agora no sistema
        tarefas_futuras = []
        for tarefa_futura in self.estado_atual.tarefas_futuras:
            if tarefa_futura.tempoDeIngresso == self.estado_atual.relogio_global:
                tarefas_futuras.append(tarefa_futura)
        for tf in tarefas_futuras:
            self.estado_atual.ingressar_tarefa(tf)
        if len(tarefas_futuras) > 0:
            self.escalonar_novas_tarefas()
        
            
            

    def processar_cpus(self) -> None: # Método que verifica todas as tarefas da cpu, diminui o tempo delas e verifica se elas finalizaram
        for p in self.estado_atual.cpus:
            if p.atualTarefa is not None: 
                if p.atualTarefa.tempoCorrido <= 0: #o usuario pode ter editado a tarefa para ela terminal antes do tempo, nesse caso a tarefa deve ser finalizada imediatamente
                    self.estado_atual.finalizar_tarefa(p.atualTarefa, p)
                    self.escalonar_cpu(p)
            if p.atualTarefa is not None:
                p.atualTarefa.quatum_dado = p.atualTarefa.quatum_dado + 1
                if p.atualTarefa.tempoCorrido <= 0:
                    self.estado_atual.finalizar_tarefa(p.atualTarefa, p)
                    #print(f"Tarefa {p.atualTarefa.id} finalizou no tick {self.estado_atual.relogio_global}.") # Debug: tarefa finalizou
                    self.escalonar_cpu(p)
                else:
                    p.atualTarefa.tempoCorrido = p.atualTarefa.tempoCorrido - 1
                    if p.atualTarefa.tempoCorrido == 0:
                        #print(f"Tarefa {p.atualTarefa.id} finalizou no tick {self.estado_atual.relogio_global}.") # Debug: tarefa finalizou
                        self.estado_atual.finalizar_tarefa(p.atualTarefa, p)
                        self.escalonar_cpu(p)
                    elif p.atualTarefa.quatum_dado == self.quantumTotal:
                        #print(f"CPU {p.id} atingiu o quantum no tick {self.estado_atual.relogio_global}.") # Debug: quantum atingido
                        self.escalonar_cpu(p)
            else:
                p.estado = EstadosCPU.DESLIGADO

                   
    #Esse método é para escalonar as tarefas na cpu em específico
    #pois quando uma tarefa atinge o quantum ou finaliza, só aquela cpu precisa ser escalonada
    #e nenhuma outra cpu precisa ser escalonada, para evitar trocas de contexto desnecessárias
    def escalonar_cpu(self,p: CPU) -> None: # Método para definir quais tarefas vão rodar em cada cpu
        print(f"Escalonando CPU {p.id} no tick ({self.estado_atual.relogio_global},{self.estado_atual.relogio_global + 1}].") # Debug: escalonando 
        candidatos = copy.copy(self.estado_atual.fila_prontos) # copia a fila de prontos para a lista de candidados, para não modificar a original
        if p.atualTarefa is not None: #se aquela cpu já tem uma tarefa, ela também é candidata
            candidatos.append(p.atualTarefa)

        t_escolhida = self.escalonador.ordenar_candidatos(candidatos) #o escalonador seleciona a nova tarefa para aquela cpu, com base no algoritmo selecionado

        if t_escolhida is None: #se nenhuma tarefa foi escolhida, pela lista estar vazia ou a tarefa da cpu antiga ter tido a tarefa finalizada a cpu é desligada
            if p.atualTarefa is None:
                p.estado = EstadosCPU.DESLIGADO
            return

        #Se alguma tarefa for escolhida, começa o processo de escolonamento na cpu
        p.estado = EstadosCPU.LIGADO # a cpu é ligada para receber a tarefa escolhida

        # Se a mesma tarefa continua escolhida, só reseta quantum e mantém rodando
        if t_escolhida == p.atualTarefa:
            t_escolhida.quatum_dado = 0
            return

        # Se havia tarefa executando e ela perdeu a CPU, volta para prontos
        if p.atualTarefa is not None:
            p.atualTarefa.estado = EstadosTarefa.PRONTO
            p.atualTarefa.idCpu = -1
            p.atualTarefa.quatum_dado = 0
            self.estado_atual.fila_prontos.append(p.atualTarefa)

        # A tarefa escolhida sai de prontos (se estava lá) e entra na CPU, medida de segurança para evitar bugs
        if t_escolhida in self.estado_atual.fila_prontos:
            self.estado_atual.fila_prontos.remove(t_escolhida)
        
        #processo para configurar a cpu com a tarefa escolhida
        p.atualTarefa = t_escolhida #atribui a tarefa escolhida para a cpu
        p.atualTarefa.quatum_dado = 0 #reseta o quantum dado para a tarefa escolhida, pois ela está começando a rodar agora
        p.atualTarefa.estado = EstadosTarefa.EXECUTANDO #atualiza o estado da tarefa escolhida para executando
        p.atualTarefa.idCpu = p.id #atualiza a cpu associada a tarefa escolhida para a cpu atual

        
    #Esse método é um versão do escalonador para novas tarefas, pois quando cada tarefa nova chega nas CPU's, elas tem que ser comparadas com as tarefas
    #que estão rodando e com as que estão na fila, pois elas podem ter mais prioridade e as que estão nas CPU'S pode entrar ou sair da prioridade
    #por isso, precisamos achar as tarefas selecionadas e manter as que já estavam na CPU das selecinadas nas suas CPU'S
    #para não gerar troca de contexto desnecessária, e depois preencher as CPU's ociosas com as tarefas novas selecionadas
    def escalonar_novas_tarefas(self) -> None: # Método para definir quais tarefas vão rodar em cada cpu
        #print(f"Escalonando novas tarefas no tick {self.estado_atual.relogio_global}.") # Debug: escalonando novas tarefas
        candidatos = copy.copy(self.estado_atual.fila_prontos)
        for p in self.estado_atual.cpus:
            if p.atualTarefa is not None:
                #print(f"CPU {p.id} tem tarefa {p.atualTarefa.id} como candidata.") # Debug: tarefa candidata
                candidatos.append(p.atualTarefa)
        
        escolhidos : list[TCB] = []

        for i in range(len(self.estado_atual.cpus)):
            t_escolhida = self.escalonador.ordenar_candidatos(candidatos)
            if t_escolhida is not None:
                escolhidos.append(t_escolhida)
                candidatos.remove(t_escolhida)
        
        #print(f"Tarefas escolhidas para as CPUs: {[t.id for t in escolhidos]}.") # Debug: tarefas escolhidas

        # 1) Mantém as tarefas já executando que continuam escolhidas.
        # 2) Para CPUs que precisam trocar (ou estão ociosas), realoca e preenche com o que sobrar em `escolhidos`.

        for p in self.estado_atual.cpus:
            #print(f"Processando CPU {p.id} para realocação. Tarefa atual: {p.atualTarefa.id if p.atualTarefa else 'None'}.") # Debug: processando CPU
            if p.atualTarefa in escolhidos:
                #print(f"CPU {p.id} mantém tarefa {p.atualTarefa.id}.") # Debug: CPU mantém tarefa
                escolhidos.remove(p.atualTarefa)
                continue

            # Se havia tarefa executando e ela não foi escolhida, devolve pra fila de prontos
            if p.atualTarefa is not None:
                p.atualTarefa.estado = EstadosTarefa.PRONTO
                p.atualTarefa.idCpu = -1
                p.atualTarefa.quatum_dado = 0
                self.estado_atual.fila_prontos.append(p.atualTarefa)
                p.atualTarefa = None

            # Preenche CPU ociosa com a próxima escolhida (se existir)
            if len(escolhidos) > 0:
                t_escolhido = None # zera a variável para evitar bugs de referência

                for t in escolhidos:
                    if t.idCpu == -1:
                        #print(f"Tarefa {t.id} que não tinha a CPU escolhida para CPU {p.id}.") # Debug: tarefa escolhida para CPU
                        t_escolhido = t
                        break

                if t_escolhido is not None:
                    escolhidos.remove(t_escolhido)
                    # Remove da fila de prontos, se estiver lá (evita duplicação)
                    if t_escolhido in self.estado_atual.fila_prontos:
                        self.estado_atual.fila_prontos.remove(t_escolhido)
                    p.atualTarefa = t_escolhido
                    p.atualTarefa.estado = EstadosTarefa.EXECUTANDO
                    p.atualTarefa.idCpu = p.id
                    p.atualTarefa.quatum_dado = 0
                    p.estado = EstadosCPU.LIGADO
            else:
                p.estado = EstadosCPU.DESLIGADO
                print(f"CPU {p.id} ficou ociosa.") # Debug: CPU ficou ociosa


    def avancar_tick(self) -> None: # Método que controla o fluxo de avançar o tempo do sistema
        #self.historico_estados.append(self.estado_atual.clonar_estado())
        self.resetarMarcadorRandomico()
        self.processarTempoCPU()
        self.processar_cpus()
        self.estado_atual.relogio_global = self.estado_atual.relogio_global + 1
        # Aplica ingressos do novo tick (tarefa com tempoDeIngresso == relogio_global)
        self.verificar_nascimento()
        self.historico_estados.append(self.estado_atual.clonar_estado())

    def retroceder_tick(self) -> None: # Método que controla o fluxo de retroceder o tempo do sistema
        # `historico_estados` guarda snapshots (deepcopy) do estado.
        # Após um `avancar_tick()`, o snapshot do tick atual está no final da lista.
        # Para voltar 1 tick, descartamos o snapshot atual e restauramos o anterior.
        if len(self.historico_estados) <= 1:
            print("Não é possível retroceder!")
            return

        self.historico_estados.pop()  # descarta snapshot do tick atual
        self.estado_atual = self.historico_estados[-1].clonar_estado()  # restaura tick anterior

    def executar_tudo(self) -> None: # Executa a simulação inteira de uma vez
        while not self.estado_atual.simulacao_finalizada():
            self.avancar_tick()

    def prepararSimulador(self) -> None:
        tarefas_para_ingressar = []

        for t in self.estado_atual.tarefas_futuras:
            if t.tempoDeIngresso == 0:
                tarefas_para_ingressar.append(t)

        for t in tarefas_para_ingressar:
            self.estado_atual.ingressar_tarefa(t)

        # Escalona o estado inicial (tick 0) para preencher CPUs disponíveis
        if len(tarefas_para_ingressar) > 0 or len(self.estado_atual.fila_prontos) > 0:
            self.escalonar_novas_tarefas()
        
        # Processa o tempo das CPUs para contabilizar o tempo ativo desde o tick 0
        # Salvar estado inicial (t=0) no histórico para sincronização com interface
        self.historico_estados.append(self.estado_atual.clonar_estado())


    def resetarMarcadorRandomico(self) -> None:
        for p in self.estado_atual.cpus:
            if (p.atualTarefa is not None) and (p.atualTarefa.sofreu_sorteio == True):
                #print(f"Resetando marcador de sorteio da tarefa {p.atualTarefa.id} na CPU {p.id} no tick {self.estado_atual.relogio_global}.") # Debug: resetando marcador de sorteio
                p.atualTarefa.sofreu_sorteio = False

    def processarTempoCPU(self) -> None:
        if self.estado_atual.relogio_global > 0:
            self.estado_atual.relogio_de_processo = self.estado_atual.relogio_de_processo + 1
        for p in self.estado_atual.cpus:
            print(f"Estado da CPU {p.id} no tick {self.estado_atual.relogio_global}: {'LIGADA' if p.estado == EstadosCPU.LIGADO else 'DESLIGADA'}, Tarefa: {p.atualTarefa.id if p.atualTarefa else 'None'}.") # Debug: estado da CPU
            if p.estado == EstadosCPU.LIGADO:
                p.tempoAtivo = p.tempoAtivo + 1
            print(f"Porcentagem de utilização da CPU {p.id} no tick {self.estado_atual.relogio_global}: {(p.tempoAtivo /self.estado_atual.relogio_de_processo)*100}%") # Debug: porcentagem de utilização da CPU
            

