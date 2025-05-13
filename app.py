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

client = init_connection()
db = client.eshop if client else None

# =============================================
# FUNÇÕES DE MANIPULAÇÃO DE DADOS
# =============================================

def salvar_no_banco(df):
    """Salva DataFrame no MongoDB com tratamento de erros"""
    try:
        records = df.to_dict('records')
        result = db.vendas.insert_many(records)
        return len(result.inserted_ids)
    except Exception as e:
        st.error(f"Erro ao salvar no banco: {str(e)}")
        logger.error(f"Erro ao salvar dados: {str(e)}")
        return 0

def carregar_vendas():
    """Carrega dados de vendas do MongoDB"""
    try:
        data = list(db.vendas.find({}))
        return pd.DataFrame(data) if data else pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar vendas: {str(e)}")
        return pd.DataFrame()

def carregar_clientes():
    """Carrega e processa dados de clientes"""
    try:
        pipeline = [
            {
                "$group": {
                    "_id": "$Cliente",
                    "TotalGasto": {"$sum": "$Preço Total"},
                    "Cidade": {"$first": "$Cidade"},
                    "QuantidadeCompras": {"$sum": 1}
                }
            },
            {"$sort": {"TotalGasto": -1}}
        ]
        clientes = list(db.vendas.aggregate(pipeline))
        return pd.DataFrame(clientes) if clientes else pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar clientes: {str(e)}")
        return pd.DataFrame()

# =============================================
# FUNÇÕES DAS ABAS
# =============================================

def aba_upload():
    """Interface para upload de arquivos com persistência real"""
    st.header("📤 Importar Dados")
    
    uploaded_file = st.file_uploader(
        "Selecione o arquivo CSV", 
        type=["csv"],
        accept_multiple_files=False
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            
            # Pré-processamento
            df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
            df['Preço Total'] = df['Quantidade'] * df['Preço Unitário']
            
            with st.expander("Pré-visualização (10 primeiras linhas)"):
                st.dataframe(df.head(10))
                
            if st.button("Salvar no Banco de Dados"):
                with st.spinner("Salvando dados..."):
                    qtd = salvar_no_banco(df)
                    if qtd > 0:
                        st.success(f"{qtd} registros salvos com sucesso!")
                        st.cache_data.clear()  # Limpa cache para atualizar visualizações
                    else:
                        st.error("Nenhum dado foi salvo")
                        
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {str(e)}")

def aba_visualizacao():
    """Visualização e manipulação de dados"""
    st.header("📊 Visualização de Dados")
    
    df = carregar_vendas()
    if df.empty:
        st.warning("Nenhum dado encontrado no banco")
        return
    
    # Filtros
    st.subheader("Filtros")
    col1, col2 = st.columns(2)
    with col1:
        produtos = st.multiselect(
            "Selecione produtos",
            options=df['Produto'].unique(),
            default=df['Produto'].unique()[:2]
        )
    with col2:
        date_range = st.date_input(
            "Período",
            value=[df['Data'].min(), df['Data'].max()]
        )
    
    # Aplicar filtros
    filtered_df = df[
        (df['Produto'].isin(produtos)) &
        (df['Data'].between(*date_range))
    ]
    
    # Visualização
    st.dataframe(filtered_df.sort_values('Data', ascending=False))
    
    # Gráficos
    st.subheader("Análise de Vendas")
    tab1, tab2 = st.tabs(["Por Produto", "Temporal"])
    
    with tab1:
        fig = px.bar(
            filtered_df.groupby('Produto')['Preço Total'].sum().reset_index(),
            x='Produto',
            y='Preço Total',
            title="Vendas por Produto"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        fig = px.line(
            filtered_df.groupby('Data')['Preço Total'].sum().reset_index(),
            x='Data',
            y='Preço Total',
            title="Vendas ao Longo do Tempo"
        )
        st.plotly_chart(fig, use_container_width=True)

def aba_clientes():
    """Gestão de clientes com análise de gastos"""
    st.header("👥 Gestão de Clientes")
    
    df = carregar_clientes()
    if df.empty:
        st.warning("Nenhum dado de cliente encontrado")
        return
    
    # Renomear colunas
    df = df.rename(columns={
        "_id": "Cliente",
        "TotalGasto": "Total Gasto (R$)",
        "QuantidadeCompras": "Qtd. Compras"
    })
    
    # Filtros
    st.subheader("Filtros")
    cidades = st.multiselect(
        "Selecione cidades",
        options=df['Cidade'].unique(),
        default=df['Cidade'].unique()[:2]
    )
    
    # Aplicar filtros
    filtered_df = df[df['Cidade'].isin(cidades)] if cidades else df
    
    # Visualização
    st.dataframe(
        filtered_df.sort_values("Total Gasto (R$)", ascending=False),
        column_config={
            "Total Gasto (R$)": st.column_config.NumberColumn(format="R$ %.2f")
        }
    )
    
    # Métricas
    st.subheader("Métricas")
    col1, col2, col3 = st.columns(3)
    col1.metric("Clientes", len(filtered_df))
    col2.metric("Gasto Médio", f"R$ {filtered_df['Total Gasto (R$)'].mean():.2f}")
    col3.metric("Compras Média", f"{filtered_df['Qtd. Compras'].mean():.1f}")

def aba_logistica():
    """Otimização logística com mapa de vendas"""
    st.header("🚚 Otimização Logística")
    
    df = carregar_vendas()
    if df.empty:
        st.warning("Nenhum dado encontrado para análise")
        return
    
    # Análise por município
    st.subheader("Vendas por Município")
    
    # Obter coordenadas aproximadas (simulação)
    coordenadas = {
        "São Paulo": (-23.5505, -46.6333),
        "Rio de Janeiro": (-22.9068, -43.1729),
        "Belo Horizonte": (-19.9167, -43.9345)
    }
    
    # Processar dados
    vendas_por_cidade = df.groupby('Cidade').agg({
        'Preço Total': 'sum',
        'Quantidade': 'sum',
        'Produto': 'count'
    }).reset_index()
    
    # Adicionar coordenadas
    vendas_por_cidade['lat'] = vendas_por_cidade['Cidade'].map(lambda x: coordenadas.get(x, (0, 0))[0]
    vendas_por_cidade['lon'] = vendas_por_cidade['Cidade'].map(lambda x: coordenadas.get(x, (0, 0))[1]
    
    # Mapa
    st.map(vendas_por_cidade,
           latitude='lat',
           longitude='lon',
           size='Preço Total',
           color='Preço Total',
           zoom=4)
    
    # Tabela detalhada
    st.dataframe(
        vendas_por_cidade.sort_values('Preço Total', ascending=False),
        column_config={
            "Preço Total": st.column_config.NumberColumn(format="R$ %.2f"),
            "Quantidade": "Qtd. Itens",
            "Produto": "Qtd. Vendas"
        }
    )

# =============================================
# INTERFACE PRINCIPAL
# =============================================

# Configuração da página
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
