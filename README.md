# NewsMailer Pro

Application Python (tkinter) pour envoyer les identifiants de connexion aux élèves par email.

## Structure

```
newsmailerpro/
├── newsmailerpro.py        ← Application principale
├── build_windows.bat       ← Génère NewsMailerPro.exe
├── data/
│   └── eleves_exemple.csv  ← Modèle de fichier CSV
└── supabase/
    ├── functions/
    │   ├── verifier-licence/   ← Vérifie la clé au démarrage
    │   └── stripe-webhook/     ← Reçoit les paiements Stripe
    └── generer_licence.py      ← Gestion manuelle des licences
```

## Lancement (développement)

```bash
python newsmailerpro.py
```

Python 3.8+ requis. Aucune bibliothèque externe nécessaire (stdlib uniquement).

## Compilation Windows

```bat
build_windows.bat
```

Génère `NewsMailerPro.exe` — à uploader dans la GitHub Release v1.0 :

```bash
gh release upload v1.0 NewsMailerPro.zip --repo zbenkhelifa/newsmailerpro
```

## Format du fichier CSV

```
nom,prenom,email,mot_de_passe
Dupont,Marie,marie.dupont@lycee.fr,Xk9#mP2q
Martin,Lucas,lucas.martin@lycee.fr,Ht7$nR4w
```

**Encodage :** UTF-8 · **Séparateur :** virgule

## Configuration SMTP

| Serveur | Hôte | Port |
|---|---|---|
| monlycee.net | `smtp.monlycee.net` | 587 |
| Gmail | `smtp.gmail.com` | 587 |
| Brevo | `smtp-relay.brevo.com` | 587 |

Délai anti-spam recommandé : **3–5 secondes** entre chaque envoi.
