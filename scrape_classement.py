"""
Scraping du classement Top 14
Genere automatiquement le fichier classement_top14.json
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re

# URLs possibles pour le classement
URLS_CLASSEMENT = [
    "https://www.lnr.fr/rugby-top-14/classement",
    "https://www.rugbyrama.fr/rugby/top-14/classement.shtml",
]

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def normaliser_nom_club(nom):
    """Normalise le nom d'un club pour le matching."""
    mapping = {
        "stade toulousain": "Toulouse",
        "toulouse": "Toulouse",
        "union bordeaux begles": "Bordeaux-Begles",
        "bordeaux begles": "Bordeaux-Begles",
        "bordeaux-begles": "Bordeaux-Begles",
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
        "stade francais paris": "Stade francais",
        "usa perpignan": "Perpignan",
        "perpignan": "Perpignan",
        "usap": "Perpignan",
        "rc vannes": "Vannes",
        "vannes": "Vannes",
        "usm montauban": "Montauban",
        "montauban": "Montauban",
    }
    
    nom_lower = nom.lower().strip()
    nom_lower = re.sub(r'[^\w\s]', '', nom_lower)
    
    return mapping.get(nom_lower, nom.title())


def scraper_classement_lnr():
    """Scrape le classement depuis le site de la LNR."""
    url = "https://www.lnr.fr/rugby-top-14/classement"
    
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        classement = {}
        
        # Chercher le tableau de classement
        rows = soup.find_all('tr')
        rang = 0
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 3:
                # Chercher le rang et le nom
                for i, cell in enumerate(cells):
                    text = cell.get_text(strip=True)
                    if text.isdigit() and int(text) <= 14:
                        rang = int(text)
                        # Le nom est souvent dans la cellule suivante
                        if i + 1 < len(cells):
                            nom = cells[i + 1].get_text(strip=True)
                            if nom and len(nom) > 2:
                                nom_norm = normaliser_nom_club(nom)
                                # Chercher les points
                                points = 0
                                for j in range(i + 2, len(cells)):
                                    pts_text = cells[j].get_text(strip=True)
                                    if pts_text.isdigit() and int(pts_text) > 0:
                                        points = int(pts_text)
                                        break
                                
                                classement[nom_norm] = {
                                    "rang": rang,
                                    "points": points
                                }
                        break
        
        return classement
        
    except Exception as e:
        print(f"[ERREUR] Impossible de scraper LNR: {e}")
        return None


def creer_classement_manuel():
    """Cree un classement manuel si le scraping echoue."""
    # Classement approximatif - A METTRE A JOUR MANUELLEMENT
    return {
        "Toulouse": {"rang": 1, "points": 90},
        "Bordeaux-Begles": {"rang": 2, "points": 78},
        "Toulon": {"rang": 3, "points": 72},
        "Bayonne": {"rang": 4, "points": 68},
        "Clermont": {"rang": 5, "points": 63},
        "Castres": {"rang": 6, "points": 63},
        "La Rochelle": {"rang": 7, "points": 62},
        "Pau": {"rang": 8, "points": 61},
        "Montpellier": {"rang": 9, "points": 56},
        "Racing 92": {"rang": 10, "points": 56},
        "Lyon": {"rang": 11, "points": 50},
        "Stade francais": {"rang": 12, "points": 45},
        "Perpignan": {"rang": 13, "points": 44},
        "Montauban": {"rang": 14, "points": 36},
    }


def sauvegarder_classement(classement, fichier="classement_top14.json"):
    """Sauvegarde le classement dans un fichier JSON."""
    data = {
        "date_maj": datetime.now().strftime("%Y-%m-%d"),
        "source": "scraping automatique ou manuel",
        "classement": classement
    }
    
    with open(fichier, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"[OK] Classement sauvegarde: {fichier}")


def main():
    print("=" * 60)
    print("SCRAPING CLASSEMENT TOP 14")
    print("=" * 60)
    
    # Essayer de scraper
    print("\nTentative de scraping du classement...")
    classement = scraper_classement_lnr()
    
    if classement and len(classement) >= 10:
        print(f"[OK] {len(classement)} equipes trouvees par scraping")
    else:
        print("[WARN] Scraping echoue ou incomplet, utilisation du classement manuel")
        classement = creer_classement_manuel()
        print(f"[OK] {len(classement)} equipes (classement manuel)")
    
    # Afficher le classement
    print("\nCLASSEMENT:")
    for club, info in sorted(classement.items(), key=lambda x: x[1]['rang']):
        print(f"   {info['rang']:2}. {club:20} - {info['points']} pts")
    
    # Sauvegarder
    sauvegarder_classement(classement)
    
    print("\n" + "=" * 60)
    print("[OK] TERMINE !")
    print("=" * 60)


if __name__ == "__main__":
    main()
