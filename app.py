import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import pydeck as pdk
import hashlib
import logging
import os

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

# Dados de exemplo (substitua pela sua conexão MongoDB)
@st.cache_data
def load_sample_data():
    clientes = pd.DataFrame({
        'Cliente': ['Cliente A', 'Cliente B', 'Cliente C', 'Cliente D'],
        'Total Gasto': [1250.50, 3420.75, 876.30, 5432.10],
        'Última Compra': ['2023-10-15', '2023-11-02', '2023-09-28', '2023-11-10'],
        'Região': ['Sudeste', 'Nordeste', 'Sul', 'Sudeste']
    })
    
    logistica = pd.DataFrame({
        'Região': ['Sudeste', 'Nordeste', 'Sul', 'Centro-Oeste', 'Norte'],
        'Total Vendas': [125430.50, 78420.30, 45670.80, 23450.60, 18760.40],
        'Entregas': [1254, 876, 543, 321, 210]
    })
    
    return clientes, logistica

# =============================================
# FUNÇÕES DE VISUALIZAÇÃO
# =============================================
def show_clientes(df):
    st.write("## 📋 Dados dos Clientes")
    st.dataframe(df.sort_values('Total Gasto', ascending=False))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Top Clientes por Valor Gasto")
        fig = px.bar(df.nlargest(5, 'Total Gasto'), 
                     x='Cliente', y='Total Gasto',
                     color='Região')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.write("### Distribuição por Região")
        fig = px.pie(df, names='Região', values='Total Gasto')
        st.plotly_chart(fig, use_container_width=True)

def show_logistica(df):
    st.write("## 🚚 Dados de Logística")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Vendas por Região")
        fig = px.bar(df, x='Região', y='Total Vendas',
                     color='Região')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.write("### Entregas por Região")
        fig = px.pie(df, names='Região', values='Entregas')
        st.plotly_chart(fig, use_container_width=True)
    
    st.write("### Mapa de Distribuição")
    # Exemplo simples - você pode substituir por coordenadas reais
    df_map = df.copy()
    df_map['lat'] = [-23.55, -12.97, -30.03, -15.78, -3.72]  # Latitudes aproximadas
    df_map['lon'] = [-46.63, -38.50, -51.23, -47.93, -61.20] # Longitudes aproximadas
    
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
            latitude=-15,
            longitude=-55,
            zoom=3,
            pitch=50,
        ),
        layers=[
            pdk.Layer(
                'ColumnLayer',
                data=df_map,
                get_position='[lon, lat]',
                get_elevation='Total Vendas/1000',
                elevation_scale=100,
                radius=50000,
                get_fill_color='[200, 30, 0, 160]',
                pickable=True,
                auto_highlight=True,
            ),
        ],
        tooltip={
            'html': '<b>Região:</b> {Região}<br><b>Vendas:</b> R$ {Total Vendas:,.2f}',
            'style': {
                'color': 'white'
            }
        }
    ))

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

if not st.session_state.logged_in:
    login_page()

# =============================================
# APLICAÇÃO PRINCIPAL
# =============================================
clientes_df, logistica_df = load_sample_data()

# Menu lateral
with st.sidebar:
    st.title("Menu")
    selected = st.selectbox("Opções", 
                          ["Dashboard", "Clientes", "Logística", "Relatórios", "Configurações"])
    
    if st.button("Sair"):
        st.session_state.logged_in = False
        st.rerun()

# Conteúdo principal
if selected == "Dashboard":
    st.title("📊 Dashboard Geral")
    st.write("Bem-vindo ao painel de administração do E-Shop Brasil")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total de Clientes", len(clientes_df))
        st.metric("Faturamento Total", f"R$ {clientes_df['Total Gasto'].sum():,.2f}")
    
    with col2:
        st.metric("Regiões Atendidas", len(logistica_df))
        st.metric("Total de Entregas", logistica_df['Entregas'].sum())

elif selected == "Clientes":
    show_clientes(clientes_df)

elif selected == "Logística":
    show_logistica(logistica_df)

elif selected == "Relatórios":
    st.title("📈 Relatórios")
    st.write("Área de relatórios - em desenvolvimento")

elif selected == "Configurações":
    st.title("⚙️ Configurações")
    st.write("Configurações do sistema - em desenvolvimento")
