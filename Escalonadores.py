import random
from abc import ABC, abstractmethod

from TCB import TCB

# Classe base, interface que tem que ser implementada por cada classe que implementa um algoritmo de escalonador
class EscalonadorBase(ABC):
    @abstractmethod
    def ordenar_candidatos(self, candidatos: list[TCB]) -> list[TCB]: # Recebe a lista de candidatos e devolve ela ordenada com base o algoritmo selecionado
        pass

# Classe escalonador SRTF
class EscalonadorSRTF(EscalonadorBase):
    def ordenar_candidatos(self, candidatos: list[TCB]) -> list[TCB]:
        candidatos.sort(key=lambda t: (
            t.tempoCorrido, # Menor tempo restante
            not t.estavaRodando, # Dar prefêrencia pela tarefa que já estava rodando
            t.tempoDeIngresso, # Menor instante de ingresso
            t.tempoTotal, # Menor tempo total
            random.random() # Sorteio Aleatório
        ))

        return candidatos
    
# Classe escalonador PRIOP
class EscalonadorPRIOP(EscalonadorBase):
    def ordenar_candidatos(self, candidatos: list[TCB]) -> list[TCB]:
        candidatos.sort(key=lambda t: (
            -t.prioridadeEstatica,      # Maior prioridade
            not t.estavaRodando,        # Dar prefêrencia pela tarefa que já estava rodando
            t.tempoDeIngresso,          # Menor instante de ingresso
            t.tempoTotal,               # Menor duração
            random.random()             # Sorteio
        ))
        return candidatos
    
# Função que executa a classe correta com base no algoritmo selecionado no config.txt
def fabrica_de_escalonadores(nome_algoritmo: str) -> EscalonadorBase:
    algoritmo_disponiveis: dict = {
        "SRTF": EscalonadorSRTF(),
        "PRIOP": EscalonadorPRIOP()
    }

    if nome_algoritmo.upper() in algoritmo_disponiveis:
        return algoritmo_disponiveis[nome_algoritmo.upper()]
    else:
        raise ValueError(f"Algortimo '{nome_algoritmo}' Não reconhecido!")