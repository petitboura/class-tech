/* Commentaires de la page suivi en direct, sans compte ni connexion.
   Lecture et envoi via l'API Supabase (adresse, clé publique et table
   dans commentaires-config.js). Les réponses s'affichent indentées
   sous le message d'origine. Tout texte d'utilisateur est échappé
   avant affichage. */
(function (racine, fabrique) {
  if (typeof module === "object" && module.exports) module.exports = fabrique();
  else racine.SuiviCommentaires = fabrique();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var NOM_ANONYME = "Anonyme";
  var surcharge = null;

  /* En test Node, configurer() injecte la config. Dans la page,
     la config vient de commentaires-config.js. */
  function configurer(c) { surcharge = c; }

  function config() {
    if (surcharge) return surcharge;
    if (typeof window !== "undefined" && window.SUIVI_COMMENTAIRES_CONFIG) {
      return window.SUIVI_COMMENTAIRES_CONFIG;
    }
    return {};
  }

  function estConfigure() {
    var c = config();
    return !!(
      c &&
      typeof c.urlSupabase === "string" &&
      c.urlSupabase.indexOf("https://") === 0 &&
      typeof c.cleAnon === "string" &&
      c.cleAnon.length > 10 &&
      c.cleAnon.indexOf("REMPLIR") === -1
    );
  }

  function longueurMax() {
    var c = config();
    return c.longueurMax && c.longueurMax > 0 ? c.longueurMax : 2000;
  }

  function base() {
    var c = config();
    return c.urlSupabase.replace(/\/+$/, "") + "/rest/v1/" + c.table;
  }

  function entetes(json) {
    var c = config();
    var h = { apikey: c.cleAnon, Authorization: "Bearer " + c.cleAnon };
    if (json) h["Content-Type"] = "application/json";
    return h;
  }

  /* Échappe le HTML et adoucit les doubles tirets et tirets longs,
     jamais affichés tels quels sur cette page. */
  function echapper(texte) {
    return String(texte == null ? "" : texte)
      .replace(/—/g, "–")
      .replace(/--/g, "–")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function formateDate(iso) {
    var d = new Date(iso);
    if (isNaN(d.getTime())) return "date inconnue";
    return (
      d.toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" }) +
      " à " +
      d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })
    );
  }

  /* Organise la liste plate en arbre : chaque réponse rejoint son parent. */
  function arbre(liste) {
    var parId = {};
    var racines = [];
    liste.forEach(function (c) {
      parId[c.id] = c;
      c.enfants = [];
    });
    liste.forEach(function (c) {
      if (c.parent_id && parId[c.parent_id] && c.parent_id !== c.id) {
        parId[c.parent_id].enfants.push(c);
      } else {
        racines.push(c);
      }
    });
    return racines;
  }

  function charger() {
    var c = config();
    var url =
      base() +
      "?page=eq." + encodeURIComponent(c.page) +
      "&select=id,page,parent_id,nom,message,created_at&order=created_at.asc";
    return fetch(url, { headers: entetes(false) }).then(function (rep) {
      if (!rep.ok) throw new Error("lecture impossible");
      return rep.json();
    });
  }

  function envoyer(donnees) {
    var c = config();
    return fetch(base(), {
      method: "POST",
      headers: entetes(true),
      body: JSON.stringify({
        page: c.page,
        parent_id: donnees.parentId || null,
        nom: donnees.nom || null,
        message: donnees.message
      })
    }).then(function (rep) {
      if (!rep.ok) throw new Error("envoi impossible");
      return rep.json();
    });
  }

  function squeletteListe() {
    var bloc =
      '<div class="sq-barre sq-titre"></div>' +
      '<div class="sq-barre"></div>' +
      '<div class="sq-barre sq-court"></div>';
    return '<div aria-hidden="true">' + bloc + bloc + "</div>";
  }

  function htmlBase() {
    var max = longueurMax();
    return (
      '<div class="doc commentaires" id="zone-commentaires">' +
      "<h2>Commentaires</h2>" +
      "<p class=\"commentaires-intro\">Donnez votre avis ici, sans créer de compte.</p>" +
      '<p class="commentaires-note" id="note-commentaires" role="status" hidden></p>' +
      '<div id="liste-commentaires" aria-live="polite"></div>' +
      '<form id="form-commentaire" class="form-commentaire">' +
      "<h3>Écrire un commentaire</h3>" +
      "<label>Nom (optionnel)" +
      '<input type="text" id="nom-commentaire" maxlength="80" autocomplete="nickname" placeholder="Votre nom, ou rien pour rester anonyme">' +
      "</label>" +
      "<label>Votre message" +
      '<textarea id="message-commentaire" rows="4" maxlength="' + max + '" required placeholder="Écrivez votre message ici"></textarea>' +
      "</label>" +
      '<p class="compteur" id="compteur-message">0 / ' + max + "</p>" +
      '<p class="form-erreur" id="erreur-commentaire" role="alert" hidden></p>' +
      '<button type="submit" class="bouton" id="bouton-envoyer">Envoyer</button>' +
      "</form>" +
      "</div>"
    );
  }

  function htmlCommentaire(c) {
    var brut = c.nom == null ? "" : String(c.nom).trim();
    var nom = brut ? echapper(brut) : NOM_ANONYME;
    var reponses = (c.enfants || []).map(htmlCommentaire).join("");
    return (
      '<article class="commentaire" data-id="' + echapper(c.id) + '">' +
      '<p class="commentaire-entete"><span class="commentaire-nom">' + nom + "</span> " +
      '<span class="commentaire-date">' + echapper(formateDate(c.created_at)) + "</span></p>" +
      '<p class="commentaire-texte">' + echapper(c.message) + "</p>" +
      '<button type="button" class="bouton-repondre">Répondre</button>' +
      '<div class="zone-reponse" hidden></div>' +
      (reponses ? '<div class="reponses">' + reponses + "</div>" : "") +
      "</article>"
    );
  }

  function htmlFormReponse() {
    var max = longueurMax();
    return (
      '<form class="form-commentaire form-reponse">' +
      "<label>Nom (optionnel)" +
      '<input type="text" name="nom" maxlength="80" autocomplete="nickname" placeholder="Votre nom, ou rien pour rester anonyme">' +
      "</label>" +
      "<label>Votre réponse" +
      '<textarea name="message" rows="3" maxlength="' + max + '" required placeholder="Écrivez votre réponse ici"></textarea>' +
      "</label>" +
      '<p class="form-erreur" role="alert" hidden></p>' +
      '<div class="form-ligne-boutons">' +
      '<button type="submit" class="bouton">Envoyer</button>' +
      '<button type="button" class="bouton-secondaire bouton-annuler">Annuler</button>' +
      "</div>" +
      "</form>"
    );
  }

  function afficherNote(racine, texte) {
    var note = racine.querySelector("#note-commentaires");
    if (!note) return;
    note.textContent = texte;
    note.hidden = false;
  }

  function cacherNote(racine) {
    var note = racine.querySelector("#note-commentaires");
    if (note) note.hidden = true;
  }

  function afficherErreurForm(form, texte) {
    var zone = form.querySelector(".form-erreur");
    if (!zone) return;
    zone.textContent = texte;
    zone.hidden = false;
  }

  function cacherErreurForm(form) {
    var zone = form.querySelector(".form-erreur");
    if (zone) zone.hidden = true;
  }

  function messageValide(texte) {
    var propre = String(texte == null ? "" : texte).trim();
    if (!propre) return { ok: false, erreur: "Écrivez votre message avant de l’envoyer." };
    if (propre.length > longueurMax()) {
      return { ok: false, erreur: "Votre message est trop long (" + longueurMax() + " lettres au maximum)." };
    }
    return { ok: true, propre: propre };
  }

  function nomPropre(texte) {
    var propre = String(texte == null ? "" : texte).trim();
    return propre ? propre.slice(0, 80) : "";
  }

  function fermerReponses(racine, sauf) {
    var zones = racine.querySelectorAll(".zone-reponse");
    for (var i = 0; i < zones.length; i++) {
      if (zones[i] !== sauf) {
        zones[i].innerHTML = "";
        zones[i].hidden = true;
      }
    }
  }

  function chargerListe(racine, silencieuse) {
    var liste = racine.querySelector("#liste-commentaires");
    var form = racine.querySelector("#form-commentaire");
    if (!liste) return;
    if (!estConfigure()) {
      if (form) form.hidden = true;
      liste.innerHTML =
        '<div class="doc vide"><p><strong>Les commentaires arrivent bientôt.</strong></p>' +
        "<p>Revenez un peu plus tard pour donner votre avis.</p></div>";
      return;
    }
    if (form) form.hidden = false;
    if (!silencieuse || !liste.querySelector(".commentaire")) {
      liste.innerHTML = squeletteListe();
    }
    charger().then(function (lignes) {
      if (!racine.querySelector("#liste-commentaires")) return;
      if (lignes.length === 0) {
        liste.innerHTML =
          '<div class="doc vide"><p><strong>Aucun commentaire pour le moment.</strong></p>' +
          "<p>Écrivez le premier avec le formulaire ci-dessous.</p></div>";
        return;
      }
      liste.innerHTML = arbre(lignes).map(htmlCommentaire).join("");
    }).catch(function () {
      if (!racine.querySelector("#liste-commentaires")) return;
      cacherNote(racine);
      if (silencieuse && liste.querySelector(".commentaire")) return;
      liste.innerHTML =
        '<div class="doc erreur" role="alert">' +
        "<p><strong>Impossible de charger les commentaires pour le moment.</strong></p>" +
        "<p>Vérifiez votre connexion puis réessayez.</p>" +
        '<p><button type="button" class="bouton" id="recharger-commentaires">Réessayer</button></p>' +
        "</div>";
      var bouton = liste.querySelector("#recharger-commentaires");
      if (bouton) {
        bouton.addEventListener("click", function () { chargerListe(racine, false); });
      }
    });
  }

  function brancherListe(racine) {
    var liste = racine.querySelector("#liste-commentaires");
    if (!liste || liste.getAttribute("data-branche") === "oui") return;
    liste.setAttribute("data-branche", "oui");
    liste.addEventListener("click", function (evt) {
      var bouton = evt.target && evt.target.closest ? evt.target.closest(".bouton-repondre") : null;
      if (!bouton) return;
      var article = bouton.closest(".commentaire");
      if (!article) return;
      var zone = article.querySelector(".zone-reponse");
      if (!zone) return;
      if (!zone.hidden) {
        zone.innerHTML = "";
        zone.hidden = true;
        return;
      }
      fermerReponses(racine, zone);
      zone.innerHTML = htmlFormReponse();
      zone.hidden = false;
      var form = zone.querySelector("form");
      form.querySelector(".bouton-annuler").addEventListener("click", function () {
        zone.innerHTML = "";
        zone.hidden = true;
      });
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        cacherErreurForm(form);
        cacherNote(racine);
        var controle = messageValide(form.message.value);
        if (!controle.ok) {
          afficherErreurForm(form, controle.erreur);
          return;
        }
        var boutonEnvoi = form.querySelector('button[type="submit"]');
        boutonEnvoi.disabled = true;
        envoyer({
          parentId: article.getAttribute("data-id"),
          nom: nomPropre(form.nom.value),
          message: controle.propre
        }).then(function () {
          afficherNote(racine, "Merci, votre réponse est publiée.");
          chargerListe(racine, true);
        }).catch(function () {
          boutonEnvoi.disabled = false;
          afficherErreurForm(form, "L’envoi n’a pas marché. Vérifiez votre connexion puis réessayez.");
        });
      });
      var champ = form.querySelector('textarea[name="message"]');
      if (champ) champ.focus();
    });
  }

  function brancherFormPrincipal(racine) {
    var form = racine.querySelector("#form-commentaire");
    if (!form) return;
    var champNom = form.querySelector("#nom-commentaire");
    var champMessage = form.querySelector("#message-commentaire");
    var compteur = form.querySelector("#compteur-message");
    var bouton = form.querySelector("#bouton-envoyer");
    champMessage.addEventListener("input", function () {
      compteur.textContent = champMessage.value.length + " / " + longueurMax();
    });
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      cacherErreurForm(form);
      cacherNote(racine);
      var controle = messageValide(champMessage.value);
      if (!controle.ok) {
        afficherErreurForm(form, controle.erreur);
        return;
      }
      bouton.disabled = true;
      envoyer({ parentId: null, nom: nomPropre(champNom.value), message: controle.propre })
        .then(function () {
          bouton.disabled = false;
          champMessage.value = "";
          compteur.textContent = "0 / " + longueurMax();
          afficherNote(racine, "Merci, votre message est publié.");
          chargerListe(racine, true);
        })
        .catch(function () {
          bouton.disabled = false;
          afficherErreurForm(form, "L’envoi n’a pas marché. Vérifiez votre connexion puis réessayez.");
        });
    });
  }

  function afficher(racine) {
    racine.innerHTML = htmlBase();
    brancherFormPrincipal(racine);
    brancherListe(racine);
    chargerListe(racine, false);
  }

  function rafraichirSilencieux(racine) {
    if (!racine.querySelector("#zone-commentaires")) {
      afficher(racine);
      return;
    }
    brancherListe(racine);
    chargerListe(racine, true);
  }

  return {
    configurer: configurer,
    estConfigure: estConfigure,
    echapper: echapper,
    formateDate: formateDate,
    arbre: arbre,
    htmlBase: htmlBase,
    htmlCommentaire: htmlCommentaire,
    charger: charger,
    envoyer: envoyer,
    afficher: afficher,
    rafraichirSilencieux: rafraichirSilencieux
  };
});
