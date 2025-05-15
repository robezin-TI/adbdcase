import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
import hashlib
from io import StringIO
from datetime import datetime

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
# FUNÇÕES DE PROCESSAMENTO (OTIMIZADAS)
# =============================================
@st.cache_data(max_entries=1, show_spinner=False)
def processar_dados(df):
    """Processa dados do CSV com tratamento de erros"""
    try:
        if 'Data' in df.columns:
            df['Data'] = pd.to_datetime(df['Data'])
        
        clientes_df = df.groupby(['ID Cliente', 'Nome do Cliente', 'Cidade']).agg({
            'Preço Total (R$)': 'sum',
            'Data': 'max'
        }).reset_index().rename(columns={
            'Preço Total (R$)': 'Total Gasto',
            'Data': 'Última Compra'
        })
        
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
        
        return clientes_df, logistica_df, df.copy()
    except Exception as e:
        st.error(f"Erro no processamento: {str(e)}")
        return None, None, None

# =============================================
# FUNÇÕES DE VISUALIZAÇÃO
# =============================================
def show_clientes(df):
    """Exibe dashboard de clientes com filtros"""
    st.write("## 📋 Dados dos Clientes")
    
    with st.expander("🔍 Filtros", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            cidades = st.multiselect("Selecione cidades", df['Cidade'].unique())
        with col2:
            min_gasto = st.number_input("Gasto mínimo (R$)", min_value=0, value=0)
    
    df_filtrado = df[df['Total Gasto'] >= min_gasto]
    if cidades:
        df_filtrado = df_filtrado[df_filtrado['Cidade'].isin(cidades)]
    
    # Paginação
    page_size = 10
    page_number = st.number_input("Página", min_value=1, 
                                max_value=max(1, len(df_filtrado)//page_size + 1), 
                                value=1)
    start_idx = (page_number - 1) * page_size
    
    st.dataframe(df_filtrado.sort_values('Total Gasto', ascending=False)
                .iloc[start_idx:start_idx+page_size])
    
    # Gráficos
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(df_filtrado.nlargest(10, 'Total Gasto'),
                    x='Nome do Cliente', y='Total Gasto',
                    color='Cidade', title='Top 10 Clientes')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.pie(df_filtrado, names='Cidade', values='Total Gasto',
                    title='Distribuição por Cidade')
        st.plotly_chart(fig, use_container_width=True)

def show_logistica(df):
    """Exibe dashboard de logística com mapa"""
    st.write("## 🚚 Dados de Logística")
    
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(df, x='Região', y='Total Vendas',
                    color='Região', title='Vendas por Região')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.pie(df, names='Região', values='Itens Vendidos',
                    title='Itens Vendidos por Região')
        st.plotly_chart(fig, use_container_width=True)
    
    # Mapa interativo
    st.write("### 🌍 Mapa de Distribuição")
    try:
        coordenadas = {
            'Embu': (-23.65, -46.85),
            'Itapecerica': (-23.72, -46.85),
            'Taboão': (-23.60, -46.78)
        }
        
        df_map = df.copy()
        df_map['lat'] = df_map['Região'].map(lambda x: coordenadas.get(x, (-15, -55))[0])
        df_map['lon'] = df_map['Região'].map(lambda x: coordenadas.get(x, (-15, -55))[1])
        
        st.pydeck_chart(pdk.Deck(
            map_style='mapbox://styles/mapbox/light-v9',
            initial_view_state=pdk.ViewState(
                latitude=-23.5,
                longitude=-46.6,
                zoom=9,
                pitch=50,
            ),
            layers=[pdk.Layer(
                'ColumnLayer',
                data=df_map,
                get_position='[lon, lat]',
                get_elevation='Total Vendas/1000',
                elevation_scale=50,
                radius=2000,
                get_fill_color='[200, 30, 0, 160]',
                pickable=True
            )],
            tooltip={
                'html': '<b>Região:</b> {Região}<br><b>Vendas:</b> R$ {Total Vendas:,.2f}',
                'style': {'color': 'white'}
            }
        ))
    except Exception as e:
        st.warning(f"Mapa não disponível: {str(e)}")

# =============================================
# FUNÇÕES DE MANIPULAÇÃO DE DADOS
# =============================================
def show_manipulacao():
    """Interface para edição de registros"""
    st.title("✏️ Manipulação de Dados")
    
    if not st.session_state.get('dados_carregados', False):
        st.warning("Carregue dados na aba Upload")
        return
    
    raw_df = st.session_state.raw_df
    tab1, tab2 = st.tabs(["Editar/Excluir", "Adicionar Novo"])
    
    with tab1:
        st.write("### Busca de Registros")
        col1, col2 = st.columns(2)
        with col1:
            cliente = st.selectbox("Cliente", raw_df['Nome do Cliente'].unique())
        with col2:
            item = st.selectbox("Item", raw_df['Item'].unique())
        
        registros = raw_df[(raw_df['Nome do Cliente'] == cliente) & 
                          (raw_df['Item'] == item)]
        
        if not registros.empty:
            edited = st.data_editor(registros)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Salvar Alterações"):
                    raw_df.loc[registros.index] = edited.values
                    st.session_state.raw_df = raw_df
                    update_dados()
                    st.success("Dados atualizados!")
            with col2:
                if st.button("🗑️ Excluir"):
                    raw_df = raw_df.drop(registros.index)
                    st.session_state.raw_df = raw_df
                    update_dados()
                    st.success("Registros excluídos!")
        else:
            st.warning("Nenhum registro encontrado")
    
    with tab2:
        with st.form("novo_registro"):
            st.write("### Novo Registro")
            col1, col2 = st.columns(2)
            with col1:
                novo_id = st.number_input("ID Cliente", min_value=1)
                nome = st.text_input("Nome do Cliente")
                item = st.selectbox("Item", raw_df['Item'].unique())
            with col2:
                data = st.date_input("Data")
                qtd = st.number_input("Quantidade", min_value=1)
                preco = st.number_input("Preço Unitário", min_value=0.01)
            
            cidade = st.selectbox("Cidade", raw_df['Cidade'].unique())
            
            if st.form_submit_button("Adicionar"):
                novo = {
                    'ID Cliente': novo_id,
                    'Data': data.strftime('%Y-%m-%d'),
                    'Nome do Cliente': nome,
                    'Cidade': cidade,
                    'Item': item,
                    'Quantidade': qtd,
                    'Preço Unitário (R$)': preco,
                    'Preço Total (R$)': qtd * preco
                }
                raw_df = pd.concat([raw_df, pd.DataFrame([novo])], ignore_index=True)
                st.session_state.raw_df = raw_df
                update_dados()
                st.success("Registro adicionado!")

def update_dados():
    """Atualiza os dados processados"""
    with st.spinner("Atualizando..."):
        clientes, logistica, _ = processar_dados(st.session_state.raw_df)
        st.session_state.clientes_df = clientes
        st.session_state.logistica_df = logistica

# =============================================
# FUNÇÃO DE UPLOAD
# =============================================
def show_upload():
    """Interface de upload de arquivos"""
    st.title("📤 Upload de Dados")
    
    file = st.file_uploader("Selecione o arquivo CSV", type="csv")
    if file:
        try:
            with st.spinner("Processando..."):
                # Leitura otimizada para grandes arquivos
                if file.size > 10_000_000:  # >10MB
                    chunks = pd.read_csv(file, chunksize=10_000)
                    df = pd.concat(chunks)
                else:
                    df = pd.read_csv(StringIO(file.getvalue().decode('utf-8')))
                
                # Validação das colunas
                required = ['ID Cliente', 'Nome do Cliente', 'Cidade', 
                          'Item', 'Quantidade', 'Preço Unitário (R$)', 
                          'Preço Total (R$)']
                if not all(col in df.columns for col in required):
                    missing = [col for col in required if col not in df.columns]
                    st.error(f"Colunas faltando: {', '.join(missing)}")
                    return
                
                st.session_state.raw_df = df
                update_dados()
                st.session_state.dados_carregados = True
                st.success("Dados carregados com sucesso!")
                
                st.write("### Visualização Rápida")
                st.dataframe(df.head())
        except Exception as e:
            st.error(f"Erro: {str(e)}")

# =============================================
# AUTENTICAÇÃO
# =============================================
def login():
    """Tela de login"""
    st.title("🔒 Login E-Shop")
    with st.form("login"):
        user = st.text_input("Usuário")
        pwd = st.text_input("Senha", type="password")
        
        if st.form_submit_button("Entrar"):
            if (user == "adminfecaf" and 
                hashlib.sha256(pwd.encode()).hexdigest() == 
                hashlib.sha256("fecafadbd".encode()).hexdigest()):
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Credenciais inválidas")
    st.stop()

# =============================================
# INICIALIZAÇÃO
# =============================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.dados_carregados = False

if not st.session_state.logged_in:
    login()

# =============================================
# MENU PRINCIPAL
# =============================================
with st.sidebar:
    st.title("Navegação")
    pagina = st.selectbox(
        "Selecione",
        ["Dashboard", "Clientes", "Logística", "Upload", "Manipulação"]
    )
    
    if st.session_state.dados_carregados:
        st.info(f"📊 {len(st.session_state.raw_df):,} registros carregados")
    
    if st.button("Sair"):
        st.session_state.clear()
        st.rerun()

# =============================================
# ROTEAMENTO
# =============================================
if pagina == "Dashboard":
    st.title("📊 Dashboard")
    if st.session_state.dados_carregados:
        df = st.session_state.clientes_df
        st.metric("Total Clientes", len(df))
        st.metric("Faturamento", f"R$ {df['Total Gasto'].sum():,.2f}")
        
        fig = px.line(
            st.session_state.raw_df.groupby(
                pd.to_datetime(st.session_state.raw_df['Data']).dt.date
            )['Preço Total (R$)'].sum().reset_index(),
            x='Data', y='Preço Total (R$)',
            title="Vendas ao Longo do Tempo"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Carregue dados primeiro")

elif pagina == "Clientes":
    if st.session_state.dados_carregados:
        show_clientes(st.session_state.clientes_df)
    else:
        st.warning("Carregue dados primeiro")

elif pagina == "Logística":
    if st.session_state.dados_carregados:
        show_logistica(st.session_state.logistica_df)
    else:
        st.warning("Carregue dados primeiro")

elif pagina == "Upload":
    show_upload()

elif pagina == "Manipulação":
    show_manipulacao()
