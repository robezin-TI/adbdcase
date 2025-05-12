import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
from datetime import datetime
import hashlib
from bson.objectid import ObjectId
import logging

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================
# CONFIGURAÇÃO DE AUTENTICAÇÃO
# =============================================
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

# Dados de login válidos
LOGIN = "adminfecaf"
PASSWORD_HASH = make_hashes("fecafadbd")  # Hash da senha

# Página de login
def login_page():
    st.title("🔒 Login - Painel E-Shop Brasil")
    st.markdown("---")
    
    login = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    
    if st.button("Acessar Sistema"):
        if login == LOGIN and check_hashes(password, PASSWORD_HASH):
            st.session_state.logged_in = True
            st.experimental_rerun()
        else:
            st.error("Credenciais inválidas. Tente novamente.")
    
    st.markdown("---")
    st.caption("Sistema de gestão de dados para a E-Shop Brasil")

# Verifica autenticação
if not hasattr(st.session_state, 'logged_in'):
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_page()
    st.stop()

# =============================================
# CONEXÃO COM O MONGODB
# =============================================
@st.cache_resource
def init_connection():
    try:
        client = MongoClient("mongodb://admin:password@mongodb:27017/eshop?authSource=admin")
        client.server_info()
        logger.info("Conexão com MongoDB estabelecida")
        return client
    except Exception as e:
        logger.error(f"Erro na conexão: {str(e)}")
        st.error(f"⚠️ Falha na conexão com o banco de dados: {str(e)}")
        return None

client = init_connection()
db = client.eshop if client else None

# =============================================
# FUNÇÕES PRINCIPAIS
# =============================================
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

# =============================================
# INTERFACE PRINCIPAL
# =============================================
st.set_page_config(page_title="E-Shop Analytics", layout="wide")
st.title("📊 Painel de Gestão - E-Shop Brasil")

# Menu lateral
with st.sidebar:
    st.image("https://via.placeholder.com/150x50?text=E-Shop", width=150)
    st.markdown("## Navegação")
    option = st.selectbox(
        "Selecione a opção",
        ["Importar Dados", "Visualizar Dados", "Gerenciar Dados", "Análise de Clientes", "Otimização Logística"],
        index=0
    )
    st.markdown("---")
    if st.button("🔒 Sair"):
        st.session_state.logged_in = False
        st.experimental_rerun()

# =============================================
# PÁGINAS DO SISTEMA
# =============================================

