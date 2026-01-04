import os
import re
import json
import base64
import urllib.request
from flask import Flask, render_template_string, Response
from pypdf import PdfReader

app = Flask(__name__)

# --- CONFIGURAÇÕES ---
PDF_FILE = "catalogo.pdf"

# Link da Imagem do Leão (Você pode trocar esse link por qualquer outro JPG/PNG que quiser)
# Escolhi um Leão Neon Azul Cibernético para combinar com o tema
URL_LEAO = "https://img.freepik.com/fotos-premium/leao-usando-fones-de-ouvido-fundo-de-dj-neon-conceito-de-musica-ia-generativa_118086-13723.jpg"

# --- LAYOUT ÚNICO ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-br" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Catálogo Karaokê</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <style>
        :root {
            /* TEMA AZUL PROFISSIONAL & NEON */
            --bg-dark: #0f172a;
            --bg-gradient-dark: linear-gradient(180deg, #020617 0%, #1e293b 100%);
            
            --bg-light: #f8fafc;
            --bg-gradient-light: linear-gradient(180deg, #f1f5f9 0%, #cbd5e1 100%);
            
            --card-dark: rgba(30, 41, 59, 0.9);
            --card-light: #ffffff;
            
            --text-dark: #f1f5f9;
            --text-light: #1e293b;
            
            --accent: #38bdf8; /* Azul Neon */
            --code-bg: #0369a1;
        }

        body { 
            background: var(--bg-dark); 
            background-image: var(--bg-gradient-dark);
            background-attachment: fixed;
            padding-bottom: 80px; 
            font-family: 'Segoe UI', Roboto, sans-serif;
            color: var(--text-dark);
            transition: 0.3s;
        }

        /* MODO CLARO */
        [data-bs-theme="light"] body {
            background: var(--bg-light);
            background-image: var(--bg-gradient-light);
            color: var(--text-light);
        }
        [data-bs-theme="light"] .card-music { background: var(--card-light); border-color: #cbd5e1; }
        [data-bs-theme="light"] .title { color: #0f172a; }
        [data-bs-theme="light"] .artist { color: #0284c7; }
        [data-bs-theme="light"] .form-control-lg { background: white; color: #333; border-color: #cbd5e1; }
        [data-bs-theme="light"] .letter-btn { background: white; color: #333; border: 1px solid #ddd; }
        [data-bs-theme="light"] .letter-btn.active { background: var(--accent); color: white; border-color: var(--accent); }

        /* HEADER */
        .hero-header {
            background: linear-gradient(135deg, #020617 0%, #172554 100%);
            padding: 30px 20px 15px 20px;
            text-align: center;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            position: relative;
            overflow: hidden;
            border-bottom-left-radius: 30px;
            border-bottom-right-radius: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            margin-bottom: 20px;
        }
        
        /* A FOTO DO LEÃO REAL */
        .lion-img {
            width: 140px; height: 140px;
            object-fit: cover;
            border-radius: 50%;
            border: 4px solid var(--accent);
            box-shadow: 0 0 20px rgba(56, 189, 248, 0.6);
            margin-bottom: 10px;
            animation: pulse 3s infinite;
        }
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.7); }
            70% { box-shadow: 0 0 0 15px rgba(56, 189, 248, 0); }
            100% { box-shadow: 0 0 0 0 rgba(56, 189, 248, 0); }
        }

        .app-title {
            font-weight: 800; font-size: 1.8rem; margin: 0;
            text-transform: uppercase; letter-spacing: 2px;
            color: white; text-shadow: 0 2px 10px rgba(0,0,0,0.8);
        }

        /* CONTROLES */
        .theme-toggle {
            position: absolute; top: 20px; right: 20px;
            background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); 
            color: white; width: 40px; height: 40px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            cursor: pointer; z-index: 20; backdrop-filter: blur(5px);
        }

        .search-container {
            padding: 0 15px; position: relative; z-index: 10;
        }
        .form-control-lg { 
            background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1); 
            color: white; border-radius: 15px; padding: 15px 20px; 
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            font-size: 1.1rem;
        }
        .form-control-lg:focus { border-color: var(--accent); box-shadow: 0 0 0 4px rgba(56, 189, 248, 0.25); }

        /* BARRA ALFABÉTICA (FILTROS) */
        .alphabet-bar {
            display: flex; overflow-x: auto; gap: 8px; padding: 15px;
            -webkit-overflow-scrolling: touch; scrollbar-width: none;
        }
        .alphabet-bar::-webkit-scrollbar { display: none; }
        
        .letter-btn {
            flex: 0 0 auto; min-width: 50px; height: 45px; 
            padding: 0 15px; border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(30, 41, 59, 0.7);
            color: #94a3b8; font-weight: bold; font-size: 0.9rem;
            display: flex; align-items: center; justify-content: center;
            cursor: pointer; transition: 0.2s; white-space: nowrap;
        }
        .letter-btn.active {
            background: var(--accent); color: #0f172a;
            box-shadow: 0 0 15px rgba(56, 189, 248, 0.5);
            border-color: var(--accent); transform: scale(1.05);
        }
        .letter-count {
            font-size: 0.7rem; margin-left: 6px; opacity: 0.7; font-weight: normal;
        }
        .letter-btn.active .letter-count { opacity: 1; font-weight: bold; }

        /* LISTA */
        .card-music { 
            background: var(--card-dark); 
            margin: 10px auto; padding: 15px 20px; border-radius: 12px; 
            display: flex; justify-content: space-between; align-items: center; 
            max-width: 800px; border-left: 4px solid var(--accent);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .info { flex: 1; padding-right: 15px; overflow: hidden; }
        .artist { 
            color: var(--accent); font-weight: 800; font-size: 0.85rem; 
            text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }
        .title { font-weight: 600; font-size: 1.05rem; line-height: 1.2; color: inherit; }

        .code-btn {
            background: var(--code-bg); color: white;
            padding: 8px 14px; border-radius: 8px;
            font-weight: 800; font-size: 1.2rem;
            text-align: center; min-width: 80px; cursor: pointer;
            box-shadow: 0 3px 8px rgba(0,0,0,0.2);
        }
        .code-btn:active { transform: scale(0.95); }
        .code-label { font-size: 0.6rem; margin-top: 4px; text-transform: uppercase; opacity: 0.7; text-align: center; }

        .pagination { justify-content: center; margin-top: 25px; display: flex; gap: 10px; align-items: center; }
        .btn-page { 
            width: 50px; height: 50px; border-radius: 10px; border: none; 
            background: rgba(255,255,255,0.05); color: inherit; 
            font-size: 1.3rem; 
        }
        .btn-page:hover:not(:disabled) { background: var(--accent); color: #0f172a; }
        .btn-page:disabled { opacity: 0.3; }

        .footer-note { 
            text-align: center; margin-top: 40px; padding: 20px;
            color: #64748b; font-size: 0.9rem; border-top: 1px solid rgba(255,255,255,0.05);
        }

        .fab-download {
            position: fixed; bottom: 25px; right: 25px;
            background: #10b981; color: white;
            width: 65px; height: 65px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.8rem; box-shadow: 0 10px 25px rgba(16, 185, 129, 0.4);
            text-decoration: none; z-index: 1000;
        }
    </style>
</head>
<body>
<div id="app">
    
    <div class="hero-header">
        <button class="theme-toggle" @click="toggleTheme">
            <i :class="isDark ? 'bi bi-moon-stars-fill' : 'bi bi-sun-fill'"></i>
        </button>
        
        <img src="__IMAGEM_SRC__" class="lion-img" alt="Leão Karaokê">
        
        <h1 class="app-title">Catálogo<br><span style="color:var(--accent)">Karaokê</span></h1>
    </div>

    <div class="search-container">
        <input type="text" class="form-control form-control-lg" v-model="busca" placeholder="🔍 Pesquisar música ou cantor..." @input="limparLetra()">
    </div>

    <div class="alphabet-bar">
        <div class="letter-btn" :class="{active: filtroLetra === ''}" @click="filtrarLetra('')">
            TODOS <span class="letter-count">({{ db.length }})</span>
        </div>
        <div class="letter-btn" v-for="letra in alfabeto" :class="{active: filtroLetra === letra}" @click="filtrarLetra(letra)">
            {{ letra }} <span class="letter-count" v-if="mapaContagem[letra]">({{ mapaContagem[letra] }})</span>
        </div>
    </div>
    
    <div class="text-center mt-2 small opacity-75">{{ listaFiltrada.length }} músicas exibidas</div>

    <div class="container">
        <div v-for="m in listaPaginada" :key="m.c" class="card-music">
            <div class="info">
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
            <span class="fw-bold opacity-75">{{ pagina }} / {{ totalPaginas }}</span>
            <button class="btn-page" @click="mudarPagina(1)" :disabled="pagina===totalPaginas"><i class="bi bi-chevron-right"></i></button>
        </div>
        
        <div class="footer-note">
            Catálogo Digital Oficial
        </div>
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
            alfabeto: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')
        }},
        mounted() {
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme) {
                this.isDark = savedTheme === 'dark';
            }
            this.applyTheme();
        },
        computed: {
            mapaContagem() {
                const map = {};
                this.db.forEach(m => {
                    if(m.a) {
                        const primeiraLetra = m.a.charAt(0).toUpperCase();
                        if(!map[primeiraLetra]) map[primeiraLetra] = 0;
                        map[primeiraLetra]++;
                    }
                });
                return map;
            },
            listaFiltrada() {
                let resultado = this.db;
                if (this.filtroLetra) {
                    resultado = resultado.filter(m => m.a.toUpperCase().startsWith(this.filtroLetra));
                }
                if (this.busca) {
                    const t = this.busca.toLowerCase();
                    resultado = resultado.filter(m => m.a.toLowerCase().includes(t) || m.m.toLowerCase().includes(t) || m.c.includes(t));
                }
                return resultado;
            },
            totalPaginas() { return Math.ceil(this.listaFiltrada.length / this.porPagina); },
            listaPaginada() {
                const i = (this.pagina - 1) * this.porPagina;
                return this.listaFiltrada.slice(i, i + this.porPagina);
            }
        },
        methods: {
            copiar(texto) { navigator.clipboard.writeText(texto).then(() => alert('Código ' + texto + ' copiado!')); },
            mudarPagina(d) { this.pagina += d; window.scrollTo(0, 0); },
            filtrarLetra(letra) {
                this.filtroLetra = letra;
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
            }
        }
    }).mount('#app');
