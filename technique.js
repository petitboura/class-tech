/* Lecture des données techniques en direct : registre des outils
   (backend/core/registre_outils.py sur main) et totaux de tests
   cités dans le journal. Pur traitement de texte, sans réseau. */
(function (racine, fabrique) {
  if (typeof module === "object" && module.exports) module.exports = fabrique();
  else racine.SuiviTechnique = fabrique();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  /* Noms cités dans une liste Python ("a", "b", ...) lue ligne par ligne. */
  function lireListePython(lignes, debut) {
    var noms = [];
    for (var i = debut; i < lignes.length; i++) {
      var ligne = lignes[i].trim();
      if (ligne === "]" || ligne === "}") return { noms: noms, fin: i };
      var m = /^"([^"]+)",?$/.exec(ligne);
      if (m) noms.push(m[1]);
    }
    return { noms: noms, fin: lignes.length };
  }

  function lireEnsemblePython(lignes, debut) {
    var noms = {};
    for (var i = debut; i < lignes.length; i++) {
      var ligne = lignes[i].trim();
      if (ligne === "}" || ligne === "]") return { noms: noms, fin: i };
      var m = /^"([^"]+)",?$/.exec(ligne);
      if (m) noms[m[1]] = true;
    }
    return { noms: noms, fin: lignes.length };
  }

  function palierDuCommentaire(ligne) {
    var m = /#.*[Pp]alier\s+(80\s*%|100\s*%|root)/.exec(ligne);
    if (!m) return null;
    if (m[1] === "80 %") return "Palier 80";
    if (m[1] === "100 %") return "Palier 100";
    return "Root";
  }

  /* Rend {total, paliers: [{nom, outils: [{nom, label, sensible}]}]}.
     Le palier suit les commentaires du fichier, "Base" par défaut. */
  function parseRegistre(source) {
    var lignes = String(source).replace(/\r/g, "").split("\n");
    var noms80 = {};
    var nomsRoot = {};
    var sensibles = {};
    var paliers = [];
    var palierCourant = "Base";
    var dansRegistre = false;

    function palierActif() {
      for (var i = paliers.length - 1; i >= 0; i--) {
        if (paliers[i].nom === palierCourant) return paliers[i];
      }
      var p = { nom: palierCourant, outils: [] };
      paliers.push(p);
      return p;
    }

    for (var i = 0; i < lignes.length; i++) {
      var ligne = lignes[i];
      var coupe = ligne.trim();
      if (coupe === "OUTILS_PALIER_80 = [") {
        var r80 = lireListePython(lignes, i + 1);
        r80.noms.forEach(function (n) { noms80[n] = true; });
        i = r80.fin;
        continue;
      }
      if (coupe === "OUTILS_PALIER_ROOT = [") {
        var rRoot = lireListePython(lignes, i + 1);
        rRoot.noms.forEach(function (n) { nomsRoot[n] = true; });
        i = rRoot.fin;
        continue;
      }
      if (coupe === "OUTILS_SENSIBLES = {") {
        var rSens = lireEnsemblePython(lignes, i + 1);
        Object.keys(rSens.noms).forEach(function (n) { sensibles[n] = true; });
        i = rSens.fin;
        continue;
      }
      if (coupe === "REGISTRE_AFFICHAGE_OUTILS = {") {
        dansRegistre = true;
        palierCourant = "Base";
        continue;
      }
      if (!dansRegistre) continue;
      if (coupe === "}") {
        dansRegistre = false;
        continue;
      }
      var palier = palierDuCommentaire(ligne);
      if (palier) {
        palierCourant = palier;
        continue;
      }
      var entree = /^    "([^"]+)": \{$/.exec(ligne);
      if (entree) {
        var nom = entree[1];
        var label = nom;
        var j = i + 1;
        while (j < lignes.length && lignes[j].trim() !== "},") {
          var mLabel = /"label":\s*"([^"]*)"/.exec(lignes[j]);
          if (mLabel) label = mLabel[1];
          j++;
        }
        i = j;
        palierActif().outils.push({
          nom: nom,
          label: label,
          sensible: Boolean(sensibles[nom] || nomsRoot[nom])
        });
      }
    }

    var total = 0;
    paliers.forEach(function (p) { total += p.outils.length; });
    return { total: total, paliers: paliers };
  }

  /* Totaux de tests cités dans le tableau des agents (§3) : rend
     {total, details: [{ref, total}]}. Vide si le journal ne cite rien. */
  function parseTestsJournal(texteJournal) {
    var details = [];
    var dansSection = false;
    String(texteJournal).replace(/\r/g, "").split("\n").forEach(function (ligne) {
      var titre = /^## (\d+)\./.exec(ligne.trim());
      if (titre) {
        dansSection = Number(titre[1]) === 3;
        return;
      }
      if (!dansSection || ligne.trim().charAt(0) !== "|") return;
      var vals = ligne.trim().replace(/^\||\|$/g, "").split("|").map(function (c) {
        return c.trim();
      });
      if (/^:?-+:?$/.test(vals[0] || "")) return;
      var m = /(\d+)\s+tests?/.exec(vals.join(" "));
      if (m && !/^#$/i.test(vals[0])) {
        details.push({ ref: vals[0], total: Number(m[1]) });
      }
    });
    var total = 0;
    details.forEach(function (d) { if (d.total > total) total = d.total; });
    return { total: total, details: details };
  }

  return { parseRegistre: parseRegistre, parseTestsJournal: parseTestsJournal };
});
