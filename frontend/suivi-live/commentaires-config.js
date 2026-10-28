/* Configuration des commentaires de la page suivi en direct.
   Adresse Supabase, clé publique (faite pour être visible dans une
   page web) et réglages. La modération se fait par suppression dans
   le tableau de bord Supabase, table suivi_commentaires. */
window.SUIVI_COMMENTAIRES_CONFIG = {
  urlSupabase: "https://ljrbwwmiainrjirymmak.supabase.co",
  cleAnon: "sb_publishable_BL8kwyBWflH-Os5J_01CEA_Z8zFBc_p",
  page: "suivi-live",
  table: "suivi_commentaires",
  longueurMax: 2000
};
