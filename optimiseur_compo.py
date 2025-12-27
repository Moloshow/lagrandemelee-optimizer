"""
Optimiseur de Composition Fantasy Rugby "La Grande Melee"
Trouve la meilleure equipe sous contrainte de budget.

Usage:
    python optimiseur_compo.py                    # Budget par defaut (300M)
    python optimiseur_compo.py --budget 250       # Budget personnalise
    python optimiseur_compo.py --help             # Aide
"""

import pandas as pd
import argparse
from itertools import combinations
import json

# --- CONFIGURATION ---
FICHIER_JOUEURS = "joueurs_avec_score.csv"
FICHIER_COMPOS = "joueurs_enrichis.csv"  # Avec statut_compo si dispo

# Composition d'equipe Fantasy (15 titulaires + 3 remplacants Fantasy)
# Regles exactes de "La Grande Melee"
COMPOSITION_REQUISE = {
    "lib_pilier": 2,        # 2 piliers
    "lib_talonneur": 1,     # 1 talonneur
    "lib_2emeligne": 2,     # 2 deuxieme ligne
    "lib_3emeligne": 3,     # 3 troisieme ligne
    "lib_12melee": 1,       # 1 demi de melee
    "lib_ouverture": 1,     # 1 demi d'ouverture
    "lib_34centre": 2,      # 2 centres
    "lib_34aile": 2,        # 2 ailiers
    "lib_arriere": 1,       # 1 arriere
}

TOTAL_TITULAIRES = sum(COMPOSITION_REQUISE.values())  # 15
NB_REMPLACANTS_FANTASY = 3  # 3 remplacants Fantasy
TOTAL_JOUEURS = TOTAL_TITULAIRES + NB_REMPLACANTS_FANTASY  # 18


def charger_joueurs(fichier=FICHIER_JOUEURS, fichier_compos=FICHIER_COMPOS):
    """Charge les joueurs avec leurs scores predictifs."""
    print(f"Chargement des joueurs depuis {fichier}")
    
    df = pd.read_csv(fichier, sep=";", encoding="utf-8-sig")
    print(f"   {len(df)} joueurs charges")
    
    # Si on a les statuts de composition, les ajouter
    try:
        if fichier_compos:
            df_compos = pd.read_csv(fichier_compos, sep=";", encoding="utf-8-sig")
            if 'statut_compo' in df_compos.columns:
                df = df.merge(df_compos[['id', 'statut_compo', 'numero_compo']], on='id', how='left')
                print(f"   Statuts de composition ajoutes")
    except:
        pass
    
    return df


def filtrer_joueurs_disponibles(df, inclure_remplacants=False):
    """Filtre les joueurs qui jouent vraiment ce weekend."""
    if 'statut_compo' not in df.columns:
        print("   [WARN] Pas de statut_compo, on garde tous les joueurs")
        return df
    
    if inclure_remplacants:
        mask = df['statut_compo'].isin(['titulaire', 'remplacant'])
    else:
        mask = df['statut_compo'] == 'titulaire'
    
    df_filtre = df[mask].copy()
    print(f"   {len(df_filtre)} joueurs disponibles (titulaires{'+ remplacants' if inclure_remplacants else ''})")
    
    return df_filtre


def optimiser_composition(df, budget, verbose=True):
    """Trouve la meilleure composition sous contrainte de budget."""
    if verbose:
        print(f"\n[OPTIM] Budget: {budget}M")
        print("-" * 40)
    
    composition = []
    budget_restant = budget
    joueurs_utilises = set()
    
    for position, nb_requis in COMPOSITION_REQUISE.items():
        df_pos = df[
            (df['position'] == position) & 
            (~df['id'].isin(joueurs_utilises))
        ].copy()
        
        df_pos = df_pos.sort_values('score_predictif', ascending=False)
        
        selectionnes = 0
        for _, joueur in df_pos.iterrows():
            if selectionnes >= nb_requis:
                break
            
            if joueur['valeur'] <= budget_restant:
                composition.append(joueur)
                joueurs_utilises.add(joueur['id'])
                budget_restant -= joueur['valeur']
                selectionnes += 1
        
        if selectionnes < nb_requis:
            if verbose:
                print(f"   [WARN] {position}: seulement {selectionnes}/{nb_requis} trouves")
    
    df_compo = pd.DataFrame(composition)
    
    if verbose:
        print(f"\n   [OK] {len(df_compo)}/{TOTAL_TITULAIRES} joueurs selectionnes")
        print(f"   Budget utilise: {budget - budget_restant:.1f}M / {budget}M")
        print(f"   Score total: {df_compo['score_predictif'].sum():.1f} pts")
    
    return df_compo, budget_restant


