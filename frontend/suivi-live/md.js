/* Petit rendu markdown maison, juste ce que les docs du suivi
   utilisent : titres, paragraphes, listes, tableaux, code, gras,
   liens, citations, séparateurs. Volontairement sans dépendance
   pour garder la page légère. */
(function (racine, fabrique) {
  if (typeof module === "object" && module.exports) module.exports = fabrique();
  else racine.SuiviMd = fabrique();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var JOKER = "##SUIVICODE##";

  function echapper(texte) {
    return texte
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function gras(texte) {
    return texte.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  }

  /* En ligne : code, liens [texte](adresse), adresses nues, gras.
     Reçoit du texte déjà échappé, ne réintroduit que nos balises. */
  function inline(texte) {
    var codes = [];
    var s = texte.replace(/`([^`]+)`/g, function (m, c) {
      codes.push(c);
      return JOKER + (codes.length - 1) + JOKER;
    });
    s = s.replace(/\[([^\]]+)\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g, function (m, t, u) {
      var externe = /^https?:\/\//i.test(u);
      return (
        '<a href="' + u + '"' +
        (externe ? ' target="_blank" rel="noopener"' : "") +
        ">" + gras(t) + "</a>"
      );
    });
    s = s.replace(/(^|[\s(])(https?:\/\/[^\s<)]+)/g, '$1<a href="$2" target="_blank" rel="noopener">$2</a>');
    s = gras(s);
    var motifJoker = new RegExp(JOKER + "(\\d+)" + JOKER, "g");
    s = s.replace(motifJoker, function (m, i) {
      return "<code>" + codes[Number(i)] + "</code>";
    });
    return s;
  }

  function ligneTableau(rang) {
    var t = rang.trim().replace(/^\||\|$/g, "");
    return t.split("|").map(function (c) { return c.trim(); });
  }

  function estSeparateur(cellules) {
    return cellules.length > 0 && cellules.every(function (c) { return /^:?-+:?$/.test(c); });
  }

  function tableau(rangs) {
    var lignes = rangs.map(ligneTableau);
    var debutCorps = 0;
    var html = '<div class="tableau"><table>';
    if (lignes.length >= 2 && estSeparateur(lignes[1])) {
      html += "<thead><tr>" + lignes[0].map(function (c) {
        return "<th>" + inline(echapper(c)) + "</th>";
      }).join("") + "</tr></thead>";
      debutCorps = 2;
    }
    html += "<tbody>";
    for (var i = debutCorps; i < lignes.length; i++) {
      html += "<tr>" + lignes[i].map(function (c) {
        return "<td>" + inline(echapper(c)) + "</td>";
      }).join("") + "</tr>";
    }
    return html + "</tbody></table></div>";
  }

  function liste(elements) {
    var sommets = [];
    elements.forEach(function (el) {
      if (el.prof === 0 || sommets.length === 0) sommets.push({ el: el, enfants: [] });
      else sommets[sommets.length - 1].enfants.push(el);
    });
    var balise = elements.length > 0 && elements[0].puce === "o" ? "ol" : "ul";
    var html = "<" + balise + ">";
    sommets.forEach(function (s) {
      html += "<li>" + inline(echapper(s.el.texte));
      if (s.enfants.length > 0) {
        var enfantBalise = s.enfants[0].puce === "o" ? "ol" : "ul";
        html += "<" + enfantBalise + ">" + s.enfants.map(function (e) {
          return "<li>" + inline(echapper(e.texte)) + "</li>";
        }).join("") + "</" + enfantBalise + ">";
      }
      html += "</li>";
    });
    return html + "</" + balise + ">";
  }

  function debutBloc(tronque) {
    return (
      /^#{1,4}\s/.test(tronque) ||
      tronque.indexOf("```") === 0 ||
      tronque.charAt(0) === "|" ||
      tronque.charAt(0) === ">" ||
      /^[-*]\s/.test(tronque) ||
      /^\d+[.)]\s/.test(tronque) ||
      /^(-{3,}|\*{3,}|_{3,})$/.test(tronque)
    );
  }

  function rendre(source) {
    var lignes = String(source).replace(/\r/g, "").split("\n");
    var html = [];
    var i = 0;
    while (i < lignes.length) {
      var ligne = lignes[i];
      var coupe = ligne.trim();
      if (coupe === "") { i++; continue; }
      if (coupe.indexOf("```") === 0) {
        var code = [];
        i++;
        while (i < lignes.length && lignes[i].trim().indexOf("```") !== 0) {
          code.push(lignes[i]);
          i++;
        }
        i++;
        html.push("<pre><code>" + echapper(code.join("\n")) + "</code></pre>");
        continue;
      }
      var titre = /^(#{1,4})\s+(.*)$/.exec(coupe);
      if (titre) {
        html.push("<h" + titre[1].length + ">" + inline(echapper(titre[2])) + "</h" + titre[1].length + ">");
        i++;
        continue;
      }
      if (/^(-{3,}|\*{3,}|_{3,})$/.test(coupe)) {
        html.push("<hr>");
        i++;
        continue;
      }
      if (coupe.charAt(0) === "|") {
        var rangs = [];
        while (i < lignes.length && lignes[i].trim().charAt(0) === "|") {
          rangs.push(lignes[i]);
          i++;
        }
        html.push(tableau(rangs));
        continue;
      }
      if (coupe.charAt(0) === ">") {
        var citation = [];
        while (i < lignes.length && lignes[i].trim().charAt(0) === ">") {
          citation.push(lignes[i].trim().replace(/^>\s?/, ""));
          i++;
        }
        html.push("<blockquote><p>" + inline(echapper(citation.join(" "))) + "</p></blockquote>");
        continue;
      }
      var marqueur = /^(\s*)([-*]|\d+[.)])\s+(.*)$/.exec(ligne);
      if (marqueur) {
        var elements = [];
        while (i < lignes.length) {
          var suivante = lignes[i];
          if (suivante.trim() === "") { i++; break; }
          var m2 = /^(\s*)([-*]|\d+[.)])\s+(.*)$/.exec(suivante);
          if (m2) {
            elements.push({
              prof: m2[1].length,
              puce: /^\d/.test(m2[2]) ? "o" : "u",
              texte: m2[3]
            });
            i++;
            continue;
          }
          if (/^\s+\S/.test(suivante) && elements.length > 0) {
            elements[elements.length - 1].texte += " " + suivante.trim();
            i++;
            continue;
          }
          break;
        }
        html.push(liste(elements));
        continue;
      }
      var paragraphe = [coupe];
      i++;
      while (i < lignes.length) {
        var courante = lignes[i].trim();
        if (courante === "" || debutBloc(courante)) break;
        paragraphe.push(courante);
        i++;
      }
      html.push("<p>" + inline(echapper(paragraphe.join(" "))) + "</p>");
    }
    return html.join("\n");
  }

  return { rendre: rendre, inline: inline, echapper: echapper };
});
