import pandas as pd
import streamlit as st
from rapidfuzz import process

# ==============================
# CONFIGURAÇÃO
# ==============================
st.set_page_config(page_title="Cotação Automática", layout="centered")

st.title("📊 Cotação Automática")
st.write("Envie sua planilha e receba pronta em segundos")

# ==============================
# FUNÇÃO: LIMPAR E PADRONIZAR COLUNAS
# ==============================
def padronizar_colunas(df):

    df.columns = df.columns.str.strip().str.lower()

    mapa = {}

    for col in df.columns:
        if "prod" in col:
            mapa[col] = "Produto"
        elif "cod" in col:
            mapa[col] = "Código"
        elif "pre" in col:
            mapa[col] = "Preço"

    df.rename(columns=mapa, inplace=True)

    return df

# ==============================
# CARREGAR BASE DE PREÇOS
# ==============================
try:
    base = pd.read_excel("base_precos.xlsx")
except:
    st.error("❌ Arquivo base_precos.xlsx não encontrado")
    st.stop()

base = padronizar_colunas(base)

# Validar base
if "Produto" not in base.columns or "Preço" not in base.columns:
    st.error("❌ A base precisa ter colunas de Produto e Preço")
    st.write("Colunas encontradas:", list(base.columns))
    st.stop()

base["Produto"] = base["Produto"].astype(str)

if "Código" in base.columns:
    base["Código"] = base["Código"].astype(str)
else:
    base["Código"] = None

# Criar mapa rápido (performance)
mapa_codigo = dict(zip(base["Código"], base["Preço"]))
base_produtos = base["Produto"].tolist()

# ==============================
# FUNÇÃO INTELIGENTE
# ==============================
def encontrar_preco(produto, codigo):

    # 1. Código (prioridade máxima)
    if pd.notna(codigo):
        codigo = str(codigo)
        if codigo in mapa_codigo:
            return mapa_codigo[codigo]

    # 2. Nome (fuzzy)
    if pd.isna(produto):
        return None

    produto = str(produto)

    match, score, idx = process.extractOne(produto, base_produtos)

    if score > 85:
        return base.iloc[idx]["Preço"]

    return None

# ==============================
# UPLOAD
# ==============================
cotacao_file = st.file_uploader("📤 Envie a cotação", type=["xlsx"])

if cotacao_file:

    cotacao = pd.read_excel(cotacao_file)
    cotacao = padronizar_colunas(cotacao)

    # Validação
    if "Produto" not in cotacao.columns:
        st.error("❌ A planilha precisa ter uma coluna de produto")
        st.write("Colunas encontradas:", list(cotacao.columns))
        st.stop()

    if "Código" not in cotacao.columns:
        cotacao["Código"] = None

    st.success("✅ Arquivo carregado")

    # ==============================
    # PROCESSAMENTO
    # ==============================
    if st.button("⚡ Processar Cotação"):

        with st.spinner("Processando..."):

            cotacao["Preço"] = cotacao.apply(
                lambda row: encontrar_preco(
                    row["Produto"],
                    row["Código"]
                ),
                axis=1
            )

        # ==============================
        # RESULTADOS
        # ==============================
        erros = cotacao[cotacao["Preço"].isnull()]

        st.success("🎉 Cotação pronta!")

        if not erros.empty:
            st.warning(f"⚠ {len(erros)} produtos não encontrados")

        st.dataframe(cotacao)

        # ==============================
        # DOWNLOAD
        # ==============================
        output = "cotacao_final.xlsx"
        cotacao.to_excel(output, index=False)

        with open(output, "rb") as f:
            st.download_button(
                "📥 Baixar Cotação",
                f,
                file_name=output
            )
