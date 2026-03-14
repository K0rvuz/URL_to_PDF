import customtkinter as ctk
from gui.app import URLToPDFConverter
from cli.cli import run_cli
import subprocess
import sys
import os
import glob

# Verifica se playwright está com browsers instalados
def ensure_playwright():
    try:
        from playwright.sync_api import sync_playwright
        # Testa se consegue lançar
        with sync_playwright() as p:
            p.chromium.launch(headless=True).close()
    except:
        print("Instalando browsers do Playwright...")
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)




# Força o Playwright a encontrar os browsers no executável
if getattr(sys, 'frozen', False):
    # Estamos em um executável
    base_path = os.path.dirname(sys.executable)
    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = os.path.join(base_path, 'playwright-browsers')
    
    # Garante que o playwright consegue importar
    import playwright
    playwright._repo.DEFAULT_BROWSERS_PATH = os.environ['PLAYWRIGHT_BROWSERS_PATH']
    
    # Verifica se os browsers existem
    chromium_path = os.path.join(base_path, 'playwright-browsers', 'chromium-*.zip')
    if not any(glob.glob(chromium_path)):
        print("Instalando browsers do Playwright...")
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)






# Configuração do tema
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def main():
    
    # Garante playwright instalado
    ensure_playwright()
    
    if len(sys.argv) > 1:
        run_cli(sys.argv[1])
        return

    root = ctk.CTk()
    app = URLToPDFConverter(root)
    root.mainloop()

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    main()