import os
import re
import json
from flask import Flask, render_template_string, Response
from pypdf import PdfReader

app = Flask(__name__)

# CONFIGURAÇÃO
PDF_FILE = "catalogo.pdf"

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
            /* Paleta Azul & Cinza Profissional */
            --bg-dark: #0f172a;
            --bg-gradient-dark: linear-gradient(180deg, #0f172a 0%, #334155 100%);
            
            --bg-light: #f8fafc;
            --bg-gradient-light: linear-gradient(180deg, #f1f5f9 0%, #cbd5e1 100%);
            
            --card-dark: rgba(30, 41, 59, 0.95);
            --card-light: #ffffff;
            
            --text-dark: #f1f5f9;
            --text-light: #1e293b;
            
            --accent: #38bdf8; /* Azul destaque */
            --code-bg: #0284c7;
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
        [data-bs-theme="light"] .card-music {
            background: var(--card-light);
            border: 1px solid #cbd5e1;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        [data-bs-theme="light"] .title { color: #0f172a; }
        [data-bs-theme="light"] .artist { color: #0369a1; }
        [data-bs-theme="light"] .form-control-lg {
            background: white; color: #333; border: 1px solid #cbd5e1;
        }

        /* HEADER COM IMAGEM SVG EMBUTIDA */
        .hero-header {
            background: linear-gradient(135deg, #020617 0%, #1e293b 100%);
            padding: 30px 20px;
            text-align: center;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            position: relative;
            overflow: hidden;
        }
        /* O Desenho do Microfone (Feito em código para não pesar) */
        .mic-icon {
            width: 80px; height: 80px;
            margin-bottom: 10px;
            fill: var(--accent);
            filter: drop-shadow(0 0 10px rgba(56, 189, 248, 0.5));
        }

        .app-title {
            font-weight: 800; font-size: 1.8rem; margin: 0;
            text-transform: uppercase; letter-spacing: 2px;
            color: white;
        }

        /* CONTROLES */
        .theme-toggle {
            position: absolute; top: 20px; right: 20px;
            background: rgba(255,255,255,0.1); border: none; 
            color: white; width: 40px; height: 40px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            cursor: pointer;
        }

        .search-container {
            padding: 0 15px; margin-top: -25px; position: relative; z-index: 10;
        }
        .form-control-lg { 
            background: rgba(30, 41, 59, 0.9); backdrop-filter: blur(5px);
            border: 1px solid rgba(255,255,255,0.1); 
            color: white; border-radius: 12px; padding: 15px 20px; 
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }
        .form-control-lg:focus { border-color: var(--accent); box-shadow: 0 0 0 4px rgba(56, 189, 248, 0.2); }

        /* LISTA */
        .card-music { 
            background: var(--card-dark); 
            margin: 12px auto; padding: 15px 20px; border-radius: 10px; 
            display: flex; justify-content: space-between; align-items: center; 
            max-width: 800px; border-left: 4px solid var(--accent);
        }
        .info { flex: 1; padding-right: 15px; }
        .artist { 
            color: var(--accent); font-weight: 700; font-size: 0.8rem; 
            text-transform: uppercase; margin-bottom: 3px; 
        }
        .title { font-weight: 600; font-size: 1.1rem; line-height: 1.2; }

        /* BOTÃO CÓDIGO */
        .code-btn {
            background: var(--code-bg); color: white;
            padding: 8px 15px; border-radius: 6px;
            font-weight: 700; font-size: 1.2rem;
            text-align: center; min-width: 80px; cursor: pointer;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }
        .code-btn:active { transform: scale(0.95); }
        .code-label { font-size: 0.6rem; margin-top: 4px; text-transform: uppercase; opacity: 0.7; text-align: center; }

        .pagination { justify-content: center; margin-top: 30px; display: flex; gap: 10px; align-items: center; }
        .btn-page { 
            width: 45px; height: 45px; border-radius: 8px; border: none; 
            background: rgba(255,255,255,0.1); color: inherit; 
            font-size: 1.2rem; 
        }
        .btn-page:hover:not(:disabled) { background: var(--accent); color: white; }
        .btn-page:disabled { opacity: 0.3; }

        .footer-note { 
            text-align: center; margin-top: 40px; padding: 20px;
            color: #64748b; font-size: 0.9rem; border-top: 1px solid rgba(255,255,255,0.05);
        }

        /* BOTÃO DOWNLOAD FLUTUANTE */
        .fab-download {
            position: fixed; bottom: 25px; right: 25px;
            background: #10b981; color: white;
            width: 65px; height: 65px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.8rem; box-shadow: 0 10px 25px rgba(16, 185, 129, 0.4);
            text-decoration: none; z-index: 1000; transition: 0.3s;
        }
        .fab-download:hover { transform: translateY(-5px); background: #059669; }
    </style>
</head>
<body>
<div id="app">
    
    <div class="hero-header">
        <button class="theme-toggle" @click="toggleTheme">
            <i :class="isDark ? 'bi bi-moon-stars-fill' : 'bi bi-sun-fill'"></i>
        </button>
        
        <svg class="mic-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
        </svg>
        
        <h1 class="app-title">Catálogo<br><span style="color:var(--accent)">Karaokê</span></h1>
    </div>

    <div class="search-container">
        <input type="text" class="form-control form-control-lg" v-model="busca" placeholder="🔍 Buscar música, cantor ou código..." @input="pagina=1">
        <div class="text-center mt-2 small opacity-75">{{ listaFiltrada.length }} músicas carregadas</div>
    </div>

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
            pagina: 1, 
            porPagina: 50,
            isDark: true
        }},
        mounted() {
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
    dados_json = json.dumps(CACHE_MUSICAS)
    # Adiciona o botão de download apenas na versão online
    btn_html = '<a href="/baixar" class="fab-download" title="Baixar App HTML"><i class="bi bi-download"></i></a>'
    
    return HTML_TEMPLATE.replace('__DADOS_AQUI__', dados_json)\
                        .replace('__BOTAO_DOWNLOAD__', btn_html)

@app.route('/baixar')
def baixar():
    dados_json = json.dumps(CACHE_MUSICAS)
    
    # Remove o botão de download na versão final
    html_final = HTML_TEMPLATE.replace('__DADOS_AQUI__', dados_json)\
                              .replace('__BOTAO_DOWNLOAD__', '')
    
    return Response(
        html_final,
        mimetype="text/html",
        headers={"Content-disposition": "attachment; filename=Catalogo_Karaoke.html"}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
