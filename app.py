import streamlit as st
import httpx
import pandas as pd

# Configuração visual
st.set_page_config(page_title="SS TECH WEB", layout="wide")

# Suas credenciais do Supabase
URL = "https://ikkcupfmcbuxnraboexx.supabase.co/rest/v1"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlra2N1cGZtY2J1eG5yYWJvZXh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk5ODU5NDYsImV4cCI6MjA4NTU2MTk0Nn0.rK5TSg2p2LJxrmqiTtlLZKylHnbE4cpFaWYxBDsASn0",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlra2N1cGZtY2J1eG5yYWJvZXh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk5ODU5NDYsImV4cCI6MjA4NTU2MTk0Nn0.rK5TSg2p2LJxrmqiTtlLZKylHnbE4cpFaWYxBDsASn0",
    "Content-Type": "application/json"
}


# --- FUNÇÃO PARA BUSCAR DADOS ---
@st.cache_data(ttl=10)  # Atualiza os dados a cada 10 segundos
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

# --- LÓGICA DAS ABAS ---

if menu == "CAIXA":
    st.header("🛒 Frente de Caixa")
    estoque_dados = get_data("estoque")

    if estoque_dados:
        # Criar a lista de seleção
        lista_prods = [f"{p['codigo']} - {p['nome']}" for p in estoque_dados]

        col1, col2 = st.columns(2)
        with col1:
            prod_sel = st.selectbox("Selecione o Produto", lista_prods)
            qtd = st.number_input("Quantidade", min_value=1, value=1, step=1)
            cliente = st.text_input("Nome do Cliente", "CONSUMIDOR")

        with col2:
            metodo = st.selectbox("Pagamento", ["Dinheiro", "Pix", "Cartão"])
            # Buscar preço do item selecionado
            cod_item = prod_sel.split(" - ")[0]
            dados_item = next(p for p in estoque_dados if str(p['codigo']) == cod_item)
            preco_un = dados_item['preco_venda']
            total = preco_un * qtd
            st.write(f"### Total: R$ {total:.2f}")

        if st.button("FINALIZAR VENDA", use_container_width=True):
            # Enviar para o banco (Vendas)
            nova_venda = {
                "cod_item": cod_item, "produto": dados_item['nome'],
                "quantidade": qtd, "total_liq": total, "metodo": metodo, "vendedor": "WEB"
            }
            httpx.post(f"{URL}/vendas", headers=HEADERS, json=nova_venda)

            # Baixar no estoque
            nova_venda_qtd = dados_item['vendas'] + qtd
            httpx.patch(f"{URL}/estoque?codigo=eq.{cod_item}", headers=HEADERS, json={"vendas": nova_venda_qtd})

            st.success("✅ Venda realizada com sucesso!")
            st.rerun()
    else:
        st.error("Não foi possível carregar os produtos. Verifique o banco.")

elif menu == "ESTOQUE":
    st.header("📦 Estoque Atual")
    dados = get_data("estoque")
    if dados:
        df = pd.DataFrame(dados)
        # Reorganizar colunas importantes
        st.dataframe(df[['codigo', 'nome', 'preco_venda', 'qtd_ini', 'vendas']], use_container_width=True)

elif menu == "VENDAS":
    st.header("📋 Relatório de Vendas")
    dados = get_data("vendas")
    if dados:
        st.dataframe(pd.DataFrame(dados), use_container_width=True)

else:
    st.info(f"A aba {menu} está em desenvolvimento.")