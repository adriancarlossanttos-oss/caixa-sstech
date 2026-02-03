import streamlit as st
import httpx
import pandas as pd
from datetime import datetime

# Configuração da Página para ocupar a tela toda
st.set_page_config(page_title="SS TECH PRO WEB", layout="wide", initial_sidebar_state="expanded")

# Credenciais Supabase
URL = "https://ikkcupfmcbuxnraboexx.supabase.co/rest/v1"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlra2N1cGZtY2J1eG5yYWJvZXh4Iiwicm9sZSI6ImFub24iLeveliaXQiOjE3Njk5ODU5NDYsImV4cCI6MjA4NTU2MTk0Nn0.rK5TSg2p2LJxrmqiTtlLZKylHnbE4cpFaWYxBDsASn0",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlra2N1cGZtY2J1eG5yYWJvZXh4Iiwicm9sZSI6ImFub24iLeveliaXQiOjE3Njk5ODU5NDYsImV4cCI6MjA4NTU2MTk0Nn0.rK5TSg2p2LJxrmqiTtlLZKylHnbE4cpFaWYxBDsASn0",
    "Content-Type": "application/json"
}


# --- FUNÇÕES DE COMUNICAÇÃO ---
def buscar_dados(tabela):
    try:
        response = httpx.get(f"{URL}/{tabela}", headers=HEADERS)
        return response.json()
    except:
        return []


# --- INTERFACE LATERAL ---
st.sidebar.title("🚀 SS TECH SISTEMAS")
menu = st.sidebar.radio("Navegação:",
                        ["CAIXA", "VENDAS", "ESTOQUE", "FIADO", "FLUXO CAIXA", "PRÓXIMAS COMPRAS", "GRÁFICO"])

# --- 1. CAIXA (FRENTE DE VENDA) ---
if menu == "CAIXA":
    st.header("🛒 Frente de Caixa")
    estoque = buscar_dados("estoque")

    if estoque:
        # CORREÇÃO DEFINITIVA DO ERRO DE TYPEERROR:
        prod_nomes = [f"{p['codigo']} - {p['nome']}" for p in estoque]

        col1, col2 = st.columns([2, 1])
        with col1:
            selecionado = st.selectbox("Selecione o Produto", prod_nomes)
            # Localiza o item no banco
            item = next(p for p in estoque if f"{p['codigo']} - {p['nome']}" == selecionado)

            qtd = st.number_input("Quantidade", min_value=1, step=1)
            cliente = st.text_input("Nome do Cliente", "CONSUMIDOR")
            metodo = st.selectbox("Método de Pagamento",
                                  ["Dinheiro", "Pix", "Cartão Débito", "Cartão Crédito", "FIADO"])

        with col2:
            subtotal = float(item['preco_venda']) * qtd
            desconto = st.number_input("Desconto (R$)", min_value=0.0, value=0.0)
            total_final = subtotal - desconto
            st.metric("Total a Pagar", f"R$ {total_final:.2f}")

            if st.button("FINALIZAR VENDA", use_container_width=True):
                # 1. Registrar na tabela de Vendas
                venda_payload = {
                    "cod_item": item['codigo'],
                    "produto": item['nome'],
                    "quantidade": qtd,
                    "subtotal": subtotal,
                    "desconto": desconto,
                    "total_liq": total_final,
                    "cliente": cliente,
                    "metodo": metodo,
                    "vendedor": "WEB-MOBILE"
                }
                httpx.post(f"{URL}/vendas", headers=HEADERS, json=venda_payload)

                # 2. Atualizar estoque (Somar na coluna 'vendas')
                nova_qtd_vendas = (item.get('vendas') or 0) + qtd
                httpx.patch(f"{URL}/estoque?codigo=eq.{item['codigo']}", headers=HEADERS,
                            json={"vendas": nova_qtd_vendas})

                # 3. Se for FIADO, registrar na tabela de fiado
                if metodo == "FIADO":
                    fiado_payload = {"cliente": cliente, "valor": total_final, "data": str(datetime.now()),
                                     "status": "PENDENTE"}
                    httpx.post(f"{URL}/fiado", headers=HEADERS, json=fiado_payload)

                st.success(f"✅ Venda de {item['nome']} finalizada!")
                st.rerun()

