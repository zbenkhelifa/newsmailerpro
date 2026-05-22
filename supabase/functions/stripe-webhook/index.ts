// supabase/functions/stripe-webhook/index.ts
// Deploy : supabase functions deploy stripe-webhook
//
// Dans Stripe Dashboard → Developers → Webhooks → Add endpoint :
//   URL : https://VOTRE_PROJECT_ID.supabase.co/functions/v1/stripe-webhook
//   Events : customer.subscription.created
//             customer.subscription.deleted
//             customer.subscription.updated
//             invoice.payment_failed

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import Stripe from "https://esm.sh/stripe@14?target=deno";

// ── Helpers ────────────────────────────────────────────────────────────────────

function genererCle(): string {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"; // pas O/0/I/1 pour éviter confusion
  const bloc = () =>
    Array.from({ length: 4 }, () =>
      chars[Math.floor(Math.random() * chars.length)]
    ).join("");
  return `ENVOI-${bloc()}-${bloc()}-${bloc()}`;
}

function dateExpiration(interval: "month" | "year" = "year"): string {
  const jours = interval === "month" ? 35 : 370; // 30+5 ou 365+5 jours de grâce
  const d = new Date();
  d.setDate(d.getDate() + jours);
  return d.toISOString();
}

// ── Email via Brevo SMTP (API transactionnelle) ────────────────────────────────

async function envoyerEmailLicence(opts: {
  destinataire_email: string;
  destinataire_nom: string;
  cle: string;
  date_expiration: string;
}) {
  const brevo_url = "https://api.brevo.com/v3/smtp/email";
  const expire    = new Date(opts.date_expiration).toLocaleDateString("fr-FR");

  const body = {
    sender: {
      name:  Deno.env.get("BREVO_SENDER_NAME") || "MailSender Pro",
      email: Deno.env.get("BREVO_SENDER_EMAIL")!,
    },
    to: [{ email: opts.destinataire_email, name: opts.destinataire_nom }],
    subject: "🔑 Votre licence MailSender Pro",
    htmlContent: `<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f9;padding:30px 0;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0"
             style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
        <tr>
          <td style="background:#1e3a5f;padding:28px 40px;text-align:center;">
            <h1 style="margin:0;color:#fff;font-size:22px;font-weight:700;">MailSender Pro</h1>
            <p style="margin:4px 0 0;color:#a8c4e0;font-size:13px;">Votre licence est prête</p>
          </td>
        </tr>
        <tr>
          <td style="padding:32px 40px;">
            <p style="margin:0 0 16px;font-size:15px;color:#333;">Bonjour <strong>${opts.destinataire_nom}</strong>,</p>
            <p style="margin:0 0 24px;font-size:14px;color:#555;line-height:1.7;">
              Merci pour votre abonnement ! Voici votre clé de licence à saisir
              lors du premier lancement de l'application.
            </p>

            <!-- Clé -->
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="background:#f0f4f8;border-radius:8px;margin-bottom:28px;">
              <tr>
                <td style="padding:20px;text-align:center;">
                  <p style="margin:0 0 8px;font-size:12px;color:#888;text-transform:uppercase;
                            letter-spacing:1px;font-weight:600;">Votre clé de licence</p>
                  <p style="margin:0;font-size:22px;font-weight:700;color:#1e3a5f;
                            letter-spacing:2px;font-family:monospace;">${opts.cle}</p>
                  <p style="margin:8px 0 0;font-size:12px;color:#aaa;">Valable jusqu'au ${expire}</p>
                </td>
              </tr>
            </table>

            <!-- Étapes -->
            <p style="margin:0 0 12px;font-size:13px;color:#888;text-transform:uppercase;
                      letter-spacing:1px;font-weight:600;">Comment activer</p>
            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
              ${["Téléchargez et lancez MailSender Pro",
                 "Une fenêtre d'activation s'affiche au premier lancement",
                 "Saisissez votre clé et cliquez sur Activer"].map((step, i) => `
              <tr>
                <td style="padding:6px 0;vertical-align:top;">
                  <span style="display:inline-block;background:#1e3a5f;color:#fff;border-radius:50%;
                               width:22px;height:22px;text-align:center;line-height:22px;
                               font-size:12px;font-weight:700;margin-right:10px;">${i + 1}</span>
                  <span style="font-size:14px;color:#555;">${step}</span>
                </td>
              </tr>`).join("")}
            </table>

            <p style="margin:0;font-size:12px;color:#aaa;line-height:1.6;">
              Besoin d'aide ? Répondez à cet email ou contactez-nous à codeappli09@gmail.com
            </p>
          </td>
        </tr>
        <tr>
          <td style="background:#f0f4f8;padding:16px 40px;text-align:center;border-top:1px solid #e8ecf0;">
            <p style="margin:0;font-size:11px;color:#bbb;">
              MailSender Pro — Abonnement annuel — Renouvellement automatique via Stripe
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>`,
  };

  const resp = await fetch(brevo_url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "api-key": Deno.env.get("BREVO_API_KEY")!,
    },
    body: JSON.stringify(body),
  });

  if (!resp.ok) {
    const err = await resp.text();
    throw new Error(`Brevo error ${resp.status}: ${err}`);
  }
}

