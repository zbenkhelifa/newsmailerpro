#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# install_stripe.sh — Installation Stripe CLI sur Lubuntu/Debian
# Usage : bash install_stripe.sh
# ─────────────────────────────────────────────────────────────────

set -e

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   Installation Stripe CLI — Lubuntu          ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── Stripe CLI ────────────────────────────────────────────────────
echo "💳 Ajout du dépôt Stripe..."

curl -s https://packages.stripe.dev/api/security/keypair/stripe-cli-gpg/public \
  | gpg --dearmor \
  | sudo tee /usr/share/keyrings/stripe.gpg > /dev/null

echo "deb [signed-by=/usr/share/keyrings/stripe.gpg] \
https://packages.stripe.dev/stripe-cli-debian-local stable main" \
  | sudo tee /etc/apt/sources.list.d/stripe.list > /dev/null

sudo apt update -qq
sudo apt install stripe -y

echo ""
echo "✅ Stripe CLI installée : $(stripe --version)"
echo ""

# ── Connexion Stripe ──────────────────────────────────────────────
echo "🔑 Connexion à votre compte Stripe..."
echo "   (Le navigateur va s'ouvrir pour autoriser)"
echo ""
stripe login

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   ✅ Stripe CLI prête !                      ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "Commandes utiles :"
echo ""
echo "  Écouter les webhooks en local :"
echo "  stripe listen --forward-to https://PROJET.supabase.co/functions/v1/stripe-webhook"
echo ""
echo "  Simuler un paiement :"
echo "  stripe trigger customer.subscription.created"
echo ""
echo "  Voir les événements récents :"
echo "  stripe events list"
echo ""
