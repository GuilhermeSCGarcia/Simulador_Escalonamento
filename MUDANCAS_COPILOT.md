# Mudanças feitas com Copilot (GPT-5.2)

Data: 2026-05-09

Este arquivo existe para você estudar depois **o que foi alterado**, **por quê**, e ter um **patch completo** das mudanças.

## Como validar rapidamente

- Rodar testes: `./.venv/bin/python -m unittest -q`
- Rodar interface: `./.venv/bin/python main.py`

## Convenções importantes que ficaram valendo

- **Snapshot do tick T** (`estado.relogio_global == T`) representa o **começo do tick T**.
- A execução do intervalo $[T, T+1)$ é o que está escalonado no snapshot do tick T.
- O Gantt foi ajustado para desenhar **intervalos executados** (transições entre snapshots), evitando “1 tick executado” no carregamento.
- O marcador `v` no Gantt representa **início real** (primeiro tick em que a tarefa executa em alguma CPU).

## Arquivos alterados / novos (git status)

Modificados:
- CPU.py
- CarregarConfig.py
- Escalonadores.py
- Interface.py
- SimuladorConfig.py
- SimuladorEngine.py
- SimuladorEstado.py
- TCB.py
- config2.txt

Novos (untracked):
- pseudobod.txt
- tests/

## Patch completo (git diff)

