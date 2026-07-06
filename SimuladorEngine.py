'''
Classe: SimuladorEngine

Este é o "Motor" principal do Sistema Operacional simulado.
Sua responsabilidade é orquestrar o tempo (Ticks), movimentar as tarefas entre as filas 
(Futuras, Prontos, Executando, Finalizadas), calcular o uso de CPU, gerenciar o limite 
de tempo (Quantum) e acionar o Escalonador para decidir quem usa o processador.
Também mantém um histórico de estados para permitir retroceder o tick.
'''

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
    estado_zero: SimuladorEstado # Estado zero para restaurar depois
    historico_estados: list[SimuladorEstado] # Lista para guardar todos os estados para retroceder no tempo
    escalonador: EscalonadorBase # Escalonador escolhido com base no config.txt
    quantumTotal: int #representa a quantidade quantum total do sistema

    def __init__(self, config: SimuladorConfig, estado_inicial: SimuladorEstado):
        self.config = config # Salva configuração
        self.estado_atual = estado_inicial # Salva o estado inicial
        self.estado_zero = None # Salva o estado zero para poder restaurar depois
        self.historico_estados = [] # Inicia como lista vaziaF
        self.escalonador = fabrica_de_escalonadores(self.config.algoritmoEscalomento, self.config.alpha) # Seleciona escalonador
        self.quantumTotal = self.config.quantum # Salva o quantum total do sistema
        self.prepararSimulador() # Prepara o simulador, colocando as tarefas que entram no tempo 0 na fila de prontos e chamando o escalonador para definir quais tarefas vão para cada cpu
    
    # Método que percorre a lista de tarefas futuras e coloca na fila de prontos as que entram agora no sistema
    def verificar_nascimento(self, escalonar: bool = True) -> bool: 
        tarefas_futuras = []

        for tarefa_futura in self.estado_atual.tarefas_futuras:
            if tarefa_futura.tempoDeIngresso == self.estado_atual.relogio_global:
                tarefas_futuras.append(tarefa_futura)

        ingressou_alguma_tarefa = False

        for tf in tarefas_futuras:
            if not (tf.estado == EstadosTarefa.BLOQUEADO):
                self.estado_atual.ingressar_tarefa(tf)
                ingressou_alguma_tarefa = True
            else:
                self.estado_atual.tarefas_futuras.remove(tf)
                continue

        if ingressou_alguma_tarefa and escalonar:
            self.escalonar_novas_tarefas()

        return ingressou_alguma_tarefa
    
    def validar_mutexes_antes_finalizar(self, tarefa: TCB) -> None:
        mutexes_possuidos = []

        for mutex in self.estado_atual.mutexes.values():
            if mutex.dono == tarefa:
                mutexes_possuidos.append(mutex.id)

        if len(mutexes_possuidos) > 0:
            ids_mutex = ", ".join([str(id_mutex) for id_mutex in mutexes_possuidos])

            raise ValueError(
                f"Tarefa T{tarefa.id} finalizou enquanto ainda era dona do(s) mutex(es): {ids_mutex}. "
                "Adicione o evento MU correspondente antes do término da tarefa."
            )

    def finalizar_tarefa_segura(self, tarefa: TCB, cpu: CPU) -> None:
        self.validar_mutexes_antes_finalizar(tarefa)
        self.estado_atual.finalizar_tarefa(tarefa, cpu)

    # Método que verifica todas as tarefas da cpu, diminui o tempo delas e verifica se elas finalizaram
    def processar_cpus(self) -> None:
        for p in self.estado_atual.cpus:
            if p.atualTarefa is not None: 
                if p.atualTarefa.tempoCorrido <= 0: #o usuario pode ter editado a tarefa para ela terminal antes do tempo, nesse caso a tarefa deve ser finalizada imediatamente
                    self.finalizar_tarefa_segura(p.atualTarefa, p)
                    self.escalonar_cpu(p)
            if p.atualTarefa is not None:
                bloqueou = self.processar_eventos_tarefa(p, p.atualTarefa)

                if bloqueou and p.atualTarefa is None:
                    continue

                if p.atualTarefa is None:
                    continue

                p.atualTarefa.quatum_dado = p.atualTarefa.quatum_dado + 1
                if p.atualTarefa.tempoCorrido <= 0:
                    self.finalizar_tarefa_segura(p.atualTarefa, p)
                    self.escalonar_cpu(p)
                else:
                    self.registrar_execucao_cpu(p, p.atualTarefa)
                    p.atualTarefa.tempoCorrido = p.atualTarefa.tempoCorrido - 1

                    if p.atualTarefa.tempoCorrido == 0:
                        tarefa_finalizando = p.atualTarefa

                        bloqueou_no_final = self.processar_eventos_tarefa(
                            p,
                            tarefa_finalizando,
                            reescalonar_ao_acordar=False
                        )

                        if bloqueou_no_final:
                            continue

                        self.finalizar_tarefa_segura(tarefa_finalizando, p)
                        self.escalonar_cpu(p, processar_eventos_ao_entrar=False)

                    elif p.atualTarefa.quatum_dado == self.quantumTotal:
                        self.escalonar_cpu(p, processar_eventos_ao_entrar=False)
            else:
                if(len(self.estado_atual.fila_prontos) > 0 ):
                    self.escalonar_cpu(p)
                else:
                    p.estado = EstadosCPU.DESLIGADO

                   
    #Esse método é para escalonar as tarefas na cpu em específico
    #pois quando uma tarefa atinge o quantum ou finaliza, só aquela cpu precisa ser escalonada
    #e nenhuma outra cpu precisa ser escalonada, para evitar trocas de contexto desnecessárias
    def escalonar_cpu(self,p: CPU, processar_eventos_ao_entrar: bool = True) -> None: # Método para definir quais tarefas vão rodar em cada cpu
        candidatos = copy.copy(self.estado_atual.fila_prontos) # copia a fila de prontos para a lista de candidados, para não modificar a original
        if p.atualTarefa is not None: #se aquela cpu já tem uma tarefa, ela também é candidata
            candidatos.append(p.atualTarefa)

        # Adiciona o atributo como true para a tarefa que estava no cpu
        for tarefa in candidatos:
            tarefa.estavaRodando = tarefa == p.atualTarefa

        t_escolhida = self.escalonador.ordenar_candidatos(candidatos) #o escalonador seleciona a nova tarefa para aquela cpu, com base no algoritmo selecionado

        if t_escolhida is None: #se nenhuma tarefa foi escolhida, pela lista estar vazia ou a tarefa da cpu antiga ter tido a tarefa finalizada a cpu é desligada
            if p.atualTarefa is None:
                p.estado = EstadosCPU.DESLIGADO
            return

        # Se alguma tarefa for escolhida, começa o processo de escolonamento na cpu
        p.estado = EstadosCPU.LIGADO # a cpu é ligada para receber a tarefa escolhida

        # Se a mesma tarefa continua escolhida, só reseta quantum e mantém rodando
        if t_escolhida == p.atualTarefa:
            t_escolhida.quatum_dado = 0
            t_escolhida.tempoEspera = 0
            if processar_eventos_ao_entrar:
                self.processar_eventos_tarefa(p, t_escolhida)
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
        p.atualTarefa.tempoEspera = 0 #reseta o tempo de espera se a tarefa escolhida entrar na cpu
        p.atualTarefa.estado = EstadosTarefa.EXECUTANDO #atualiza o estado da tarefa escolhida para executando
        p.atualTarefa.idCpu = p.id #atualiza a cpu associada a tarefa escolhida para a cpu atual
        if processar_eventos_ao_entrar:
            self.processar_eventos_tarefa(p, p.atualTarefa)

        
    #Esse método é um versão do escalonador para novas tarefas, pois quando cada tarefa nova chega nas CPU's, elas tem que ser comparadas com as tarefas
    #que estão rodando e com as que estão na fila, pois elas podem ter mais prioridade e as que estão nas CPU'S pode entrar ou sair da prioridade
    #por isso, precisamos achar as tarefas selecionadas e manter as que já estavam na CPU das selecinadas nas suas CPU'S
    #para não gerar troca de contexto desnecessária, e depois preencher as CPU's ociosas com as tarefas novas selecionadas
    def escalonar_novas_tarefas(self) -> None: # Método para definir quais tarefas vão rodar em cada cpu
        candidatos = copy.copy(self.estado_atual.fila_prontos)
        for p in self.estado_atual.cpus:
            if p.atualTarefa is not None:
                candidatos.append(p.atualTarefa)

        # Verifica se a tarefa já estava executando na cpu
        for tarefa in candidatos:
            tarefa.estavaRodando = tarefa.idCpu != -1

        escolhidos : list[TCB] = []

        for i in range(len(self.estado_atual.cpus)):
            t_escolhida = self.escalonador.ordenar_candidatos(candidatos)
            if t_escolhida is not None:
                escolhidos.append(t_escolhida)
                candidatos.remove(t_escolhida)


        # 1) Mantém as tarefas já executando que continuam escolhidas.
        # 2) Para CPUs que precisam trocar (ou estão ociosas), realoca e preenche com o que sobrar em `escolhidos`.

        for p in self.estado_atual.cpus:
            if p.atualTarefa in escolhidos:
                p.atualTarefa.tempoEspera = 0
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
                    p.atualTarefa.tempoEspera = 0
                    p.estado = EstadosCPU.LIGADO
            else:
                p.estado = EstadosCPU.DESLIGADO

        self.processar_eventos_cpus_ativas()


    # Método que controla o fluxo de avançar o tempo do sistema
    def avancar_tick(self) -> None: 
        self.resetarMarcadorRandomico()
        self.atualizar_tempo_espera()
        self.processarTempoCPU()
        self.processar_cpus()
        self.estado_atual.relogio_global = self.estado_atual.relogio_global + 1
        acordou_por_io = self.processar_irqs_io()
        # Aplica ingressos do novo tick (tarefa com tempoDeIngresso == relogio_global)
        ingressou_tarefa = self.verificar_nascimento(escalonar=False)
        if acordou_por_io or ingressou_tarefa:
            self.escalonar_novas_tarefas()
        self.historico_estados.append(self.estado_atual.clonar_estado())

    # Método que controla o fluxo de retroceder o tempo do sistema
    def retroceder_tick(self) -> None:
        # `historico_estados` guarda snapshots (deepcopy) do estado.
        # Após um `avancar_tick()`, o snapshot do tick atual está no final da lista.
        # Para voltar 1 tick, descartamos o snapshot atual e restauramos o anterior.
        if len(self.historico_estados) <= 1:
            print("Não é possível retroceder!")
            return

        self.historico_estados.pop()  # descarta snapshot do tick atual
        self.estado_atual = self.historico_estados[-1].clonar_estado()  # restaura tick anterior

    # Executa a simulação inteira de uma vez
    def executar_tudo(self) -> None: 
        while not self.estado_atual.simulacao_finalizada():
            self.avancar_tick()

    # Método que Organiza os dados e cria o Tick 0 para começar a simulação
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
        self.estado_zero = self.estado_atual.clonar_estado() # Salva o estado zero para poder restaurar depois
        self.historico_estados.append(self.estado_atual.clonar_estado())

    # Método que foca em limpar as flags da interface gráfica
    def resetarMarcadorRandomico(self) -> None:
        for p in self.estado_atual.cpus:
            if (p.atualTarefa is not None) and (p.atualTarefa.sofreu_sorteio == True):
                p.atualTarefa.sofreu_sorteio = False

    # Método quue controla as Estatísticas Físicas da CPU
    def processarTempoCPU(self) -> None:
        if self.estado_atual.relogio_global > 0:
            self.estado_atual.relogio_de_processo = self.estado_atual.relogio_de_processo + 1
        for p in self.estado_atual.cpus:
            if p.estado == EstadosCPU.LIGADO:
                p.tempoAtivo = p.tempoAtivo + 1

    # Método que Restaura o estado inicial do Tick 0
    def restaurarEstadoZero(self) -> None:
        if self.estado_zero is None:
            return
        self.estado_atual = self.estado_zero.clonar_estado()
        self.historico_estados = [self.estado_atual.clonar_estado()] #Restaura o estado zero diretamente da engine, para garantir que tudo volte ao início corretamente

    def atualizar_tempo_espera(self) -> None:
        for tarefa in self.estado_atual.fila_prontos:
            tarefa.tempoEspera += 1

        for cpu in self.estado_atual.cpus:
            if cpu.atualTarefa is not None:
                cpu.atualTarefa.tempoEspera = 0

    def tempo_executado_tarefa(self, tarefa: TCB) -> int:
        return tarefa.tempoTotal - tarefa.tempoCorrido
    
    def processar_eventos_tarefa(self, cpu: CPU, tarefa: TCB, reescalonar_ao_acordar: bool = True) -> bool:
        tempo_executado = self.tempo_executado_tarefa(tarefa)

        eventos_do_tick = []

        for evento in tarefa.listaEvento:
            if evento.tempo == tempo_executado and evento.ordem not in tarefa.eventosExecutados:
                eventos_do_tick.append(evento)

        eventos_do_tick.sort(key=lambda evento: evento.ordem)

        precisa_reescalonar_global = False

        for evento in eventos_do_tick:
            if evento.tipo == "ML":
                bloqueou = self.executar_lock_mutex(cpu, tarefa, evento)

                if bloqueou:
                    if precisa_reescalonar_global and reescalonar_ao_acordar:
                        self.escalonar_novas_tarefas()
                    return True

            elif evento.tipo == "MU":
                acordou_tarefa = self.executar_unlock_mutex(tarefa, evento)

                if acordou_tarefa:
                    precisa_reescalonar_global = True

            elif evento.tipo == "IO":
                bloqueou = self.executar_io(cpu, tarefa, evento)

                if bloqueou:
                    if precisa_reescalonar_global and reescalonar_ao_acordar:
                        self.escalonar_novas_tarefas()
                    return True

        if precisa_reescalonar_global and reescalonar_ao_acordar:
            self.escalonar_novas_tarefas()

        return False

    def registrar_execucao_cpu(self, cpu: CPU, tarefa: TCB) -> None:
        if not hasattr(self.estado_atual, "execucoes_gantt"):
            self.estado_atual.execucoes_gantt = []

        self.estado_atual.execucoes_gantt.append({
            "tick": self.estado_atual.relogio_global,
            "cpu_id": cpu.id,
            "tarefa_id": tarefa.id,
            "sofreu_sorteio": tarefa.sofreu_sorteio,
        })
    
    def executar_lock_mutex(self, cpu: CPU, tarefa: TCB, evento) -> bool:
        mutex = self.estado_atual.mutexes[evento.mutex_id]

        tarefa.eventosExecutados.add(evento.ordem)

        if mutex.dono == tarefa:
            raise ValueError(
                f"Tarefa T{tarefa.id} tentou travar novamente o mutex {evento.mutex_id}, "
                "mas ela já é a dona desse mutex."
            )

        if mutex.dono is None:
            mutex.dono = tarefa
            self.registrar_evento_mutex(tarefa, evento, bloqueou=False)
            return False

        if all(t.id != tarefa.id for t in mutex.fila_espera):
            mutex.fila_espera.append(tarefa)

        tarefa.motivoBloqueio = "MUTEX"
        tarefa.mutexBloqueado = evento.mutex_id

        self.estado_atual.suspender_tarefa(tarefa)
        self.registrar_evento_mutex(tarefa, evento, bloqueou=True)
        self.escalonar_cpu(cpu)

        return True
    
    def executar_unlock_mutex(self, tarefa: TCB, evento) -> bool:
        mutex = self.estado_atual.mutexes[evento.mutex_id]

        tarefa.eventosExecutados.add(evento.ordem)

        if mutex.dono != tarefa:
            raise ValueError(
                f"Tarefa T{tarefa.id} tentou liberar o mutex {evento.mutex_id}, "
                "mas ela não é a dona desse mutex."
            )

        if len(mutex.fila_espera) == 0:
            mutex.dono = None
            self.registrar_evento_mutex(tarefa, evento, acordou=False)
            return False

        proxima_tarefa = mutex.fila_espera.pop(0)

        mutex.dono = proxima_tarefa

        proxima_tarefa.motivoBloqueio = ""
        proxima_tarefa.mutexBloqueado = None

        self.estado_atual.acordar_tarefa(proxima_tarefa)
        self.registrar_evento_mutex(
            tarefa,
            evento,
            acordou=True,
            tarefa_acordada_id=proxima_tarefa.id
        )

        return True

    def processar_eventos_cpus_ativas(self) -> None:
        cpus_com_tarefas = []

        for cpu in self.estado_atual.cpus:
            if cpu.atualTarefa is not None:
                cpus_com_tarefas.append((cpu, cpu.atualTarefa))

        for cpu, tarefa in cpus_com_tarefas:
            if cpu.atualTarefa == tarefa:
                self.processar_eventos_tarefa(cpu, tarefa)

    def registrar_evento_mutex(self, tarefa: TCB, evento, bloqueou=False, acordou=False, tarefa_acordada_id=None) -> None:
        if not hasattr(self.estado_atual, "eventos_gantt"):
            self.estado_atual.eventos_gantt = []

        evento_gantt = {
            "tick": self.estado_atual.relogio_global,
            "tarefa_id": tarefa.id,
            "tipo": evento.tipo,
            "mutex_id": evento.mutex_id,
            "bloqueou": bloqueou,
            "acordou": acordou,
        }

        if tarefa_acordada_id is not None:
            evento_gantt["tarefa_acordada_id"] = tarefa_acordada_id

        self.estado_atual.eventos_gantt.append(evento_gantt)

    def registrar_evento_io(self, tarefa: TCB, evento) -> None:
        if not hasattr(self.estado_atual, "eventos_gantt"):
            self.estado_atual.eventos_gantt = []

        self.estado_atual.eventos_gantt.append({
            "tick": self.estado_atual.relogio_global,
            "tarefa_id": tarefa.id,
            "tipo": "IO",
            "duracao": evento.duracao,
        })

    def registrar_evento_irq(self, tarefa: TCB) -> None:
        if not hasattr(self.estado_atual, "eventos_gantt"):
            self.estado_atual.eventos_gantt = []

        self.estado_atual.eventos_gantt.append({
            "tick": self.estado_atual.relogio_global,
            "tarefa_id": tarefa.id,
            "tipo": "IRQ",
        })

    def executar_io(self, cpu: CPU, tarefa: TCB, evento) -> bool:
        tarefa.eventosExecutados.add(evento.ordem)

        if evento.duracao is None or evento.duracao < 1:
            raise ValueError(
                f"Tarefa T{tarefa.id} possui evento de E/S inválido. "
                "A duração da operação de E/S deve ser maior ou igual a 1."
            )

        tarefa.motivoBloqueio = "IO"
        tarefa.mutexBloqueado = None
        tarefa.ioTempoTermina = self.estado_atual.relogio_global + evento.duracao

        self.registrar_evento_io(tarefa, evento)

        self.estado_atual.suspender_tarefa(tarefa)

        self.escalonar_cpu(cpu)

        return True
    
    def processar_irqs_io(self) -> bool:
        acordou_alguma_tarefa = False

        for tarefa in list(self.estado_atual.fila_suspensas):
            if tarefa.motivoBloqueio != "IO":
                continue

            if tarefa.ioTempoTermina is None:
                continue

            if self.estado_atual.relogio_global >= tarefa.ioTempoTermina:
                tarefa.motivoBloqueio = ""
                tarefa.ioTempoTermina = None

                self.estado_atual.acordar_tarefa(tarefa)
                self.registrar_evento_irq(tarefa)

                acordou_alguma_tarefa = True

        return acordou_alguma_tarefa
