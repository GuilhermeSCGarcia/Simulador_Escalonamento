from dataclasses import dataclass
# a fazer
@dataclass
class ConfigSimulador:
    algoritmoEscalomento : str = "SRTF"
    tamQuantum: int = "2"
    numCPU: int = "4"
    pass

