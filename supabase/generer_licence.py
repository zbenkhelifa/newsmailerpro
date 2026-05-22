#!/usr/bin/env python3
"""
Générateur et gestionnaire de licences — NewsMailer Pro
Utilisation :
    python generer_licence.py                     → générer une nouvelle licence
    python generer_licence.py --list              → lister toutes les licences
    python generer_licence.py --suspend CLE       → suspendre une licence
    python generer_licence.py --activer CLE       → réactiver une licence
    python generer_licence.py --supprimer CLE     → supprimer une licence
"""

import argparse
import os
import random
import json
from datetime import datetime, timedelta

try:
    from supabase import create_client
except ImportError:
    print("Installation de supabase-py...")
    os.system("pip install supabase --break-system-packages -q")
    from supabase import create_client

# ── Config Supabase ────────────────────────────────────────────────────────────
# Remplissez ces valeurs avec vos propres clés Supabase
SUPABASE_URL      = "https://tcexvmzfesnbhfjcgrnz.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRjZXh2bXpmZXNuYmhmamNncm56Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTM5MTk2NiwiZXhwIjoyMDk0OTY3OTY2fQ.OWRbmZCkrMH53HgEBCv_1OmKdjUtTYhqjqWw_4WKcxo"

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# ── Génération de clé ──────────────────────────────────────────────────────────

_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sans O/0/I/1 pour éviter confusion

def generer_cle():
    """Génère une clé au format ENVOI-XXXX-XXXX-XXXX"""
    def bloc():
        return ''.join(random.choices(_CHARS, k=4))
    return f"ENVOI-{bloc()}-{bloc()}-{bloc()}"

# ── Commandes ──────────────────────────────────────────────────────────────────

def creer_licence():
    print("\n── Nouvelle licence ──────────────────────────")
    client_nom   = input("Nom du client / établissement : ").strip()
    client_email = input("Email du client (optionnel)   : ").strip()
    max_act      = input("Nb max de machines [3]        : ").strip() or "3"
    duree        = input("Durée en jours (vide = illimitée) : ").strip()
    notes        = input("Notes internes (optionnel)    : ").strip()

    cle = generer_cle()
    date_expiration = None
    if duree:
        date_expiration = (datetime.utcnow() + timedelta(days=int(duree))).isoformat()

    data = {
        "cle":             cle,
        "client_nom":      client_nom,
        "client_email":    client_email or None,
        "statut":          "active",
        "max_activations": int(max_act),
        "date_expiration": date_expiration,
        "notes":           notes or None,
    }

    res = supabase.table("licences").insert(data).execute()
    if res.data:
        print(f"\n✅ Licence créée avec succès !")
        print(f"   Clé       : {cle}")
        print(f"   Client    : {client_nom}")
        if date_expiration:
            print(f"   Expire le : {date_expiration[:10]}")
        else:
            print(f"   Expire le : jamais")
        print(f"\n📋 À transmettre au client : {cle}\n")
    else:
        print(f"❌ Erreur : {res}")

def lister_licences():
    res = supabase.table("licences").select("*").order("date_creation", desc=True).execute()
    licences = res.data or []
    if not licences:
        print("Aucune licence trouvée.")
        return
    print(f"\n── {len(licences)} licence(s) ──────────────────────────────────")
    for l in licences:
        exp = l["date_expiration"][:10] if l["date_expiration"] else "illimitée"
        machines = len(l.get("machines") or [])
        print(f"  [{l['statut'].upper():10}] {l['cle']}  |  {l['client_nom']:<30}  |  machines: {machines}/{l['max_activations']}  |  expire: {exp}")
    print()

def changer_statut(cle, statut):
    cle = cle.upper().strip()
    res = supabase.table("licences").update({"statut": statut}).eq("cle", cle).execute()
    if res.data:
        print(f"✅ Licence {cle} → {statut}")
    else:
        print(f"❌ Clé introuvable : {cle}")

def supprimer_licence(cle):
    cle = cle.upper().strip()
    confirm = input(f"Supprimer définitivement {cle} ? (oui/non) : ")
    if confirm.lower() == "oui":
        supabase.table("licences").delete().eq("cle", cle).execute()
        print(f"✅ Licence {cle} supprimée.")
    else:
        print("Annulé.")

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Gestionnaire de licences NewsMailer Pro")
    parser.add_argument("--list",      action="store_true", help="Lister les licences")
    parser.add_argument("--suspend",   metavar="CLE",       help="Suspendre une licence")
    parser.add_argument("--activer",   metavar="CLE",       help="Réactiver une licence")
    parser.add_argument("--supprimer", metavar="CLE",       help="Supprimer une licence")
    args = parser.parse_args()

    if args.list:
        lister_licences()
    elif args.suspend:
        changer_statut(args.suspend, "suspendue")
    elif args.activer:
        changer_statut(args.activer, "active")
    elif args.supprimer:
        supprimer_licence(args.supprimer)
    else:
        creer_licence()

if __name__ == "__main__":
    main()
