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
# FUNÇÕES AUXILIARES
# =============================================
@st.cache_data(max_entries=1, show_spinner=False)
def processar_dados(df):
    """Processa os dados para gerar visualizações"""
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
        
        return clientes_df, logistica_df
        
    except Exception as e:
        st.error(f"Erro no processamento: {str(e)}")
        return None, None

def validar_dados(df):
    """Valida a estrutura do DataFrame"""
    required_columns = ['ID Cliente', 'Nome do Cliente', 'Cidade', 
                      'Item', 'Quantidade', 'Preço Unitário (R$)', 
                      'Preço Total (R$)']
    return all(col in df.columns for col in required_columns)

# =============================================
# FUNÇÕES PRINCIPAIS
# =============================================
def show_visualizacao():
    if not st.session_state.get('dados_carregados', False):
        st.warning("Carregue dados primeiro na aba Upload de Dados")
        return
    
    st.title("🔍 Visualização Completa dos Dados")
    df = st.session_state.raw_df
    
    # Ordenar por data (mais recente primeiro)
    if 'Data' in df.columns:
        df = df.sort_values('Data', ascending=False)
    
    # Visão geral estatística
    with st.expander("📊 Estatísticas Gerais", expanded=True):
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Registros", len(df))
        col2.metric("Período Coberto", 
                   f"{df['Data'].min().strftime('%d/%m/%Y') if 'Data' in df.columns else 'N/A'} - "
                   f"{df['Data'].max().strftime('%d/%m/%Y') if 'Data' in df.columns else 'N/A'}")
        col3.metric("Valor Total", f"R$ {df['Preço Total (R$)'].sum():,.2f}")
    
    # Filtros interativos
    with st.expander("🔍 Filtros Avançados", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            clientes = st.multiselect("Clientes", df['Nome do Cliente'].unique())
        with col2:
            cidades = st.multiselect("Cidades", df['Cidade'].unique())
        with col3:
            itens = st.multiselect("Itens", df['Item'].unique())
        
        # Aplicar filtros
        if clientes:
            df = df[df['Nome do Cliente'].isin(clientes)]
        if cidades:
            df = df[df['Cidade'].isin(cidades)]
        if itens:
            df = df[df['Item'].isin(itens)]
    
    # Visualização tabular
    st.write(f"### 📋 Registros ({len(df)})")
    
    # Configuração de colunas para exibição
    cols_to_show = [
        'Data', 'Nome do Cliente', 'Cidade', 'Item', 
        'Quantidade', 'Preço Unitário (R$)', 'Preço Total (R$)'
    ]
    available_cols = [col for col in cols_to_show if col in df.columns]
    
    # Paginação
    page_size = st.selectbox("Registros por página", [10, 25, 50, 100], index=1)
    total_pages = max(1, (len(df) // page_size) + 1)
    page = st.number_input("Página", min_value=1, max_value=total_pages, value=1)
    start_idx = (page - 1) * page_size
    
    st.dataframe(
        df[available_cols].iloc[start_idx:start_idx + page_size],
        column_config={
            'Data': st.column_config.DateColumn(format="DD/MM/YYYY"),
            'Preço Unitário (R$)': st.column_config.NumberColumn(format="R$ %.2f"),
            'Preço Total (R$)': st.column_config.NumberColumn(format="R$ %.2f")
        },
        use_container_width=True,
        height=500
    )
    
    # Resumo por cliente
    st.write("### 🧑‍💼 Resumo por Cliente")
    resumo = df.groupby('Nome do Cliente').agg({
        'Preço Total (R$)': 'sum',
        'Data': 'max',
        'Item': 'count'
    }).rename(columns={
        'Preço Total (R$)': 'Total Gasto',
        'Data': 'Última Compra',
        'Item': 'Itens Comprados'
    }).sort_values('Total Gasto', ascending=False)
    
    st.dataframe(
        resumo,
        column_config={
            'Total Gasto': st.column_config.NumberColumn(format="R$ %.2f"),
            'Última Compra': st.column_config.DateColumn(format="DD/MM/YYYY")
        }
    )

def show_upload():
    st.title("📤 Upload de Dados")
    
    modo = st.radio(
        "Modo de carregamento:",
        ["Combinar múltiplos arquivos", "Acumular dados"],
        horizontal=True
    )
    
    if modo == "Combinar múltiplos arquivos":
        files = st.file_uploader(
            "Selecione os arquivos CSV", 
            type="csv",
            accept_multiple_files=True
        )
        
        if files:
            try:
                dfs = []
                with st.spinner(f'Processando {len(files)} arquivos...'):
                    for file in files:
                        if file.size > 10_000_000:
                            chunks = pd.read_csv(file, chunksize=10_000)
                            df = pd.concat(chunks)
                        else:
                            df = pd.read_csv(StringIO(file.getvalue().decode('utf-8')))
                        
                        if not validar_dados(df):
                            st.error(f"Arquivo {file.name} não possui a estrutura requerida")
                            return
                        
                        dfs.append(df)
                
                combined_df = pd.concat(dfs, ignore_index=True)
                st.session_state.raw_df = combined_df
                st.session_state.clientes_df, st.session_state.logistica_df = processar_dados(combined_df)
                st.session_state.dados_carregados = True
                
                st.success(f"✅ {len(files)} arquivos combinados | Total: {len(combined_df):,} registros")
                
            except Exception as e:
                st.error(f"Erro: {str(e)}")
    
    else:  # Modo acumulativo
        file = st.file_uploader("Selecione um arquivo CSV", type="csv")
        
        if file:
            try:
                if file.size > 10_000_000:
                    chunks = pd.read_csv(file, chunksize=10_000)
                    new_df = pd.concat(chunks)
                else:
                    new_df = pd.read_csv(StringIO(file.getvalue().decode('utf-8')))
                
                if not validar_dados(new_df):
                    st.error("O arquivo não possui a estrutura requerida")
                    return
                
                if 'raw_df' in st.session_state:
                    combined_df = pd.concat([st.session_state.raw_df, new_df], ignore_index=True)
                    st.session_state.raw_df = combined_df
                    st.success(f"✅ Arquivo adicionado | Total: {len(combined_df):,} registros")
                else:
                    st.session_state.raw_df = new_df
                    st.success("✅ Primeiro arquivo carregado")
                
                st.session_state.clientes_df, st.session_state.logistica_df = processar_dados(st.session_state.raw_df)
                st.session_state.dados_carregados = True
                
            except Exception as e:
                st.error(f"Erro: {str(e)}")
    
    if st.session_state.get('dados_carregados', False):
        st.divider()
        if st.button("🧹 Limpar todos os dados"):
            st.session_state.clear()
            st.rerun()

def show_clientes():
    if not st.session_state.get('dados_carregados', False):
        st.warning("Carregue dados primeiro")
        return
    
    st.title("👥 Análise de Clientes")
    df = st.session_state.clientes_df
    
    with st.expander("🔍 Filtros", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            cidades = st.multiselect(
                "Cidades", 
                df['Cidade'].unique(),
                default=df['Cidade'].unique()[:3]
            )
        with col2:
            min_gasto = st.number_input("Gasto mínimo (R$)", min_value=0, value=0)
    
    filtered_df = df[
        (df['Cidade'].isin(cidades)) & 
        (df['Total Gasto'] >= min_gasto)
    ].sort_values('Total Gasto', ascending=False)
    
    page_size = 10
    page = st.number_input(
        "Página", 
        min_value=1, 
        max_value=max(1, len(filtered_df)//page_size + 1),
        value=1
    )
    start_idx = (page-1)*page_size
    
    st.dataframe(filtered_df.iloc[start_idx:start_idx+page_size])
    
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(
            filtered_df.nlargest(10, 'Total Gasto'),
            x='Nome do Cliente',
            y='Total Gasto',
            color='Cidade',
            title='Top 10 Clientes'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.pie(
            filtered_df,
            names='Cidade',
            values='Total Gasto',
            title='Distribuição por Cidade'
        )
        st.plotly_chart(fig, use_container_width=True)

def show_logistica():
    if not st.session_state.get('dados_carregados', False):
        st.warning("Carregue dados primeiro")
        return
    
    st.title("🚚 Logística e Distribuição")
    df = st.session_state.logistica_df
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Vendas", f"R$ {df['Total Vendas'].sum():,.2f}")
    col2.metric("Itens Vendidos", f"{df['Itens Vendidos'].sum():,}")
    col3.metric("Cidades", len(df))
    
    tab1, tab2 = st.tabs(["Vendas", "Mapa"])
    
    with tab1:
        fig = px.bar(
            df,
            x='Região',
            y='Total Vendas',
            color='Região',
            title='Vendas por Região'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
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
            st.warning(f"Não foi possível carregar o mapa: {str(e)}")

def show_dashboard():
    st.title("📊 Dashboard Geral")
    
    if not st.session_state.get('dados_carregados', False):
        st.warning("Carregue dados primeiro")
        return
    
    raw_df = st.session_state.raw_df
    clientes_df = st.session_state.clientes_df
    logistica_df = st.session_state.logistica_df
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Clientes", len(clientes_df))
    col2.metric("Faturamento Total", f"R$ {clientes_df['Total Gasto'].sum():,.2f}")
    col3.metric("Cidades Atendidas", len(logistica_df))
    
    if 'Data' in raw_df.columns:
        st.subheader("📈 Evolução Temporal")
        vendas_por_data = raw_df.groupby(raw_df['Data'].dt.to_period('M'))['Preço Total (R$)'].sum().reset_index()
        vendas_por_data['Data'] = vendas_por_data['Data'].dt.to_timestamp()
        
        fig = px.line(
            vendas_por_data,
            x='Data',
            y='Preço Total (R$)',
            title='Vendas Mensais',
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)

def login():
    st.title("🔒 Login - Painel E-Shop")
    
    with st.form("login_form"):
        user = st.text_input("Usuário")
        pwd = st.text_input("Senha", type="password")
        
        if st.form_submit_button("Acessar"):
            if (user == "adminfecaf" and 
                hashlib.sha256(pwd.encode()).hexdigest() == 
                hashlib.sha256("fecafadbd".encode()).hexdigest()):
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Credenciais inválidas")
    st.stop()

# =============================================
# CONFIGURAÇÃO DE ESTADO E ROTEAMENTO
# =============================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()

# Menu lateral
with st.sidebar:
    st.title("Navegação")
    pagina = st.selectbox(
        "Selecione a página",
        ["Dashboard", "Visualização", "Clientes", "Logística", "Upload de Dados"]
    )
    
    if st.session_state.get('dados_carregados', False):
        st.info(f"📁 Dados carregados: {len(st.session_state.raw_df):,} registros")
    
    if st.button("🚪 Sair"):
        st.session_state.clear()
        st.rerun()

# Roteamento
if pagina == "Dashboard":
    show_dashboard()
elif pagina == "Visualização":
    show_visualizacao()
elif pagina == "Clientes":
    show_clientes()
elif pagina == "Logística":
    show_logistica()
elif pagina == "Upload de Dados":
    show_upload()
