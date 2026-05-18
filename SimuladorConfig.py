'''
CLASSE: SimuladorConfig

Atua como a entre a leitura dos dados (CarregarConfig) de um arquiivo .txt e o motor do simulador.
A responsabilidade desta classe é inicializar os parâmetros globais do sistema operacional 
(Algoritmo, Quantum, Quantidade de CPUs) e preparar a lista definitiva de tarefas e 
processadores físicos que serão entregues para a Engine rodar.
'''

from CarregarConfig import CarregarConfig
from TCB import TCB
from Estados import EstadosTarefa
from CPU import CPU

class SimuladorConfig:
    algoritmoEscalomento : str #algoritmo escolhido
    quantum: int #duração do quantum
    qtde_cpus: int #quantidade de cpus

    def __init__(self,txt: str):
        self.listaTarefasCarregadas = [] #lista de tarefas carregadas que sera usada pelo SimuladorEstado
        self.listaCPU = [] #lista de cpus que sera usado pelo SimuladorEstado
        configParse = CarregarConfig() #cria um objeto que lê o arquivo txt
        print(configParse.carregarArquivoTXT(txt)) #um print para saber se o arquivo foi lido com sucesso
        configParse.carregarParametros() # método para ler o arquivo txt
        configGeral = configParse.getConfigSim() # pega as configurações gerais
        self.algoritmoEscalomento = configGeral["algoritmo_escalonamento"]
        self.quantum = configGeral["quantum"]
        self.qtde_cpus = configGeral["qtde_cpus"]
        self.listaTarefasCarregadas = configParse.getlistaTarefas().copy()
        self.criarCPUS()  #método para criar a lista de cpu's iniciais
        
                   
    def criarCPUS(self): # método para criar a lista das cpus do sistema, levando em consideração o quantidade de cpus passada na configuração no txt
        i = 0
        while i< self.qtde_cpus:
            cpu = CPU(id= i,
                    )
            self.listaCPU.append(cpu)
            i += 1 