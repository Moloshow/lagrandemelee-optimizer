"""
Script de scoring predictif Fantasy Rugby "La Grande Melee"
Calcule un score predictif pour chaque joueur base sur:
- stat_moy (performance moyenne)
- forme recente (T=Titulaire, R=Remplacant, N=Non joue)
- adversaire (force de l'equipe adverse)
- domicile/exterieur
"""

import pandas as pd
import json
import os

# --- CONFIGURATION ---
FICHIER_JOUEURS = "joueurs_lagrandemelee_complet.csv"
FICHIER_CLASSEMENT = "classement_top14.json"
FICHIER_SORTIE = "joueurs_avec_score.csv"

# Bonus/Malus pour le score predictif
BONUS_DOMICILE = 1.20     # +20% a domicile
BONUS_EXTERIEUR = 1.0     # 0% a l'exterieur (neutre)

# Bonus adversaire graduel base sur le rang
# Rang 1 (meilleur) = malus, Rang 14 (dernier) = bonus
# Formule: bonus = 1 + (rang - 7.5) * FACTEUR_RANG
# Ex: Rang 1 = 1 + (1-7.5)*0.02 = 0.87 (-13%)
# Ex: Rang 14 = 1 + (14-7.5)*0.02 = 1.13 (+13%)
FACTEUR_RANG_ADVERSAIRE = 0.02  # 2% par rang d'ecart avec le milieu

# Bonus forme recente (T=Titulaire, R=Remplacant, N=Non joue)
BONUS_FORME = {
    "T": 1.08,   # Titulaire recent = +8%
    "R": 1.0,    # Remplacant = neutre
    "N": 0.85    # N'a pas joue = -15%
}


