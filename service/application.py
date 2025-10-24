from db_config import engine
from sqlalchemy import text
from datetime import datetime

def create_candidate(tenant_name: str, name: str, email: str, document: str):
    """
    Cadastra um novo candidato na tabela ats_candidate.
    Apenas os campos iniciais: nome, email e CPF.
    """

    # Garante que o CPF tenha apenas números
    cpf = ''.join([c for c in document if c.isdigit()])

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

    # Normaliza o telefone
    phone = phone.strip().replace(" ", "")
    
    # Extrai o código do país (ex: 55 do +55)
    # Caso não tenha código, define 55 como padrão (Brasil)
    country_code = 55
    if phone.startswith("+"):
        country_code = int(phone[1:3])
        phone = phone[3:]
    elif phone.startswith("55"):
        country_code = 55
        phone = phone[2:]

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
            question_id = int(row["id"])
            answer = row["answer"]
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
                matched_option_id = None
                if isinstance(answer_options, list):
                    for opt in answer_options:
                        if str(opt.get("desc") or opt.get("option_name")).strip().lower() == str(answer).strip().lower():
                            matched_option_id = opt.get("opcao") or opt.get("option_id")
                            break

                if matched_option_id is None:
                    print(f"⚠️ Nenhuma opção correspondente encontrada para a pergunta {question_id}: {answer}")
                    continue

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
                    },
                )

            else:
                print(f"⚠️ Tipo de resposta desconhecido: {answer_type} (pergunta {question_id})")

    print("✅ Todas as respostas foram registradas com sucesso.")
