"""
Scraper des compositions d'equipes - AllRugby
Recupere les compositions officielles des equipes du Top 14.
"""

import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from unidecode import unidecode
import os

# --- CONFIGURATION ---
ALLRUGBY_BASE = "https://www.allrugby.com"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def trouver_url_compos():
    """Tente de trouver automatiquement l'URL de la page des compositions."""
    print("Recherche de la page des compositions sur AllRugby...")
    
    try:
        response = requests.get(ALLRUGBY_BASE, headers={"User-Agent": USER_AGENT}, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'compos' in href.lower() and 'top-14' in href.lower():
                url = href if href.startswith('http') else ALLRUGBY_BASE + href
                print(f"   URL trouvee: {url}")
                return url
        
        print("[WARN] Page des compositions non trouvee automatiquement.")
        return None
        
    except Exception as e:
        print(f"[ERREUR] {e}")
        return None


def scraper_compos(url):
    """Scrape les compositions depuis la page AllRugby."""
    print(f"Scraping des compositions depuis : {url}")
    
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Chercher les joueurs dans les liens
        joueurs_trouves = {}
        clubs_avec_compos = set()
        
        # Methode 1: Chercher les liens vers les joueurs
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/joueurs/' in href:
                nom = link.get_text(strip=True)
                if nom and len(nom) > 2:
                    nom_norm = normaliser_nom(nom)
                    if nom_norm not in joueurs_trouves:
                        joueurs_trouves[nom_norm] = {
                            'nom': nom,
                            'statut': 'titulaire',
                            'numero': None
                        }
        
        # Methode 2: Parser le texte pour trouver les numeros
        texte = soup.get_text()
        
        # Pattern pour les blocs par club
        pattern_club = r'(TOULOUSE|RACING 92|RACING|LA ROCHELLE|BORDEAUX|TOULON|CLERMONT|MONTPELLIER|LYON|CASTRES|PAU|BAYONNE|PERPIGNAN|MONTAUBAN|PARIS|STADE FRANCAIS|STADE FRANÇAIS)'
        blocs = re.split(pattern_club, texte, flags=re.IGNORECASE)
        
        current_club = None
        for bloc in blocs:
            bloc_upper = bloc.strip().upper()
            if re.match(pattern_club, bloc_upper, re.IGNORECASE):
                current_club = normaliser_club(bloc_upper)
                clubs_avec_compos.add(current_club)
                continue
            
            if current_club and len(bloc) > 50:
                # Chercher les joueurs numerotes
                pattern_joueur = r'(\d{1,2})\s*[.\-–)]\s*([A-Z][a-zA-ZéèêëàâäùûüôöîïçÉÈÊËÀÂÄÙÛÜÔÖÎÏÇ\'\-\s]+?)(?=\d{1,2}\s*[.\-–)]|$)'
                matches = re.findall(pattern_joueur, bloc + " 99.")
                
                for numero, nom in matches:
                    num = int(numero)
                    nom = nom.strip()
                    if num >= 1 and num <= 23 and len(nom) > 2:
                        nom_norm = normaliser_nom(nom)
                        statut = 'titulaire' if num <= 15 else 'remplacant'
                        
                        joueurs_trouves[nom_norm] = {
                            'nom': nom,
                            'statut': statut,
                            'numero': num,
                            'club': current_club
                        }
        
        print(f"[OK] {len(joueurs_trouves)} joueurs trouves dans les compositions")
        
        # Filtrer les clubs valides (exclure les titres de page)
        clubs_valides = {c for c in clubs_avec_compos if len(c) < 30}
        print(f"   Clubs avec compos publiees: {sorted(clubs_valides)}")
        
        return joueurs_trouves, clubs_valides
        
    except Exception as e:
        print(f"[ERREUR] Erreur lors du scraping : {e}")
        import traceback
        traceback.print_exc()
        return {}, set()


def normaliser_nom(nom):
    """Normalise un nom pour faciliter le matching."""
    nom = unidecode(nom.lower().strip())
    nom = re.sub(r'[^\w\s\-]', '', nom)
    nom = ' '.join(nom.split())
    return nom


def normaliser_club(club):
    """Normalise le nom d'un club pour matching."""
    club = club.strip().upper()
    
    mapping = {
        "RACING 92": "Racing 92",
        "RACING": "Racing 92",
        "TOULOUSE": "Toulouse",
        "STADE TOULOUSAIN": "Toulouse",
        "LA ROCHELLE": "La Rochelle",
        "STADE ROCHELAIS": "La Rochelle",
        "BORDEAUX": "Bordeaux-Begles",
        "BORDEAUX-BEGLES": "Bordeaux-Begles",
        "UBB": "Bordeaux-Begles",
        "TOULON": "Toulon",
        "RCT": "Toulon",
        "CLERMONT": "Clermont",
        "ASM": "Clermont",
        "MONTPELLIER": "Montpellier",
        "MHR": "Montpellier",
        "LYON": "Lyon",
        "LOU": "Lyon",
        "CASTRES": "Castres",
        "PARIS": "Stade francais",
        "STADE FRANCAIS": "Stade francais",
        "STADE FRANÇAIS": "Stade francais",
        "PAU": "Pau",
        "SECTION PALOISE": "Pau",
        "BAYONNE": "Bayonne",
        "AVIRON BAYONNAIS": "Bayonne",
        "PERPIGNAN": "Perpignan",
        "USAP": "Perpignan",
        "MONTAUBAN": "Montauban",
        "USM": "Montauban",
    }
    
    return mapping.get(club, club.title())


def charger_joueurs_fantasy(csv_path=None):
    """Charge le CSV des joueurs Fantasy et prepare le matching."""
    if csv_path is None:
        csv_path = os.path.join(os.path.dirname(__file__), "output", "joueurs_lagrandemelee_complet.csv")
    print(f"Chargement du CSV Fantasy : {csv_path}")
    
    if not os.path.exists(csv_path):
        print(f"[ERREUR] Fichier {csv_path} non trouve")
        return None
    
    df = pd.read_csv(csv_path, sep=";", encoding="utf-8-sig")
    df['nom_normalise'] = df['nom'].apply(normaliser_nom)
    
    print(f"   {len(df)} joueurs charges")
    return df


def matching_fuzzy(nom1, nom2):
    """Matching approximatif simple entre deux noms."""
    mots1 = set(w for w in nom1.split() if len(w) > 2)
    mots2 = set(w for w in nom2.split() if len(w) > 2)
    
    if not mots1 or not mots2:
        return False
    
    intersection = mots1 & mots2
    return len(intersection) >= 1


def enrichir_avec_compos(df, compos, clubs_avec_compos):
    """Enrichit le DataFrame des joueurs Fantasy avec les statuts de composition."""
    print("Enrichissement des donnees avec les compositions...")
    
    df['statut_compo'] = 'inconnu'
    df['numero_compo'] = None
    
    matched = 0
    
    for idx, row in df.iterrows():
        nom_norm = row['nom_normalise']
        club = row['club']
        club_normalise = normaliser_club(club)
        
        found = False
        if nom_norm in compos:
            info = compos[nom_norm]
            df.at[idx, 'statut_compo'] = info['statut']
            df.at[idx, 'numero_compo'] = info['numero']
            matched += 1
            found = True
        else:
            for nom_compo, info in compos.items():
                if matching_fuzzy(nom_norm, nom_compo):
                    df.at[idx, 'statut_compo'] = info['statut']
                    df.at[idx, 'numero_compo'] = info['numero']
                    matched += 1
                    found = True
                    break
        
        if not found:
            if club_normalise in clubs_avec_compos:
                df.at[idx, 'statut_compo'] = 'absent'
            else:
                df.at[idx, 'statut_compo'] = 'compo_non_dispo'
    
    # Calculer les clubs sans compo
    tous_les_clubs = set(df['club'].apply(normaliser_club).unique())
    clubs_valides = {c for c in clubs_avec_compos if len(c) < 50}
    clubs_sans_compo = tous_les_clubs - clubs_valides
    
    # Affichage des stats
    print(f"\nSTATISTIQUES DE COMPOSITION")
    print(f"   Clubs avec compo publiee ({len(clubs_valides)}):")
    for club in sorted(clubs_valides):
        print(f"      [OK] {club}")
    
    if clubs_sans_compo:
        print(f"\n   Clubs sans compo ({len(clubs_sans_compo)}):")
        for club in sorted(clubs_sans_compo):
            print(f"      [WAIT] {club}")
    else:
        print(f"\n   [OK] Toutes les equipes ont leur composition publiee !")
    
    print(f"\n[OK] {matched} joueurs matches avec les compositions")
    print(f"   - Titulaires: {len(df[df['statut_compo'] == 'titulaire'])}")
    print(f"   - Remplacants: {len(df[df['statut_compo'] == 'remplacant'])}")
    print(f"   - Absents (non selectionnes): {len(df[df['statut_compo'] == 'absent'])}")
    print(f"   - Compo non dispo: {len(df[df['statut_compo'] == 'compo_non_dispo'])}")
    
    return df


def sauvegarder_csv_enrichi(df, fichier=None):
    """Sauvegarde le CSV enrichi."""
    if fichier is None:
        fichier = os.path.join(os.path.dirname(__file__), "output", "joueurs_enrichis.csv")
    os.makedirs(os.path.dirname(fichier), exist_ok=True)
    df.to_csv(fichier, index=False, sep=";", encoding="utf-8-sig")
    print(f"[OK] CSV enrichi sauvegarde : {fichier}")


def sauvegarder_par_role(df, dossier="joueurs_par_role"):
    """Sauvegarde des CSV par position."""
    os.makedirs(dossier, exist_ok=True)
    
    for position in df['position'].unique():
        df_pos = df[df['position'] == position]
        fichier = os.path.join(dossier, f"joueurs_{position}.csv")
        df_pos.to_csv(fichier, index=False, sep=";", encoding="utf-8-sig")
        print(f"   [OK] {position}: {len(df_pos)} joueurs")


def main():
    import sys
    
    print("=" * 60)
    print("SCRAPER COMPOSITIONS ALLRUGBY")
    print("=" * 60)
    
    # Determiner l'URL
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = trouver_url_compos()
        if not url:
            print("\n[INFO] Fournissez l'URL en argument:")
            print("   python scrape_compos.py <URL>")
            return
    
    # Scraper les compositions
    compos, clubs_avec_compos = scraper_compos(url)
    
    if not compos:
        print("[ERREUR] Aucune composition trouvee")
        return
    
    # Charger les joueurs Fantasy
    df = charger_joueurs_fantasy()
    if df is None:
        return
    
    # Enrichir avec les compositions
    df = enrichir_avec_compos(df, compos, clubs_avec_compos)
    
    # Sauvegarder
    sauvegarder_csv_enrichi(df)
    
    print("\n" + "=" * 60)
    print("[OK] TERMINE !")
    print("=" * 60)


if __name__ == "__main__":
    main()