# --- 2. VENDAS (RELATÓRIO HISTÓRICO) ---
elif menu == "VENDAS":
    st.header("📋 Relatório Geral de Vendas")
    vendas = buscar_dados("vendas")
    if vendas:
        df_vendas = pd.DataFrame(vendas)
        st.dataframe(df_vendas, use_container_width=True)
        st.download_button("Baixar Relatório (CSV)", df_vendas.to_csv(), "vendas.csv")

# --- 3. ESTOQUE (GESTÃO E EDIÇÃO) ---
elif menu == "ESTOQUE":
    st.header("📦 Gestão de Estoque")
    dados = buscar_dados("estoque")
    if dados:
        df_e = pd.DataFrame(dados)
        # Cálculo da Quantidade Disponível (Lógica do seu EXE)
        df_e['Disponível'] = df_e['qtd_ini'] + df_e['compras'] - df_e['vendas'] - df_e.get('fiado', 0)
        st.dataframe(df_e, use_container_width=True)

        st.divider()
        st.subheader("🛠️ Editar Produto / Entrada Manual")
        with st.form("edit_form"):
            c1, c2, c3 = st.columns(3)
            e_cod = c1.text_input("Código do Item")
            e_preco = c2.number_input("Novo Preço Venda", min_value=0.0)
            e_compra = c3.number_input("Adicionar Compras (Qtd)", min_value=0)
            if st.form_submit_button("Salvar Alterações"):
                # Busca item atual para somar compras
                item_atual = next((p for p in dados if str(p['codigo']) == e_cod), None)
                if item_atual:
                    nova_compra = item_atual['compras'] + e_compra
                    httpx.patch(f"{URL}/estoque?codigo=eq.{e_cod}", headers=HEADERS,
                                json={"preco_venda": e_preco, "compras": nova_compra})
                    st.success("Estoque Atualizado!")
                    st.rerun()

# --- 4. FIADO (CLIENTES DEVENDO) ---
elif menu == "FIADO":
    st.header("📝 Controle de Fiados")
    fiados = buscar_dados("fiado")
    if fiados:
        df_f = pd.DataFrame(fiados)
        st.table(df_f)

        st.divider()
        devedor = st.selectbox("Dar baixa em:", df_f['cliente'].unique())
        if st.button("Marcar como Pago"):
            httpx.delete(f"{URL}/fiado?cliente=eq.{devedor}", headers=HEADERS)
            st.success(f"Dívida de {devedor} removida!")
            st.rerun()

# --- 5. FLUXO CAIXA (FINANCEIRO) ---
elif menu == "FLUXO CAIXA":
    st.header("💰 Fluxo de Caixa Real")
    vendas = buscar_dados("vendas")
    if vendas:
        df = pd.DataFrame(vendas)
        faturamento = df['total_liq'].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Entradas", f"R$ {faturamento:.2f}")
        c2.metric("Nº de Vendas", len(df))
        c3.metric("Ticket Médio", f"R$ {(faturamento / len(df)):.2f}")

        st.subheader("Vendas por Método")
        st.bar_chart(df['metodo'].value_counts())

# --- 6. PRÓXIMAS COMPRAS (ALERTA) ---
elif menu == "PRÓXIMAS COMPRAS":
    st.header("🛒 Sugestão de Reposição")
    estoque = buscar_dados("estoque")
    if estoque:
        df = pd.DataFrame(estoque)
        df['Disponível'] = df['qtd_ini'] + df['compras'] - df['vendas']
        # Filtra apenas o que está abaixo de 3 unidades
        baixo_estoque = df[df['Disponível'] <= 3]
        if not baixo_estoque.empty:
            st.warning("Os itens abaixo precisam de reposição urgente!")
            st.table(baixo_estoque[['codigo', 'nome', 'Disponível']])
        else:
            st.success("Todos os itens estão com estoque em dia!")

# --- 7. GRÁFICO (PERFORMANCE) ---
elif menu == "GRÁFICO":
    st.header("📊 Análise de Performance")
    vendas = buscar_dados("vendas")
    if vendas:
        df_v = pd.DataFrame(vendas)
        st.subheader("Produtos Mais Vendidos (Faturamento)")
        chart_data = df_v.groupby('produto')['total_liq'].sum()
        st.bar_chart(chart_data)