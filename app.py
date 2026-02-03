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


# Função de busca sem Cache agressivo para ver os dados na hora
def get_data(table):
    try:
        r = httpx.get(f"{URL}/{table}", headers=HEADERS)
        return r.json()
    except:
        return []


# Menu Lateral
st.sidebar.title("MENU SS TECH")
menu = st.sidebar.radio("Ir para:",
                        ["CAIXA", "VENDAS", "ESTOQUE", "FIADO", "FLUXO CAIXA", "PRÓXIMAS COMPRAS", "GRÁFICO"])

# --- 1. CAIXA ---
if menu == "CAIXA":
    st.header("🛒 Frente de Caixa")
    estoque_dados = get_data("estoque")
    if estoque_dados:
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
            # Enviar Venda (Garante os mesmos nomes de coluna que o seu banco usa)
            nova_venda = {
                "cod_item": cod_item,
                "produto": dados_item['nome'],
                "quantidade": qtd,
                "total_liq": total,
                "metodo": metodo,
                "vendedor": "WEB"
            }
            httpx.post(f"{URL}/vendas", headers=HEADERS, json=nova_venda)

            # Baixar no estoque
            vendas_atuais = int(dados_item.get('vendas', 0) or 0)
            httpx.patch(f"{URL}/estoque?codigo=eq.{cod_item}", headers=HEADERS, json={"vendas": vendas_atuais + qtd})

            if metodo == "FIADO":
                httpx.post(f"{URL}/fiado", headers=HEADERS, json={"cliente": cliente, "valor": total})

            st.success("✅ Venda realizada!")
            st.rerun()

# --- 2. VENDAS (MOSTRAR TUDO) ---
elif menu == "VENDAS":
    st.header("📋 Relatório de Vendas")
    dados = get_data("vendas")
    if dados:
        df = pd.DataFrame(dados)
        st.dataframe(df, use_container_width=True)  # Mostra todas as colunas existentes no banco
    else:
        st.info("Nenhuma venda encontrada no banco de dados.")

# --- 3. ESTOQUE ---
elif menu == "ESTOQUE":
    st.header("📦 Estoque Atual")
    dados = get_data("estoque")
    if dados:
        df = pd.DataFrame(dados)
        if 'qtd_ini' in df.columns:
            df['Disponível'] = df['qtd_ini'].fillna(0) + df.get('compras', 0).fillna(0) - df.get('vendas', 0).fillna(0)
        st.dataframe(df, use_container_width=True)

# --- 4. FIADO ---
elif menu == "FIADO":
    st.header("📝 Clientes em Aberto")
    dados = get_data("fiado")
    if dados:
        st.dataframe(pd.DataFrame(dados), use_container_width=True)

# --- 5. FLUXO CAIXA ---
elif menu == "FLUXO CAIXA":
    st.header("💰 Fluxo Financeiro")
    vendas = get_data("vendas")
    if vendas:
        df = pd.DataFrame(vendas)
        # Tenta encontrar a coluna de valor independente do nome
        col_valor = 'total_liq' if 'total_liq' in df.columns else 'total'
        if col_valor in df.columns:
            df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)
            st.metric("Total Vendido (R$)", f"{df[col_valor].sum():.2f}")
            st.write("Faturamento por Método:")
            st.bar_chart(df.groupby('metodo')[col_valor].sum())

# --- 6. PRÓXIMAS COMPRAS ---
elif menu == "PRÓXIMAS COMPRAS":
    st.header("🛒 Necessidade de Reposição")
    estoque = get_data("estoque")
    if estoque:
        df = pd.DataFrame(estoque)
        df['Disponível'] = df.get('qtd_ini', 0).fillna(0) + df.get('compras', 0).fillna(0) - df.get('vendas', 0).fillna(
            0)
        baixo = df[df['Disponível'] <= 3]
        st.table(baixo[['codigo', 'nome', 'Disponível']])

# --- 7. GRÁFICO ---
elif menu == "GRÁFICO":
    st.header("📊 Desempenho")
    vendas = get_data("vendas")
    if vendas:
        df = pd.DataFrame(vendas)
        col_valor = 'total_liq' if 'total_liq' in df.columns else 'total'
        if col_valor in df.columns:
            df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)
            st.bar_chart(df.groupby('produto')[col_valor].sum())