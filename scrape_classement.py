"""
Scraping du classement Top 14 et forme des equipes
Genere automatiquement le fichier classement_top14.json
Recupere la forme des equipes depuis l'API La Grande Melee
"""

import requests
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
        "bordeaux-bègles": "Bordeaux-Begles",
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
    nom_lower = re.sub(r'[^\w\s-]', '', nom_lower)
    
    return mapping.get(nom_lower, nom.title())


def scraper_forme_equipes_lgm(env_vars, journee=13):
    """
    Scrape la forme des equipes depuis l'API La Grande Melee.
    Endpoint: /v1/private/journeecalendrier/{journee}?lg=fr
    Retourne un dict {club_normalise: forme_str} ex: {"Toulouse": "G,G,G,G,G"}
    """
    if not env_vars:
        print("[WARN] Pas de credentials .env pour l'API LGM")
        return {}
    
    url = f"https://lagrandemelee.midi-olympique.fr/v1/private/journeecalendrier/{journee}?lg=fr"
    
    headers = {
        "accept": "application/json",
        "authorization": env_vars.get('API_AUTH_TOKEN', ''),
        "cookie": env_vars.get('API_COOKIES', ''),
        "x-access-key": env_vars.get('API_ACCESS_KEY', ''),
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        formes = {}
        
        if 'journee' in data and 'matchs' in data['journee']:
            matchs = data['journee']['matchs']
            
            for match in matchs:
                # Equipe domicile
                club_dom = match.get('clubdom', '')
                forme_dom = match.get('formeclubdom', [])
                if club_dom and forme_dom:
                    club_norm = normaliser_nom_club(club_dom)
                    formes[club_norm] = ','.join(forme_dom)
                
                # Equipe exterieur
                club_ext = match.get('clubext', '')
                forme_ext = match.get('formeclubext', [])
                if club_ext and forme_ext:
                    club_norm = normaliser_nom_club(club_ext)
                    formes[club_norm] = ','.join(forme_ext)
        
        if formes:
            print(f"[OK] Forme recuperee pour {len(formes)} equipes via API LGM")
        
        return formes
        
    except requests.exceptions.RequestException as e:
        print(f"[WARN] Erreur API calendrier: {e}")
        return {}
    except Exception as e:
        print(f"[WARN] Erreur parsing calendrier: {e}")
        return {}


def creer_classement_manuel():
    """Cree un classement manuel avec les dernieres donnees connues.
    Classement Top 14 2025-2026 - Journee 13 (decembre 2025)
    """
    return {
        "Pau": {"rang": 1, "points": 35},
        "Toulouse": {"rang": 2, "points": 35},
        "Bordeaux-Begles": {"rang": 3, "points": 31},
        "Toulon": {"rang": 4, "points": 29},
        "Stade francais": {"rang": 5, "points": 27},
        "Montpellier": {"rang": 6, "points": 25},
        "La Rochelle": {"rang": 7, "points": 24},
        "Bayonne": {"rang": 8, "points": 23},
        "Castres": {"rang": 9, "points": 22},
        "Racing 92": {"rang": 10, "points": 21},
        "Clermont": {"rang": 11, "points": 20},
        "Lyon": {"rang": 12, "points": 18},
        "Montauban": {"rang": 13, "points": 12},
        "Perpignan": {"rang": 14, "points": 10},
    }


def sauvegarder_classement(classement, fichier="classement_top14.json"):
    """Sauvegarde le classement dans un fichier JSON."""
    data = {
        "date_maj": datetime.now().strftime("%Y-%m-%d"),
        "source": "API La Grande Melee",
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
    
    # Recuperer la forme depuis l'API LGM
    if env_vars:
        print("\nRecuperation de la forme des equipes via API LGM...")
        formes_api = scraper_forme_equipes_lgm(env_vars, journee=13)
        
        if formes_api:
            # Mettre a jour le classement avec les formes de l'API
            for club, forme in formes_api.items():
                if club in classement:
                    classement[club]['forme'] = forme
                else:
                    # Club trouve mais pas dans le classement de base
                    print(f"   [INFO] Club trouve dans API mais pas dans classement: {club}")
        else:
            print("[WARN] API non disponible, utilisation des formes par defaut")
            # Ajouter des formes par defaut
            formes_defaut = {
                "Pau": "P,G,G,G,G",
                "Toulouse": "G,G,G,G,G",
                "Bordeaux-Begles": "G,G,P,P,G",
                "Toulon": "G,G,P,G,P",
                "Stade francais": "G,P,G,P,N",
                "Montpellier": "P,P,G,G,G",
                "La Rochelle": "G,P,P,P,G",
                "Bayonne": "P,G,P,G,P",
                "Castres": "P,P,G,G,P",
                "Racing 92": "G,P,G,P,N",
                "Clermont": "G,G,P,G,P",
                "Lyon": "P,P,G,P,P",
                "Montauban": "G,P,P,P,P",
                "Perpignan": "P,P,P,P,G",
            }
            for club, forme in formes_defaut.items():
                if club in classement:
                    classement[club]['forme'] = forme
    else:
        print("[WARN] Pas de .env, utilisation des donnees par defaut")
    
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
