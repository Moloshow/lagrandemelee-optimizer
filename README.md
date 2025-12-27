# Fantasy Rugby - La Grande Melee

Systeme d'optimisation de composition pour le Fantasy Rugby "La Grande Melee".

## Installation

```bash
# Cloner le repo
git clone <url>
cd lagrandemelee

# Installer les dependances
pip install pandas requests beautifulsoup4 unidecode
```

## Utilisation

### Pipeline complet (recommande)
```bash
python main.py --budget 300 --inclure-remplacants
```

### Options
| Option | Description |
|--------|-------------|
| `--budget` | Budget en millions (defaut: 300) |
| `--url-compos` | URL des compositions AllRugby |
| `--skip-scrape` | Ne pas re-scraper (utiliser CSV existants) |
| `--inclure-remplacants` | Inclure les remplacants reels |

### Scripts individuels
```bash
python scrape_joueurs.py         # 1. Scrape API Fantasy
python scrape_compos.py URL      # 2. Scrape compositions AllRugby
python score_predictif.py        # 3. Calcule scores predictifs
python optimiseur_compo.py       # 4. Optimise la composition
```

## Fonctionnalites

- **Scraping API Fantasy** : Recupere tous les joueurs avec stats
- **Scraping AllRugby** : Recupere les compositions officielles (titulaires/remplacants)
- **Score predictif** : Calcule un score base sur forme, adversaire, domicile
- **Optimisation** : Trouve la meilleure equipe de 18 joueurs sous contrainte de budget
- **Capitaine & Supersub** : Recommandation automatique

## Formule de scoring

```
score = stat_moy x bonus_forme x bonus_domicile x bonus_adversaire
```

- **Domicile** : +20%
- **Adversaire** : graduel par rang (2% par rang d'ecart)
- **Forme** : T=+8%, R=0%, N=-15%

## Structure

```
lagrandemelee/
├── main.py                 # Pipeline principal
├── scrape_joueurs.py       # Scraping API Fantasy
├── scrape_compos.py        # Scraping AllRugby
├── score_predictif.py      # Calcul scores
├── optimiseur_compo.py     # Optimisation
└── classement_top14.json   # Classement (a mettre a jour)
```

## Notes

- Le fichier `classement_top14.json` doit etre mis a jour manuellement apres chaque journee
- Les credentials API sont dans `scrape_joueurs.py` (token, cookies)

## Licence

Usage personnel uniquement.
