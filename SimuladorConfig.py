from CarregarConfig import CarregarConfig
from TCB import TCB
from Estados import EstadosTarefa
from CPU import CPU

#Essa classe carrega as configurações iniciais do simulador, usa a classe CarregarConfig, que lê o arquivo de texto
class SimuladorConfig:
    algoritmoEscalomento : str #algoritmo escolhido
    quantum: int #duração do quantum
    qtde_cpus: int #quantidade de cpus
    listaTarefasCarregadas: list = [] #lista de tarefas carregadas, representa o estado inicial das tarefas
    listaCPU: list = [] #lista das cpus criadas, representa o estado inicial das cpus

    def __init__(self,txt: str):
        configParse = CarregarConfig() #cria um objeto que lê o arquivo txt
        print(configParse.carregarArquivoTXT(txt)) #um print para saber se o arquivo foi lido com sucesso
        configParse.carregarParametros() # método para ler o arquivo txt
        configGeral = configParse.getConfigSim() # pega as configurações gerais
        self.algoritmoEscalomento = configGeral["algoritmo_escalonamento"]
        self.quantum = configGeral["quantum"]
        self.qtde_cpus = configGeral["qtde_cpus"]
        self.carregarTarefas(configParse.getlistaTarefas()) #método para carregar a lista de tarefas inicias
        self.criarCPUS()  #método para criar a lista de cpu's iniciais
        
    def carregarTarefas(self,listaTarefas: list): # método para carregar as tarefas, para cada tarefa atribui-se uma TCB
        self.listaTarefasCarregadas = listaTarefas.copy()  
                   
    def criarCPUS(self): # método para criar a lista das cpus do sistema, levando em consideração o quantidade de cpus passada na configuração no txt
        i = 0
        while i< self.qtde_cpus:
            cpu = CPU(id= i,
                    )
            self.listaCPU.append(cpu)
            i += 1 