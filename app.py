# Todas as importações primeiro
import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import pydeck as pdk
import hashlib
import logging
import time
import os

# =============================================
# CONFIGURAÇÃO DA PÁGINA - DEVE SER O PRIMEIRO COMANDO STREAMLIT
# =============================================
st.set_page_config(
    page_title="E-Shop Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================
# CONFIGURAÇÕES INICIAIS (APÓS A CONFIG DA PÁGINA)
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
            serverSelectionTimeoutMS=5000,
            socketTimeoutMS=30000,
            connectTimeoutMS=30000,
            retryWrites=True
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
# PÁGINA DE LOGIN
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
            if 'Data' in df.columns:
                df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
            if all(col in df.columns for col in ['Quantidade', 'Preço Unitário']):
                df['Preço Total'] = df['Quantidade'] * df['Preço Unitário']
            
            with st.expander("Pré-visualização (10 primeiras linhas)"):
                st.dataframe(df.head(10))
                
            if st.button("Salvar no Banco de Dados"):
                with st.spinner("Salvando dados..."):
                    qtd = salvar_no_banco(df)
                    if qtd > 0:
                        st.success(f"{qtd} registros salvos com sucesso!")
                        st.cache_data.clear()
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
            default=df['Produto'].unique()[:2] if len(df['Produto'].unique()) > 0 else []
        )
    
    with col2:
        if 'Data' in df.columns:
            date_range = st.date_input(
                "Período",
                value=[df['Data'].min(), df['Data'].max()]
            )
    
    # Aplicar filtros
    filtered_df = df.copy()
    if produtos:
        filtered_df = filtered_df[filtered_df['Produto'].isin(produtos)]
    if 'Data' in df.columns:
        filtered_df = filtered_df[filtered_df['Data'].between(*date_range)]
    
    # Visualização
    st.dataframe(filtered_df.sort_values('Data' if 'Data' in df.columns else 'Produto', ascending=False))
    
    # Gráficos
    st.subheader("Análise de Vendas")
    tab1, tab2 = st.tabs(["Por Produto", "Temporal"])
    
    with tab1:
        if not filtered_df.empty:
            fig = px.bar(
                filtered_df.groupby('Produto')['Preço Total'].sum().reset_index(),
                x='Produto',
                y='Preço Total',
                title="Vendas por Produto"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        if 'Data' in filtered_df.columns and not filtered_df.empty:
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
        default=df['Cidade'].unique()[:2] if len(df['Cidade'].unique()) > 0 else []
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
    col2.metric("Gasto Médio", f"R$ {filtered_df['Total Gasto (R$)'].mean():.2f}" if not filtered_df.empty else "R$ 0.00")
    col3.metric("Compras Média", f"{filtered_df['Qtd. Compras'].mean():.1f}" if not filtered_df.empty else "0")

def aba_logistica():
    """Otimização logística com mapa de vendas"""
    st.header("🚚 Otimização Logística")
    
    df = carregar_vendas()
    if df.empty:
        st.warning("Nenhum dado encontrado para análise")
        return
    
    # Dicionário de coordenadas (latitude, longitude)
    coordenadas = {
        "São Paulo": (-23.5505, -46.6333),
        "Rio de Janeiro": (-22.9068, -43.1729),
        "Belo Horizonte": (-19.9167, -43.9345),
        "Porto Alegre": (-30.0346, -51.2177),
        "Curitiba": (-25.4296, -49.2717),
        "Salvador": (-12.9714, -38.5014),
        "Recife": (-8.0476, -34.8770),
        "Fortaleza": (-3.7319, -38.5267),
        "Manaus": (-3.1190, -60.0217),
        "Goiânia": (-16.6869, -49.2648)
    }
    
    # Processar dados
    vendas_por_cidade = df.groupby('Cidade').agg({
        'Preço Total': 'sum',
        'Quantidade': 'sum',
        'Produto': 'count'
    }).reset_index()
    
    # Adicionar coordenadas de forma segura
    vendas_por_cidade['lat'] = vendas_por_cidade['Cidade'].apply(
        lambda x: coordenadas.get(x, (0, 0))[0]
    )
    vendas_por_cidade['lon'] = vendas_por_cidade['Cidade'].apply(
        lambda x: coordenadas.get(x, (0, 0))[1]
    )
    
    # Mapa interativo
    st.pydeck_chart(
        pdk.Deck(
            map_style='mapbox://styles/mapbox/light-v9',
            initial_view_state=pdk.ViewState(
                latitude=-15,
                longitude=-55,
                zoom=3,
                pitch=50,
            ),
            layers=[
                pdk.Layer(
                    'ScatterplotLayer',
                    data=vendas_por_cidade,
                    get_position='[lon, lat]',
                    get_color='[200, 30, 0, 160]',
                    get_radius='Preço Total / 1000',
                    pickable=True
                ),
            ],
            tooltip={
                "html": "<b>Cidade:</b> {Cidade}<br><b>Vendas:</b> R$ {Preço Total:,.2f}",
                "style": {
                    "backgroundColor": "steelblue",
                    "color": "white"
                }
            }
        )
    )
    
    # Tabela detalhada
    st.subheader("Detalhes por Município")
    st.dataframe(
        vendas_por_cidade.sort_values('Preço Total', ascending=False),
        column_config={
            "Preço Total": st.column_config.NumberColumn(
                "Total Vendido",
                format="R$ %.2f",
                width="medium"
            ),
            "Quantidade": st.column_config.NumberColumn(
                "Qtd. Itens",
                format="%.0f",
                width="small"
            ),
            "Produto": st.column_config.NumberColumn(
                "Qtd. Vendas",
                format="%.0f",
                width="small"
            ),
            "Cidade": "Município"
        },
        hide_index=True,
        use_container_width=True
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
        st.session_state.clear()
        st.rerun()

# Conteúdo principal
if aba_selecionada == "Dashboard":
    st.title("📊 Dashboard Principal")
    st.write("Bem-vindo ao painel de controle E-Shop Brasil")
    
    # Métricas rápidas
    try:
        df_vendas = carregar_vendas()
        df_clientes = carregar_clientes()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Vendas", 
                   f"R$ {df_vendas['Preço Total'].sum():,.2f}" if not df_vendas.empty else "R$ 0.00")
        col2.metric("Clientes Ativos", 
                   len(df_clientes) if not df_clientes.empty else 0)
        col3.metric("Produtos Vendidos", 
                   df_vendas['Produto'].nunique() if not df_vendas.empty else 0)
        
        # Gráfico rápido
        if not df_vendas.empty and 'Data' in df_vendas.columns:
            st.subheader("Vendas Recentes")
            fig = px.line(
                df_vendas.groupby('Data')['Preço Total'].sum().reset_index().tail(30),
                x='Data',
                y='Preço Total',
                title="Últimos 30 dias"
            )
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Erro ao carregar dados do dashboard: {str(e)}")
    
elif aba_selecionada == "Upload de Arquivos":
    aba_upload()
    
elif aba_selecionada == "Visualização de Dados":
    aba_visualizacao()
    
elif aba_selecionada == "Gestão de Clientes":
    aba_clientes()
    
elif aba_selecionada == "Otimização Logística":
    aba_logistica()
