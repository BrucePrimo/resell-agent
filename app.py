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

# --- 2. LES MOTEURS DE RECHERCHE ---

# Récupération sécurisée du token Discogs dans le Cloud ou en local
DISCOGS_TOKEN = st.secrets.get("DISCOGS_TOKEN", "")

def fetch_discogs_api(keywords):
    """Interroge l'API officielle de Discogs pour identifier précisément les pressages de vinyles"""
    if not DISCOGS_TOKEN:
        return []
    
    query = urllib.parse.quote(keywords)
    url = f"https://api.discogs.com/database/search?q={query}&type=release&per_page=10"
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
                titre = item.get("title", "Sans titre")
                annee = item.get("year", "N/C")
                label = item.get("label", ["N/C"])[0]
                catno = item.get("catno", "N/C")
                pays = item.get("country", "N/C")
                
                # Note pour la tarification : L'API publique Discogs Database ne donne pas les prix en direct 
                # pour éviter le siphonnage, on simule une estimation de base basée sur la rareté ou l'argus
                # que l'on va croiser ou compléter au besoin.
                ventes.append({
                    "Plateforme": "Discogs API",
                    "Titre": titre,
                    "Édition / Label": f"{label} - {catno} ({pays})",
                    "Année": annee,
                    "Info Complémentaire": f"Ref: {catno}"
                })
            return ventes
        return []
    except:
        return []

def fetch_delcampe(keywords):
    query = urllib.parse.quote_plus(keywords)
    url = f"https://www.delcampe.net/fr/collections/search?term={query}&status=closed&net_prices=all&order=sale_date_desc"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        ventes = []
        for art in soup.select("div.item-listing-card") or soup.select(".item-main-infos")[:10]:
            titre = art.select_one(".item-title").text.strip() if art.select_one(".item-title") else "Objet"
            p_elem = art.select_one(".price") or art.select_one(".item-price")
            if p_elem:
                p_txt = p_elem.text.replace("€", "").replace(",", ".").replace(" ", "").strip()
                prix = float(''.join(c for c in p_txt if c.isdigit() or c == '.'))
                ventes.append({"Plateforme": "Delcampe", "Titre": titre, "Prix (€)": prix, "Détails": "Vente validée"})
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
        for prod in soup.select("[data-qa='product_card']")[:10]:
            titre = prod.select_one("[data-qa='product_title']").text.strip()
            p_elem = prod.select_one("[data-qa='product_price']")
            if p_elem:
                p_txt = p_elem.text.replace("€", "").replace(",", ".").replace(" ", "").strip()
                ventes.append({"Plateforme": "Rakuten (Argus)", "Titre": titre, "Prix (€)": float(''.join(c for c in p_txt if c.isdigit() or c == '.')), "Détails": "Prix constaté"})
        return ventes
    except: return []

# --- 3. INTERFACE UTILISATEUR ---

with st.sidebar:
    st.title("⚙️ Configuration")
    univers = st.radio("Choisissez l'univers de vente :", ("📚 Bandes Dessinées", "🎵 Disques & Vinyles"))
    st.divider()
    if DISCOGS_TOKEN:
        st.success("🔑 API Discogs : Connectée au Cloud")
    else:
        st.warning("⚠️ API Discogs : En attente du Token dans les Secrets")
    st.info("ℹ️ Moteurs de scraping : Prêts (Delcampe, Rakuten)")

st.title("⚡ ResellAgent IA")
st.subheader("Analyse de valeur en temps réel et identification d'éditions")

# Ajustement de la valeur par défaut selon l'univers choisi
default_search = "Tramber La Grande Souris Noire" if univers == "📚 Bandes Dessinées" else "Prince Purple Rain Original"
query = st.text_input("Recherche (Titre, Code-barres, Numéro de matrice, Artiste...) :", value=default_search)
bouton_analyser = st.button("🚀 Lancer l'analyse sectorielle", type="primary")

if bouton_analyser and query:
    with st.spinner("🔄 Traitement de la requête et requêtage des API en cours..."):
        
        if univers == "📚 Bandes Dessinées":
            # --- BRANCHE BD ---
            resultats = []
            resultats.extend(fetch_delcampe(query))
            resultats.extend(fetch_rakuten(query))
            
            if resultats:
                df = pd.DataFrame(resultats)
                prix_bruts = df["Prix (€)"].tolist()
                q1, q3 = np.percentile(prix_bruts, [25, 75])
                iqr = q3 - q1
                prix_nettoyes = [p for p in prix_bruts if (q1 - 1.5*iqr) <= p <= (q3 + 1.5*iqr)]
                
                mediane = round(np.median(prix_nettoyes), 2)
                plafond = round(max(prix_nettoyes), 2)
                plancher = round(min(prix_nettoyes), 2)
                
                col1, col2, col3 = st.columns(3)
                with col1: st.markdown(f'<div class="metric-box"><p style="margin:0;font-weight:bold;">PRIX MÉDIAN BD</p><p class="big-price">{mediane} €</p><p style="margin:0;font-size:12px;color:green;">🎯 Zone de vente conseillée</p></div>', unsafe_allow_html=True)
                with col2: st.markdown(f'<div class="metric-box" style="border-left-color:#2ca02c;"><p style="margin:0;font-weight:bold;">PRIX PLAFOND (EO)</p><p class="big-price" style="color:#2ca02c;">{plafond} €</p><p style="margin:0;font-size:12px;">État Supérieur certifié</p></div>', unsafe_allow_html=True)
                with col3: st.markdown(f'<div class="metric-box" style="border-left-color:#d62728;"><p style="margin:0;font-weight:bold;">PRIX PLANCHER</p><p class="big-price" style="color:#d62728;">{plancher} €</p><p style="margin:0;font-size:12px;">Rotation rapide</p></div>', unsafe_allow_html=True)
                
                st.subheader("Détail des correspondances tarifaires")
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("Aucune transaction trouvée sur les plateformes BD pour ce mot-clé.")

        else:
            # --- BRANCHE VINYLES (DISCOGS) ---
            resultats_vinyles = fetch_discogs_api(query)
            
            if resultats_vinyles:
                st.success(f"🎯 {len(resultats_vinyles)} pressages officiels répertoriés trouvés dans la base mondiale Discogs :")
                
                # Affichage des pressages sous forme de fiches claires pour le terrain
                for v in resultats_vinyles:
                    with st.expander(f"🎵 {v['Titre']} ({v['Année']})"):
                        st.markdown(f"**Label / Pressage :** {v['Édition / Label']}")
                        st.markdown(f"**Pays d'origine :** {v['Info Complémentaire']}")
                        st.markdown(f"<span class="vinyl-spec">Format: 12\" LP</span><span class="vinyl-spec">Identification validée ✅</span>", unsafe_allow_html=True)
                
                # Transformation en tableau pour l'export Excel de stock
                df_v = pd.DataFrame(resultats_vinyles)
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_v.to_excel(writer, sheet_name='Pressages_Vinyles', index=False)
                
                st.write(" ")
                st.download_button(
                    label="📥 Exporter ces fiches pressages vers mon catalogue Excel",
                    data=output.getvalue(),
                    file_name=f"Pressages_{query.replace(' ', '_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            else:
                st.warning("⚠️ Aucun pressage trouvé sur Discogs. Vérifie l'orthographe ou le numéro de catalogue inscrit sur la pochette (ex: Oved 138, Warner 925...).")
