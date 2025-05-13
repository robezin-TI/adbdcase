import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
from datetime import datetime
import hashlib
from bson.objectid import ObjectId
import logging
import time
import os

# =============================================
# CONFIGURAÇÕES INICIAIS
# =============================================

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurações específicas para Codespaces
if os.environ.get('CODESPACES') == 'true':
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'

# =============================================
# CONFIGURAÇÃO DE AUTENTICAÇÃO
# =============================================

def make_hashes(password):
    """Gera hash SHA-256 da senha"""
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    """Verifica se a senha corresponde ao hash"""
    if not password or not hashed_text:
        return False
    return make_hashes(password) == hashed_text

# Credenciais de acesso
LOGIN = "adminfecaf"
PASSWORD_HASH = make_hashes("fecafadbd")

# =============================================
# CONEXÃO COM O MONGODB
# =============================================

@st.cache_resource
def init_connection():
    """Estabelece conexão com o MongoDB"""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            client = MongoClient(
                "mongodb://admin:password@eshop-mongodb:27017/eshop?authSource=admin",
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                retryWrites=True
            )
            client.admin.command('ping')  # Testa a conexão
            logger.info("Conexão com MongoDB estabelecida")
            return client
        except Exception as e:
            logger.warning(f"Tentativa {attempt + 1} falhou: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    
    logger.error("Falha ao conectar ao MongoDB após várias tentativas")
    st.warning("⚠️ Falha na conexão com o banco de dados. Tente novamente mais tarde.")
    return None

# =============================================
# FUNÇÕES PRINCIPAIS
# =============================================

def load_data():
    """Carrega dados do MongoDB"""
    try:
        if not db:
            raise ConnectionError("Banco de dados não conectado")
            
        data = list(db.vendas.find({}))
        if not data:
            logger.warning("Nenhum dado encontrado no banco de dados")
            return None
            
        df = pd.DataFrame(data)
        
        # Conversão segura de tipos
        numeric_cols = ['Quantidade', 'Preço Unitário (R$)', 'Preço Total (R$)']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df.dropna()
        
    except Exception as e:
        logger.error(f"Erro ao carregar dados: {str(e)}", exc_info=True)
        st.warning(f"Erro ao carregar dados: {str(e)}")
        return None

# =============================================
# PÁGINA DE LOGIN
# =============================================

def login_page():
    """Renderiza a página de login"""
    st.title("🔒 Login - Painel E-Shop Brasil")
    st.markdown("---")
    
    with st.form("login_form"):
        login = st.text_input("Usuário", key="login_field")
        password = st.text_input("Senha", type="password", key="pass_field")
        
        if st.form_submit_button("Acessar Sistema"):
            if login == LOGIN and check_hashes(password, PASSWORD_HASH):
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.warning("Credenciais inválidas. Tente novamente.")
    
    st.markdown("---")
    st.caption("Sistema de gestão de dados para a E-Shop Brasil")

# =============================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================

st.set_page_config(
    page_title="E-Shop Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================
# VERIFICAÇÃO DE AUTENTICAÇÃO
# =============================================

if not hasattr(st.session_state, 'logged_in'):
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_page()
    st.stop()  # Corrigido para st.stop()

# Inicializa conexão com MongoDB
client = init_connection()
db = client.eshop if client else None

# =============================================
# INTERFACE PRINCIPAL
# =============================================

st.title("📊 Painel de Gestão - E-Shop Brasil")

# Menu lateral
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
        key="menu_principal"
    )
    
    st.markdown("---")
    if st.button("🔒 Sair", key="logout_btn"):
        st.session_state.logged_in = False
        st.rerun()

# =============================================
# PÁGINAS DO SISTEMA
# =============================================

if selected_option == "Importar Dados":
    # Implementação da página de importação...
    pass

elif selected_option == "Visualizar Dados":
    # Implementação da página de visualização...
    pass

# [...] (Demais páginas implementadas conforme necessário)

elif selected_option == "Otimização Logística":
    st.header("🚚 Otimização Logística")
    st.markdown("---")
    
    df = load_data()
    if df is not None:
        st.subheader("📌 Distribuição Geográfica de Entregas")
        cidade_stats = df.groupby('Cidade').agg({
            'Quantidade': 'sum',
            'ID Cliente': 'nunique'
        }).sort_values('Quantidade', ascending=False)
        
        fig = px.bar(
            cidade_stats.reset_index(),
            x='Cidade',
            y='Quantidade',
            color='ID Cliente',
            title='Volume de Entregas por Cidade',
            labels={'Quantidade': 'Total de Itens', 'ID Cliente': 'Clientes Únicos'},
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
