import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px

# Conexão com o MongoDB
client = MongoClient("mongodb://admin:password@mongodb:27017/")
db = client.eshop

st.title("E-Shop Brasil - Painel de Dados")

# Menu de opções
option = st.sidebar.selectbox(
    "Menu",
    ("Importar Dados", "Visualizar Dados", "Análise de Clientes", "Otimização Logística")
)

if option == "Importar Dados":
    st.header("Importar Dados para o MongoDB")
    uploaded_file = st.file_uploader("Escolha um arquivo CSV", type="csv")
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if st.button("Importar para MongoDB"):
            db.vendas.insert_many(df.to_dict('records'))
            st.success("Dados importados com sucesso!")

elif option == "Visualizar Dados":
    st.header("Dados Armazenados")
    collections = db.list_collection_names()
    selected_collection = st.selectbox("Selecione uma coleção", collections)
    
    if selected_collection:
        data = list(db[selected_collection].find().limit(100))
        df = pd.DataFrame(data)
        st.dataframe(df)

elif option == "Análise de Clientes":
    st.header("📊 Análise de Comportamento de Clientes")
    
    # Obter dados dos clientes
    clientes_data = list(db.vendas.aggregate([
        {"$group": {
            "_id": "$ID Cliente",
            "Nome": {"$first": "$Nome do Cliente"},
            "Cidade": {"$first": "$Cidade"},
            "TotalCompras": {"$sum": 1},
            "TotalGasto": {"$sum": "$Preço Total (R$)"}
        }},
        {"$sort": {"TotalGasto": -1}}
    ]))
    
    if clientes_data:
        df_clientes = pd.DataFrame(clientes_data)
        
        # Mostrar tabela de clientes
        st.subheader("Lista de Clientes")
        st.dataframe(df_clientes[["_id", "Nome", "Cidade", "TotalCompras", "TotalGasto"]]
                    .rename(columns={"_id": "ID Cliente", "TotalGasto": "Total Gasto (R$)"}))
        
        # Gráfico de top clientes
        st.subheader("Top 10 Clientes por Valor Gasto")
        top_clientes = df_clientes.nlargest(10, 'TotalGasto')
        fig = px.bar(top_clientes, x='Nome', y='TotalGasto', 
                    labels={'TotalGasto': 'Total Gasto (R$)', 'Nome': 'Cliente'},
                    color='Cidade')
        st.plotly_chart(fig)
        
        # Distribuição por cidade
        st.subheader("Distribuição de Clientes por Cidade")
        cidade_counts = df_clientes['Cidade'].value_counts().reset_index()
        cidade_counts.columns = ['Cidade', 'Quantidade']
        fig = px.pie(cidade_counts, values='Quantidade', names='Cidade')
        st.plotly_chart(fig)
    else:
        st.warning("Nenhum dado de cliente encontrado. Importe dados primeiro.")

elif option == "Otimização Logística":
    st.header("🚚 Otimização de Rotas e Estoque")
    
    # Análise por região
    st.subheader("Entregas por Região")
    regiao_data = list(db.vendas.aggregate([
        {"$group": {
            "_id": "$Cidade",
            "TotalEntregas": {"$sum": 1},
            "ItensVendidos": {"$sum": "$Quantidade"}
        }},
        {"$sort": {"TotalEntregas": -1}}
    ]))
    
    if regiao_data:
        df_regiao = pd.DataFrame(regiao_data)
        
        # Gráfico de entregas por região
        fig1 = px.bar(df_regiao, x='_id', y='TotalEntregas',
                     labels={'_id': 'Cidade', 'TotalEntregas': 'Número de Entregas'},
                     title='Total de Entregas por Cidade')
        st.plotly_chart(fig1)
        
        # Gráfico de itens vendidos por região
        fig2 = px.pie(df_regiao, values='ItensVendidos', names='_id',
                     title='Distribuição de Itens Vendidos por Cidade')
        st.plotly_chart(fig2)
        
        # Sugestões de otimização
        st.subheader("Sugestões de Otimização")
        cidade_mais_entregas = df_regiao.iloc[0]['_id']
        st.markdown(f"""
        - **Foco em {cidade_mais_entregas}**: Esta cidade tem o maior número de entregas. 
          Considere aumentar o estoque local ou estabelecer um centro de distribuição regional.
        - **Análise de rotas**: As cidades com mais entregas podem se beneficiar de rotas otimizadas.
        - **Estoque dinâmico**: Ajuste os níveis de estoque com base na demanda regional.
        """)
    else:
        st.warning("Nenhum dado logístico encontrado. Importe dados primeiro.")
