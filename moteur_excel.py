import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import urllib.parse
import os

# --- MOTEURS DE RECHERCHE ---
def fetch_delcampe(keywords):
    query = urllib.parse.quote_plus(keywords)
    url = f"https://www.delcampe.net/fr/collections/search?term={query}&status=closed&net_prices=all&order=sale_date_desc"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        ventes = []
        for art in soup.select("div.item-listing-card") or soup.select(".item-main-infos")[:8]:
            p_elem = art.select_one(".price") or art.select_one(".item-price")
            if p_elem:
                p_txt = p_elem.text.replace("€", "").replace(",", ".").replace(" ", "").strip()
                ventes.append(float(''.join(c for c in p_txt if c.isdigit() or c == '.')))
        return ventes
    except: return []

def fetch_rakuten(keywords):
    query = urllib.parse.quote(keywords)
    url = f"https://fr.shopping.rakuten.com/s/{query}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        ventes = []
        for prod in soup.select("[data-qa='product_card']")[:8]:
            p_elem = prod.select_one("[data-qa='product_price']")
            if p_elem:
                p_txt = p_elem.text.replace("€", "").replace(",", ".").replace(" ", "").strip()
                ventes.append(float(''.join(c for c in p_txt if c.isdigit() or c == '.')))
        return ventes
    except: return []

# --- CALCULATEUR STATISTIQUE ---
def calculer_estimation(nom_objet):
    prix_bruts = []
    prix_bruts.extend(fetch_delcampe(nom_objet))
    prix_bruts.extend(fetch_rakuten(nom_objet))
    
    if len(prix_bruts) < 2:
        return 0.0, 0.0, 0.0
        
    q1, q3 = np.percentile(prix_bruts, [25, 75])
    iqr = q3 - q1
    prix_nettoyes = [p for p in prix_bruts if (q1 - 1.5 * iqr) <= p <= (q3 + 1.5 * iqr)]
    
    if not prix_nettoyes:
        prix_nettoyes = prix_bruts

    return (
        round(np.median(prix_nettoyes), 2),
        round(max(prix_nettoyes), 2),
        round(min(prix_nettoyes), 2)
    )

# --- TRAITEMENT DU FICHIER INVENTAIRE ---
def executer_moteur_excel():
    fichier_entree = "a_estimer.xlsx"
    fichier_sortie = "mon_inventaire_resell.xlsx"
    
    if not os.path.exists(fichier_entree):
        print(f"[*] Création du fichier exemple : {fichier_entree}")
        df_exemple = pd.DataFrame({
            "Titre/Objet": ["Tramber La Grande Souris Noire", "Vinyle Prince Purple Rain Original", "BD Bilal Partie de chasse"],
            "Prix d'achat (€)": [5.00, 10.00, 4.50]
        })
        df_exemple.to_excel(fichier_entree, index=False)
    
    print(f"[+] Analyse en cours...")
    df = pd.read_excel(fichier_entree)
    
    list_median, list_plafond, list_plancher, list_marge = [], [], [], []
    
    for index, row in df.iterrows():
        nom = row["Titre/Objet"]
        achat = row["Prix d'achat (€)"]
        print(f" 🔍 Analyse : {nom}...")
        
        median, plafond, plancher = calculer_estimation(nom)
        marge = round(median - achat, 2) if median > 0 else 0.0
        
        list_median.append(median)
        list_plafond.append(plafond)
        list_plancher.append(plancher)
        list_marge.append(marge)
    
    df["Prix Plancher Constaté (€)"] = list_plancher
    df["Prix Médian Estimé (€)"] = list_median
    df["Prix Plafond Constaté (€)"] = list_plafond
    df["Marge Brute Estimée (€)"] = list_marge
    df["Statut Vente"] = "À lister"
    
    df.to_excel(fichier_sortie, index=False, engine='openpyxl')
    print(f"[🎉] Terminé ! Ton inventaire valorisé est disponible ici : {fichier_sortie}")

if __name__ == "__main__":
    executer_moteur_excel()
