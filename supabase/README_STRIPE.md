# 💳 Configuration Stripe — Abonnement annuel automatisé

## Vue d'ensemble du flow

```
Client clique "Acheter"
  → Stripe Checkout (page de paiement hébergée par Stripe)
    → Paiement accepté
      → Stripe envoie un webhook
        → Edge Function Supabase
          → Génère une clé ENVOI-XXXX-XXXX-XXXX
          → Insère en base
          → Envoie l'email via Brevo avec la clé
            → Client reçoit sa clé, active l'app
```

---

## Étape 1 — Créer le produit Stripe

1. Aller sur https://dashboard.stripe.com
2. **Products → Add product**
   - Nom : `MailSender Pro`
   - Prix : ex. `49,00 €`
   - Type de facturation : **Recurring** → **Yearly**
3. Copier le **Price ID** (ex. `price_1ABC...`)

---

## Étape 2 — Créer un lien de paiement Stripe

1. **Payment Links → Create payment link**
2. Sélectionner votre produit MailSender Pro
3. Dans **After payment** → cocher "Don't show confirmation page"
   (l'email Brevo remplacera la page de confirmation)
4. Copier l'URL du lien (ex. `https://buy.stripe.com/XXXX`)
5. Mettre ce lien sur votre site / landing page

---

## Étape 3 — Créer le webhook Stripe

1. **Developers → Webhooks → Add endpoint**
2. **Endpoint URL** :
   ```
   https://VOTRE_PROJECT_ID.supabase.co/functions/v1/stripe-webhook
   ```
3. **Events to send** — cocher :
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
4. Cliquer **Add endpoint**
5. Copier le **Signing secret** (commence par `whsec_...`)

---

## Étape 4 — Configurer les variables d'environnement Supabase

Dans Supabase → **Settings → Edge Functions → Add new secret** :

| Nom | Valeur |
|---|---|
| `STRIPE_SECRET_KEY` | `sk_live_...` (clé secrète Stripe) |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` (signing secret du webhook) |
| `BREVO_API_KEY` | Votre clé API Brevo (Settings → SMTP & API) |
| `BREVO_SENDER_EMAIL` | Ex. `noreply@votre-domaine.fr` |
| `BREVO_SENDER_NAME` | Ex. `MailSender Pro` |

> ⚠️ En test, utilisez `sk_test_...` et `whsec_test_...`
> Basculez en `sk_live_...` pour la production.

---

## Étape 5 — Déployer la Edge Function

```bash
supabase functions deploy stripe-webhook
```

---

## Étape 6 — Mise à jour de la base de données

Dans Supabase → **SQL Editor**, exécuter dans l'ordre :

```sql
-- Si table déjà créée :
-- Coller le contenu de 02_licences_stripe_migration.sql

-- Si nouvelle installation :
-- Coller d'abord 01_licences_table.sql
-- Puis 02_licences_stripe_migration.sql
```

---

## Étape 7 — Tester en mode test Stripe

1. Dans Stripe, basculer en mode **Test**
2. Utiliser la carte de test : `4242 4242 4242 4242`
3. Passer une commande test via votre lien de paiement
4. Vérifier dans **Stripe → Webhooks → Events** que le webhook est bien reçu (200 OK)
5. Vérifier dans **Supabase → Table Editor → licences** que la ligne est créée
6. Vérifier que vous recevez bien l'email avec la clé

---

## Gestion des cas particuliers

| Événement | Comportement automatique |
|---|---|
| Nouveau paiement | Clé générée + email envoyé |
| Renouvellement annuel | Date d'expiration mise à jour + email de confirmation |
| Résiliation | Licence passée en `suspendue` |
| Paiement échoué | Stripe gère les relances (3 tentatives par défaut) |
| Client déjà connu | Réactivation de l'ancienne licence (même clé) |

---

## Gestion manuelle (depuis votre machine)

```bash
# Voir toutes les licences
python supabase/generer_licence.py --list

# Suspendre un client
python supabase/generer_licence.py --suspend ENVOI-XXXX-XXXX-XXXX

# Réactiver manuellement
python supabase/generer_licence.py --activer ENVOI-XXXX-XXXX-XXXX
```

---

## Variables à remplacer dans le code

| Fichier | Ligne | Remplacer par |
|---|---|---|
| `envoi_identifiants.py` | 18 | Votre Project URL Supabase |
| `generer_licence.py` | 31-32 | URL + service_role key |

Les secrets Stripe et Brevo sont dans les variables d'environnement
Supabase — jamais dans le code.
