import random
from abc import ABC, abstractmethod

from TCB import TCB



# Classe base, interface que tem que ser implementada por cada classe que implementa um algoritmo de escalonador
class EscalonadorBase(ABC):
    @abstractmethod
    def ordenar_candidatos(self, candidatos: list[TCB]) -> TCB: # Recebe a lista de candidatos e devolve ela ordenada com base o algoritmo selecionado
        pass

# Classe escalonador SRTF
class EscalonadorSRTF(EscalonadorBase):
    def ordenar_candidatos(self, candidatos: list[TCB]) -> TCB:
        candidatos.sort(key=lambda t: (
            t.tempoCorrido, # Menor tempo restante
            not t.estavaRodando, # Dar prefêrencia pela tarefa que já estava rodando
            t.tempoDeIngresso, # Menor instante de ingresso
            t.tempoTotal, # Menor tempo total
            random.random() # Sorteio Aleatório
        ))

        if(len(candidatos) > 1):
            motivo = self.motivo_de_escolha(candidatos[0], candidatos[1])
            print(f"Motivo da escolha: {motivo}")


        return candidatos[0] if len(candidatos) > 0 else None
    
    def motivo_de_escolha(self,t1 : TCB, t2 : TCB) -> int:
        if t1.tempoCorrido != t2.tempoCorrido:
            return "Menor tempo restante"
        elif t1.estavaRodando != t2.estavaRodando:
            return "Dar prefêrencia pela tarefa que já estava rodando"
        elif t1.tempoDeIngresso != t2.tempoDeIngresso:
            return "Menor instante de ingresso"
        elif t1.tempoTotal != t2.tempoTotal:
            return "Menor tempo total"      
        else:
            t1.sofreu_sorteio = True
            return "Sorteio Aleatório"

    
# Classe escalonador PRIOP
class EscalonadorPRIOP(EscalonadorBase):
    def ordenar_candidatos(self, candidatos: list[TCB]) -> TCB:
        candidatos.sort(key=lambda t: (
            -t.prioridadeEstatica,      # Maior prioridade
            not t.estavaRodando,        # Dar prefêrencia pela tarefa que já estava rodando
            t.tempoDeIngresso,          # Menor instante de ingresso
            t.tempoTotal,               # Menor duração
            random.random()             # Sorteio
        ))
        if(len(candidatos) > 1):
            motivo = self.motivo_de_escolha(candidatos[0], candidatos[1])
            print(f"Motivo da escolha: {motivo}")
            
        return candidatos[0] if len(candidatos) > 0 else None    


    def motivo_de_escolha(self,t1 : TCB, t2 : TCB) -> int:
        if t1.prioridadeEstatica != t2.prioridadeEstatica:
            return "Maior prioridade"
        elif t1.estavaRodando != t2.estavaRodando:
            return "Dar prefêrencia pela tarefa que já estava rodando"
        elif t1.tempoDeIngresso != t2.tempoDeIngresso:
            return "Menor instante de ingresso"
        elif t1.tempoTotal != t2.tempoTotal:
            return "Menor tempo total"      
        else:
            t1.sofreu_sorteio = True
            return "Sorteio Aleatório"

    
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