import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import pydeck as pdk
import hashlib
import logging
import os

# =============================================
# CONFIGURAÇÃO INICIAL (PRIMEIRO COMANDO STREAMLIT)
# =============================================
st.set_page_config(
    page_title="E-Shop Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================
# CONFIGURAÇÕES GERAIS
# =============================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Credenciais (em produção, usar variáveis de ambiente)
LOGIN = "adminfecaf"
PASSWORD_HASH = hashlib.sha256("fecafadbd".encode()).hexdigest()

# =============================================
# FUNÇÕES PRINCIPAIS
# =============================================
@st.cache_resource
def init_connection():
    try:
        client = MongoClient(
            "mongodb://admin:password@eshop-mongodb:27017/eshop?authSource=admin",
            serverSelectionTimeoutMS=5000
        )
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error("Erro na conexão com o MongoDB")
        logger.error(f"Erro MongoDB: {str(e)}")
        return None

def login_page():
    """Tela de login com redirecionamento garantido"""
    st.title("🔒 Login - Painel E-Shop Brasil")
    
    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        
        if st.form_submit_button("Acessar"):
            if (username == LOGIN and 
                hashlib.sha256(password.encode()).hexdigest() == PASSWORD_HASH):
                st.session_state.logged_in = True
                st.rerun()  # Força atualização imediata
            else:
                st.error("Credenciais inválidas!")
    
    st.stop()  # Bloqueia o resto do app se não logado

# =============================================
# VERIFICAÇÃO DE LOGIN
# =============================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_page()

# =============================================
# APLICAÇÃO PRINCIPAL (SÓ EXECUTA SE LOGADO)
# =============================================
client = init_connection()
db = client.eshop if client else None

# Menu lateral
with st.sidebar:
    st.title("Menu")
    selected = st.selectbox("Opções", ["Dashboard", "Relatórios", "Configurações"])
    
    if st.button("Sair"):
        st.session_state.logged_in = False
        st.rerun()

# Conteúdo principal
if selected == "Dashboard":
    st.title("📊 Dashboard")
    # Adicione seus componentes aqui

elif selected == "Relatórios":
    st.title("📈 Relatórios")
    # Adicione seus componentes aqui
