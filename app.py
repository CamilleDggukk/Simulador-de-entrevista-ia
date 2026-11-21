
import os
import streamlit as st
from dotenv import load_dotenv
from groq import Groq, APIError

load_dotenv()

st.set_page_config(
    page_title="Treinador de Entrevista Técnica",
    page_icon="🎙️"
)

# Configuração da API
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("Configure a variável GROQ_API_KEY no arquivo .env")
    st.stop()

client = Groq(api_key=api_key)

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

st.title("🎙️ Simulador de Entrevista Técnica")
st.write(
    "Pratique suas respostas técnicas em voz alta "
    "e receba feedback estruturado."
)


SYSTEM_PROMPT = """
Você é um entrevistador técnico experiente, responsável por
avaliar respostas de entrevistas para vagas de Desenvolvimento
de Sistemas e áreas relacionadas.

O candidato pode ser estudante de TI ou profissional com
experiência na área.

Sua função é avaliar cada resposta de maneira criteriosa,
justa, coerente e padronizada.

REGRAS DA AVALIAÇÃO:

1. Avalie somente o conteúdo apresentado pelo candidato.
2. Não invente conhecimentos, experiências ou informações.
3. Não desconte pontos por não mencionar bibliotecas ou
   tecnologias que não sejam necessárias para responder
   à pergunta.
4. Não recomende tecnologias específicas sem explicar
   por que seriam relevantes para aquela resposta.
5. Considere o nível de conhecimento demonstrado.
6. Utilize sempre a mesma estrutura de feedback.
7. Não omita nenhuma seção, mesmo quando não houver
   pontos positivos ou pontos a melhorar.
8. Seja construtivo e explique o motivo de cada avaliação.

FORMATO OBRIGATÓRIO DO FEEDBACK:

## 1. Avaliação por critérios

Apresente uma tabela com as seguintes colunas:
Critério | Nota (0 a 10) | Justificativa.

Avalie:
- Conhecimento técnico.
- Clareza da comunicação.
- Estrutura lógica (Contexto, Ação e Resultado).
- Aplicação prática do conhecimento.

Ao final, apresente a nota geral de 0 a 10,
calculada pela média dos quatro critérios.

## 2. Análise geral
Explique a qualidade da resposta e se ela respondeu
adequadamente à pergunta.

## 3. Pontos positivos
Liste os aspectos corretos e relevantes apresentados.

Se não houver pontos positivos, explique isso
de maneira respeitosa.

## 4. Pontos a melhorar
Liste os aspectos que poderiam ser aprofundados,
corrigidos ou explicados melhor.

Não invente exigências que não fazem parte da pergunta.

#
## 6. Dica do entrevistador

Apresente uma orientação prática e personalizada,
considerando a pergunta realizada e a resposta fornecida.

A dica deve:
- Identificar o que o candidato precisa melhorar.
- Explicar como poderia desenvolver melhor a resposta.
- Sugerir um exemplo ou aspecto técnico para estudar,
  quando isso for relevante.
- Evitar recomendações genéricas que poderiam servir
  para qualquer pergunta.

Se a resposta não apresentar conteúdo suficiente,
oriente o candidato sobre como estruturar uma resposta
mais completa.


## 5. Resposta Ouro

Apresente uma versão aprimorada da resposta do candidato.

Siga estas regras:

- Se a resposta apresentar conteúdo relevante, reorganize
  as informações, melhore a clareza e utilize termos técnicos
  adequados.
- Se faltar explicação, indique como o candidato poderia
  aprofundar a resposta.
- Não invente experiências, projetos ou conhecimentos
  que o candidato não mencionou.
- Se a resposta for muito curta, vaga, sem sentido ou não
  apresentar conteúdo técnico, NÃO repita simplesmente
  o texto original.
- Nesse caso, explique que não existem informações
  suficientes para construir uma resposta completa e
  apresente um exemplo de estrutura que o candidato
  poderia utilizar, com campos para preencher.

Exemplo para respostas sem conteúdo suficiente:

"Não foi possível construir uma Resposta Ouro com base
nas informações fornecidas.

Uma boa resposta poderia seguir esta estrutura:

Contexto: [Explique qual era o problema.]
Ação: [Descreva o que você fez para resolver.]
Resultado: [Explique o resultado alcançado.]"

Nunca apresente informações fictícias como se fossem
experiências reais do candidato.

"""