def optimiser_avec_amelioration(df, budget, iterations=100, verbose=True):
    """Optimisation avec amelioration iterative."""
    import random
    
    df_compo, budget_restant = optimiser_composition(df, budget, verbose=False)
    
    if len(df_compo) < TOTAL_TITULAIRES:
        if verbose:
            print("[WARN] Composition incomplete, optimisation limitee")
        return df_compo, budget_restant
    
    meilleur_score = df_compo['score_predictif'].sum()
    budget_utilise = df_compo['valeur'].sum()
    
    if verbose:
        print(f"\n[PHASE 1] Composition initiale: {meilleur_score:.1f} pts, {budget_utilise:.1f}M utilises")
    
    # Phase 2: Upgrade
    if verbose:
        print(f"[PHASE 2] Upgrade des joueurs (budget restant: {budget_restant:.1f}M)...")
    
    amelioration = True
    passes = 0
    max_passes = 20
    
    while amelioration and passes < max_passes:
        amelioration = False
        passes += 1
        
        for idx in range(len(df_compo)):
            joueur_actuel = df_compo.iloc[idx]
            position = joueur_actuel['position']
            
            budget_dispo = budget_restant + joueur_actuel['valeur']
            
            candidats = df[
                (df['position'] == position) &
                (~df['id'].isin(df_compo['id'].values)) &
                (df['valeur'] <= budget_dispo) &
                (df['score_predictif'] > joueur_actuel['score_predictif'])
            ].copy()
            
            if len(candidats) > 0:
                meilleur_candidat = candidats.loc[candidats['score_predictif'].idxmax()]
                
                df_compo = df_compo.drop(df_compo.index[idx]).reset_index(drop=True)
                df_compo = pd.concat([df_compo, pd.DataFrame([meilleur_candidat])], ignore_index=True)
                budget_restant = budget_dispo - meilleur_candidat['valeur']
                amelioration = True
                break
    
    if verbose:
        nouveau_score = df_compo['score_predictif'].sum()
        print(f"   Apres {passes} passes d'upgrade: {nouveau_score:.1f} pts")
    
    # Phase 3: Optimisation aleatoire
    if verbose:
        print(f"[PHASE 3] Optimisation aleatoire ({iterations} tentatives)...")
    
    meilleur_score = df_compo['score_predictif'].sum()
    meilleure_compo = df_compo.copy()
    
    for i in range(iterations):
        if len(df_compo) == 0:
            break
            
        idx_remplacer = random.randint(0, len(df_compo) - 1)
        joueur_actuel = df_compo.iloc[idx_remplacer]
        position = joueur_actuel['position']
        
        budget_dispo = budget_restant + joueur_actuel['valeur']
        
        candidats = df[
            (df['position'] == position) &
            (~df['id'].isin(df_compo['id'].values)) &
            (df['valeur'] <= budget_dispo) &
            (df['score_predictif'] > joueur_actuel['score_predictif'])
        ]
        
        if len(candidats) > 0:
            meilleur_candidat = candidats.loc[candidats['score_predictif'].idxmax()]
            
            nouvelle_compo = df_compo.drop(df_compo.index[idx_remplacer]).reset_index(drop=True)
            nouvelle_compo = pd.concat([nouvelle_compo, pd.DataFrame([meilleur_candidat])], ignore_index=True)
            nouveau_score = nouvelle_compo['score_predictif'].sum()
            
            if nouveau_score > meilleur_score:
                meilleur_score = nouveau_score
                meilleure_compo = nouvelle_compo.copy()
                df_compo = nouvelle_compo
                budget_restant = budget_dispo - meilleur_candidat['valeur']
    
    if verbose:
        budget_final = budget - meilleure_compo['valeur'].sum()
        print(f"   Score final: {meilleur_score:.1f} pts (budget restant: {budget_final:.1f}M)")
    
    return meilleure_compo, budget - meilleure_compo['valeur'].sum()


