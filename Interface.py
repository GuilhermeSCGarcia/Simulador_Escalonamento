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
        self.frame_controles = tk.Frame(self.root, width=300, bg="#2C3E50", padx=20, pady=20) #configura a coluna da esquerda, onde ficam os controles, e a cor de fundo
        self.frame_controles.pack(side=tk.LEFT, fill=tk.Y) #preenche na região da esquerda, com altura total da janela
        self.frame_controles.pack_propagate(False) #impede que o autoajuste do frame mude o tamanho definidos

        #Texto para configurar o painel de controle
        tk.Label(self.frame_controles, text="Painel de Controle", font=("Helvetica", 18, "bold"), bg="#2C3E50", fg="white").pack(pady=(0, 20))

        #Botão para carregar o arquivo txt
        self.btn_carregar = tk.Button(self.frame_controles, text="Carregar config.txt", font=("Helvetica", 12), bg="#27AE60", fg="white", relief="flat", command=self.carregar_arquivo)
        self.btn_carregar.pack(fill=tk.X, pady=10)
        
        #Mensagem para mostrar que não tem configuração carregada
        self.lbl_info = tk.Label(self.frame_controles, text="Nenhuma configuração carregada.", font=("Helvetica", 10), bg="#2C3E50", fg="#BDC3C7", justify=tk.LEFT)
        self.lbl_info.pack(anchor="w", pady=10)
        
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
        
        #Botão de anvançar tick
        self.btn_avancar = tk.Button(self.frame_controles, text="Avançar Tick (+1)", font=("Helvetica", 11), bg="#2980B9", fg="white", relief="flat", state=tk.DISABLED, command=self.acao_avancar)
        self.btn_avancar.pack(fill=tk.X, pady=5)

        #Botão de retroceder tick
        self.btn_retroceder = tk.Button(self.frame_controles, text="Voltar Tick (-1)", font=("Helvetica", 11), bg="#E67E22", fg="white", relief="flat", state=tk.DISABLED, command=self.acao_retroceder)
        self.btn_retroceder.pack(fill=tk.X, pady=5)

        #Botão de executar tudo
        self.btn_executar_tudo = tk.Button(self.frame_controles, text="Executar Até o Fim", font=("Helvetica", 11), bg="#8E44AD", fg="white", relief="flat", state=tk.DISABLED, command=self.acao_executar_tudo)
        self.btn_executar_tudo.pack(fill=tk.X, pady=5)

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

        self.fig, self.ax = plt.subplots(figsize=(8, 4)) #configuração do gráfico para ser integrado ao tk, junto com seu frame de destaque
        self.fig.patch.set_facecolor('#F8F9FA') 
        self.ax.set_facecolor('#FFFFFF')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_grafico) #integração do gráfico com o tk, usando o frame do gráfico como destaque
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=20, pady=(20, 0))

        # Tabela no rodapé
        self.frame_tabela = tk.Frame(self.frame_direito, bg="white", height=150) #frame do editor de tarefa
        self.frame_tabela.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)
        
        tk.Label(self.frame_tabela, text="Editor de Tarefas (Dê um duplo clique em uma tarefa para editá-la)", font=("Helvetica", 10, "bold"), bg="white", fg="#2C3E50").pack(anchor="w", pady=(0,5))

        #colunas para o nome das tabelas:
        #id é o identificador da tarefa
        #estado é o estado da tarefa no programa
        #tempo restante é o tempo que falta para a tarefa finalizar
        #tempo de ingresso é o tempo que ela entra no programa

        colunas = ("ID", "Estado", "Tempo Restante", "Prioridade Estática", "Tempo de Ingresso") #colunas da tabelas

        self.tree = ttk.Treeview(self.frame_tabela, columns=colunas, show='headings', height=5)   #configura a tabela indicando as colunas , com altura máxima de 5
        for col in colunas:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")
        # Empacota a tabela e a barra de rolagem lado a lado para que a rolagem funcione
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll_y = ttk.Scrollbar(self.frame_tabela, orient="vertical", command=self.tree.yview) #barra para conseguir rolar as tarefas, caso elas passem de 5
        self.tree.configure(yscrollcommand=scroll_y.set) #configuração da barra de rolagem
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Vincula o evento de duplo clique à função de edição
        self.tree.bind("<Double-1>", self.acao_editar_tarefa)
        #desenha o gráfico vazio 
        self.desenhar_gantt_vazio()


    def carregar_arquivo(self):
        filepath = filedialog.askopenfilename(title="Selecione o arquivo config.txt", filetypes=[("Text Files", "*.txt")])
        if not filepath:
            return

        try:
            #tenta abrir o arquivo txt com a classe SimuladorConfig, usado para processar os arquivos de forma mais fácil
            config = SimuladorConfig(filepath)
            
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
            
            #ativa os botões para funcionar apos carregar as configurações
            self.btn_avancar.config(state=tk.NORMAL)
            self.btn_retroceder.config(state=tk.NORMAL)
            self.btn_executar_tudo.config(state=tk.NORMAL)
            self.btn_exportar.config(state=tk.NORMAL)

            self.atualizar_tela() #atualiza a tela com as informações inciais
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
        if len(self.engine.historico_estados) <= 1:
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
                # Acordar: usar o novo método sincronizado
                estado_atual.acordar_tarefa(tarefa)
                messagebox.showinfo("Sucesso", f"Tarefa T{tarefa.id} foi Despertada (Pronta)!")
            else:
                # Suspender: usar o novo método sincronizado
                estado_atual.suspender_tarefa(tarefa)
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
                
                # Validação: tempo não pode ser negativo
                if novo_tempo < 0:
                    messagebox.showerror("Erro", "O tempo restante não pode ser negativo.")
                    return
                
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
        #Pega o estado atual para mostrar a serie de tempo
        estado_atual = self.engine.estado_atual
        
        #ppega todas as fotos de tempo para mostrar a serie de tempo, e se não tiver nenhuma serie ele pega apenas o estado atual
        todas_fotos_do_tempo = list(self.engine.historico_estados)
        if len(todas_fotos_do_tempo) == 0:
            todas_fotos_do_tempo = [estado_atual]
        else:
            # Substitui o último snapshot pelo estado atual (mesmo tick), para refletir edições
            if todas_fotos_do_tempo[-1].relogio_global == estado_atual.relogio_global:
                todas_fotos_do_tempo[-1] = estado_atual
            else:
                todas_fotos_do_tempo.append(estado_atual)
        
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
                    self.ax.text(tick + 0.5, y_pos, f"CPU {cpu.id}\nq:{cpu.atualTarefa.quatum_dado}", ha='center', va='center', color='black', fontweight='bold', fontsize=9)

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
        self.ax.legend(handles=legend_elements, loc='upper right', fontsize=9)

        self.canvas.draw()