import os
import json
import re

# Arquivo de configuração persistente (localizado na raiz do projeto)
CONFIG_FILE = os.path.normpath(os.path.join(os.path.dirname(__file__), os.pardir, "converter_config.json"))

def safe_filename(name):
    #Sanitiza nome de arquivo para Windows
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.strip().replace(' ', '_')[:50]
    return name if name else "webpage"

def load_config():
    #Carrega configurações do arquivo JSON
    default_config = {
        'remove_bg': False,
        'include_logo': False,
        'show_source': False,
        'disable_links': False,
        'underline_links': False,
        'add_index': False,
        'index_depth': 2,
        'index_depth_text': 'H1 e H2',
        'index_position': 'Início do documento',
        'auto_save': False,
        'save_folder': '',
        'scroll_pages': True,
        'scroll_delay': 500
    }

    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                saved_config = json.load(f)
                default_config.update(saved_config)
    except Exception as e:
        print(f"Erro ao carregar config: {e}")

    return default_config

def save_config(config):
    #Salva configurações no arquivo JSON
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Erro ao salvar config: {e}")