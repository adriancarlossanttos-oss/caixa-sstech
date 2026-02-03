import streamlit as st
import httpx
import pandas as pd

# Configuração da Página
st.set_page_config(page_title="SS TECH PRO", layout="wide")

# Credenciais Supabase
URL = "https://ikkcupfmcbuxnraboexx.supabase.co/rest/v1"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlra2N1cGZtY2J1eG5yYWJvZXh4Iiwicm9sZSI6ImFub24iLeveliaXQiOjE3Njk5ODU5NDYsImV4cCI6MjA4NTU2MTk0Nn0.rK5TSg2p2LJxrmqiTtlLZKylHnbE4cpFaWYxBDsASn0",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlra2N1cGZtY2J1eG5yYWJvZXh4Iiwicm9sZSI6ImFub24iLeveliaXQiOjE3Njk5ODU5NDYsImV4cCI6MjA4NTU2MTk0Nn0.rK5TSg2p2LJxrmqiTtlLZKylHnbE4cpFaWYxBDsASn0",
    "Content-Type": "application/json"
}


# --- FUNÇÕES DE BUSCA ---
def buscar(tabela):
    try:
        r = httpx.get(f"{URL}/{tabela}", headers=HEADERS)
        return r.json()
    except:
        return []


# --- MENU LATERAL ---
st.sidebar.title("🚀 SS TECH WEB")
menu = st.sidebar.radio("Navegação:", ["CAIXA", "ESTOQUE", "VENDAS", "FIADO", "FLUXO CAIXA"])

# --- 1. CAIXA ---
if menu == "CAIXA":
    st.header("🛒 Frente de Caixa")
    estoque = buscar("estoque")
    if estoque:
        # CORREÇÃO DA LINHA 37 AQUI:
        prod_nomes = [f"{p['codigo']} - {p['nome']}" for p in estoque]

        col1, col2 = st.columns([2, 1])
        with col1:
            selecionado = st.selectbox("Selecione o Produto", prod_nomes)
            item = next(p for p in estoque if f"{p['codigo']} - {p['nome']}" == selecionado)
            qtd = st.number_input("Quantidade", min_value=1, step=1)
            cliente = st.text_input("Cliente", "CONSUMIDOR")
            metodo = st.selectbox("Pagamento", ["Dinheiro", "Pix", "Cartão", "FIADO"])

        with col2:
            total = float(item['preco_venda']) * qtd
            st.metric("Total", f"R$ {total:.2f}")
            if st.button("FINALIZAR VENDA", use_container_width=True):
                # Enviar Venda
                venda = {"cod_item": item['codigo'], "produto": item['nome'], "quantidade": qtd, "total_liq": total,
                         "cliente": cliente, "metodo": metodo, "vendedor": "WEB"}
                httpx.post(f"{URL}/vendas", headers=HEADERS, json=venda)
                # Baixar Estoque
                httpx.patch(f"{URL}/estoque?codigo=eq.{item['codigo']}", headers=HEADERS,
                            json={"vendas": item['vendas'] + qtd})
                st.success("Venda realizada!")
                st.rerun()

# --- 2. ESTOQUE (CADASTRO E EDIÇÃO) ---
elif menu == "ESTOQUE":
    st.header("📦 Gestão de Estoque")
    dados = buscar("estoque")
    if dados:
        df = pd.DataFrame(dados)
        st.dataframe(df[['codigo', 'nome', 'preco_venda', 'vendas']], use_container_width=True)

        st.divider()
        st.subheader("📝 Cadastrar / Editar Produto")
        c1, c2, c3 = st.columns(3)
        with c1:
            cod = st.text_input("Código")
        with c2:
            nome = st.text_input("Nome do Produto")
        with c3:
            preco = st.number_input("Preço de Venda", min_value=0.0)

        if st.button("SALVAR NO BANCO"):
            payload = {"codigo": cod, "nome": nome, "preco_venda": preco}
            # Tenta atualizar, se não existir, você pode implementar o POST
            httpx.patch(f"{URL}/estoque?codigo=eq.{cod}", headers=HEADERS, json=payload)
            st.success("Produto atualizado!")
            st.rerun()

# --- 3. FIADO ---
elif menu == "FIADO":
    st.header("📝 Contas de Fiado")
    fiados = buscar("fiado")
    if fiados:
        st.table(pd.DataFrame(fiados))

    with st.expander("Registrar Novo Fiado Manual"):
        f_cli = st.text_input("Nome do Devedor")
        f_val = st.number_input("Valor Devido", min_value=0.0)
        if st.button("SALVAR FIADO"):
            httpx.post(f"{URL}/fiado", headers=HEADERS, json={"cliente": f_cli, "valor": f_val, "status": "PENDENTE"})
            st.rerun()

# --- 4. FLUXO CAIXA ---
elif menu == "FLUXO CAIXA":
    st.header("💰 Resumo Financeiro")
    vendas = buscar("vendas")
    if vendas:
        df_v = pd.DataFrame(vendas)
        st.metric("Faturamento Total", f"R$ {df_v['total_liq'].sum():.2f}")
        st.write("### Últimas Vendas")
        st.dataframe(df_v[['produto', 'total_liq', 'metodo', 'cliente']])   