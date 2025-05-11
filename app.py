import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px

# Configuração inicial do Streamlit
st.set_page_config(page_title="E-Shop Brasil", layout="wide")

# Conexão com o MongoDB
try:
    client = MongoClient("mongodb://admin:password@mongodb:27017/", serverSelectionTimeoutMS=5000)
    db = client.eshop
    client.server_info()  # Testa a conexão
    st.success("✅ Conectado ao MongoDB!")
except Exception as e:
    st.error(f"❌ Falha na conexão com MongoDB: {e}")

# Menu principal
option = st.sidebar.selectbox(
    "Menu de Navegação",
    ["Importar Dados", "Visualizar Dados", "Análise de Clientes", "Otimização Logística"],
    index=0
)

# Função para carregar dados
def load_data():
    try:
        data = list(db.vendas.find({}))
        if not data:
            st.warning("⚠️ Nenhum dado encontrado no banco de dados")
            return None
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

if option == "Importar Dados":
    st.header("📤 Importação de Dados")
    uploaded_file = st.file_uploader("Carregue seu arquivo CSV", type="csv")
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.write("Pré-visualização dos dados:", df.head())
            
            if st.button("Importar para o MongoDB"):
                db.vendas.delete_many({})  # Limpa a coleção existente
                db.vendas.insert_many(df.to_dict('records'))
                st.success(f"✅ {len(df)} registros importados com sucesso!")
        except Exception as e:
            st.error(f"Erro ao importar: {e}")

elif option == "Visualizar Dados":
    st.header("📋 Visualização de Dados")
    df = load_data()
    if df is not None:
        st.dataframe(df)
        
        # Mostrar estatísticas básicas
        st.subheader("Estatísticas Básicas")
        st.json({
            "Total de Registros": len(df),
            "Clientes Únicos": df['ID Cliente'].nunique(),
            "Período dos Dados": {
                "Início": df['Data'].min(),
                "Fim": df['Data'].max()
            }
        })

elif option == "Análise de Clientes":
    st.header("👥 Análise de Comportamento de Clientes")
    df = load_data()
    
    if df is not None:
        # Métricas principais
        col1, col2, col3 = st.columns(3)
        col1.metric("Clientes Únicos", df['ID Cliente'].nunique())
        col2.metric("Cidades Atendidas", df['Cidade'].nunique())
        col3.metric("Ticket Médio", f"R${df['Preço Total (R$)'].mean():.2f}")
        
        # Top clientes
        st.subheader("🏆 Top 10 Clientes")
        top_clientes = df.groupby('Nome do Cliente').agg({
            'Preço Total (R$)': 'sum',
            'Quantidade': 'sum',
            'Cidade': 'first'
        }).nlargest(10, 'Preço Total (R$)')
        
        st.dataframe(top_clientes.style.format({'Preço Total (R$)': "R$ {:.2f}"}))
        
        # Análise geográfica
        st.subheader("🗺️ Distribuição Geográfica")
        fig = px.pie(
            df.groupby('Cidade')['ID Cliente'].nunique().reset_index(),
            values='ID Cliente',
            names='Cidade',
            title='Distribuição de Clientes por Cidade'
        )
        st.plotly_chart(fig, use_container_width=True)

elif option == "Otimização Logística":
    st.header("🚛 Otimização de Rotas e Estoque")
    df = load_data()
    
    if df is not None:
        # Análise por cidade
        st.subheader("📌 Entregas por Região")
        cidade_stats = df.groupby('Cidade').agg({
            'Quantidade': 'sum',
            'ID Cliente': 'nunique',
            'Preço Total (R$)': 'sum'
        }).sort_values('Quantidade', ascending=False)
        
        fig1 = px.bar(
            cidade_stats.reset_index(),
            x='Cidade',
            y='Quantidade',
            color='Preço Total (R$)',
            title='Volume de Entregas por Cidade'
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # Gestão de estoque
        st.subheader("📦 Análise de Estoque")
        produto_stats = df.groupby('Item').agg({
            'Quantidade': 'sum',
            'Preço Unitário (R$)': 'mean'
        }).sort_values('Quantidade', ascending=False)
        
        fig2 = px.treemap(
            produto_stats.reset_index(),
            path=['Item'],
            values='Quantidade',
            title='Demanda de Produtos'
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        # Recomendações
        st.subheader("💡 Recomendações de Otimização")
        cidade_principal = cidade_stats.index[0]
        produto_principal = produto_stats.index[0]
        
        st.markdown(f"""
        - **Aumentar estoque** de **{produto_principal}** em **{cidade_principal}**
        - **Otimizar rotas** para a região de **{cidade_principal}**
        - **Estoque mínimo** para produtos menos vendidos
        """)
