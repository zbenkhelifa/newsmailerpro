# 📧 Envoi Identifiants Élèves

Application Python pour envoyer les identifiants de connexion aux élèves par email.

## 📁 Structure

```
envoi_identifiants/
├── envoi_identifiants.py   ← Application principale
├── config.json             ← Créé automatiquement après la 1ère sauvegarde
├── README.md
└── data/
    └── eleves_exemple.csv  ← Modèle de fichier CSV
```

## 🚀 Lancement

```bash
python envoi_identifiants.py
```

Python 3.8+ requis. Aucune bibliothèque externe nécessaire (stdlib uniquement).

## 📄 Format du fichier CSV

Le fichier CSV doit être placé dans le dossier `data/` et contenir ces colonnes :

```
nom,prenom,email,mot_de_passe
Dupont,Marie,marie.dupont@lycee.fr,Xk9#mP2q
Martin,Lucas,lucas.martin@lycee.fr,Ht7$nR4w
```

**Encodage :** UTF-8 (avec ou sans BOM)  
**Séparateur :** virgule

## ⚙️ Configuration SMTP

### monlycee.net (Académie de Versailles)
- Hôte : `smtp.monlycee.net`
- Port : `587`
- TLS : ✅ activé
- Utilisateur : votre adresse @monlycee.net
- Mot de passe : votre mot de passe ENT

### Gmail
- Hôte : `smtp.gmail.com`
- Port : `587`
- TLS : ✅ activé
- Utilisateur : votre adresse Gmail
- Mot de passe : mot de passe d'application (pas le mot de passe principal)

### Brevo (anciennement Sendinblue)
- Hôte : `smtp-relay.brevo.com`
- Port : `587`
- TLS : ✅ activé
- Utilisateur : votre email Brevo
- Mot de passe : clé API SMTP Brevo

## ⏱️ Délai anti-spam

Régler à **3–5 secondes** entre chaque envoi pour éviter d'être bloqué comme spam.  
Pour 1 500 élèves à 3 s/email → environ **75 minutes**.  
Lancer de préférence la veille ou tôt le matin.

## 📝 Variables du template

Dans le corps du message, utilisez :

| Variable | Remplacée par |
|---|---|
| `{prenom}` | Prénom de l'élève |
| `{nom}` | Nom de l'élève |
| `{email}` | Adresse email |
| `{mot_de_passe}` | Mot de passe |
