import subprocess
import tempfile
import json
import sys
import os
import base64
import hashlib
from functools import lru_cache

@lru_cache(maxsize=32)
def get_script_hash(config_json, url):
    #Cache de scripts para URLs repetidas
    return hashlib.md5(f"{config_json}{url}".encode()).hexdigest()

def convert_url(url, config):
    #Converte uma URL para PDF usando subprocess para isolamento
    try:
        temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(config, temp_config)
        temp_config.close()

        current_dir = os.path.dirname(__file__)
        internal_package = os.path.dirname(current_dir)
        project_root = os.path.dirname(internal_package)
        package_name = os.path.basename(internal_package)

        
        script_content = f'''
import sys
import os
import json
import base64

sys.path.insert(0, r"{project_root}")

try:
    from {package_name}.engine.playwright_engine import gerar_pdf
    with open(r"{temp_config.name}", 'r') as f:
        config = json.load(f)
    sys.stdout.buffer.write(base64.b64encode(gerar_pdf("{url}", config)))
except Exception as e:
    sys.stderr.write(str(e))
    sys.exit(1)
'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(script_content)
            script_file = f.name

        
        result = subprocess.run(
            [sys.executable, script_file],
            capture_output=True,
            timeout=60,  
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )

        try:
            os.unlink(script_file)
            os.unlink(temp_config.name)
        except:
            pass

        if result.returncode == 0 and result.stdout:
            return base64.b64decode(result.stdout)
        else:
            error_msg = result.stderr.decode('utf-8', errors='ignore') if result.stderr else "Erro desconhecido"
            raise Exception(f"Falha: {error_msg}")

    except subprocess.TimeoutExpired:
        raise Exception("Timeout")
    except Exception as e:
        raise e