from flask import Flask, request, jsonify
from service.application import create_candidate, create_candidate_phone, create_recruitment_process, get_chat_stage_by_id, update_chat_stage, save_answers
import pandas as pd
import json
from datetime import datetime


app = Flask(__name__)

# GET simples: retorna uma mensagem JSON
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Olá!"})

# POST: recebe JSON e retorna processado
from service.application import get_chat_stage_by_id, update_chat_stage

@app.route("/update_session", methods=["POST"])
def update_session():
    try:
        payload = request.get_json(force=True)

        candidate_message = payload.get("candidate_message")
        system_message = payload.get("system_message")
        question_id = payload.get("question_id")
        interaction = payload.get("interaction")
        chat_stage_id = payload.get("chat_stage_id")
        tenant_name = payload.get("tenant_name")
        status = payload.get("status")

        now_iso = datetime.utcnow().isoformat() + "Z"

        # Busca os dados atuais (sem expor engine aqui)
        result = get_chat_stage_by_id(chat_stage_id, tenant_name)
        if not result:
            return jsonify({"error": "Registro não encontrado"}), 404

        conversation = result["conversation"] or []
        if isinstance(conversation, str):
            conversation = json.loads(conversation)

        conversation.extend([
            {"date": now_iso, "from": "system", "message": system_message},
            {"date": now_iso, "from": "candidate", "message": candidate_message}
        ])

        context = result["context"] or {}
        if isinstance(context, str):
            context = json.loads(context)

        if interaction == "answer":
            updated = False
            for question in context.get("steps", {}).get("questions", []):
                if question.get("id") == question_id:
                    question["candidate_answer"] = candidate_message
                    updated = True
                    break

            if not updated:
                return jsonify({"error": f"Questão com id {question_id} não encontrada no contexto"}), 400

            update_chat_stage(
                chat_stage_id=chat_stage_id,
                tenant_name=tenant_name,
                conversation=conversation,
                status=status,
                context=context
            )
        else:
            update_chat_stage(
                chat_stage_id=chat_stage_id,
                tenant_name=tenant_name,
                conversation=conversation,
                status=status
            )

        return jsonify({"status": "OK"}), 200

    except Exception as e:
        print("Erro interno:", e)
        return jsonify({"error": str(e)}), 500



# POST: recebe JSON e retorna processado
@app.route("/add_application", methods=["POST"])
def add_application():
    try:
        data = request.get_json(force=True)
        chat_id = data["ats_chat_stage_id"]

        # Busca o contexto da conversa
        result = get_chat_stage_by_id(chat_id)
        context = result["context"]
        tenant_name = result["tenant_name"]
        job_posting_id = result["job_posting_id"]
        phone = result["candidate_phone_number_id"]
        questions = context[0].get("steps", {}).get("questions", [])

        # Inicializa variáveis
        name = cpf = email = document = None
        customized_rows = []

        for q in questions:
            q_type = q.get("type")
            q_key = q.get("key")
            q_user_answer = q.get("user_answer")

            # Campos individuais
            if q_key == "name" and q_type == "basic":
                name = q_user_answer
            elif q_key == "email" and q_type == "basic":
                email = q_user_answer
            elif q_key == "cpf" and q_type == "basic":
                cpf = q_user_answer
            elif q_key == "document":
                document = q_user_answer

            # Dados para o dataframe
            if q_type == "customized":
                customized_rows.append({
                    "id": q.get("id"),
                    "name": q.get("name"),
                    "key": q.get("key"),
                    "answer_type": q.get("answer_type"),
                    "user_answer": q.get("user_answer"),
                    "answer_options": q.get("answer_options", [])
                })
                
        print(customized_rows)

        # Apenas para debug no log
        print("Name:", name)
        print("Phone:", phone)
        print("Cpf:", cpf)
        print("Email:", email)
        print("Document:", document)

        # Cria o DataFrame com perguntas personalizadas
        questions_df = pd.DataFrame(customized_rows)

        #cria o candidato
        candidate_id = create_candidate(tenant_name, name, email, cpf)

        #cria telefone do candidato
        create_candidate_phone(tenant_name, candidate_id, phone)

        #registra a inscrição
        recruitment_process_id = create_recruitment_process(tenant_name, candidate_id, job_posting_id)

        #salva as respostas
        save_answers(questions_df, recruitment_process_id, tenant_name)

        # Opcional: retornar dados como JSON
        return jsonify({
            "nome": name,
            "phone": phone,
            "email": email,
            "document": document,
            "questions": questions_df.to_dict(orient="records")
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"erro": str(e)}), 500


        # # Cria o DataFrame com as perguntas
        # df_questions = pd.DataFrame(body["questions"])

        # #cria o candidato
        # candidate_id = create_candidate(tenant_name,name,email,document)

        # #cria telefone do candidato
        # create_candidate_phone(tenant_name, candidate_id, phone)

        # #registra a inscrição
        # recruitment_process_id = create_recruitment_process(tenant_name, candidate_id, job_posting_id)

        # #salva as respostas
        # #save_answers(df_questions, recruitment_process_id, tenant_name)
        #return jsonify({"chat_id": chat_id}), 200

# Executa localmente (Railway ignora essa parte no deploy)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
