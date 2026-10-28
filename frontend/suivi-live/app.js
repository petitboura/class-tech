/* Page suivi en direct : lit les docs sur la branche main de GitHub,
   les affiche, et recommence seule toutes les heures. */
(function () {
  "use strict";

  var config = window.SUIVI_CONFIG;
  var md = window.SuiviMd;
  var outilProgression = window.SuiviProgression;

  var nav = document.getElementById("nav");
  var contenu = document.getElementById("contenu");
  var maj = document.getElementById("maj");
  var majCommit = document.getElementById("maj-commit");
  var prochaine = document.getElementById("prochaine");

  var MINUTE = 60 * 1000;
  var delaiRefresh = config.refreshMinutes * MINUTE;
  var dernierChargement = 0;
  var sensTri = "recent";

  function brut(chemin) {
    return (
      "https://raw.githubusercontent.com/" +
      config.owner + "/" + config.repo + "/" + config.branch + "/" + chemin
    );
  }

  function sectionParId(id) {
    for (var i = 0; i < config.sections.length; i++) {
      if (config.sections[i].id === id) return config.sections[i];
    }
    return config.sections[0];
  }

  function idDepuisHash() {
    var h = window.location.hash.replace(/^#\/?/, "").split("?")[0];
    for (var i = 0; i < config.sections.length; i++) {
      if (config.sections[i].id === h) return h;
    }
    return config.sections[0].id;
  }

  function formateDate(d) {
    return (
      d.toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" }) +
      " à " +
      d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })
    );
  }

  function construireNav() {
    config.sections.forEach(function (s) {
      var a = document.createElement("a");
      a.href = "#/" + s.id;
      a.textContent = s.titre;
      a.className = "lien-nav";
      a.setAttribute("data-section", s.id);
      nav.appendChild(a);
    });
    var depot = document.getElementById("lien-depot");
    depot.href = "https://github.com/" + config.owner + "/" + config.repo;
  }

  function marquerNavActive(id) {
    var liens = nav.querySelectorAll(".lien-nav");
    for (var i = 0; i < liens.length; i++) {
      var actif = liens[i].getAttribute("data-section") === id;
      liens[i].classList.toggle("actif", actif);
      if (actif) liens[i].setAttribute("aria-current", "page");
      else liens[i].removeAttribute("aria-current");
    }
  }

  function squelette(nbDocs) {
    var bloc =
      '<div class="doc squelette" aria-hidden="true">' +
      '<div class="sq-barre sq-titre"></div>' +
      '<div class="sq-barre"></div><div class="sq-barre"></div>' +
      '<div class="sq-barre sq-court"></div>' +
      '<div class="sq-barre"></div><div class="sq-barre sq-moyen"></div>' +
      "</div>";
    var html = "";
    for (var i = 0; i < nbDocs; i++) html += bloc;
    return html;
  }

  function chargerDocuments(section) {
    var appels = section.fichiers.map(function (chemin) {
      return fetch(brut(chemin), { cache: "no-store" }).then(function (rep) {
        if (rep.ok) {
          return rep.text().then(function (texte) {
            return { chemin: chemin, texte: texte, absent: false };
          });
        }
        if (rep.status === 404 && section.optionnel) {
          return { chemin: chemin, texte: "", absent: true };
        }
        throw new Error("doc inaccessible");
      });
    });
    return Promise.all(appels);
  }

  function htmlEvenement(e) {
    var ref = e.ref ? "<strong>" + md.inline(md.echapper(e.ref)) + "</strong> " : "";
    return (
      "<li class=\"evt\">" +
      (e.heureTexte ? "<span class=\"evt-heure\">" + md.echapper(e.heureTexte) + "</span>" : "") +
      "<span class=\"evt-etiquette\">" + md.echapper(e.etiquette) + "</span>" +
      "<span class=\"evt-texte\">" + ref + md.inline(md.echapper(e.texte)) + "</span>" +
      "</li>"
    );
  }

  function htmlGroupes(texteJournal, sens, ouverts) {
    var groupes = outilProgression.grouper(texteJournal, sens);
    if (groupes.length === 0) return "";
    return groupes.map(function (g, index) {
      var ouvert = ouverts ? ouverts.indexOf(g.cle) !== -1 : index === 0;
      return (
        "<details class=\"heure\" data-cle=\"" + g.cle + "\"" + (ouvert ? " open" : "") + ">" +
        "<summary><span class=\"heure-titre\">" + md.echapper(g.titre) + "</span>" +
        "<span class=\"chevron\" aria-hidden=\"true\"></span></summary>" +
        "<ul class=\"evts\">" + g.evenements.map(htmlEvenement).join("") + "</ul>" +
        "</details>"
      );
    }).join("");
  }

  function groupesOuverts() {
    var cles = [];
    contenu.querySelectorAll("details.heure[open]").forEach(function (d) {
      cles.push(d.getAttribute("data-cle"));
    });
    return cles;
  }

  function htmlSection(section, docs) {
    if (section.optionnel && docs.length > 0 && docs[0].absent) {
      return (
        '<div class="doc vide">' +
        "<p><strong>Aucune note pour le moment.</strong></p>" +
        "<p>Les notes dictées par Bourama apparaîtront ici toutes seules.</p>" +
        "</div>"
      );
    }
    var html = "";
    if (section.progression && docs.length > 0 && !docs[0].absent) {
      html +=
        '<div class="outils-progression">' +
        '<div class="tri" role="group" aria-label="Ordre des heures">' +
        '<button type="button" data-tri="recent">Plus récent d\u2019abord</button>' +
        '<button type="button" data-tri="ancien">Plus ancien d\u2019abord</button>' +
        "</div></div>" +
        '<div id="groupes">' + htmlGroupes(docs[0].texte, sensTri, null) + "</div>";
    }
    docs.forEach(function (d) {
      if (!d.absent) html += '<article class="doc">' + md.rendre(d.texte) + "</article>";
    });
    return html;
  }

  function brancherTri(section, docs) {
    var boutons = contenu.querySelectorAll(".tri button");
    for (var i = 0; i < boutons.length; i++) {
      if (boutons[i].getAttribute("data-tri") === sensTri) {
        boutons[i].setAttribute("aria-pressed", "true");
      }
      boutons[i].addEventListener("click", function () {
        sensTri = this.getAttribute("data-tri");
        var boites = contenu.querySelectorAll(".tri button");
        for (var j = 0; j < boites.length; j++) {
          if (boites[j].getAttribute("data-tri") === sensTri) boites[j].setAttribute("aria-pressed", "true");
          else boites[j].removeAttribute("aria-pressed");
        }
        document.getElementById("groupes").innerHTML = htmlGroupes(docs[0].texte, sensTri, null);
      });
    }
  }

  function afficherErreur(section) {
    contenu.innerHTML =
      '<div class="doc erreur" role="alert">' +
      "<p><strong>Impossible de charger les documents pour le moment.</strong></p>" +
      "<p>Vérifiez votre connexion puis réessayez.</p>" +
      '<p><button type="button" id="reessayer">Réessayer</button></p>' +
      "</div>";
    document.getElementById("reessayer").addEventListener("click", function () {
      afficherSection();
      chargerCommit();
    });
  }

  function afficherSection() {
    var section = sectionParId(idDepuisHash());
    marquerNavActive(section.id);
    document.title = section.titre + " · Suivi Class-Tech";
    contenu.innerHTML = squelette(section.fichiers.length);
    chargerDocuments(section).then(function (docs) {
      if (sectionParId(idDepuisHash()).id !== section.id) return;
      contenu.innerHTML = htmlSection(section, docs);
      if (section.progression) brancherTri(section, docs);
      dernierChargement = Date.now();
      afficherMaj();
    }).catch(function () {
      afficherErreur(section);
    });
  }

  /* Relecture silencieuse (toutes les heures) : pas de squelette, les
     heures ouvertes restent ouvertes. */
  function rafraichir() {
    var section = sectionParId(idDepuisHash());
    var ouverts = groupesOuverts();
    chargerDocuments(section).then(function (docs) {
      if (sectionParId(idDepuisHash()).id !== section.id) return;
      if (section.progression && docs.length > 0 && !docs[0].absent) {
        var zone = document.getElementById("groupes");
        if (zone) zone.innerHTML = htmlGroupes(docs[0].texte, sensTri, ouverts.length > 0 ? ouverts : null);
      } else {
        contenu.innerHTML = htmlSection(section, docs);
        if (section.progression) brancherTri(section, docs);
      }
      dernierChargement = Date.now();
      afficherMaj();
    }).catch(function () {
      /* On garde l'ancien contenu affiché, la prochaine heure réessaiera. */
    });
  }

  function afficherMaj() {
    if (!dernierChargement) return;
    maj.textContent = "Dernière mise à jour : " + formateDate(new Date(dernierChargement));
    tickProchaine();
  }

  function tickProchaine() {
    if (!dernierChargement) return;
    var reste = delaiRefresh - (Date.now() - dernierChargement);
    if (reste < 0) reste = 0;
    var minutes = Math.ceil(reste / MINUTE);
    prochaine.textContent =
      minutes <= 1 ? "Prochaine actualisation dans moins d\u2019une minute" : "Prochaine actualisation dans " + minutes + " min";
  }

  function chargerCommit() {
    var url =
      "https://api.github.com/repos/" + config.owner + "/" + config.repo +
      "/commits?path=docs&per_page=1";
    fetch(url, { cache: "no-store" }).then(function (rep) {
      if (!rep.ok) throw new Error("api");
      return rep.json();
    }).then(function (liste) {
      if (liste && liste.length > 0 && liste[0].commit && liste[0].commit.committer) {
        majCommit.textContent = "Documents publiés le " + formateDate(new Date(liste[0].commit.committer.date));
        majCommit.hidden = false;
      }
    }).catch(function () {
      /* Ligne simplement absente, la page reste utilisable. */
    });
  }

  construireNav();
  afficherSection();
  chargerCommit();
  window.addEventListener("hashchange", function () {
    afficherSection();
    window.scrollTo(0, 0);
  });
  window.setInterval(function () {
    rafraichir();
    chargerCommit();
  }, delaiRefresh);
  window.setInterval(tickProchaine, 30000);
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden && dernierChargement && Date.now() - dernierChargement > delaiRefresh) {
      rafraichir();
      chargerCommit();
    }
  });
})();
