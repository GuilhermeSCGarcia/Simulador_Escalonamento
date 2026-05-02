from CPU import CPU
from Estados import EstadosCPU, EstadosTarefa

def main():
    cpu1 = CPU(
        id = 1,
        estado = EstadosCPU.LIGADO,
        atualTarefa = None,
    )
    
    print(cpu1.id)
    
    cpu1.historico(0,3,EstadosCPU.ativo)    
    
if __name__ == "__main__":
    main()