def selectionner_remplacants_fantasy(df, df_titulaires, budget_restant, nb_remplacants=NB_REMPLACANTS_FANTASY):
    """Selectionne les remplacants Fantasy (3 meilleurs joueurs restants dans le budget)."""
    ids_titulaires = set(df_titulaires['id'].values)
    df_dispo = df[~df['id'].isin(ids_titulaires)].copy()
    
    df_dispo = df_dispo.sort_values('score_predictif', ascending=False)
    
    remplacants = []
    budget = budget_restant
    
    for _, joueur in df_dispo.iterrows():
        if len(remplacants) >= nb_remplacants:
            break
        if joueur['valeur'] <= budget:
            remplacants.append(joueur)
            budget -= joueur['valeur']
    
    df_remplacants = pd.DataFrame(remplacants)
    return df_remplacants, budget


def afficher_composition(df_titulaires, df_remplacants, budget_initial):
    """Affiche la composition complete avec capitaine et supersub."""
    print("\n" + "=" * 70)
    print("COMPOSITION OPTIMALE - LA GRANDE MELEE")
    print("=" * 70)
    
    budget_titulaires = df_titulaires['valeur'].sum()
    budget_remplacants = df_remplacants['valeur'].sum() if len(df_remplacants) > 0 else 0
    budget_total = budget_titulaires + budget_remplacants
    score_titulaires = df_titulaires['score_predictif'].sum()
    
    # Identifier le capitaine (meilleur score titulaire)
    if len(df_titulaires) > 0:
        idx_capitaine = df_titulaires['score_predictif'].idxmax()
        capitaine = df_titulaires.loc[idx_capitaine]
    else:
        capitaine = None
    
    # Identifier le supersub (meilleur score remplacant)
    if len(df_remplacants) > 0:
        idx_supersub = df_remplacants['score_predictif'].idxmax()
        supersub = df_remplacants.loc[idx_supersub]
    else:
        supersub = None
    
    # Afficher les 15 titulaires par position
    print("\nTITULAIRES (15):")
    print("-" * 70)
    for position in COMPOSITION_REQUISE.keys():
        joueurs_pos = df_titulaires[df_titulaires['position'] == position]
        nom_position = position.replace('lib_', '').upper()
        
        for _, j in joueurs_pos.iterrows():
            is_cap = " [CAPITAINE]" if capitaine is not None and j['id'] == capitaine['id'] else ""
            print(f"   {nom_position:12} | {j['nom']:20} | {j['club']:15} | {j['valeur']:5.1f}M | {j['score_predictif']:5.1f} pts{is_cap}")
    
    # Afficher les 3 remplacants Fantasy
    if len(df_remplacants) > 0:
        print("\nREMPLACANTS FANTASY (3):")
        print("-" * 70)
        for _, j in df_remplacants.iterrows():
            is_super = " [SUPERSUB]" if supersub is not None and j['id'] == supersub['id'] else ""
            position = j['position'].replace('lib_', '').upper()
            print(f"   {position:12} | {j['nom']:20} | {j['club']:15} | {j['valeur']:5.1f}M | {j['score_predictif']:5.1f} pts{is_super}")
    
    # Afficher le capitaine et supersub recommandes
    print("\n" + "=" * 70)
    print("RECOMMANDATIONS:")
    if capitaine is not None:
        print(f"   CAPITAINE: {capitaine['nom']} ({capitaine['club']}) - {capitaine['score_predictif']:.1f} pts")
    if supersub is not None:
        print(f"   SUPERSUB:  {supersub['nom']} ({supersub['club']}) - {supersub['score_predictif']:.1f} pts")
    
    # Statistiques
    print("\n" + "-" * 70)
    print(f"Budget: {budget_total:.1f}M / {budget_initial}M (reste {budget_initial - budget_total:.1f}M)")
    print(f"Score titulaires: {score_titulaires:.1f} pts (moyenne: {score_titulaires / len(df_titulaires):.1f} pts)")
    print(f"Effectif: {len(df_titulaires)} titulaires + {len(df_remplacants)} remplacants = {len(df_titulaires) + len(df_remplacants)} joueurs")
    print("=" * 70)


