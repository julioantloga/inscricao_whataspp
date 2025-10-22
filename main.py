from flask import Flask, request, jsonify
from service.application import set_application

app = Flask(__name__)

# GET simples: retorna uma mensagem JSON
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Olá!"})


# POST: recebe JSON e retorna processado
@app.route("/add_application", methods=["POST"])
def processar():
    data = request.get_json()  # pega o JSON enviado no body
    if not data:
        return jsonify({"erro": "JSON inválido"}), 400
    
    return set_application (data)

# Executa localmente (Railway ignora essa parte no deploy)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
