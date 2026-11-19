# to start: streamlit run main.py

import streamlit as st
from auth import require_password
from config import load_settings
from n8n_client import N8nClient, N8nError, CvRejectedError

st.set_page_config(page_title="Anonymisation de CV", layout="wide")
settings = load_settings()

st.title("📄 Anonymisation de CV")
st.caption("Déposez un CV, obtenez un dossier de compétences anonymisé.")

require_password(settings.app_password)   # nothing below runs without it
client = N8nClient(settings.n8n_base_url, settings.n8n_api_key)


@st.cache_data(ttl=30)
def load_consultants(_client: N8nClient):
    return _client.list_consultants()

tab_upload, tab_cvs, tab_db = st.tabs(["Déposer un CV", "CV anonymisés", "Base consultants"])

with tab_upload:
    file = st.file_uploader("CV (PDF ou Word)", type=["pdf", "docx"])
    if file and st.button("Anonymiser"):
        try:
            with st.spinner("Traitement en cours (≈ 20 s)…"):
                result = client.upload_cv(file.name, file.getvalue(), file.type)
            load_consultants.clear()
            st.success(f"Code consultant : {result.code}")
            st.link_button("Ouvrir le CV anonymisé", result.link)
            st.caption(f"Alertes RGPD rattrapées : {result.alertes}")

        except CvRejectedError as exc:
            st.warning(str(exc))
        
        except N8nError as exc:
            st.error(str(exc))

try:
    df = load_consultants(client)
except N8nError as exc:
    st.error(str(exc))
    st.stop()

with tab_cvs:   # anonymised columns only, never real data
    public = ["Code consultant", "Poste", "Années d'expérience",
              "Compétences", "Lien CV anonymisé"]
    st.dataframe(
        df[public], width='stretch', hide_index=True,
        column_config={"Lien CV anonymisé": st.column_config.LinkColumn("CV")},
    )

with tab_db:
    query = st.text_input("Recherche")
    if query:
        mask = df.astype(str).apply(
            lambda col: col.str.contains(query, case=False, na=False)
        ).any(axis=1)
        df = df[mask]
    st.dataframe(df, use_container_width=True, hide_index=True)