import os
import re
import json
from flask import Flask, render_template_string, Response
from pypdf import PdfReader

app = Flask(__name__)

# CONFIGURAÇÃO
PDF_FILE = "catalogo.pdf"

# --- LAYOUT ÚNICO (Serve tanto para o site online quanto para o arquivo baixado) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-br" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Catálogo de Karaokê 🎤</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <style>
        :root {
            --bg-gradient-dark: linear-gradient(135deg, #12001f 0%, #290038 100%);
            --bg-gradient-light: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            --card-bg-dark: rgba(255, 255, 255, 0.05);
            --card-bg-light: rgba(255, 255, 255, 0.8);
            --text-main-dark: #eee;
            --text-main-light: #333;
            --highlight: #ff00cc;
        }

        body { 
            background: var(--bg-gradient-dark); 
            background-attachment: fixed;
            padding-bottom: 80px; 
            font-family: 'Segoe UI', Roboto, sans-serif;
            color: var(--text-main-dark);
            transition: background 0.5s;
        }

        /* Modo Claro (Sobrescrita) */
        [data-bs-theme="light"] body {
            background: var(--bg-gradient-light);
            color: var(--text-main-light);
        }
        [data-bs-theme="light"] .card-music {
            background: var(--card-bg-light);
            border: 1px solid rgba(0,0,0,0.1);
            color: #333;
        }
        [data-bs-theme="light"] .title { color: #333; }
        [data-bs-theme="light"] .form-control-lg {
            background: white; color: #333; border: 1px solid #ccc;
        }
        [data-bs-theme="light"] .form-control-lg::placeholder { color: #666; }

        /* Cabeçalho */
        .header-bar {
            display: flex; justify-content: space-between; align-items: center;
            padding: 15px 20px;
            background: rgba(0,0,0,0.2);
            backdrop-filter: blur(5px);
        }
        .header-title { font-weight: 900; font-size: 1.2rem; margin: 0; text-transform: uppercase; letter-spacing: 1px; }

        /* Botão de Tema */
        .theme-toggle {
            background: none; border: none; color: inherit; font-size: 1.5rem; cursor: pointer; transition: 0.3s;
        }
        .theme-toggle:hover { transform: rotate(20deg); color: var(--highlight); }

        /* Busca */
        .search-box-container { 
            position: sticky; top: 0; z-index: 100; 
            background: rgba(0, 0, 0, 0.3); 
            backdrop-filter: blur(15px); 
            padding: 15px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.1); 
        }
        [data-bs-theme="light"] .search-box-container { background: rgba(255, 255, 255, 0.6); }

        .form-control-lg { 
            background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); 
            color: white; border-radius: 50px; padding-left: 20px; 
        }
        .form-control-lg:focus { box-shadow: 0 0 0 0.25rem rgba(255, 0, 204, 0.25); border-color: var(--highlight); }

        /* Cards de Música */
        .card-music { 
            background: var(--card-bg-dark); 
            margin: 10px auto; padding: 15px; border-radius: 16px; 
            border: 1px solid rgba(255, 255, 255, 0.1);
            display: flex; justify-content: space-between; align-items: center; 
            max-width: 800px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        .info { flex: 1; padding-right: 15px; }
        .artist { color: var(--highlight); font-weight: 700; font-size: 0.85rem; text-transform: uppercase; margin-bottom: 2px; }
        .title { font-weight: 600; font-size: 1.1rem; line-height: 1.2; color: #eee; }

        /* Código */
        .code-box {
            background: linear-gradient(45deg, #ffcc00, #ff9900);
            color: #440000;
            padding: 8px 15px; border-radius: 12px;
            font-weight: 900; font-size: 1.4rem;
            text-align: center; min-width: 80px;
            cursor: pointer; box-shadow: 0 4px 10px rgba(255, 153, 0, 0.3);
            border: 2px solid rgba(255,255,255,0.2);
        }
        .code-box:active { transform: scale(0.95); }
        .copy-label { font-size: 0.6rem; text-transform: uppercase; font-weight: bold; margin-top: 3px; opacity: 0.8;}

        /* Paginação */
        .pagination { justify-content: center; margin-top: 30px; display: flex; gap: 15px; align-items: center; }
        .btn-page { 
            width: 45px; height: 45px; border-radius: 50%; border: none; 
            background: rgba(255,255,255,0.1); color: inherit; 
            font-size: 1.2rem; transition: 0.2s; 
        }
        [data-bs-theme="light"] .btn-page { background: rgba(0,0,0,0.1); }
        .btn-page:hover:not(:disabled) { background: var(--highlight); color: white; }
        .btn-page:disabled { opacity: 0.3; }

        /* Botão Flutuante de Download (Só aparece no modo Online) */
        .fab-download {
            position: fixed; bottom: 20px; right: 20px;
            background: #28a745; color: white;
            width: 60px; height: 60px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.8rem; box-shadow: 0 5px 20px rgba(0,0,0,0.4);
            text-decoration: none; z-index: 1000; transition: 0.3s;
            animation: bounce 2s infinite;
        }
        .fab-download:hover { transform: scale(1.1); background: #218838; color: white; }
        @keyframes bounce { 0%, 20%, 50%, 80%, 100% {transform: translateY(0);} 40% {transform: translateY(-10px);} 60% {transform: translateY(-5px);} }
        
        .hide-on-offline { display: none; }
    </style>
</head>
<body>
<div id="app">
    <div class="header-bar">
        <h1 class="header-title">🎤 Karaokê <span style="color:var(--highlight)">Vibes</span></h1>
        <button class="theme-toggle" @click="toggleTheme">
            <i :class="isDark ? 'bi bi-moon-stars-fill' : 'bi bi-sun-fill'"></i>
        </button>
    </div>

    <div class="search-box-container">
        <input type="text" class="form-control form-control-lg" v-model="busca" placeholder="🔍 Buscar música, cantor ou código..." @input="pagina=1">
        <div class="text-center mt-2 small opacity-75">{{ listaFiltrada.length }} músicas encontradas</div>
    </div>

    <div class="container mt-2">
        <div v-for="m in listaPaginada" :key="m.c" class="card-music">
            <div class="info">
                <div class="artist">{{ m.a }}</div>
                <div class="title">{{ m.m }}</div>
            </div>
            <div @click="copiar(m.c)" class="text-center">
                <div class="code-box">{{ m.c }}</div>
                <div class="copy-label">Copiar</div>
            </div>
        </div>

        <div class="pagination" v-if="totalPaginas > 1">
            <button class="btn-page" @click="mudarPagina(-1)" :disabled="pagina===1"><i class="bi bi-chevron-left"></i></button>
            <span class="fw-bold opacity-75">{{ pagina }} / {{ totalPaginas }}</span>
            <button class="btn-page" @click="mudarPagina(1)" :disabled="pagina===totalPaginas"><i class="bi bi-chevron-right"></i></button>
        </div>
        
        <div class="text-center mt-5 text-muted small pb-4">
            Catálogo atualizado via Automação LE
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
            pagina: 1, 
            porPagina: 50,
            isDark: true
        }},
        mounted() {
            // Verifica preferencia do usuario
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme) {
                this.isDark = savedTheme === 'dark';
            }
            this.applyTheme();
        },
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
            copiar(texto) { navigator.clipboard.writeText(texto).then(() => alert('Código ' + texto + ' copiado!')); },
            mudarPagina(d) { this.pagina += d; window.scrollTo(0, 0); },
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
    # Renderiza o site com o botão de download
    dados_json = json.dumps(CACHE_MUSICAS)
    btn_html = '<a href="/baixar" class="fab-download" title="Baixar Catálogo Offline"><i class="bi bi-download"></i></a>'
    
    return HTML_TEMPLATE.replace('__DADOS_AQUI__', dados_json).replace('__BOTAO_DOWNLOAD__', btn_html)

@app.route('/baixar')
def baixar():
    # Renderiza o site SEM o botão de download (versão final limpa)
    dados_json = json.dumps(CACHE_MUSICAS)
    
    html_final = HTML_TEMPLATE.replace('__DADOS_AQUI__', dados_json).replace('__BOTAO_DOWNLOAD__', '')
    
    return Response(
        html_final,
        mimetype="text/html",
        headers={"Content-disposition": "attachment; filename=Catalogo_Karaoke_App.html"}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
