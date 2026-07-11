import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import urllib.parse
from io import BytesIO

# --- 1. CONFIGURATION ET DESIGN ---
st.set_page_config(page_title="ResellAgent IA", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .metric-box { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #1f77b4; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .big-price { font-size: 32px; font-weight: bold; color: #1f77b4; }
    .vinyl-spec { font-size: 13px; color: #555; background: #eef2f7; padding: 4px 8px; border-radius: 4px; margin-right: 5px; display: inline-block; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LES MOTEURS DE RECHERCHE AUTOMATIQUES ---

DISCOGS_TOKEN = st.secrets.get("DISCOGS_TOKEN", "")

def fetch_discogs_api(keywords):
    """Interroge l'API officielle de Discogs pour identifier précisément les pressages de vinyles"""
    if not DISCOGS_TOKEN:
        return []
    query = urllib.parse.quote(keywords)
    url = f"https://api.discogs.com/database/search?q={query}&type=release&per_page=8"
    headers = {
        "User-Agent": "ResellAgentIA/1.0 (brucepremier)",
        "Authorization": f"Discogs token={DISCOGS_TOKEN}"
    }
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            ventes = []
            for item in data.get("results", []):
                ventes.append({
                    "Plateforme": "Discogs API",
                    "Titre": item.get("title", "Sans titre"),
                    "Édition / Label": f"{item.get('label', ['N/C'])[0]} - {item.get('catno', 'N/C')} ({item.get('country', 'N/C')})",
                    "Année": item.get("year", "N/C"),
                    "Info Complémentaire": f"Ref: {item.get('catno', 'N/C')}"
                })
            return ventes
        return []
    except: return []

def fetch_ebay_sold(keywords):
    """Aaspire l'historique des VENTES REUSSIES sur eBay France pour avoir les vrais prix d'adjudication"""
    query = urllib.parse.quote(keywords)
    # LH_Complete=1 & LH_Sold=1 force eBay à afficher uniquement ce qui a été vendu et payé
    url = f"https://www.ebay.fr/sch/i.html?_nkw={query}&LH_Complete=1&LH_Sold=1"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        ventes = []
        for item in soup.select(".s-item")[:8]:
            title_elem = item.select_one(".s-item__title")
            price_elem = item.select_one(".s-item__price")
            if title_elem and price_elem:
                title = title_elem.text.replace("Nouvelle annonce", "").strip()
                if "Shop on eBay" in title or "Boutique sur" in title:
                    continue
                p_txt = price_elem.text.replace("EUR", "").replace("€", "").replace(",", ".").replace(" ", "").strip()
                if "à" in p_txt:  # Gère les fourchettes de prix eBay (ex: 10€ à 15€)
                    p_txt = p_txt.split("à")[0]
                try:
                    prix = float(''.join(c for c in p_txt if c.isdigit() or c == '.'))
                    ventes.append({"Plateforme": "eBay (Vendu)", "Titre": title, "Prix (€)": prix, "Détails": "Transaction validée"})
                except: pass
        return ventes
    except: return []

def fetch_delcampe(keywords):
    query = urllib.parse.quote_plus(keywords)
    url = f"https://www.delcampe.net/fr/collections/search?term={query}&status=closed&net_prices=all&order=sale_date_desc"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        ventes = []
        for art in soup.select("div.item-listing-card") or soup.select(".item-main-infos")[:8]:
            titre = art.select_one(".item-title").text.strip() if art.select_one(".item-title") else "Objet"
            p_elem = art.select_one(".price") or art.select_one(".item-price")
            if p_elem:
                p_txt = p_elem.text.replace("€", "").replace(",", ".").replace(" ", "").strip()
                prix = float(''.join(c for c in p_txt if c.isdigit() or c == '.'))
                ventes.append({"Plateforme": "Delcampe", "Titre": titre, "Prix (€)": prix, "Détails": "Vente clôturée"})
        return ventes
    except: return []

def fetch_rakuten(keywords):
    query = urllib.parse.quote(keywords)
    url = f"https://fr.shopping.rakuten.com/s/{query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        ventes = []
        for prod in soup.select("[data-qa='product_card']")[:8]:
            titre = prod.select_one("[data-qa='product_title']").text.strip()
            p_elem = prod.select_one("[data-qa='product_price']")
            if p_elem:
                p_txt = p_elem.text.replace("€", "").replace(",", ".").replace(" ", "").strip()
                ventes.append({"Plateforme": "Rakuten", "Titre": titre, "Prix (€)": float(''.join(c for c in p_txt if c.isdigit() or c == '.')), "Détails": "Prix constaté"})
        return ventes
    except: return []

# --- 3. INTERFACE UTILISATEUR ---

with st.sidebar:
    st.title("⚙️ Configuration")
    univers = st.radio("Choisissez l'univers de vente :", ("📚 Bandes Dessinées", "🎵 Disques & Vinyles", "🏺 Objets de Collection & Mag"))
    st.divider()
    if DISCOGS_TOKEN:
        st.success("🔑 API Discogs : Connectée")
    else:
        st.warning("⚠️ API Discogs : Hors ligne")
    st.info("ℹ️ Moteurs actifs : eBay (Vendus), Delcampe, Rakuten")

st.title("⚡ ResellAgent IA")
st.subheader("Analyseur sectoriel multi-plateformes en temps réel")

# Ajustement selon l'univers
if univers == "📚 Bandes Dessinées":
    default_search = "Tramber La Grande Souris Noire"
elif univers == "🎵 Disques & Vinyles":
    default_search = "Prince Purple Rain Original"
else:
    default_search = "Magazine Starwax"

query = st.text_input("Recherche (Titre, Artiste, Réf, Code-barres...) :", value=default_search)

# Bouton LeBonCoin intelligent (Raccourci terrain)
lbc_query = urllib.parse.quote(query)
url_lbc = f"https://www.leboncoin.fr/recherche?text={lbc_query}"

col_btn1, col_btn2 = st.columns([1, 1])
with col_btn1:
    bouton_analyser = st.button("🚀 Lancer l'analyse automatique", type="primary", use_container_width=True)
with col_btn2:
    st.markdown(f'<a href="{url_lbc}" target="_blank" style="text-decoration:none;"><button style="width:100%; height:38px; background-color:#ff6e14; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">🟠 Ouvrir sur LeBonCoin</button></a>', unsafe_allow_html=True)

if bouton_analyser and query:
    with st.spinner("🔄 Requêtage simultané des bases de données de marché..."):
        
        # Récupération des prix pour le calcul des statistiques (eBay fonctionne partout maintenant)
        resultats_prix = []
        resultats_prix.extend(fetch_ebay_sold(query))
        
        if univers == "📚 Bandes Dessinées":
            resultats_prix.extend(fetch_delcampe(query))
            resultats_prix.extend(fetch_rakuten(query))
        elif univers == "🏺 Objets de Collection & Mag":
            resultats_prix.extend(fetch_delcampe(query)) # Delcampe est excellent pour les vieux mags/papiers
            
        # Affichage des statistiques financières si on a des prix
        if resultats_prix:
            df = pd.DataFrame(resultats_prix)
            prix_bruts = df["Prix (€)"].tolist()
            q1, q3 = np.percentile(prix_bruts, [25, 75])
            iqr = q3 - q1
            prix_nettoyes = [p for p in prix_bruts if (q1 - 1.5*iqr) <= p <= (q3 + 1.5*iqr)]
            if not prix_nettoyes: prix_nettoyes = prix_bruts
            
            mediane = round(np.median(prix_nettoyes), 2)
            plafond = round(max(prix_nettoyes), 2)
            plancher = round(min(prix_nettoyes), 2)
            
            col1, col2, col3 = st.columns(3)
            with col1: st.markdown(f'<div class="metric-box"><p style="margin:0;font-weight:bold;">ESTIMATION MÉDIANE</p><p class="big-price">{mediane} €</p><p style="margin:0;font-size:12px;color:green;">🎯 Cible de revente idéale</p></div>', unsafe_allow_html=True)
            with col2: st.markdown(f'<div class="metric-box" style="border-left-color:#2ca02c;"><p style="margin:0;font-weight:bold;">PRIX CONSTANTÉ HAUT</p><p class="big-price" style="color:#2ca02c;">{plafond} €</p><p style="margin:0;font-size:12px;">Objets état Neuf / Collector</p></div>', unsafe_allow_html=True)
            with col3: st.markdown(f'<div class="metric-box" style="border-left-color:#d62728;"><p style="margin:0;font-weight:bold;">PRIX PLANCHER MIN</p><p class="big-price" style="color:#d62728;">{plancher} €</p><p style="margin:0;font-size:12px;">Prix de liquidation rapide</p></div>', unsafe_allow_html=True)
            
            st.subheader("📊 Liste des dernières ventes réelles enregistrées (dont eBay France)")
            st.dataframe(df, use_container_width=True)
        else:
            if univers != "🎵 Disques & Vinyles":
                st.warning("Aucun prix récent trouvé pour cet objet sur eBay/Delcampe.")

        # Structure additionnelle spécifique pour l'API Discogs (Vinyles)
        if univers == "🎵 Disques & Vinyles":
            st.subheader("🔍 Identification du pressage officiel (Base Discogs)")
            resultats_vinyles = fetch_discogs_api(query)
            
            if resultats_vinyles:
                st.success(f"🎯 {len(resultats_vinyles)} pressages d'origine identifiés. Utilise les filtres pour vérifier ta matrice :")
                for v in resultats_vinyles:
                    with st.expander(f"🎵 {v['Titre']} ({v['Année']})"):
                        st.markdown(f"**Label / Pressage d'origine :** {v['Édition / Label']}")
                        st.markdown(f"**Infos :** {v['Info Complémentaire']}")
                        st.markdown('<span class="vinyl-spec">Format: LP / Vinyle</span><span class="vinyl-spec">Référence certifiée</span>', unsafe_allow_html=True)
            else:
                st.info("Aucune fiche de pressage Discogs trouvée pour ce mot-clé précis.")
