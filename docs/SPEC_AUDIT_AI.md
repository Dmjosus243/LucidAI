# Spécification fonctionnelle & technique — LucidAI v2 (7 fonctionnalités)

> Document de référence pour l'incrément `feature/audit-ai-2026`.
> Marché : RDC / PME · Interface : français · Paiement : MaishaPay Checkout (CDF).

---

## 0. Contexte & objectifs

LucidAI est un SaaS d'audit financier par IA destiné aux PME et cabinets d'audit de la
francophonie (RDC en priorité). La v1 fournit l'upload de fichiers comptables
(CSV/XLSX), l'analyse d'anomalies (règles + statistiques + seuils) avec score de risque,
le rapport PDF, la gestion d'organisation/membres/rôles, et le paiement MaishaPay.

La v2 ajoute 7 fonctionnalités majeures pour passer d'un outil d'analyse ponctuelle à une
**plateforme d'audit continue et collaborative** :

1. **OCR intelligent avec validation humaine** — captures/factures → écritures comptables prêtes.
2. **Rapprochement bancaire automatisé** — pointage écritures vs relevés, score de confiance.
3. **Suggestions d'écritures prédictives** — projets d'écritures par apprentissage des historiques.
4. **Détection d'anomalies renforcée (ML/stats)** — enrichissement du moteur existant.
5. **Assistant conversationnel** — interrogation des données en langage naturel.
6. **Piste d'audit & rôles** — traçabilité exhaustive, hiérarchie de permissions.
7. **APIs bancaires & webhooks** — ingestion automatisée des relevés, notification en temps réel.

**Contraintes techniques (décidées) :**
- OCR & bancaire : **bibliothèques gratuites / open source** (Tesseract/PaddleOCR en option,
  sinon pipeline numpy/pandas local). **Aucun** appel cloud payant bloquant.
- `scikit-learn` **absent volontairement** : le moteur statistique utilise numpy/pandas (z-score).
  Les modèles ML le cas échéant sont implémentés manuellement (Isolation Forest en pur numpy).
- Paiement : **MaishaPay Checkout** (page hébergée), montants en **CDF**.

---

## 1. Architecture

### 1.1 Diagramme applicatif (backend)

```
                        ┌─────────────────────────────────────────────┐
   Frontend React/TS    │              Backend FastAPI                │
   (Vite + Tailwind)    │                                             │
   ┌───────────────┐    │  ┌──────────┐   ┌────────────────────────┐  │
   │ Pages / Comps │───▶│  │ api/     │   │ engine/                │  │
   │  api.ts       │    │  │ routes/  │──▶│  rules_engine.py       │  │
   └───────────────┘    │  │  auth    │   │  ocr_pipeline.py   [F1]│  │
        │ HTTP/JSON     │  │  upload  │   │  reconciliation.py [F2]│  │
        │ (axios)       │  │  analysis│   │  prediction.py    [F3]│  │
        │               │  │  admin   │   │  recommender.py   [F5]│  │
        ▼               │  │  billing │   │  bank_import.py   [F7]│  │
   ┌───────────────┐    │  │  ocr     │[F1]│  ─────────────       │  │
   │ MaishaPay     │    │  │  recon   │[F2]│  agents/             │  │
   │ Checkout (CDF)│    │  │  predict │[F3]│  orchestrator/llm    │  │
   └───────────────┘    │  │  chat    │[F5]│  sentinel            │  │
                        │  │  banking │[F7]│                       │  │
                        │  └──────────┘   │  api/                  │  │
                        │  main.py        │  dependencies (auth)   │  │
                        │  config.py      │  audit (log_action)    │  │
                        │  database.py    │  storage (mémoire)     │  │
                        └──────┬──────────┴────────────────────────┘
                               │ SQLAlchemy / raw SQL (migrations ALTER TABLE)
                               ▼
                        ┌───────────────┐
                        │ Supabase      │
                        │ Postgres      │
                        └───────────────┘
```

### 1.2 Schéma de données (nouvelles tables + colonnes)

**Nouvelles tables :**

