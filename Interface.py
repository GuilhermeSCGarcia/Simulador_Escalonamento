import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.lines import Line2D 

from SimuladorConfig import SimuladorConfig
from SimuladorEstado import SimuladorEstado
from SimuladorEngine import SimuladorEngine
from Estados import EstadosTarefa

class InterfaceSimulador:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Escalonamento de SO")
        self.root.geometry("1600x900")
        self.root.configure(bg="#F0F0F0") 

        self.engine: SimuladorEngine = None
        self.mapa_tarefas = {} # Dicionário para mapear a linha clicada na tabela para o objeto TCB real

        self.criar_widgets()

    def criar_widgets(self):
        # --- PAINEL LATERAL ---
        self.frame_controles = tk.Frame(self.root, width=300, bg="#2C3E50", padx=20, pady=20)
        self.frame_controles.pack(side=tk.LEFT, fill=tk.Y)
        self.frame_controles.pack_propagate(False) 

        tk.Label(self.frame_controles, text="Painel de Controle", font=("Helvetica", 18, "bold"), bg="#2C3E50", fg="white").pack(pady=(0, 20))

        self.btn_carregar = tk.Button(self.frame_controles, text="Carregar config.txt", font=("Helvetica", 12), bg="#27AE60", fg="white", relief="flat", command=self.carregar_arquivo)
        self.btn_carregar.pack(fill=tk.X, pady=10)

        self.lbl_info = tk.Label(self.frame_controles, text="Nenhuma configuração carregada.", font=("Helvetica", 10), bg="#2C3E50", fg="#BDC3C7", justify=tk.LEFT)
        self.lbl_info.pack(anchor="w", pady=10)

        self.frame_status = tk.Frame(self.frame_controles, bg="#34495E", padx=10, pady=10)
        self.frame_status.pack(fill=tk.X, pady=20)

        self.lbl_relogio = tk.Label(self.frame_status, text="Tick Atual: 0", font=("Courier", 14, "bold"), bg="#34495E", fg="#F1C40F")
        self.lbl_relogio.pack(anchor="w")

        self.lbl_prontos = tk.Label(self.frame_status, text="Fila de Prontos: []", font=("Helvetica", 10), bg="#34495E", fg="white", wraplength=240, justify=tk.LEFT)
        self.lbl_prontos.pack(anchor="w", pady=(10,0))

        self.lbl_futuras = tk.Label(self.frame_status, text="Tarefas Futuras: []", font=("Helvetica", 10), bg="#34495E", fg="#95A5A6", wraplength=240, justify=tk.LEFT)
        self.lbl_futuras.pack(anchor="w", pady=(10,0))

        tk.Label(self.frame_controles, text="Controles de Tempo", font=("Helvetica", 12, "bold"), bg="#2C3E50", fg="white").pack(anchor="w", pady=(20, 5))

        self.btn_avancar = tk.Button(self.frame_controles, text="Avançar Tick (+1)", font=("Helvetica", 11), bg="#2980B9", fg="white", relief="flat", state=tk.DISABLED, command=self.acao_avancar)
        self.btn_avancar.pack(fill=tk.X, pady=5)

        self.btn_retroceder = tk.Button(self.frame_controles, text="Voltar Tick (-1)", font=("Helvetica", 11), bg="#E67E22", fg="white", relief="flat", state=tk.DISABLED, command=self.acao_retroceder)
        self.btn_retroceder.pack(fill=tk.X, pady=5)

        self.btn_executar_tudo = tk.Button(self.frame_controles, text="Executar Até o Fim", font=("Helvetica", 11), bg="#8E44AD", fg="white", relief="flat", state=tk.DISABLED, command=self.acao_executar_tudo)
        self.btn_executar_tudo.pack(fill=tk.X, pady=5)

        tk.Label(self.frame_controles, text="Exportação", font=("Helvetica", 12, "bold"), bg="#2C3E50", fg="white").pack(anchor="w", pady=(20, 5))
        self.btn_exportar = tk.Button(self.frame_controles, text="Exportar Gráfico (.PNG)", font=("Helvetica", 11), bg="#7F8C8D", fg="white", relief="flat", state=tk.DISABLED, command=self.acao_exportar)
        self.btn_exportar.pack(fill=tk.X, pady=5)

        # --- PAINEL DIREITO (Gráfico + Tabela) ---
        self.frame_direito = tk.Frame(self.root, bg="white")
        self.frame_direito.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Matplotlib no topo
        self.frame_grafico = tk.Frame(self.frame_direito, bg="white")
        self.frame_grafico.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.fig.patch.set_facecolor('#F8F9FA') 
        self.ax.set_facecolor('#FFFFFF')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_grafico)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=20, pady=(20, 0))

        # --- NOVA TABELA DE EDIÇÃO MANUAL (Requisito 1.5.2b e 3.4) ---
        self.frame_tabela = tk.Frame(self.frame_direito, bg="white", height=150)
        self.frame_tabela.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)
        
        tk.Label(self.frame_tabela, text="Editor de Tarefas (Dê um duplo clique em uma tarefa para editá-la)", font=("Helvetica", 10, "bold"), bg="white", fg="#2C3E50").pack(anchor="w", pady=(0,5))

        colunas = ("ID", "Estado", "Tempo Restante", "Prioridade Estática", "Tempo de Ingresso")
        self.tree = ttk.Treeview(self.frame_tabela, columns=colunas, show='headings', height=5)
        for col in colunas:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Vincula o evento de duplo clique à função de edição
        self.tree.bind("<Double-1>", self.acao_editar_tarefa)

        self.desenhar_gantt_vazio()


    def carregar_arquivo(self):
        filepath = filedialog.askopenfilename(title="Selecione o arquivo config.txt", filetypes=[("Text Files", "*.txt")])
        if not filepath:
            return

        try:
            config = SimuladorConfig(filepath)
            estado_inicial = SimuladorEstado(config.listaCPU, config.listaTarefasCarregadas)
            self.engine = SimuladorEngine(config, estado_inicial)

            self.lbl_info.config(text=f"Algoritmo: {config.algoritmoEscalomento}\nCPUs: {config.qtde_cpus}\nTarefas carregadas: {len(config.listaTarefasCarregadas)}")
            
            self.btn_avancar.config(state=tk.NORMAL)
            self.btn_retroceder.config(state=tk.NORMAL)
            self.btn_executar_tudo.config(state=tk.NORMAL)
            self.btn_exportar.config(state=tk.NORMAL)

            self.atualizar_tela()
            messagebox.showinfo("Sucesso", "Configuração carregada com sucesso!")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao ler o arquivo:\n{str(e)}")

    def acao_avancar(self):
        if self.engine.estado_atual.simulacao_finalizada():
            messagebox.showinfo("Fim", "A simulação já foi finalizada!")
            return
        self.engine.avancar_tick()
        self.atualizar_tela()

    def acao_retroceder(self):
        if len(self.engine.historico_estados) == 0:
            messagebox.showwarning("Aviso", "Já estamos no tick 0!")
            return
        self.engine.retroceder_tick()
        self.atualizar_tela()

    def acao_executar_tudo(self):
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

    def acao_editar_tarefa(self, event):
        # Impede edição se não houver simulação carregada
        if not self.engine: return

        selecao = self.tree.selection()
        if not selecao: return
        
        item_id = selecao[0]
        tarefa = self.mapa_tarefas.get(item_id)
        
        if not tarefa: return
        
        # Se a tarefa já acabou, não faz sentido editar
        if tarefa.estado.name == "FINALIZADO":
            messagebox.showwarning("Aviso", "Esta tarefa já foi finalizada e não pode ser editada.")
            return

        # Abre a janela popup de edição
        win = tk.Toplevel(self.root)
        win.title(f"Editar Tarefa T{tarefa.id}")
        win.geometry("300x320") # Aumentei um pouco a altura
        win.configure(bg="#ECF0F1")
        win.wait_visibility()
        win.grab_set()

        tk.Label(win, text=f"Editando Tarefa T{tarefa.id}", font=("Helvetica", 12, "bold"), bg="#ECF0F1").pack(pady=15)

        tk.Label(win, text="Tempo Restante (Ticks):", bg="#ECF0F1").pack()
        entry_tempo = tk.Entry(win, justify='center')
        entry_tempo.insert(0, str(tarefa.tempoCorrido))
        entry_tempo.pack(pady=(0, 10))

        tk.Label(win, text="Prioridade Estática:", bg="#ECF0F1").pack()
        entry_prio = tk.Entry(win, justify='center')
        entry_prio.insert(0, str(tarefa.prioridadeEstatica))
        entry_prio.pack(pady=(0, 15))

        # Variável para controlar se vamos suspender ou acordar a tarefa
        esta_suspensa = tarefa in self.engine.estado_atual.fila_suspensas

        def alternar_suspensao():
            estado_atual = self.engine.estado_atual
            
            if esta_suspensa:
                # Acordar: Tira da fila de suspensas e joga na de prontos
                estado_atual.fila_suspensas.remove(tarefa)
                estado_atual.fila_prontos.append(tarefa)
                tarefa.estado = EstadosTarefa.PRONTO
                messagebox.showinfo("Sucesso", f"Tarefa T{tarefa.id} foi Despertada (Pronta)!")
            else:
                # Suspender: Remove de onde estiver e joga na fila de suspensas
                if tarefa in estado_atual.fila_prontos:
                    estado_atual.fila_prontos.remove(tarefa)
                for cpu in estado_atual.cpus:
                    if cpu.atualTarefa == tarefa:
                        cpu.atualTarefa = None
                        
                estado_atual.fila_suspensas.append(tarefa)
                tarefa.estado = EstadosTarefa.BLOQUEADO
                messagebox.showinfo("Sucesso", f"Tarefa T{tarefa.id} foi Suspensa!")
            
            self.atualizar_tela()
            win.destroy()

        texto_botao_suspender = "Despertar Tarefa" if esta_suspensa else "Suspender Tarefa"
        cor_botao_suspender = "#F39C12" if esta_suspensa else "#E74C3C"
        
        tk.Button(win, text=texto_botao_suspender, bg=cor_botao_suspender, fg="white", font=("Helvetica", 10, "bold"), relief="flat", command=alternar_suspensao).pack(pady=(0, 10))

        def salvar_alteracoes():
            try:
                novo_tempo = int(entry_tempo.get())
                nova_prio = int(entry_prio.get())
                tarefa.tempoCorrido = novo_tempo
                tarefa.prioridadeEstatica = nova_prio
                self.atualizar_tela()
                win.destroy()
                messagebox.showinfo("Sucesso", f"Tarefa T{tarefa.id} atualizada!")
            except ValueError:
                messagebox.showerror("Erro", "Insira apenas números inteiros válidos.")

        tk.Button(win, text="Salvar Valores", bg="#27AE60", fg="white", font=("Helvetica", 10, "bold"), relief="flat", command=salvar_alteracoes).pack()


    def atualizar_tela(self):
        estado = self.engine.estado_atual
        
        self.lbl_relogio.config(text=f"Tick Atual: {estado.relogio_global}")
        
        prontos_str = ", ".join([f"T{t.id}" for t in estado.fila_prontos])
        futuras_str = ", ".join([f"T{t.id}" for t in estado.tarefas_futuras])
        
        self.lbl_prontos.config(text=f"Fila de Prontos: [{prontos_str}]")
        self.lbl_futuras.config(text=f"Tarefas Futuras: [{futuras_str}]")

        # Atualiza a tabela com o estado de todas as tarefas
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        self.mapa_tarefas.clear()
        
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
            self.mapa_tarefas[linha_id] = t # Guarda a referência do objeto para poder editar

        self.desenhar_gantt()

    def desenhar_gantt_vazio(self):
        self.ax.clear()
        self.ax.set_title("Gráfico de Gantt - Aguardando Configuração", fontsize=14, fontweight="bold", color="#2C3E50")
        self.ax.set_xlabel("Tempo (Ticks)")
        self.ax.set_yticks([])
        self.canvas.draw()

    def desenhar_gantt(self):
        self.ax.clear()

        estado_atual = self.engine.estado_atual
        todas_fotos_do_tempo = self.engine.historico_estados[1:] + [estado_atual]

        todas_tarefas = self.engine.config.listaTarefasCarregadas
        tarefas_ordenadas = sorted(todas_tarefas, key=lambda t: t.id)
        nomes_tarefas = [f"Tarefa {t.id}" for t in tarefas_ordenadas]
        posicoes_y = list(range(len(tarefas_ordenadas)))
        mapa_y = {t.id: y for t, y in zip(tarefas_ordenadas, posicoes_y)}

        self.ax.set_yticks(posicoes_y)
        self.ax.set_yticklabels(nomes_tarefas, fontweight="bold", color="#34495E")
        self.ax.set_xlabel("Tempo (Ticks)", fontweight="bold", color="#34495E")
        self.ax.set_title(f"Execução - {self.engine.config.algoritmoEscalomento}", fontsize=14, fontweight="bold", color="#2C3E50")

        tarefas_iniciadas = set()
        tarefas_concluidas = set()

        for tick, foto_estado in enumerate(todas_fotos_do_tempo):
            
            for cpu in foto_estado.cpus:
                tarefa = cpu.atualTarefa
                if tarefa is not None:
                    y_pos = mapa_y[tarefa.id]
                    cor_hex = f"#{tarefa.cor}" if not tarefa.cor.startswith('#') else tarefa.cor
                    self.ax.barh(y=y_pos, width=1, left=tick, color=cor_hex, edgecolor='black', height=0.6)
                    self.ax.text(tick + 0.5, y_pos, f"CPU {cpu.id}", ha='center', va='center', color='black', fontweight='bold', fontsize=9)

            for tarefa_pronta in foto_estado.fila_prontos:
                y_pos = mapa_y[tarefa_pronta.id]
                self.ax.barh(y=y_pos, width=1, left=tick, color='white', edgecolor='black', height=0.6)

            for t in tarefas_ordenadas:
                if tick == t.tempoDeIngresso and t.id not in tarefas_iniciadas:
                    y_pos = mapa_y[t.id]
                    self.ax.plot(tick, y_pos + 0.35, marker='v', color='#2980B9', markersize=8) 
                    tarefas_iniciadas.add(t.id)

                if any(tf.id == t.id for tf in foto_estado.tarefas_finalizadas) and t.id not in tarefas_concluidas:
                    y_pos = mapa_y[t.id]
                    self.ax.plot(tick, y_pos - 0.35, marker='X', color='#E74C3C', markersize=8) 
                    tarefas_concluidas.add(t.id)

            for tarefa_suspensa in getattr(foto_estado, 'fila_suspensas', []):
                y_pos = mapa_y[tarefa_suspensa.id]
                # Requisito 2.1c: Tarefa suspensa com cor preta
                self.ax.barh(y=y_pos, width=1, left=tick, color='black', edgecolor='white', height=0.6)

        self.ax.xaxis.grid(True, linestyle='--', alpha=0.7)
        self.ax.set_axisbelow(True) 
        
        tick_maximo = max(10, estado_atual.relogio_global + 2)
        self.ax.set_xticks(range(0, tick_maximo + 1))
        self.ax.set_xlim(0, tick_maximo)

        legend_elements = [
            Line2D([0], [0], color='#2980B9', marker='v', linestyle='None', markersize=8, label='Chegada (*)*'),
            Line2D([0], [0], color='#E74C3C', marker='X', linestyle='None', markersize=8, label='Término (X)'),
            plt.Rectangle((0,0),1,1, facecolor="white", edgecolor="black", label='Fila de Prontos'),
            plt.Rectangle((0,0),1,1, facecolor="black", edgecolor="white", label='Suspensa') # <--- NOVO ITEM NA LEGENDA
        ]
        self.ax.legend(handles=legend_elements, loc='upper right', fontsize=9)

        self.canvas.draw()