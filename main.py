"""
Pipeline Automatise - Fantasy Rugby "La Grande Melee"

Ce script orchestre toutes les etapes pour generer une composition optimale :
1. Scrape les joueurs depuis l'API Fantasy
2. Scrape les compositions depuis AllRugby
3. Calcule les scores predictifs
4. Optimise la composition (18 joueurs avec capitaine et supersub)

Usage:
    python main.py                              # Toutes les etapes
    python main.py --url-compos URL             # URL specifique des compos
    python main.py --budget 250                 # Budget personnalise
    python main.py --skip-scrape                # Ne pas re-scraper (utiliser les CSV existants)
"""

import subprocess
import sys
import os
import argparse
from datetime import datetime


def run_script(script_name, args=None, description=""):
    """Execute un script Python et affiche le resultat."""
    print(f"\n{'='*60}")
    print(f"[EXEC] {description}")
    print(f"   Script: {script_name}")
    print(f"{'='*60}")
    
    cmd = [sys.executable, script_name]
    if args:
        cmd.extend(args)
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    if result.returncode != 0:
        print(f"[ERREUR] Erreur lors de l'execution de {script_name}")
        return False
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline Automatise Fantasy Rugby",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--budget', type=float, default=300, 
                       help='Budget en millions (defaut: 300)')
    parser.add_argument('--url-compos', type=str, default=None,
                       help='URL de la page des compositions AllRugby')
    parser.add_argument('--skip-scrape', action='store_true',
                       help='Ne pas re-scraper les donnees (utiliser CSV existants)')
    parser.add_argument('--inclure-remplacants', action='store_true',
                       help='Inclure les remplacants reels dans la pool de joueurs')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("PIPELINE FANTASY RUGBY - LA GRANDE MELEE")
    print("=" * 60)
    print(f"   Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"   Budget: {args.budget}M")
    print(f"   Skip scrape: {args.skip_scrape}")
    
    # Etape 1: Scraper les joueurs Fantasy
    if not args.skip_scrape:
        success = run_script(
            "scrape_joueurs.py",
            description="Etape 1/5 - Scraping des joueurs depuis l'API Fantasy"
        )
        if not success:
            print("[ERREUR] Pipeline interrompu a l'etape 1")
            return 1
    else:
        print("\n[SKIP] Etape 1 ignoree (--skip-scrape)")
    
    # Etape 2: Scraper les compositions AllRugby
    if not args.skip_scrape:
        compo_args = []
        if args.url_compos:
            compo_args.append(args.url_compos)
        
        success = run_script(
            "scrape_compos.py",
            args=compo_args if compo_args else None,
            description="Etape 2/5 - Scraping des compositions AllRugby"
        )
        if not success:
            print("[ERREUR] Pipeline interrompu a l'etape 2")
            return 1
    else:
        print("\n[SKIP] Etape 2 ignoree (--skip-scrape)")
    
    # Etape 3: Scraper/Mettre a jour le classement Top 14
    if not args.skip_scrape:
        success = run_script(
            "scrape_classement.py",
            description="Etape 3/5 - Mise a jour du classement Top 14"
        )
        if not success:
            print("[WARN] Classement non mis a jour, utilisation du fichier existant")
    else:
        print("\n[SKIP] Etape 3 ignoree (--skip-scrape)")
    
    # Etape 4: Calculer les scores predictifs
    success = run_script(
        "score_predictif.py",
        description="Etape 4/5 - Calcul des scores predictifs"
    )
    if not success:
        print("[ERREUR] Pipeline interrompu a l'etape 4")
        return 1
    
    # Etape 5: Optimiser la composition
    optim_args = ["--budget", str(args.budget)]
    if args.inclure_remplacants:
        optim_args.append("--remplacants")
    
    success = run_script(
        "optimiseur_compo.py",
        args=optim_args,
        description="Etape 5/5 - Optimisation de la composition"
    )
    if not success:
        print("[ERREUR] Pipeline interrompu a l'etape 5")
        return 1
    
    # Resume final
    print("\n" + "=" * 60)
    print("[OK] PIPELINE TERMINE AVEC SUCCES !")
    print("=" * 60)
    print("\nFichiers generes:")
    print("   - joueurs_lagrandemelee_complet.csv - Tous les joueurs")
    print("   - joueurs_enrichis.csv - Joueurs avec statut compo")
    print("   - joueurs_avec_score.csv - Joueurs avec score predictif")
    print("   - ma_composition.csv - Composition optimale (18 joueurs)")
    print("\nProchaine etape: Ouvre ma_composition.csv pour voir ta composition !")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
