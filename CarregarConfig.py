from TCB import TCB

CORES_SUGESTAO = [
    "FF6B6B",  # vermelho suave
    "4ECDC4",  # verde-água
    "45B7D1",  # azul
    "F7B801",  # amarelo
    "A29BFE",  # roxo
    "FF8C42",  # laranja
    "2ECC71",  # verde
    "E84393",  # rosa
]

class CarregarConfig:
    f: object
    configSim: dict
    listTarefas : list[TCB]
    
    def __init__(self):
        self.f = None
        self.configSim = {"algoritmo_escalonamento" : "STFR", #Valores padrão de carregamento
                     "quantum": 2,
                     "qtde_cpus": 4
                    }
        self.listTarefas = [] 

    def carregarArquivoTXT(self,caminho: str): #função para abrir o arquivo e salvar na variavel da classe
        try:
            self.f = open(caminho,"r")
            return "arquivo aberto"
        except FileNotFoundError:
            return "arquivo não encontrado"
        except PermissionError:
            return "Sem permissão para abrir"
    
    
    def carregarParametros(self): #função para fazer o parser do arquivo txt
        try:
            for i, linhas in enumerate(self.f): #loop em todas as linhas do arquivo
                linhas = linhas.strip() #remove espaços
                if linhas: #testa a linha para ver se não é vazia
                    if i == 0:
                        conteudo = linhas.split(";") #faz uma lista com os elementos 
                        self.configSim.update({"algoritmo_escalonamento" : "STFR" if conteudo[0].upper() == "" else conteudo[0].upper(),
                                            "quantum": 2 if conteudo[1].upper() == "" else int(conteudo[1]),
                                                "qtde_cpus": 2 if conteudo[2].upper() == "" else int(conteudo[2])})
                    else:
                        conteudo = linhas.split(";") #configuraçao das tarefas
                        tarefa = TCB(
                            id = -1 if conteudo[0] == "" else int(conteudo[0]),
                            cor = conteudo[1],                        
                            tempoDeIngresso = -1 if conteudo[2] == "" else int(conteudo[2]),     
                            tempoTotal = -1 if conteudo[3] == "" else int(conteudo[3]),           
                            tempoCorrido = -1 if conteudo[3] == "" else int(conteudo[3]),       
                            prioridadeEstatica = -1 if conteudo[4] == "" else int(conteudo[4]),    
                            listaEvento = conteudo[5]               
                        )
                        self.listTarefas.append(tarefa)
            self.checarParametros(self.listTarefas) #chama a função para checar os parametros das tarefas e preencher os vazios
        except Exception as e:
            print(f"Erro ao carregar parâmetros: {e}")

        # Fecha o arquivo após o parse para evitar vazamento de descritor
        try:
            self.f.close()
        except Exception:
            pass
        

    def getConfigSim(self) -> dict: # Método que retorna as configurações do simulador
        return self.configSim
        
    def getlistaTarefas(self) -> list: # Método que retornar a lista de tarefas
        return self.listTarefas
    
    def checarParametros(self, T: list[TCB]):
        l_id: list[int] = []
        l_cor: list[str] = []
        for t in T:
            l_id.append(t.id)
            l_cor.append(t.cor)
        for t in T:
            if t.id == -1:
                t.id = max(l_id) + 1
                l_id.append(t.id)
            if t.cor == "":
                for cor in CORES_SUGESTAO:
                    if cor not in l_cor:
                        t.cor = cor
                        l_cor.append(cor)
                        break
            if t.tempoDeIngresso == -1:
                t.tempoDeIngresso = 0
            if t.tempoTotal == -1:
                t.tempoTotal = 10
                t.tempoCorrido = 10
            if t.prioridadeEstatica == -1:
                t.prioridadeEstatica = 5
            

        


#teste

def main():
    objcarregar = CarregarConfig()
    print(objcarregar.carregarArquivoTXT("config2.txt"))
    objcarregar.carregarParametros()
    print(objcarregar.listTarefas)
    
if __name__ == "__main__":
    main()
    