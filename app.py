import streamlit as st
from pymongo import MongoClient
import pandas as pd

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
    st.header("Análise de Comportamento de Clientes")
    # Adicione aqui análises de clientes e recomendações personalizadas

elif option == "Otimização Logística":
    st.header("Otimização de Rotas e Estoque")
    # Adicione aqui análises logísticas
