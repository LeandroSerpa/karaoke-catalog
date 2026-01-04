from flask import Flask
from pypdf import PdfReader
import os

app = Flask(__name__)

PDF_FILE = "catalogo.pdf"

@app.route('/')
def debug_pdf():
    if not os.path.exists(PDF_FILE):
        return "<h1>ERRO: O arquivo catalogo.pdf não foi encontrado!</h1>"
    
    try:
        reader = PdfReader(PDF_FILE)
        texto_completo = ""
        # Lê apenas as 2 primeiras páginas para teste
        for i, page in enumerate(reader.pages[:2]):
            texto_completo += f"--- PÁGINA {i+1} ---\n"
            texto_completo += page.extract_text() + "\n\n"
        
        if not texto_completo.strip():
            return "<h1>O PDF parece ser uma imagem (scan). Preciso de um PDF com texto selecionável!</h1>"

        return f"""
        <h1>DIAGNÓSTICO DO PDF</h1>
        <p>Me mande um print dessa tela ou copie o texto abaixo para o chat:</p>
        <hr>
        <pre style="background: #f4f4f4; padding: 20px; white-space: pre-wrap;">{texto_completo}</pre>
        """
    except Exception as e:
        return f"<h1>Erro ao ler PDF: {str(e)}</h1>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
