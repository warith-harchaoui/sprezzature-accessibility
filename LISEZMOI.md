# sprezzature-accessibility

[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

🇫🇷 LISEZMOI.md · [🇬🇧 README.md](README.md)

[![logo](assets/logo.png)](https://harchaoui.org/warith/sprezzature/)

Une page web est accessible quand une personne qui utilise un lecteur d'écran, qui
navigue au clavier seul (sans souris), ou qui a activé le réglage « mouvement réduit »
de son navigateur, peut malgré tout s'en servir. Cet outil relit le code source HTML
à la recherche des erreurs qui cassent le plus souvent cette expérience : une balise
`<img>` sans texte alternatif est aussi invisible pour un lecteur d'écran que si
l'image n'existait tout simplement pas sur la page.

C'est un linter statique : quatorze règles issues des WCAG (*Web Content
Accessibility Guidelines*, la norme du W3C qui définit ce que « accessible » veut
dire pour le web) et de WAI-ARIA (le vocabulaire d'attributs, `role`, `aria-label`
et consorts, qui permet à un composant fait maison de se décrire aux logiciels
d'assistance), chacune décidable à la seule lecture du texte HTML. Aucun navigateur
ne s'ouvre, aucune page ne s'affiche, aucun JavaScript ne s'exécute : il n'y a donc
pas de DOM (l'arbre d'éléments qu'un navigateur construit en affichant une page) à
inspecter, et rien à installer en dehors de Python lui-même. C'est ce qui rend
l'outil assez rapide pour un hook pre-commit ou une étape d'intégration continue
(CI) : une porte déterministe avant que la moindre modification n'atteigne la
production.

Les violations couvertes représentent la majorité des problèmes d'accessibilité
réels : textes alternatifs manquants, champs de formulaire sans étiquette, boutons
vides, `<div>` cliquables qu'un clavier ne peut pas atteindre, fenêtres de dialogue
sans moyen de les fermer au clavier, attribut `lang` absent (ce qui casse la
prononciation du lecteur d'écran), niveaux de titre qui sautent au lieu de s'emboîter
dans l'ordre, état montré par la seule couleur (un rouge et un vert qu'une personne
daltonienne ne distingue pas), et animations sans moyen de les réduire pour qui y est
sensible. Cinq de ces quatorze règles disposent en plus d'une correction automatique
mécanique (`--fix`), pour que la porte répare elle-même ce qu'elle peut réparer sans
risque, au lieu de se contenter de le signaler.

Cet outil ne lit que du code source : il ne peut donc pas détecter ce qui n'apparaît
qu'une fois la page réellement affichée dans un navigateur, l'ordre de parcours au
clavier, le minutage des annonces du lecteur d'écran, le contraste des couleurs sur
un fond réel. Associez-le à axe-core, Pa11y ou Lighthouse, qui pilotent un vrai
navigateur, pour cette couche-là. Les deux approches se complètent, elles ne se
remplacent pas : celui-ci est la porte rapide sans navigateur ; les autres sont la
passe plus lente mais fidèle au rendu réel.

## Fonctionnalités

- 14 règles couvrant img, a, button, div/span, input, dialog, html, tabindex, aria,
  ordre des titres, état par couleur seule, et guards motion-reduce
- Correction automatique pour 5 règles : détection et insertion du lang, suppression
  d'aria redondant, rétrogradation du tabindex, suppression d'aria-hidden, ajout du
  guard motion-reduce
- Sortie texte et JSON, composable avec jq ou tout parseur CI
- Code de sortie 1 sur tout résultat (0 si propre), utilisable comme porte pre-commit
- Stdlib Python uniquement à l'exécution : Python 3.10+, pas de pip install requis
- `langdetect` optionnel pour le correcteur automatique `html-missing-lang`

## Démarrage rapide

```bash
# Lint d'une page unique
python scripts/lint_a11y.py public/index.html

# Lint récursif d'un répertoire, sortie 1 sur tout résultat
python scripts/lint_a11y.py public/

# Sortie JSON pour une chaîne CI
python scripts/lint_a11y.py --format json public/index.html

# Ignorer deux règles
python scripts/lint_a11y.py --ignore heading-skip,motion-no-reduce-guard public/

# Corriger automatiquement ce qui peut l'être
python scripts/lint_a11y.py --fix public/

# Prévisualiser sans écrire
python scripts/lint_a11y.py --fix --dry-run public/
```

## Installation

```bash
pip install sprezzature-accessibility
# Avec détection de langue pour le correcteur html-missing-lang :
pip install "sprezzature-accessibility[lang]"
```

Ou exécution directe sans installation :

```bash
python scripts/lint_a11y.py public/
```

## Licence

BSD-3-Clause. Copyright 2026 Warith HARCHAOUI.
