"""
Scraping des joueurs Fantasy Rugby "La Grande Melee"
Recupere tous les joueurs depuis l'API Fantasy avec leurs statistiques.

Les credentials API sont stockes dans .env (non versionne)
"""

import requests
import pandas as pd
import os


def charger_env():
    """Charge les variables d'environnement depuis .env"""
    env_vars = {}
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    if not os.path.exists(env_path):
        print("[ERREUR] Fichier .env non trouve !")
        print("   Copiez .env.example vers .env et remplissez les valeurs")
        return None
    
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    return env_vars


# --- CONFIGURATION API ---
URL = "https://lagrandemelee.midi-olympique.fr/v1/private/searchjoueurs?lg=fr"


def get_headers(env_vars):
    """Construit les headers avec les credentials du .env"""
    return {
        "authority": "lagrandemelee.midi-olympique.fr",
        "method": "POST",
        "path": "/v1/private/searchjoueurs?lg=fr",
        "scheme": "https",
        "accept": "application/json",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9,fr;q=0.8",
        "authorization": env_vars.get('API_AUTH_TOKEN', ''),
        "content-type": "application/json",
        "cookie": env_vars.get('API_COOKIES', ''),
        "origin": "https://lagrandemelee.midi-olympique.fr",
        "referer": "https://lagrandemelee.midi-olympique.fr/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "x-access-key": env_vars.get('API_ACCESS_KEY', '')
    }


def get_payload(journee="13"):
    """Construit le payload de la requete"""
    return {
        "filters": {
            "nom": "",
            "club": "",
            "position": "",
            "budget_ok": False,
            "valeur_max": 25,
            "engage": False,
            "partant": False,
            "dreamteam": False,
            "quota": "",
            "idj": journee,
            "pageIndex": 0,
            "pageSize": 700,
            "loadSelect": 1,
            "searchonly": 1
        }
    }


def main():
    print("=" * 60)
    print("SCRAPING JOUEURS - LA GRANDE MELEE")
    print("=" * 60)
    
    # Charger les credentials
    env_vars = charger_env()
    if env_vars is None:
        return
    
    print("[OK] Credentials charges depuis .env")
    
    headers = get_headers(env_vars)
    payload = get_payload()
    
    print("Tentative de recuperation de TOUS les joueurs...")
    
    try:
        response = requests.post(URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        if "joueurs" in data:
            liste_joueurs = data["joueurs"]
            total_trouve = len(liste_joueurs)
            print(f"[OK] {total_trouve} joueurs recuperes.")
            
            if total_trouve > 0:
                df = pd.DataFrame(liste_joueurs)
                
                # Extraction de forme_recent
                def extraire_forme(forme_dict):
                    if isinstance(forme_dict, dict) and 'items' in forme_dict:
                        return ','.join(forme_dict['items'])
                    return ''
                
                df['forme_recent'] = df['forme'].apply(extraire_forme)
                
                # Extraction des donnees de match
                def extraire_adversaire(adv_dict):
                    if isinstance(adv_dict, dict) and 'nom' in adv_dict:
                        return adv_dict['nom']
                    return ''
                
                def extraire_domicile(adv_dict):
                    if isinstance(adv_dict, dict) and 'domicile' in adv_dict:
                        return 'domicile' if adv_dict['domicile'] else 'exterieur'
                    return ''
                
                def extraire_date_match(date_str):
                    if date_str and isinstance(date_str, str):
                        try:
                            return date_str.split('T')[0]
                        except:
                            return date_str
                    return ''
                
                if 'adversaire' in df.columns:
                    df['domicile'] = df['adversaire'].apply(extraire_domicile)
                    df['adversaire'] = df['adversaire'].apply(extraire_adversaire)
                
                if 'date_match' in df.columns:
                    df['date_match'] = df['date_match'].apply(extraire_date_match)
                
                print("   Donnees de match extraites (adversaire, domicile, date)")
                
                # Selection des colonnes utiles
                colonnes_utiles = [
                    'id', 'nom', 'nomcomplet', 'club', 'position', 
                    'valeur', 'stat_moy', 'stat_nb', 'pourcentage_selection',
                    'forme_recent', 'adversaire', 'domicile', 'date_match'
                ]
                
                cols_finales = [c for c in colonnes_utiles if c in df.columns]
                df_clean = df[cols_finales]
                
                # Sauvegarde du fichier global
                fichier_global = os.path.join(os.path.dirname(__file__), "output", "joueurs_lagrandemelee_complet.csv")
                os.makedirs(os.path.dirname(fichier_global), exist_ok=True)
                df_clean.to_csv(fichier_global, index=False, sep=";", encoding="utf-8-sig")
                print(f"[OK] Fichier global sauvegarde : {fichier_global}")
                
                # Afficher top 5
                print("\n--- Top 5 des joueurs recuperes ---")
                print(df_clean[['nom', 'valeur', 'club']].head(5))
                
        else:
            print("[ERREUR] Cle 'joueurs' non trouvee dans la reponse.")
            print("Cles disponibles:", data.keys())
            
    except requests.exceptions.RequestException as e:
        print(f"[ERREUR] Requete echouee: {e}")
    
    print("\n" + "=" * 60)
    print("[OK] TERMINE !")
    print("=" * 60)


if __name__ == "__main__":
    main()
