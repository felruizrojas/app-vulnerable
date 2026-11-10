from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def index():
    return 'App vulnerable de prueba - DevSecOps DM'

@app.route('/hello')
def hello():
    # Entrada de usuario SIN sanitizar -> XSS reflejado (vulnerabilidad intencional)
    name = request.args.get('name', 'mundo')
    return f'<h1>Hola, {name}!</h1>'

if __name__ == '__main__':
    # debug=True es una mala practica de seguridad (vulnerabilidad intencional)
    app.run(host='0.0.0.0', port=5000, debug=True)
