import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, colorchooser
import smtplib
import ssl
import csv
import json
import os
import time
import threading
import hashlib
import socket
import tempfile
import urllib.request
import urllib.error
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime

# ── Fichier de config ──────────────────────────────────────────────────────────
CONFIG_FILE  = os.path.join(os.path.dirname(__file__), "config.json")
LICENCE_FILE = os.path.join(os.path.dirname(__file__), ".licence")

# ── URL de votre Edge Function Supabase ───────────────────────────────────────
SUPABASE_VERIFY_URL = "https://tcexvmzfesnbhfjcgrnz.supabase.co/functions/v1/verifier-licence"

# ── Fingerprint machine ────────────────────────────────────────────────────────
def get_machine_id():
    raw = socket.gethostname() + os.environ.get("USERNAME", "") + os.environ.get("USER", "")
    return hashlib.sha256(raw.encode()).hexdigest()[:32]

# ── Vérification licence ───────────────────────────────────────────────────────
def verifier_licence(cle: str) -> dict:
    """Appelle la Edge Function et retourne {valide, message, client_nom}"""
    payload = json.dumps({"cle": cle, "machine_id": get_machine_id()}).encode()
    req = urllib.request.Request(
        SUPABASE_VERIFY_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return json.loads(body)
        except Exception:
            return {"valide": False, "message": f"Erreur serveur ({e.code})."}
    except Exception as e:
        return {"valide": False, "message": f"Impossible de contacter le serveur : {e}"}

def lire_licence_locale() -> str | None:
    """Lit la clé sauvegardée localement."""
    if os.path.exists(LICENCE_FILE):
        with open(LICENCE_FILE, "r") as f:
            return f.read().strip() or None
    return None

def sauver_licence_locale(cle: str):
    with open(LICENCE_FILE, "w") as f:
        f.write(cle.strip())

# ── Utilitaires ────────────────────────────────────────────────────────────────

def build_html(design):
    """Génère le HTML complet à partir des paramètres du design."""
    org      = design.get("org_nom", "Mon Organisation")
    slogan   = design.get("org_slogan", "")
    couleur  = design.get("header_couleur", "#1e3a5f")
    message  = design.get("message", "")
    boutons  = design.get("boutons", [])
    footer   = design.get("footer", "Cordialement")

    # Message : retours à la ligne → <br>
    message_html = ""
    if message.strip():
        lignes = message.replace("\r\n", "\n").split("\n")
        message_html = "<p style=\"margin:0 0 24px;font-size:15px;color:#555;line-height:1.7;\">" \
                       + "<br>".join(lignes) + "</p>"

    # Boutons
    boutons_html = ""
    if boutons:
        rows = ""
        for i, b in enumerate(boutons):
            margin = "0 6px 12px" if i < len(boutons) - 1 else "0 6px"
            rows += f"""
              <tr>
                <td align="center" style="padding:{margin};">
                  <a href="{b['url']}"
                     style="display:inline-block;background:{b['couleur']};color:#ffffff;text-decoration:none;
                            padding:14px 28px;border-radius:8px;font-size:14px;font-weight:600;
                            width:220px;text-align:center;box-sizing:border-box;">
                    {b['texte']}
                  </a>
                </td>
              </tr>"""
        boutons_html = f"""
            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">{rows}
            </table>"""

    slogan_html = f'<p style="margin:6px 0 0;color:#a8c4e0;font-size:14px;">{slogan}</p>' if slogan.strip() else ""

    return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f9;padding:30px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
        <tr>
          <td style="background:{couleur};padding:32px 40px;text-align:center;">
            <h1 style="margin:0;color:#ffffff;font-size:26px;font-weight:700;letter-spacing:-0.5px;">{org}</h1>
            {slogan_html}
          </td>
        </tr>
        <tr>
          <td style="padding:36px 40px;">
            {message_html}
            {boutons_html}
          </td>
        </tr>
        <tr>
          <td style="background:#f0f4f8;padding:20px 40px;text-align:center;border-top:1px solid #e8ecf0;">
            <p style="margin:0;font-size:12px;color:#aaa;">{footer}</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

DEFAULT_DESIGN = {
    "org_nom":       "Mon Organisation",
    "org_slogan":    "",
    "header_couleur":"#1e3a5f",
    "message":       "",
    "boutons":       [{"texte": "Accéder à la plateforme", "url": "https://votre-site.fr", "couleur": "#1e3a5f"}],
    "footer":        "Cordialement",
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "smtp_host":     "",
        "smtp_port":     "587",
        "smtp_user":     "",
        "smtp_password": "",
        "smtp_tls":      True,
        "delai":         "3",
        "objet":         "Message",
        "csv_path":      "",
        "design":        DEFAULT_DESIGN,
    }

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def load_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

# ── Fenêtre d'activation ───────────────────────────────────────────────────────

class FenetreActivation(tk.Toplevel):
    """Affichée au premier lancement ou si la licence est invalide."""
    def __init__(self, parent, callback_succes):
        super().__init__(parent)
        self.title("Activation")
        self.geometry("460x280")
        self.resizable(False, False)
        self.configure(bg="#f0f4f8")
        self.grab_set()
        self._callback = callback_succes
        self._build()

    def _build(self):
        tk.Frame(self, bg="#1e3a5f", height=6).pack(fill="x")

        tk.Label(self, text="🔑 Activation de l'application",
                 bg="#f0f4f8", font=("Helvetica", 15, "bold"),
                 fg="#1e3a5f").pack(pady=(20, 4))

        tk.Label(self,
                 text="Saisissez votre clé de licence\n(format : ENVOI-XXXX-XXXX-XXXX)",
                 bg="#f0f4f8", fg="#666", font=("Helvetica", 11),
                 justify="center").pack(pady=(0, 16))

        self._cle_var = tk.StringVar()
        entry = tk.Entry(self, textvariable=self._cle_var,
                         font=("Courier", 14), width=26, justify="center")
        entry.pack(pady=(0, 8))
        entry.focus()
        entry.bind("<Return>", lambda e: self._activer())

        self._lbl_status = tk.Label(self, text="", bg="#f0f4f8",
                                     font=("Helvetica", 11), fg="#c0392b")
        self._lbl_status.pack()

        self._btn_activer = tk.Button(self, text="Activer",
                                       bg="#1e3a5f", fg="white",
                                       font=("Helvetica", 12, "bold"),
                                       relief="flat", padx=20, pady=8,
                                       cursor="hand2", command=self._activer)
        self._btn_activer.pack(pady=12)

        tk.Label(self,
                 text="Pour obtenir une licence : codeappli09@gmail.com",
                 bg="#f0f4f8", fg="#aaa", font=("Helvetica", 10)).pack()

    def _activer(self):
        cle = self._cle_var.get().strip().upper()
        if not cle:
            self._lbl_status.config(text="Veuillez saisir une clé.")
            return

        self._btn_activer.config(state="disabled", text="Vérification...")
        self._lbl_status.config(text="Connexion au serveur...", fg="#555")
        self.update()

        def _do():
            result = verifier_licence(cle)
            def _update():
                self._btn_activer.config(state="normal", text="Activer")
                if result.get("valide"):
                    sauver_licence_locale(cle)
                    self._lbl_status.config(
                        text=f"✅ Activé — Bienvenue, {result.get('client_nom', '')} !",
                        fg="#2d7a4f"
                    )
                    self.after(1200, lambda: [self.destroy(), self._callback()])
                else:
                    self._lbl_status.config(
                        text=f"❌ {result.get('message', 'Clé invalide.')}",
                        fg="#c0392b"
                    )
            self.after(0, _update)

        threading.Thread(target=_do, daemon=True).start()


def verifier_au_demarrage(parent, callback_succes):
    """
    Vérifie la licence au démarrage.
    - Si aucune clé locale → affiche FenetreActivation
    - Si clé locale → vérifie en ligne silencieusement
      (en cas de timeout réseau, on laisse passer pour ne pas bloquer offline)
    """
    cle = lire_licence_locale()
    if not cle:
        FenetreActivation(parent, callback_succes)
        return

    def _check():
        result = verifier_licence(cle)
        def _update():
            if result.get("valide"):
                callback_succes()
            elif "Impossible de contacter" in result.get("message", ""):
                # Pas de réseau → on laisse passer (grace offline)
                callback_succes()
            else:
                # Licence révoquée / expirée → redemander
                os.remove(LICENCE_FILE)
                msg = result.get("message", "Licence invalide.")
                messagebox.showerror("Licence invalide", f"{msg}\n\nVeuillez entrer une nouvelle clé.")
                FenetreActivation(parent, callback_succes)
        parent.after(0, _update)

    threading.Thread(target=_check, daemon=True).start()


# ── Application principale ─────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NewsMailer Pro")
        self.geometry("860x740")
        self.resizable(True, True)
        self.configure(bg="#f0f4f8")

        self.cfg        = load_config()
        self._stop_flag = False
        self._sending   = False
        self._boutons   = []

        self._build_ui()
        # Désactiver l'interface jusqu'à validation de la licence
        self._lock_ui()
        self.after(200, lambda: verifier_au_demarrage(self, self._unlock_ui))

    def _lock_ui(self):
        """Grise le notebook pendant la vérification."""
        self.notebook.pack_forget()

    def _unlock_ui(self):
        """Affiche et charge l'interface après validation."""
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self._load_fields()

    # ── UI ─────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        header = tk.Frame(self, bg="#1e3a5f", pady=10)
        header.pack(fill="x")
        tk.Label(header, text="NewsMailer Pro",
                 bg="#1e3a5f", fg="white", font=("Helvetica", 17, "bold")).pack()

        style = ttk.Style()
        style.configure("TNotebook.Tab", font=("Helvetica", 12, "bold"), padding=[12, 6])

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_config = tk.Frame(self.notebook, bg="#f0f4f8")
        self.tab_design = tk.Frame(self.notebook, bg="#f0f4f8")
        self.tab_envoi  = tk.Frame(self.notebook, bg="#f0f4f8")
        self.tab_log    = tk.Frame(self.notebook, bg="#f0f4f8")

        self.notebook.add(self.tab_config, text="⚙️  Configuration")
        self.notebook.add(self.tab_design, text="🎨  Design email")
        self.notebook.add(self.tab_envoi,  text="📤  Envoi")
        self.notebook.add(self.tab_log,    text="📋  Log")

        self._build_tab_config()
        self._build_tab_design()
        self._build_tab_envoi()
        self._build_tab_log()

    # ── Onglet Configuration ───────────────────────────────────────────────────

    def _build_tab_config(self):
        f   = self.tab_config
        pad = {"padx": 16, "pady": 6}

        lf_smtp = tk.LabelFrame(f, text=" Serveur SMTP ", bg="#f0f4f8",
                                font=("Helvetica", 12, "bold"), fg="#1e3a5f")
        lf_smtp.pack(fill="x", padx=14, pady=(14, 6))

        self._smtp_vars = {}
        for label, key, secret in [
            ("Hôte SMTP",    "smtp_host",     False),
            ("Port",         "smtp_port",     False),
            ("Utilisateur",  "smtp_user",     False),
            ("Mot de passe", "smtp_password", True),
        ]:
            row = tk.Frame(lf_smtp, bg="#f0f4f8")
            row.pack(fill="x", **pad)
            tk.Label(row, text=label + " :", bg="#f0f4f8", width=16,
                     anchor="w", font=("Helvetica", 11)).pack(side="left")
            var = tk.StringVar()
            tk.Entry(row, textvariable=var, show="*" if secret else "",
                     width=38, font=("Helvetica", 11)).pack(side="left", padx=(4, 0))
            self._smtp_vars[key] = var

        row_tls = tk.Frame(lf_smtp, bg="#f0f4f8")
        row_tls.pack(fill="x", **pad)
        tk.Label(row_tls, text="Sécurité :", bg="#f0f4f8", width=16,
                 anchor="w", font=("Helvetica", 11)).pack(side="left")
        self._tls_var = tk.BooleanVar()
        tk.Checkbutton(row_tls, text="Utiliser TLS (STARTTLS)",
                       variable=self._tls_var, bg="#f0f4f8",
                       font=("Helvetica", 11)).pack(side="left")

        btn_frame = tk.Frame(f, bg="#f0f4f8")
        btn_frame.pack(fill="x", padx=14, pady=6)
        self._btn(btn_frame, "💾 Sauvegarder", self._save_config, "#2d7a4f").pack(side="left", padx=4)
        self._btn(btn_frame, "🔌 Tester la connexion", self._test_smtp, "#1e3a5f").pack(side="left", padx=4)

        lf_delay = tk.LabelFrame(f, text=" Options d'envoi ", bg="#f0f4f8",
                                 font=("Helvetica", 12, "bold"), fg="#1e3a5f")
        lf_delay.pack(fill="x", padx=14, pady=6)

        row_d = tk.Frame(lf_delay, bg="#f0f4f8")
        row_d.pack(fill="x", **pad)
        tk.Label(row_d, text="Délai entre envois :", bg="#f0f4f8",
                 font=("Helvetica", 11), width=20, anchor="w").pack(side="left")
        self._delai_var = tk.StringVar()
        tk.Spinbox(row_d, from_=1, to=30, textvariable=self._delai_var,
                   width=5, font=("Helvetica", 11)).pack(side="left")
        tk.Label(row_d, text="secondes  (recommandé : 3–5 s pour éviter le spam)",
                 bg="#f0f4f8", fg="#666", font=("Helvetica", 10)).pack(side="left", padx=6)

    # ── Onglet Design ──────────────────────────────────────────────────────────

    def _build_tab_design(self):
        f   = self.tab_design
        pad = {"padx": 14, "pady": 5}

        canvas = tk.Canvas(f, bg="#f0f4f8", highlightthickness=0)
        scroll = ttk.Scrollbar(f, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg="#f0f4f8")
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_resize(e):
            canvas.itemconfig(win_id, width=e.width)
        canvas.bind("<Configure>", _on_resize)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # ── Identité ──
        lf_id = tk.LabelFrame(inner, text=" Identité ", bg="#f0f4f8",
                              font=("Helvetica", 12, "bold"), fg="#1e3a5f")
        lf_id.pack(fill="x", padx=14, pady=(14, 6))

        self._dv = {}   # design vars

        for label, key, w in [
            ("Nom organisation :", "org_nom",    36),
            ("Slogan (optionnel):", "org_slogan", 36),
        ]:
            row = tk.Frame(lf_id, bg="#f0f4f8")
            row.pack(fill="x", **pad)
            tk.Label(row, text=label, bg="#f0f4f8", width=20,
                     anchor="w", font=("Helvetica", 11)).pack(side="left")
            var = tk.StringVar()
            tk.Entry(row, textvariable=var, width=w,
                     font=("Helvetica", 11)).pack(side="left")
            self._dv[key] = var

        # Couleur header
        row_c = tk.Frame(lf_id, bg="#f0f4f8")
        row_c.pack(fill="x", **pad)
        tk.Label(row_c, text="Couleur header :", bg="#f0f4f8", width=20,
                 anchor="w", font=("Helvetica", 11)).pack(side="left")
        self._couleur_var = tk.StringVar(value="#1e3a5f")
        self._couleur_preview = tk.Label(row_c, text="  ", bg="#1e3a5f",
                                         width=4, relief="solid", cursor="hand2")
        self._couleur_preview.pack(side="left", padx=(0, 6))
        tk.Entry(row_c, textvariable=self._couleur_var, width=10,
                 font=("Helvetica", 11)).pack(side="left", padx=(0, 6))
        self._btn(row_c, "🎨 Choisir", self._pick_color, "#555").pack(side="left")
        self._couleur_var.trace_add("write", lambda *_: self._update_color_preview())

        # ── Message ──
        lf_msg = tk.LabelFrame(inner, text=" Message ", bg="#f0f4f8",
                               font=("Helvetica", 12, "bold"), fg="#1e3a5f")
        lf_msg.pack(fill="x", padx=14, pady=6)

        tk.Label(lf_msg,
                 text="Corps du mail. Utilisez {colonne} pour insérer une valeur du CSV. Ex : Bonjour {prenom},",
                 bg="#f0f4f8", fg="#888", font=("Helvetica", 10)).pack(anchor="w", padx=10, pady=(6, 2))
        self._msg_text = scrolledtext.ScrolledText(lf_msg, height=6,
                                                    font=("Helvetica", 11), wrap="word")
        self._msg_text.pack(fill="x", padx=10, pady=(0, 4))
        self._lbl_cols = tk.Label(lf_msg, text="Chargez un CSV pour voir les variables disponibles.",
                                   bg="#f0f4f8", fg="#aaa", font=("Helvetica", 10),
                                   wraplength=520, justify="left")
        self._lbl_cols.pack(anchor="w", padx=10, pady=(0, 8))

        # ── Boutons ──
        lf_btn = tk.LabelFrame(inner, text=" Boutons ", bg="#f0f4f8",
                               font=("Helvetica", 12, "bold"), fg="#1e3a5f")
        lf_btn.pack(fill="x", padx=14, pady=6)

        tk.Label(lf_btn, text="Ajoutez jusqu'à 4 boutons (liens) dans le mail.",
                 bg="#f0f4f8", fg="#888", font=("Helvetica", 10)).pack(anchor="w", padx=10, pady=(6, 4))

        self._btn_frame_list = tk.Frame(lf_btn, bg="#f0f4f8")
        self._btn_frame_list.pack(fill="x", padx=10, pady=(0, 4))

        self._btn(lf_btn, "+ Ajouter un bouton", self._add_bouton_row, "#2d7a4f").pack(
            anchor="w", padx=10, pady=(0, 8))

        # ── Footer ──
        lf_foot = tk.LabelFrame(inner, text=" Pied de mail ", bg="#f0f4f8",
                                font=("Helvetica", 12, "bold"), fg="#1e3a5f")
        lf_foot.pack(fill="x", padx=14, pady=6)

        row_f = tk.Frame(lf_foot, bg="#f0f4f8")
        row_f.pack(fill="x", **pad)
        tk.Label(row_f, text="Texte footer :", bg="#f0f4f8", width=20,
                 anchor="w", font=("Helvetica", 11)).pack(side="left")
        var = tk.StringVar()
        tk.Entry(row_f, textvariable=var, width=36,
                 font=("Helvetica", 11)).pack(side="left")
        self._dv["footer"] = var

        # Bouton aperçu
        self._btn(inner, "👁 Aperçu du mail (HTML)", self._preview_html, "#1e3a5f").pack(
            pady=10)

    # ── Gestion des lignes de boutons ──────────────────────────────────────────

    def _add_bouton_row(self, texte="", url="", couleur="#1e3a5f"):
        if len(self._boutons) >= 4:
            messagebox.showinfo("Limite", "Maximum 4 boutons.")
            return

        idx  = len(self._boutons)
        row  = tk.Frame(self._btn_frame_list, bg="#f0f4f8", pady=3)
        row.pack(fill="x")

        tk.Label(row, text=f"Bouton {idx+1} :", bg="#f0f4f8",
                 font=("Helvetica", 11), width=9, anchor="w").pack(side="left")

        var_texte  = tk.StringVar(value=texte)
        var_url    = tk.StringVar(value=url)
        var_couleur= tk.StringVar(value=couleur)

        tk.Entry(row, textvariable=var_texte, width=16,
                 font=("Helvetica", 11)).pack(side="left", padx=2)
        tk.Entry(row, textvariable=var_url, width=22,
                 font=("Helvetica", 11)).pack(side="left", padx=2)

        preview = tk.Label(row, text="  ", bg=couleur, width=3,
                           relief="solid", cursor="hand2")
        preview.pack(side="left", padx=2)
        var_couleur.trace_add("write", lambda *_, p=preview, v=var_couleur: self._safe_bg(p, v.get()))

        def pick_btn_color(v=var_couleur, p=preview):
            c = colorchooser.askcolor(color=v.get(), title="Couleur du bouton")
            if c and c[1]:
                v.set(c[1])
                self._safe_bg(p, c[1])

        self._btn(row, "🎨", pick_btn_color, "#555").pack(side="left", padx=2)

        def remove(r=row, entry=None):
            r.destroy()
            self._boutons = [b for b in self._boutons if b["row"] is not r]
            self._renumber_bouton_rows()

        self._btn(row, "✕", remove, "#c0392b").pack(side="left", padx=2)

        entry = {"row": row, "texte": var_texte, "url": var_url, "couleur": var_couleur}
        self._boutons.append(entry)

    def _renumber_bouton_rows(self):
        for i, b in enumerate(self._boutons):
            for w in b["row"].winfo_children():
                if isinstance(w, tk.Label) and w.cget("text").startswith("Bouton"):
                    w.config(text=f"Bouton {i+1} :")
                    break

    def _safe_bg(self, widget, color):
        try:
            widget.config(bg=color)
        except Exception:
            pass

    def _pick_color(self):
        c = colorchooser.askcolor(color=self._couleur_var.get(), title="Couleur du header")
        if c and c[1]:
            self._couleur_var.set(c[1])
            self._safe_bg(self._couleur_preview, c[1])

    def _update_color_preview(self):
        self._safe_bg(self._couleur_preview, self._couleur_var.get())

    def _collect_design(self):
        boutons = []
        for b in self._boutons:
            t = b["texte"].get().strip()
            u = b["url"].get().strip()
            c = b["couleur"].get().strip() or "#1e3a5f"
            if t and u:
                boutons.append({"texte": t, "url": u, "couleur": c})
        return {
            "org_nom":        self._dv["org_nom"].get().strip(),
            "org_slogan":     self._dv["org_slogan"].get().strip(),
            "header_couleur": self._couleur_var.get().strip(),
            "message":        self._msg_text.get("1.0", "end-1c"),
            "boutons":        boutons,
            "footer":         self._dv["footer"].get().strip(),
        }

    def _preview_html(self):
        import webbrowser
        from pathlib import Path
        design = self._collect_design()
        html   = build_html(design)
        csv_path = self._csv_var.get()
        if csv_path and os.path.exists(csv_path):
            try:
                rows = load_csv(csv_path)
                if rows:
                    for key, val in rows[0].items():
                        html = html.replace(f"{{{key}}}",
                                            f"<span style='background:#fff3cd;padding:0 3px'>{val}</span>")
            except Exception:
                pass
        fd, tmp = tempfile.mkstemp(suffix=".html", prefix="apercu_email_")
        with os.fdopen(fd, "w", encoding="utf-8") as f_tmp:
            f_tmp.write(html)
        webbrowser.open(Path(tmp).as_uri())

    # ── Onglet Envoi ───────────────────────────────────────────────────────────

    def _build_tab_envoi(self):
        f   = self.tab_envoi
        pad = {"padx": 14, "pady": 5}

        lf_csv = tk.LabelFrame(f, text=" Fichier destinataires (CSV) ", bg="#f0f4f8",
                               font=("Helvetica", 12, "bold"), fg="#1e3a5f")
        lf_csv.pack(fill="x", padx=14, pady=(14, 6))

        row_csv = tk.Frame(lf_csv, bg="#f0f4f8")
        row_csv.pack(fill="x", **pad)
        self._csv_var = tk.StringVar()
        tk.Entry(row_csv, textvariable=self._csv_var, width=42,
                 font=("Helvetica", 11), state="readonly").pack(side="left")
        self._btn(row_csv, "📂 Parcourir", self._browse_csv, "#555").pack(side="left", padx=6)
        self._lbl_count = tk.Label(lf_csv, text="", bg="#f0f4f8",
                                   font=("Helvetica", 11), fg="#2d7a4f")
        self._lbl_count.pack(anchor="w", padx=14, pady=(0, 4))

        row_ecol = tk.Frame(lf_csv, bg="#f0f4f8")
        row_ecol.pack(fill="x", padx=10, pady=(0, 8))
        tk.Label(row_ecol, text="Colonne email :", bg="#f0f4f8",
                 font=("Helvetica", 11), width=16, anchor="w").pack(side="left")
        self._email_col_var = tk.StringVar()
        self._email_col_combo = ttk.Combobox(row_ecol, textvariable=self._email_col_var,
                                              state="readonly", width=24,
                                              font=("Helvetica", 11))
        self._email_col_combo.pack(side="left", padx=(4, 0))

        lf_msg = tk.LabelFrame(f, text=" Objet du mail ", bg="#f0f4f8",
                               font=("Helvetica", 12, "bold"), fg="#1e3a5f")
        lf_msg.pack(fill="x", padx=14, pady=6)

        row_obj = tk.Frame(lf_msg, bg="#f0f4f8")
        row_obj.pack(fill="x", padx=10, pady=8)
        tk.Label(row_obj, text="Objet :", bg="#f0f4f8",
                 font=("Helvetica", 11), width=8, anchor="w").pack(side="left")
        self._objet_var = tk.StringVar()
        tk.Entry(row_obj, textvariable=self._objet_var, width=48,
                 font=("Helvetica", 11)).pack(side="left")

        # Fichiers PDF
        lf_pdf = tk.LabelFrame(f, text=" Fichiers PDF à joindre (optionnel) ", bg="#f0f4f8",
                               font=("Helvetica", 12, "bold"), fg="#1e3a5f")
        lf_pdf.pack(fill="x", padx=14, pady=6)

        tk.Label(lf_pdf,
                 text="Nommez les PDF : Prenom_Nom.pdf, Nom_Prenom.pdf ou email.pdf — correspondance automatique.",
                 bg="#f0f4f8", fg="#888", font=("Helvetica", 10)).pack(anchor="w", padx=14, pady=(6, 2))

        row_pdf = tk.Frame(lf_pdf, bg="#f0f4f8")
        row_pdf.pack(fill="x", padx=10, pady=(4, 4))
        self._pdf_dir_var = tk.StringVar()
        tk.Entry(row_pdf, textvariable=self._pdf_dir_var, width=42,
                 font=("Helvetica", 11), state="readonly").pack(side="left")
        self._btn(row_pdf, "📂 Dossier", self._browse_pdf_dir, "#555").pack(side="left", padx=6)
        self._lbl_pdf = tk.Label(lf_pdf, text="Aucun dossier sélectionné.", bg="#f0f4f8",
                                  font=("Helvetica", 11), fg="#aaa")
        self._lbl_pdf.pack(anchor="w", padx=14, pady=(0, 8))

        # Info design
        lf_info = tk.LabelFrame(f, text=" Design utilisé ", bg="#f0f4f8",
                                font=("Helvetica", 12, "bold"), fg="#1e3a5f")
        lf_info.pack(fill="x", padx=14, pady=6)
        tk.Label(lf_info,
                 text="Le mail sera envoyé avec le design configuré dans l'onglet 🎨 Design email.",
                 bg="#f0f4f8", fg="#555", font=("Helvetica", 11)).pack(padx=14, pady=8, anchor="w")
        self._btn(lf_info, "👁 Aperçu avant envoi", self._preview_html, "#555").pack(
            padx=14, pady=(0, 8), anchor="w")

        self._progress = ttk.Progressbar(f, mode="determinate")
        self._progress.pack(fill="x", padx=14, pady=(12, 2))
        self._lbl_progress = tk.Label(f, text="", bg="#f0f4f8",
                                      font=("Helvetica", 11), fg="#555")
        self._lbl_progress.pack()

        btn_row = tk.Frame(f, bg="#f0f4f8")
        btn_row.pack(pady=8)
        self._btn_send = self._btn(btn_row, "🚀 Lancer l'envoi", self._start_send, "#1e3a5f")
        self._btn_send.pack(side="left", padx=6)
        self._btn_stop = self._btn(btn_row, "⛔ Arrêter", self._stop_send, "#c0392b")
        self._btn_stop.pack(side="left", padx=6)
        self._btn_stop.config(state="disabled")

    # ── Onglet Log ─────────────────────────────────────────────────────────────

    def _build_tab_log(self):
        f = self.tab_log
        self._log_text = scrolledtext.ScrolledText(f, font=("Courier", 11),
                                                    state="disabled", bg="#1a1a2e",
                                                    fg="#a8d8a8", insertbackground="white")
        self._log_text.pack(fill="both", expand=True, padx=10, pady=10)

        btn_row = tk.Frame(f, bg="#f0f4f8")
        btn_row.pack(pady=(0, 8))
        self._btn(btn_row, "🗑️ Effacer le log", self._clear_log, "#888").pack(side="left", padx=6)
        self._btn(btn_row, "💾 Exporter le log", self._export_log, "#2d7a4f").pack(side="left", padx=6)

    # ── Helpers UI ─────────────────────────────────────────────────────────────

    def _btn(self, parent, text, cmd, bg):
        return tk.Button(parent, text=text, command=cmd, bg=bg, fg="white",
                         font=("Helvetica", 11, "bold"), relief="flat",
                         padx=10, pady=5, cursor="hand2",
                         activebackground=bg, activeforeground="white")

    def _log(self, msg, level="INFO"):
        icons = {"INFO": "ℹ️", "OK": "✅", "ERR": "❌", "WARN": "⚠️", "START": "🚀"}
        icon = icons.get(level, "•")
        ts   = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {icon}  {msg}\n"
        self._log_text.config(state="normal")
        self._log_text.insert("end", line)
        self._log_text.see("end")
        self._log_text.config(state="disabled")
        if level == "ERR":
            self.notebook.select(self.tab_log)

    # ── Chargement / Sauvegarde ────────────────────────────────────────────────

    def _load_fields(self):
        for key, var in self._smtp_vars.items():
            var.set(self.cfg.get(key, ""))
        self._tls_var.set(self.cfg.get("smtp_tls", True))
        self._delai_var.set(self.cfg.get("delai", "3"))
        self._csv_var.set(self.cfg.get("csv_path", ""))
        self._objet_var.set(self.cfg.get("objet", "Message"))
        self._email_col_var.set(self.cfg.get("email_col", ""))
        pdf_dir = self.cfg.get("pdf_dir", "")
        self._pdf_dir_var.set(pdf_dir)
        if pdf_dir:
            self._update_pdf_count()

        d = self.cfg.get("design", DEFAULT_DESIGN)
        self._dv["org_nom"].set(d.get("org_nom", ""))
        self._dv["org_slogan"].set(d.get("org_slogan", ""))
        self._dv["footer"].set(d.get("footer", "Cordialement"))
        couleur = d.get("header_couleur", "#1e3a5f")
        self._couleur_var.set(couleur)
        self._safe_bg(self._couleur_preview, couleur)
        self._msg_text.delete("1.0", "end")
        self._msg_text.insert("1.0", d.get("message", ""))
        for b in d.get("boutons", []):
            self._add_bouton_row(b.get("texte", ""), b.get("url", ""), b.get("couleur", "#1e3a5f"))

        if self.cfg.get("csv_path"):
            self._update_count()

    def _collect_config(self):
        for key, var in self._smtp_vars.items():
            self.cfg[key] = var.get().strip()
        self.cfg["smtp_tls"]  = self._tls_var.get()
        self.cfg["delai"]     = self._delai_var.get()
        self.cfg["csv_path"]  = self._csv_var.get()
        self.cfg["objet"]     = self._objet_var.get().strip()
        self.cfg["email_col"] = self._email_col_var.get()
        self.cfg["pdf_dir"]   = self._pdf_dir_var.get()
        self.cfg["design"]    = self._collect_design()

    def _save_config(self):
        self._collect_config()
        save_config(self.cfg)
        self._log("Configuration sauvegardée.", "OK")
        messagebox.showinfo("Sauvegardé", "Configuration sauvegardée avec succès.")

    # ── PDF ────────────────────────────────────────────────────────────────────

    def _browse_pdf_dir(self):
        path = filedialog.askdirectory(title="Choisir le dossier contenant les PDF")
        if path:
            self._pdf_dir_var.set(path)
            self.cfg["pdf_dir"] = path
            self._update_pdf_count()

    def _update_pdf_count(self):
        d = self._pdf_dir_var.get()
        if d and os.path.isdir(d):
            pdfs = [f for f in os.listdir(d) if f.lower().endswith(".pdf")]
            self._lbl_pdf.config(
                text=f"✅ {len(pdfs)} fichier(s) PDF trouvé(s) dans le dossier",
                fg="#2d7a4f"
            )
        else:
            self._lbl_pdf.config(text="Dossier introuvable.", fg="#c0392b")

    def _find_pdf(self, pdf_dir, dest, email):
        """Cherche un PDF correspondant au destinataire dans le dossier donné."""
        if not pdf_dir or not os.path.isdir(pdf_dir):
            return None
        prenom, nom = "", ""
        for k, v in dest.items():
            kl = k.strip().lower()
            if kl in ("prenom", "prénom", "firstname", "first_name"):
                prenom = v.strip()
            elif kl in ("nom", "name", "lastname", "last_name", "surname"):
                nom = v.strip()
        candidates = []
        if prenom and nom:
            candidates += [
                f"{prenom}_{nom}.pdf", f"{nom}_{prenom}.pdf",
                f"{prenom} {nom}.pdf", f"{nom} {prenom}.pdf",
            ]
        if email:
            candidates.append(f"{email}.pdf")
        try:
            files_lower = {f.lower(): f for f in os.listdir(pdf_dir)}
        except Exception:
            return None
        for name in candidates:
            match = files_lower.get(name.lower())
            if match:
                return os.path.join(pdf_dir, match)
        return None

    # ── CSV ────────────────────────────────────────────────────────────────────

    def _browse_csv(self):
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        path = filedialog.askopenfilename(
            initialdir=data_dir,
            title="Choisir le fichier CSV",
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")]
        )
        if path:
            self._csv_var.set(path)
            self.cfg["csv_path"] = path
            self._update_count()

    def _update_count(self):
        try:
            rows = load_csv(self._csv_var.get())
            self._lbl_count.config(text=f"✅ {len(rows)} destinataire(s) chargé(s)", fg="#2d7a4f")
            if rows:
                cols = list(rows[0].keys())
                self._email_col_combo["values"] = cols
                current = self._email_col_var.get()
                if not current or current not in cols:
                    for c in cols:
                        if c.strip().lower() in ("email", "mail", "e-mail", "courriel"):
                            self._email_col_var.set(c)
                            break
                    else:
                        self._email_col_var.set(cols[0])
                self._update_col_hint(cols)
        except Exception as e:
            self._lbl_count.config(text=f"❌ Erreur lecture CSV : {e}", fg="#c0392b")

    def _update_col_hint(self, cols):
        placeholders = "   ".join(f"{{{c}}}" for c in cols)
        self._lbl_cols.config(text=f"Variables disponibles : {placeholders}", fg="#1e3a5f")

    # ── Test SMTP ──────────────────────────────────────────────────────────────

    def _test_smtp(self):
        self._collect_config()
        host     = self.cfg["smtp_host"]
        port     = int(self.cfg["smtp_port"] or 587)
        user     = self.cfg["smtp_user"]
        password = self.cfg["smtp_password"]
        use_tls  = self.cfg["smtp_tls"]
        self._log(f"Test connexion → {host}:{port} ...", "INFO")

        def _do():
            try:
                ctx = ssl.create_default_context()
                with smtplib.SMTP(host, port, timeout=10) as s:
                    if use_tls:
                        s.starttls(context=ctx)
                    s.login(user, password)
                self.after(0, lambda: self._log("Connexion SMTP réussie ✔", "OK"))
                self.after(0, lambda: messagebox.showinfo("Succès", "Connexion SMTP réussie !"))
            except Exception as e:
                m = str(e)
                self.after(0, lambda: self._log(f"Échec connexion : {m}", "ERR"))
                self.after(0, lambda: messagebox.showerror("Erreur SMTP", f"Connexion échouée :\n{m}"))

        threading.Thread(target=_do, daemon=True).start()

    # ── Envoi ──────────────────────────────────────────────────────────────────

    def _start_send(self):
        if self._sending:
            return
        self._collect_config()
        csv_path = self.cfg["csv_path"]
        if not csv_path or not os.path.exists(csv_path):
            messagebox.showerror("Erreur", "Veuillez sélectionner un fichier CSV valide.")
            return
        if not self.cfg["smtp_host"] or not self.cfg["smtp_user"]:
            messagebox.showerror("Erreur", "Veuillez configurer le serveur SMTP.")
            return
        if not self.cfg.get("email_col"):
            messagebox.showerror("Erreur", "Veuillez sélectionner la colonne email dans l'onglet Envoi.")
            return
        try:
            destinataires = load_csv(csv_path)
        except Exception as e:
            messagebox.showerror("Erreur CSV", str(e))
            return
        if not destinataires:
            messagebox.showwarning("Fichier vide", "Aucun destinataire trouvé dans le CSV.")
            return

        confirm = messagebox.askyesno(
            "Confirmer",
            f"Envoyer à {len(destinataires)} destinataire(s) avec un délai de {self.cfg['delai']} s ?\n\n"
            f"Durée estimée : ~{len(destinataires) * int(self.cfg['delai'])} secondes"
        )
        if not confirm:
            return

        self._stop_flag = False
        self._sending   = True
        self._btn_send.config(state="disabled")
        self._btn_stop.config(state="normal")
        self._progress["maximum"] = len(destinataires)
        self._progress["value"]   = 0
        self.notebook.select(self.tab_log)

        threading.Thread(target=self._send_all, args=(destinataires,), daemon=True).start()

    def _stop_send(self):
        self._stop_flag = True
        self._log("Arrêt demandé — en attente de fin d'envoi en cours...", "WARN")

    def _send_all(self, destinataires):
        host     = self.cfg["smtp_host"]
        port     = int(self.cfg["smtp_port"] or 587)
        user     = self.cfg["smtp_user"]
        password = self.cfg["smtp_password"]
        use_tls  = self.cfg["smtp_tls"]
        delai    = int(self.cfg["delai"])
        objet    = self.cfg["objet"]
        design    = self.cfg["design"]
        pdf_dir   = self.cfg.get("pdf_dir", "")
        email_col = self.cfg.get("email_col", "email")
        template  = build_html(design)

        total      = len(destinataires)
        ok_count   = 0
        err_list   = []
        err_rows   = []

        self.after(0, lambda: self._log(f"Début de l'envoi — {total} destinataires", "START"))

        try:
            ctx = ssl.create_default_context()
            with smtplib.SMTP(host, port, timeout=15) as server:
                if use_tls:
                    server.starttls(context=ctx)
                server.login(user, password)
                self.after(0, lambda: self._log("Connecté au serveur SMTP.", "OK"))

                for i, dest in enumerate(destinataires):
                    if self._stop_flag:
                        self.after(0, lambda: self._log("Envoi interrompu par l'utilisateur.", "WARN"))
                        break

                    # Récupérer l'adresse email depuis la colonne configurée
                    email = ""
                    for k, v in dest.items():
                        if k.strip().lower() == email_col.strip().lower():
                            email = v.strip()
                            break
                    if not email:
                        self.after(0, lambda ix=i+1:
                            self._log(f"Ligne {ix} : colonne '{email_col}' vide — ignorée", "WARN"))
                        continue

                    # Substitution dynamique de toutes les colonnes CSV
                    corps_html  = template
                    corps_texte = design.get("message", "")
                    for key, val in dest.items():
                        corps_html  = corps_html.replace(f"{{{key}}}", val)
                        corps_texte = corps_texte.replace(f"{{{key}}}", val)

                    pdf_path = self._find_pdf(pdf_dir, dest, email)
                    if pdf_path:
                        msg = MIMEMultipart("mixed")
                        alt = MIMEMultipart("alternative")
                        alt.attach(MIMEText(corps_texte, "plain", "utf-8"))
                        alt.attach(MIMEText(corps_html,  "html",  "utf-8"))
                        msg.attach(alt)
                        with open(pdf_path, "rb") as f_pdf:
                            att = MIMEApplication(f_pdf.read(), _subtype="pdf")
                        att.add_header("Content-Disposition", "attachment",
                                       filename=os.path.basename(pdf_path))
                        msg.attach(att)
                    else:
                        msg = MIMEMultipart("alternative")
                        msg.attach(MIMEText(corps_texte, "plain", "utf-8"))
                        msg.attach(MIMEText(corps_html,  "html",  "utf-8"))
                    msg["Subject"] = objet
                    msg["From"]    = user
                    msg["To"]      = email

                    try:
                        server.sendmail(user, email, msg.as_string())
                        ok_count += 1
                        idx = i + 1
                        pj = f" 📎 {os.path.basename(pdf_path)}" if pdf_path else ""
                        self.after(0, lambda e=email, ix=idx, pj=pj:
                            self._log(f"[{ix}/{total}] ✔ Envoyé à {e}{pj}", "OK"))
                    except Exception as e:
                        err_list.append(email)
                        err_rows.append(dest)
                        m = str(e)
                        self.after(0, lambda p=prenom, n=nom, e=email, err=m:
                            self._log(f"Erreur {p} {n} <{e}> : {err}", "ERR"))

                    val = i + 1
                    self.after(0, lambda v=val: self._update_progress(v, total))

                    if i < total - 1 and not self._stop_flag:
                        time.sleep(delai)

        except Exception as e:
            m = str(e)
            self.after(0, lambda: self._log(f"Erreur SMTP : {m}", "ERR"))

        def _final():
            self._sending = False
            self._btn_send.config(state="normal")
            self._btn_stop.config(state="disabled")
            self._log("─" * 50, "INFO")
            self._log(f"Envoi terminé : {ok_count} succès, {len(err_list)} erreur(s)", "OK")
            if err_rows:
                self._log(f"Emails en erreur : {', '.join(err_list)}", "WARN")
                data_dir = os.path.join(os.path.dirname(__file__), "data")
                ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
                err_path = os.path.join(data_dir, f"erreurs_{ts}.csv")
                try:
                    with open(err_path, "w", newline="", encoding="utf-8-sig") as f_err:
                        fieldnames = list(err_rows[0].keys()) if err_rows else []
                        writer = csv.DictWriter(f_err, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(err_rows)
                    self._log(f"CSV erreurs exporté → data/erreurs_{ts}.csv", "WARN")
                except Exception as ex:
                    self._log(f"Impossible d'écrire le CSV erreurs : {ex}", "ERR")
            self._lbl_progress.config(text=f"Terminé — {ok_count}/{total} envoyés")

        self.after(0, _final)

    def _update_progress(self, val, total):
        self._progress["value"] = val
        self._lbl_progress.config(text=f"Envoi en cours : {val}/{total}")

    # ── Log actions ────────────────────────────────────────────────────────────

    def _clear_log(self):
        self._log_text.config(state="normal")
        self._log_text.delete("1.0", "end")
        self._log_text.config(state="disabled")

    def _export_log(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Fichier texte", "*.txt")],
            initialfile=f"log_envoi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        if path:
            content = self._log_text.get("1.0", "end")
            with open(path, "w", encoding="utf-8") as f_log:
                f_log.write(content)
            messagebox.showinfo("Exporté", f"Log exporté vers :\n{path}")

# ── Lancement ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
