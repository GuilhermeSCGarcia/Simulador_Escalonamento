import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.lines import Line2D 

from SimuladorConfig import SimuladorConfig
from SimuladorEstado import SimuladorEstado
from SimuladorEngine import SimuladorEngine
from Estados import EstadosTarefa
from Escalonadores import fabrica_de_escalonadores
from TCB import TCB

class InterfaceSimulador:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Escalonamento de SO")
        self.root.geometry("1600x900")
        self.root.configure(bg="#F0F0F0") 

        self.engine: SimuladorEngine = None
        self.mapa_tarefas = {} # Dicionário para mapear a linha clicada na tabela para o objeto TCB real
        self.filepath = None # Variável para armazenar o caminho do arquivo carregado, para usar na reiniciação

        self.criar_widgets()

    def criar_widgets(self):
        # --- PAINEL LATERAL ---
        self.frame_controles = tk.Frame(self.root, width=300, bg="#2C3E50", padx=20, pady=20) #configura a coluna da esquerda, onde ficam os controles, e a cor de fundo
        self.frame_controles.pack(side=tk.LEFT, fill=tk.Y) #preenche na região da esquerda, com altura total da janela
        self.frame_controles.pack_propagate(False) #impede que o autoajuste do frame mude o tamanho definidos

        #Texto para configurar o painel de controle
        tk.Label(self.frame_controles, text="Painel de Controle", font=("Helvetica", 18, "bold"), bg="#2C3E50", fg="white").pack(pady=(0, 20))

        #Botão para carregar o arquivo txt
        self.btn_carregar = tk.Button(self.frame_controles, text="Carregar config.txt", font=("Helvetica", 12), bg="#27AE60", fg="white", relief="flat", command=self.carregar_arquivo)
        self.btn_carregar.pack(fill=tk.X, pady=10)
        
        # Mensagem para mostrar que não tem configuração carregada
        self.lbl_info = tk.Label(self.frame_controles, text="Nenhuma configuração carregada.", font=("Helvetica", 10), bg="#2C3E50", fg="#BDC3C7", justify=tk.LEFT)
        self.lbl_info.pack(anchor="w", pady=10)

        # Mudar Algoritmo em Tempo de execução
        tk.Label(self.frame_controles, text="Algoritmo Atual:", font=("Helvetica", 10, "bold"), bg="#2C3E50", fg="white").pack(anchor="w", pady=(10, 0))
        self.combo_algoritmo = ttk.Combobox(self.frame_controles, values=["SRTF", "PRIOP"], state="disabled")
        self.combo_algoritmo.pack(fill=tk.X, pady=(2, 10))
        self.combo_algoritmo.bind("<<ComboboxSelected>>", self.acao_mudar_algoritmo)
        
        #frame que contém o status do sistema
        self.frame_status = tk.Frame(self.frame_controles, bg="#34495E", padx=10, pady=10)
        self.frame_status.pack(fill=tk.X, pady=20)

        #informação do tick atual
        self.lbl_relogio = tk.Label(self.frame_status, text="Tick Atual: 0", font=("Courier", 14, "bold"), bg="#34495E", fg="#F1C40F")
        self.lbl_relogio.pack(anchor="w")

        #informação da fila de prontos
        self.lbl_prontos = tk.Label(self.frame_status, text="Fila de Prontos: []", font=("Helvetica", 10), bg="#34495E", fg="white", wraplength=240, justify=tk.LEFT)
        self.lbl_prontos.pack(anchor="w", pady=(10,0))
        
        #informação das tarefas futuras
        self.lbl_futuras = tk.Label(self.frame_status, text="Tarefas Futuras: []", font=("Helvetica", 10), bg="#34495E", fg="#95A5A6", wraplength=240, justify=tk.LEFT)
        self.lbl_futuras.pack(anchor="w", pady=(10,0))

        #Texto do control de tempo
        tk.Label(self.frame_controles, text="Controles de Tempo", font=("Helvetica", 12, "bold"), bg="#2C3E50", fg="white").pack(anchor="w", pady=(20, 5))
        
        #Botão de avançar tick
        self.btn_avancar = tk.Button(self.frame_controles, text="Avançar Tick (+1)", font=("Helvetica", 11), bg="#2980B9", fg="white", relief="flat", state=tk.DISABLED, command=self.acao_avancar)
        self.btn_avancar.pack(fill=tk.X, pady=5)

        #Botão de retroceder tick
        self.btn_retroceder = tk.Button(self.frame_controles, text="Voltar Tick (-1)", font=("Helvetica", 11), bg="#E67E22", fg="white", relief="flat", state=tk.DISABLED, command=self.acao_retroceder)
        self.btn_retroceder.pack(fill=tk.X, pady=5)

        #Botão de executar tudo
        self.btn_executar_tudo = tk.Button(self.frame_controles, text="Executar Até o Fim", font=("Helvetica", 11), bg="#8E44AD", fg="white", relief="flat", state=tk.DISABLED, command=self.acao_executar_tudo)
        self.btn_executar_tudo.pack(fill=tk.X, pady=5)

        #Botão de reiniciar simulação
        self.btn_reiniciar = tk.Button(self.frame_controles, text="Reiniciar simulação", font=("Helvetica", 11), bg="#EE0B0B", fg="white", relief="flat", state=tk.DISABLED, command=self.acao_reiniciar)
        self.btn_reiniciar.pack(fill=tk.X, pady=5)

        #Botão de exportar gráfico
        tk.Label(self.frame_controles, text="Exportação", font=("Helvetica", 12, "bold"), bg="#2C3E50", fg="white").pack(anchor="w", pady=(20, 5))
        self.btn_exportar = tk.Button(self.frame_controles, text="Exportar Gráfico (.PNG)", font=("Helvetica", 11), bg="#7F8C8D", fg="white", relief="flat", state=tk.DISABLED, command=self.acao_exportar)
        self.btn_exportar.pack(fill=tk.X, pady=5)

        # --- PAINEL DIREITO (Gráfico + Tabela) ---
        self.frame_direito = tk.Frame(self.root, bg="white") #configura um frame para o lado direito, onde ficam o gráfico e a tabela, e a cor de fundo
        self.frame_direito.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True) #preenche na região da direita, com altura total da janela e largura máxima possível

        # Matplotlib no topo
        self.frame_grafico = tk.Frame(self.frame_direito, bg="white") #framme do gráfico
        self.frame_grafico.pack(side=tk.TOP, fill=tk.BOTH, expand=True) #configuração para preencher toda o lado direto, em largura e altura na parte de cima

        self.fig, self.ax = plt.subplots(figsize=(12, 8)) #configuração do gráfico para ser integrado ao tk, junto com seu frame de destaque
        self.fig.patch.set_facecolor('#F8F9FA') 
        self.ax.set_facecolor('#FFFFFF')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_grafico) #integração do gráfico com o tk, usando o frame do gráfico como destaque
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=(5, 0))

        # Tabela no rodapé
        self.frame_tabela = tk.Frame(self.frame_direito, bg="white", height=150) #frame do editor de tarefa
        self.frame_tabela.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        tk.Label(self.frame_tabela, text="Editor de Tarefas (Dê um duplo clique em uma tarefa para editá-la)", font=("Helvetica", 10, "bold"), bg="white", fg="#2C3E50").pack(anchor="w", pady=(0,5))

        # --- Botões para alternar a tabela ---
        frame_abas = tk.Frame(self.frame_tabela, bg="white")
        frame_abas.pack(fill=tk.X, pady=(0,5))
        
        self.btn_ver_tarefas = tk.Button(frame_abas, text="📊 Ver Tarefas", font=("Helvetica", 10), bg="#3498DB", fg="white", relief="flat", command=lambda: self.mudar_aba_tabela("Tarefas"))
        self.btn_ver_tarefas.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_ver_cpus = tk.Button(frame_abas, text="💻 Ver Uso das CPUs", font=("Helvetica", 10), bg="#95A5A6", fg="white", relief="flat", command=lambda: self.mudar_aba_tabela("CPUs"))
        self.btn_ver_cpus.pack(side=tk.LEFT)

        # Controle de modo atual
        self.modo_visualizacao = "Tarefas"

        # Tabela base (sem as colunas fixas ainda, pois o método vai inseri-las)
        self.tree = ttk.Treeview(self.frame_tabela, show='headings', height=5, selectmode="browse")   
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll_y = ttk.Scrollbar(self.frame_tabela, orient="vertical", command=self.tree.yview) 
        self.tree.configure(yscrollcommand=scroll_y.set) 
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<Double-1>", self.acao_editar_tarefa)
        self.desenhar_gantt_vazio()
        
        # Chama a função para criar as colunas iniciais de Tarefas
        self.mudar_aba_tabela("Tarefas")

    def mudar_aba_tabela(self, modo):
        self.modo_visualizacao = modo
        if modo == "Tarefas":
            self.btn_ver_tarefas.config(bg="#3498DB") # Fica azul
            self.btn_ver_cpus.config(bg="#95A5A6")    # Fica cinza
            colunas = ("ID", "Estado", "Tempo Restante", "Prioridade Estática", "Tempo de Ingresso")
        else:
            self.btn_ver_tarefas.config(bg="#95A5A6") # Fica cinza
            self.btn_ver_cpus.config(bg="#3498DB")    # Fica azul
            colunas = ("ID CPU", "Status Energia", "Tarefa Atual", "Uso (%)", "Quantum Atual")

        # Configura as novas colunas
        self.tree["columns"] = colunas
        for col in colunas:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")
            
        # Atualiza os dados se a engine já estiver carregada
        if self.engine: 
            self.atualizar_tela()


    def carregar_arquivo(self):
        self.filepath = filedialog.askopenfilename(title="Selecione o arquivo config.txt", filetypes=[("Text Files", "*.txt")])
        if not self.filepath:
            return

        try:
            #tenta abrir o arquivo txt com a classe SimuladorConfig, usado para processar os arquivos de forma mais fácil
            config = SimuladorConfig(self.filepath)
            
            #verificação para garantir que há alguma tarefa carregada no sistema, se não exibe uma janela de aviso
            if len(config.listaTarefasCarregadas) == 0:
                messagebox.showwarning("Aviso", "Nenhuma tarefa foi carregada do arquivo. Verifique o conteúdo.")
                return
            
            #limpar figura anterior quando carregar um novo arquivo, para evitar que a simulação anterior atrapalhe a nova
            if self.fig:
                plt.close(self.fig)
            
            
            estado_inicial = SimuladorEstado(config.listaCPU, config.listaTarefasCarregadas, config.quantum) #prepra o estado inicial
            self.engine = SimuladorEngine(config, estado_inicial) #prepara a engine do simulador
            #Atualiza as informações do painel lateral com os dados do arquivos carregado
            self.lbl_info.config(text=f"Algoritmo: {config.algoritmoEscalomento}\nCPUs: {config.qtde_cpus}\nTarefas carregadas: {len(config.listaTarefasCarregadas)}\nQuantum total: {config.quantum}")
            
            # Destrava e seta o algoritmo atual ---
            self.combo_algoritmo.config(state="readonly")
            self.combo_algoritmo.set(config.algoritmoEscalomento.upper())

            #ativa os botões para funcionar apos carregar as configurações
            self.btn_avancar.config(state=tk.NORMAL)
            self.btn_retroceder.config(state=tk.NORMAL)
            self.btn_executar_tudo.config(state=tk.NORMAL)
            self.btn_reiniciar.config(state=tk.NORMAL)
            self.btn_exportar.config(state=tk.NORMAL)

            self.atualizar_tela() #atualiza a tela com as informações inciais
            messagebox.showinfo("Sucesso", "Configuração carregada com sucesso!")
    
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao ler o arquivo:\n{str(e)}")

    def acao_mudar_algoritmo(self, event=None):
        if not self.engine: return
        
        novo_alg = self.combo_algoritmo.get()
        # Atualiza a string no config (para o título do gráfico atualizar)
        self.engine.config.algoritmoEscalomento = novo_alg
        # Substitui a instância do escalonador em tempo real!
        self.engine.escalonador = fabrica_de_escalonadores(novo_alg)
        
        self.atualizar_tela() # Atualiza para mudar o título do gráfico instantaneamente

    def acao_avancar(self):
        if self.engine.estado_atual.simulacao_finalizada():
            messagebox.showinfo("Fim", "A simulação já foi finalizada!")
            return
        self.engine.avancar_tick()
        self.atualizar_tela()

    def acao_retroceder(self):
        if len(self.engine.historico_estados) <= 1:
            self.engine.restaurarEstadoZero() # Restaura o estado zero diretamente da engine, para garantir que tudo volte ao início corretamente
            messagebox.showwarning("Aviso", "Já estamos no tick 0!")
            return
        self.engine.retroceder_tick()
        self.atualizar_tela()

    def acao_executar_tudo(self):
        if len(self.engine.estado_atual.fila_suspensas) > 0:
            messagebox.showwarning("Aviso", "Existem tarefas bloqueadas. Por favor, acorde ou remova as tarefas bloqueadas para executar até o fim.")
            return
        if self.engine.estado_atual.simulacao_finalizada():
            messagebox.showinfo("Fim", "A simulação já foi finalizada!")
            return
        self.engine.executar_tudo()
        self.atualizar_tela()

    def acao_exportar(self):
        try:
            filepath = filedialog.asksaveasfilename(defaultextension=".png", title="Salvar Gráfico de Gantt", filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("SVG", "*.svg")])
            if filepath:
                self.fig.savefig(filepath)
                messagebox.showinfo("Sucesso", f"Gráfico salvo com sucesso em:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar a imagem:\n{str(e)}")

    def acao_reiniciar(self):
            #tenta abrir o arquivo txt com a classe SimuladorConfig, usado para processar os arquivos de forma mais fácil
            config = SimuladorConfig(self.filepath)
            
            #verificação para garantir que há alguma tarefa carregada no sistema, se não exibe uma janela de aviso
            if len(config.listaTarefasCarregadas) == 0:
                messagebox.showwarning("Aviso", "Nenhuma tarefa foi carregada do arquivo. Verifique o conteúdo.")
                return
            
            #limpar figura anterior quando carregar um novo arquivo, para evitar que a simulação anterior atrapalhe a nova
            if self.fig:
                plt.close(self.fig)
            
            
            estado_inicial = SimuladorEstado(config.listaCPU, config.listaTarefasCarregadas, config.quantum) #prepra o estado inicial
            self.engine = SimuladorEngine(config, estado_inicial) #prepara a engine do simulador
            #Atualiza as informações do painel lateral com os dados do arquivos carregado
            self.lbl_info.config(text=f"Algoritmo: {config.algoritmoEscalomento}\nCPUs: {config.qtde_cpus}\nTarefas carregadas: {len(config.listaTarefasCarregadas)}\nQuantum total: {config.quantum}")
            
            # Destrava e seta o algoritmo atual ---
            self.combo_algoritmo.config(state="readonly")
            self.combo_algoritmo.set(config.algoritmoEscalomento.upper())

            #ativa os botões para funcionar apos carregar as configurações
            self.btn_avancar.config(state=tk.NORMAL)
            self.btn_retroceder.config(state=tk.NORMAL)
            self.btn_executar_tudo.config(state=tk.NORMAL)
            self.btn_reiniciar.config(state=tk.NORMAL)
            self.btn_exportar.config(state=tk.NORMAL)

            self.atualizar_tela() #atualiza a tela com as informações inciais
            messagebox.showinfo("Sucesso", "Simulação reiniciada com sucesso!")

    def acao_editar_tarefa(self, event):
        # Impede edição se não houver simulação carregada
        if not self.engine: return

        # Se está no modo CPU, não fazer nada
        if self.modo_visualizacao == "CPUs" : return

        #seleciona uma tarefa da tabela para editar
        
        item_id = self.tree.focus() #pega o item selecionado

        tarefa = self.mapa_tarefas.get(item_id) #procura na tabela qual é a tarefa para edição
        
        if not tarefa: return #se não encontrar a tarefa, retorna por segurança
        
        # Verifica se a tarefa está finalizada
        esta_finalizada = tarefa.estado.name == "FINALIZADO"

        # Abre a janela popup de edição
        win = tk.Toplevel(self.root)
        win.title(f"Editar Tarefa T{tarefa.id}")
        win.geometry("300x320") # Aumentei um pouco a altura
        win.configure(bg="#ECF0F1")
        win.wait_visibility() # espera que a janela fique visível para bloquear o clique em outras janelas
        win.grab_set() # garante que os cliques fiquem apenas aqui quando a janela abrir
        
        #Exibe o label para editar tarefa
        tk.Label(win, text=f"Editando Tarefa T{tarefa.id}", font=("Helvetica", 12, "bold"), bg="#ECF0F1").pack(pady=15)
        
        #Mostra o tempo restante
        tk.Label(win, text="Tempo Restante (Ticks):", bg="#ECF0F1").pack()
        entry_tempo = tk.Entry(win, justify='center')
        entry_tempo.insert(0, str(tarefa.tempoCorrido))
        entry_tempo.pack(pady=(0, 10))

        # Se está finalizada, desative
        if esta_finalizada: entry_tempo.config(state="disabled")

        #Mostra a prioridade estática
        tk.Label(win, text="Prioridade Estática:", bg="#ECF0F1").pack()
        entry_prio = tk.Entry(win, justify='center')
        entry_prio.insert(0, str(tarefa.prioridadeEstatica))
        entry_prio.pack(pady=(0, 15))

        # Se está finalizada, desative
        if esta_finalizada: entry_prio.config(state="disabled")

        # Variável para controlar se vamos suspender ou acordar a tarefa
        esta_suspensa = tarefa in self.engine.estado_atual.fila_suspensas

        def alternar_suspensao():
            estado_atual = self.engine.estado_atual
            
            if esta_suspensa:
                # Acordar: usar o novo método sincronizado
                estado_atual.acordar_tarefa(tarefa)
                #Essa condição é necessária para garantir que a atualização não rode mais um estado em suspenso, pois ele atualiza até o ultimo snapshot, que era antes da mudança
                #O tick atual vai refletir o intervalo, ou seja, o estado do tick T representa o que rodará durante [T, T+1), então a mudança tem que refletir nesse intervalo, e não no próximo tick
                if self.engine.historico_estados:
                    if self.engine.historico_estados[-1].relogio_global == self.engine.estado_atual.relogio_global: #atuliza o ultimo estado para refletir a mudança
                        self.engine.historico_estados[-1] = self.engine.estado_atual.clonar_estado()
                messagebox.showinfo("Sucesso", f"Tarefa T{tarefa.id} foi Despertada (Pronta)!")
            else:
                # Suspender: usar o novo método sincronizado
                estado_atual.suspender_tarefa(tarefa)
                if self.engine.historico_estados:
                    if self.engine.historico_estados[-1].relogio_global == estado_atual.relogio_global:
                        self.engine.historico_estados[-1] = estado_atual.clonar_estado() # Atualiza o último snapshot para refletir a suspensão
                messagebox.showinfo("Sucesso", f"Tarefa T{tarefa.id} foi Suspensa!")
            
            self.atualizar_tela()
            win.destroy()

        def forcar_finalizacao():
            # Tira das CPUs
            for cpu in self.engine.estado_atual.cpus:
                if cpu.atualTarefa == tarefa:
                    cpu.atualTarefa = None
                    
            # Tira das filas e atualiza estado
            if tarefa in self.engine.estado_atual.tarefas_futuras: self.engine.estado_atual.tarefas_futuras.remove(tarefa)
            if tarefa in self.engine.estado_atual.fila_prontos: self.engine.estado_atual.fila_prontos.remove(tarefa)
            if tarefa in self.engine.estado_atual.fila_suspensas: self.engine.estado_atual.fila_suspensas.remove(tarefa)
            
            tarefa.tempoCorrido = 0
            tarefa.quatum_dado = 0
            tarefa.idCpu = -1
            tarefa.estado = EstadosTarefa.FINALIZADO
            if tarefa not in self.engine.estado_atual.tarefas_finalizadas:
                self.engine.estado_atual.tarefas_finalizadas.append(tarefa)
            
            # Sincroniza e re-escalona
            if self.engine.historico_estados and self.engine.historico_estados[-1].relogio_global == self.engine.estado_atual.relogio_global:
                self.engine.historico_estados[-1] = self.engine.estado_atual.clonar_estado()
            self.engine.escalonar_novas_tarefas()

            self.atualizar_tela()
            win.destroy()
            messagebox.showinfo("Sucesso", f"Tarefa T{tarefa.id} foi encerrada à força!")

        def reviver_tarefa():
            estado_atual = self.engine.estado_atual
            config = self.engine.config
            
            # Descobre o maior ID atual para não duplicar
            novo_id = max([t.id for t in config.listaTarefasCarregadas]) + 1
            
            # Cria a "nova" tarefa clonada
            nova_tarefa = TCB(
                tempoDeIngresso=estado_atual.relogio_global, # Nasce AGORA
                tempoTotal=tarefa.tempoTotal,
                tempoCorrido=tarefa.tempoTotal,
                prioridadeEstatica=tarefa.prioridadeEstatica,
                id=novo_id,
                cor=tarefa.cor
            )
            nova_tarefa.estado = EstadosTarefa.PRONTO
            
            # Joga no sistema global e na fila
            config.listaTarefasCarregadas.append(nova_tarefa)
            estado_atual.fila_prontos.append(nova_tarefa)
            
            self.engine.escalonar_novas_tarefas()
            
            if self.engine.historico_estados and self.engine.historico_estados[-1].relogio_global == estado_atual.relogio_global:
                self.engine.historico_estados[-1] = estado_atual.clonar_estado()

            self.atualizar_tela()
            win.destroy()
            messagebox.showinfo("Renasceu!", f"A Tarefa T{tarefa.id} foi revivida! Novo ID: T{novo_id}")

        if esta_finalizada:
            # Se já acabou, mostra só o botão de Reviver
            tk.Label(win, text="[ Esta tarefa já FINALIZOU ]", fg="#E74C3C", bg="#ECF0F1", font=("Helvetica", 9, "bold")).pack(pady=5)
            tk.Button(win, text="Reviver Tarefa (Clonar)", bg="#9B59B6", fg="white", font=("Helvetica", 10, "bold"), relief="flat", command=reviver_tarefa).pack(fill=tk.X, padx=30, pady=10)
        else:
            # Se está viva, mostra Suspender e Forçar Finalização
            texto_botao_suspender = "Despertar Tarefa" if esta_suspensa else "Suspender Tarefa"
            cor_botao_suspender = "#F39C12" if esta_suspensa else "#E74C3C"
            tk.Button(win, text=texto_botao_suspender, bg=cor_botao_suspender, fg="white", font=("Helvetica", 10, "bold"), relief="flat", command=alternar_suspensao).pack(fill=tk.X, padx=30, pady=5)
            tk.Button(win, text="Forçar Finalização", bg="#C0392B", fg="white", font=("Helvetica", 10, "bold"), relief="flat", command=forcar_finalizacao).pack(fill=tk.X, padx=30, pady=5)

        def salvar_alteracoes():
            try:
                novo_tempo = int(entry_tempo.get())
                nova_prio = int(entry_prio.get())
                
                # Validação: tempo não pode ser negativo
                if novo_tempo < 0:
                    messagebox.showerror("Erro", "O tempo restante não pode ser negativo.")
                    return
                    
                # Se colocar zero, usa a função de forçar finalização que criamos!
                elif novo_tempo == 0 and not esta_finalizada:
                    forcar_finalizacao()
                    return
                
                tarefa.tempoCorrido = novo_tempo
                tarefa.prioridadeEstatica = nova_prio
                self.atualizar_tela()
                win.destroy()
                messagebox.showinfo("Sucesso", f"Tarefa T{tarefa.id} atualizada!")
            except ValueError:
                messagebox.showerror("Erro", "Insira apenas números inteiros válidos.")

        # Só mostra o botão de salvar se a tarefa NÃO estiver morta
        if not esta_finalizada:
            tk.Button(win, text="💾 Salvar Valores Manuais", bg="#27AE60", fg="white", font=("Helvetica", 10, "bold"), relief="flat", command=salvar_alteracoes).pack(pady=(10, 0))


    def atualizar_tela(self):
        self.ax.set_title(f"Execução - {self.engine.config.algoritmoEscalomento}", fontsize=14, fontweight="bold", color="#2C3E50") # atualiza o título do gráfico para refletir o algoritmo atual
        # Declara a variável estado puxando da engine
        estado = self.engine.estado_atual
        
        estado_quantum = self.engine.historico_estados[-2] if len(self.engine.historico_estados) > 1 else self.engine.estado_atual

        
        #Atualiza os textos dos labels
        self.lbl_relogio.config(text=f"Tick Atual: {estado.relogio_global}")
        
        prontos_str = ", ".join([f"T{t.id}" for t in estado.fila_prontos])
        futuras_str = ", ".join([f"T{t.id}" for t in estado.tarefas_futuras])
        
        self.lbl_prontos.config(text=f"Fila de Prontos: [{prontos_str}]")
        self.lbl_futuras.config(text=f"Tarefas Futuras: [{futuras_str}]")

        # Limpa a tabela atual antes de preencher
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        self.mapa_tarefas.clear()
        
        # Preenche a tabela dependendo do botão (Tarefas ou CPUs)
        if self.modo_visualizacao == "Tarefas":
            todas_tarefas = []
            todas_tarefas.extend(estado.tarefas_futuras)
            todas_tarefas.extend(estado.fila_prontos)
            todas_tarefas.extend(estado.tarefas_finalizadas)
            todas_tarefas.extend(estado.fila_suspensas) 

            for cpu in estado.cpus:
                if cpu.atualTarefa:
                    todas_tarefas.append(cpu.atualTarefa)
                    
            todas_tarefas.sort(key=lambda t: t.id)
            
            for t in todas_tarefas:
                estado_nome = t.estado.name if hasattr(t.estado, 'name') else str(t.estado)
                linha_id = self.tree.insert("", tk.END, values=(f"T{t.id}", estado_nome, t.tempoCorrido, t.prioridadeEstatica, t.tempoDeIngresso))
                self.mapa_tarefas[linha_id] = t 
                
        elif self.modo_visualizacao == "CPUs":
            for cpu in estado.cpus:
                status_energia = cpu.estado.name if hasattr(cpu.estado, 'name') else str(cpu.estado)
                tarefa_str = f"T{cpu.atualTarefa.id}" if cpu.atualTarefa else "Nenhuma"
                cpu_quantum = estado_quantum.cpus[cpu.id].atualTarefa.quatum_dado if estado_quantum.cpus[cpu.id].atualTarefa else 0
                quantum_str = f"{cpu_quantum+1}/{self.engine.quantumTotal}" if cpu.atualTarefa else "-"
                
                # Cálculo da % de uso da CPU (evitando divisão por zero)
                tempo_total_decorrido = max(1, estado.relogio_de_processo)
                # Verifica se a CPU tem o atributo tempoAtivo (senão usa 0)
                tempo_ativo = getattr(cpu, 'tempoAtivo', 0)
                porcentagem = (tempo_ativo / tempo_total_decorrido) * 100
                uso_str = f"{porcentagem:.1f}%"
                
                linha_id = self.tree.insert("", tk.END, values=(f"CPU {cpu.id}", status_energia, tarefa_str, uso_str, quantum_str))
                self.mapa_tarefas[linha_id] = cpu

        # Manda desenhar o gráfico com os dados atualizados
        self.desenhar_gantt()

    def desenhar_gantt_vazio(self):
        self.ax.clear()
        self.ax.set_title("Gráfico de Gantt - Aguardando Configuração", fontsize=14, fontweight="bold", color="#2C3E50")
        self.ax.set_xlabel("Tempo (Ticks)")
        self.ax.set_yticks([])
        self.canvas.draw()

    def desenhar_gantt(self):
        self.ax.clear()
        #Pega o estado atual para mostrar a serie de tempo
        estado_atual = self.engine.estado_atual
        
        #ppega todas as fotos de tempo para mostrar a serie de tempo, e se não tiver nenhuma serie ele pega apenas o estado atual
        todas_fotos_do_tempo = list(self.engine.historico_estados)
        if len(todas_fotos_do_tempo) == 0:
            todas_fotos_do_tempo = [estado_atual]

        
        #Pega a lista de tarefas, ordena elas e mostra no exito y
        todas_tarefas = self.engine.config.listaTarefasCarregadas #carrega a lista de tarefas
        tarefas_ordenadas = sorted(todas_tarefas, key=lambda t: t.id) #ordena as tarefas por id para atender o requisito de mostrar as tarefas em ordem crescente de id no eixo y
        nomes_tarefas = [f"Tarefa {t.id}" for t in tarefas_ordenadas] #cria uma lista de nomes mostrar no eixo y, com o formato de Tarefa id da tarefa
        posicoes_y = list(range(len(tarefas_ordenadas))) #Lista de posições y para cada tarefa, de acordo com o tamanho
        mapa_y = {t.id: y for t, y in zip(tarefas_ordenadas, posicoes_y)} #Mapeia cada id para sua posição y correspondente, em uma tupla, para facilitar a exibição

        self.ax.set_yticks(posicoes_y) #configura a quantidade de ticks no eixo y de acordo com a quantidade de tarefas
        self.ax.set_yticklabels(nomes_tarefas, fontweight="bold", color="#34495E") #cor e estilo
        self.ax.set_xlabel("Tempo (Ticks)", fontweight="bold", color="#34495E") # legenda do eixo x
        self.ax.set_title(f"Execução - {self.engine.config.algoritmoEscalomento}", fontsize=14, fontweight="bold", color="#2C3E50") #titulo

        # marca o início real: primeiro tick em que a tarefa executa em alguma CPU
        tarefas_iniciadas = set()
        # marca o termino de uma tarefa: primeiro tick em que a tarefa é finalizada
        tarefas_concluidas = set()

        # desenha por intervalos executados: o estado do tick T representa o que rodará durante [T, T+1)
        # começa em um o loop a partit do tick 1, para comparar como tick anterior e mostrar a execução do tick 0.
        # isso faz que a gente consiga mostrar a inicialização sem avançar um tick das tarefas já carregadas
        # e como a gente mostra o intervalo [T, T+1), o estado do tick 0 representa o que acontece durante o intervalo [0, 1)
        for i in range(1, len(todas_fotos_do_tempo)):
            foto_execucao = todas_fotos_do_tempo[i - 1] 
            tick = foto_execucao.relogio_global

            for cpu in foto_execucao.cpus:
                tarefa = cpu.atualTarefa
                if tarefa is not None:
                    y_pos = mapa_y[tarefa.id]
                    cor_hex = f"#{tarefa.cor}" if not tarefa.cor.startswith('#') else tarefa.cor
                    self.ax.barh(y=y_pos, width=1, left=tick, color=cor_hex, edgecolor='black', height=0.6)
                    self.ax.text(tick + 0.5, y_pos, f"CPU {cpu.id}", ha='center', va='center', color='black', fontweight='bold', fontsize=9)

                    # Marcador de início: só quando a tarefa realmente começou a executar
                    if tarefa.id not in tarefas_iniciadas:
                        self.ax.plot(tick, y_pos + 0.35, marker='v', color='#2980B9', markersize=8)
                        if tarefa.sofreu_sorteio == True:
                            self.ax.plot(tick, y_pos - 0.35, marker='*', color="#F39C12", markersize=8) # Tarefa que sofreu sorteio tem marcador laranja
                        tarefas_iniciadas.add(tarefa.id)

            for tarefa_pronta in foto_execucao.fila_prontos:
                y_pos = mapa_y[tarefa_pronta.id]
                self.ax.barh(y=y_pos, width=1, left=tick, color='white', edgecolor='black', height=0.6)

            for tarefa_suspensa in getattr(foto_execucao, 'fila_suspensas', []):
                y_pos = mapa_y[tarefa_suspensa.id]
                # Requisito 2.1c: Tarefa suspensa com cor preta
                self.ax.barh(y=y_pos, width=1, left=tick, color='black', edgecolor='white', height=0.6)

        for foto_estado in todas_fotos_do_tempo:
            tick = foto_estado.relogio_global
            for tf in getattr(foto_estado, 'tarefas_finalizadas', []):
                if tf.id not in tarefas_concluidas:
                    y_pos = mapa_y[tf.id]
                    self.ax.plot(tick, y_pos - 0.35, marker='X', color='#E74C3C', markersize=8)
                    tarefas_concluidas.add(tf.id)

        self.ax.xaxis.grid(True, linestyle='--', alpha=0.7)
        self.ax.set_axisbelow(True) 
        
        tick_maximo = max(10, estado_atual.relogio_global + 2)
        self.ax.set_xticks(range(0, tick_maximo + 1))
        self.ax.set_xlim(0, tick_maximo)

        legend_elements = [
            Line2D([0], [0], color='#2980B9', marker='v', linestyle='None', markersize=8, label='Início (v)'),
            Line2D([0], [0], color='#E74C3C', marker='X', linestyle='None', markersize=8, label='Término (X)'),
            Line2D([0], [0], color='#F39C12', marker='*', linestyle='None', markersize=8, label='Sorteiro (*)'),
            plt.Rectangle((0,0),1,1, facecolor="white", edgecolor="black", label='Fila de Prontos'),
            plt.Rectangle((0,0),1,1, facecolor="black", edgecolor="white", label='Suspensa'), 
        ]
        self.ax.legend(handles=legend_elements, loc='upper right', fontsize=7)

        self.canvas.draw()