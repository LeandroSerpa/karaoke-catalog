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

# --- LAYOUT HTML/VUE (SUPER APP VERSION) ---
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
        }

        /* TEMA CLARO */
        [data-bs-theme="light"] body {
            --bg-dark: #f0f2f5;
            --bg-gradient: linear-gradient(180deg, #ffffff 0%, #e9ecef 100%);
            --card-bg: #ffffff;
            --text-main: #333333;
            color: #333;
        }
        [data-bs-theme="light"] .card-music { border: 1px solid #ccc; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        [data-bs-theme="light"] .title { color: #000; }
        [data-bs-theme="light"] .letter-btn { background: #fff; color: #333; border: 1px solid #ddd; }
        [data-bs-theme="light"] .letter-btn.active { color: #000; }
        [data-bs-theme="light"] .modal-content { background: #fff; color: #333; }

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
            max-width: 130px; height: auto; display: block; margin: 0 auto 5px auto;
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

        /* ABAS A-Z + FAVORITOS */
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
        
        /* Botão de Favoritos */
        .btn-fav-filter {
            background: #330000; border-color: #ff4444; color: #ff4444;
        }
        .btn-fav-filter.active {
            background: #ff4444; color: white; border-color: #ff4444;
            box-shadow: 0 0 10px rgba(255, 0, 0, 0.5);
        }

        /* LISTA */
        .card-music { 
            background: var(--card-bg); 
            margin: 10px auto; padding: 12px 15px; border-radius: 10px; 
            display: flex; justify-content: space-between; align-items: center; 
            max-width: 800px; border-left: 4px solid var(--accent);
            position: relative;
        }
        .artist { color: var(--accent); font-weight: bold; font-size: 0.8rem; text-transform: uppercase; }
        [data-bs-theme="light"] .artist { color: #d4b106; }
        .title { font-weight: 600; font-size: 1rem; color: var(--text-main); line-height: 1.2; }
        
        .code-btn {
            background: #0d6efd; color: white;
            padding: 8px 10px; border-radius: 6px; font-weight: 900; font-size: 1.1rem;
            min-width: 75px; text-align: center;
        }
        .code-label { font-size: 0.55rem; text-align: center; opacity: 0.6; margin-top: 3px; text-transform: uppercase; }

        /* AÇÕES DO CARD */
        .card-actions {
            display: flex; gap: 10px; align-items: center;
        }
        .btn-icon {
            font-size: 1.2rem; color: #666; cursor: pointer; padding: 5px; transition: 0.2s;
        }
        .btn-icon.is-fav { color: #ff4444; animation: heartbeat 1s; }
        @keyframes heartbeat { 0% { transform: scale(1); } 50% { transform: scale(1.3); } 100% { transform: scale(1); } }

        /* MODAL (DETALHES DA MÚSICA) */
        .modal-overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.85); z-index: 2000;
            display: flex; align-items: center; justify-content: center;
            backdrop-filter: blur(5px); animation: fadeIn 0.3s;
        }
        .modal-content {
            background: #1a1a1a; width: 90%; max-width: 500px;
            border-radius: 20px; padding: 30px; text-align: center;
            border: 2px solid var(--accent);
            box-shadow: 0 0 30px rgba(255, 215, 0, 0.2);
            position: relative; animation: slideUp 0.3s;
        }
        .close-modal {
            position: absolute; top: 15px; right: 20px; font-size: 1.5rem;
            color: #888; cursor: pointer; background: none; border: none;
        }
        .modal-code {
            font-size: 3rem; font-weight: 900; color: white;
            background: #0d6efd; display: inline-block;
            padding: 10px 30px; border-radius: 15px; margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(13, 110, 253, 0.4);
        }
        .modal-title { font-size: 1.5rem; font-weight: bold; margin-bottom: 10px; color: var(--text-main); }
        .modal-artist { font-size: 1.2rem; color: var(--accent); text-transform: uppercase; margin-bottom: 30px; }
        .btn-search-lyrics {
            background: transparent; border: 1px solid var(--accent); color: var(--accent);
            padding: 10px 20px; border-radius: 30px; text-decoration: none;
            font-weight: bold; display: inline-block; transition: 0.2s;
        }
        .btn-search-lyrics:hover { background: var(--accent); color: black; }

        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes slideUp { from { transform: translateY(50px); } to { transform: translateY(0); } }

        /* PAGINAÇÃO */
        .pagination { justify-content: center; margin-top: 25px; display: flex; gap: 10px; align-items: center; }
        .btn-page { width: 45px; height: 45px; border-radius: 50%; border: none; background: #333; color: white; font-size: 1.2rem; }
        [data-bs-theme="light"] .btn-page { background: #ddd; color: #333; }
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
    
    <div class="modal-overlay" v-if="modalVisible" @click.self="fecharModal">
        <div class="modal-content">
            <button class="close-modal" @click="fecharModal">&times;</button>
            
            <div class="modal-code" @click="copiar(musicaSelecionada.c)">{{ musicaSelecionada.c }}</div>
            <div class="small text-muted mb-3">Toque para copiar</div>
            
            <h3 class="modal-title">{{ musicaSelecionada.m }}</h3>
            <div class="modal-artist">{{ musicaSelecionada.a }}</div>
            
            <hr style="border-color: #444; margin: 20px 0;">
            
            <p class="text-muted small">
                Se a letra estiver disponível no arquivo, apareceria aqui. 
                Caso contrário, use o botão abaixo:
            </p>
            
            <a :href="'https://www.google.com/search?q=letra+' + musicaSelecionada.a + '+' + musicaSelecionada.m" 
               target="_blank" class="btn-search-lyrics">
               <i class="bi bi-music-note-beamed"></i> Ver Letra Completa Online
            </a>
        </div>
    </div>

    <div class="hero-header">
        <button class="theme-toggle" @click="toggleTheme">
            <i :class="isDark ? 'bi bi-moon-stars-fill' : 'bi bi-sun-fill'"></i>
        </button>

        <img src="__IMAGEM_SRC__" class="lion-img" alt="Logo">
        <h1 class="brand-title">VIDEOKÊ</h1>
        <div class="sub-title">Catálogo Digital</div>
    </div>

    <div class="search-container">
        <input type="text" class="form-control form-control-lg" v-model="busca" placeholder="🔍 Digite música, cantor ou número..." @input="limparLetra()">
    </div>

    <div class="alphabet-bar">
        <div class="letter-btn letter-btn-wide btn-fav-filter" :class="{active: filtroLetra === 'FAV'}" @click="filtrarLetra('FAV')">
            <i class="bi bi-heart-fill"></i>
            <span class="letter-count">{{ favoritos.length }}</span>
        </div>

        <div class="letter-btn letter-btn-wide" :class="{active: filtroLetra === ''}" @click="filtrarLetra('')">
            TODOS
            <span class="letter-count">{{ db.length }}</span>
        </div>
        
        <div class="letter-btn" :class="{active: filtroLetra === '0-9'}" @click="filtrarLetra('0-9')">
            0-9
            <span class="letter-count">{{ mapaContagem['0-9'] || 0 }}</span>
        </div>

        <div class="letter-btn" v-for="letra in alfabeto" :class="{active: filtroLetra === letra}" @click="filtrarLetra(letra)">
            {{ letra }}
            <span class="letter-count">{{ mapaContagem[letra] || 0 }}</span>
        </div>
    </div>
    
    <div class="text-center mt-2 small opacity-50">
        <span v-if="filtroLetra === 'FAV'">{{ favoritos.length }} músicas favoritas</span>
        <span v-else>{{ listaFiltrada.length }} músicas encontradas</span>
    </div>

    <div class="container pb-5">
        <div v-for="m in listaPaginada" :key="m.c" class="card-music">
            <div style="flex: 1; padding-right: 10px; cursor: pointer;" @click="abrirModal(m)">
                <div class="artist">{{ m.a }}</div>
                <div class="title">{{ m.m }}</div>
            </div>
            
            <div class="card-actions">
                <i class="bi btn-icon" 
                   :class="isFavorito(m.c) ? 'bi-heart-fill is-fav' : 'bi-heart'"
                   @click.stop="toggleFavorito(m)"></i>
                   
                <i class="bi bi-eye-fill btn-icon" style="color: var(--accent)" @click.stop="abrirModal(m)"></i>

                <div @click.stop="copiar(m.c)">
                    <div class="code-btn">{{ m.c }}</div>
                    <div class="code-label">Copiar</div>
                </div>
            </div>
        </div>
        
        <div v-if="filtroLetra === 'FAV' && favoritos.length === 0" class="text-center mt-5 text-muted">
            <h3>💔 Nenhum favorito ainda</h3>
            <p>Toque no coração ao lado das músicas para salvar aqui!</p>
        </div>

        <div class="pagination" v-if="totalPaginas > 1">
            <button class="btn-page" @click="mudarPagina(-1)" :disabled="pagina===1">❮</button>
            <span class="fw-bold align-self-center">{{ pagina }} / {{ totalPaginas }}</span>
            <button class="btn-page" @click="mudarPagina(1)" :disabled="pagina===totalPaginas">❯</button>
        </div>
        
        <div class="text-center mt-4 text-muted small">Catálogo Karaokê Oficial</div>
    </div>

    __BOTAO_DOWNLOAD__
</div>

<script>
    const musicas = __DADOS_AQUI__;
    
    const { createApp } = Vue;
    createApp({
        data() { return { 
            db: musicas, 
            busca: '', 
            filtroLetra: '', 
            pagina: 1, 
            porPagina: 50,
            isDark: true,
            alfabeto: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split(''),
            favoritos: [], // Lista de códigos favoritos
            modalVisible: false,
            musicaSelecionada: {}
        }},
        mounted() {
            // Recupera tema
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme === 'light') { this.isDark = false; }
            this.applyTheme();

            // Recupera favoritos
            const savedFavs = localStorage.getItem('karaoke_favs');
            if (savedFavs) { this.favoritos = JSON.parse(savedFavs); }
        },
        computed: {
            mapaContagem() {
                const map = {};
                this.db.forEach(m => {
                    if(m.a) {
                        const char = m.a.charAt(0).toUpperCase();
                        if (/[0-9]/.test(char)) { map['0-9'] = (map['0-9'] || 0) + 1; } 
                        else { map[char] = (map[char] || 0) + 1; }
                    }
                });
                return map;
            },
            listaFiltrada() {
                let res = this.db;

                // Filtro FAVORITOS
                if (this.filtroLetra === 'FAV') {
                    return res.filter(m => this.favoritos.includes(m.c));
                }

                if (this.filtroLetra) {
                    if (this.filtroLetra === '0-9') { res = res.filter(m => /^[0-9]/.test(m.a)); } 
                    else { res = res.filter(m => m.a.toUpperCase().startsWith(this.filtroLetra)); }
                }

                if (this.busca) {
                    const t = this.busca.toLowerCase();
                    res = res.filter(m => 
                        m.a.toLowerCase().includes(t) || 
                        m.m.toLowerCase().includes(t) || 
                        m.c.includes(t)
                    );
                }
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
            filtrarLetra(l) { 
                this.filtroLetra = l; 
                this.busca = ''; 
                this.pagina = 1; 
            },
            limparLetra() { 
                if(this.busca) this.filtroLetra = ''; 
                this.pagina = 1; 
            },
            toggleTheme() {
                this.isDark = !this.isDark;
                this.applyTheme();
                localStorage.setItem('theme', this.isDark ? 'dark' : 'light');
            },
            applyTheme() {
                document.documentElement.setAttribute('data-bs-theme', this.isDark ? 'dark' : 'light');
            },
            // NOVOS MÉTODOS DE FAVORITOS
            isFavorito(codigo) {
                return this.favoritos.includes(codigo);
            },
            toggleFavorito(m) {
                if (this.isFavorito(m.c)) {
                    this.favoritos = this.favoritos.filter(code => code !== m.c);
                } else {
                    this.favoritos.push(m.c);
                }
                localStorage.setItem('karaoke_favs', JSON.stringify(this.favoritos));
            },
            // NOVOS MÉTODOS DO MODAL
            abrirModal(m) {
                this.musicaSelecionada = m;
                this.modalVisible = true;
            },
            fecharModal() {
                this.modalVisible = false;
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
    if not caminho_arquivo:
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
    dados_json = json.dumps(CACHE_MUSICAS, ensure_ascii=False)
    caminho_img = encontrar_imagem_local()
    if caminho_img: src_img = f"/{caminho_img}"
    else: src_img = "https://cdn-icons-png.flaticon.com/512/3408/3408764.png"
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
