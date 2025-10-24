from flask import Flask, request, jsonify
#from service.application import set_application
import pandas as pd

app = Flask(__name__)

# GET simples: retorna uma mensagem JSON
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Olá!"})

@app.route("/add_application", methods=["POST"])
def add_application():
    try:
        data = request.get_json(force=True)
        import json
        print("📥 JSON recebido:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        # Tenta acessar a estrutura
        print("👉 Tipo do data:", type(data))
        if isinstance(data, list):
            body = data[0].get("output", {}).get("body")
        elif isinstance(data, dict):
            body = data.get("output", {}).get("body")
        else:
            raise ValueError("Formato inesperado de data: não é lista nem dict")

        if not body:
            raise ValueError("Campo body não encontrado no JSON recebido")

        name = body.get("name")
        print("✅ Nome extraído:", name)

        return jsonify({"status": "sucesso", "name": name})

    except Exception as e:
        import traceback
        print("❌ ERRO DETALHADO:")
        traceback.print_exc()
        return jsonify({"erro": str(e)}), 500


# # POST: recebe JSON e retorna processado
# @app.route("/add_application", methods=["POST"])
# def add_application():
#     try:
#         data = request.get_json(force=True)   
#         # Extrai o corpo principal
#         body = data[0]["output"]["body"]

#         # Cria variáveis individuais
#         name = body["name"]
#         phone = body["phone"]
#         email = body["email"]
#         document = body["document"]
#         tenant_name = body["tenant_name"]
#         job_posting_id = body["job_posting_id"]

#         # Inferir tipo de documento automaticamente
#         if len(document.replace(".", "").replace("-", "")) == 11:
#             document_type = "CPF"
#         elif len(document.replace(".", "").replace("-", "")) == 14:
#             document_type = "CNPJ"
#         else:
#             document_type = "Outro"

#         # Cria o DataFrame com as perguntas
#         df_questions = pd.DataFrame(body["questions"])

#         # Exibe resultados
#         print("📋 Variáveis extraídas:")
#         print(f"Name: {name}")
#         print(f"Phone: {phone}")
#         print(f"Email: {email}")
#         print(f"Document: {document}")
#         print(f"Document Type: {document_type}")
#         print(f"Tenant Name: {tenant_name}")
#         print(f"Job Posting ID: {job_posting_id}")
#         print("\n📊 DataFrame de perguntas:")
#         print(df_questions)

#         return data

#     except Exception as e:
#         print("Erro interno:", e)
#         return jsonify({"erro": str(e)}), 500

# Executa localmente (Railway ignora essa parte no deploy)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
