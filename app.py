import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import pydeck as pdk
import hashlib
import logging
import os
from io import StringIO

# =============================================
# CONFIGURAÇÃO INICIAL
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

# Credenciais
LOGIN = "adminfecaf"
PASSWORD_HASH = hashlib.sha256("fecafadbd".encode()).hexdigest()

# =============================================
# FUNÇÕES DE PROCESSAMENTO DE DADOS
# =============================================
def processar_dados(df):
    """Processa os dados do CSV para gerar os dataframes necessários"""
    try:
        # Converter coluna de data se existir
        if 'Data' in df.columns:
            df['Data'] = pd.to_datetime(df['Data'])
        
        # Criar dataframe de clientes
        clientes_df = df.groupby(['ID Cliente', 'Nome do Cliente', 'Cidade']).agg({
            'Preço Total (R$)': 'sum',
            'Data': 'max'
        }).reset_index().rename(columns={
            'Preço Total (R$)': 'Total Gasto',
            'Data': 'Última Compra'
        })
        
        # Criar dataframe de logística
        logistica_df = df.groupby('Cidade').agg({
            'Preço Total (R$)': 'sum',
            'ID Cliente': 'nunique',
            'Quantidade': 'sum'
        }).reset_index().rename(columns={
            'Preço Total (R$)': 'Total Vendas',
            'ID Cliente': 'Clientes Únicos',
            'Quantidade': 'Itens Vendidos',
            'Cidade': 'Região'
        })
        
        return clientes_df, logistica_df
    except Exception as e:
        st.error(f"Erro ao processar dados: {str(e)}")
        return None, None

# =============================================
# FUNÇÕES DE VISUALIZAÇÃO
# =============================================
def show_clientes(df):
    st.write("## 📋 Dados dos Clientes")
    st.dataframe(df.sort_values('Total Gasto', ascending=False))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Top Clientes por Valor Gasto")
        fig = px.bar(df.nlargest(10, 'Total Gasto'), 
                     x='Nome do Cliente', y='Total Gasto',
                     color='Cidade',
                     labels={'Nome do Cliente': 'Cliente', 'Total Gasto': 'Total Gasto (R$)'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.write("### Distribuição por Cidade")
        fig = px.pie(df, names='Cidade', values='Total Gasto',
                    title='Distribuição de Vendas por Cidade')
        st.plotly_chart(fig, use_container_width=True)

def show_logistica(df):
    st.write("## 🚚 Dados de Logística")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Vendas por Região")
        fig = px.bar(df, x='Região', y='Total Vendas',
                     color='Região',
                     labels={'Total Vendas': 'Total Vendas (R$)'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.write("### Itens Vendidos por Região")
        fig = px.pie(df, names='Região', values='Itens Vendidos',
                    title='Distribuição de Itens Vendidos por Região')
        st.plotly_chart(fig, use_container_width=True)

def show_upload():
    st.write("## 📤 Upload de Dados")
    
    uploaded_file = st.file_uploader("Carregue seu arquivo CSV", type="csv")
    
    if uploaded_file is not None:
        try:
            # Ler o arquivo CSV
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            df = pd.read_csv(stringio)
            
            # Mostrar pré-visualização
            st.write("### Pré-visualização dos Dados")
            st.dataframe(df.head())
            
            # Processar dados
            clientes_df, logistica_df = processar_dados(df)
            
            if clientes_df is not None and logistica_df is not None:
                # Armazenar dados na sessão
                st.session_state.clientes_df = clientes_df
                st.session_state.logistica_df = logistica_df
                st.session_state.dados_carregados = True
                
                st.success("Dados carregados com sucesso!")
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {str(e)}")

# =============================================
# FUNÇÕES DE AUTENTICAÇÃO
# =============================================
def login_page():
    st.title("🔒 Login - Painel E-Shop Brasil")
    
    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        
        if st.form_submit_button("Acessar"):
            if (username == LOGIN and 
                hashlib.sha256(password.encode()).hexdigest() == PASSWORD_HASH):
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Credenciais inválidas!")
    
    st.stop()

# =============================================
# VERIFICAÇÃO DE LOGIN
# =============================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.dados_carregados = False

if not st.session_state.logged_in:
    login_page()

# =============================================
# APLICAÇÃO PRINCIPAL
# =============================================
# Menu lateral
with st.sidebar:
    st.title("Menu")
    selected = st.selectbox("Opções", 
                          ["Dashboard", "Clientes", "Logística", "Upload de Dados"])
    
    if st.button("Sair"):
        st.session_state.logged_in = False
        st.session_state.dados_carregados = False
        st.rerun()

# Conteúdo principal
if selected == "Dashboard":
    st.title("📊 Dashboard Geral")
    
    if not st.session_state.get('dados_carregados', False):
        st.warning("Nenhum dado carregado. Por favor, faça upload de um arquivo CSV na aba 'Upload de Dados'.")
    else:
        clientes_df = st.session_state.clientes_df
        logistica_df = st.session_state.logistica_df
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Clientes", len(clientes_df))
            st.metric("Cliente Top", clientes_df.loc[clientes_df['Total Gasto'].idxmax(), 'Nome do Cliente'])
        
        with col2:
            st.metric("Faturamento Total", f"R$ {clientes_df['Total Gasto'].sum():,.2f}")
            st.metric("Média por Cliente", f"R$ {clientes_df['Total Gasto'].mean():,.2f}")
        
        with col3:
            st.metric("Cidades Atendidas", len(logistica_df))
            st.metric("Cidade Top", logistica_df.loc[logistica_df['Total Vendas'].idxmax(), 'Região'])

elif selected == "Clientes":
    st.title("👥 Clientes")
    
    if not st.session_state.get('dados_carregados', False):
        st.warning("Nenhum dado carregado. Por favor, faça upload de um arquivo CSV na aba 'Upload de Dados'.")
    else:
        show_clientes(st.session_state.clientes_df)

elif selected == "Logística":
    st.title("🚚 Logística")
    
    if not st.session_state.get('dados_carregados', False):
        st.warning("Nenhum dado carregado. Por favor, faça upload de um arquivo CSV na aba 'Upload de Dados'.")
    else:
        show_logistica(st.session_state.logistica_df)

elif selected == "Upload de Dados":
    st.title("📤 Upload de Dados")
    show_upload()