</script>
</body>
</html>
"""

# Função para baixar imagem da web e converter para Base64 (Texto)
def obter_imagem_base64():
    try:
        # Usa headers para fingir ser um navegador e evitar bloqueio
        req = urllib.request.Request(
            URL_LEAO, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req) as response:
            dados = response.read()
            b64 = base64.b64encode(dados).decode('utf-8')
            return f"data:image/jpeg;base64,{b64}"
    except Exception as e:
        print(f"Erro ao baixar imagem: {e}")
        # Se der erro, retorna um placeholder cinza
        return "https://via.placeholder.com/150"

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
    # Na versão online, usa o link direto (carrega mais rápido)
    dados_json = json.dumps(CACHE_MUSICAS)
    btn_html = '<a href="/baixar" class="fab-download" title="Baixar App"><i class="bi bi-download"></i></a>'
    return HTML_TEMPLATE.replace('__DADOS_AQUI__', dados_json)\
                        .replace('__BOTAO_DOWNLOAD__', btn_html)\
                        .replace('__IMAGEM_SRC__', URL_LEAO)

@app.route('/baixar')
def baixar():
    # Na versão baixada, EMBUTE a imagem real (Base64)
    print("Baixando imagem e convertendo para Base64...")
    imagem_b64 = obter_imagem_base64()
    
    dados_json = json.dumps(CACHE_MUSICAS)
    html_final = HTML_TEMPLATE.replace('__DADOS_AQUI__', dados_json)\
                              .replace('__BOTAO_DOWNLOAD__', '')\
                              .replace('__IMAGEM_SRC__', imagem_b64)
    
    return Response(
        html_final,
        mimetype="text/html",
        headers={"Content-disposition": "attachment; filename=Catalogo_Karaoke.html"}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
