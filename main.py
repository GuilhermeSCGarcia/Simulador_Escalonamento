'''
Classe: Main 

Este arquivo é o único que deve ser executado para rodar 
o simulador. Ele inicializa o framework gráfico (Tkinter) e invoca a classe controladora 
da interface, mantendo o loop de eventos ativo.
'''

import tkinter as tk
from Interface import InterfaceSimulador

def main():
    # 1. Cria a janela raiz do sistema operacional
    root = tk.Tk()

    # 2. Instancia a interface
    app = InterfaceSimulador(root)
    
    # 3. Roda o loop principal
    root.mainloop()

if __name__ == "__main__":
    main()