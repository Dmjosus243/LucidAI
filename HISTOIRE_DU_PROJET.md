# LucidAI — L'histoire d'un projet

> **L'audit financier par intelligence artificielle, fait pour l'Afrique francophone.**

*Un récit personnel de la genèse du projet : l'inspiration, la montée en compétence en Python, l'architecture construite, et les obstacles surmontés en chemin.*

---

## Table des matières

1. [L'inspiration : pourquoi ce projet ?](#linspiration--pourquoi-ce-projet-)
2. [Le problème que je veux résoudre](#le-problème-que-je-veux-résoudre)
3. [Ce que j'ai appris de Python](#ce-que-jai-appris-de-python)
4. [Comment je l'ai construit](#comment-je-lai-construit)
5. [Les formules mathématiques au cœur du moteur](#les-formules-mathématiques-au-cœur-du-moteur)
6. [Les difficultés rencontrées](#les-difficultés-rencontrées)
7. [Et maintenant ?](#et-maintenant-)
8. [Résumé en chiffres](#résumé-en-chiffres)

---

## L'inspiration : pourquoi ce projet ?

Tout est parti d'une observation simple mais frappante. Autour de moi, au **Congo** et en **Afrique francophone**, les cabinets comptables et les PME traitaient des **milliers d'écritures comptables chaque mois** à la main ou avec des outils importés qu'ils ne pouvaient ni financer, ni vraiment adapter à leur réalité.

Les grandes solutions d'audit (MindBridge, Oversight, ou les suites des Big Four) sont formidables… mais elles coûtent **entre 15 000 et 460 000 € par an**, exigent des **implémentations lourdes**, parlent **anglais**, et sont calées sur des normes **SOX, IFRS ou PCAOB**. Pour un cabinet congolais, c'était tout simplement **hors de portée**.

L'idée a germé : et si on créait un outil qui fait la même chose — détecter des **fraudes et des anomalies financières** — mais qui soit :

- pensé pour les normes **SYSCOHADA / OHADA** ;
- en **français**, avec le vocabulaire local ;
- **sans configuration**, avec un résultat en moins de 60 secondes ;
- payable en **Mobile Money** (Orange Money, M-Pesa, Airtel) via **MaishaPay** ;
- **accessible financièrement** aux cabinets et PME locales.

Mon envie était de **démocratiser le contrôle interne**. La technologie existe déjà, mais elle n'est pas arrivée jusqu'aux cabinets et aux PME d'Afrique francophone. LucidAI est ma tentative de combler ce fossé.

---

## Le problème que je veux résoudre

Chaque mois, un cabinet comptable doit contrôler des centaines, parfois des milliers d'écritures. Cette tâche est :

- **Cronophage** : passer ligne par ligne prend des heures, voire des jours.
- **Inefficace** : les contrôles manuels ne détectent qu'une fraction des anomalies (biais d'échantillonnage).
- **Coûteux** : une fraude non détectée peut coûter très cher à une entreprise.

L'objectif : **analyser 100 % des transactions** (pas un échantillon), repérer les anomalies en quelques secondes, et produire un **rapport clair** que tout le monde peut comprendre et utiliser.

---

## Ce que j'ai appris de Python

Ce projet a été mon **terrain d'apprentissage le plus riche en Python**. Voici ce que j'ai réellement appris en le construisant :

### 1. Manipulation de données avec **pandas** et **NumPy**
Le cœur du projet repose sur la manipulation de DataFrames. J'ai appris à :
- charger et normaliser des fichiers Excel/CSV ;
- filtrer des lignes selon des conditions (doublons, seuils, négatifs) ;
- appliquer des fonctions vectorisées sans écrire de boucles lentes ;

```python
# Détection de transactions en double (même montant + date + fournisseur)
dupes = df[df.duplicated(subset=["amount", "date", "vendor"], keep=False)]
```

### 2. Le calcul vectoriel avec NumPy
J'ai découvert que **Python brille** pour l'analyse statistique grâce à NumPy, qui travaille sur des tableaux entiers sans boucle explicite :

```python
import numpy as np
mean = amount.mean()
std = amount.std()
zscores = ((amount - mean) / std).abs()
outliers = df[zscores >= 3]
```

### 3. La gestion des données manquantes (NaN)
Un fichier réel contient **toujours** des cellules vides. J'ai appris à les gérer proprement pour que le JSON ne contienne pas de `NaN` invalide :

```python
def _safe_dict(row):
    d = row.to_dict()
    return {
        k: (None if isinstance(v, float) and np.isnan(v) else v)
        for k, v in d.items()
    }
```

### 4. L'architecture orientée objet
J'ai structuré le moteur en **classes** avec des méthodes statiques séparées par responsabilité (moteur de règles, moteur statistique, moteur de fractionnement, moteur de décision) :

```python
class RulesEngine:
    @staticmethod
    def _rule_engine(df): ...        # Moteur 1 : règles déterministes
    @staticmethod
    def _statistical_engine(df): ... # Moteur 2 : analyse statistique
    @staticmethod
    def _splitting_engine(df): ...   # Moteur 3 : fractionnement de seuil
    @staticmethod
    def detect_anomalies(df): ...    # Orchestrateur / décision
```

### 5. L'integration avec FastAPI et une base de données
Au-delà du calcul, j'ai appris à exposer le moteur via une **API REST (FastAPI)**, à le connecter à une **base de données Postgres (Supabase)** avec SQLAlchemy, et à gérer l'authentification.

---

## Comment je l'ai construit

L'architecture est volontairement **simple et modulaire**. Voici les briques principales :

### L'architecture générale

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                      │
│        Landing · Connexion · Dashboard · Organisation        │
│        Équipe · Admin · Abonnement                           │
└──────────────────────────────┬──────────────────────────────┘
                               │ API (Axios)
┌──────────────────────────────▼──────────────────────────────┐
│                        BACKEND (FastAPI)                     │
│   auth · users · upload · analysis · reports · admin         │
│   billing (MaishaPay)                                        │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│              MOTEUR DE DÉTECTION (Python)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ Règles       │  │ Statistique  │  │ Fractionne-  │        │
│  │ déterministes│  │ (z-score)    │  │ ment de seuil│        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         └─────────────────┴────────┬────────┘                │
│                            ┌──────▼──────┐                    │
│                            │ Moteur de   │                    │
│                            │ décision    │                    │
│                            └─────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

### Le flux d'une analyse

1. L'utilisateur **importe un fichier** Excel/CSV (upload).
2. Le fichier est converti en `DataFrame` pandas.
3. Le **moteur de règles** détecte les motifs connus (doublons, montants ronds, TVA invalide, fournisseurs à risque, transactions négatives).
4. Le **moteur statistique** repère les montants hors norme (via le z-score).
5. Le **moteur de fractionnement** repère les petits paiements cumulés qui contournent les seuils.
6. Le **moteur de décision** fusionne les résultats, attribue un **score de confiance** et un **niveau de sévérité**.
7. Un **score de risque global** est calculé.
8. Le tout est renvoyé à l'interface et un **rapport PDF** peut être généré.

### La stack technique

| Couche | Technologie |
|--------|-------------|
| Frontend | React + TypeScript + Tailwind CSS + Vite |
| Backend | Python + FastAPI + Uvicorn |
| Modèle | pandas + NumPy (sans dépendances lourdes d'apprentissage) |
| Base de données | PostgreSQL hébergée sur Supabase |
| Authentification | JWT (JSON Web Tokens) |
| Paiement | MaishaPay (Mobile Money + carte) |

> **Choix délibéré :** je n'ai pas ajouté `scikit-learn` pour le machine learning. J'ai implémenté l'analyse statistique **à la main avec NumPy** pour garder le projet léger, compréhensible et déployable partout. C'est un choix que je peux faire évoluer plus tard (Isolation Forest, PCA, etc.).

---

## Les formules mathématiques au cœur du moteur

Le moteur repose sur quelques formules mathématiques que je vais détailler ici (rendues en LaTeX).

### 1. Le score z (écart-type / valeur hors norme)

Le **z-score** mesure de combien d'écarts-types une transaction $x$ s'écarte de la moyenne $\bar{x}$ de l'ensemble des transactions :

$$
z = \frac{x - \bar{x}}{\sigma}
$$

où $\bar{x}$ est la **moyenne** et $\sigma$ l'**écart-type** :

$$
\bar{x} = \frac{1}{n}\sum_{i=1}^{n} x_i, \qquad
\sigma = \sqrt{\frac{1}{n}\sum_{i=1}^{n} (x_i - \bar{x})^2}
$$

Une transaction est considérée comme **hors norme** (anomalie statistique) lorsque :

$$
|z| \geq 3
$$

> En statistique, le seuil $|z| \geq 3$ correspond à un événement très improbable sous une distribution normale (environ 0,27 % des valeurs). C'est une forte indication d'anomalie.

### 2. Le score de risque global

Chaque anomalie détectée reçoit une **pondération** selon sa sévérité :

$$
W = \{\text{critical}: 10,\; \text{high}: 5,\; \text{medium}: 2,\; \text{low}: 1\}
$$

Le score de risque global est alors :

$$
\text{RiskScore} = \min\left(100,\; \frac{\sum_{a \in \mathcal{A}} W(\text{sev}_a) \cdot c_a}{T} \times 100\right)
$$

où :

- $\mathcal{A}$ est l'ensemble des anomalies détectées ;
- $W(\text{sev}_a)$ est le poids de la sévérité de l'anomalie $a$ ;
- $c_a \in [0,1]$ est le **score de confiance** du moteur pour l'anomalie $a$ ;
- $T$ est le nombre total de transactions (avec $T \geq 1$).

Le score est **borné à 100**.

### 3. La confiance du moteur statistique

Le score de confiance de l'anomalie statistique augmente avec l'écart observé :

$$
c = \min(0.95,\; 0.55 + 0.08 \cdot |z|)
$$

Plus la transaction s'écarte de la moyenne, plus on est confiant qu'il s'agit d'une vraie anomalie, plafonnée à 95 %.

### 4. Le prix des plans (conversion € → CDF)

L'idée de tarification en **Franc Congolais (CDF)** repose sur une conversion indicative depuis l'euro :

$$
\text{Prix}_{\text{CDF}} \approx \text{Prix}_{\text{€}} \times \text{Taux}
$$

Par exemple, aux alentours de **2 900 CDF pour 1 €** :

$$
\text{Pro} : 19\,\text{€} \approx 55\,000\,\text{CDF}, \qquad
\text{Enterprise} : 49\,\text{€} \approx 142\,000\,\text{CDF}
$$

---

## Les difficultés rencontrées

Comme tout projet ambitieux, le chemin n'a pas été un long fleuve tranquille. Voici les principales difficultés rencontrées et comment je les ai surmontées.

### 1. Les erreurs de connexion à la base de données
Au début, le backend plantait en production avec des erreurs de type **« could not translate host name »** (résolution DNS intermittente). La base Supabase était parfois lente à répondre au démarrage.
**Solution :** j'ai ajouté une **logique de reconnexion** avec plusieurs tentatives, un `pool_timeout` et un réchauffement de la connexion (`SELECT 1`).

### 2. Les dates et les NaN dans les fichiers Excel
Quand un fichier contenait des **cellules vides** ou des valeurs non numériques, l'analyse plantait ou renvoyait du `NaN` invalide dans le JSON, ce qui cassait l'affichage.
**Solution :** j'ai formaté les colonnes de date, puis remplacé proprement les valeurs `NaN` par `null` avant d'envoyer le JSON.

### 3. La lenteur de l'analyse synchrone
`startAnalysis` était **synchronique** et bloquait pendant près de 100 secondes pendant que l'orchestrateur travaillait, ce qui frustrait l'utilisateur.
**Solution :** j'ai augmenté le temps d'expiration côté client (timeout à 5 minutes) et travaillé à rendre le retour plus explicite.

### 4. Le choix du paiement pour la RDC
Stripe ne supporte **pas la RDC**. J'ai d'abord cherché CinetPay, puis j'ai découvert que tu avais déjà un compte **MaishaPay** — bien adapté au marché congolais.
**Solution :** j'ai intégré le **Checkout de MaishaPay** (page de paiement hébergée) avec callback de confirmation, paiement par Mobile Money ou carte.

### 5. La gestion du contrôle d'accès et des rôles
Il fallait distinguer **super admin**, **org admin**, **admin** et **auditeur**, avec des permissions différentes sur chaque page.
**Solution :** mise en place des **rôles** et de garde-fous côté backend (`require_org_admin`, `require_super_admin`) et côté frontend (routes protégées).

### 6. Les doublons et les montants non conformes dans les données
Les fichiers réels venaient rarement propres : doublons, montants ronds, TVA invalide. Il a fallu **construire les règles** une par une et les tester sur des données variées.

### 7. La propagation des NaN (l'interlude NumPy)
En utilisant la renomination groupée (`replaceAll`), un bug s'était glissé : la fonction d'assistance appelait elle-même la conversion de manière récursive, ce qui plantait. Il a fallu **corriger la récursion** et rétablir `row.to_dict()` à l'intérieur de la fonction utilité.

---

## Et maintenant ?

Le projet est fonctionnel de bout en bout :

- ✅ Upload de fichier Excel/CSV et aperçu
- ✅ Moteur de détection multi-critères
- ✅ Rapport avec score de risque et anomalies expliquées
- ✅ Rapport PDF téléchargeable
- ✅ Gestion des équipes et des rôles
- ✅ Espace administrateur (super admin)
- ✅ Abonnement et paiement via MaishaPay
- ✅ Page publique de présentation

### Les prochaines évolutions possibles

- Ajouter du **machine learning** plus avancé (Isolation Forest, PCA) pour détecter des motifs subtils ;
- Analyser **continuement** les données (pas seulement à l'upload) ;
- Connecter des **ERP** directement par API ;
- Générer des **états financiers OHADA** (bilan, CPC) ;
- Déployer sur un **hébergement accessible publiquement** pour finaliser les paiements en production.

---

## Résumé en chiffres

| Élément | Valeur |
|---------|--------|
| Temps pour une analyse | Moins de 60 secondes |
| Moteurs de détection | 3 (règles, statistique, fractionnement) |
| Seuil de détection statistique | $\|z\| \geq 3$ |
| Plans tarifaires | Essai gratuit, Pro (55 000 CDF), Enterprise (142 000 CDF) |
| Paiement | Mobile Money & carte via MaishaPay |
| Technologie principale | Python + FastAPI + React + Supabase |
| Marché visé | RDC / Afrique francophone (normes OHADA) |
| Coût des géants vs LucidAI | 15 000 – 460 000 €/an vs prix local |

---

> *LucidAI n'est pas seulement un logiciel. C'est la conviction qu'un cabinet comptable de Kinshasa mérite les mêmes outils que ceux d'une tour de Manhattan — adaptés à sa langue, à ses normes et à son budget.*

---

*Ce document est rendu en Markdown avec support des formules mathématiques en LaTeX (délimiteurs `$...$` pour les formules en ligne et `$$...$$` pour les formules en bloc). Il s'affiche correctement dans VS Code (extension Markdown Preview Enhanced), GitHub, Typora ou tout éditeur Markdown avec support mathématique.*
