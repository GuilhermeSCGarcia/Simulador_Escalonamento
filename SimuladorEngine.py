from SimuladorConfig import ConfigSimulador
#a fazer

class SimuladorEngine:
    tick: int = 0
    config : ConfigSimulador

    def __init__(self):
        self.config = ConfigSimulador("config.txt")
        
    
    
def main():
    engine = SimuladorEngine()
    print("acabou")
    
    
    
if __name__ == "__main__":
    main()
    
    
    
    