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