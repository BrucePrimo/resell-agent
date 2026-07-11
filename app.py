import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import urllib.parse
from streamlit_mic_recorder import speech_to_text

# --- CONFIGURATION ET DESIGN ---
NOM_APPLI    = "Primo Bruce 1 system"    
ICONE_APPLI  = "⚡"                      
SOUS_TITRE   = "Expertise Argus & Estimations de Marché Professionnelles"
COULEUR_PRINCIPALE = "#1E293B"          

st.set_page_config(page_title=NOM_APPLI, page_icon=ICONE_APPLI, layout="wide")

st.markdown(f"""
    <style>
    html, body, [class*="css"], p, div, button, input, label {{ font-family: 'Roboto', sans-serif !important; }}
    .metric-box {{ background-color: #ffffff; padding: 22px; border-radius: 8px; border: 1px solid #e2e8f0; border-top: 4px solid {COULEUR_PRINCIPALE}; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
    .big-price {{ font-size: 34px; font-weight: 700; color: {COULEUR_PRINCIPALE}; margin-top: 5px; margin-bottom: 5px; }}
    div.stButton > button:first-child {{ background-color: {COULEUR_PRINCIPALE}; color: white; border: none; border-radius: 6px; font-weight: 600; }}
    </style>
""", unsafe_allow_html=True)

DISCOGS_TOKEN = st.secrets.get("DISCOGS_TOKEN", "")

# --- FONCTIONS DE RECHERCHE ---
def fetch_discogs_api(keywords):
    if not DISCOGS_TOKEN: return []
    query = urllib.parse.quote(keywords)
    url = f"https://api.discogs.com/database/search?q={query}&type=release&per_page=8"
    headers = {"User-Agent": "ResellAgentIA/1.0", "Authorization": f"Discogs token={DISCOGS_TOKEN}"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            return [{"Plateforme": "Discogs API", "Titre": item.get("title"), "Année": item.get("year", "N/C")} for item in res.json().get("results", [])]
        return []
    except: return []

def fetch_ebay_sold(keywords):
    query = urllib.parse.quote(keywords)
    url = f"https://www.ebay.fr/sch/i.html?_nkw={query}&LH_Complete=1&LH_Sold=1"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        ventes = []
        for item in soup.select(".s-item")[:10]:
            title_elem = item.select_one(".s-item__title")
            price_elem = item.select_one(".s-item__price")
            if title_elem and price_elem:
                title = title_elem.text.replace("Nouvelle annonce", "").strip()
                p_txt = price_elem.text.replace("EUR", "").replace("€", "").replace(",", ".").replace(" ", "").strip()
                try:
                    prix = float(''.join(c for c in p_txt if c.isdigit() or c == '.'))
                    ventes.append({"Plateforme": "eBay (Vendu)", "Titre": title, "Prix (€)": prix})
                except: pass
        return ventes
    except: return []

# --- INTERFACE ---
with st.sidebar:
    st.title("⚙️ Secteurs de Veille")
    univers = st.radio("Univers :", ("📚 Bandes Dessinées", "🎵 Disques & Vinyles", "🏺 Objets de Collection & Mag", "⌚ Montres de Collection"))

st.title(f"{ICONE_APPLI} {NOM_APPLI}")

# Dictée vocale + saisie clavier combinées
st.write("🎙️ **Dicter ou saisir l'objet :**")
texte_dicte = speech_to_text(language='fr', start_prompt="▶️ Lancer l'écoute", stop_prompt="⏹️ Arrêter", key='dictation')
query = st.text_input("Saisir ou modifier le texte :", value=texte_dicte if texte_dicte else "")

if query:
    encoded_query = urllib.parse.quote(query)
    cols_btn = st.columns(4)
    with cols_btn[0]: st.markdown(f'<a href="https://www.leboncoin.fr/recherche?text={encoded_query}" target="_blank"><button style="width:100%; height:38px; background-color:#ff6e14; color:white; border:none; border-radius:4px; font-weight:bold;">🟠 LeBonCoin</button></a>', unsafe_allow_html=True)
    with cols_btn[1]: st.markdown(f'<a href="https://www.vinted.fr/catalog?search_text={encoded_query}" target="_blank"><button style="width:100%; height:38px; background-color:#09b1ba; color:white; border:none; border-radius:4px; font-weight:bold;">🟢 Vinted</button></a>', unsafe_allow_html=True)

if st.button("🚀 Extraire la valeur et calculer l'argus", type="primary", use_container_width=True):
    resultats = fetch_ebay_sold(query)
    if resultats:
        df = pd.DataFrame(resultats)
        st.write(f"Médiane : {round(np.median(df['Prix (€)']), 2)} €")
        st.dataframe(df, use_container_width=True)
    if univers == "🎵 Disques & Vinyles":
        st.subheader("Base Discogs")
        st.dataframe(pd.DataFrame(fetch_discogs_api(query)))
