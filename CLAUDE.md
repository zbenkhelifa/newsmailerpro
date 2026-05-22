# Instructions projet — Claude Code

Ce fichier est lu automatiquement par Claude Code à chaque session.

---

## Contexte

Projet : **MailSender Pro** — Application Python (tkinter) d'envoi d'identifiants par email avec système de licences commerciales.
Développeur : Zahire, enseignant-développeur indépendant, Académie de Versailles.

Stack :
- **App bureau** : Python 3 + tkinter, aucune dépendance externe
- **Backend** : Supabase (PostgreSQL + Edge Functions Deno)
- **Paiement** : Stripe abonnements annuels
- **Email livraison licence** : Brevo API
- **Licences** : format ENVOI-XXXX-XXXX-XXXX, vérification en ligne

---

## Structure

```
envoi_identifiants/
├── envoi_identifiants.py       ← App principale (tkinter)
├── build_windows.bat           ← Génère le .exe Windows
├── install_stripe.sh           ← Installe Stripe CLI sur Lubuntu
├── CLAUDE.md                   ← Ce fichier
├── data/
│   └── eleves_exemple.csv
└── supabase/
    ├── 01_licences_table.sql           ← À exécuter dans Supabase SQL Editor
    ├── 02_licences_stripe_migration.sql
    ├── generer_licence.py              ← Gestion manuelle des licences
    ├── README_SUPABASE.md
    ├── README_STRIPE.md
    └── functions/
        ├── verifier-licence/index.ts   ← Vérifie la clé au démarrage app
        └── stripe-webhook/index.ts     ← Reçoit les paiements Stripe
```

---

## Conventions

- Python : snake_case, méthodes privées en `_methode`
- TypeScript Edge Functions : camelCase, runtime Deno
- Commentaires en français
- Zéro dépendance externe Python (stdlib uniquement)

---

## Règles importantes

1. Ne jamais committer `.licence`, `config.json`
2. Clés API uniquement dans variables d'environnement Supabase
3. `service_role_key` jamais côté client
4. Toujours tester avec `sk_test_` avant `sk_live_`
5. Délai anti-spam entre emails : configurable, défaut 3 s

---

## Variables d'environnement Supabase

```
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
BREVO_API_KEY
BREVO_SENDER_EMAIL
BREVO_SENDER_NAME
```

---

## Commandes fréquentes

```bash
# Déployer les Edge Functions
supabase functions deploy verifier-licence
supabase functions deploy stripe-webhook

# Tester les webhooks en local
stripe listen --forward-to https://PROJET.supabase.co/functions/v1/stripe-webhook

# Simuler un abonnement Stripe
stripe trigger customer.subscription.created

# Générer une licence manuellement
python supabase/generer_licence.py

# Lister les licences
python supabase/generer_licence.py --list

# Compiler le .exe (depuis Windows)
build_windows.bat
```

---

## À remplacer dans le code

| Fichier | Valeur à remplacer |
|---|---|
| `envoi_identifiants.py` ligne ~18 | URL Edge Function Supabase |
| `supabase/generer_licence.py` lignes 31-32 | URL + service_role key Supabase |
| `supabase/functions/stripe-webhook/index.ts` | Variables via env Supabase |
