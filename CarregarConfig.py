
'''
CLASSE: CarregarConfig

Esse classe é responsavel por carregar as configurações do simulador a partir de um arquivo txt, fazer a separação e conferir se estão corretas
A descisão de usar uma classe pra carregar as configurações foi por modularizar o codigo e separa as responsabilidades
'''

import re

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
    f: object # Arquivo a ser carregado
    configSim: dict # Configuração do sistema
    listTarefas : list[TCB] # Tarefas carregadas do txt
    
    def __init__(self):
        self.f = None # Inicia o arquivo como none
        self.configSim = {"algoritmo_escalonamento" : "STFR", #Valores padrão de carregamento
                     "quantum": 2,
                     "qtde_cpus": 4
                    }
        self.listTarefas = [] # Inicia a lista vazia

    # Método para abrir o arquivo e salvar na variavel da classe
    def carregarArquivoTXT(self,caminho: str): 
        try: #try paraa tentar abrir o arquivo, caso haja algum erro, como arquivo não encontrado ou sem permissão, retorna a mensagem de erro
            self.f = open(caminho,"r")
            return "arquivo aberto"
        except FileNotFoundError:
            return "arquivo não encontrado"
        except PermissionError:
            return "Sem permissão para abrir"
    
    # Método para fazer o parser do arquivo txt
    def carregarParametros(self):
        try:
            for i, linhas in enumerate(self.f): # loop em todas as linhas do arquivo
                linhas = linhas.strip() # remove espaços
                if linhas: # testa a linha para ver se não é vazia
                    if i == 0:
                        conteudo = linhas.split(";") # faz uma lista com os elementos 
                        self.configSim.update({"algoritmo_escalonamento" : "STFR" if conteudo[0].upper() == "" else conteudo[0].upper(),
                                            "quantum": 2 if conteudo[1].upper() == "" else int(conteudo[1]),
                                                "qtde_cpus": 2 if conteudo[2].upper() == "" else int(conteudo[2])})
                    else:
                        conteudo = linhas.split(";") # faz uma lista com elementos separados por ":"
                        tarefa = TCB(
                            id = self.parsetarefaId(conteudo[0]), # trata as ids em especial, se a entrada for um número direto ou uma
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
        
    # Método que retorna as configurações do simulador
    def getConfigSim(self) -> dict: 
        return self.configSim
    
    # Método que retornar a lista de tarefas
    def getlistaTarefas(self) -> list: 
        return self.listTarefas

    # Método que faz um parse no id, pegando só a parte do número
    def parsetarefaId(self, valor: str) -> int:
        valor = valor.strip() #remove espaços em branco
        if valor == "": # se for vazio, retorna -1 para ser preenchido depois
            return -1
        if valor.isdigit(): # se for um número, retorna o número inteiro
            return int(valor)
        if not valor[0].isdigit(): # Se o  primeiro caractere não for um dígito, tenta extraior os digitgitos da entrada
            digits = re.findall(r"\d+", valor) #extrai todos os digitos de uma string
            if digits: #Se a entrada não for vazie e tiver digitos, retorna o númer inteiro formado pelos digitos
                return int("".join(digits)) #juntos os digitos encontrados e converve para inteiro
        raise ValueError(f"Id de tarefa invalido: '{valor}'. acresente algum número para que possa ser identificada.")
    
    # Método para checar os parametros das tarefas, preeencher os vazios com valores padrão ou sugerido e verificar por IDs repetidos
    def checarParametros(self, T: list[TCB]):
        l_id: list[int] = [] #lista para armazenar os ids já usados
        l_cor: list[str] = [] #lista para armazenar as cores já usadas
        
        # Verifica se existe id repetido
        for t in T:
            if t.id != -1: # Ignora as que vieram vazias (serão preenchidas no próximo laço)
                if t.id in l_id:
                    # Se o ID já estiver na lista, lança o erro interrompendo o carregamento!
                    raise ValueError(f"Arquivo inválido! O ID '{t.id}' está repetido no config.txt.")
                l_id.append(t.id) # Adiciona o id na lista de ids usados
            
            if t.cor != "":
                l_cor.append(t.cor) # Adiciona a cor na lista de cores usadas

        for t in T:
            if t.id == -1: #se o id da tarefa for -1, o id tava vazio, então atribui um id com base no maior id já usado + 1
                t.id = max(l_id) + 1 if l_id else 1
                l_id.append(t.id)
            if t.cor == "": # se a cor for vazia, atribui uma cor sugerida dos enum de cres
                for cor in CORES_SUGESTAO:
                    if cor not in l_cor:
                        t.cor = cor
                        l_cor.append(cor)
                        break
            if t.tempoDeIngresso == -1: # se o for tempo de ingresso vazio, atribui 0 
                t.tempoDeIngresso = 0
            if t.tempoTotal == -1: #se o tempo total for vazio, atribui 10 no total e no corrido
                t.tempoTotal = 10
                t.tempoCorrido = 10
            if t.prioridadeEstatica == -1: #se a prioridade estatica for vazia, atribui 5
                t.prioridadeEstatica = 5
            

