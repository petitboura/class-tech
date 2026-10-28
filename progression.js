/* Regroupe les entrées du journal par heure : tableaux à colonne
   "Heure" (§2 décisions, §3 agents, §6 incidents) et liste des jalons
   (§4). Si le journal change de forme, ce module rend simplement moins
   de groupes, le journal complet reste affiché en dessous. */
(function (racine, fabrique) {
  if (typeof module === "object" && module.exports) module.exports = fabrique();
  else racine.SuiviProgression = fabrique();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var ETIQUETTES = { 2: "Décision", 3: "Agent", 6: "Incident" };

  function extraireHeure(texte) {
    var m = /(\d{1,2}):(\d{2})/.exec(texte);
    if (!m) return null;
    var heure = Number(m[1]);
    var minute = Number(m[2]);
    if (heure > 23 || minute > 59) return null;
    return { heure: heure, minute: minute, tri: heure * 60 + minute };
  }

  function cellules(rang) {
    return rang.trim().replace(/^\||\|$/g, "").split("|").map(function (c) {
      return c.trim();
    });
  }

  function estSeparateur(ligne) {
    return /^\|?[\s:|-]+\|?$/.test(ligne.trim()) && ligne.indexOf("-") !== -1;
  }

  /* Découpe le journal en morceaux "## N. Titre" : [{numero, lignes}]. */
  function morceaux(texte) {
    var resultat = [];
    var courant = null;
    texte.replace(/\r/g, "").split("\n").forEach(function (ligne) {
      var m = /^## (\d+)\.\s*(.*)$/.exec(ligne.trim());
      if (m) {
        courant = { numero: Number(m[1]), lignes: [] };
        resultat.push(courant);
      } else if (courant) {
        courant.lignes.push(ligne);
      }
    });
    return resultat;
  }

  function evenementsTableau(lignes, etiquette) {
    var evenements = [];
    var i = 0;
    while (i < lignes.length) {
      if (lignes[i].trim().charAt(0) !== "|") { i++; continue; }
      var rangs = [];
      while (i < lignes.length && lignes[i].trim().charAt(0) === "|") {
        rangs.push(lignes[i]);
        i++;
      }
      if (rangs.length < 2) continue;
      var entete = cellules(rangs[0]);
      var colHeure = -1;
      for (var c = 0; c < entete.length; c++) {
        if (/^heures?$/i.test(entete[c])) { colHeure = c; break; }
      }
      if (colHeure === -1 || !estSeparateur(rangs[1])) continue;
      for (var r = 2; r < rangs.length; r++) {
        var vals = cellules(rangs[r]);
        var reference = vals[0] || "";
        var moment = colHeure < vals.length ? extraireHeure(vals[colHeure]) : null;
        var morceauxTexte = [];
        for (var k = 1; k < vals.length; k++) {
          if (k !== colHeure && vals[k]) morceauxTexte.push(vals[k]);
        }
        evenements.push({
          heure: moment ? moment.heure : null,
          tri: moment ? moment.tri : -1,
          heureTexte: moment
            ? moment.heure + "h" + (moment.minute < 10 ? "0" : "") + moment.minute
            : "",
          etiquette: etiquette,
          ref: reference,
          texte: morceauxTexte.join(" · ")
        });
      }
    }
    return evenements;
  }

  function evenementsJalons(lignes) {
    var evenements = [];
    var courant = null;
    function pousser() {
      if (courant) evenements.push(courant);
      courant = null;
    }
    lignes.forEach(function (ligne) {
      var m = /^-\s+(.*)$/.exec(ligne.trim());
      if (m) {
        pousser();
        var moment = extraireHeure(m[1].slice(0, 24));
        var texte = m[1].replace(/^~?\d{1,2}:\d{2}(?:\s*[–-]\s*~?\d{1,2}:\d{2})?\s*:\s*/, "");
        courant = {
          heure: moment ? moment.heure : null,
          tri: moment ? moment.tri : -1,
          heureTexte: moment
            ? moment.heure + "h" + (moment.minute < 10 ? "0" : "") + moment.minute
            : "",
          etiquette: "Jalon",
          ref: "",
          texte: texte || m[1]
        };
      } else if (courant && /^\s+\S/.test(ligne)) {
        courant.texte += " " + ligne.trim();
      } else if (ligne.trim() === "") {
        pousser();
      }
    });
    pousser();
    return evenements;
  }

  /* Rend [{cle, titre, evenements}] triés selon sens ("recent" ou
     "ancien"). Le groupe sans heure passe toujours en dernier. */
  function grouper(texteJournal, sens) {
    var evenements = [];
    morceaux(texteJournal).forEach(function (morceau) {
      if (ETIQUETTES[morceau.numero]) {
        evenements = evenements.concat(evenementsTableau(morceau.lignes, ETIQUETTES[morceau.numero]));
      } else if (morceau.numero === 4) {
        evenements = evenements.concat(evenementsJalons(morceau.lignes));
      }
    });
    var parHeure = {};
    var sansHeure = [];
    evenements.forEach(function (e) {
      if (e.heure === null) sansHeure.push(e);
      else {
        if (!parHeure[e.heure]) parHeure[e.heure] = [];
        parHeure[e.heure].push(e);
      }
    });
    var recent = sens !== "ancien";
    var cles = Object.keys(parHeure).map(Number).sort(function (a, b) {
      return recent ? b - a : a - b;
    });
    var groupes = cles.map(function (h) {
      var evts = parHeure[h].sort(function (a, b) {
        return recent ? b.tri - a.tri : a.tri - b.tri;
      });
      return {
        cle: "h" + h,
        titre: h + "h, " + evts.length + (evts.length > 1 ? " événements" : " événement"),
        evenements: evts
      };
    });
    if (sansHeure.length > 0) {
      groupes.push({
        cle: "sansheure",
        titre: "Sans heure précisée, " + sansHeure.length + (sansHeure.length > 1 ? " événements" : " événement"),
        evenements: sansHeure
      });
    }
    return groupes;
  }

  return { grouper: grouper };
});
