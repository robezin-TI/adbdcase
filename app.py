import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import hashlib
import logging
import time
import os
from io import StringIO

# =============================================
# CONFIGURAÇÕES INICIAIS
# =============================================

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Credenciais fixas (apenas para desenvolvimento)
LOGIN = "adminfecaf"
PASSWORD = "fecafadbd"

# =============================================
# PÁGINA DE LOGIN (À prova de erros)
# =============================================

def login_page():
    """Tela de login robusta"""
    st.title("🔒 Login - Painel E-Shop Brasil")
    st.markdown("---")
    
    with st.form("login_form"):
        login = st.text_input("Usuário", key="login_field")
        password = st.text_input("Senha", type="password", key="pass_field")
        
        if st.form_submit_button("Acessar Sistema"):
            if login == LOGIN and password == PASSWORD:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Credenciais inválidas")
    
    st.markdown("---")

# =============================================
# CONEXÃO COM BANCO DE DADOS
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
        st.error("Erro na conexão com o banco de dados")
        logger.error(f"Erro MongoDB: {str(e)}")
        return None

# =============================================
# FUNÇÕES DAS ABAS
# =============================================

def aba_upload():
    """Interface para upload de arquivos"""
    st.header("📤 Importar Dados")
    
    uploaded_file = st.file_uploader(
        "Selecione o arquivo CSV", 
        type=["csv"],
        accept_multiple_files=False
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.success("Arquivo carregado com sucesso!")
            
            with st.expander("Pré-visualização"):
                st.dataframe(df.head(10))
                
            if st.button("Salvar no Banco de Dados"):
                # Lógica para salvar no MongoDB
                st.success("Dados importados com sucesso!")
                
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {str(e)}")

def aba_visualizacao():
    """Visualização de dados"""
    st.header("📊 Visualização de Dados")
    
    try:
        client = init_connection()
        if client:
            db = client.eshop
            data = list(db.vendas.find({}))
            
            if data:
                df = pd.DataFrame(data)
                st.dataframe(df)
                
                # Gráficos de exemplo
                st.subheader("Análise de Vendas")
                fig = px.bar(df, x='Produto', y='Quantidade')
                st.plotly_chart(fig)
            else:
                st.warning("Nenhum dado encontrado no banco")
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")

def aba_clientes():
    """Gestão de clientes"""
    st.header("👥 Gestão de Clientes")
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        filtro_cidade = st.selectbox("Filtrar por cidade", ["Todas", "São Paulo", "Rio de Janeiro"])
    
    # Tabela de clientes
    st.dataframe(pd.DataFrame({
        "Cliente": ["Cliente A", "Cliente B"],
        "Cidade": ["São Paulo", "Rio de Janeiro"],
        "Compras": [15, 8]
    }))

def aba_logistica():
    """Otimização logística"""
    st.header("🚚 Otimização Logística")
    
    # Mapa de distribuição
    st.subheader("Mapa de Entregas")
    st.map(pd.DataFrame({
        "lat": [-23.5505, -22.9068],
        "lon": [-46.6333, -43.1729],
        "size": [10, 5],
        "local": ["SP", "RJ"]
    }))
    
    # Estatísticas
    st.subheader("Métricas")
    col1, col2, col3 = st.columns(3)
    col1.metric("Entregas Hoje", "25", "3%")
    col2.metric("Tempo Médio", "2h15m", "-5%")
    col3.metric("Custo Médio", "R$ 8,50", "1.2%")

# =============================================
# CONFIGURAÇÃO PRINCIPAL
# =============================================

st.set_page_config(
    page_title="E-Shop Analytics",
    page_icon="📊",
    layout="wide"
)

# Verificação de login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_page()
    st.stop()

# =============================================
# INTERFACE PRINCIPAL
# =============================================

# Menu lateral
with st.sidebar:
    st.image("https://via.placeholder.com/150x50?text=E-Shop", width=150)
    st.markdown("## Navegação")
    
    opcoes_menu = [
        "Dashboard",
        "Upload de Arquivos",
        "Visualização de Dados",
        "Gestão de Clientes",
        "Otimização Logística"
    ]
    
    aba_selecionada = st.selectbox(
        "Selecione a opção",
        opcoes_menu,
        key="menu_principal"
    )
    
    st.markdown("---")
    if st.button("🔒 Sair", key="logout_btn"):
        st.session_state.logged_in = False
        st.rerun()

# Conteúdo principal
if aba_selecionada == "Dashboard":
    st.title("📊 Dashboard Principal")
    st.write("Bem-vindo ao painel de controle E-Shop Brasil")
    
elif aba_selecionada == "Upload de Arquivos":
    aba_upload()
    
elif aba_selecionada == "Visualização de Dados":
    aba_visualizacao()
    
elif aba_selecionada == "Gestão de Clientes":
    aba_clientes()
    
elif aba_selecionada == "Otimização Logística":
    aba_logistica()
