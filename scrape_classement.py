"""
Scraping du classement Top 14 et forme des equipes
Genere automatiquement le fichier classement_top14.json
Recupere la forme des equipes depuis l'API La Grande Melee
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
import os


def charger_env():
    """Charge les variables d'environnement depuis .env"""
    env_vars = {}
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    if not os.path.exists(env_path):
        return None
    
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    return env_vars


def normaliser_nom_club(nom):
    """Normalise le nom d'un club pour le matching."""
    mapping = {
        "stade toulousain": "Toulouse",
        "toulouse": "Toulouse",
        "union bordeaux begles": "Bordeaux-Begles",
        "bordeaux begles": "Bordeaux-Begles",
        "bordeaux-begles": "Bordeaux-Begles",
        "bordeaux bègles": "Bordeaux-Begles",
        "ubb": "Bordeaux-Begles",
        "rc toulon": "Toulon",
        "toulon": "Toulon",
        "rct": "Toulon",
        "aviron bayonnais": "Bayonne",
        "bayonne": "Bayonne",
        "asm clermont": "Clermont",
        "clermont": "Clermont",
        "castres olympique": "Castres",
        "castres": "Castres",
        "stade rochelais": "La Rochelle",
        "la rochelle": "La Rochelle",
        "section paloise": "Pau",
        "pau": "Pau",
        "montpellier hr": "Montpellier",
        "montpellier": "Montpellier",
        "mhr": "Montpellier",
        "racing 92": "Racing 92",
        "racing": "Racing 92",
        "lyon ou": "Lyon",
        "lyon": "Lyon",
        "lou": "Lyon",
        "stade francais": "Stade francais",
        "stade français": "Stade francais",
        "stade francais paris": "Stade francais",
        "usa perpignan": "Perpignan",
        "perpignan": "Perpignan",
        "usap": "Perpignan",
        "usm montauban": "Montauban",
        "montauban": "Montauban",
    }
    
    nom_lower = nom.lower().strip()
    nom_lower = re.sub(r'[^\w\s]', '', nom_lower)
    
    return mapping.get(nom_lower, nom.title())


def scraper_calendrier_lgm(env_vars):
    """
    Scrape le calendrier et la forme des equipes depuis l'API La Grande Melee.
    Retourne un dict {club_normalise: forme_str} ex: {"Toulouse": "G,G,G,G,G"}
    """
    if not env_vars:
        print("[WARN] Pas de credentials .env pour l'API LGM")
        return {}
    
    # L'API du calendrier (endpoint a tester)
    urls_to_try = [
        "https://lagrandemelee.midi-olympique.fr/v1/private/calendrier?lg=fr",
        "https://lagrandemelee.midi-olympique.fr/v1/private/journees?lg=fr",
        "https://lagrandemelee.midi-olympique.fr/v1/private/matchs?lg=fr",
    ]
    
    headers = {
        "accept": "application/json",
        "authorization": env_vars.get('API_AUTH_TOKEN', ''),
        "cookie": env_vars.get('API_COOKIES', ''),
        "x-access-key": env_vars.get('API_ACCESS_KEY', '')
    }
    
    for url in urls_to_try:
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                print(f"[OK] API calendrier trouvee: {url}")
                # Analyser la reponse pour extraire la forme
                # (La structure exacte depend de l'API)
                return extraire_forme_depuis_api(data)
        except:
            continue
    
    print("[WARN] API calendrier non trouvee, utilisation des donnees manuelles")
    return {}


def extraire_forme_depuis_api(data):
    """Extrait la forme des equipes depuis les donnees de l'API."""
    formes = {}
    
    # Essayer differentes structures possibles
    if isinstance(data, dict):
        # Chercher des cles comme 'matchs', 'journees', 'calendrier'
        for key in ['matchs', 'journees', 'calendrier', 'rencontres']:
            if key in data:
                items = data[key]
                if isinstance(items, list):
                    for item in items:
                        # Extraire info equipe et forme
                        for club_key in ['equipe', 'club', 'dom', 'ext']:
                            if club_key in item:
                                club_data = item[club_key]
                                if isinstance(club_data, dict):
                                    nom = club_data.get('nom', '')
                                    forme = club_data.get('forme', '')
                                    if nom and forme:
                                        formes[normaliser_nom_club(nom)] = forme
    
    return formes


