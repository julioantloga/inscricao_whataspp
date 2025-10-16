from flask import Flask, request, jsonify
from db_config import engine

app = Flask(__name__)

# GET simples: retorna uma mensagem JSON
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "API está online!"})


# GET com parâmetro
@app.route("/hello/<nome>", methods=["GET"])
def hello(nome):
    return jsonify({"mensagem": f"Olá, {nome}!"})


# POST: recebe JSON e retorna processado
@app.route("/processar", methods=["POST"])
def processar():
    data = request.get_json()  # pega o JSON enviado no body
    if not data:
        return jsonify({"erro": "JSON inválido"}), 400

    nome = data.get("nome")
    idade = data.get("idade")

    return jsonify({
        "mensagem": f"Recebido com sucesso!",
        "dados_recebidos": {"nome": nome, "idade": idade}
    })


# Executa localmente (Railway ignora essa parte no deploy)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
