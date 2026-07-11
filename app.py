import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import urllib.parse
from streamlit_mic_recorder import speech_to_text

# --- 1. CONFIGURATION ET DESIGN ---
NOM_APPLI = "Primo Bruce 1 system"
ICONE_APPLI = "⚡"
SOUS_TITRE = "Expertise Argus & Estimations de Marché par Dictée Vocale"
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

# --- 2. FONCTION DE RECHERCHE EBAY ---
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
                if "à" in p_txt: p_txt = p_txt.split("à")[0]
                try:
                    prix = float(''.join(c for c in p_txt if c.isdigit() or c == '.'))
                    ventes.append({"Plateforme": "eBay (Vendu)", "Titre": title, "Prix (€)": prix})
                except: pass
        return ventes
    except: return []

# --- 3. INTERFACE UTILISATEUR ---
st.title(f"{ICONE_APPLI} {NOM_APPLI}")
st.markdown(f"<p style='color:#64748b; font-size:16px; margin-top:-15px; margin-bottom:25px;'>{SOUS_TITRE}</p>", unsafe_allow_html=True)

# Bloc Micro de dictée vocale
st.write("🎙️ **Cliquez ci-dessous pour dicter l'objet à haute voix :**")
texte_dicte = speech_to_text(language='fr', start_prompt="▶️ Lancer l'écoute", stop_prompt="⏹️ Arrêter", justify='center', key='dictation')

# Champ de texte qui se remplit automatiquement avec la voix
if texte_dicte:
    st.success(f"🗣️ Compris : **{texte_dicte}**")
    query = st.text_input("Texte de recherche actuel :", value=texte_dicte)
else:
    query = st.text_input("Texte de recherche actuel :", value="")

st.write(" ")
bouton_analyser = st.button("🚀 Extraire la valeur de l'objet et calculer l'argus", type="primary", use_container_width=True)

if bouton_analyser and query:
    with st.spinner("Analyse des prix en cours..."):
        resultats_prix = fetch_ebay_sold(query)
            
        if resultats_prix:
            df = pd.DataFrame(resultats_prix)
            mediane = round(np.median(df["Prix (€)"]), 2)
            plafond = round(max(df["Prix (€)"]), 2)
            plancher = round(min(df["Prix (€)"]), 2)
            
            col1, col2, col3 = st.columns(3)
            with col1: st.markdown(f'<div class="metric-box"><p style="margin:0;font-size:13px;font-weight:600;color:#64748b;">ESTIMATION MÉDIANE</p><p class="big-price">{mediane} €</p></div>', unsafe_allow_html=True)
            with col2: st.markdown(f'<div class="metric-box"><p style="margin:0;font-size:13px;font-weight:600;color:#64748b;">VALEUR HAUTE</p><p class="big-price" style="color:#10b981;">{plafond} €</p></div>', unsafe_allow_html=True)
            with col3: st.markdown(f'<div class="metric-box"><p style="margin:0;font-size:13px;font-weight:600;color:#64748b;">SEUIL PLANCHER</p><p class="big-price" style="color:#ef4444;">{plancher} €</p></div>', unsafe_allow_html=True)
            
            st.write(" ")
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("Aucun résultat récent trouvé pour cette recherche.")