// ── Email renouvellement ───────────────────────────────────────────────────────

async function envoyerEmailRenouvellement(opts: {
  destinataire_email: string;
  destinataire_nom: string;
  cle: string;
  date_expiration: string;
}) {
  const brevo_url = "https://api.brevo.com/v3/smtp/email";
  const expire    = new Date(opts.date_expiration).toLocaleDateString("fr-FR");

  const body = {
    sender: {
      name:  Deno.env.get("BREVO_SENDER_NAME") || "MailSender Pro",
      email: Deno.env.get("BREVO_SENDER_EMAIL")!,
    },
    to: [{ email: opts.destinataire_email, name: opts.destinataire_nom }],
    subject: "✅ Votre abonnement MailSender Pro a été renouvelé",
    htmlContent: `<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="padding:30px 0;background:#f4f6f9;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0"
             style="background:#fff;border-radius:12px;overflow:hidden;">
        <tr><td style="background:#2d7a4f;padding:24px 40px;text-align:center;">
          <h1 style="margin:0;color:#fff;font-size:20px;">✅ Abonnement renouvelé</h1>
        </td></tr>
        <tr><td style="padding:28px 40px;">
          <p style="color:#333;font-size:15px;">Bonjour <strong>${opts.destinataire_nom}</strong>,</p>
          <p style="color:#555;font-size:14px;line-height:1.7;">
            Votre abonnement MailSender Pro a été renouvelé avec succès.
            Votre clé de licence reste la même :
          </p>
          <div style="background:#f0f4f8;border-radius:8px;padding:16px;text-align:center;margin:20px 0;">
            <p style="margin:0 0 4px;font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;">Clé de licence</p>
            <p style="margin:0;font-size:20px;font-weight:700;color:#1e3a5f;
                      letter-spacing:2px;font-family:monospace;">${opts.cle}</p>
            <p style="margin:6px 0 0;font-size:12px;color:#aaa;">Valable jusqu'au ${expire}</p>
          </div>
          <p style="color:#aaa;font-size:12px;">Aucune action requise de votre part.</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>`,
  };

  await fetch(brevo_url, {
    method: "POST",
    headers: { "Content-Type": "application/json", "api-key": Deno.env.get("BREVO_API_KEY")! },
    body: JSON.stringify(body),
  });
}

// ── Webhook principal ─────────────────────────────────────────────────────────

