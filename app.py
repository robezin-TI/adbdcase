import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
from datetime import datetime
import logging
import os
from dotenv import load_dotenv

# Configuração de segurança
load_dotenv()  # Carrega credenciais do .env

if not st.session_state.get('logged_in'):
    st.set_page_config(layout="centered")  # Configuração temporária para o login
    
    with st.form("login_form"):
        st.title("🔒 Painel E-Shop - Acesso Restrito")
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        
        if st.form_submit_button("Entrar"):
            if (username == os.getenv("LOGIN_USERNAME") and 
                (password == os.getenv("LOGIN_PASSWORD")):
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Credenciais inválidas")
    
    st.info("ℹ️ Use as credenciais fornecidas pelo administrador")
    st.stop()  # Bloqueia o resto do aplicativo

# Restaura a configuração original da página
st.set_page_config(page_title="E-Shop Analytics", layout="wide")

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Título da aplicação
st.title("📊 E-Shop Brasil - Painel de Dados")

# Conexão com o MongoDB
@st.cache_resource
def init_connection():
    try:
        client = MongoClient("mongodb://admin:password@mongodb:27017/eshop?authSource=admin")
        client.server_info()  # Testa a conexão
        logger.info("Conexão com MongoDB estabelecida")
        return client
    except Exception as e:
        logger.error(f"Erro na conexão: {str(e)}")
        st.error(f"⚠️ Falha na conexão com o banco de dados: {str(e)}")
        return None

client = init_connection()
db = client.eshop if client else None

# Função para carregar dados
def load_data():
    try:
        data = list(db.vendas.find({}))
        if not data:
            st.warning("Nenhum dado encontrado no banco de dados")
            return None
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None

# Menu principal
option = st.sidebar.selectbox(
    "Menu",
    ["Importar Dados", "Visualizar Dados", "Análise de Clientes", "Otimização Logística"],
    index=0
)

# Botão de logout (novo)
if st.sidebar.button("🔒 Sair"):
    st.session_state.logged_in = False
    st.rerun()

if option == "Importar Dados":
    st.header("📤 Importação de Dados")
    uploaded_file = st.file_uploader("Selecione o arquivo CSV", type=["csv"])
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            
            # Pré-processamento
            df.columns = df.columns.str.strip()
            if 'Data' in df.columns:
                df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
            
            st.subheader("Pré-visualização dos Dados")
            st.dataframe(df.head(3))
            
            if st.button("Confirmar Importação"):
                if db is None:
                    st.error("Banco de dados não conectado")
                else:
                    with st.spinner("Importando..."):
                        try:
                            # Conversão de tipos
                            numeric_cols = ['Quantidade', 'Preço Unitário (R$)', 'Preço Total (R$)']
                            for col in numeric_cols:
                                if col in df.columns:
                                    df[col] = pd.to_numeric(df[col], errors='coerce')
                            
                            # Remove linhas com dados inválidos
                            df_clean = df.dropna()
                            
                            # Insere no MongoDB
                            db.vendas.delete_many({})
                            result = db.vendas.insert_many(df_clean.to_dict('records'))
                            
                            st.success(f"""
                            ✅ Importação concluída!
                            - Registros importados: {len(result.inserted_ids)}
                            - Registros ignorados (dados inválidos): {len(df) - len(df_clean)}
                            """)
                        except Exception as e:
                            st.error(f"Erro durante a importação: {str(e)}")
                            logger.exception("Erro na importação")
                        
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {str(e)}")
            logger.exception("Erro no processamento do CSV")

elif option == "Visualizar Dados":
    st.header("📋 Dados Armazenados")
    df = load_data()
    if df is not None:
        st.dataframe(df)
        st.download_button(
            label="Exportar como CSV",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name='dados_exportados.csv',
            mime='text/csv'
        )

elif option == "Análise de Clientes":
    st.header("👥 Análise de Clientes")
    df = load_data()
    if df is not None:
        # Métricas principais
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Clientes", df['ID Cliente'].nunique())
        col2.metric("Cidades Atendidas", df['Cidade'].nunique())
        col3.metric("Ticket Médio", f"R$ {df['Preço Total (R$)'].mean():.2f}")
        
        # Top clientes
        st.subheader("🏆 Top 10 Clientes")
        top_clientes = df.groupby('Nome do Cliente').agg({
            'Preço Total (R$)': 'sum',
            'Quantidade': 'sum',
            'Cidade': 'first'
        }).nlargest(10, 'Preço Total (R$)')
        st.dataframe(top_clientes)

elif option == "Otimização Logística":
    st.header("🚚 Otimização Logística")
    df = load_data()
    if df is not None:
        st.subheader("📌 Entregas por Região")
        cidade_stats = df.groupby('Cidade').agg({
            'Quantidade': 'sum',
            'ID Cliente': 'nunique'
        }).sort_values('Quantidade', ascending=False)
        
        fig = px.bar(
            cidade_stats.reset_index(),
            x='Cidade',
            y='Quantidade',
            color='ID Cliente',
            title='Volume de Entregas por Cidade'
        )
        st.plotly_chart(fig, use_container_width=True)