# Inicialização do estado da entrevista
if "pergunta_atual" not in st.session_state:
    st.session_state.pergunta_atual = (
        "Me conte sobre um problema técnico que você "
        "resolveu recentemente envolvendo banco de dados "
        "SQL ou integração de APIs. Como você investigou "
        "e resolveu?"
    )

if "historico" not in st.session_state:
    st.session_state.historico = []

if "feedback_atual" not in st.session_state:
    st.session_state.feedback_atual = None

if "numero_pergunta" not in st.session_state:
    st.session_state.numero_pergunta = 1

# Exibição da pergunta
st.info(
    f"**Pergunta {st.session_state.numero_pergunta}:** "
    f"{st.session_state.pergunta_atual}"
)

# Entrada por áudio ou texto
audio_value = st.audio_input(
    "Grave sua resposta:",
    key=f"audio_{st.session_state.numero_pergunta}"
)

texto_value = st.text_area(
    "Ou escreva sua resposta:",
    key=f"texto_{st.session_state.numero_pergunta}"
)

# Enviar resposta
if st.button("Enviar Resposta"):

    if audio_value is not None or texto_value.strip():

        with st.spinner("Analisando sua resposta..."):

            try:
                # Obtém a resposta do candidato
                if audio_value is not None:

                    audio_bytes = audio_value.getvalue()

                    transcricao = client.audio.transcriptions.create(
                        file=("resposta.wav", audio_bytes),
                        model="whisper-large-v3-turbo",
                        language="pt"
                    )

                    resposta_candidato = transcricao.text

                    st.markdown("### 🎙️ Resposta transcrita")
                    st.write(resposta_candidato)

                else:
                    resposta_candidato = texto_value.strip()

                # Avaliação da resposta
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Pergunta: {st.session_state.pergunta_atual}\n\n"
                                f"Resposta: {resposta_candidato}"
                            )
                        }
                    ],
                    temperature=0.2
                )

                feedback = response.choices[0].message.content

                # Salva a rodada no histórico
                st.session_state.historico.append({
                    "pergunta": st.session_state.pergunta_atual,
                    "resposta": resposta_candidato,
                    "feedback": feedback
                })

                st.session_state.feedback_atual = feedback

            except APIError as e:
                st.error("Erro ao comunicar com a API do Groq.")
                st.caption(f"Detalhes técnicos: {e}")

    else:
        st.warning("Grave um áudio ou digite uma resposta.")

# Exibição do feedback salvo
if st.session_state.feedback_atual:

    st.divider()

    st.markdown("### 📊 Feedback do Entrevistador")
    st.markdown(st.session_state.feedback_atual)

    st.divider()

    # Próxima pergunta
    if st.button("➡️ Próxima pergunta"):

        with st.spinner("Preparando a próxima pergunta..."):

            try:
                # Monta o histórico da entrevista
                contexto = ""

                for i, rodada in enumerate(
                    st.session_state.historico, start=1
                ):
                    contexto += (
                        f"\nPergunta {i}: {rodada['pergunta']}\n"
                        f"Resposta: {rodada['resposta']}\n"
                        f"Feedback: {rodada['feedback']}\n"
                    )

                # Solicita uma nova pergunta
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": PROMPT_PROXIMA_PERGUNTA
                        },
                        {
                            "role": "user",
                            "content": (
                                "Histórico da entrevista:\n"
                                + contexto
                                + "\nCrie a próxima pergunta."
                            )
                        }
                    ],
                    temperature=0.7
                )

                nova_pergunta = (
                    response.choices[0].message.content.strip()
                )

                # Atualiza o estado da entrevista
                st.session_state.pergunta_atual = nova_pergunta
                st.session_state.numero_pergunta += 1
                st.session_state.feedback_atual = None

                st.rerun()

            except APIError as e:
                st.error("Não foi possível gerar a próxima pergunta.")
                st.caption(f"Detalhes técnicos: {e}")
