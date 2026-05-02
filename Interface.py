import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from SimuladorConfig import SimuladorConfig
from SimuladorEstado import SimuladorEstado
from SimuladorEngine import SimuladorEngine

class InterfaceSimulador:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Escalonamento de SO")
        self.root.geometry("1600x900")
        self.root.configure(bg="#F0F0F0") # Fundo cinza claro

        self.engine: SimuladorEngine = None

        self.criar_widgets()

    def criar_widgets(self):
        # --- PAINEL LATERAL ---
        self.frame_controles = tk.Frame(self.root, width=300, bg="#2C3E50", padx=20, pady=20)
        self.frame_controles.pack(side=tk.LEFT, fill=tk.Y)
        self.frame_controles.pack_propagate(False) # Impede que o frame encolha

        # Título Lateral
        tk.Label(self.frame_controles, text="Painel de Controle", font=("Helvetica", 18, "bold"), bg="#2C3E50", fg="white").pack(pady=(0, 20))

        # Botão de Carregar Arquivo
        self.btn_carregar = tk.Button(self.frame_controles, text="Carregar config.txt", font=("Helvetica", 12), bg="#27AE60", fg="white", relief="flat", command=self.carregar_arquivo)
        self.btn_carregar.pack(fill=tk.X, pady=10)

        # Informações do Sistema
        self.lbl_info = tk.Label(self.frame_controles, text="Nenhuma configuração carregada.", font=("Helvetica", 10), bg="#2C3E50", fg="#BDC3C7", justify=tk.LEFT)
        self.lbl_info.pack(anchor="w", pady=10)

        # Painel de Filas (Status)
        self.frame_status = tk.Frame(self.frame_controles, bg="#34495E", padx=10, pady=10)
        self.frame_status.pack(fill=tk.X, pady=20)

        self.lbl_relogio = tk.Label(self.frame_status, text="Tick Atual: 0", font=("Courier", 14, "bold"), bg="#34495E", fg="#F1C40F")
        self.lbl_relogio.pack(anchor="w")

        self.lbl_prontos = tk.Label(self.frame_status, text="Fila de Prontos: []", font=("Helvetica", 10), bg="#34495E", fg="white", wraplength=240, justify=tk.LEFT)
        self.lbl_prontos.pack(anchor="w", pady=(10,0))

        self.lbl_futuras = tk.Label(self.frame_status, text="Tarefas Futuras: []", font=("Helvetica", 10), bg="#34495E", fg="#95A5A6", wraplength=240, justify=tk.LEFT)
        self.lbl_futuras.pack(anchor="w", pady=(10,0))

        # Botões de Ação do Tempo
        tk.Label(self.frame_controles, text="Controles de Tempo", font=("Helvetica", 12, "bold"), bg="#2C3E50", fg="white").pack(anchor="w", pady=(20, 5))

        self.btn_avancar = tk.Button(self.frame_controles, text="Avançar Tick (+1)", font=("Helvetica", 11), bg="#2980B9", fg="white", relief="flat", state=tk.DISABLED, command=self.acao_avancar)
        self.btn_avancar.pack(fill=tk.X, pady=5)

        self.btn_retroceder = tk.Button(self.frame_controles, text="Voltar Tick (-1)", font=("Helvetica", 11), bg="#E67E22", fg="white", relief="flat", state=tk.DISABLED, command=self.acao_retroceder)
        self.btn_retroceder.pack(fill=tk.X, pady=5)

        self.btn_executar_tudo = tk.Button(self.frame_controles, text="Executar Até o Fim", font=("Helvetica", 11), bg="#8E44AD", fg="white", relief="flat", state=tk.DISABLED, command=self.acao_executar_tudo)
        self.btn_executar_tudo.pack(fill=tk.X, pady=5)

        # --- PAINEL DO GRÁFICO (DIREITA) ---
        self.frame_grafico = tk.Frame(self.root, bg="white")
        self.frame_grafico.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Configuração do Matplotlib
        self.fig, self.ax = plt.subplots(figsize=(8, 5))
        self.fig.patch.set_facecolor('#F8F9FA') # Cor de fundo do gráfico
        self.ax.set_facecolor('#FFFFFF')
        
        # Conecta o Matplotlib dentro do Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_grafico)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.desenhar_gantt_vazio()


    def carregar_arquivo(self):
        # Abre a janela para o usuário escolher o config.txt
        filepath = filedialog.askopenfilename(title="Selecione o arquivo config.txt", filetypes=[("Text Files", "*.txt")])
        if not filepath:
            return

        try:
            # Integração com o simulador!
            config = SimuladorConfig(filepath)
            estado_inicial = SimuladorEstado(config.listaCPU, config.listaTarefasCarregadas)
            self.engine = SimuladorEngine(config, estado_inicial)

            # Atualiza textos da interface
            self.lbl_info.config(text=f"Algoritmo: {config.algoritmoEscalomento}\nCPUs: {config.qtde_cpus}\nTarefas carregadas: {len(config.listaTarefasCarregadas)}")
            
            # Habilita os botões
            self.btn_avancar.config(state=tk.NORMAL)
            self.btn_retroceder.config(state=tk.NORMAL)
            self.btn_executar_tudo.config(state=tk.NORMAL)

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

    def atualizar_tela(self):
        estado = self.engine.estado_atual
        
        # Atualiza os textos
        self.lbl_relogio.config(text=f"Tick Atual: {estado.relogio_global}")
        
        # Formata as listas para mostrar apenas T1, T2, etc.
        prontos_str = ", ".join([f"T{t.id}" for t in estado.fila_prontos])
        futuras_str = ", ".join([f"T{t.id}" for t in estado.tarefas_futuras])
        
        self.lbl_prontos.config(text=f"Fila de Prontos: [{prontos_str}]")
        self.lbl_futuras.config(text=f"Tarefas Futuras: [{futuras_str}]")

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

        # Configurações do eixo Y (As CPUs)
        nomes_cpus = [f"CPU {cpu.id}" for cpu in estado_atual.cpus]
        posicoes_y = [cpu.id for cpu in estado_atual.cpus]

        self.ax.set_yticks(posicoes_y)
        self.ax.set_yticklabels(nomes_cpus, fontweight="bold", color="#34495E")
        self.ax.set_xlabel("Tempo (Ticks)", fontweight="bold", color="#34495E")
        self.ax.set_title(f"Execução - {self.engine.config.algoritmoEscalomento}", fontsize=14, fontweight="bold", color="#2C3E50")

        # O Loop Mágico: Olha para o passado e desenha os blocos!
        for tick, foto_estado in enumerate(todas_fotos_do_tempo):
            for cpu in foto_estado.cpus:
                tarefa = cpu.atualTarefa
                if tarefa is not None:
                    # Formata a cor (adiciona o # se faltar)
                    cor_hex = f"#{tarefa.cor}" if not tarefa.cor.startswith('#') else tarefa.cor
                    
                    # Desenha o retângulo da tarefa
                    self.ax.barh(y=cpu.id, width=1, left=tick, color=cor_hex, edgecolor='black', height=0.6)
                    
                    # Escreve o ID da tarefa no meio do bloco
                    self.ax.text(tick + 0.5, cpu.id, f"T{tarefa.id}", ha='center', va='center', color='black', fontweight='bold', fontsize=9)

        # Ajustes de grade e visual
        self.ax.xaxis.grid(True, linestyle='--', alpha=0.7)
        self.ax.set_axisbelow(True) # Coloca a grade atrás das barras
        
        # Mostra ticks inteiros no eixo X
        tick_maximo = max(10, estado_atual.relogio_global + 2)
        self.ax.set_xticks(range(0, tick_maximo + 1))
        self.ax.set_xlim(0, tick_maximo)

        # Atualiza a tela do matplotlib
        self.canvas.draw()