Deno.serve(async (req: Request) => {
  const stripe = new Stripe(Deno.env.get("STRIPE_SECRET_KEY")!, {
    apiVersion: "2024-04-10",
    httpClient: Stripe.createFetchHttpClient(),
  });

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
  );

  // Vérification signature Stripe
  const sig  = req.headers.get("stripe-signature")!;
  const body = await req.text();

  let event: Stripe.Event;
  try {
    event = await stripe.webhooks.constructEventAsync(
      body,
      sig,
      Deno.env.get("STRIPE_WEBHOOK_SECRET")!
    );
  } catch (err) {
    console.error("Signature Stripe invalide:", err);
    return new Response("Signature invalide", { status: 400 });
  }

  // ── Nouvel abonnement ────────────────────────────────────────────────────────
  if (event.type === "customer.subscription.created") {
    try {
      const sub      = event.data.object as Stripe.Subscription;
      const customer = await stripe.customers.retrieve(sub.customer as string) as Stripe.Customer;
      const interval = (sub.items.data[0]?.price?.recurring?.interval ?? "year") as "month" | "year";

      const client_nom   = customer.name || customer.email?.split("@")[0] || "Client";
      const client_email = customer.email!;
      const stripe_sub_id = sub.id;
      const stripe_cust_id = customer.id;

      // Vérifier si une licence existe déjà pour ce client Stripe
      const { data: existante } = await supabase
        .from("licences")
        .select("cle")
        .eq("stripe_customer_id", stripe_cust_id)
        .single();

      if (existante) {
        // Réactiver si suspendue
        await supabase.from("licences").update({
          statut: "active",
          date_expiration: dateExpiration(interval),
          stripe_subscription_id: stripe_sub_id,
        }).eq("stripe_customer_id", stripe_cust_id);
        console.log(`Licence réactivée pour ${client_email}`);
        return new Response("OK", { status: 200 });
      }

      // Créer la nouvelle licence
      const cle     = genererCle();
      const expire  = dateExpiration(interval);

      const { error } = await supabase.from("licences").insert({
        cle,
        client_nom,
        client_email,
        statut:                 "active",
        date_expiration:        expire,
        max_activations:        3,
        machines:               [],
        nb_activations:         0,
        stripe_customer_id:     stripe_cust_id,
        stripe_subscription_id: stripe_sub_id,
        notes:                  `Créé automatiquement via Stripe le ${new Date().toLocaleDateString("fr-FR")}`,
      });

      if (error) {
        console.error("Erreur insertion licence:", JSON.stringify(error));
        return new Response("Erreur DB", { status: 500 });
      }

      await envoyerEmailLicence({ destinataire_email: client_email, destinataire_nom: client_nom, cle, date_expiration: expire });
      console.log(`✅ Licence créée et email envoyé à ${client_email}`);
    } catch (err) {
      console.error("Erreur inattendue subscription.created:", err);
      return new Response("Erreur interne", { status: 500 });
    }
  }

  // ── Renouvellement ────────────────────────────────────────────────────────────
  if (event.type === "customer.subscription.updated") {
    const sub = event.data.object as Stripe.Subscription;
    if (sub.status !== "active") return new Response("OK", { status: 200 });

    const { data: licence } = await supabase
      .from("licences")
      .select("*")
      .eq("stripe_subscription_id", sub.id)
      .single();

    if (!licence) return new Response("OK", { status: 200 });

    const interval = (sub.items.data[0]?.price?.recurring?.interval ?? "year") as "month" | "year";
    const expire = dateExpiration(interval);
    await supabase.from("licences").update({
      statut: "active",
      date_expiration: expire,
    }).eq("id", licence.id);

    await envoyerEmailRenouvellement({
      destinataire_email: licence.client_email,
      destinataire_nom:   licence.client_nom,
      cle:                licence.cle,
      date_expiration:    expire,
    });
    console.log(`✅ Licence renouvelée pour ${licence.client_email}`);
  }

  // ── Résiliation / suspension ──────────────────────────────────────────────────
  if (event.type === "customer.subscription.deleted") {
    const sub = event.data.object as Stripe.Subscription;
    await supabase.from("licences").update({ statut: "suspendue" })
      .eq("stripe_subscription_id", sub.id);
    console.log(`Licence suspendue : ${sub.id}`);
  }

  // ── Paiement échoué ───────────────────────────────────────────────────────────
  if (event.type === "invoice.payment_failed") {
    const invoice = event.data.object as Stripe.Invoice;
    console.log(`Paiement échoué pour ${invoice.customer_email} — Stripe gère les relances.`);
    // Stripe envoie ses propres emails de relance, pas besoin d'agir ici
  }

  return new Response("OK", { status: 200 });
});
