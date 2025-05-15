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
# FUNÇÕES DE PROCESSAMENTO DE DADOS (COM CACHE PARA GRANDES DATASETS)
# =============================================
@st.cache_data(max_entries=1, show_spinner=False)
def processar_dados(df):
    """Processa os dados do CSV para gerar os dataframes necessários"""
    try:
        # Converter coluna de data se existir
        if 'Data' in df.columns:
            df['Data'] = pd.to_datetime(df['Data'])
        
        # Criar dataframe de clientes (agrupado por ID Cliente)
        clientes_df = df.groupby(['ID Cliente', 'Nome do Cliente', 'Cidade']).agg({
            'Preço Total (R$)': 'sum',
            'Data': 'max'
        }).reset_index().rename(columns={
            'Preço Total (R$)': 'Total Gasto',
            'Data': 'Última Compra'
        })
        
        # Criar dataframe de logística (agrupado por Cidade)
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
        st.error(f"Erro ao processar dados: {str(e)}")
        return None, None, None

# =============================================
# FUNÇÕES DE VISUALIZAÇÃO (OTIMIZADAS PARA PERFORMANCE)
# =============================================
def show_clientes(df):
    st.write("## 📋 Dados dos Clientes")
    
    # Filtros para grandes datasets
    with st.expander("🔍 Filtros"):
        col1, col2 = st.columns(2)
        with col1:
            cidades = st.multiselect("Filtrar por cidade", df['Cidade'].unique())
        with col2:
            min_gasto = st.number_input("Gasto mínimo (R$)", min_value=0, value=0)
    
    # Aplicar filtros
    if cidades:
        df_filtrado = df[df['Cidade'].isin(cidades)]
    else:
        df_filtrado = df.copy()
    
    df_filtrado = df_filtrado[df_filtrado['Total Gasto'] >= min_gasto]
    
    # Paginação para melhor performance
    page_size = 10
    page_number = st.number_input("Página", min_value=1, max_value=len(df_filtrado)//page_size + 1, value=1)
    start_idx = (page_number - 1) * page_size
    end_idx = start_idx + page_size
    
    st.dataframe(df_filtrado.sort_values('Total Gasto', ascending=False).iloc[start_idx:end_idx])
    
    # Gráficos otimizados
    col1, col2 = st.columns(2)
    with col1:
        top_clientes = df_filtrado.nlargest(10, 'Total Gasto')
        fig = px.bar(top_clientes, 
                    x='Nome do Cliente', y='Total Gasto',
                    color='Cidade',
                    labels={'Total Gasto': 'Total Gasto (R$)'},
                    title='Top 10 Clientes')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.pie(df_filtrado, names='Cidade', values='Total Gasto',
                    title='Distribuição por Cidade')
        st.plotly_chart(fig, use_container_width=True)

def show_logistica(df):
    st.write("## 🚚 Dados de Logística")
    
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(df, x='Região', y='Total Vendas',
                    color='Região',
                    labels={'Total Vendas': 'Total Vendas (R$)'},
                    title='Vendas por Região')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.pie(df, names='Região', values='Itens Vendidos',
                    title='Distribuição de Itens Vendidos')
        st.plotly_chart(fig, use_container_width=True)
    
    # Mapa otimizado
    st.write("### Mapa de Distribuição")
    try:
        # Coordenadas aproximadas para exemplo (substitua por dados reais)
        coordenadas = {
            'Embu': (-23.65, -46.85),
            'Itapecerica': (-23.72, -46.85),
            'Taboão': (-23.60, -46.78)
        }
        
        df_map = df.copy()
        df_map['lat'] = df_map['Região'].map(lambda x: coordenadas.get(x, (-15, -55))[0]
        df_map['lon'] = df_map['Região'].map(lambda x: coordenadas.get(x, (-15, -55))[1]
        
        st.pydeck_chart(pdk.Deck(
            map_style='mapbox://styles/mapbox/light-v9',
            initial_view_state=pdk.ViewState(
                latitude=-23.5,
                longitude=-46.6,
                zoom=9,
                pitch=50,
            ),
            layers=[
                pdk.Layer(
                    'ColumnLayer',
                    data=df_map,
                    get_position='[lon, lat]',
                    get_elevation='Total Vendas/1000',
                    elevation_scale=50,
                    radius=2000,
                    get_fill_color='[200, 30, 0, 160]',
                    pickable=True,
                    auto_highlight=True,
                ),
            ],
            tooltip={
                'html': '<b>Região:</b> {Região}<br><b>Vendas:</b> R$ {Total Vendas:,.2f}',
                'style': {'color': 'white'}
            }
        ))
    except Exception as e:
        st.warning(f"Não foi possível carregar o mapa: {str(e)}")

# =============================================
# FUNÇÕES DE MANIPULAÇÃO DE DADOS
# =============================================
def show_manipulacao():
    st.title("✏️ Manipulação de Dados")
    
    if not st.session_state.get('dados_carregados', False):
        st.warning("Nenhum dado carregado. Por favor, faça upload de um arquivo CSV.")
        return
    
    raw_df = st.session_state.raw_df
    
    tab1, tab2 = st.tabs(["Editar/Excluir Registros", "Adicionar Novo Registro"])
    
    with tab1:
        st.write("### Buscar e Editar Registros")
        
        # Filtros para encontrar registros
        col1, col2 = st.columns(2)
        with col1:
            cliente_selecionado = st.selectbox(
                "Selecione pelo Nome do Cliente",
                raw_df['Nome do Cliente'].unique()
            )
        with col2:
            item_selecionado = st.selectbox(
                "Selecione pelo Item",
                raw_df['Item'].unique()
            )
        
        # Aplicar filtros
        registros_filtrados = raw_df[
            (raw_df['Nome do Cliente'] == cliente_selecionado) & 
            (raw_df['Item'] == item_selecionado)
        ]
        
        if not registros_filtrados.empty:
            st.write("Registro(s) encontrado(s):")
            edited_row = st.data_editor(registros_filtrados)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Salvar Alterações", key="save_edit"):
                    indices = registros_filtrados.index
                    raw_df.loc[indices] = edited_row.values
                    st.session_state.raw_df = raw_df
                    # Reprocessar dados
                    with st.spinner('Atualizando visualizações...'):
                        st.session_state.clientes_df, st.session_state.logistica_df, _ = processar_dados(raw_df)
                    st.success("Alterações salvas!")
                    st.rerun()
            
            with col2:
                if st.button("🗑️ Excluir Registro(s)", key="delete"):
                    raw_df = raw_df.drop(registros_filtrados.index)
                    st.session_state.raw_df = raw_df
                    # Reprocessar dados
                    with st.spinner('Atualizando visualizações...'):
                        st.session_state.clientes_df, st.session_state.logistica_df, _ = processar_dados(raw_df)
                    st.success("Registro(s) excluído(s)!")
                    st.rerun()
        else:
            st.warning("Nenhum registro encontrado com esses critérios.")
    
    with tab2:
        st.write("### Adicionar Novo Registro")
        with st.form("novo_registro_form"):
            col1, col2 = st.columns(2)
            with col1:
                novo_id = st.number_input("ID Cliente", min_value=1, step=1)
                novo_nome = st.text_input("Nome do Cliente")
                novo_item = st.selectbox("Item", raw_df['Item'].unique())
            with col2:
                nova_data = st.date_input("Data", datetime.now())
                nova_quantidade = st.number_input("Quantidade", min_value=1, step=1, value=1)
                novo_preco = st.number_input("Preço Unitário (R$)", min_value=0.01, value=0.0, step=0.01)
            
            cidade = st.selectbox("Cidade", raw_df['Cidade'].unique())
            
            if st.form_submit_button("➕ Adicionar Registro"):
                novo_registro = {
                    'ID Cliente': novo_id,
                    'Data': nova_data.strftime('%Y-%m-%d'),
                    'Nome do Cliente': novo_nome,
                    'Cidade': cidade,
                    'Item': novo_item,
                    'Quantidade': nova_quantidade,
                    'Preço Unitário (R$)': novo_preco,
                    'Preço Total (R$)': nova_quantidade * novo_preco
                }
                
                # Adicionar novo registro
                raw_df = pd.concat([raw_df, pd.DataFrame([novo_registro])], ignore_index=True)
                st.session_state.raw_df = raw_df
                
                # Reprocessar dados
                with st.spinner('Processando novo registro...'):
                    st.session_state.clientes_df, st.session_state.logistica_df, _ = processar_dados(raw_df)
                
                st.success("Registro adicionado com sucesso!")
                st.rerun()

# =============================================
# FUNÇÃO DE UPLOAD DE DADOS (OTIMIZADA)
# =============================================
def show_upload():
    st.title("📤 Upload de Dados")
    
    uploaded_file = st.file_uploader(
        "Carregue seu arquivo CSV", 
        type="csv",
        help="O arquivo deve conter as colunas: ID Cliente, Data, Nome do Cliente, Cidade, Item, Quantidade, Preço Unitário, Preço Total"
    )
    
    if uploaded_file is not None:
        try:
            with st.spinner('Processando arquivo...'):
                # Ler o arquivo em chunks se for muito grande
                if uploaded_file.size > 10_000_000:  # >10MB
                    chunks = pd.read_csv(uploaded_file, chunksize=10_000)
                    df = pd.concat(chunks)
                else:
                    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
                    df = pd.read_csv(stringio)
                
                # Validar colunas necessárias
                required_columns = ['ID Cliente', 'Nome do Cliente', 'Cidade', 'Item', 'Quantidade', 'Preço Unitário (R$)', 'Preço Total (R$)']
                if not all(col in df.columns for col in required_columns):
                    missing = [col for col in required_columns if col not in df.columns]
                    st.error(f"Colunas obrigatórias faltando: {', '.join(missing)}")
                    return
                
                # Mostrar pré-visualização
                st.success("Arquivo carregado com sucesso!")
                st.write("### Pré-visualização (5 primeiras linhas)")
                st.dataframe(df.head())
                
                # Processar dados
                with st.spinner('Gerando visualizações...'):
                    clientes_df, logistica_df, processed_df = processar_dados(df)
                
                if clientes_df is not None:
                    # Armazenar dados na sessão
                    st.session_state.raw_df = processed_df
                    st.session_state.clientes_df = clientes_df
                    st.session_state.logistica_df = logistica_df
                    st.session_state.dados_carregados = True
                    
                    st.success("Dados processados com sucesso! Navegue pelas outras abas para visualização.")
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {str(e)}")

# =============================================
# FUNÇÕES DE AUTENTICAÇÃO
# =============================================
def login_page():
    st.title("🔒 Login - Painel E-Shop Brasil")
    
    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        
        if st.form_submit_button("Acessar"):
            if (username == "adminfecaf" and 
                hashlib.sha256(password.encode()).hexdigest() == hashlib.sha256("fecafadbd".encode()).hexdigest()):
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Credenciais inválidas!")
    
    st.stop()

# =============================================
# VERIFICAÇÃO DE LOGIN E INICIALIZAÇÃO
# =============================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.dados_carregados = False

if not st.session_state.logged_in:
    login_page()

# =============================================
# APLICAÇÃO PRINCIPAL
# =============================================
# Menu lateral
with st.sidebar:
    st.title("Menu")
    selected = st.selectbox(
        "Opções", 
        ["Dashboard", "Clientes", "Logística", "Upload de Dados", "Manipular Dados"]
    )
    
    if st.session_state.get('dados_carregados', False):
        st.info(f"Dados carregados: {len(st.session_state.raw_df):,} registros")
    
    if st.button("🚪 Sair"):
        st.session_state.logged_in = False
        st.session_state.dados_carregados = False
        st.rerun()

# Conteúdo principal
if selected == "Dashboard":
    st.title("📊 Dashboard Geral")
    
    if not st.session_state.get('dados_carregados', False):
        st.warning("Nenhum dado carregado. Por favor, faça upload de um arquivo CSV.")
    else:
        clientes_df = st.session_state.clientes_df
        logistica_df = st.session_state.logistica_df
        
        # Métricas principais
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Clientes", f"{len(clientes_df):,}")
            st.metric("Média por Cliente", f"R$ {clientes_df['Total Gasto'].mean():,.2f}")
        
        with col2:
            st.metric("Faturamento Total", f"R$ {clientes_df['Total Gasto'].sum():,.2f}")
            st.metric("Cliente Top", f"{clientes_df.loc[clientes_df['Total Gasto'].idxmax(), 'Nome do Cliente']}")
        
        with col3:
            st.metric("Cidades Atendidas", len(logistica_df))
            st.metric("Cidade Top", f"{logistica_df.loc[logistica_df['Total Vendas'].idxmax(), 'Região']}")
        
        # Gráfico rápido de evolução temporal (se houver dados de data)
        if 'Data' in st.session_state.raw_df.columns:
            st.write("### Evolução Temporal de Vendas")
            vendas_por_data = st.session_state.raw_df.groupby(pd.to_datetime(st.session_state.raw_df['Data']).dt.date)['Preço Total (R$)'].sum().reset_index()
            fig = px.line(vendas_por_data, x='Data', y='Preço Total (R$)',
                         title='Vendas ao Longo do Tempo',
                         labels={'Preço Total (R$)': 'Total de Vendas (R$)'})
            st.plotly_chart(fig, use_container_width=True)

elif selected == "Clientes":
    if not st.session_state.get('dados_carregados', False):
        st.warning("Nenhum dado carregado. Por favor, faça upload de um arquivo CSV.")
    else:
        show_clientes(st.session_state.clientes_df)

elif selected == "Logística":
    if not st.session_state.get('dados_carregados', False):
        st.warning("Nenhum dado carregado. Por favor, faça upload de um arquivo CSV.")
    else:
        show_logistica(st.session_state.logistica_df)

elif selected == "Upload de Dados":
    show_upload()

elif selected == "Manipular Dados":
    show_manipulacao()