def charger_classement(fichier=FICHIER_CLASSEMENT):
    """Charge le fichier JSON de classement."""
    print(f"Chargement du classement depuis {fichier}")
    
    if not os.path.exists(fichier):
        print(f"[WARN] Fichier {fichier} non trouve. Utilisation de valeurs par defaut.")
        return {}
    
    with open(fichier, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    classement = data.get("classement", {})
    print(f"   {len(classement)} equipes chargees")
    return classement


def calculer_bonus_forme(forme_str):
    """
    Calcule le bonus de forme base sur les derniers matchs.
    forme_str: "T,T,N,T,R" 
    Poids decroissant : le dernier match compte plus.
    """
    if not forme_str or pd.isna(forme_str):
        return 1.0
    
    items = forme_str.split(',')
    if not items:
        return 1.0
    
    # Poids decroissants (le plus recent compte plus)
    poids = [1.0, 0.7, 0.5, 0.3, 0.1]  # 5 derniers matchs, plus forte ponderation recente
    
    total_bonus = 0
    total_poids = 0
    
    for i, item in enumerate(reversed(items[-5:])):  # 5 derniers
        if i < len(poids):
            bonus = BONUS_FORME.get(item.strip(), 1.0)
            total_bonus += bonus * poids[i]
            total_poids += poids[i]
    
    if total_poids == 0:
        return 1.0
    
    return total_bonus / total_poids


def calculer_bonus_adversaire(rang_adversaire):
    """
    Calcule le bonus adversaire base sur le rang.
    Rang 1 (1er) = equipe forte = malus
    Rang 14 (dernier) = equipe faible = bonus
    """
    if rang_adversaire == 0:
        return 1.0  # Inconnu
    
    # Centre sur rang 7.5 (milieu de tableau)
    bonus = 1 + (rang_adversaire - 7.5) * FACTEUR_RANG_ADVERSAIRE
    
    # Limiter entre 0.80 et 1.20
    return max(0.80, min(1.20, bonus))


# Bonus forme equipe (G=Gagne, N=Nul, P=Perdu) - Format La Grande Melee
BONUS_FORME_EQUIPE = {
    "G": 1.05,   # Gagne = +5%
    "N": 1.0,    # Nul = neutre
    "P": 0.95    # Perdu = -5%
}


def calculer_bonus_forme_equipe(forme_str):
    """
    Calcule le bonus de forme de l'equipe du joueur.
    forme_str: "V,V,D,V,D" (5 derniers resultats)
    Poids decroissant : le dernier resultat compte plus.
    """
    if not forme_str or pd.isna(forme_str):
        return 1.0
    
    items = forme_str.split(',')
    if not items:
        return 1.0
    
    # Poids decroissants (le plus recent compte plus)
    poids = [1.0, 0.7, 0.5, 0.3, 0.1]
    
    total_bonus = 0
    total_poids = 0
    
    for i, item in enumerate(reversed(items[-5:])):
        if i < len(poids):
            bonus = BONUS_FORME_EQUIPE.get(item.strip().upper(), 1.0)
            total_bonus += bonus * poids[i]
            total_poids += poids[i]
    
    if total_poids == 0:
        return 1.0
    
    return total_bonus / total_poids


def calculer_score_predictif(row, classement):
    """
    Calcule le score predictif pour un joueur.
    Score = stat_moy x bonus_forme_joueur x bonus_forme_equipe x bonus_domicile x bonus_adversaire
    """
    stat_moy = row.get('stat_moy', 0)
    if pd.isna(stat_moy) or stat_moy == 0:
        return 0.0
    
    # Bonus forme joueur
    forme_recent = row.get('forme_recent', '')
    bonus_forme_joueur = calculer_bonus_forme(forme_recent)
    
    # Bonus forme equipe (dynamique de l'equipe)
    club = row.get('club', '')
    info_club = classement.get(club, {})
    forme_equipe = info_club.get('forme', '')
    bonus_forme_equipe = calculer_bonus_forme_equipe(forme_equipe)
    
    # Bonus domicile/exterieur
    domicile = row.get('domicile', '')
    if domicile == 'domicile':
        bonus_lieu = BONUS_DOMICILE
    else:
        bonus_lieu = BONUS_EXTERIEUR
    
    # Bonus adversaire (graduel par rang)
    adversaire = row.get('adversaire', '')
    info_adv = classement.get(adversaire, {})
    rang_adv = info_adv.get('rang', 0)
    bonus_adv = calculer_bonus_adversaire(rang_adv)
    
    # Score final
    score = stat_moy * bonus_forme_joueur * bonus_forme_equipe * bonus_lieu * bonus_adv
    
    return round(score, 2)


def calculer_rapport_qualite_prix(row):
    """
    Calcule le rapport qualite/prix = score_predictif / valeur
    Plus c'est eleve, meilleur est le deal.
    """
    score = row.get('score_predictif', 0)
    valeur = row.get('valeur', 1)
    
    if pd.isna(valeur) or valeur == 0:
        return 0.0
    
    return round(score / valeur, 2)


def main():
    print("=" * 60)
    print("CALCUL DES SCORES PREDICTIFS - LA GRANDE MELEE")
    print("=" * 60)
    
    # 1. Charger les donnees
    print(f"\nChargement des joueurs depuis {FICHIER_JOUEURS}")
    df = pd.read_csv(FICHIER_JOUEURS, sep=";", encoding="utf-8-sig")
    print(f"   {len(df)} joueurs charges")
    
    # 2. Charger le classement
    classement = charger_classement()
    
    # 3. Calculer les scores
    print("\nCalcul des scores predictifs...")
    df['score_predictif'] = df.apply(lambda row: calculer_score_predictif(row, classement), axis=1)
    df['rapport_qp'] = df.apply(calculer_rapport_qualite_prix, axis=1)
    
    # 4. Ajouter info adversaire
    df['force_adversaire'] = df['adversaire'].apply(
        lambda adv: classement.get(adv, {}).get('force', 'inconnu')
    )
    df['rang_adversaire'] = df['adversaire'].apply(
        lambda adv: classement.get(adv, {}).get('rang', 0)
    )
    
    # 5. Statistiques
    print("\nSTATISTIQUES:")
    print(f"   Score predictif moyen: {df['score_predictif'].mean():.2f}")
    print(f"   Score max: {df['score_predictif'].max():.2f}")
    print(f"   Joueurs avec score > 30: {len(df[df['score_predictif'] > 30])}")
    
    # 6. Top 10 joueurs par score predictif
    print("\nTOP 10 JOUEURS (Score Predictif):")
    top10 = df.nlargest(10, 'score_predictif')[['nom', 'club', 'position', 'valeur', 'stat_moy', 'adversaire', 'domicile', 'score_predictif', 'rapport_qp']]
    print(top10.to_string(index=False))
    
    # 7. Top 10 meilleurs rapports qualite/prix
    print("\nTOP 10 RAPPORT QUALITE/PRIX:")
    df_valides = df[df['score_predictif'] > 15]
    top10_qp = df_valides.nlargest(10, 'rapport_qp')[['nom', 'club', 'position', 'valeur', 'score_predictif', 'rapport_qp']]
    print(top10_qp.to_string(index=False))
    
    # 8. Sauvegarder
    colonnes_export = [
        'id', 'nom', 'nomcomplet', 'club', 'position',
        'valeur', 'stat_moy', 'stat_nb', 'forme_recent',
        'adversaire', 'domicile', 'date_match',
        'force_adversaire', 'rang_adversaire',
        'score_predictif', 'rapport_qp'
    ]
    cols_finales = [c for c in colonnes_export if c in df.columns]
    
    df[cols_finales].to_csv(FICHIER_SORTIE, index=False, sep=";", encoding="utf-8-sig")
    print(f"\n[OK] Fichier sauvegarde: {FICHIER_SORTIE}")
    
    print("\n" + "=" * 60)
    print("[OK] TERMINE !")
    print("=" * 60)


if __name__ == "__main__":
    main()
