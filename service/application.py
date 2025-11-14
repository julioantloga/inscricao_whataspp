from flask import Flask, request, jsonify
from db_config import engine
from sqlalchemy import text
from datetime import datetime
import pandas as pd
import json

def create_candidate(tenant_name: str, name: str, email: str, cpf: str):
    """
    Cadastra um novo candidato na tabela ats_candidate.
    Apenas os campos iniciais: nome, email e CPF.
    """

        # Define timestamps
    now = datetime.now()

    # SQL de inserção
    sql = text(f"""
        INSERT INTO {tenant_name}.ats_candidate 
        (name, email, cpf, created_at, updated_at)
        VALUES (:name, :email, :cpf, :created_at, :updated_at)
        RETURNING id;
    """)

    # Executa a inserção
    with engine.begin() as conn:
        result = conn.execute(
            sql,
            {
                "name": name,
                "email": email,
                "cpf": cpf,
                "created_at": now,
                "updated_at": now,
            }
        ).mappings().first()

    print(f"Candidato cadastrado com ID: {result['id']}")
    return result["id"]

def create_candidate_phone(tenant_name: str, candidate_id: int, phone: str):
    """
    Cadastra o telefone do candidato na tabela ats_candidatephonecontact.
    Campos obrigatórios: number, type, country_code, candidate_id, timestamps.
    """
    # Caso não tenha código, define 55 como padrão (Brasil)
    country_code = 55

    # Define tipo padrão (ex: mobile)
    phone_type = "mobile"

    # Define timestamps
    now = datetime.now()

    # SQL de inserção
    sql = text(f"""
        INSERT INTO {tenant_name}.ats_candidatephonecontact 
        ("number", type, country_code, candidate_id, created_at, updated_at)
        VALUES (:number, :type, :country_code, :candidate_id, :created_at, :updated_at)
        RETURNING id;
    """)

    # Executa a inserção
    with engine.begin() as conn:
        result = conn.execute(
            sql,
            {
                "number": phone,
                "type": phone_type,
                "country_code": country_code,
                "candidate_id": candidate_id,
                "created_at": now,
                "updated_at": now,
            }
        ).mappings().first()

    print(f"📞 Telefone cadastrado com ID: {result['id']}")
    return result["id"]

def create_recruitment_process(tenant_name: str, candidate_id: int, job_posting_id: int):
    """
    Cria o registro de inscrição do candidato em uma vaga (ats_recruitmentprocess).
    Campos fixos:
      - status: 'em_andamento'
      - subscription_type: 'automático'
      - stage_type: 'inscrito'
    """

    now = datetime.now()

    sql = text(f"""
        INSERT INTO {tenant_name}.ats_recruitmentprocess 
        (
            status,
            subscription_type,
            created_at,
            updated_at,
            candidate_id,
            stage_id,
            stage_type,
            job_posting_id
        )
        VALUES (
            :status,
            :subscription_type,
            :created_at,
            :updated_at,
            :candidate_id,
            :stage_id,
            :stage_type,
            :job_posting_id
        )
        RETURNING id;
    """)

    # Executa o insert
    with engine.begin() as conn:
        result = conn.execute(
            sql,
            {
                "status": "em_andamento",
                "subscription_type": "automático",
                "created_at": now,
                "updated_at": now,
                "candidate_id": candidate_id,
                "stage_id": 1,  # por padrão, estágio inicial = 1
                "stage_type": "inscrito",
                "job_posting_id": job_posting_id,
            }
        ).mappings().first()

    print(f"🧩 Processo seletivo criado com ID: {result['id']}")
    return result["id"]

