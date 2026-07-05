
'''
CLASSE: CarregarConfig

Esse classe é responsavel por carregar as configurações do simulador a partir de um arquivo txt, fazer a separação e conferir se estão corretas
A descisão de usar uma classe pra carregar as configurações foi por modularizar o codigo e separa as responsabilidades
'''

import re

from TCB import TCB, EventoTarefa

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
        self.configSim = {"algoritmo_escalonamento" : "SRTF", #Valores padrão de carregamento
                     "quantum": 2,
                     "qtde_cpus": 4,
                     "alpha": 1
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

                if not linhas:
                    continue
                
                numero_linha = i + 1
                conteudo = linhas.split(";")
                algoritmo = "SRTF" if conteudo[0].upper() == "" else conteudo[0].upper()

                if i == 0:
                    if algoritmo == "PRIOPENV":
                        if len(conteudo) != 4:
                            raise ValueError(
                                f"Erro na linha {numero_linha}: para o algoritmo PRIOPEnv, a primeira linha deve ter o formato "
                                "'PRIOPEnv;QUANTUM;CPUS;ALPHA'. Exemplo: PRIOPEnv;5;2;1"
                            )
                    elif len(conteudo) != 3:
                        raise ValueError(
                            f"Erro na linha {numero_linha}: a primeira linha deve ter o formato "
                            "'ALGORITMO;QUANTUM;CPUS'. Exemplo: SRTF;2;2"
                        )
                    self.configSim.update({
                        "algoritmo_escalonamento": "SRTF" if conteudo[0].upper() == "" else conteudo[0].upper(),
                        "quantum": 2 if conteudo[1].upper() == "" else int(conteudo[1]),
                        "qtde_cpus": 2 if conteudo[2].upper() == "" else int(conteudo[2]),
                        "alpha": 1 if len(conteudo) == 3 or conteudo[3] == "" else int(conteudo[3])
                    })
                else:
                    if len(conteudo) < 5:
                        raise ValueError(
                            f"Erro na linha {numero_linha}: cada tarefa deve ter 6 campos separados por ponto e vírgula.\n"
                            "Formato esperado: id;cor;tempoDeIngresso;tempoTotal;prioridade;listaEventos\n"
                            "Exemplo: 1;FF6B6B;0;10;3;[]"
                        )
                    
                    texto_eventos = ";".join(conteudo[5:]) if len(conteudo) > 5 else ""

                    tarefa = TCB(
                        id = self.parsetarefaId(conteudo[0]), # trata as ids em especial, se a entrada for um número direto ou uma
                        cor = conteudo[1],                        
                        tempoDeIngresso = -1 if conteudo[2] == "" else int(conteudo[2]),     
                        tempoTotal = -1 if conteudo[3] == "" else int(conteudo[3]),           
                        tempoCorrido = -1 if conteudo[3] == "" else int(conteudo[3]),       
                        prioridadeEstatica = -1 if conteudo[4] == "" else int(conteudo[4]),    
                        listaEvento = self.parseListaEventos(texto_eventos, numero_linha)             
                    )

                    self.listTarefas.append(tarefa)

            self.checarParametros(self.listTarefas) #chama a função para checar os parametros das tarefas e preencher os vazios

        finally:
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
                t.id = max(l_id) + 1 if l_id else 0
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
            if t.prioridadeEstatica == -1: # se a prioridade estatica for vazia, atribui 5
                t.prioridadeEstatica = 5
        

    # Método para pegar o valor passado no txt e transformar e uma litsa de EventoTarefa
    def parseListaEventos(self, valor: str, numero_linha: int) -> list[EventoTarefa]:
        valor = valor.strip().upper()

        if valor == "" or valor == "[]":
            return []

        if valor.startswith("[") or valor.endswith("]"):
            if not (valor.startswith("[") and valor.endswith("]")):
                raise ValueError(
                    f"Erro na linha {numero_linha}: lista de eventos com colchetes inválidos. "
                    "Use ML01:00;MU01:05;IO:02-03 ou [ML01:00,MU01:05,IO:02-03]."
                )

            valor = valor[1:-1].strip()

        if valor == "":
            return []

        eventos: list[EventoTarefa] = []

        padrao_evento = re.compile(r"(ML|MU)(\d+):(\d+)|IO:(\d+)-(\d+)")

        posicao_atual = 0

        for ordem, resultado in enumerate(padrao_evento.finditer(valor)):
            texto_entre_eventos = valor[posicao_atual:resultado.start()]

            if re.fullmatch(r"[\s,;]*", texto_entre_eventos) is None:
                raise ValueError(
                    f"Erro na linha {numero_linha}: trecho inválido na lista de eventos: '{texto_entre_eventos}'. "
                    "Formatos esperados: MLxx:tempo, MUxx:tempo ou IO:tempo-duracao."
                )

            if resultado.group(1) is not None:
                tipo = resultado.group(1)
                mutex_id = int(resultado.group(2))
                tempo = int(resultado.group(3))

                eventos.append(EventoTarefa(
                    tipo=tipo,
                    mutex_id=mutex_id,
                    tempo=tempo,
                    ordem=ordem
                ))
            else:
                tempo = int(resultado.group(4))
                duracao = int(resultado.group(5))

                if duracao < 1:
                    raise ValueError(
                        f"Erro na linha {numero_linha}: evento IO inválido 'IO:{tempo:02d}-{duracao:02d}'. "
                        "A duração mínima de uma operação de E/S é 1."
                    )

                eventos.append(EventoTarefa(
                    tipo="IO",
                    tempo=tempo,
                    duracao=duracao,
                    ordem=ordem
                ))

            posicao_atual = resultado.end()

        texto_final = valor[posicao_atual:]

        if re.fullmatch(r"[\s,;]*", texto_final) is None:
            raise ValueError(
                f"Erro na linha {numero_linha}: trecho inválido no final da lista de eventos: '{texto_final}'. "
                "Formatos esperados: MLxx:tempo, MUxx:tempo ou IO:tempo-duracao."
            )

        return eventos
            