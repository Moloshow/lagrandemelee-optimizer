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

---

## Utilisation

### Pipeline complet (recommande)

```bash
python main.py --budget 300 --inclure-remplacants
```

Cette commande execute les 5 etapes automatiquement :
1. Scraping des joueurs depuis l'API Fantasy
2. Scraping des compositions depuis AllRugby
3. Mise a jour du classement et forme des equipes
4. Calcul des scores predictifs
5. Optimisation de la composition (18 joueurs)

### Options disponibles

| Option | Description |
|--------|-------------|
| `--budget` | Budget en millions (defaut: 300) |
| `--url-compos` | URL des compositions AllRugby |
| `--skip-scrape` | Utiliser les donnees existantes sans re-scraper |
| `--inclure-remplacants` | Inclure les remplacants reels dans la pool |

### Exemples

```bash
# Budget personnalise
python main.py --budget 250

# Re-run rapide (sans re-scraper)
python main.py --skip-scrape --inclure-remplacants
```

---

## Fichiers du projet

### Scripts Python

| Fichier | Description |
|---------|-------------|
| `main.py` | Pipeline principal - orchestre toutes les etapes |
| `scrape_joueurs.py` | Scrape les joueurs depuis l'API Fantasy |
| `scrape_compos.py` | Scrape les compositions officielles depuis AllRugby |
| `scrape_classement.py` | Genere le classement et forme des equipes |
| `score_predictif.py` | Calcule le score predictif multi-facteurs |
| `optimiseur_compo.py` | Optimise la composition (15 tit + 3 remp) |

### Fichiers de configuration

| Fichier | Description |
|---------|-------------|
| `.env` | Credentials API (non versionne) |
| `.env.example` | Template pour les credentials |
| `classement_top14.json` | Classement et forme des equipes (non versionne) |

### Fichiers generes

| Fichier | Description |
|---------|-------------|
| `joueurs_lagrandemelee_complet.csv` | Tous les joueurs avec stats |
| `joueurs_enrichis.csv` | Joueurs avec statut de composition |
| `joueurs_avec_score.csv` | Joueurs avec score predictif |
| `ma_composition.csv` | Composition optimale (18 joueurs) |

---

## Mise a jour du classement

Le fichier `classement_top14.json` contient le classement et la forme des equipes.

### Generation automatique

```bash
python scrape_classement.py
```

Le script recupere **automatiquement** la forme des equipes via l'API La Grande Melee :
- Endpoint : `/v1/private/journeecalendrier/{journee}`
- Extrait `formeclubdom` et `formeclubext` pour chaque match
- Fallback sur donnees manuelles si l'API n'est pas disponible

### Format du fichier

```json
{
  "date_maj": "2025-12-27",
  "source": "API La Grande Melee",
  "classement": {
    "Pau": {"rang": 1, "points": 35, "forme": "P,G,G,G,G"},
    "Toulouse": {"rang": 2, "points": 35, "forme": "G,G,G,G,G"}
  }
}
```

---

## Formule de scoring

Le score predictif combine 5 facteurs :

```
score = stat_moy x bonus_forme_joueur x bonus_forme_equipe x bonus_domicile x bonus_adversaire
```

### Bonus forme joueur (T/R/N)

Base sur les 5 derniers matchs du joueur (poids decroissant) :

| Statut | Bonus |
|--------|-------|
| T (Titulaire) | +8% |
| R (Remplacant) | 0% |
| N (Non joue) | -15% |

### Bonus forme equipe (G/N/P)

Base sur les 5 derniers resultats de l'equipe :

| Resultat | Bonus |
|----------|-------|
| G (Gagne) | +5% |
| N (Nul) | 0% |
| P (Perdu) | -5% |

Exemple : Toulouse (G,G,G,G,G) = +5% / Perpignan (P,P,P,P,G) = -4%

### Bonus domicile

| Lieu | Bonus |
|------|-------|
| Domicile | +20% |
| Exterieur | 0% |

### Bonus adversaire

Calcule selon le rang de l'adversaire (graduel) :
- Rang 1 (1er) : -13% (equipe forte)
- Rang 7-8 : 0% (neutre)
- Rang 14 (dernier) : +13% (equipe faible)

---

## Resultat

Le script genere une composition de 18 joueurs :

- **15 titulaires** : 2 piliers, 1 talonneur, 2 deuxieme ligne, 3 troisieme ligne, 1 demi de melee, 1 ouverture, 2 centres, 2 ailiers, 1 arriere
- **3 remplacants Fantasy**

Avec recommandations :
- **Capitaine** : Joueur avec le meilleur score parmi les titulaires
- **Supersub** : Joueur avec le meilleur score parmi les remplacants

---

## Licence

Usage personnel uniquement.
