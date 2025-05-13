import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
from datetime import datetime
import hashlib
from bson.objectid import ObjectId
import logging
import os

# =============================================
# CONFIGURAÇÕES ESPECÍFICAS PARA CODESPACES
# =============================================
if os.environ.get('CODESPACES') == 'true':
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_SERVER_PORT'] = '8501'
    os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'

# =============================================
# CONFIGURAÇÃO DE LOGGING
# =============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================
# CONFIGURAÇÃO DE AUTENTICAÇÃO
# =============================================
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if not password or not hashed_text:
        return False
    return make_hashes(password) == hashed_text

# Dados de login válidos
LOGIN = "adminfecaf"
PASSWORD_HASH = make_hashes("fecafadbd")

# =============================================
# CONEXÃO COM O MONGODB (OTIMIZADA)
# =============================================
@st.cache_resource
def init_connection():
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            client = MongoClient(
                "mongodb://admin:password@eshop-mongodb:27017/eshop?authSource=admin",
                serverSelectionTimeoutMS=5000,
                socketTimeoutMS=30000,
                connectTimeoutMS=30000,
                retryWrites=True,
                retryReads=True
            )
            # Testa a conexão
            client.admin.command('ping')
            logger.info("Conexão com MongoDB estabelecida")
            return client
        except Exception as e:
            logger.warning(f"Tentativa {attempt + 1} falhou: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    
    logger.error("Falha ao conectar ao MongoDB após várias tentativas")
    st.error("⚠️ Falha na conexão com o banco de dados. Tente novamente mais tarde.")
    return None

# =============================================
# FUNÇÕES PRINCIPAIS (COM TRATAMENTO DE ERROS)
# =============================================
def load_data():
    try:
        if not db:
            raise ConnectionError("Banco de dados não conectado")
            
        data = list(db.vendas.find({}))
        if not data:
            logger.warning("Nenhum dado encontrado no banco de dados")
            return None
            
        df = pd.DataFrame(data)
        
        # Conversão segura de tipos
        numeric_cols = ['Quantidade', 'Preço Unitário (R$)', 'Preço Total (R$)']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df.dropna()
        
    except Exception as e:
        logger.error(f"Erro ao carregar dados: {str(e)}", exc_info=True)
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None

# =============================================
# PÁGINA DE LOGIN
# =============================================
def login_page():
    st.title("🔒 Login - Painel E-Shop Brasil")
    st.markdown("---")
    
    with st.form("login_form"):
        login = st.text_input("Usuário", key="login_field")
        password = st.text_input("Senha", type="password", key="pass_field")
        
        if st.form_submit_button("Acessar Sistema", use_container_width=True):
            if login == LOGIN and check_hashes(password, PASSWORD_HASH):
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Credenciais inválidas. Tente novamente.")
    
    st.markdown("---")
    st.caption("Sistema de gestão de dados para a E-Shop Brasil")

# =============================================
# CONFIGURAÇÃO INICIAL DA PÁGINA
# =============================================
st.set_page_config(
    page_title="E-Shop Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================
# VERIFICAÇÃO DE AUTENTICAÇÃO
# =============================================
if not hasattr(st.session_state, 'logged_in'):
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_page()
    st.stop()

# Inicializa conexão com MongoDB
client = init_connection()
db = client.eshop if client else None

# =============================================
# INTERFACE PRINCIPAL
# =============================================
st.title("📊 Painel de Gestão - E-Shop Brasil")

# Menu lateral
with st.sidebar:
    st.image("https://via.placeholder.com/150x50?text=E-Shop", width=150)
    st.markdown("## Navegação")
    
    menu_options = [
        "Importar Dados",
        "Visualizar Dados", 
        "Gerenciar Dados",
        "Análise de Clientes",
        "Otimização Logística"
    ]
    
    selected_option = st.selectbox(
        "Selecione a opção",
        menu_options,
        index=0
    )
    
    st.markdown("---")
    if st.button("🔒 Sair", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# =============================================
# PÁGINAS DO SISTEMA
# =============================================

# PÁGINA: IMPORTAR DADOS
if selected_option == "Importar Dados":
    st.header("📤 Importação de Dados")
    st.markdown("---")
    
    with st.expander("Instruções de Importação", expanded=True):
        st.markdown("""
        1. Selecione um arquivo CSV com os dados de vendas
        2. Verifique a pré-visualização
        3. Confirme a importação
        """)
    
    uploaded_file = st.file_uploader(
        "Selecione o arquivo CSV", 
        type=["csv"],
        accept_multiple_files=False,
        key="file_uploader"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
            
            # Pré-processamento
            df.columns = df.columns.str.strip()
            if 'Data' in df.columns:
                df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
            
            with st.expander("Pré-visualização dos Dados (10 primeiras linhas)"):
                st.dataframe(df.head(10), use_container_width=True)
            
            if st.button("Confirmar Importação", type="primary", use_container_width=True):
                if db is None:
                    st.error("Banco de dados não conectado")
                else:
                    with st.spinner("Importando dados..."):
                        try:
                            # Conversão de tipos segura
                            numeric_cols = ['Quantidade', 'Preço Unitário (R$)', 'Preço Total (R$)']
                            for col in numeric_cols:
                                if col in df.columns:
                                    df[col] = pd.to_numeric(df[col], errors='coerce')
                            
                            # Remove linhas com dados inválidos
                            df_clean = df.dropna()
                            
                            # Insere no MongoDB em lotes
                            batch_size = 100
                            total_rows = len(df_clean)
                            inserted_ids = []
                            
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            for i in range(0, total_rows, batch_size):
                                batch = df_clean.iloc[i:i + batch_size].to_dict('records')
                                result = db.vendas.insert_many(batch)
                                inserted_ids.extend(result.inserted_ids)
                                
                                progress = min((i + batch_size) / total_rows, 1.0)
                                progress_bar.progress(progress)
                                status_text.text(f"Progresso: {int(progress * 100)}%")
                            
                            st.success(f"""
                            ✅ Importação concluída com sucesso!
                            - Registros importados: {len(inserted_ids)}
                            - Registros ignorados (dados inválidos): {len(df) - len(df_clean)}
                            """)
                            
                            # Limpa cache após importação
                            st.cache_data.clear()
                            
                        except Exception as e:
                            st.error(f"Erro durante a importação: {str(e)}")
                            logger.exception("Erro na importação")
                        
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {str(e)}")
            logger.exception("Erro no processamento do CSV")

# PÁGINA: VISUALIZAR DADOS
elif selected_option == "Visualizar Dados":
    st.header("📋 Dados Armazenados")
    st.markdown("---")
    
    df = load_data()
    if df is not None:
        with st.expander("Visualização Completa", expanded=True):
            st.dataframe(df, use_container_width=True)
        
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
                st.rerun()

# [...] (Continuação com as outras páginas seguindo o mesmo padrão)

# PÁGINA: OTIMIZAÇÃO LOGÍSTICA
elif selected_option == "Otimização Logística":
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
            labels={'Quantidade': 'Total de Itens', 'ID Cliente': 'Clientes Únicos'},
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
