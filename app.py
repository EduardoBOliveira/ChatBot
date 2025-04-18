import os
import streamlit as st
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

import fitz  # PyMuPDF
import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi

# Configuração da API
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('GROQ_API_KEY')


chat = ChatGroq(model='llama-3.3-70b-versatile')

# Função de resposta do bot
def resposta_bot(mensagens, documento):
    mensagens_modelo = [
        ('system', 'Você é um assistente pessoal, que tem por objetivo apoiar o usuario em qualquer tipo de atividade que ele necessitar, focando em aumentar a produtividade dele, você pode utilizar como base algumas informações: {informacoes}.')
    ]
    mensagens_modelo += mensagens
    template = ChatPromptTemplate.from_messages(mensagens_modelo)
    chain = template | chat
    return chain.invoke({'informacoes': documento}).content

# Função para extrair texto de PDF
def extrair_texto_pdf(pdf):
    texto = ""
    with fitz.open(stream=pdf.read(), filetype="pdf") as doc:
        for pagina in doc:
            texto += pagina.get_text()
    return texto

# Função para extrair texto de um site
def extrair_texto_site(url):
    try:
        resposta = requests.get(url)
        sopa = BeautifulSoup(resposta.content, 'html.parser')
        return sopa.get_text(separator='\n')
    except Exception as e:
        return f"Erro ao acessar o site: {e}"

# Função para extrair transcrição do YouTube
def extrair_transcricao_youtube(link):
    try:
        video_id = link.split("v=")[-1].split("&")[0]
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt', 'pt-BR'])
        return " ".join([x['text'] for x in transcript])
    except Exception as e:
        return f"Erro ao obter transcrição do vídeo: {e}"

# Inicialização do estado da sessão
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

if "documento" not in st.session_state:
    st.session_state.documento = ""

# Layout da página
st.set_page_config(page_title="Vistinha - Suporte GPS", page_icon="🤖")
st.title("🤖 Vistinha - Suporte ao Sistema GPS VISTA")

# Informações adicionais
with st.expander("📄 Adicionar informações para o Vistinha (opcional)"):
    st.session_state.documento = st.text_area(
        "Coloque aqui informações que o Vistinha deve considerar nas respostas.",
        height=150
    )

# Upload de PDF
with st.sidebar:
    st.subheader("📎 Referências adicionais")
    pdf = st.file_uploader("📄 Enviar PDF", type="pdf")
    if pdf:
        texto_pdf = extrair_texto_pdf(pdf)
        st.session_state.documento += "\n" + texto_pdf
        st.success("Texto do PDF adicionado!")

    url_site = st.text_input("🌐 Inserir URL de site")
    if url_site:
        texto_site = extrair_texto_site(url_site)
        st.session_state.documento += "\n" + texto_site
        st.success("Texto do site adicionado!")

    link_yt = st.text_input("📺 Link de vídeo do YouTube")
    if link_yt:
        texto_video = extrair_transcricao_youtube(link_yt)
        st.session_state.documento += "\n" + texto_video
        st.success("Transcrição do vídeo adicionada!")

# Campo de entrada de mensagem
pergunta = st.chat_input("Digite sua pergunta para o Vistinha...")

if pergunta:
    st.session_state.mensagens.append(('user', pergunta))
    resposta = resposta_bot(st.session_state.mensagens, st.session_state.documento)
    st.session_state.mensagens.append(('assistant', resposta))

# Exibir histórico do chat
for role, texto in st.session_state.mensagens:
    with st.chat_message("🧑‍💼" if role == 'user' else "🤖"):
        st.markdown(texto)

# Botão lateral para resetar
st.sidebar.button("🔄 Reiniciar Conversa", on_click=lambda: st.session_state.clear())
