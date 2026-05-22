# ⚙️ Configuration Supabase — Système de licences

## 1. Créer le projet Supabase

1. Aller sur https://supabase.com → New Project
2. Noter votre **Project URL** et vos deux clés API :
   - `anon` (publique)
   - `service_role` (privée — ne jamais exposer côté client)

---

## 2. Créer la table licences

Dans Supabase → **SQL Editor**, coller et exécuter le contenu de :
```
supabase/01_licences_table.sql
```

---

## 3. Déployer la Edge Function

### Installer Supabase CLI
```bash
npm install -g supabase
```

### Lier votre projet
```bash
supabase login
supabase link --project-ref VOTRE_PROJECT_ID
```

### Déployer la fonction
```bash
supabase functions deploy verifier-licence
```

La fonction sera disponible à :
```
https://VOTRE_PROJECT_ID.supabase.co/functions/v1/verifier-licence
```

---

## 4. Configurer l'application

### Dans `envoi_identifiants.py`
Remplacer ligne 18 :
```python
SUPABASE_VERIFY_URL = "https://VOTRE_PROJECT_ID.supabase.co/functions/v1/verifier-licence"
```

### Dans `supabase/generer_licence.py`
Remplacer lignes 31-32 :
```python
SUPABASE_URL         = "https://VOTRE_PROJECT_ID.supabase.co"
SUPABASE_SERVICE_KEY = "VOTRE_SERVICE_ROLE_KEY"
```

> ⚠️ Le fichier `generer_licence.py` contient la `service_role_key` — gardez-le
> sur votre machine, ne le partagez jamais avec vos clients.

---

## 5. Générer votre première licence

```bash
cd supabase
pip install supabase --break-system-packages
python generer_licence.py
```

Exemple de session :
```
── Nouvelle licence ──────────────────────────
Nom du client / établissement : Lycée Jean Moulin
Email du client (optionnel)   : secretariat@lycee-jeanmoulin.fr
Nb max de machines [3]        : 2
Durée en jours (vide = illimitée) : 365
Notes internes (optionnel)    : Achat du 21/05/2026

✅ Licence créée avec succès !
   Clé       : ENVOI-A7K2-XR9P-B3MQ
   Client    : Lycée Jean Moulin
   Expire le : 2027-05-21

📋 À transmettre au client : ENVOI-A7K2-XR9P-B3MQ
```

---

## 6. Gérer vos licences

```bash
python generer_licence.py --list              # Lister toutes les licences
python generer_licence.py --suspend ENVOI-A7K2-XR9P-B3MQ   # Suspendre
python generer_licence.py --activer ENVOI-A7K2-XR9P-B3MQ   # Réactiver
python generer_licence.py --supprimer ENVOI-A7K2-XR9P-B3MQ # Supprimer
```

---

## 7. Comportement de l'application côté client

| Situation | Comportement |
|---|---|
| Premier lancement | Fenêtre de saisie de clé |
| Clé valide | Accès déverrouillé, clé sauvegardée localement |
| Clé déjà saisie | Vérification silencieuse en arrière-plan |
| Pas de réseau | Accès autorisé (grace offline) |
| Licence suspendue | Message d'erreur, re-saisie demandée |
| Licence expirée | Message d'erreur, re-saisie demandée |
| Machine limite atteinte | Message d'erreur avec instruction de contact |

---

## 8. Modèles de tarification suggérés

| Offre | Machines | Durée | Prix suggéré |
|---|---|---|---|
| Annuel | 1 machine | 1 an | 29 € |
| Établissement | 3 machines | 1 an | 49 € |
| Permanent | illimité | illimitée | 79 € |
