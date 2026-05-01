class CarregarConfig:
    f : object
    configSim: dict
    listTarefas : list
    
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
        for i, linhas in enumerate(self.f): #loop em todas as linhas do arquivo
            linhas = linhas.strip() #remove espaços
            if linhas: #testa a linha para ver se não é vazia
                if i == 0:
                    conteudo = linhas.split(";") #faz uma lista com os elementos 
                    self.configSim.update({"algoritmo_escalonamento" : conteudo[0].upper(), #configuração da simulação
                                           "quantum": int(conteudo[1]),
                                            "qtde_cpus": int(conteudo[2])})
                else:
                    conteudo = linhas.split(";") #configuraçao das tarefas
                    tarefa = {"id": int(conteudo[0]),
                            "cor": conteudo[1],
                            "ingresso": int(conteudo[2]),
                            "duracao": int(conteudo[3]),
                            "listaEvent": conteudo[4]}
                    self.listTarefas.append(tarefa)
        
    
            
#teste
'''
def main():
    objcarregar = CarregarConfig()
    print(objcarregar.carregarArquivoTXT("config.txt"))
    objcarregar.carregarParametros()
    print(objcarregar.listTarefas)
    print(objcarregar.configSim)
    
if __name__ == "__main__":
    main()
    
'''
    
