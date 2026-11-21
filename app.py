
import os
import streamlit as st
from dotenv import load_dotenv
from groq import Groq, APIError

load_dotenv()

st.set_page_config(
    page_title="Treinador de Entrevista Técnica",
    page_icon="🎙️"
)

# Inicializa o cliente Groq
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("Configure a variável GROQ_API_KEY no arquivo .env")
    st.stop()

client = Groq(api_key=api_key)

st.title("🎙️ Simulador de Entrevista Técnica")
st.write(
    "Pratique suas respostas técnicas em voz alta "
    "e receba feedback estruturado."
)

# Prompt do entrevistador
SYSTEM_PROMPT = """
Você é um entrevistador técnico sênior do iFood
conduzindo uma entrevista para a trilha de GenAI.

A candidata é formada em Análise e Desenvolvimento
de Sistemas e tem experiência com C#, ASP.NET,
PHP/Laravel, SQL, FastReport, APIs REST/OData e SAP.

Sua função:
1. Avaliar a resposta da candidata.
2. Dar uma nota de 0 a 10 para a clareza técnica.
3. Avaliar se ela usou uma estrutura lógica
   (Contexto, Ação, Resultado).
4. Reescrever a resposta em uma versão Ouro,
   mais técnica, direta e estruturada.
5. Fazer a próxima pergunta técnica, uma por vez,
   focando em lógica, APIs, banco de dados
   ou resolução de problemas.

Organize o feedback em seções claras.
"""

# Pergunta inicial
if "pergunta_atual" not in st.session_state:
    st.session_state.pergunta_atual = (
        "Me conte sobre um problema técnico que você "
        "resolveu recentemente envolvendo banco de dados "
        "SQL ou integração de APIs. Como você investigou "
        "e resolveu?"
    )

st.info(f"**Entrevistador:** {st.session_state.pergunta_atual}")

# Entrada por áudio ou texto
audio_value = st.audio_input(
    "Grave sua resposta falando como se estivesse na entrevista:"
)

texto_value = st.text_area(
    "Ou escreva sua resposta se preferir testar rápido:"
)

if st.button("Enviar Resposta"):

    if audio_value is not None or texto_value.strip():

        with st.spinner("Analisando sua resposta..."):

            try:
                # 1. Obtém a resposta da candidata
                if audio_value is not None:

                    audio_bytes = audio_value.getvalue()

                    # Transcreve o áudio usando Whisper
                    transcricao = client.audio.transcriptions.create(
                        file=("resposta.wav", audio_bytes),
                        model="whisper-large-v3-turbo",
                        language="pt"
                    )

                    resposta_candidata = transcricao.text

                    st.markdown("### 🎙️ Sua resposta transcrita")
                    st.write(resposta_candidata)

                else:
                    resposta_candidata = texto_value.strip()

                # 2. Envia a resposta para avaliação
                response = client.chat.completions.create(
                    model=os.getenv(
                        "GROQ_MODEL",
                        "openai/gpt-oss-20b"
                    ),
                    messages=[
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Pergunta feita: "
                                f"{st.session_state.pergunta_atual}\n\n"
                                f"Resposta da candidata: "
                                f"{resposta_candidata}"
                            )
                        }
                    ],
                    temperature=0.4
                )

                # 3. Exibe o feedback
                st.markdown("### 📊 Feedback do Entrevistador")

                st.markdown(
                    response.choices[0].message.content
                )

            except APIError as e:
                st.error(
                    "Não foi possível processar sua resposta "
                    "pela API do Groq."
                )
                st.caption(f"Detalhes técnicos: {e}")

    else:
        st.warning(
            "Grave um áudio ou digite uma resposta antes de enviar!"
        )