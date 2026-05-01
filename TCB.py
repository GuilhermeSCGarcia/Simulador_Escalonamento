class TCB:
    id: int #id da tarefa
    cor: str #pode alterar por causa do matplotlip
    temp_chegada: int #tempo de tick de chegada da tarefa
    temp_total: int #tempo total da tarefa
    temp_restante: int #tempo restante até a tarefa terminar
    estado: str #guardar o estado da tarefa?
    prioridade_estatica: int #prioridade estática positiva ou negativa
    id_cpu: int #cpu associada com o processo

    def __init__(self,id,temp_chegada,temp_total,prioridade_estatica: int):
        self.id = id
        self.temp_chegada = temp_chegada
        self.temp_total = temp_total
        self.prioridade_estatica = prioridade_estatica
        pass

    


    