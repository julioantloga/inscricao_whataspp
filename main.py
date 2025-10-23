from flask import Flask, request, jsonify
from service.application import set_application

app = Flask(__name__)

# GET simples: retorna uma mensagem JSON
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Olá!"})


# POST: recebe JSON e retorna processado
@app.route("/add_application", methods=["POST"])
def add_application():
    try:
        data = request.get_json(force=True)
        print("JSON recebido:", data)

        context = data.get("context")
        print("Context:", context)

        # Verifica campos esperados
        if not all(k in data for k in ["context", "phone", "tenant_name", "job_posting_id"]):
            return jsonify({"erro": "Campos obrigatórios faltando"}), 400

        return jsonify({"mensagem": "Recebido com sucesso!", "dados": data})

    except Exception as e:
        print("Erro interno:", e)
        return jsonify({"erro": str(e)}), 500
    set_application (data)

# Executa localmente (Railway ignora essa parte no deploy)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
