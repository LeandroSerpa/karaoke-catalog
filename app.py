import os
import re
import json
import base64
import urllib.request
import ssl
from flask import Flask, Response
from pypdf import PdfReader

app = Flask(__name__)

# --- CONFIGURAÇÕES ---
PDF_FILE = "catalogo.pdf"

# LINK DA IMAGEM (Leão Dourado estilo Videokê)
# O sistema vai baixar essa imagem e salvar dentro do HTML
URL_LEAO = "https://cdn-icons-png.flaticon.com/512/10609/10609071.png"

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
            --bg-dark: #0f172a;
            --bg-gradient-dark: linear-gradient(180deg, #020617 0%, #1e293b 100%);
            --card-dark: rgba(30, 41, 59, 0.95);
            --accent: #FFD700; /* Dourado */
            --text-dark: #f1f5f9;
        }

        body { 
            background: var(--bg-dark); 
            background-image: var(--bg-gradient-dark);
            background-attachment: fixed;
            padding-bottom: 80px; 
            font-family: 'Segoe UI', Roboto, sans-serif;
            color: var(--text-dark);
        }

        /* HEADER ESTILO VIDEOKÊ RETRÔ */
        .hero-header {
            background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%);
            padding: 30px 20px;
            text-align: center;
            border-bottom: 4px solid var(--accent);
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            margin-bottom: 20px;
            border-radius: 0 0 30px 30px;
        }

        .lion-img {
            width: 120px; height: 120px;
            object-fit: contain;
            filter: drop-shadow(0 0 10px rgba(255, 215, 0, 0.5));
            margin-bottom: 5px;
        }

        /* TEXTO VIDEOKÊ IGUAL DA IMAGEM */
        .videoke-logo {
            font-family: 'Arial Black', 'Impact', sans-serif;
            font-size: 2.5rem;
            color: #FFD700; /* Amarelo Ouro */
            text-transform: uppercase;
            letter-spacing: 2px;
            margin: 0;
            line-height: 1;
            /* Borda preta em volta da letra */
            text-shadow: 
                2px 2px 0 #000, -1px -1px 0 #000,  
                1px -1px 0 #000, -1px 1px 0 #000,
                1px 1px 0 #000, 0 0 20px rgba(255, 215, 0, 0.4);
        }
        
        .app-subtitle {
            color: #ccc; font-size: 0.9rem; letter-spacing: 4px; text-transform: uppercase; margin-top: 5px;
        }

        /* CONTROLES */
        .search-container { padding: 0 15px; margin-top: -40px; }
        .form-control-lg { 
            background: rgba(30, 41, 59, 0.95); border: 2px solid #444; 
            color: white; border-radius: 50px; padding: 15px 25px; 
            box-shadow: 0 10px 20px rgba(0,0,0,0.3); font-size: 1.1rem;
        }
        .form-control-lg:focus { border-color: var(--accent); box-shadow: 0 0 0 4px rgba(255, 215, 0, 0.2); }

        /* ABAS A-Z */
        .alphabet-bar {
            display: flex; overflow-x: auto; gap: 6px; padding: 15px;
            scrollbar-width: none;
        }
        .letter-btn {
            flex: 0 0 auto; min-width: 45px; height: 40px; 
            border-radius: 8px; border: 1px solid #444;
            background: #1e293b; color: #aaa; font-weight: bold;
            display: flex; align-items: center; justify-content: center;
        }
        .letter-btn.active {
            background: var(--accent); color: #000; border-color: var(--accent);
            transform: scale(1.1); font-weight: 900;
        }
        .letter-count { font-size: 0.65rem; margin-left: 4px; font-weight: normal; }
        .letter-btn.active .letter-count { font-weight: bold; }

        /* LISTA */
        .card-music { 
            background: var(--card-dark); 
            margin: 10px auto; padding: 15px 20px; border-radius: 12px; 
            display: flex; justify-content: space-between; align-items: center; 
            max-width: 800px; border-left: 5px solid var(--accent);
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }
        .artist { color: var(--accent); font-weight: 800; font-size: 0.85rem; text-transform: uppercase; }
        .title { font-weight: 600; font-size: 1.1rem; color: white; }
        
        .code-btn {
            background: #0ea5e9; color: white;
            padding: 8px 15px; border-radius: 8px; font-weight: 800; font-size: 1.3rem;
            min-width: 85px; text-align: center;
        }
        .code-label { font-size: 0.6rem; text-align: center; opacity: 0.7; margin-top: 3px; text-transform: uppercase; }

        .pagination { justify-content: center; margin-top: 25px; display: flex; gap: 10px; align-items: center; }
        .btn-page { width: 50px; height: 50px; border-radius: 50%; border: none; background: #333; color: white; font-size: 1.2rem; }
        .btn-page:hover:not(:disabled) { background: var(--accent); color: black; }
        .btn-page:disabled { opacity: 0.3; }

        .fab-download {
            position: fixed; bottom: 25px; right: 25px; background: #22c55e; color: white;
            width: 65px; height: 65px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
            font-size: 1.8rem; box-shadow: 0 10px 25px rgba(0,255,0,0.3); text-decoration: none; z-index: 1000;
        }
    </style>
</head>
<body>
<div id="app">
    
    <div class="hero-header">
        <img src="__IMAGEM_SRC__" class="lion-img">
        <h1 class="videoke-logo">VIDEOKÊ</h1>
        <div class="app-subtitle">Catálogo Digital</div>
    </div>

    <div class="search-container">
        <input type="text" class="form-control form-control-lg" v-model="busca" placeholder="🔍 Buscar música..." @input="limparLetra()">
    </div>

    <div class="alphabet-bar">
        <div class="letter-btn" :class="{active: filtroLetra === ''}" @click="filtrarLetra('')">
            TODOS <span class="letter-count">({{ db.length }})</span>
        </div>
        <div class="letter-btn" v-for="letra in alfabeto" :class="{active: filtroLetra === letra}" @click="filtrarLetra(letra)">
            {{ letra }} <span class="letter-count" v-if="mapaContagem[letra]">({{ mapaContagem[letra] }})</span>
        </div>
    </div>
    
    <div class="text-center mt-2 small opacity-75">{{ listaFiltrada.length }} músicas</div>

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
            <button class="btn-page" @click="mudarPagina(-1)" :disabled="pagina===1"><i class="bi bi-chevron-left"></i></button>
            <span class="fw-bold">{{ pagina }}</span>
            <button class="btn-page" @click="mudarPagina(1)" :disabled="pagina===totalPaginas"><i class="bi bi-chevron-right"></i></button>
        </div>
        
        <div class="text-center mt-4 text-muted small">Catálogo Oficial</div>
    </div>

    __BOTAO_DOWNLOAD__
</div>

<script>
    const musicas = __DADOS_AQUI__;
    
    const { createApp } = Vue;
    createApp({
        data() { return { 
            db: musicas, busca: '', filtroLetra: '', pagina: 1, porPagina: 50,
            alfabeto: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')
        }},
        computed: {
            mapaContagem() {
                const map = {};
                this.db.forEach(m => {
                    if(m.a) {
                        const l = m.a.charAt(0).toUpperCase();
                        map[l] = (map[l] || 0) + 1;
                    }
                });
                return map;
            },
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

def obter_imagem_base64():
    try:
        ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(URL_LEAO, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx) as r:
            b64 = base64.b64encode(r.read()).decode('utf-8')
            return f"data:image/png;base64,{b64}"
    except: return "https://via.placeholder.com/150"

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
    # Aqui corrigimos o problema de encoding do JSON para visualização online
    dados_json = json.dumps(CACHE_MUSICAS, ensure_ascii=False)
    btn = '<a href="/baixar" class="fab-download"><i class="bi bi-download"></i></a>'
    return HTML_TEMPLATE.replace('__DADOS_AQUI__', dados_json).replace('__BOTAO_DOWNLOAD__', btn).replace('__IMAGEM_SRC__', URL_LEAO)

@app.route('/baixar')
def baixar():
    # 1. Baixa a imagem e converte para código (Base64)
    img_code = obter_imagem_base64()
    
    # 2. Garante que os acentos fiquem corretos (ensure_ascii=False)
    dados_json = json.dumps(CACHE_MUSICAS, ensure_ascii=False)
    
    html_final = HTML_TEMPLATE.replace('__DADOS_AQUI__', dados_json)\
                              .replace('__BOTAO_DOWNLOAD__', '')\
                              .replace('__IMAGEM_SRC__', img_code)
    
    # 3. Força o download como UTF-8 para não quebrar caracteres
    return Response(
        html_final.encode('utf-8'),
        mimetype="text/html",
        headers={"Content-disposition": "attachment; filename=Catalogo_Videoke.html"}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
