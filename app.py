import os
import re
from flask import Flask, render_template_string
from pypdf import PdfReader

app = Flask(__name__)

# CONFIGURAÇÃO
PDF_FILE = "catalogo.pdf"

# HTML EMBUTIDO COM CORREÇÃO DE CONFLITO (Vue usa [[ ]] agora)
HTML_SITE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Karaokê Catalogo</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <style>
        body { background: #f4f4f4; padding-bottom: 50px; font-family: sans-serif; }
        .search-box { position: sticky; top: 0; background: white; padding: 15px; border-bottom: 3px solid #0d6efd; z-index: 100; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        .card-music { background: white; margin: 10px auto; padding: 15px; border-radius: 8px; border-left: 5px solid #0d6efd; box-shadow: 0 2px 5px rgba(0,0,0,0.05); max-width: 800px; display: flex; justify-content: space-between; align-items: center; }
        .artist { color: #0d6efd; font-weight: 800; font-size: 0.85rem; text-transform: uppercase; }
        .title { font-weight: bold; font-size: 1.1rem; }
        .lyrics { font-size: 0.8rem; color: #666; font-style: italic; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 200px; }
        .code { background: #eee; padding: 10px; border-radius: 8px; font-weight: 900; font-size: 1.3rem; color: #333; min-width: 80px; text-align: center; cursor: pointer; border: 2px dashed #ccc; }
        .pagination { justify-content: center; margin-top: 20px; display: flex; gap: 15px; align-items: center; }
        .btn-page { background: #0d6efd; color: white; border: none; width: 45px; height: 45px; border-radius: 50%; font-size: 1.2rem; }
        .btn-page:disabled { opacity: 0.5; }
    </style>
</head>
<body>
<div id="app">
    <div class="search-box">
        <input type="text" class="form-control form-control-lg" v-model="busca" placeholder="🔍 Pesquise aqui..." @input="pagina=1">
        <div class="text-center mt-2 small text-muted">[[ listaFiltrada.length ]] músicas encontradas</div>
    </div>

    <div class="container mt-2">
        <div v-for="m in listaPaginada" :key="m.c" class="card-music">
            <div style="flex: 1; padding-right: 10px;">
                <div class="artist">[[ m.a ]]</div>
                <div class="title">[[ m.m ]]</div>
                <div class="lyrics" v-if="m.l">"[[ m.l ]]"</div>
            </div>
            <div class="code" @click="copiar(m.c)">[[ m.c ]]</div>
        </div>

        <div class="pagination" v-if="totalPaginas > 1">
            <button class="btn-page" @click="mudarPagina(-1)" :disabled="pagina===1"><</button>
            <strong>[[ pagina ]] / [[ totalPaginas ]]</strong>
            <button class="btn-page" @click="mudarPagina(1)" :disabled="pagina===totalPaginas">></button>
        </div>
    </div>
</div>

<script>
    const musicas = {{ dados | tojson }};
    const { createApp } = Vue;

    createApp({
        delimiters: ['[[', ']]'], // Aqui resolvemos o conflito com o Python!
        data() { return { db: musicas, busca: '', pagina: 1, porPagina: 50 } },
        computed: {
            listaFiltrada() {
                if (!this.busca) return this.db;
                const t = this.busca.toLowerCase();
                return this.db.filter(m => m.a.toLowerCase().includes(t) || m.m.toLowerCase().includes(t) || m.c.includes(t) || (m.l && m.l.toLowerCase().includes(t)));
            },
            totalPaginas() { return Math.ceil(this.listaFiltrada.length / this.porPagina); },
            listaPaginada() {
                const i = (this.pagina - 1) * this.porPagina;
                return this.listaFiltrada.slice(i, i + this.porPagina);
            }
        },
        methods: {
            copiar(texto) { navigator.clipboard.writeText(texto).then(() => alert('Copiado: ' + texto)); },
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
        texto = ""
        for page in reader.pages: texto += page.extract_text() + "\n"
        
        # Regex padrão
        pattern = r'"([^"]*?)"\s*,\s*"([^"]*?)"\s*,\s*"([^"]*?)"\s*,\s*"([^"]*?)"'
        matches = re.findall(pattern, texto, re.DOTALL)
        
        lista = []
        vistos = set()
        for m in matches:
            c = m[1].replace('\n', ' ').strip()
            if c.isdigit() and c not in vistos:
                lista.append({
                    "a": m[0].replace('\n', ' ').strip(),
                    "c": c,
                    "m": m[2].replace('\n', ' ').strip(),
                    "l": m[3].replace('\n', ' ').strip()
                })
                vistos.add(c)
        
        lista.sort(key=lambda x: x['a'].lower())
        print(f"--- SUCESSO: {len(lista)} músicas carregadas! ---")
        return lista
    except Exception as e:
        print(f"Erro no PDF: {e}")
        return []

# Carrega na memória
CACHE_MUSICAS = processar_pdf()

@app.route('/')
def index():
    return render_template_string(HTML_SITE, dados=CACHE_MUSICAS)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
