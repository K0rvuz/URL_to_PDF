import streamlit as st
import pdfkit
import requests
import chardet
import tempfile
import os

WKHTMLTOPDF_PATH = 'C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe'  # Windows

config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)

options = {
    'enable-local-file-access': '',
    'page-size': 'A4',
    'encoding': "UTF-8",
    'custom-header': [('Accept-Charset', 'utf-8')],
    'print-media-type': '',
    'disable-smart-shrinking': '',
    'footer-right': '[page]/[topage]',
    'footer-font-size': '8',
    'footer-spacing': '5',
    'zoom': '1.0'
}

st.set_page_config(page_title="Conversor de URL para PDF com Acentuação", layout="centered")
st.title("🌐📄 Conversor de URL para PDF")

url = st.text_input("Digite a URL da página que deseja converter para PDF:")

if st.button("Converter"):
    if not url:
        st.warning("Por favor, insira uma URL válida.")
    else:
        with st.spinner("Baixando e convertendo..."):
            try:
                # Baixa o conteúdo bruto
                response = requests.get(url)
                raw_bytes = response.content

                # Detecta a codificação real
                detected = chardet.detect(raw_bytes)
                encoding = detected['encoding'] or 'utf-8'

                html_content = raw_bytes.decode(encoding, errors='replace')

                # Adiciona meta charset, se necessário
                if '<meta charset=' not in html_content.lower():
                    html_content = html_content.replace(
                        '<head>',
                        f'<head><meta charset="UTF-8">'
                    )

                # Salva HTML temporário
                with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as temp_html:
                    temp_html.write(html_content)
                    temp_html_path = temp_html.name

                # Converte para PDF
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                    pdfkit.from_file(temp_html_path, temp_pdf.name, options=options, configuration=config)
                    temp_pdf.seek(0)
                    st.success("PDF gerado com sucesso!")
                    st.download_button(
                        label="📥 Baixar PDF",
                        data=temp_pdf.read(),
                        file_name="pagina_convertida.pdf",
                        mime="application/pdf"
                    )

                os.remove(temp_html_path)

            except Exception as e:
                st.error(f"Erro ao gerar PDF: {e}")
