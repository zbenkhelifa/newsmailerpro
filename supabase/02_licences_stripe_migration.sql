-- ─────────────────────────────────────────────────────────────────
-- Migration : ajout des colonnes Stripe à la table licences
-- À exécuter dans Supabase > SQL Editor
-- (Seulement si vous avez déjà créé la table avec 01_licences_table.sql)
-- ─────────────────────────────────────────────────────────────────

ALTER TABLE licences
  ADD COLUMN IF NOT EXISTS stripe_customer_id     text,
  ADD COLUMN IF NOT EXISTS stripe_subscription_id text;

-- Index pour lookup rapide par ID Stripe
CREATE INDEX IF NOT EXISTS idx_licences_stripe_customer
  ON licences(stripe_customer_id);

CREATE INDEX IF NOT EXISTS idx_licences_stripe_sub
  ON licences(stripe_subscription_id);