| Table | Usage | Colonnes clés |
|-------|-------|---------------|
| `ocr_documents` | documents OCR (F1) | id, org_id, user_id, filename, status (pending/validated/rejected), extracted_json, validated_json, confidence, created_at, validated_at, validated_by |
| `journal_entries` | écritures (F1/F2/F3) | id, org_id, entry_ref, date, lines JSON (compte, libellé, débit, crédit), source (ocr/recon/prédit/manuel), confidence, status, validated_by, created_at |
| `bank_accounts` | comptes bancaires (F2/F7) | id, org_id, bank_code, label, currency, provider, last_sync_at, config JSON |
| `bank_statements` | relevés bruts (F2/F7) | id, org_id, account_id, date_range, source, raw JSON, imported_by, created_at |
| `reconciliation_items` | pointages (F2) | id, org_id, statement_line_id, entry_id, status (matched/unmatched/auto), confidence, matched_at, matched_by |
| `chat_sessions` | sessions assistant (F5) | id, org_id, user_id, title, created_at |
| `chat_messages` | messages (F5) | id, session_id, role (user/assistant), content, context JSON, created_at |
| `webhook_events` | événements entrants (F7) | id, org_id, provider, event_type, payload JSON, status (received/processed/failed), received_at, processed_at |

**Nouvelles colonnes (migrations `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`) :**
- `analyses`: `status` existant ; ne pas modifier.
- `organizations`: `bank_sync_enabled BOOLEAN DEFAULT FALSE`.
- `profiles`: rien d'obligatoire (rôles existent).

Toutes les migrations sont **idempotentes** et suivent le motif existant de `database.py`
(Phase A `CREATE TABLE IF NOT EXISTS`, Phase B `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`).

### 1.3 Flux de bout en bout (exemple : OCR F1)

1. `POST /api/v1/ocr/upload` (multipart, PDF/image) → pipeline pilote virtuel (numpy/pillow)
   ou Tesseract/PaddleOCR **si disponible**. Extraction texte → `extracted_json` + `confidence`.
2. Stockage dans `ocr_documents` (status `pending`), `log_action("ocr.upload")`.
3. `GET /api/v1/ocr/documents?org_id=` liste les docs de l'organisation.
4. Frontend : `DocumentsOCR.tsx` affiche le texte extrait, l'utilisateur **valide/corrige**
   ligne par ligne.
5. `POST /api/v1/ocr/documents/{id}/validate` (json corrigé) → generation d'écritures
   dans `journal_entries` (source `ocr`), status `validated`, `log_action("ocr.validate")`.
6. `POST /api/v1/ocr/documents/{id}/reject` → statut `rejected`.

Critère : **précision OCR ≥ 92 % sur 500 factures** ; le pipeline doit fonctionner sans
dépendance système (mode « transparent »), et se renforcer si Tesseract/PaddleOCR présents.

---

## 2. Les 7 fonctionnalités

### F1 — OCR intelligent + validation humaine

**Objectif :** extraire automatiquement les écritures des factures/justificatifs numérisés,
soumettre à validation humaine avant intégration comptable.

- **Backend** : `api/routes/ocr.py`, `engine/ocr_pipeline.py`.
  - Détection de moteur : `pytesseract` / `PaddleOCR` si installés, sinon `zeros` (mode pur
    numpy/pillow pour OCR de base), toujours dégradable sans crash.
  - Parsing de champs (date, montant, fournisseur, TVA) via extraction structurée + heuristiques.
  - Score de confiance par champ et par document.
- **Frontend** : `Pages/DocumentsOCR.tsx`, `Components/OcrReview.tsx`.
- **Tests** : précision ≥ 92 %, parsing, rejet, validation, génération d'écritures.

### F2 — Rapprochement bancaire automatisé

**Objectif :** pointer automatiquement les écritures avec les lignes de relevé bancaire,
avec score de confiance.

- **Backend** : `api/routes/recon.py`, `engine/reconciliation.py`.
  - Matching: montant exact + fenêtre de date + normalisation libellés (fuzzy via difflib),
  - 2 passes : correspondance stricte (montant+date±3j) puis floue (diff de montant ≤ 0,01 %),
  - Confiance = f(écart montant, écart date, similarité libellé, unicité).
- **Frontend** : `Pages/Reconciliation.tsx`, `Components/ReconReview.tsx`.
- **Tests** : taux d'automatisation ≥ 80 %, faux positifs faibles, cas limites.

### F3 — Suggestions d'écritures prédictives

