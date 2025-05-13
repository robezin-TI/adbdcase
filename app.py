import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import hashlib
import logging
import time
import os

# =============================================
# CONFIGURAÇÕES INICIAIS (Obrigatórias)
# =============================================

# Configuração robusta de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Configurações para Codespaces/Ambiente Remoto
if os.environ.get('CODESPACES') == 'true':
    os.environ.update({
        'STREAMLIT_SERVER_HEADLESS': 'true',
        'STREAMLIT_SERVER_PORT': '8501',
        'STREAMLIT_SERVER_ADDRESS': '0.0.0.0'
    })

# =============================================
# SEGURANÇA (Credenciais Fixas)
# =============================================

def make_hashes(password: str) -> str:
    """Gera hash SHA-256 com tratamento de erro"""
    try:
        return hashlib.sha256(str.encode(password)).hexdigest()
    except Exception as e:
        logger.error(f"Erro ao gerar hash: {e}")
        raise

# Credenciais fixas (substitua por variáveis de ambiente em produção)
LOGIN = "adminfecaf"
PASSWORD_HASH = make_hashes("fecafadbd")  # Hash pré-calculado

# =============================================
# BANCO DE DADOS (Conexão Resiliente)
# =============================================

@st.cache_resource(ttl=3600)
def init_connection():
    """Conexão com MongoDB com retry automático"""
    retry_config = {
        'max_attempts': 3,
        'delay': 2,
        'backoff': 2
    }
    
    for attempt in range(retry_config['max_attempts']):
        try:
            client = MongoClient(
                "mongodb://admin:password@eshop-mongodb:27017/",
                authSource="admin",
                serverSelectionTimeoutMS=5000,
                socketTimeoutMS=30000,
                retryWrites=True,
                appname="E-Shop-App"
            )
            # Teste de conexão imediato
            client.admin.command('ping')
            logger.info("Conexão com MongoDB estabelecida")
            return client
        except Exception as e:
            logger.warning(f"Tentativa {attempt + 1} falhou: {str(e)}")
            if attempt < retry_config['max_attempts'] - 1:
                time.sleep(retry_config['delay'] * (retry_config['backoff'] ** attempt))
    
    logger.error("Falha crítica: Não foi possível conectar ao MongoDB")
    st.error("⚠️ Sistema indisponível. Contate o suporte.")
    return None

# =============================================
# PÁGINA DE LOGIN (À prova de erros)
# =============================================

def login_page() -> None:
    """Tela de login com tratamento completo de erros"""
    try:
        st.title("🔒 Login - Painel E-Shop Brasil")
        st.markdown("---")
        
        with st.form(key="login_form", clear_on_submit=True):
            login = st.text_input("Usuário", key="login_field")
            password = st.text_input("Senha", type="password", key="pass_field")
            
            if st.form_submit_button("Acessar Sistema", use_container_width=True):
                if not login or not password:
                    st.warning("Preencha todos os campos")
                    return
                
                if login == LOGIN and check_hashes(password, PASSWORD_HASH):
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.warning("Credenciais inválidas")
        
        st.markdown("---")
        st.caption("v1.0 - Sistema de gestão E-Shop Brasil")
        
    except Exception as e:
        logger.critical(f"Falha na página de login: {str(e)}", exc_info=True)
        st.error("Falha temporária no sistema. Tente recarregar a página.")

# =============================================
# CONFIGURAÇÃO DO STREAMLIT (Obrigatório primeiro)
# =============================================

st.set_page_config(
    page_title="E-Shop Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://fecaf.com.br/suporte',
        'About': "Painel administrativo E-Shop Brasil"
    }
)

# =============================================
# VERIFICAÇÃO DE SESSÃO (Segurança)
# =============================================

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_page()
    st.stop()  # Impede execução do resto do código

# =============================================
# INICIALIZAÇÃO DO SISTEMA
# =============================================

try:
    client = init_connection()
    db = client.eshop if client else None
    
    if not db:
        st.error("Banco de dados não disponível")
        st.stop()

except Exception as e:
    logger.error(f"Falha na inicialização: {str(e)}")
    st.error("Sistema temporariamente indisponível")
    st.stop()

# =============================================
# INTERFACE PRINCIPAL (Protegida)
# =============================================

def main_interface():
    """Interface após login válido"""
    st.title("📊 Painel de Gestão - E-Shop Brasil")
    
    # Menu lateral seguro
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50?text=E-Shop", width=150)
        st.markdown("## Navegação")
        
        menu_options = [
            "Importar Dados",
            "Visualizar Dados", 
            "Gerenciar Dados",
            "Análise de Clientes",
            "Otimização Logística"
        ]
        
        selected_option = st.selectbox(
            "Selecione a opção",
            menu_options,
            index=0,
            key="main_menu"
        )
        
        st.markdown("---")
        if st.button("🔒 Sair", key="logout_btn", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    
    # Rotas do sistema
    if selected_option == "Importar Dados":
        handle_data_import()
    elif selected_option == "Visualizar Dados":
        handle_data_view()
    elif selected_option == "Otimização Logística":
        handle_logistics()

# =============================================
# FUNCIONALIDADES PRINCIPAIS
# =============================================

def handle_data_import():
    """Lógica para importação de dados"""
    st.header("📤 Importação de Dados")
    # Implementação segura aqui...

def handle_data_view():
    """Visualização de dados com tratamento de erros"""
    try:
        st.header("📋 Visualização de Dados")
        # Implementação segura aqui...
    except Exception as e:
        logger.error(f"Erro na visualização: {str(e)}")
        st.error("Falha ao carregar dados")

def handle_logistics():
    """Otimização logística"""
    st.header("🚚 Otimização Logística")
    # Implementação segura aqui...

# =============================================
# PONTO DE ENTRADA (Protegido)
# =============================================

if __name__ == "__main__":
    try:
        main_interface()
    except Exception as e:
        logger.critical(f"Falha crítica: {str(e)}", exc_info=True)
        st.error("Sistema interrompido. Recarregue a página ou contate o suporte.")
