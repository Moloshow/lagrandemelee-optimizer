# Fantasy Rugby Optimizer - La Grande Melee

Optimiseur de composition pour le Fantasy Rugby "La Grande Melee" (Top 14).

Genere automatiquement la meilleure equipe de 18 joueurs en fonction du budget, des compositions officielles, et de multiples facteurs predictifs.

---

## Table des matieres

- [Installation](#installation)
- [Configuration des credentials](#configuration-des-credentials)
- [Utilisation](#utilisation)
- [Fichiers du projet](#fichiers-du-projet)
- [Mise a jour du classement](#mise-a-jour-du-classement)
- [Formule de scoring](#formule-de-scoring)

---

## Installation

### 1. Cloner le repository

```bash
git clone https://github.com/Moloshow/lagrandemelee-optimizer.git
cd lagrandemelee-optimizer
```

### 2. Installer les dependances

```bash
pip install pandas requests beautifulsoup4 unidecode
```

---

## Configuration des credentials

Le script necessite des credentials pour acceder a l'API "La Grande Melee".

### 1. Copier le template

```bash
cp .env.example .env
```

### 2. Recuperer vos credentials

1. Connectez-vous sur [lagrandemelee.midi-olympique.fr](https://lagrandemelee.midi-olympique.fr/)
2. Ouvrez les Developer Tools (F12) > Onglet "Network"
3. Actualisez la page et cherchez une requete vers `searchjoueurs`
4. Dans les Headers de la requete, copiez :
   - `authorization` : Token JWT (commence par "Token eyJ...")
   - `cookie` : Chaine de cookies complete
   - `x-access-key` : Cle d'acces (format "XXX@XX.XX@@...")

### 3. Remplir le fichier .env

```env
API_AUTH_TOKEN=Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
API_COOKIES=_ga=GA1.1...; __stripe_mid=...; ...
API_ACCESS_KEY=740@16.17@@d50f0d9f-...
```

> **Note** : Le fichier `.env` est ignore par git et ne sera jamais pousse.

---

## Utilisation

### Pipeline complet (recommande)

```bash
python main.py --budget 300 --inclure-remplacants
```

Cette commande execute les 4 etapes automatiquement :
1. Scrape les joueurs depuis l'API Fantasy
2. Scrape les compositions depuis AllRugby
3. Calcule les scores predictifs
4. Optimise la composition (18 joueurs)

### Options disponibles

| Option | Description |
|--------|-------------|
| `--budget` | Budget en millions (defaut: 300) |
| `--url-compos` | URL des compositions AllRugby (si non trouvee auto) |
| `--skip-scrape` | Utiliser les donnees existantes sans re-scraper |
| `--inclure-remplacants` | Inclure les remplacants reels dans la pool |

### Exemples

```bash
# Budget personnalise
python main.py --budget 250

# Avec URL specifique des compositions
python main.py --url-compos "https://www.allrugby.com/news/top-14-2026-j13-compos-3447.html"

# Re-run rapide (sans re-scraper)
python main.py --skip-scrape --inclure-remplacants
```

### Scripts individuels

```bash
python scrape_joueurs.py         # Scrape API Fantasy
python scrape_compos.py [URL]    # Scrape compositions AllRugby
python score_predictif.py        # Calcule les scores predictifs
python optimiseur_compo.py       # Optimise la composition
```

---

## Fichiers du projet

### Scripts Python

| Fichier | Description |
|---------|-------------|
| `main.py` | Pipeline principal - orchestre toutes les etapes |
| `scrape_joueurs.py` | Scrape les joueurs depuis l'API Fantasy |
| `scrape_compos.py` | Scrape les compositions officielles depuis AllRugby |
| `score_predictif.py` | Calcule un score predictif pour chaque joueur |
| `optimiseur_compo.py` | Trouve la meilleure equipe sous contrainte de budget |

### Fichiers de configuration

| Fichier | Description |
|---------|-------------|
| `.env` | Credentials API (non versionne) |
| `.env.example` | Template pour les credentials |
| `classement_top14.json` | Classement actuel des equipes (non versionne) |

### Fichiers generes (non versionnes)

| Fichier | Description |
|---------|-------------|
| `joueurs_lagrandemelee_complet.csv` | Tous les joueurs avec stats |
| `joueurs_enrichis.csv` | Joueurs avec statut de composition |
| `joueurs_avec_score.csv` | Joueurs avec score predictif |
| `ma_composition.csv` | Composition optimale (18 joueurs) |

---

## Mise a jour du classement

Le fichier `classement_top14.json` doit etre cree et mis a jour manuellement apres chaque journee.

### Format du fichier

```json
{
  "journee": 13,
  "date_maj": "2025-12-26",
  "classement": {
    "Pau": {"rang": 1, "points": 35, "force": "fort"},
    "Toulouse": {"rang": 2, "points": 33, "force": "fort"},
    "Bordeaux-Begles": {"rang": 3, "points": 31, "force": "fort"},
    "La Rochelle": {"rang": 4, "points": 29, "force": "fort"},
    "Toulon": {"rang": 5, "points": 27, "force": "moyen"},
    "Racing 92": {"rang": 6, "points": 25, "force": "moyen"},
    "Clermont": {"rang": 7, "points": 23, "force": "moyen"},
    "Stade francais": {"rang": 8, "points": 22, "force": "moyen"},
    "Castres": {"rang": 9, "points": 21, "force": "moyen"},
    "Bayonne": {"rang": 10, "points": 20, "force": "moyen"},
    "Lyon": {"rang": 11, "points": 18, "force": "faible"},
    "Montpellier": {"rang": 12, "points": 16, "force": "faible"},
    "Montauban": {"rang": 13, "points": 10, "force": "faible"},
    "Perpignan": {"rang": 14, "points": 8, "force": "faible"}
  }
}
```

### Champs

- `rang` : Position au classement (1 = 1er)
- `points` : Points au classement
- `force` : Categorie de force ("fort", "moyen", "faible")

Le bonus adversaire est calcule de maniere graduelle en fonction du rang.

---

## Formule de scoring

Le score predictif est calcule ainsi :

```
score = stat_moy x bonus_forme x bonus_domicile x bonus_adversaire
```

### Bonus domicile

| Lieu | Bonus |
|------|-------|
| Domicile | +20% |
| Exterieur | 0% |

### Bonus adversaire (graduel)

Calcule selon le rang de l'adversaire :
- Rang 1 (1er) : -13% (equipe forte)
- Rang 7-8 : 0% (neutre)
- Rang 14 (dernier) : +13% (equipe faible)

### Bonus forme

Basee sur les 5 derniers matchs (poids decroissant) :

| Statut | Bonus |
|--------|-------|
| T (Titulaire) | +8% |
| R (Remplacant) | 0% |
| N (Non joue) | -15% |

---

## Resultat

Le script genere une composition de 18 joueurs :
- **15 titulaires** (2 piliers, 1 talonneur, 2 deuxieme ligne, 3 troisieme ligne, 1 demi de melee, 1 ouverture, 2 centres, 2 ailiers, 1 arriere)
- **3 remplacants Fantasy**

Avec recommandation de :
- **Capitaine** : Joueur avec le meilleur score parmi les titulaires
- **Supersub** : Joueur avec le meilleur score parmi les remplacants

---

## Licence

Usage personnel uniquement.