def sauvegarder_composition(df_titulaires, df_remplacants, fichier="ma_composition.csv"):
    """Sauvegarde la composition complete dans un fichier."""
    df_tit = df_titulaires.copy()
    df_tit['role_fantasy'] = 'titulaire'
    
    df_remp = df_remplacants.copy() if len(df_remplacants) > 0 else pd.DataFrame()
    if len(df_remp) > 0:
        df_remp['role_fantasy'] = 'remplacant'
    
    # Identifier capitaine et supersub
    if len(df_tit) > 0:
        idx_cap = df_tit['score_predictif'].idxmax()
        df_tit.loc[idx_cap, 'role_fantasy'] = 'capitaine'
    
    if len(df_remp) > 0:
        idx_super = df_remp['score_predictif'].idxmax()
        df_remp.loc[idx_super, 'role_fantasy'] = 'supersub'
    
    df_total = pd.concat([df_tit, df_remp], ignore_index=True)
    
    colonnes = ['nom', 'nomcomplet', 'club', 'position', 'valeur', 
                'score_predictif', 'adversaire', 'domicile', 'role_fantasy']
    cols = [c for c in colonnes if c in df_total.columns]
    df_total[cols].to_csv(fichier, index=False, sep=";", encoding="utf-8-sig")
    print(f"\n[OK] Composition sauvegardee: {fichier}")


def main():
    parser = argparse.ArgumentParser(description="Optimiseur de Composition Fantasy Rugby")
    parser.add_argument('--budget', type=float, default=300, help='Budget en millions (defaut: 300)')
    parser.add_argument('--remplacants', action='store_true', help='Inclure les remplacants reels dans la pool de joueurs')
    parser.add_argument('--iterations', type=int, default=500, help='Nb iterations optimisation (defaut: 500)')
    parser.add_argument('--output', type=str, default='ma_composition.csv', help='Fichier de sortie')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("OPTIMISEUR DE COMPOSITION - LA GRANDE MELEE")
    print("=" * 70)
    print(f"   Budget: {args.budget}M")
    print(f"   Composition: {TOTAL_TITULAIRES} titulaires + {NB_REMPLACANTS_FANTASY} remplacants = {TOTAL_JOUEURS} joueurs")
    
    # 1. Charger les donnees
    df = charger_joueurs()
    
    # 2. Filtrer les joueurs disponibles
    df = filtrer_joueurs_disponibles(df, inclure_remplacants=args.remplacants)
    
    # 3. Verifier qu'on a des scores predictifs
    if 'score_predictif' not in df.columns:
        print("[ERREUR] Pas de score_predictif. Executez d'abord score_predictif.py")
        return
    
    # 4. Optimiser les 15 titulaires
    df_titulaires, budget_restant = optimiser_avec_amelioration(
        df, args.budget, iterations=args.iterations
    )
    
    # 5. Selectionner les 3 remplacants Fantasy
    df_remplacants, budget_final = selectionner_remplacants_fantasy(
        df, df_titulaires, budget_restant
    )
    
    print(f"\n   [OK] {len(df_titulaires)} titulaires + {len(df_remplacants)} remplacants selectionnes")
    
    # 6. Afficher
    afficher_composition(df_titulaires, df_remplacants, args.budget)
    
    # 7. Sauvegarder
    sauvegarder_composition(df_titulaires, df_remplacants, args.output)
    
    print("\n[OK] Termine !")


if __name__ == "__main__":
    main()
