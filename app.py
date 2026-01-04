import os
import re
import json
from flask import Flask, render_template_string, Response
from pypdf import PdfReader

app = Flask(__name__)

# CONFIGURAÇÃO
PDF_FILE = "catalogo.pdf"

# --- LAYOUT DO SITE ONLINE (O que você vê no Easypanel) ---
HTML_ONLINE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gerador de Catálogo</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f0f2f5; display: flex; align-items: center; justify-content: center; height: 100vh; font-family: sans-serif; }
        .card { max-width: 500px; width: 90%; padding: 30px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center; }
        .btn-download { background: #28a745; color: white; padding: 15px 30px; font-size: 1.2rem; border-radius: 50px; text-decoration: none; display: block; margin-top: 20px; font-weight: bold; transition: 0.3s; }
        .btn-download:hover { background: #218838; transform: scale(1.05); }
        .stats { color: #666; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="card">
        <h1 class="mb-3">🎤 Tudo Pronto!</h1>
        <p class="stats">Processamos <strong>{{ qtd }}</strong> músicas do seu PDF.</p>
        <p>Clique abaixo para baixar o arquivo HTML único. Depois, você pode enviar esse arquivo pelo WhatsApp e desligar este servidor.</p>
        
        <a href="/baixar" class="btn-download">📥 BAIXAR CATÁLOGO OFFLINE</a>
    </div>
</body>
</html>
"""

# --- LAYOUT DO ARQUIVO FINAL (O que vai pro WhatsApp) ---
# Este HTML contém o Vue.js e os dados embutidos para rodar sem servidor
HTML_OFFLINE_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Catálogo de Karaokê</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <style>
        body { background: #f4f4f4; padding-bottom: 50px; font-family: sans-serif; }
        .search-box { position: sticky; top: 0; background: white; padding: 15px; border-bottom: 3px solid #0d6efd; z-index: 100; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        .card-music { background: white; margin: 10px auto; padding: 15px; border-radius: 8px; border-left: 5px solid #0d6efd; box-shadow: 0 2px 5px rgba(0,0,0,0.05); max-width: 800px; display: flex; justify-content: space-between; align-items: center; }
        .info { flex: 1; padding-right: 10px; overflow: hidden; }
        .artist { color: #0d6efd; font-weight: 800; font-size: 0.9rem; text-transform: uppercase; margin-bottom: 2px; }
        .title { font-weight: bold; font-size: 1.1rem; line-height: 1.2; color: #333; }
        .code { background: #eee; padding: 10px; border-radius: 8px; font-weight: 900; font-size: 1.4rem; color: #333; min-width: 90px; text-align: center; cursor: pointer; border: 2px dashed #ccc; }
        .code:active { background: #ccc; transform: scale(0.95); }
        .pagination { justify-content: center; margin-top: 20px; display: flex; gap: 15px; align-items: center; }
        .btn-page { background: #0d6efd; color: white; border: none; width: 45px; height: 45px; border-radius: 50%; font-size: 1.2rem; }
        .btn-page:disabled { opacity: 0.5; }
        .footer-note { text-align: center; margin-top: 30px; color: #999; font-size: 0.8rem; }
    </style>
</head>
<body>
<div id="app">
    <div class="search-box">
        <input type="text" class="form-control form-control-lg" v-model="busca" placeholder="🔍 Digite artista, música ou código..." @input="pagina=1">
        <div class="text-center mt-2 small text-muted">{{ listaFiltrada.length }} músicas disponíveis</div>
    </div>

    <div class="container mt-2">
        <div v-for="m in listaPaginada" :key="m.c" class="card-music">
            <div class="info">
                <div class="artist">{{ m.a }}</div>
                <div class="title">{{ m.m }}</div>
            </div>
            <div class="code" @click="copiar(m.c)">{{ m.c }}</div>
        </div>

        <div class="pagination" v-if="totalPaginas > 1">
            <button class="btn-page" @click="mudarPagina(-1)" :disabled="pagina===1"><</button>
            <strong>{{ pagina }} / {{ totalPaginas }}</strong>
            <button class="btn-page" @click="mudarPagina(1)" :disabled="pagina===totalPaginas">></button>
        </div>
        
        <div class="footer-note">Arquivo gerado via Automação LE</div>
    </div>
</div>

<script>
    // AQUI ENTRA A MÁGICA: O Python vai injetar os dados aqui dentro
    const musicas = __DADOS_AQUI__;
    
    const { createApp } = Vue;
    createApp({
        data() { return { db: musicas, busca: '', pagina: 1, porPagina: 50 } },
        computed: {
            listaFiltrada() {
                if (!this.busca) return this.db;
                const t = this.busca.toLowerCase();
                return this.db.filter(m => m.a.toLowerCase().includes(t) || m.m.toLowerCase().includes(t) || m.c.includes(t));
            },
            totalPaginas() { return Math.ceil(this.listaFiltrada.length / this.porPagina); },
            listaPaginada() {
                const i = (this.pagina - 1) * this.porPagina;
                return this.listaFiltrada.slice(i, i + this.porPagina);
            }
        },
        methods: {
            copiar(texto) { navigator.clipboard.writeText(texto).then(() => alert('Código copiado: ' + texto)); },
            mudarPagina(d) { this.pagina += d; window.scrollTo(0, 0); }
        }
    }).mount('#app');
</script>
</body>
</html>
"""

def processar_pdf():
    if not os.path.exists(PDF_FILE): return []
    try:
        reader = PdfReader(PDF_FILE)
        lista = []
        vistos = set()
        pattern = re.compile(r"(.+?)\s+(\d{4,5})\s+(.+)")

        for page in reader.pages:
            texto = page.extract_text()
            if not texto: continue
            for linha in texto.split('\n'):
                match = pattern.search(linha)
                if match:
                    codigo = match.group(2).strip()
                    if codigo not in vistos:
                        lista.append({
                            "a": match.group(1).strip(),
                            "c": codigo,
                            "m": match.group(3).strip()
                        })
                        vistos.add(codigo)
        lista.sort(key=lambda x: x['a'].lower())
        return lista
    except Exception as e:
        print(f"Erro: {e}")
        return []

CACHE_MUSICAS = processar_pdf()

@app.route('/')
def index():
    return render_template_string(HTML_ONLINE, qtd=len(CACHE_MUSICAS))

@app.route('/baixar')
def baixar():
    # Converte a lista de músicas para texto JSON
    dados_json = json.dumps(CACHE_MUSICAS)
    
    # Coloca os dados dentro do template HTML
    html_final = HTML_OFFLINE_TEMPLATE.replace('__DADOS_AQUI__', dados_json)
    
    # Força o navegador a baixar como arquivo
    return Response(
        html_final,
        mimetype="text/html",
        headers={"Content-disposition": "attachment; filename=catalogo_karaoke.html"}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
