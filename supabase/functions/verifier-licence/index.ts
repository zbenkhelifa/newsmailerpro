// supabase/functions/verifier-licence/index.ts
// Deploy : supabase functions deploy verifier-licence

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "content-type",
};

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const { cle, machine_id } = await req.json();

    if (!cle || !machine_id) {
      return Response.json(
        { valide: false, message: "Paramètres manquants." },
        { status: 400, headers: corsHeaders }
      );
    }

    // Client Supabase avec service_role (accès total)
    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
    );

    // Récupérer la licence
    const { data: licence, error } = await supabase
      .from("licences")
      .select("*")
      .eq("cle", cle.toUpperCase().trim())
      .single();

    if (error || !licence) {
      return Response.json(
        { valide: false, message: "Clé de licence invalide." },
        { headers: corsHeaders }
      );
    }

    // Vérifier le statut
    if (licence.statut !== "active") {
      return Response.json(
        { valide: false, message: `Licence ${licence.statut}. Contactez le support.` },
        { headers: corsHeaders }
      );
    }

    // Vérifier l'expiration
    if (licence.date_expiration) {
      const expire = new Date(licence.date_expiration);
      if (expire < new Date()) {
        await supabase
          .from("licences")
          .update({ statut: "expiree" })
          .eq("id", licence.id);
        return Response.json(
          { valide: false, message: "Licence expirée. Contactez le support." },
          { headers: corsHeaders }
        );
      }
    }

    // Vérifier si cette machine est déjà connue
    const machines: string[] = licence.machines || [];
    const machine_connue = machines.includes(machine_id);

    if (!machine_connue) {
      // Vérifier le plafond d'activations
      if (
        licence.max_activations !== null &&
        machines.length >= licence.max_activations
      ) {
        return Response.json(
          {
            valide: false,
            message: `Nombre maximum de machines atteint (${licence.max_activations}). Contactez le support.`,
          },
          { headers: corsHeaders }
        );
      }

      // Enregistrer la nouvelle machine
      const nouvelles_machines = [...machines, machine_id];
      await supabase
        .from("licences")
        .update({
          machines: nouvelles_machines,
          nb_activations: licence.nb_activations + 1,
        })
        .eq("id", licence.id);
    }

    return Response.json(
      {
        valide: true,
        message: "Licence valide.",
        client_nom: licence.client_nom,
        date_expiration: licence.date_expiration,
      },
      { headers: corsHeaders }
    );
  } catch (err) {
    return Response.json(
      { valide: false, message: "Erreur serveur." },
      { status: 500, headers: corsHeaders }
    );
  }
});
