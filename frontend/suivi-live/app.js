/* Page suivi en direct : lit les docs sur la branche main de GitHub,
   les affiche, et recommence seule toutes les 5 heures. Deux faces :
   Normal (simple) et Technique (détails). */
(function () {
  "use strict";

  var config = window.SUIVI_CONFIG;
  var md = window.SuiviMd;
  var outilProgression = window.SuiviProgression;
  var outilTechnique = window.SuiviTechnique;

  var faces = document.getElementById("faces");
  var nav = document.getElementById("nav");
  var contenu = document.getElementById("contenu");
  var maj = document.getElementById("maj");
  var majCommit = document.getElementById("maj-commit");
  var prochaine = document.getElementById("prochaine");

  var MINUTE = 60 * 1000;
  var delaiRefresh = config.refreshMinutes * MINUTE;
  var dernierChargement = 0;
  var face = "normal";
  var sensTri = "recent";

  function sections() {
    return face === "technique" ? config.sectionsTechnique : config.sectionsNormal;
  }

  function titreFace() {
    for (var i = 0; i < config.faces.length; i++) {
      if (config.faces[i].id === face) return config.faces[i].titre;
    }
    return "";
  }

  function brut(chemin) {
    return (
      "https://raw.githubusercontent.com/" +
      config.owner + "/" + config.repo + "/" + config.branch + "/" + chemin
    );
  }

  function api(chemin) {
    return "https://api.github.com/repos/" + config.owner + "/" + config.repo + "/" + chemin;
  }

  function sectionParId(id) {
    var liste = sections();
    for (var i = 0; i < liste.length; i++) {
      if (liste[i].id === id) return liste[i];
    }
    return liste[0];
  }

  function idDepuisHash() {
    var h = window.location.hash.replace(/^#\/?/, "").split("?")[0];
    var liste = sections();
    for (var i = 0; i < liste.length; i++) {
      if (liste[i].id === h) return h;
    }
    return liste[0].id;
  }

  function formateDate(d) {
    return (
      d.toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" }) +
      " à " +
      d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })
    );
  }

  function construireFaces() {
    config.faces.forEach(function (f) {
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = f.titre;
      b.setAttribute("data-face", f.id);
      if (f.id === face) b.setAttribute("aria-pressed", "true");
      b.addEventListener("click", function () { changerFace(f.id); });
      faces.appendChild(b);
    });
  }

  function changerFace(nouvelle) {
    if (nouvelle === face) return;
    face = nouvelle;
    var boutons = faces.querySelectorAll("button");
    for (var i = 0; i < boutons.length; i++) {
      if (boutons[i].getAttribute("data-face") === face) boutons[i].setAttribute("aria-pressed", "true");
      else boutons[i].removeAttribute("aria-pressed");
    }
    document.body.setAttribute("data-face", face);
    construireNav();
    if (window.location.hash === "#/accueil" || window.location.hash === "") afficherSection();
    else window.location.hash = "#/accueil";
    window.scrollTo(0, 0);
  }

  function construireNav() {
    nav.innerHTML = "";
    sections().forEach(function (s) {
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

  function chargerJson(url) {
    return fetch(url, { cache: "no-store" }).then(function (rep) {
      if (!rep.ok) throw new Error("api inaccessible");
      return rep.json();
    });
  }

  function htmlHackathon() {
    var h = config.hackathon;
    return (
      '<div class="doc hackathon">' +
      '<p class="sur-titre">Contexte</p>' +
      "<p><strong>" + md.echapper(h.nom) + "</strong></p>" +
      "<p>" + md.echapper("Bourama y participe avec ce projet Class-Tech.") + "</p>" +
      "<p>" + md.echapper("Organisé par " + h.organisateur + " : " + h.detail + ".") + "</p>" +
      '<p><a href="' + md.echapper(h.urlAnnonce) + '" target="_blank" rel="noopener">' +
      md.echapper("Voir l’annonce officielle") + "</a></p>" +
      "</div>"
    );
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
      var corps = g.evenements.length === 0
        ? '<p class="rien">Rien pour l\u2019instant.</p>'
        : "<ul class=\"evts\">" + g.evenements.map(htmlEvenement).join("") + "</ul>";
      return (
        "<details class=\"heure\" data-cle=\"" + g.cle + "\"" + (ouvert ? " open" : "") + ">" +
        "<summary><span class=\"heure-titre\">" + md.echapper(g.titre) + "</span>" +
        "<span class=\"chevron\" aria-hidden=\"true\"></span></summary>" +
        corps +
        "</details>"
      );
    }).join("");
  }

  function ouverts(choix) {
    var cles = [];
    contenu.querySelectorAll(choix).forEach(function (d) {
      cles.push(d.getAttribute("data-cle"));
    });
    return cles;
  }

  function htmlCommits(liste) {
    var lignes = liste.map(function (c) {
      var message = (c.commit && c.commit.message ? c.commit.message : "").split("\n")[0];
      var date = c.commit && c.commit.committer ? new Date(c.commit.committer.date) : null;
      return (
        "<li class=\"evt\">" +
        (date ? "<span class=\"evt-heure\">" + md.echapper(formateDate(date)) + "</span>" : "") +
        "<span class=\"evt-texte\">" + md.inline(md.echapper(message)) + "</span>" +
        (c.html_url ? ' <a href="' + md.echapper(c.html_url) + '" target="_blank" rel="noopener">voir</a>' : "") +
        "</li>"
      );
    }).join("");
    return (
      '<div class="doc"><h2>Derniers commits sur main</h2>' +
      "<ul class=\"evts\">" + lignes + "</ul></div>"
    );
  }

  function htmlOutils(registre, paliersOuverts) {
    var blocs = registre.paliers.map(function (p, index) {
      var ouvert = paliersOuverts ? paliersOuverts.indexOf(p.nom) !== -1 : index === 0;
      var lignes = p.outils.map(function (o) {
        return (
          "<li class=\"evt\">" +
          "<span class=\"evt-texte\"><strong>" + md.echapper(o.label) + "</strong> " +
          "<code>" + md.echapper(o.nom) + "</code></span>" +
          (o.sensible ? "<span class=\"evt-etiquette\">confirmation exigée</span>" : "") +
          "</li>"
        );
      }).join("");
      return (
        "<details class=\"heure\" data-cle=\"" + md.echapper(p.nom) + "\"" + (ouvert ? " open" : "") + ">" +
        "<summary><span class=\"heure-titre\">" + md.echapper(p.nom + ", " + p.outils.length + (p.outils.length > 1 ? " outils" : " outil")) + "</span>" +
        "<span class=\"chevron\" aria-hidden=\"true\"></span></summary>" +
        "<ul class=\"evts\">" + lignes + "</ul>" +
        "</details>"
      );
    }).join("");
    return (
      '<div class="doc"><h2>' + registre.total + " outils au total</h2>" +
      "<p>Liste lue en direct dans le registre du projet.</p></div>" + blocs
    );
  }

  function htmlTests(totaux, fichiers) {
    var lignes = fichiers.map(function (f) {
      return (
        "<li class=\"evt\">" +
        "<span class=\"evt-texte\"><code>" + md.echapper(f.name) + "</code></span>" +
        ' <a href="' + md.echapper(f.html_url) + '" target="_blank" rel="noopener">voir</a>' +
        "</li>"
      );
    }).join("");
    var details = totaux.details.map(function (d) {
      return (
        "<li class=\"evt\">" +
        "<span class=\"evt-etiquette\">" + md.echapper(d.ref) + "</span>" +
        "<span class=\"evt-texte\">" + d.total + " tests cités</span>" +
        "</li>"
      );
    }).join("");
    return (
      '<div class="doc"><h2>Tests</h2>' +
      (totaux.total > 0
        ? "<p>Plus gros total cité dans le journal : <strong>" + totaux.total + " tests</strong>.</p>"
        : "<p>Le journal ne cite aucun total pour l\u2019instant.</p>") +
      "<ul class=\"evts\">" + details + "</ul>" +
      '<p><a href="#/journal">Détail dans le journal</a></p></div>' +
      '<div class="doc"><h2>Fichiers de test sur main</h2>' +
      "<ul class=\"evts\">" + lignes + "</ul></div>"
    );
  }

  function htmlDocs(section, docs) {
    if (section.optionnel && docs.length > 0 && docs[0].absent) {
      return (
        '<div class="doc vide">' +
        "<p><strong>Aucune note pour le moment.</strong></p>" +
        "<p>Les notes dictées par Bourama apparaîtront ici toutes seules.</p>" +
        "</div>"
      );
    }
    var html = "";
    if (section.hackathon) html += htmlHackathon();
    if (section.progression && docs.length > 0 && !docs[0].absent) {
      html +=
        '<div class="outils-progression">' +
        '<div class="tri" role="group" aria-label="Ordre des heures">' +
        '<button type="button" data-tri="recent">Plus récent d\u2019abord</button>' +
        '<button type="button" data-tri="ancien">Plus ancien d\u2019abord</button>' +
        "</div></div>" +
        '<div id="groupes">' + htmlGroupes(docs[0].texte, sensTri, null) + "</div>";
    }
    docs.forEach(function (d, index) {
      if (d.absent) return;
      var id = section.progression && index === 0 ? ' id="journal-complet"' : "";
      html += '<article class="doc"' + id + ">" + md.rendre(d.texte) + "</article>";
    });
    return html;
  }

  /* Charge une section et rend son HTML, quel que soit son type. */
  function chargerSection(section, clesOuvertes) {
    if (section.type === "commits") {
      return chargerJson(api("commits?sha=" + config.branch + "&per_page=" + config.technique.commitsNombre))
        .then(htmlCommits);
    }
    if (section.type === "outils") {
      return fetch(brut(config.technique.outilsFichier), { cache: "no-store" }).then(function (rep) {
        if (!rep.ok) throw new Error("registre inaccessible");
        return rep.text();
      }).then(function (texte) {
        return htmlOutils(outilTechnique.parseRegistre(texte), clesOuvertes);
      });
    }
    if (section.type === "tests") {
      return Promise.all([
        chargerDocuments(section),
        chargerJson(api("contents/" + config.technique.testsDossier + "?ref=" + config.branch))
      ]).then(function (paquet) {
        var totaux = outilTechnique.parseTestsJournal(paquet[0][0].texte);
        var fichiers = paquet[1].filter(function (f) { return f.type === "file"; }).sort(function (a, b) {
          return a.name < b.name ? -1 : 1;
        });
        return htmlTests(totaux, fichiers);
      });
    }
    return chargerDocuments(section).then(function (docs) {
      return { html: htmlDocs(section, docs), docs: docs };
    });
  }

  function brancherTri(docs) {
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
    var marque = face + section.id;
    marquerNavActive(section.id);
    document.title = section.titre + " · " + titreFace() + " · Suivi Class-Tech";
    contenu.innerHTML = squelette(section.type ? 1 : section.fichiers.length);
    chargerSection(section, null).then(function (rendu) {
      if (face + sectionParId(idDepuisHash()).id !== marque) return;
      if (typeof rendu === "string") {
        contenu.innerHTML = rendu;
      } else {
        contenu.innerHTML = rendu.html;
        if (section.progression) brancherTri(rendu.docs);
      }
      dernierChargement = Date.now();
      afficherMaj();
    }).catch(function () {
      afficherErreur(section);
    });
  }

  /* Relecture silencieuse (toutes les 5 heures) : pas de squelette,
     les blocs ouverts restent ouverts. */
  function rafraichir() {
    var section = sectionParId(idDepuisHash());
    var marque = face + section.id;
    var cles = ouverts("details.heure[open]");
    chargerSection(section, cles.length > 0 ? cles : null).then(function (rendu) {
      if (face + sectionParId(idDepuisHash()).id !== marque) return;
      if (typeof rendu === "string") {
        contenu.innerHTML = rendu;
      } else if (section.progression && rendu.docs.length > 0 && !rendu.docs[0].absent) {
        var zone = document.getElementById("groupes");
        if (zone) zone.innerHTML = htmlGroupes(rendu.docs[0].texte, sensTri, cles.length > 0 ? cles : null);
        var complet = document.getElementById("journal-complet");
        if (complet) complet.innerHTML = md.rendre(rendu.docs[0].texte);
      } else {
        contenu.innerHTML = rendu.html;
        if (section.progression) brancherTri(rendu.docs);
      }
      dernierChargement = Date.now();
      afficherMaj();
    }).catch(function () {
      /* On garde l'ancien contenu affiché, la prochaine fois réessaiera. */
    });
  }

  function afficherMaj() {
    if (!dernierChargement) return;
    maj.textContent = "Dernière mise à jour : " + formateDate(new Date(dernierChargement));
    tickProchaine();
  }

  function delaiProchaine(minutes) {
    if (minutes <= 1) return "moins d\u2019une minute";
    if (minutes < 90) return minutes + " min";
    var heures = Math.floor(minutes / 60);
    var reste = minutes % 60;
    return reste === 0 ? heures + " h" : heures + " h " + (reste < 10 ? "0" : "") + reste;
  }

  function tickProchaine() {
    if (!dernierChargement) return;
    var reste = delaiRefresh - (Date.now() - dernierChargement);
    if (reste < 0) reste = 0;
    prochaine.textContent = "Prochaine actualisation dans " + delaiProchaine(Math.ceil(reste / MINUTE));
  }

  function chargerCommit() {
    chargerJson(api("commits?path=docs&per_page=1")).then(function (liste) {
      if (liste && liste.length > 0 && liste[0].commit && liste[0].commit.committer) {
        majCommit.textContent = "Documents publiés le " + formateDate(new Date(liste[0].commit.committer.date));
        majCommit.hidden = false;
      }
    }).catch(function () {
      /* Ligne simplement absente, la page reste utilisable. */
    });
  }

  document.body.setAttribute("data-face", face);
  construireFaces();
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