# PÁGINA: IMPORTAR DADOS
if option == "Importar Dados":
    st.header("📤 Importação de Dados")
    st.markdown("---")
    
    uploaded_file = st.file_uploader("Selecione o arquivo CSV", type=["csv"])
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
            
            # Pré-processamento
            df.columns = df.columns.str.strip()
            if 'Data' in df.columns:
                df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
            
            st.subheader("Pré-visualização dos Dados")
            st.dataframe(df.head(3))
            
            if st.button("Confirmar Importação", type="primary"):
                if db is None:
                    st.error("Banco de dados não conectado")
                else:
                    with st.spinner("Importando dados..."):
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
                            ✅ Importação concluída com sucesso!
                            - Registros importados: {len(result.inserted_ids)}
                            - Registros ignorados (dados inválidos): {len(df) - len(df_clean)}
                            """)
                        except Exception as e:
                            st.error(f"Erro durante a importação: {str(e)}")
                            logger.exception("Erro na importação")
                        
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {str(e)}")
            logger.exception("Erro no processamento do CSV")

# PÁGINA: VISUALIZAR DADOS
elif option == "Visualizar Dados":
    st.header("📋 Dados Armazenados")
    st.markdown("---")
    
    df = load_data()
    if df is not None:
        st.dataframe(df)
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="Exportar como CSV",
                data=df.to_csv(index=False).encode('utf-8'),
                file_name='dados_exportados.csv',
                mime='text/csv',
                use_container_width=True
            )
        with col2:
            if st.button("Atualizar Dados", use_container_width=True):
                st.experimental_rerun()

# PÁGINA: GERENCIAR DADOS
elif option == "Gerenciar Dados":
    st.header("✏️ Gerenciamento de Dados")
    st.markdown("---")
    
    df = load_data()
    if df is not None:
        # Seção para adicionar novo registro
        with st.expander("➕ Adicionar Novo Registro", expanded=False):
            with st.form("novo_registro_form"):
                col1, col2 = st.columns(2)
                with col1:
                    novo_id = st.number_input("ID Cliente", min_value=1)
                    novo_nome = st.text_input("Nome do Cliente")
                    novo_item = st.selectbox("Item", ["Notebook", "Micro Ondas", "Liquidificador", "Ventilador", "Cafeteira"])
                with col2:
                    nova_data = st.date_input("Data")
                    nova_cidade = st.selectbox("Cidade", ["Embu", "Itapecerica", "Taboão"])
                    nova_quantidade = st.number_input("Quantidade", min_value=1)
                    novo_preco = st.number_input("Preço Unitário (R$)", min_value=0.0)
                
                if st.form_submit_button("Adicionar Registro", type="primary"):
                    novo_registro = {
                        "ID Cliente": novo_id,
                        "Data": str(nova_data),
                        "Nome do Cliente": novo_nome,
                        "Cidade": nova_cidade,
                        "Item": novo_item,
                        "Quantidade": nova_quantidade,
                        "Preço Unitário (R$)": novo_preco,
                        "Preço Total (R$)": nova_quantidade * novo_preco
                    }
                    db.vendas.insert_one(novo_registro)
                    st.success("Registro adicionado com sucesso!")
                    st.experimental_rerun()
        
        # Seção para editar/excluir registros
        st.markdown("---")
        st.subheader("🛠️ Editar ou Excluir Registros Existentes")
        
        # Filtros
        with st.form("filtro_form"):
            col1, col2 = st.columns(2)
            with col1:
                filtro_id = st.number_input("Filtrar por ID Cliente", min_value=1)
            with col2:
                filtro_nome = st.text_input("Filtrar por Nome do Cliente")
            
            if st.form_submit_button("Aplicar Filtros"):
                st.experimental_rerun()
        
        # Aplicar filtros
        registros_filtrados = df.copy()
        if filtro_id:
            registros_filtrados = registros_filtrados[registros_filtrados["ID Cliente"] == filtro_id]
        if filtro_nome:
            registros_filtrados = registros_filtrados[
                registros_filtrados["Nome do Cliente"].str.contains(filtro_nome, case=False, na=False)
            ]
        
        if not registros_filtrados.empty:
            # Selecionar registro
            registro_selecionado = st.selectbox(
                "Selecione um registro para editar/excluir",
                registros_filtrados["_id"].astype(str) + " | " + 
                registros_filtrados["Nome do Cliente"] + " | " + 
                registros_filtrados["Item"] + " | R$" + 
                registros_filtrados["Preço Total (R$)"].astype(str)
            )
            
            registro_id = ObjectId(registro_selecionado.split(" | ")[0])
            registro = db.vendas.find_one({"_id": registro_id})
            
            # Formulário de edição
            with st.form("editar_registro_form"):
                st.markdown("### Editar Registro")
                
                col1, col2 = st.columns(2)
                with col1:
                    edit_id = st.number_input("ID Cliente", value=registro["ID Cliente"], disabled=True)
                    edit_nome = st.text_input("Nome do Cliente", value=registro["Nome do Cliente"])
                    edit_item = st.selectbox(
                        "Item", 
                        ["Notebook", "Micro Ondas", "Liquidificador", "Ventilador", "Cafeteira"],
                        index=["Notebook", "Micro Ondas", "Liquidificador", "Ventilador", "Cafeteira"].index(registro["Item"])
                    )
                with col2:
                    edit_data = st.date_input("Data", value=datetime.strptime(registro["Data"], "%Y-%m-%d").date())
                    edit_cidade = st.selectbox(
                        "Cidade", 
                        ["Embu", "Itapecerica", "Taboão"],
                        index=["Embu", "Itapecerica", "Taboão"].index(registro["Cidade"])
                    )
                    edit_quantidade = st.number_input("Quantidade", min_value=1, value=registro["Quantidade"])
                    edit_preco = st.number_input("Preço Unitário (R$)", min_value=0.0, value=registro["Preço Unitário (R$)"])
                
                col1, col2, col3 = st.columns([1,1,2])
                with col1:
                    if st.form_submit_button("💾 Salvar Alterações"):
                        db.vendas.update_one(
                            {"_id": registro_id},
                            {"$set": {
                                "Nome do Cliente": edit_nome,
                                "Data": str(edit_data),
                                "Cidade": edit_cidade,
                                "Item": edit_item,
                                "Quantidade": edit_quantidade,
                                "Preço Unitário (R$)": edit_preco,
                                "Preço Total (R$)": edit_quantidade * edit_preco
                            }}
                        )
                        st.success("Registro atualizado com sucesso!")
                        st.experimental_rerun()
                with col2:
                    if st.form_submit_button("🗑️ Excluir Registro"):
                        db.vendas.delete_one({"_id": registro_id})
                        st.success("Registro excluído com sucesso!")
                        st.experimental_rerun()
        else:
            st.warning("Nenhum registro encontrado com os filtros aplicados")

# PÁGINA: ANÁLISE DE CLIENTES
elif option == "Análise de Clientes":
    st.header("👥 Análise de Clientes")
    st.markdown("---")
    
    df = load_data()
    if df is not None:
        # Métricas principais
        st.subheader("📊 Métricas Principais")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Clientes", df['ID Cliente'].nunique())
        with col2:
            st.metric("Cidades Atendidas", df['Cidade'].nunique())
        with col3:
            st.metric("Ticket Médio", f"R$ {df['Preço Total (R$)'].mean():.2f}")
        
        # Top clientes
        st.markdown("---")
        st.subheader("🏆 Top 10 Clientes por Valor Gasto")
        top_clientes = df.groupby('Nome do Cliente').agg({
            'Preço Total (R$)': 'sum',
            'Quantidade': 'sum',
            'Cidade': 'first'
        }).nlargest(10, 'Preço Total (R$)')
        st.dataframe(top_clientes.style.format({'Preço Total (R$)': "R$ {:.2f}"}))

# PÁGINA: OTIMIZAÇÃO LOGÍSTICA
elif option == "Otimização Logística":
    st.header("🚚 Otimização Logística")
    st.markdown("---")
    
    df = load_data()
    if df is not None:
        st.subheader("📌 Distribuição Geográfica de Entregas")
        cidade_stats = df.groupby('Cidade').agg({
            'Quantidade': 'sum',
            'ID Cliente': 'nunique'
        }).sort_values('Quantidade', ascending=False)
        
        fig = px.bar(
            cidade_stats.reset_index(),
            x='Cidade',
            y='Quantidade',
            color='ID Cliente',
            title='Volume de Entregas por Cidade',
            labels={'Quantidade': 'Total de Itens', 'ID Cliente': 'Clientes Únicos'}
        )
        st.plotly_chart(fig, use_container_width=True)
