import streamlit as st
import httpx
import pandas as pd

# Configuração visual
st.set_page_config(page_title="SS TECH WEB", layout="wide")

# Credenciais
URL = "https://ikkcupfmcbuxnraboexx.supabase.co/rest/v1"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlra2N1cGZtY2J1eG5yYWJvZXh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk5ODU5NDYsImV4cCI6MjA4NTU2MTk0Nn0.rK5TSg2p2LJxrmqiTtlLZKylHnbE4cpFaWYxBDsASn0",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlra2N1cGZtY2J1eG5yYWJvZXh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk5ODU5NDYsImV4cCI6MjA4NTU2MTk0Nn0.rK5TSg2p2LJxrmqiTtlLZKylHnbE4cpFaWYxBDsASn0",
    "Content-Type": "application/json"
}


# Função de busca que você já testou e deu certo
@st.cache_data(ttl=5)
def get_data(table):
    try:
        r = httpx.get(f"{URL}/{table}", headers=HEADERS)
        return r.json()
    except:
        return []


# Menu Lateral (conforme você pediu)
st.sidebar.title("MENU SS TECH")
menu = st.sidebar.radio("Ir para:",
                        ["CAIXA", "VENDAS", "ESTOQUE", "FIADO", "FLUXO CAIXA", "PRÓXIMAS COMPRAS", "GRÁFICO"])

# --- ABA CAIXA ---
if menu == "CAIXA":
    st.header("🛒 Frente de Caixa")
    estoque_dados = get_data("estoque")
    if estoque_dados:
        # Filtra apenas itens que tenham código e nome para não dar erro
        lista_prods = [f"{p['codigo']} - {p['nome']}" for p in estoque_dados if 'codigo' in p and 'nome' in p]

        col1, col2 = st.columns(2)
        with col1:
            prod_sel = st.selectbox("Selecione o Produto", lista_prods)
            qtd = st.number_input("Quantidade", min_value=1, value=1, step=1)
            cliente = st.text_input("Nome do Cliente", "CONSUMIDOR")
            metodo = st.selectbox("Pagamento", ["Dinheiro", "Pix", "Cartão", "FIADO"])

        with col2:
            cod_item = prod_sel.split(" - ")[0]
            dados_item = next(p for p in estoque_dados if str(p['codigo']) == cod_item)
            preco_un = float(dados_item.get('preco_venda', 0))
            total = preco_un * qtd
            st.write(f"### Total: R$ {total:.2f}")

        if st.button("FINALIZAR VENDA", use_container_width=True):
            # 1. Registra Venda
            nova_venda = {"cod_item": cod_item, "produto": dados_item['nome'], "quantidade": qtd, "total_liq": total,
                          "metodo": metodo, "vendedor": "WEB"}
            httpx.post(f"{URL}/vendas", headers=HEADERS, json=nova_venda)
            # 2. Baixa Estoque
            nova_venda_qtd = int(dados_item.get('vendas', 0)) + qtd
            httpx.patch(f"{URL}/estoque?codigo=eq.{cod_item}", headers=HEADERS, json={"vendas": nova_venda_qtd})
            # 3. Se for FIADO
            if metodo == "FIADO":
                httpx.post(f"{URL}/fiado", headers=HEADERS,
                           json={"cliente": cliente, "valor": total, "status": "PENDENTE"})

            st.success("✅ Venda realizada!")
            st.rerun()

# --- ABA VENDAS ---
elif menu == "VENDAS":
    st.header("📋 Relatório de Vendas")
    dados = get_data("vendas")
    if dados:
        st.dataframe(pd.DataFrame(dados), use_container_width=True)

# --- ABA ESTOQUE ---
elif menu == "ESTOQUE":
    st.header("📦 Estoque Atual")
    dados = get_data("estoque")
    if dados:
        df = pd.DataFrame(dados)
        # Cálculo de quantidade disponível
        if 'qtd_ini' in df.columns and 'vendas' in df.columns:
            df['Disponível'] = df['qtd_ini'].fillna(0) + df.get('compras', 0) - df['vendas'].fillna(0)
        st.dataframe(df, use_container_width=True)

# --- ABA FIADO ---
elif menu == "FIADO":
    st.header("📝 Clientes em Aberto")
    dados = get_data("fiado")
    if dados:
        st.table(pd.DataFrame(dados))
    else:
        st.info("Nenhum fiado encontrado.")

# --- ABA FLUXO CAIXA ---
elif menu == "FLUXO CAIXA":
    st.header("💰 Fluxo Financeiro")
    vendas = get_data("vendas")
    if vendas:
        df = pd.DataFrame(vendas)
        st.metric("Total Vendido (R$)", f"{df['total_liq'].sum():.2f}")
        st.write("Resumo por método:")
        st.bar_chart(df.groupby('metodo')['total_liq'].sum())

# --- ABA PRÓXIMAS COMPRAS ---
elif menu == "PRÓXIMAS COMPRAS":
    st.header("🛒 Necessidade de Reposição")
    estoque = get_data("estoque")
    if estoque:
        df = pd.DataFrame(estoque)
        df['Disponível'] = df['qtd_ini'].fillna(0) + df.get('compras', 0) - df['vendas'].fillna(0)
        baixo = df[df['Disponível'] <= 3]
        st.warning("Itens com menos de 3 unidades:")
        st.table(baixo[['codigo', 'nome', 'Disponível']])

# --- ABA GRÁFICO ---
elif menu == "GRÁFICO":
    st.header("📊 Desempenho")
    vendas = get_data("vendas")
    if vendas:
        df = pd.DataFrame(vendas)
        st.line_chart(df.groupby('produto')['total_liq'].sum())