```diff
diff --git a/CPU.py b/CPU.py
index 5646fde..e266bb8 100644
--- a/CPU.py
+++ b/CPU.py
@@ -7,4 +7,5 @@ class CPU:
     id: int = -1 #número do processador
     estado: EstadosCPU = EstadosCPU.DESLIGADO #controle de ativado ou não
     atualTarefa : TCB = None # qual tarefa está associado aquele processesador
+    quantumProprio: int = 0 #quantum do prórpio processador
     historico: list[tuple[int,int,EstadosCPU]] = field(default_factory=list) #histórico de tempo que a cpu ficou ligada
diff --git a/CarregarConfig.py b/CarregarConfig.py
index 95072d6..bd1888e 100644
--- a/CarregarConfig.py
+++ b/CarregarConfig.py
@@ -56,6 +56,11 @@ class CarregarConfig:
                     )
                     self.listTarefas.append(tarefa)
         self.checarParametros(self.listTarefas) #chama a função para checar os parametros das tarefas e preencher os vazios
+        # Fecha o arquivo após o parse para evitar vazamento de descritor
+        try:
+            self.f.close()
+        except Exception:
+            pass
         
 
     def getConfigSim(self) -> dict: # Método que retorna as configurações do simulador
diff --git a/Escalonadores.py b/Escalonadores.py
index f45bd37..c86b222 100644
--- a/Escalonadores.py
+++ b/Escalonadores.py
@@ -3,15 +3,17 @@ from abc import ABC, abstractmethod
 
 from TCB import TCB
 
+
+
 # Classe base, interface que tem que ser implementada por cada classe que implementa um algoritmo de escalonador
 class EscalonadorBase(ABC):
     @abstractmethod
-    def ordenar_candidatos(self, candidatos: list[TCB]) -> list[TCB]: # Recebe a lista de candidatos e devolve ela ordenada com base o algoritmo selecionado
+    def ordenar_candidatos(self, candidatos: list[TCB]) -> TCB: # Recebe a lista de candidatos e devolve ela ordenada com base o algoritmo selecionado
         pass
 
 # Classe escalonador SRTF
 class EscalonadorSRTF(EscalonadorBase):
-    def ordenar_candidatos(self, candidatos: list[TCB]) -> list[TCB]:
+    def ordenar_candidatos(self, candidatos: list[TCB]) -> TCB:
         candidatos.sort(key=lambda t: (
             t.tempoCorrido, # Menor tempo restante
             not t.estavaRodando, # Dar prefêrencia pela tarefa que já estava rodando
@@ -20,7 +22,26 @@ class EscalonadorSRTF(EscalonadorBase):
             random.random() # Sorteio Aleatório
         ))
 
-        return candidatos
+        if(len(candidatos) > 1):
+            motivo = self.motivo_de_escolha(candidatos[0], candidatos[1])
+            print(f"Motivo da escolha: {motivo}")
+
+
+        return candidatos[0] if len(candidatos) > 0 else None
+    
+    def motivo_de_escolha(self,t1 : TCB, t2 : TCB) -> int:
+        if t1.tempoCorrido != t2.tempoCorrido:
+            return "Menor tempo restante"
+        elif t1.estavaRodando != t2.estavaRodando:
+            return "Dar prefêrencia pela tarefa que já estava rodando"
+        elif t1.tempoDeIngresso != t2.tempoDeIngresso:
+            return "Menor instante de ingresso"
+        elif t1.tempoTotal != t2.tempoTotal:
+            return "Menor tempo total"      
+        else:
+            t1.sofreu_sorteio = True
+            return "Sorteio Aleatório"
+
     
 # Classe escalonador PRIOP
 class EscalonadorPRIOP(EscalonadorBase):
diff --git a/Interface.py b/Interface.py
index b50e130..29c77bd 100644
--- a/Interface.py
+++ b/Interface.py
@@ -103,7 +103,17 @@ class InterfaceSimulador:
 
         try:
             config = SimuladorConfig(filepath)
-            estado_inicial = SimuladorEstado(config.listaCPU, config.listaTarefasCarregadas)
+            
+            # Validação: verifica se há tarefas carregadas
+            if len(config.listaTarefasCarregadas) == 0:
+                messagebox.showwarning("Aviso", "Nenhuma tarefa foi carregada do arquivo. Verifique o conteúdo.")
+                return
+            
+            # Limpar figura anterior para evitar memory leak
+            if self.fig:
+                plt.close(self.fig)
+            
+            estado_inicial = SimuladorEstado(config.listaCPU, config.listaTarefasCarregadas, config.quantum)
             self.engine = SimuladorEngine(config, estado_inicial)
 
             self.lbl_info.config(text=f"Algoritmo: {config.algoritmoEscalomento}\nCPUs: {config.qtde_cpus}\nTarefas carregadas: {len(config.listaTarefasCarregadas)}")
@@ -115,7 +125,7 @@ class InterfaceSimulador:
 
             self.atualizar_tela()
             messagebox.showinfo("Sucesso", "Configuração carregada com sucesso!")
-
+    
         except Exception as e:
             messagebox.showerror("Erro", f"Falha ao ler o arquivo:\n{str(e)}")
 
@@ -127,7 +137,7 @@ class InterfaceSimulador:
         self.atualizar_tela()
 
     def acao_retroceder(self):
-        if len(self.engine.historico_estados) == 0:
+        if len(self.engine.historico_estados) <= 1:
             messagebox.showwarning("Aviso", "Já estamos no tick 0!")
             return
         self.engine.retroceder_tick()
@@ -193,21 +203,12 @@ class InterfaceSimulador:
             estado_atual = self.engine.estado_atual
             
             if esta_suspensa:
-                # Acordar: Tira da fila de suspensas e joga na de prontos
-                estado_atual.fila_suspensas.remove(tarefa)
-                estado_atual.fila_prontos.append(tarefa)
-                tarefa.estado = EstadosTarefa.PRONTO
+                # Acordar: usar o novo método sincronizado
+                estado_atual.acordar_tarefa(tarefa)
                 messagebox.showinfo("Sucesso", f"Tarefa T{tarefa.id} foi Despertada (Pronta)!")
             else:
-                # Suspender: Remove de onde estiver e joga na fila de suspensas
-                if tarefa in estado_atual.fila_prontos:
-                    estado_atual.fila_prontos.remove(tarefa)
-                for cpu in estado_atual.cpus:
-                    if cpu.atualTarefa == tarefa:
-                        cpu.atualTarefa = None
-                        
-                estado_atual.fila_suspensas.append(tarefa)
-                tarefa.estado = EstadosTarefa.BLOQUEADO
+                # Suspender: usar o novo método sincronizado
+                estado_atual.suspender_tarefa(tarefa)
                 messagebox.showinfo("Sucesso", f"Tarefa T{tarefa.id} foi Suspensa!")
             
             self.atualizar_tela()
@@ -222,6 +223,12 @@ class InterfaceSimulador:
             try:
                 novo_tempo = int(entry_tempo.get())
                 nova_prio = int(entry_prio.get())
+                
+                # Validação: tempo não pode ser negativo
+                if novo_tempo < 0:
+                    messagebox.showerror("Erro", "O tempo restante não pode ser negativo.")
+                    return
+                
                 tarefa.tempoCorrido = novo_tempo
                 tarefa.prioridadeEstatica = nova_prio
                 self.atualizar_tela()
@@ -280,7 +287,17 @@ class InterfaceSimulador:
         self.ax.clear()
 
         estado_atual = self.engine.estado_atual
-        todas_fotos_do_tempo = self.engine.historico_estados[1:] + [estado_atual]
+        # Monta a série temporal evitando duplicar o último snapshot e
+        # permitindo que edições manuais (no estado atual) sejam refletidas.
+        todas_fotos_do_tempo = list(self.engine.historico_estados)
+        if len(todas_fotos_do_tempo) == 0:
+            todas_fotos_do_tempo = [estado_atual]
+        else:
+            # Substitui o último snapshot pelo estado atual (mesmo tick), para refletir edições
+            if todas_fotos_do_tempo[-1].relogio_global == estado_atual.relogio_global:
+                todas_fotos_do_tempo[-1] = estado_atual
+            else:
+                todas_fotos_do_tempo.append(estado_atual)
 
         todas_tarefas = self.engine.config.listaTarefasCarregadas
         tarefas_ordenadas = sorted(todas_tarefas, key=lambda t: t.id)
@@ -293,12 +310,17 @@ class InterfaceSimulador:
         self.ax.set_xlabel("Tempo (Ticks)", fontweight="bold", color="#34495E")
         self.ax.set_title(f"Execução - {self.engine.config.algoritmoEscalomento}", fontsize=14, fontweight="bold", color="#2C3E50")
 
+        # Marca o início real: primeiro tick em que a tarefa executa em alguma CPU
         tarefas_iniciadas = set()
         tarefas_concluidas = set()
 
-        for tick, foto_estado in enumerate(todas_fotos_do_tempo):
-            
-            for cpu in foto_estado.cpus:
+        # Desenha por intervalos executados: o estado do tick T representa o que rodará durante [T, T+1).
+        # Assim, no carregamento (apenas snapshot do tick 0), não aparece "1 tick executado" no gráfico.
+        for i in range(1, len(todas_fotos_do_tempo)):
+            foto_execucao = todas_fotos_do_tempo[i - 1]
+            tick = foto_execucao.relogio_global
+
+            for cpu in foto_execucao.cpus:
                 tarefa = cpu.atualTarefa
                 if tarefa is not None:
                     y_pos = mapa_y[tarefa.id]
@@ -306,26 +328,28 @@ class InterfaceSimulador:
                     self.ax.barh(y=y_pos, width=1, left=tick, color=cor_hex, edgecolor='black', height=0.6)
                     self.ax.text(tick + 0.5, y_pos, f"CPU {cpu.id}", ha='center', va='center', color='black', fontweight='bold', fontsize=9)
 
-            for tarefa_pronta in foto_estado.fila_prontos:
+                    # Marcador de início: só quando a tarefa realmente começou a executar
+                    if tarefa.id not in tarefas_iniciadas:
+                        self.ax.plot(tick, y_pos + 0.35, marker='v', color='#2980B9', markersize=8)
+                        tarefas_iniciadas.add(tarefa.id)
+
+            for tarefa_pronta in foto_execucao.fila_prontos:
                 y_pos = mapa_y[tarefa_pronta.id]
                 self.ax.barh(y=y_pos, width=1, left=tick, color='white', edgecolor='black', height=0.6)
 
-            for t in tarefas_ordenadas:
-                if tick == t.tempoDeIngresso and t.id not in tarefas_iniciadas:
-                    y_pos = mapa_y[t.id]
-                    self.ax.plot(tick, y_pos + 0.35, marker='v', color='#2980B9', markersize=8) 
-                    tarefas_iniciadas.add(t.id)
-
-                if any(tf.id == t.id for tf in foto_estado.tarefas_finalizadas) and t.id not in tarefas_concluidas:
-                    y_pos = mapa_y[t.id]
-                    self.ax.plot(tick, y_pos - 0.35, marker='X', color='#E74C3C', markersize=8) 
-                    tarefas_concluidas.add(t.id)
-
-            for tarefa_suspensa in getattr(foto_estado, 'fila_suspensas', []):
+            for tarefa_suspensa in getattr(foto_execucao, 'fila_suspensas', []):
                 y_pos = mapa_y[tarefa_suspensa.id]
                 # Requisito 2.1c: Tarefa suspensa com cor preta
                 self.ax.barh(y=y_pos, width=1, left=tick, color='black', edgecolor='white', height=0.6)
 
+        for foto_estado in todas_fotos_do_tempo:
+            tick = foto_estado.relogio_global
+            for tf in getattr(foto_estado, 'tarefas_finalizadas', []):
+                if tf.id not in tarefas_concluidas:
+                    y_pos = mapa_y[tf.id]
+                    self.ax.plot(tick, y_pos - 0.35, marker='X', color='#E74C3C', markersize=8)
+                    tarefas_concluidas.add(tf.id)
+
         self.ax.xaxis.grid(True, linestyle='--', alpha=0.7)
         self.ax.set_axisbelow(True) 
         
@@ -334,7 +358,7 @@ class InterfaceSimulador:
         self.ax.set_xlim(0, tick_maximo)
 
         legend_elements = [
-            Line2D([0], [0], color='#2980B9', marker='v', linestyle='None', markersize=8, label='Chegada (*)*'),
+            Line2D([0], [0], color='#2980B9', marker='v', linestyle='None', markersize=8, label='Início (v)'),
             Line2D([0], [0], color='#E74C3C', marker='X', linestyle='None', markersize=8, label='Término (X)'),
             plt.Rectangle((0,0),1,1, facecolor="white", edgecolor="black", label='Fila de Prontos'),
             plt.Rectangle((0,0),1,1, facecolor="black", edgecolor="white", label='Suspensa') # <--- NOVO ITEM NA LEGENDA
diff --git a/SimuladorConfig.py b/SimuladorConfig.py
index 02cd7bf..ca38e8c 100644
--- a/SimuladorConfig.py
+++ b/SimuladorConfig.py
@@ -8,10 +8,10 @@ class SimuladorConfig:
     algoritmoEscalomento : str #algoritmo escolhido
     quantum: int #duração do quantum
     qtde_cpus: int #quantidade de cpus
-    listaTarefasCarregadas: list = [] #lista de tarefas carregadas, representa o estado inicial das tarefas
-    listaCPU: list = [] #lista das cpus criadas, representa o estado inicial das cpus
 
     def __init__(self,txt: str):
+        self.listaTarefasCarregadas = []
+        self.listaCPU = []
         configParse = CarregarConfig() #cria um objeto que lê o arquivo txt
         print(configParse.carregarArquivoTXT(txt)) #um print para saber se o arquivo foi lido com sucesso
         configParse.carregarParametros() # método para ler o arquivo txt
diff --git a/SimuladorEngine.py b/SimuladorEngine.py
index 827ce38..f26150f 100644
--- a/SimuladorEngine.py
+++ b/SimuladorEngine.py
@@ -1,3 +1,4 @@
+import copy
 from SimuladorConfig import SimuladorConfig
 from SimuladorEstado import SimuladorEstado
 from TCB import TCB
@@ -5,85 +6,181 @@ from Estados import EstadosTarefa, EstadosCPU
 from CPU import CPU
 from Escalonadores import fabrica_de_escalonadores, EscalonadorBase
 
+
 class SimuladorEngine:
     config : SimuladorConfig # Configuração do sistema
     estado_atual: SimuladorEstado # Estado atual
     historico_estados: list[SimuladorEstado] # Lista para guardar todos os estados para retroceder no tempo
     escalonador: EscalonadorBase # Escalonador escolhido com base no config.txt
+    quantumTotal: int #representa a quantidade quantum total do sistema
 
     def __init__(self, config: SimuladorConfig, estado_inicial: SimuladorEstado):
         self.config = config # Salva configuração
         self.estado_atual = estado_inicial # Salva o estado inicial
         self.historico_estados = [] # Inicia como lista vazia
         self.escalonador = fabrica_de_escalonadores(self.config.algoritmoEscalomento) # Seleciona escalonador
+        self.quantumTotal = self.config.quantum # Salva o quantum total do sistema
+        self.prepararSimulador() # Prepara o simulador, colocando as tarefas que entram no tempo 0 na fila de prontos e chamando o escalonador para definir quais tarefas vão para cada cpu
     
     def verificar_nascimento(self) -> None: # Método que percorre a lista de tarefas futuras e coloca na fila de prontos as que entram agora no sistema
-        for tarefa_futura in self.estado_atual.tarefas_futuras.copy(): # O copy serve para evitar problemas com o remove() dentro do método ingressar_tarefa
+        tarefas_futuras = []
+        for tarefa_futura in self.estado_atual.tarefas_futuras:
             if tarefa_futura.tempoDeIngresso == self.estado_atual.relogio_global:
-                self.estado_atual.ingressar_tarefa(tarefa_futura)
+                tarefas_futuras.append(tarefa_futura)
+        for tf in tarefas_futuras:
+            self.estado_atual.ingressar_tarefa(tf)
+        if len(tarefas_futuras) > 0:
+            self.escalonar_novas_tarefas()
+        
+            
+            
 
     def processar_cpus(self) -> None: # Método que verifica todas as tarefas da cpu, diminui o tempo delas e verifica se elas finalizaram
-        for cpu in self.estado_atual.cpus:
-            if cpu.atualTarefa is not None:
-                cpu.atualTarefa.tempoCorrido = cpu.atualTarefa.tempoCorrido - 1
+        for p in self.estado_atual.cpus:
+            p.quantumProprio = p.quantumProprio + 1
+            if p.atualTarefa is not None:
+                if p.atualTarefa.tempoCorrido <= 0:
+                    self.estado_atual.finalizar_tarefa(p.atualTarefa, p)
+                    self.escalonar_cpu(p)
+                else:
+                    p.atualTarefa.tempoCorrido = p.atualTarefa.tempoCorrido - 1
+                    if p.atualTarefa.tempoCorrido == 0:
+                        self.estado_atual.finalizar_tarefa(p.atualTarefa, p)
+                        self.escalonar_cpu(p)
+                    elif p.quantumProprio == self.quantumTotal:
+                        self.escalonar_cpu(p)
+            else:
+                if p.quantumProprio == self.quantumTotal:
+                    self.escalonar_cpu(p)
 
-                if cpu.atualTarefa.tempoCorrido == 0: # Verifica se a tarefa finalizou
-                    self.estado_atual.finalizar_tarefa(cpu.atualTarefa, cpu)
+        for cpu in self.estado_atual.cpus:
+            if cpu.atualTarefa is None:
+                cpu.estado = EstadosCPU.DESLIGADO
+            else:
+                cpu.estado = EstadosCPU.LIGADO
+                   
  
-    def chamar_escalonador(self) -> None: # Método para definir quais tarefas vão rodar em cada cpu
-        candidatos: list[TCB] = []
+    def escalonar_cpu(self,p: CPU) -> None: # Método para definir quais tarefas vão rodar em cada cpu
+        candidatos = copy.copy(self.estado_atual.fila_prontos)
+        if p.atualTarefa is not None:
+            candidatos.append(p.atualTarefa)
 
-        for tarefa_pronta in self.estado_atual.fila_prontos: # Pega todas as tarefas da filas de pronto
-            tarefa_pronta.estavaRodando = False # Atributo temporário para desempate
-            candidatos.append(tarefa_pronta)
-        
-        for cpu in self.estado_atual.cpus: # Pega todas as tarefas rodando em cada cpu
-            if cpu.atualTarefa is not None:
-                cpu.atualTarefa.estavaRodando = True # Atributo temporário para desempate
-                candidatos.append(cpu.atualTarefa)
-                cpu.atualTarefa = None
-
-        if not candidatos: # Se não houver nenhum candido desliga todas as cpus e retorna
-            for cpu in self.estado_atual.cpus:
-                cpu.estado = EstadosCPU.DESLIGADO # Desliga todas a cpus
+        t_escolhida = self.escalonador.ordenar_candidatos(candidatos)
+
+        if t_escolhida is None:
+            if p.atualTarefa is None:
+                p.estado = EstadosCPU.DESLIGADO
             return
-        
-        candidatos = self.escalonador.ordenar_candidatos(candidatos) # Ordena os candidatos usando o algortimo escalonador escolhido de forma modularizada
 
-        self.estado_atual.fila_prontos.clear()
+        p.estado = EstadosCPU.LIGADO
 
-        for candidato in candidatos:
-            cpu_livre: CPU = next((c for c in self.estado_atual.cpus if c.atualTarefa is None), None) # Procura primeira CPU livre
+        # Se a mesma tarefa continua escolhida, só reseta quantum e mantém rodando
+        if t_escolhida == p.atualTarefa:
+            p.quantumProprio = 0
+            return
+
+        # Se havia tarefa executando e ela perdeu a CPU, volta para prontos
+        if p.atualTarefa is not None:
+            p.atualTarefa.estado = EstadosTarefa.PRONTO
+            p.atualTarefa.idCpu = -1
+            self.estado_atual.fila_prontos.append(p.atualTarefa)
+
+        # A tarefa escolhida sai de prontos (se estava lá) e entra na CPU
+        if t_escolhida in self.estado_atual.fila_prontos:
+            self.estado_atual.fila_prontos.remove(t_escolhida)
+
+        p.atualTarefa = t_escolhida
+        p.atualTarefa.estado = EstadosTarefa.EXECUTANDO
+        p.atualTarefa.idCpu = p.id
+        p.quantumProprio = 0
 
-            if cpu_livre is not None:
-                # A tarefa do topo da lista de candidatos foi selecionada para essa cpu
-                cpu_livre.atualTarefa = candidato
-                candidato.estado = EstadosTarefa.EXECUTANDO
-            else:
-                # Não tem mais vaga, o candidato volta para a fila de prontos
-                self.estado_atual.fila_prontos.append(candidato)
-                candidato.estado = EstadosTarefa.PRONTO
         
-        # Verifica todas as cpus, se não tem tarefa, seta como desligada
-        for cpu in self.estado_atual.cpus:
-            if cpu.atualTarefa is None:
-                cpu.estado = EstadosCPU.DESLIGADO
-            else:
-                cpu.estado = EstadosCPU.LIGADO
+    
+    def escalonar_novas_tarefas(self) -> None: # Método para definir quais tarefas vão rodar em cada cpu
+        candidatos = copy.copy(self.estado_atual.fila_prontos)
+        for p in self.estado_atual.cpus:
+            if p.atualTarefa is not None:
+                candidatos.append(p.atualTarefa)
+        
+        escolhidos = []
+
+        for i in range(len(self.estado_atual.cpus)):
+            t_escolhida = self.escalonador.ordenar_candidatos(candidatos)
+            if t_escolhida is not None:
+                escolhidos.append(t_escolhida)
+                candidatos.remove(t_escolhida)
+
+        # 1) Mantém as tarefas já executando que continuam escolhidas.
+        # 2) Para CPUs que precisam trocar (ou estão ociosas), realoca e preenche com o que sobrar em `escolhidos`.
+        for p in self.estado_atual.cpus:
+            if p.atualTarefa in escolhidos:
+                escolhidos.remove(p.atualTarefa)
+                continue
+
+            # Se havia tarefa executando e ela não foi escolhida, devolve pra fila de prontos
+            if p.atualTarefa is not None:
+                p.atualTarefa.estado = EstadosTarefa.PRONTO
+                p.atualTarefa.idCpu = -1
+                self.estado_atual.fila_prontos.append(p.atualTarefa)
+                p.atualTarefa = None
+
+            # Preenche CPU ociosa com a próxima escolhida (se existir)
+            if len(escolhidos) > 0:
+                t = escolhidos.pop(0)
+                # Remove da fila de prontos, se estiver lá (evita duplicação)
+                if t in self.estado_atual.fila_prontos:
+                    self.estado_atual.fila_prontos.remove(t)
+                p.atualTarefa = t
+                p.atualTarefa.estado = EstadosTarefa.EXECUTANDO
+                p.atualTarefa.idCpu = p.id
+                p.quantumProprio = 0
+
 
     def avancar_tick(self) -> None: # Método que controla o fluxo de avançar o tempo do sistema
-        self.historico_estados.append(self.estado_atual.clonar_estado())
-        self.verificar_nascimento()
+        #self.historico_estados.append(self.estado_atual.clonar_estado())
+        self.resetarMarcadorRandomico()
         self.processar_cpus()
-        self.chamar_escalonador()
         self.estado_atual.relogio_global = self.estado_atual.relogio_global + 1
+        # Aplica ingressos do novo tick (tarefa com tempoDeIngresso == relogio_global)
+        self.verificar_nascimento()
+        self.historico_estados.append(self.estado_atual.clonar_estado())
 
     def retroceder_tick(self) -> None: # Método que controla o fluxo de retroceder o tempo do sistema
-        if len(self.historico_estados) > 0:
-            self.estado_atual = self.historico_estados.pop()
-        else:
+        # `historico_estados` guarda snapshots (deepcopy) do estado.
+        # Após um `avancar_tick()`, o snapshot do tick atual está no final da lista.
+        # Para voltar 1 tick, descartamos o snapshot atual e restauramos o anterior.
+        if len(self.historico_estados) <= 1:
             print("Não é possível retroceder!")
+            return
+
+        self.historico_estados.pop()  # descarta snapshot do tick atual
+        self.estado_atual = self.historico_estados[-1].clonar_estado()  # restaura tick anterior
 
     def executar_tudo(self) -> None: # Executa a simulação inteira de uma vez
         while not self.estado_atual.simulacao_finalizada():
-            self.avancar_tick()
\ No newline at end of file
+            self.avancar_tick()
+
+    def prepararSimulador(self) -> None:
+        tarefas_para_ingressar = []
+
+        for t in self.estado_atual.tarefas_futuras:
+            if t.tempoDeIngresso == 0:
+                tarefas_para_ingressar.append(t)
+
+        for t in tarefas_para_ingressar:
+            self.estado_atual.ingressar_tarefa(t)
+
+        # Escalona o estado inicial (tick 0) para preencher CPUs disponíveis
+        if len(tarefas_para_ingressar) > 0 or len(self.estado_atual.fila_prontos) > 0:
+            self.escalonar_novas_tarefas()
+        
+        # Salvar estado inicial (t=0) no histórico para sincronização com interface
+        self.historico_estados.append(self.estado_atual.clonar_estado())
+
+
+    def resetarMarcadorRandomico(self) -> None:
+        for p in self.estado_atual.cpus:
+            if (p.atualTarefa is not None) and (p.atualTarefa.sofreu_sorteio == True):
+                p.atualTarefa.sofreu_sorteio = False
+
+
diff --git a/SimuladorEstado.py b/SimuladorEstado.py
index e926d05..ac74af9 100644
--- a/SimuladorEstado.py
+++ b/SimuladorEstado.py
@@ -10,12 +10,13 @@ from Estados import EstadosTarefa
 class SimuladorEstado:
     relogio_global: int = 0 # Relógio do sistema
     cpus: list[CPU] # Lista de CPUs
+    quantumTotal: int  #representa a quantidade quantum total do sistema
     fila_prontos: list[TCB] # Lista da fila da tarefas prontas para execução 
     fila_suspensas: list[TCB] # Lista da fila de tarefas suspensas
     tarefas_futuras: list[TCB] # Lista de tarefas futuras
     tarefas_finalizadas: list[TCB] # Lista de tarefas finalizadas
 
-    def __init__(self, lista_cpus: list[CPU], lista_tarefas_carregadas: list[TCB]):
+    def __init__(self, lista_cpus: list[CPU], lista_tarefas_carregadas: list[TCB],quantumTotal: int):
         self.relogio_global = 0 # Inicia relógio do sistema em zero
         # Usa deepcopy para desvincular da configuração original, desacoplamento
         self.cpus = copy.deepcopy(lista_cpus) # Recebe lista de cpus criada pelo SimuladorConfig
@@ -23,6 +24,7 @@ class SimuladorEstado:
         self.fila_prontos = [] # Inicia fila de prontos vazia
         self.fila_suspensas = [] # Inicia fila de tarefas suspensas vazia
         self.tarefas_finalizadas = [] # Inicia fila de tarefas finalizadas vazia
+        self.quantumTotal = quantumTotal #recebe o quantum total do sistema, criado pelo SimuladorConfig
 
     def simulacao_finalizada(self) -> bool: # Método que retorna se a simulacao está finalizada
         if self.tarefas_futuras: # Verifiica se ainda existem tarefas futuras
@@ -37,7 +39,7 @@ class SimuladorEstado:
             
         return True
 
-    def obter_cpus_livres(self) -> list[CPU]: # Método que retorna as cpus livres do siistema
+    def obter_cpus_livres(self) -> list[CPU]: # Método que retorna as cpus livres do sistema
         cpus_livres: list[CPU] = []
         for cpu in self.cpus:
             if cpu.estado == EstadosCPU.LIGADO and cpu.atualTarefa == None:  # Verifica quais cpus estão ligadas e não tem nenhuma tarefa atribuida a elas
@@ -56,4 +58,29 @@ class SimuladorEstado:
         tarefa.estado = EstadosTarefa.FINALIZADO
 
     def clonar_estado(self) -> SimuladorEstado: # Método que retorna uma cópia profunda desse estado, ajuuda no histórico
-        return copy.deepcopy(self)
\ No newline at end of file
+        return copy.deepcopy(self)
+
+    def suspender_tarefa(self, tarefa: TCB) -> None: # Método para suspender uma tarefa manualmente, mantendo sincronização com engine
+        # Remove da fila de prontos, se estiver
+        if tarefa in self.fila_prontos:
+            self.fila_prontos.remove(tarefa)
+        
+        # Remove de qualquer CPU que esteja executando
+        for cpu in self.cpus:
+            if cpu.atualTarefa == tarefa:
+                cpu.atualTarefa = None
+        
+        # Coloca na fila de suspensas e atualiza estado
+        if tarefa not in self.fila_suspensas:
+            self.fila_suspensas.append(tarefa)
+        tarefa.estado = EstadosTarefa.BLOQUEADO
+
+    def acordar_tarefa(self, tarefa: TCB) -> None: # Método para acordar uma tarefa suspensa, colocando-a de volta na fila de prontos
+        # Remove da fila de suspensas
+        if tarefa in self.fila_suspensas:
+            self.fila_suspensas.remove(tarefa)
+        
+        # Coloca na fila de prontos e atualiza estado
+        if tarefa not in self.fila_prontos:
+            self.fila_prontos.append(tarefa)
+        tarefa.estado = EstadosTarefa.PRONTO
\ No newline at end of file
diff --git a/TCB.py b/TCB.py
index 157181b..78ca48f 100644
--- a/TCB.py
+++ b/TCB.py
@@ -10,7 +10,7 @@ class TCB:
     
     id: int = -1 #id da tarefa
     cor: str = "FFFFFF" #pode alterar por causa do matplotlip
-    estado: EstadosTarefa = EstadosTarefa.NOVO  #guardar o estado da tarefa?
+    estado: EstadosTarefa = EstadosTarefa.NOVO  #guardar o estado da tarefa, incia como novo, que é quando ela entrou no sistema 
     idCpu: int = -1 #cpu associada com o processo
     listaEvento : list[int] = field(default_factory=list) #guarda uma lista de evento para o projeto B
     historico: list[tuple[int,int,EstadosTarefa]] = field(default_factory=list) # guarda o histórico de tempo e o estado da tarefa(inicio,fim,qual_estado)
diff --git a/config2.txt b/config2.txt
index 630168b..faaed50 100644
--- a/config2.txt
+++ b/config2.txt
@@ -1,6 +1,6 @@
-SRTF;2;
-;;;;;[]
-;;;;;[]
-3;#2ECC71;2;2;5;[]
-4;#F1C40F;;5;2;[]
-;;;;;[]
\ No newline at end of file
+SRTF;;30
+;#3498DB;0;10;3;[]
+;#E74C3C;0;4;1;[]
+;#2ECC71;2;2;5;[]
+;#F1C40F;5;5;2;[]
+;#9B59B6;8;8;4;[]
\ No newline at end of file
```