def save_answers(df_questions, recruitment_process_id: int, tenant_name: str):
    """
    Salva as respostas das questões do candidato nas tabelas:
      - ats_answertext (para respostas textuais)
      - ats_answeralternative (para respostas de múltipla escolha)
    """

    now = datetime.now()

    with engine.begin() as conn:
        for _, row in df_questions.iterrows():
            question_id = int(row["id"]) if pd.notna(row["id"]) else None
            answer = row["user_answer"]
            answer_type = row["answer_type"]
            answer_options = row.get("answer_options", [])

            # 🧾 Caso 1: resposta do tipo texto
            if answer_type == "text":
                sql = text(f"""
                    INSERT INTO {tenant_name}.ats_answertext
                    (text, created_at, updated_at, question_id, recruitment_process_id)
                    VALUES (:text, :created_at, :updated_at, :question_id, :recruitment_process_id);
                """)
                conn.execute(
                    sql,
                    {
                        "text": answer,
                        "created_at": now,
                        "updated_at": now,
                        "question_id": question_id,
                        "recruitment_process_id": recruitment_process_id,
                    },
                )

            # 🧾 Caso 2: resposta do tipo múltipla escolha (options)
            elif answer_type == "options":
                # Busca o ID da opção que corresponde à resposta
                matched_option_id = 0
                
                if isinstance(answer_options, list):
                    for opt in answer_options:
                        if str(opt.get("option_id")) == str(answer):
                            matched_option_id = opt["option_id"]
                            break

                sql = text(f"""
                    INSERT INTO {tenant_name}.ats_answeralternative
                    (created_at, updated_at, question_alternative_id, recruitment_process_id)
                    VALUES (:created_at, :updated_at, :question_alternative_id, :recruitment_process_id);
                """)
                conn.execute(
                    sql,
                    {
                        "created_at": now,
                        "updated_at": now,
                        "question_alternative_id": matched_option_id,
                        "recruitment_process_id": recruitment_process_id,
                    }
                )

            else:
                print(f"⚠️ Tipo de resposta desconhecido: {answer_type} (pergunta {question_id})")

    print("✅ Todas as respostas foram registradas com sucesso.")

def get_chat_stage_by_id(chat_stage_id):
    """
    Busca os dados atuais (conversation e context) da tabela ats_chat_stage.
    """
    with engine.begin() as conn:
        select_sql = text(f"""
            SELECT *
            FROM public.ats_chat_stage
            WHERE id = :chat_stage_id
        """)
        result = conn.execute(select_sql, {"chat_stage_id": chat_stage_id}).mappings().first()
        return result

def update_chat_stage(chat_stage_id, tenant_name, conversation, status, context=None):

    """
    Atualiza os campos conversation, status e opcionalmente context da tabela ats_chat_stage.
    """
    with engine.begin() as conn:
        update_fields = {
            "conversation": json.dumps(conversation),
            "status": status,
            "chat_stage_id": chat_stage_id
        }

        update_sql = f"""
            UPDATE {tenant_name}.ats_chat_stage
            SET conversation = :conversation,
                status = :status
        """

        if context is not None:
            update_fields["context"] = json.dumps(context)
            update_sql += ", context = :context"

        update_sql += " WHERE id = :chat_stage_id"

        conn.execute(text(update_sql), update_fields)

def get_basic_questions():
    with engine.begin() as conn:
        # Buscar campos da tabela ats_candidateregisterfield
        fields_sql = text("""
            SELECT id, key, visible, required
            FROM mindsight.ats_candidateregisterfield
            ORDER BY id
        """)
        fields = conn.execute(fields_sql).mappings().all()

        # Buscar opções da tabela ats_candidatesourceoption (caso "source" exista)
        source_options_sql = text("""
            SELECT id, name
            FROM mindsight.ats_candidatesourceoption
            WHERE visible = true
            ORDER BY sequence ASC
        """)
        source_options = conn.execute(source_options_sql).mappings().all()

    questions = []
    sequence = 1

    for field in fields:
        key = field["key"].lower()

        question = {
            "id": None,
            "key": key,
            "name": key,  # Usa o valor exato da key como nome da pergunta
            "type": "basic",
            "sequence": sequence,
            "answer_type": "text",  # padrão
            "user_answer": "",
            "answer_options": []
        }

        if key == "source":
            question["answer_type"] = "options"
            question["answer_options"] = [
                {"option": opt["name"], "option_id": opt["id"]} for opt in source_options
            ]

        questions.append(question)
        sequence += 1

    output = {
        "steps": {
            "questions": questions,
            "total_questions": len(questions)
        }
    }

    return jsonify(output)