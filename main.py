from flask import Flask, request, jsonify
from service.application import create_candidate, create_candidate_phone, create_recruitment_process, save_answers
import pandas as pd
import json

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
        # Extrai o corpo principal
        body = data["output"]["body"]

        # Cria variáveis individuais
        name = body["name"]
        phone = body["phone"]
        email = body["email"]
        document = body["document"]
        tenant_name = body["tenant_name"]
        job_posting_id = body["job_posting_id"]

        # Inferir tipo de documento automaticamente
        if len(document.replace(".", "").replace("-", "")) == 11:
            document_type = "CPF"
        elif len(document.replace(".", "").replace("-", "")) == 14:
            document_type = "CNPJ"
        else:
            document_type = "Outro"

        # Cria o DataFrame com as perguntas
        df_questions = pd.DataFrame(body["questions"])

        #cria o candidato
        candidate_id = create_candidate(tenant_name,name,email,document)

        #cria telefone do candidato
        create_candidate_phone(tenant_name, candidate_id, phone)

        #registra a inscrição
        recruitment_process_id = create_recruitment_process(tenant_name, candidate_id, job_posting_id)

        #salva as respostas
        #save_answers(df_questions, recruitment_process_id, tenant_name)

        return data

    except Exception as e:
        print("Erro interno:", e)
        return jsonify({"erro": str(e)}), 500

# Executa localmente (Railway ignora essa parte no deploy)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