def creer_classement_manuel():
    """Cree un classement manuel avec les dernieres donnees connues.
    Classement Top 14 2025-2026 - Journee 13 (decembre 2025)
    forme = 5 derniers resultats (G=Gagne, N=Nul, P=Perdu) du plus ancien au plus recent
    Donnees extraites de La Grande Melee
    """
    return {
        "Pau": {"rang": 1, "points": 35, "forme": "P,G,G,G,G"},
        "Toulouse": {"rang": 2, "points": 35, "forme": "G,G,G,G,G"},
        "Bordeaux-Begles": {"rang": 3, "points": 31, "forme": "G,G,P,P,G"},
        "Toulon": {"rang": 4, "points": 29, "forme": "G,G,P,G,P"},
        "Stade francais": {"rang": 5, "points": 27, "forme": "G,P,G,P,N"},
        "Montpellier": {"rang": 6, "points": 25, "forme": "P,P,G,G,G"},
        "La Rochelle": {"rang": 7, "points": 24, "forme": "G,P,P,P,G"},
        "Bayonne": {"rang": 8, "points": 23, "forme": "P,G,P,G,P"},
        "Castres": {"rang": 9, "points": 22, "forme": "P,P,G,G,P"},
        "Racing 92": {"rang": 10, "points": 21, "forme": "G,P,G,P,N"},
        "Clermont": {"rang": 11, "points": 20, "forme": "G,G,P,G,P"},
        "Lyon": {"rang": 12, "points": 18, "forme": "P,P,G,P,P"},
        "Montauban": {"rang": 13, "points": 12, "forme": "G,P,P,P,P"},
        "Perpignan": {"rang": 14, "points": 10, "forme": "P,P,P,P,G"},
    }


def sauvegarder_classement(classement, fichier="classement_top14.json"):
    """Sauvegarde le classement dans un fichier JSON."""
    data = {
        "date_maj": datetime.now().strftime("%Y-%m-%d"),
        "source": "La Grande Melee / manuel",
        "classement": classement
    }
    
    with open(fichier, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"[OK] Classement sauvegarde: {fichier}")


def main():
    print("=" * 60)
    print("SCRAPING CLASSEMENT ET FORME TOP 14")
    print("=" * 60)
    
    # Charger les credentials
    env_vars = charger_env()
    
    # Utiliser le classement manuel comme base
    classement = creer_classement_manuel()
    print(f"[OK] {len(classement)} equipes chargees")
    
    # Essayer de recuperer la forme depuis l'API LGM
    if env_vars:
        print("\nTentative de recuperation de la forme depuis l'API...")
        formes_api = scraper_calendrier_lgm(env_vars)
        
        if formes_api:
            print(f"[OK] Forme recuperee pour {len(formes_api)} equipes")
            # Mettre a jour le classement avec les formes de l'API
            for club, forme in formes_api.items():
                if club in classement:
                    classement[club]['forme'] = forme
        else:
            print("[INFO] Utilisation des formes manuelles")
    else:
        print("[WARN] Pas de .env, utilisation des donnees manuelles")
    
    # Afficher le classement avec forme
    print("\nCLASSEMENT ET FORME:")
    for club, info in sorted(classement.items(), key=lambda x: x[1]['rang']):
        forme = info.get('forme', 'N/A')
        print(f"   {info['rang']:2}. {club:20} - {info['points']:2} pts | {forme}")
    
    # Sauvegarder
    sauvegarder_classement(classement)
    
    print("\n" + "=" * 60)
    print("[OK] TERMINE !")
    print("=" * 60)


if __name__ == "__main__":
    main()
