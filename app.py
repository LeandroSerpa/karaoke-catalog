import os
import re
import json
import base64
import mimetypes
from flask import Flask, Response, send_file
from pypdf import PdfReader

app = Flask(__name__)

# --- CONFIGURAÇÕES ---
PDF_FILE = "catalogo.pdf"
# O sistema vai procurar por estes nomes de imagem no seu GitHub
NOME_IMAGEM = ["logo.png", "logo.jpg", "logo.jpeg"]

# --- LAYOUT ÚNICO ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-br" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Catálogo VIDEOKÊ</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <style>
        :root {
            --bg-dark: #050505;
            --bg-gradient: linear-gradient(180deg, #000000 0%, #1a1a1a 100%);
            --accent: #FFD700; /* Dourado Clássico Videokê */
            --card-bg: #1e1e1e;
            --text-main: #f0f0f0;
        }

        body { 
            background: var(--bg-dark); 
            background-image: var(--bg-gradient);
            background-attachment: fixed;
            padding-bottom: 80px; 
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            color: var(--text-main);
        }

        /* HEADER */
        .hero-header {
            background: linear-gradient(to bottom, #000 0%, #222 100%);
            padding: 30px 20px;
            text-align: center;
            border-bottom: 3px solid var(--accent);
            box-shadow: 0 0 20px rgba(255, 215, 0, 0.2);
            border-radius: 0 0 20px 20px;
            margin-bottom: 25px;
        }
        
        /* A Imagem do Leão */
        .lion-img {
            max-width: 150px;
            height: auto;
            display: block;
            margin: 0 auto 10px auto;
            filter: drop-shadow(0 0 8px rgba(255, 215, 0, 0.3));
        }

        /* Texto VIDEOKÊ estilizado caso a imagem não tenha o texto */
        .brand-title {
            font-family: 'Arial Black', sans-serif;
            font-size: 2rem;
            color: var(--accent);
            text-transform: uppercase;
            letter-spacing: 2px;
            margin: 0;
            text-shadow: 2px 2px 0 #000;
        }
        
        .sub-title { color: #888; font-size: 0.9rem; letter-spacing: 1px; text-transform: uppercase; }

        /* BUSCA */
        .search-container { padding: 0 15px; margin-top: -15px; }
        .form-control-lg { 
            background: #2d2d2d; border: 1px solid #444; 
            color: white; border-radius: 12px; padding: 12px 20px; 
        }
        .form-control-lg:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(255, 215, 0, 0.2); }

        /* ABAS A-Z */
        .alphabet-bar {
            display: flex; overflow-x: auto; gap: 8px; padding: 15px;
            scrollbar-width: none;
        }
        .letter-btn {
            flex: 0 0 auto; min-width: 45px; height: 40px; 
            border-radius: 8px; border: 1px solid #333;
            background: #1a1a1a; color: #888; font-weight: bold;
            display: flex; align-items: center; justify-content: center;
        }
        .letter-btn.active {
            background: var(--accent); color: #000; border-color: var(--accent);
            transform: scale(1.05); font-weight: 900;
        }

        /* LISTA */
        .card-music { 
            background: var(--card-bg); 
            margin: 10px auto; padding: 15px; border-radius: 10px; 
            display: flex; justify-content: space-between; align-items: center; 
            max-width: 800px; border-left: 4px solid var(--accent);
        }
        .artist { color: var(--accent); font-weight: bold; font-size: 0.85rem; text-transform: uppercase; }
        .title { font-weight: 600; font-size: 1.1rem; color: white; line-height: 1.2; }
        
        .code-btn {
            background: #0d6efd; color: white; /* Azul padrão para contraste */
            padding: 8px 12px; border-radius: 6px; font-weight: 900; font-size: 1.2rem;
            min-width: 80px; text-align: center;
        }
        .code-label { font-size: 0.6rem; text-align: center; opacity: 0.6; margin-top: 3px; text-transform: uppercase; }

        /* PAGINAÇÃO & BOTÃO */
        .pagination { justify-content: center; margin-top: 25px; display: flex; gap: 10px; align-items: center; }
        .btn-page { width: 45px; height: 45px; border-radius: 50%; border: none; background: #333; color: white; font-size: 1.2rem; }
        .btn-page:disabled { opacity: 0.3; }

        .fab-download {
            position: fixed; bottom: 25px; right: 25px; background: #198754; color: white;
            width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
            font-size: 1.5rem; box-shadow: 0 5px 15px rgba(0,0,0,0.5); text-decoration: none; z-index: 1000;
        }
    </style>
</head>
<body>
<div id="app">
    
    <div class="hero-header">
        <img src="__IMAGEM_SRC__" class="lion-img" alt="Logo">
        <h1 class="brand-title">VIDEOKÊ</h1>
        <div class="sub-title">Catálogo Digital</div>
    </div>

    <div class="search-container">
        <input type="text" class="form-control form-control-lg" v-model="busca" placeholder="🔍 Buscar música..." @input="limparLetra()">
    </div>

    <div class="alphabet-bar">
        <div class="letter-btn" :class="{active: filtroLetra === ''}" @click="filtrarLetra('')">
            ALL
        </div>
        <div class="letter-btn" v-for="letra in alfabeto" :class="{active: filtroLetra === letra}" @click="filtrarLetra(letra)">
            {{ letra }}
        </div>
    </div>
    
    <div class="text-center mt-2 small opacity-50">{{ listaFiltrada.length }} músicas</div>

    <div class="container pb-5">
        <div v-for="m in listaPaginada" :key="m.c" class="card-music">
            <div style="flex: 1; padding-right: 10px;">
                <div class="artist">{{ m.a }}</div>
                <div class="title">{{ m.m }}</div>
            </div>
            <div @click="copiar(m.c)">
                <div class="code-btn">{{ m.c }}</div>
                <div class="code-label">Copiar</div>
            </div>
        </div>

        <div class="pagination" v-if="totalPaginas > 1">
            <button class="btn-page" @click="mudarPagina(-1)" :disabled="pagina===1">❮</button>
            <span class="fw-bold align-self-center">{{ pagina }}</span>
            <button class="btn-page" @click="mudarPagina(1)" :disabled="pagina===totalPaginas">❯</button>
        </div>
        
        <div class="text-center mt-4 text-muted small">Gerado via Sistema</div>
    </div>

    __BOTAO_DOWNLOAD__
</div>

<script>
    // AQUI O PYTHON GARANTE QUE OS ACENTOS VENHAM CERTOS (UTF-8)
    const musicas = __DADOS_AQUI__;
    
    const { createApp } = Vue;
    createApp({
        data() { return { 
            db: musicas, busca: '', filtroLetra: '', pagina: 1, porPagina: 50,
            alfabeto: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')
        }},
        computed: {
            listaFiltrada() {
                let res = this.db;
                if (this.filtroLetra) res = res.filter(m => m.a.toUpperCase().startsWith(this.filtroLetra));
                if (this.busca) {
                    const t = this.busca.toLowerCase();
                    res = res.filter(m => m.a.toLowerCase().includes(t) || m.m.toLowerCase().includes(t) || m.c.includes(t));
                }
                return res;
            },
            totalPaginas() { return Math.ceil(this.listaFiltrada.length / this.porPagina); },
            listaPaginada() {
                const i = (this.pagina - 1) * this.porPagina;
                return this.listaFiltrada.slice(i, i + this.porPagina);
            }
        },
        methods: {
            copiar(t) { navigator.clipboard.writeText(t).then(() => alert('Código ' + t + ' copiado!')); },
            mudarPagina(d) { this.pagina += d; window.scrollTo(0, 0); },
            filtrarLetra(l) { this.filtroLetra = l; this.busca = ''; this.pagina = 1; },
            limparLetra() { if(this.busca) this.filtroLetra = ''; this.pagina = 1; }
        }
    }).mount('#app');
</script>
</body>
</html>
"""

def encontrar_imagem_local():
    """Procura por logo.png/jpg no diretório e retorna caminho ou None"""
    for nome in NOME_IMAGEM:
        if os.path.exists(nome):
            return nome
    return None

def imagem_para_base64(caminho_arquivo):
    """Converte arquivo de imagem para string Base64 para embutir no HTML"""
    if not caminho_arquivo:
        # Se não tiver imagem, usa um microfone genérico transparente
        return "https://cdn-icons-png.flaticon.com/512/3408/3408764.png"
    
    with open(caminho_arquivo, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        mime_type, _ = mimetypes.guess_type(caminho_arquivo)
        return f"data:{mime_type};base64,{encoded_string}"

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
                        lista.append({"a": match.group(1).strip(), "c": codigo, "m": match.group(3).strip()})
                        vistos.add(codigo)
        lista.sort(key=lambda x: x['a'].lower())
        return lista
    except: return []

CACHE_MUSICAS = processar_pdf()

@app.route('/')
def index():
    # Garante acentos corretos (UTF-8)
    dados_json = json.dumps(CACHE_MUSICAS, ensure_ascii=False)
    
    # Tenta mostrar a imagem online (link direto do arquivo se existir)
    caminho_img = encontrar_imagem_local()
    if caminho_img:
        # Rota local para imagem (simplificada)
        src_img = f"/{caminho_img}"
    else:
        src_img = "https://cdn-icons-png.flaticon.com/512/3408/3408764.png"

    btn = '<a href="/baixar" class="fab-download"><i class="bi bi-download"></i></a>'
    return HTML_TEMPLATE.replace('__DADOS_AQUI__', dados_json)\
                        .replace('__BOTAO_DOWNLOAD__', btn)\
                        .replace('__IMAGEM_SRC__', src_img)

# Rota para servir a imagem localmente na prévia
@app.route('/<path:filename>')
def serve_static(filename):
    if filename in NOME_IMAGEM and os.path.exists(filename):
        return send_file(filename)
    return "Arquivo não encontrado", 404

@app.route('/baixar')
def baixar():
    # 1. Pega a imagem que você subiu e converte para código
    caminho_img = encontrar_imagem_local()
    if caminho_img:
        print(f"Embutindo imagem: {caminho_img}")
        img_code = imagem_para_base64(caminho_img)
    else:
        print("Imagem logo.png não encontrada! Usando genérica.")
        img_code = "https://cdn-icons-png.flaticon.com/512/3408/3408764.png"
    
    # 2. Garante acentos (ensure_ascii=False)
    dados_json = json.dumps(CACHE_MUSICAS, ensure_ascii=False)
    
    html_final = HTML_TEMPLATE.replace('__DADOS_AQUI__', dados_json)\
                              .replace('__BOTAO_DOWNLOAD__', '')\
                              .replace('__IMAGEM_SRC__', img_code)
    
    # 3. Força codificação UTF-8 no download
    return Response(
        html_final,
        mimetype="text/html; charset=utf-8",
        headers={"Content-disposition": "attachment; filename=Catalogo_Videoke.html"}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
