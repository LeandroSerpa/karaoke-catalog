from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <div style="text-align: center; padding-top: 50px; font-family: sans-serif;">
        <h1 style="color: green;">SUCESSO TOTAL! 🟢</h1>
        <h2>O Servidor e o Easypanel estão configurados perfeitamente.</h2>
        <p>Se você está vendo isso, o problema anterior era no <strong>ARQUIVO PDF</strong>.</p>
        <p>Pode ser que o PDF esteja corrompido ou o nome estava errado.</p>
    </div>
    """

if __name__ == '__main__':
    # Mantendo a porta 5000 que já configuramos
    app.run(host='0.0.0.0', port=5000)