> ⚠️ **Décision produit importante** : introduit la « prédiction » d'écritures courantes
> (amortissements, loyers, paie) par apprentissage des modèles observés. **Positionné —
> nécessite validation du client avant démarrage en production.**

- **Backend** : `api/routes/predict.py`, `engine/prediction.py`.
  - Patterns récurrents par compte (fréquence, périodicité, montants typiques) via pandas.
  - Génération d'un « projet d'écriture » avec confiance + explication.
- **Frontend** : `Components/PredictionSuggestions.tsx` (valider/ignorer).
- **Tests** : détection de récurrence, qualité des suggestions.

### F4 — Détection d'anomalies renforcée

**Objectif :** enrichir le moteur existant (`rules_engine.py`, déjà à 3 moteurs) avec des
signaux supplémentaires et un score de confiance pondéré.

- **Déjà en place** : moteurs règles / z-score statistique / seuils, champs
  `confidence`, `summary`, `reason`, `red_flags`, `suggested_action`, score pondéré par la
  confiance. **À compléter** : appétence au risque par organisation, regroupement
  temporel (pointe mensuels), benchmarks intra-organisation.
- **Backend** : enrichissements de `rules_engine.py` + `api/routes/analysis.py`.
- **Frontend** : `Components/AnomalyList.tsx` (déjà enrichi).
- **Tests** : rappel ≥ 95 %, faux positifs < 5 %.

### F5 — Assistant conversationnel

**Objectif :** interroger les données et le contexte d'audit en langage naturel.

- **Backend** : `api/routes/chat.py`, `engine/recommender.py`, s'appuie sur `agents/llm.py`
  (Gemini) avec repli dégradé local.
  - Convertit la question en requête structurée (filtres, resumé) → réponse en français.
- **Frontend** : `Pages/Assistant.tsx`, `Components/ChatWindow.tsx`.
- **Tests** : boucle question→réponse, sessions, repli hors API key.

### F6 — Piste d'audit & rôles

**Objectif :** traçabilité exhaustive des actions + hiérarchie de rôles stricte.

- **Déjà en place** : `AuditLog` + `log_action()`, rôles
  (`super_admin/org_admin/admin/manager/auditor`), helpers `is_org_admin`,
  `require_org_admin`, `require_super_admin`, endpoint `/audit-logs`, UI
  `AdminDashboard.tsx` (journal), `TeamManagement.tsx`.
- **À compléter** : pagination + filtres du journal, export CSV, traçage des
  validations OCR/recon/prédiction (déjà hub pour chaque mutation via `log_action`),
  attribution des permissions par fonctionnalité.
- **Tests** : chaque mutation écrit une trace, contrôle d'accès par rôle (tests d'intégration).

### F7 — APIs bancaires & webhooks

**Objectif :** ingestion automatisée des relevés via API et webhooks de notification.

- **Backend** : `api/routes/banking.py`.
  - `POST /api/v1/banking/statements/import` : import JSON/CSV de relevé, validation,
    stockage `bank_statements`, déclenche reconnaissance.
  - `POST /api/v1/banking/webhook` : réception d'événements (signature optionnelle),
    stockage `webhook_events`, traitement idempotent, retour 200 rapide.
  - `GET /api/v1/banking/accounts`, `POST /api/v1/banking/accounts`.
- **Fournisseurs** : adaptateurs extensibles ; pour la version OSS, import générique agnostique
  fournisseur + placeholder API réelle (MaishaPay/banques RDC) documenté.
- **Frontend** : `Pages/Banking.tsx`.
- **Tests** : import, idempotence webhook, validation de payload.

---

## 3. Backlog sprint (2 semaines)

Priorité par **dépendance** : rôles/piste d'abord, puis moteur, puis ingestion.

### Sprint 1 (fondations + ingestion)
| # | Tâche | Feature | Livrable | Critère |
|---|-------|---------|----------|---------|
| S1.1 | Piste d'audit & rôles : pagination journal, export CSV, contrôle accès par fonctionnalité | F6 | `admin.py` + `AdminDashboard` + `TeamManagement` | traces ✓, accès contrôlé ✓ |
| S1.2 | Enrichissement moteur anomalies (appétence risque, benchmarks) | F4 | `rules_engine.py` | rappel ≥ 95 %, FP < 5 % |
| S1.3 | Pipeline OCR (moteur détecté, extraction champs, confiance) | F1 | `ocr_pipeline.py` + `ocr.py` | précision ≥ 92 % / 500 |
| S1.4 | UI validation OCR + génération d'écritures | F1 | `DocumentsOCR.tsx` + `OcrReview.tsx` | flux validé → écriture |