Nota: o bloco acima é o `git diff` bruto. Ele é longo e inclui trechos completos de funções onde a lógica mudou (especialmente em escalonamento, histórico e Gantt).

## Novos arquivos (não aparecem no git diff)

### tests/test_engine_history.py

```python
import random
import tempfile
import unittest

from SimuladorConfig import SimuladorConfig
from SimuladorEstado import SimuladorEstado
from SimuladorEngine import SimuladorEngine


def _write_temp_config(text: str) -> str:
    tmp = tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt")
    tmp.write(text)
    tmp.flush()
    tmp.close()
    return tmp.name


def _find_task_anywhere(estado, task_id: int):
    for t in getattr(estado, "tarefas_futuras", []):
        if t.id == task_id:
            return t
    for t in getattr(estado, "fila_prontos", []):
        if t.id == task_id:
            return t
    for t in getattr(estado, "fila_suspensas", []):
        if t.id == task_id:
            return t
    for t in getattr(estado, "tarefas_finalizadas", []):
        if t.id == task_id:
            return t
    for cpu in getattr(estado, "cpus", []):
        if cpu.atualTarefa is not None and cpu.atualTarefa.id == task_id:
            return cpu.atualTarefa
    return None


def _task_ids_in_prontos(estado) -> set[int]:
    return {t.id for t in getattr(estado, "fila_prontos", [])}


def _task_ids_in_cpus(estado) -> set[int]:
    ids: set[int] = set()
    for cpu in getattr(estado, "cpus", []):
        if cpu.atualTarefa is not None:
            ids.add(cpu.atualTarefa.id)
    return ids


class TestEngineHistoricoSemantica(unittest.TestCase):
    def setUp(self):
        random.seed(0)

    def _make_engine(self, quantum: int = 1, cpus: int = 1):
        cfg_text = (
            f"SRTF;{quantum};{cpus}\n"
            "1;FF6B6B;0;3;1;[]\n"
            "2;4ECDC4;0;5;1;[]\n"
        )
        path = _write_temp_config(cfg_text)
        config = SimuladorConfig(path)
        estado = SimuladorEstado(config.listaCPU, config.listaTarefasCarregadas, config.quantum)
        return SimuladorEngine(config, estado)

    def test_estado_inicial_nao_deve_vir_adiantado(self):
        engine = self._make_engine(quantum=2, cpus=1)
        self.assertEqual(engine.estado_atual.relogio_global, 0)
        self.assertEqual(len(engine.historico_estados), 1)
        self.assertEqual(engine.historico_estados[0].relogio_global, 0)

        t1 = _find_task_anywhere(engine.estado_atual, 1)
        t2 = _find_task_anywhere(engine.estado_atual, 2)
        self.assertIsNotNone(t1)
        self.assertIsNotNone(t2)
        self.assertEqual(t1.tempoCorrido, 3)
        self.assertEqual(t2.tempoCorrido, 5)

    def test_retroceder_deve_voltar_exatamente_um_tick(self):
        engine = self._make_engine(quantum=2, cpus=1)
        engine.avancar_tick()
        self.assertEqual(engine.estado_atual.relogio_global, 1)
        self.assertEqual(len(engine.historico_estados), 2)
        engine.retroceder_tick()
        self.assertEqual(engine.estado_atual.relogio_global, 0)
        self.assertEqual(len(engine.historico_estados), 1)

    def test_avancar_apos_retroceder_deve_ser_deterministico(self):
        engine = self._make_engine(quantum=1, cpus=1)
        engine.avancar_tick()
        snap_tick_1 = engine.estado_atual.clonar_estado()
        engine.retroceder_tick()
        self.assertEqual(engine.estado_atual.relogio_global, 0)
        engine.avancar_tick()

        self.assertEqual(engine.estado_atual.relogio_global, snap_tick_1.relogio_global)
        self.assertEqual(len(engine.estado_atual.cpus), len(snap_tick_1.cpus))
        cpu_now = engine.estado_atual.cpus[0]
        cpu_prev = snap_tick_1.cpus[0]
        self.assertEqual(cpu_now.quantumProprio, cpu_prev.quantumProprio)

        t1_now = _find_task_anywhere(engine.estado_atual, 1)
        t1_prev = _find_task_anywhere(snap_tick_1, 1)
        self.assertIsNotNone(t1_now)
        self.assertIsNotNone(t1_prev)
        self.assertEqual(t1_now.tempoCorrido, t1_prev.tempoCorrido)

    def test_quantum_cpu_deve_ser_restaurado_no_retrocesso(self):
        engine = self._make_engine(quantum=2, cpus=1)
        engine.avancar_tick()
        self.assertGreaterEqual(engine.estado_atual.cpus[0].quantumProprio, 0)
        engine.retroceder_tick()
        self.assertEqual(engine.estado_atual.cpus[0].quantumProprio, 0)

    def test_ingresso_no_tick_deve_aparecer_no_estado_do_mesmo_tick(self):
        cfg_text = (
            "SRTF;1;1\n"
            "1;FF6B6B;0;3;1;[]\n"
            "2;4ECDC4;1;5;1;[]\n"
        )
        path = _write_temp_config(cfg_text)
        config = SimuladorConfig(path)
        estado = SimuladorEstado(config.listaCPU, config.listaTarefasCarregadas, config.quantum)
        engine = SimuladorEngine(config, estado)

        def esta_em_cpu(estado_atual, task_id: int) -> bool:
            return any(cpu.atualTarefa is not None and cpu.atualTarefa.id == task_id for cpu in estado_atual.cpus)

        def esta_em_prontos(estado_atual, task_id: int) -> bool:
            return any(t.id == task_id for t in estado_atual.fila_prontos)

        def esta_em_futuras(estado_atual, task_id: int) -> bool:
            return any(t.id == task_id for t in estado_atual.tarefas_futuras)

        self.assertTrue(esta_em_prontos(engine.estado_atual, 1) or esta_em_cpu(engine.estado_atual, 1))
        self.assertTrue(esta_em_futuras(engine.estado_atual, 2))
        self.assertFalse(esta_em_prontos(engine.estado_atual, 2) or esta_em_cpu(engine.estado_atual, 2))

        engine.avancar_tick()
        self.assertEqual(engine.estado_atual.relogio_global, 1)
        self.assertFalse(esta_em_futuras(engine.estado_atual, 2))
        self.assertTrue(esta_em_prontos(engine.estado_atual, 2) or esta_em_cpu(engine.estado_atual, 2))

    def test_cpu_livre_nao_pode_deixar_tarefa_em_prontos(self):
        cfg_text = (
            "SRTF;10;2\n"
            "1;FF6B6B;0;20;1;[]\n"
            "4;F7B801;6;3;1;[]\n"
        )
        path = _write_temp_config(cfg_text)
        config = SimuladorConfig(path)
        estado = SimuladorEstado(config.listaCPU, config.listaTarefasCarregadas, config.quantum)
        engine = SimuladorEngine(config, estado)

        for _ in range(6):
            engine.avancar_tick()

        self.assertEqual(engine.estado_atual.relogio_global, 6)
        cpu_ids = _task_ids_in_cpus(engine.estado_atual)
        prontos_ids = _task_ids_in_prontos(engine.estado_atual)
        self.assertIn(4, cpu_ids)
        self.assertNotIn(4, prontos_ids)

    def test_tarefa_nao_pode_estar_em_cpu_e_em_prontos_ao_mesmo_tempo(self):
        engine = self._make_engine(quantum=10, cpus=2)
        intersec = _task_ids_in_cpus(engine.estado_atual) & _task_ids_in_prontos(engine.estado_atual)
        self.assertEqual(intersec, set())
        engine.avancar_tick()
        intersec2 = _task_ids_in_cpus(engine.estado_atual) & _task_ids_in_prontos(engine.estado_atual)
        self.assertEqual(intersec2, set())

    def test_nenhuma_tarefa_deve_sumir_do_estado(self):
        cfg = SimuladorConfig('config.txt')
        estado = SimuladorEstado(cfg.listaCPU, cfg.listaTarefasCarregadas, cfg.quantum)
        engine = SimuladorEngine(cfg, estado)

        all_ids = {t.id for t in cfg.listaTarefasCarregadas}

        def present_ids(st):
            ids = set(t.id for t in st.fila_prontos)
            ids |= set(t.id for t in st.tarefas_futuras)
            ids |= set(t.id for t in st.tarefas_finalizadas)
            ids |= set(t.id for t in getattr(st, 'fila_suspensas', []))
            ids |= {cpu.atualTarefa.id for cpu in st.cpus if cpu.atualTarefa is not None}
            return ids

        for _ in range(15):
            missing = all_ids - present_ids(engine.estado_atual)
            self.assertEqual(missing, set())
            if engine.estado_atual.simulacao_finalizada():
                break
            engine.avancar_tick()


if __name__ == "__main__":
    unittest.main()
```

### pseudobod.txt

Arquivo de apoio/rascunho com o raciocínio do fluxo.
