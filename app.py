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
NOME_IMAGEM = ["logo.png", "logo.jpg", "logo.jpeg"]

# --- LAYOUT HTML/VUE ---
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
            --bg-gradient: linear-gradient(180deg, #000000 0%, #111 100%);
            --accent: #FFD700; /* Dourado */
            --card-bg: #1e1e1e;
            --text-main: #f0f0f0;
        }

        body { 
            background: var(--bg-dark); 
            background-image: var(--bg-gradient);
            background-attachment: fixed;
            padding-bottom: 80px; 
            font-family: 'Segoe UI', Roboto, sans-serif;
            color: var(--text-main);
            overflow-x: hidden;
            user-select: none; /* Bloqueia seleção de texto */
        }

        [data-bs-theme="light"] body {
            --bg-dark: #f0f2f5;
            --bg-gradient: linear-gradient(180deg, #ffffff 0%, #e9ecef 100%);
            --card-bg: #ffffff;
            --text-main: #333333;
            color: #333;
        }
        [data-bs-theme="light"] .card-music { border: 1px solid #ccc; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        [data-bs-theme="light"] .letter-btn { background: #fff; color: #333; border: 1px solid #ddd; }
        [data-bs-theme="light"] .letter-btn.active { color: #000; }

        /* HEADER */
        .hero-header {
            background: linear-gradient(to bottom, #000 0%, #222 100%);
            padding: 20px; text-align: center;
            border-bottom: 3px solid var(--accent);
            box-shadow: 0 0 20px rgba(255, 215, 0, 0.2);
            border-radius: 0 0 25px 25px; margin-bottom: 25px; position: relative;
        }
        
        .theme-toggle {
            position: absolute; top: 15px; right: 15px;
            background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); 
            color: var(--accent); width: 40px; height: 40px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            cursor: pointer; z-index: 50; backdrop-filter: blur(4px);
        }

        .lion-img {
            max-width: 140px; height: auto; display: block; margin: 0 auto 5px auto;
            filter: drop-shadow(0 0 8px rgba(255, 215, 0, 0.3));
        }

        .brand-title {
            font-family: 'Arial Black', sans-serif; font-size: 2rem; color: var(--accent);
            text-transform: uppercase; letter-spacing: 2px; margin: 0;
            text-shadow: 2px 2px 0 #000;
        }
        .sub-title { color: #888; font-size: 0.8rem; letter-spacing: 2px; text-transform: uppercase; }

        /* BUSCA */
        .search-container { padding: 0 15px; margin-top: -15px; }
        .form-control-lg { 
            background: rgba(45, 45, 45, 0.9); border: 1px solid #555; 
            color: white; border-radius: 12px; padding: 12px 20px; 
        }
        [data-bs-theme="light"] .form-control-lg { background: #fff; color: #333; border: 1px solid #ccc; }
        .form-control-lg:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(255, 215, 0, 0.2); }

        /* FILTROS */
        .alphabet-bar {
            display: flex; flex-wrap: wrap; justify-content: center; gap: 6px; padding: 15px 10px;
        }
        .letter-btn {
            flex: 0 0 auto; width: 42px; height: 38px;
            border-radius: 8px; border: 1px solid #333;
            background: #1a1a1a; color: #888; font-weight: bold; font-size: 0.9rem;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            cursor: pointer; transition: 0.2s; line-height: 1;
        }
        .letter-btn-wide { width: auto; padding: 0 15px; }
        .letter-btn.active {
            background: var(--accent); color: #000; border-color: var(--accent);
            transform: scale(1.1); font-weight: 900; box-shadow: 0 0 10px rgba(255,215,0,0.4);
        }
        .letter-count { font-size: 0.6rem; opacity: 0.8; font-weight: normal; margin-top: 2px; }
        .letter-btn.active .letter-count { font-weight: bold; }
        
        .btn-fav-filter { background: #330000; border-color: #ff4444; color: #ff4444; }
        .btn-fav-filter.active { background: #ff4444; color: white; border-color: #ff4444; box-shadow: 0 0 10px rgba(255, 0, 0, 0.5); }

        /* LISTA DE MÚSICAS */
        .card-music { 
            background: var(--card-bg); 
            margin: 10px auto; padding: 15px 15px; border-radius: 10px; 
            display: flex; justify-content: space-between; align-items: center; 
            max-width: 800px; border-left: 4px solid var(--accent);
        }
        
        /* ÁREA DE TEXTO (Esquerda) */
        .info-col {
            flex: 1; 
            padding-right: 15px; 
            display: flex; 
            flex-direction: column;
            gap: 2px;
        }

        /* 1. ARTISTA (Dourado) */
        .music-artist {
            font-size: 0.85rem;
            color: var(--accent); 
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        [data-bs-theme="light"] .music-artist { color: #b89c08; }

        /* 2. MÚSICA (Branco - Destaque) */
        .music-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: #ffffff;
            line-height: 1.25;
            margin-bottom: 2px;
            white-space: normal; /* Quebra de linha permitida */
        }
        [data-bs-theme="light"] .music-title { color: #000; }

        /* 3. TRECHO DA LETRA (Cinza - Texto Puro) */
        .music-lyrics-snippet {
            font-size: 0.75rem;
            color: #777;
            font-weight: 400;
            font-style: italic;
            white-space: normal;
            display: -webkit-box;
            -webkit-line-clamp: 2; /* Limita a 2 linhas se for muito grande */
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        [data-bs-theme="light"] .music-lyrics-snippet { color: #666; }

        /* AÇÕES (Direita) */
        .card-actions { 
            display: flex; 
            flex-direction: row; 
            align-items: center; 
            gap: 12px; 
        }
        
        /* Botões de Ícone */
        .btn-icon { 
            font-size: 1.4rem; color: #555; transition: 0.2s; cursor: pointer; text-decoration: none;
            padding: 5px;
        }
        .btn-icon:hover { color: var(--accent); transform: scale(1.1); }
        .btn-icon.is-fav { color: #ff4444; animation: heartbeat 0.5s; }
        
        /* Botão Código */
        .code-box-wrapper { cursor: pointer; text-align: center; }
        .code-btn {
            background: #0d6efd; color: white;
            padding: 8px 10px; border-radius: 6px; font-weight: 900; font-size: 1.1rem;
            min-width: 75px; 
        }
        .code-label { font-size: 0.55rem; opacity: 0.6; margin-top: 3px; text-transform: uppercase; font-weight: bold; }

        @keyframes heartbeat { 0% { transform: scale(1); } 50% { transform: scale(1.3); } 100% { transform: scale(1); } }

        /* PAGINAÇÃO */
        .pagination { justify-content: center; margin-top: 25px; display: flex; gap: 10px; align-items: center; }
        .btn-page { width: 45px; height: 45px; border-radius: 50%; border: none; background: #333; color: white; font-size: 1.2rem; }
        .btn-page:hover:not(:disabled) { background: var(--accent); color: black; }
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
        <button class="theme-toggle" @click="toggleTheme"><i :class="isDark ? 'bi bi-moon-stars-fill' : 'bi bi-sun-fill'"></i></button>
        <img src="__IMAGEM_SRC__" class="lion-img" alt="Logo">
        <h1 class="brand-title">VIDEOKÊ</h1>
        <div class="sub-title">Catálogo Digital</div>
    </div>

    <div class="search-container">
        <input type="text" class="form-control form-control-lg" v-model="busca" placeholder="🔍 Digite música, cantor ou número..." @input="limparLetra()">
    </div>

    <div class="alphabet-bar">
        <div class="letter-btn letter-btn-wide btn-fav-filter" :class="{active: filtroLetra === 'FAV'}" @click="filtrarLetra('FAV')">
            <i class="bi bi-heart-fill"></i> <span class="letter-count">{{ favoritos.length }}</span>
        </div>
        <div class="letter-btn letter-btn-wide" :class="{active: filtroLetra === ''}" @click="filtrarLetra('')">
            TODOS <span class="letter-count">{{ db.length }}</span>
        </div>
        <div class="letter-btn" :class="{active: filtroLetra === '0-9'}" @click="filtrarLetra('0-9')">
            0-9 <span class="letter-count">{{ mapaContagem['0-9'] || 0 }}</span>
        </div>
        <div class="letter-btn" v-for="letra in alfabeto" :class="{active: filtroLetra === letra}" @click="filtrarLetra(letra)">
            {{ letra }} <span class="letter-count">{{ mapaContagem[letra] || 0 }}</span>
        </div>
    </div>
    
    <div class="text-center mt-2 small opacity-50">
        <span v-if="filtroLetra === 'FAV'">{{ favoritos.length }} músicas favoritas</span>
        <span v-else>{{ listaFiltrada.length }} músicas encontradas</span>
    </div>

    <div class="container pb-5">
        <div v-for="m in listaPaginada" :key="m.c" class="card-music">
            
            <div class="info-col">
                <div class="music-artist">{{ m.a }}</div>
                
                <div class="music-title">{{ m.m }}</div>
                
                <div class="music-lyrics-snippet" v-if="m.l">{{ m.l }}</div>
                <div class="music-lyrics-snippet" v-else>Letra da música</div>
            </div>
            
            <div class="card-actions">
                
                <i class="bi btn-icon" 
                   :class="isFavorito(m.c) ? 'bi-heart-fill is-fav' : 'bi-heart'"
                   @click="toggleFavorito(m)"
                   title="Favoritar"></i>
                
                <a :href="'https://www.google.com/search?q=letra+' + m.a + '+' + m.m" 
                   target="_blank" 
                   class="bi bi-search btn-icon" 
                   title="Pesquisar Letra no Google"></a>

                <div class="code-box-wrapper" @click="copiar(m.c)">
                    <div class="code-btn">{{ m.c }}</div>
                    <div class="code-label">Copiar</div>
                </div>
            </div>
        </div>
        
        <div v-if="filtroLetra === 'FAV' && favoritos.length === 0" class="text-center mt-5 text-muted">
            <h3>💔 Nada por aqui</h3>
            <p>Clique no coração das músicas para salvar seus favoritos!</p>
        </div>

        <div class="pagination" v-if="totalPaginas > 1">
            <button class="btn-page" @click="mudarPagina(-1)" :disabled="pagina===1">❮</button>
            <span class="fw-bold align-self-center">{{ pagina }} / {{ totalPaginas }}</span>
            <button class="btn-page" @click="mudarPagina(1)" :disabled="pagina===totalPaginas">❯</button>
        </div>
        
        <div class="text-center mt-4 text-muted small">Karaokê - Catálogo Oficial</div>
    </div>

    __BOTAO_DOWNLOAD__
</div>

<script>
    const musicas = __DADOS_AQUI__;
    const { createApp } = Vue;

    createApp({
        data() { return { 
            db: musicas, busca: '', filtroLetra: '', pagina: 1, porPagina: 50,
            isDark: true, alfabeto: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split(''),
            favoritos: []
        }},
        mounted() {
            if (localStorage.getItem('theme') === 'light') this.isDark = false;
            this.applyTheme();
            if (localStorage.getItem('karaoke_favs')) this.favoritos = JSON.parse(localStorage.getItem('karaoke_favs'));
        },
        computed: {
            mapaContagem() {
                const map = {}; this.db.forEach(m => { if(m.a) { const c = m.a.charAt(0).toUpperCase(); /[0-9]/.test(c) ? map['0-9'] = (map['0-9']||0)+1 : map[c] = (map[c]||0)+1; }}); return map;
            },
            listaFiltrada() {
                let res = this.db;
                if (this.filtroLetra === 'FAV') return res.filter(m => this.favoritos.includes(m.c));
                if (this.filtroLetra) {
                    this.filtroLetra === '0-9' ? res = res.filter(m => /^[0-9]/.test(m.a)) : res = res.filter(m => m.a.toUpperCase().startsWith(this.filtroLetra));
                }
                if (this.busca) { const t = this.busca.toLowerCase(); res = res.filter(m => m.a.toLowerCase().includes(t) || m.m.toLowerCase().includes(t) || m.c.includes(t)); }
                return res;
            },
            totalPaginas() { return Math.ceil(this.listaFiltrada.length / this.porPagina); },
            listaPaginada() { 
                if (this.listaFiltrada.length === 0) return [];
                const i = (this.pagina - 1) * this.porPagina;
                return this.listaFiltrada.slice(i, i + this.porPagina); 
            }
        },
        methods: {
            copiar(t) { navigator.clipboard.writeText(t).then(() => alert('Código ' + t + ' copiado!')); },
            mudarPagina(d) { this.pagina += d; window.scrollTo(0, 0); },
            filtrarLetra(l) { this.filtroLetra = l; this.busca = ''; this.pagina = 1; },
            limparLetra() { if(this.busca) this.filtroLetra = ''; this.pagina = 1; },
            toggleTheme() { this.isDark = !this.isDark; this.applyTheme(); localStorage.setItem('theme', this.isDark ? 'dark' : 'light'); },
            applyTheme() { document.documentElement.setAttribute('data-bs-theme', this.isDark ? 'dark' : 'light'); },
            isFavorito(c) { return this.favoritos.includes(c); },
            toggleFavorito(m) { 
                this.isFavorito(m.c) ? this.favoritos = this.favoritos.filter(c => c !== m.c) : this.favoritos.push(m.c); 
                localStorage.setItem('karaoke_favs', JSON.stringify(this.favoritos)); 
            }
        }
    }).mount('#app');
</script>
</body>
</html>
"""

def encontrar_imagem_local():
    for nome in NOME_IMAGEM:
        if os.path.exists(nome): return nome
    return None

def imagem_para_base64(caminho_arquivo):
    if not caminho_arquivo: return "https://cdn-icons-png.flaticon.com/512/3408/3408764.png"
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
                    artista_cru = match.group(1).strip()
                    # Bloqueia "UM" e outros lixos comuns de cabeçalho
                    if artista_cru.upper() == "UM" or len(artista_cru) < 2: continue
                    
                    codigo = match.group(2).strip()
                    
                    # Tenta separar Título da Letra (quebra por espaço duplo se houver)
                    resto = match.group(3).strip()
                    partes = re.split(r'\s{2,}', resto, maxsplit=1)
                    titulo = partes[0]
                    letra_snippet = partes[1] if len(partes) > 1 else ""

                    if codigo not in vistos:
                        lista.append({
                            "a": artista_cru, 
                            "c": codigo, 
                            "m": titulo,
                            "l": letra_snippet # Campo novo: Letra
                        })
                        vistos.add(codigo)
        lista.sort(key=lambda x: x['a'].lower())
        return lista
    except: return []

CACHE_MUSICAS = processar_pdf()

@app.route('/')
def index():
    dados_json = json.dumps(CACHE_MUSICAS, ensure_ascii=False)
    caminho_img = encontrar_imagem_local()
    src_img = f"/{caminho_img}" if caminho_img else "https://cdn-icons-png.flaticon.com/512/3408/3408764.png"
    btn = '<a href="/baixar" class="fab-download"><i class="bi bi-download"></i></a>'
    return HTML_TEMPLATE.replace('__DADOS_AQUI__', dados_json)\
                        .replace('__BOTAO_DOWNLOAD__', btn)\
                        .replace('__IMAGEM_SRC__', src_img)

@app.route('/<path:filename>')
def serve_static(filename):
    if filename in NOME_IMAGEM and os.path.exists(filename): return send_file(filename)
    return "Arquivo não encontrado", 404

@app.route('/baixar')
def baixar():
    caminho_img = encontrar_imagem_local()
    img_code = imagem_para_base64(caminho_img)
    dados_json = json.dumps(CACHE_MUSICAS, ensure_ascii=False)
    html_final = HTML_TEMPLATE.replace('__DADOS_AQUI__', dados_json)\
                              .replace('__BOTAO_DOWNLOAD__', '')\
                              .replace('__IMAGEM_SRC__', img_code)
    return Response(html_final.encode('utf-8'), mimetype="text/html; charset=utf-8", headers={"Content-disposition": "attachment; filename=Catalogo_Videoke.html"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