### Sprint 2 (rapprochement, prédiction, assistant, webhooks)
| # | Tâche | Feature | Livrable | Critère |
|---|-------|---------|----------|---------|
| S2.1 | Rapprochement bancaire (2 passes + confiance) | F2 | `reconciliation.py` + `recon.py` | auto ≥ 80 % |
| S2.2 | UI rapprochement | F2 | `Reconciliation.tsx` | revue interactive |
| S2.3 | Suggestions d'écritures prédictives (validation client requise) | F3 | `prediction.py` + `predict.py` | récurrences détectées |
| S2.4 | Assistant conversationnel | F5 | `chat.py` + `Assistant.tsx` | Q/R fonctionnelle |
| S2.5 | APIs bancaires & webhooks | F7 | `banking.py` + `Banking.tsx` | import + webhook idempotent |
| S2.6 | Migrations finales, tests, déploiement, rollback, PRs | toutes | `database.py` + tests + doc | build OK, tests verts |

---

## 4. Critères d'acceptation globaux

- **OCR (F1)** : précision ≥ 92 % sur 500 factures ; validation humaine obligatoire avant
  écriture ; mode sans dépendance système opérationnel.
- **Rapprochement (F2)** : ≥ 80 % d'écritures rapprochées automatiquement ; score de
  confiance affiché ; points « à revoir » exigeant validation.
- **Prédiction (F3)** : suggestions avec explication + confiance ; jamais auto-intégrées.
- **Anomalies (F4)** : rappel ≥ 95 %, faux positifs < 5 % ; chaque anomalie porte
  `confidence`, `summary`, `reason`, `red_flags`, `suggested_action`.
- **Assistant (F5)** : répond en français sur le contexte org ; repli dégradé sans API key.
- **Piste & rôles (F6)** : 100 % des mutations tracées ; accès par fonctionnalité respecté.
- **Banking/webhooks (F7)** : import validé ; webhook idempotent (rejeu sûr) ; retour < 2 s.
- **Tests** : couverture unitaire ≥ 70 % (backend), tests d'intégration flux
  OCR → écriture et rapprochement ; `tsc --noEmit` + `vite build` verts côté front.
- **Déploiement** : migration idempotente, rollback documenté, checklists de production.

---

## 5. Matrice des rôles

| Capacité | auditeur | manager | admin / org_admin | super_admin |
|----------|----------|---------|-------------------|-------------|
| Upload + analyse | ✅ | ✅ | ✅ | ✅ |
| Valider OCR/écritures | ✅ | ✅ | ✅ | ✅ |
| Rapprocher | ✅ | ✅ | ✅ | ✅ |
| Prédiction (valider) | ❌ | ✅ | ✅ | ✅ |
| Assistant | ✅ | ✅ | ✅ | ✅ |
| Gérer membres/rôles | ❌ | ❌ | ✅ | ✅ |
| Configurer banque/webhooks | ❌ | ✅ | ✅ | ✅ |
| Piste d'audit (org) | ❌ | ❌ | ✅ | ✅ |
| Stats plateforme | ❌ | ❌ | ❌ | ✅ |

---

## 6. Rappels opérationnels (bloquants externes)

- **MaishaPay** : coller `MAISHAPAY_PUBLIC_KEY` / `MAISHAPAY_SECRET_KEY` dans `Backend/.env`
  (menu « Développeur »), paramétrer `MAISHAPAY_GATEWAY_MODE` (0 = sandbox), redémarrer le
  backend, et fournir une URL backend publique (callback) pour la prod. **Sans quoi**
  `POST /billing/checkout` renvoie `{"detail":"MaishaPay non configuré"}` (500).
- **OCR intensif** : Tesseract/PaddleOCR restent optionnels pour renforcer la précision ;
  le pipeline livre toujours un résultat (degraded) sans eux.

---

*Document généré pour l'incrément `feature/audit-ai-2026`.*
