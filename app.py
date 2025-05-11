import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import os

# Conexão com o MongoDB
client = MongoClient("mongodb://admin:password@mongodb:27017/")
db = client.eshop

# Configuração para GitHub Codespaces
if 'CODESPACES' in os.environ:
    st.set_page_config(serverAddress="0.0.0.0", serverPort=8501)

st.title("E-Shop Brasil - Painel de Dados")

# Menu de opções
option = st.sidebar.selectbox(
    "Menu",
    ("Importar Dados", "Visualizar Dados", "Análise de Clientes", "Otimização Logística")
)

if option == "Importar Dados":
    st.header("📤 Importar Dados para o MongoDB")
    uploaded_file = st.file_uploader("Escolha um arquivo CSV", type="csv")
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if st.button("Importar para MongoDB"):
            db.vendas.insert_many(df.to_dict('records'))
            st.success("✅ Dados importados com sucesso!")

elif option == "Visualizar Dados":
    st.header("📋 Dados Armazenados")
    collections = db.list_collection_names()
    selected_collection = st.selectbox("Selecione uma coleção", collections)
    
    if selected_collection:
        data = list(db[selected_collection].find().limit(100))
        df = pd.DataFrame(data)
        st.dataframe(df)

elif option == "Análise de Clientes":
    st.header("👥 Análise de Comportamento de Clientes")
    
    # Carrega dados
    clientes_data = list(db.vendas.find())
    
    if clientes_data:
        df = pd.DataFrame(clientes_data)
        
        # 1. Métricas-chave
        st.subheader("📊 Métricas-Chave")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Clientes Únicos", df['ID Cliente'].nunique())
        with col2:
            st.metric("Cidades Atendidas", df['Cidade'].nunique())
        with col3:
            st.metric("Ticket Médio", f"R${df['Preço Total (R$)'].mean():.2f}")

        # 2. Top clientes
        st.subheader("🏆 Top 10 Clientes")
        top_clientes = df.groupby('Nome do Cliente').agg({
            'Preço Total (R$)': 'sum',
            'Quantidade': 'sum',
            'Cidade': 'first'
        }).nlargest(10, 'Preço Total (R$)').reset_index()
        
        fig1 = px.bar(top_clientes, 
                     x='Nome do Cliente', 
                     y='Preço Total (R$)',
                     color='Cidade',
                     title='Clientes que Mais Compram')
        st.plotly_chart(fig1)

        # 3. Preferências por cidade
        st.subheader("🗺️ Distribuição Geográfica")
        cidade_stats = df.groupby('Cidade').agg({
            'Preço Total (R$)': 'sum',
            'ID Cliente': 'nunique'
        }).reset_index()
        
        fig2 = px.pie(cidade_stats, 
                     values='Preço Total (R$)', 
                     names='Cidade',
                     title='Distribuição de Vendas por Cidade')
        st.plotly_chart(fig2)

    else:
        st.warning("⚠️ Nenhum dado encontrado. Importe dados primeiro.")

elif option == "Otimização Logística":
    st.header("🚚 Otimização de Rotas e Estoque")
    
    # Carrega dados
    vendas_data = list(db.vendas.find())
    
    if vendas_data:
        df = pd.DataFrame(vendas_data)
        
        # 1. Análise por cidade
        st.subheader("📌 Entregas por Região")
        cidade_entregas = df.groupby('Cidade').agg({
            'Quantidade': 'sum',
            'ID Cliente': 'nunique'
        }).reset_index()
        
        fig1 = px.bar(cidade_entregas,
                     x='Cidade',
                     y='Quantidade',
                     color='ID Cliente',
                     title='Volume de Entregas por Cidade')
        st.plotly_chart(fig1)

        # 2. Gestão de estoque
        st.subheader("📦 Gestão de Estoque")
        produto_stats = df.groupby('Item').agg({
            'Quantidade': 'sum',
            'Preço Unitário (R$)': 'mean'
        }).sort_values('Quantidade', ascending=False)
        
        fig2 = px.treemap(produto_stats.reset_index(),
                         path=['Item'],
                         values='Quantidade',
                         title='Demanda Relativa por Produto')
        st.plotly_chart(fig2)

        # 3. Sugestões automáticas
        st.subheader("💡 Recomendações")
        cidade_critica = cidade_entregas.loc[cidade_entregas['Quantidade'].idxmax(), 'Cidade']
        produto_critico = produto_stats.index[0]
        
        st.markdown(f"""
        - **Estoque prioritário**: Aumentar estoque de **{produto_critico}** em **{cidade_critica}**
        - **Centro de distribuição**: Sugerido para **{cidade_critica}**
        - **Rotas otimizadas**: Agrupar entregas em **{cidade_critica}** no mesmo dia
        """)

    else:
        st.warning("⚠️ Nenhum dado encontrado. Importe dados primeiro.")
