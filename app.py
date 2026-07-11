import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import urllib.parse

# --- CONFIGURATION ---
NOM_APPLI = "Primo Bruce 1 system"
ICONE_APPLI = "⚡"
COULEUR_PRINCIPALE = "#1E293B"

st.set_page_config(page_title=NOM_APPLI, page_icon=ICONE_APPLI, layout="wide")

# CSS propre pour des boutons bien alignés
st.markdown(f"""
    <style>
    div.stButton > button {{ width: 100%; border-radius: 4px; font-weight: bold; }}
    .metric {{ background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; }}
    </style>
""", unsafe_allow_html=True)

# --- SCRAPER SIMPLE ---
def get_ebay_prices(keywords):
    url = f"https://www.ebay.fr/sch/i.html?_nkw={urllib.parse.quote(keywords)}&LH_Complete=1&LH_Sold=1"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        data = []
        for item in soup.select(".s-item")[:10]:
            title = item.select_one(".s-item__title")
            price = item.select_one(".s-item__price")
            if title and price:
                titre_txt = title.text.replace("Nouvelle annonce", "").strip()
                prix_txt = price.text.replace("EUR", "").replace("€", "").replace(",", ".").split("à")[0].strip()
                try:
                    prix_val = float(''.join(c for c in prix_txt if c.isdigit() or c == '.'))
                    data.append({"Titre": titre_txt, "Prix (€)": prix_val})
                except: continue
        return data
    except: return []

# --- INTERFACE ---
with st.sidebar:
    st.title("⚙️ Secteurs de Veille")
    univers = st.radio("Univers :", ("📚 Bandes Dessinées", "🎵 Disques & Vinyles", "🏺 Objets de Collection", "⌚ Montres"))

st.title(f"{ICONE_APPLI} {NOM_APPLI}")
query = st.text_input("Objet à rechercher :")

if query:
    q = urllib.parse.quote(query)
    st.write("### 🔍 Accès rapides")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<a href="https://www.ebay.fr/sch/i.html?_nkw={q}&LH_Complete=1&LH_Sold=1" target="_blank"><button>🟠 eBay (Vendus)</button></a>', unsafe_allow_html=True)
    c2.markdown(f'<a href="https://www.leboncoin.fr/recherche?text={q}" target="_blank"><button>🔴 LBC</button></a>', unsafe_allow_html=True)
    c3.markdown(f'<a href="https://www.vinted.fr/catalog?search_text={q}" target="_blank"><button>🔵 Vinted</button></a>', unsafe_allow_html=True)
    
    if univers == "⌚ Montres":
        c4.markdown(f'<a href="https://www.chrono24.fr/search/index.htm?query={q}" target="_blank"><button>⌚ Chrono24</button></a>', unsafe_allow_html=True)
    else:
        c4.markdown(f'<a href="https://www.catawiki.com/fr/s?q={q}" target="_blank"><button>🟣 Catawiki</button></a>', unsafe_allow_html=True)

    st.write("---")
    if st.button("🚀 Extraire l'argus eBay"):
        data = get_ebay_prices(query)
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
            prices = df["Prix (€)"].tolist()
            col1, col2, col3 = st.columns(3)
            col1.metric("Médiane", f"{np.median(prices):.2f} €")
            col2.metric("Max", f"{max(prices):.2f} €")
            col3.metric("Min", f"{min(prices):.2f} €")
        else:
            st.warning("Échec extraction automatique. Utilise les boutons ci-dessus.")
