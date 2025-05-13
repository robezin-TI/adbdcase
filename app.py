import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import hashlib
import logging
import time
import os

# =============================================
# CONFIGURAÇÕES INICIAIS
# =============================================

# Configuração robusta de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Configurações para ambiente remoto
if os.environ.get('CODESPACES') == 'true':
    os.environ.update({
        'STREAMLIT_SERVER_HEADLESS': 'true',
        'STREAMLIT_SERVER_PORT': '8501',
        'STREAMLIT_SERVER_ADDRESS': '0.0.0.0'
    })

# =============================================
# CREDENCIAIS DE ACESSO (FIXAS PARA DEMONSTRAÇÃO)
# =============================================
LOGIN_CORRETO = "adminfecaf"
SENHA_CORRETA = "fecafadbd"  # Senha em texto puro (apenas para desenvolvimento)

# =============================================
# PÁGINA DE LOGIN (À PROVA DE FALHAS)
# =============================================
def login_page():
    """Tela de login simplificada e robusta"""
    try:
        st.title("🔒 Login - Painel E-Shop Brasil")
        st.markdown("---")
        
        # Layout em colunas para melhor organização
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image("https://via.placeholder.com/150x50?text=E-Shop", width=150)
        
        with col2:
            with st.form(key="login_form"):
                login = st.text_input("Usuário", key="login_field")
                password = st.text_input("Senha", type="password", key="pass_field")
                
                if st.form_submit_button("Acessar Sistema"):
                    if not login or not password:
                        st.warning("⚠️ Preencha todos os campos!")
                    elif login.strip() == LOGIN_CORRETO and password.strip() == SENHA_CORRETA:
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        st.error("❌ Credenciais inválidas!")
        
        st.markdown("---")
        st.caption("Sistema de gestão E-Shop Brasil | v1.0")

    except Exception as e:
        logger.error(f"FALHA NO LOGIN: {str(e)}", exc_info=True)
        st.error("🚨 Erro temporário. Recarregue a página ou contate o suporte.")

# =============================================
# CONFIGURAÇÃO DO STREAMLIT
# =============================================
st.set_page_config(
    page_title="E-Shop Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================
# VERIFICAÇÃO DE SESSÃO
# =============================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_page()
    st.stop()  # Impede a execução do restante do código

# =============================================
# CONEXÃO COM BANCO DE DADOS (MongoDB)
# =============================================
@st.cache_resource
def init_connection():
    try:
        client = MongoClient(
            "mongodb://admin:password@eshop-mongodb:27017/",
            authSource="admin",
            serverSelectionTimeoutMS=5000
        )
        client.admin.command('ping')
        return client
    except Exception as e:
        logger.error(f"ERRO NO MONGODB: {str(e)}")
        st.error("⛔ Banco de dados indisponível")
        st.stop()

# =============================================
# INTERFACE PRINCIPAL (APÓS LOGIN)
# =============================================
def main_interface():
    """Interface após autenticação bem-sucedida"""
    try:
        client = init_connection()
        db = client.eshop
        
        st.title("📊 Painel de Gestão - E-Shop Brasil")
        
        # Menu lateral
        with st.sidebar:
            st.markdown("## Navegação")
            selected_option = st.selectbox(
                "Selecione a opção",
                ["Dashboard", "Relatórios", "Configurações"],
                key="main_menu"
            )
            
            if st.button("🔒 Sair", key="logout_btn"):
                st.session_state.clear()
                st.rerun()
        
        # Conteúdo principal
        if selected_option == "Dashboard":
            st.header("Visão Geral")
            # Adicione seus componentes aqui
            
        elif selected_option == "Relatórios":
            st.header("Relatórios Analíticos")
            # Adicione seus componentes aqui

    except Exception as e:
        logger.error(f"ERRO NA INTERFACE: {str(e)}")
        st.error("⚠️ Falha no sistema. Recarregue a página.")

# =============================================
# EXECUÇÃO PRINCIPAL
# =============================================
if __name__ == "__main__":
    main_interface()
