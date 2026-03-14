from utils import load_config, safe_filename
from engine.converter import convert_url
import os
from datetime import datetime


def run_cli(target):
    import os

    if os.path.isfile(target):
        run_batch(target)
    else:
        run_single(target)

def run_single(url):
    print(f"Convertendo: {url}")

    config = load_config()

    try:
        pdf_bytes = convert_url(url, config)

        # Salva o PDF
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = safe_filename(parsed.netloc.replace('www.', ''))
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{domain}_{timestamp}.pdf"

        if config.get('auto_save') and config.get('save_folder'):
            save_path = os.path.join(config['save_folder'], filename)
            with open(save_path, 'wb') as f:
                f.write(pdf_bytes)
            print(f"PDF salvo em: {save_path}")
        else:
            with open(filename, 'wb') as f:
                f.write(pdf_bytes)
            print(f"PDF salvo como: {filename}")

    except Exception as e:
        print(f"Erro em {url}: {e}")




def run_batch(file_path):

    print(f"Lendo lista: {file_path}")

    config = load_config()

    with open(file_path, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"{len(urls)} URLs encontradas")

    for url in urls:
        try:
            print(f"\nConvertendo: {url}")

            pdf_bytes = convert_url(url, config)

            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = safe_filename(parsed.netloc.replace('www.', ''))
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{domain}_{timestamp}.pdf"

            with open(filename, "wb") as f:
                f.write(pdf_bytes)

            print(f"PDF salvo como: {filename}")

        except Exception as e:
            print(f"Erro em {url}: {e}")
