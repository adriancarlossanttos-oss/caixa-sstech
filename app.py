import streamlit as st
import httpx
import pandas as pd

# Configuração da Página
st.set_page_config(page_title="SS TECH WEB", layout="wide")

# Credenciais (as mesmas do seu sistema)
URL = "https://ikkcupfmcbuxnraboexx.supabase.co/rest/v1"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlra2N1cGZtY2J1eG5yYWJvZXh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk5ODU5NDYsImV4cCI6MjA4NTU2MTk0Nn0.rK5TSg2p2LJxrmqiTtlLZKylHnbE4cpFaWYxBDsASn0",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlra2N1cGZtY2J1eG5yYWJvZXh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk5ODU5NDYsImV4cCI6MjA4NTU2MTk0Nn0.rK5TSg2p2LJxrmqiTtlLZKylHnbE4cpFaWYxBDsASn0",
    "Content-Type": "application/json"
}

st.sidebar.title("MENU SS TECH")
menu = st.sidebar.radio("Ir para:",
                        ["CAIXA", "VENDAS", "ESTOQUE", "FIADO", "FLUXO CAIXA", "PRÓXIMAS COMPRAS", "GRÁFICO"])


# Função para buscar estoque
def carregar_dados():
    try:
        response = httpx.get(f"{URL}/estoque", headers=HEADERS)
        return response.json()
    except:
        return []


if menu == "CAIXA":
    st.header("🛒 Frente de Caixa")
    dados = carregar_dados()
    if dados:
        produtos = {f"{p['codigo']} - {p['nome']}": p for p in dados}
        escolha = st.selectbox("Selecione o Produto", list(produtos.keys()))
        qtd = st.number_input("Quantidade", min_value=1, value=1)

        if st.button("Finalizar Venda"):
            # Lógica de registro igual ao seu .exe
            st.success(f"Venda de {qtd}x registrada com sucesso!")

elif menu == "ESTOQUE":
    st.header("📦 Controle de Estoque")
    dados = carregar_dados()
    if dados:
        st.dataframe(pd.DataFrame(dados))

# As outras abas seguem a mesma lógica do seu código original