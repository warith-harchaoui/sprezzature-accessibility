# sprezzature-accessibility

[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

🇫🇷 LISEZMOI.md · [🇬🇧 README.md](README.md)

[![logo](assets/logo.png)](https://harchaoui.org/warith/sprezzature/)

Un linter d'accessibilité statique pour HTML. Quatorze règles WCAG/WAI décidables
depuis le code source, sans navigateur, sans DOM, sans réseau. Il s'intègre dans
un hook pre-commit ou une étape CI et fournit une porte rapide et déterministe avant
que toute modification n'atterrisse en production.

Le linter couvre les violations qui représentent la majorité des problèmes
d'accessibilité réels : textes alternatifs manquants, champs sans étiquette, boutons
vides, divs cliquables, fenêtres de dialogue sans bouton de fermeture, attributs lang
absents, ordre des titres inversé, indicateurs d'état par couleur seule, et guards
pour les animations réduites. Cinq de ces règles disposent d'un mode de correction
automatique (`--fix`) pour que la porte puisse se réparer elle-même.

Ce n'est pas un substitut aux tests DOM au moment de l'exécution. Associez-le à
axe-core, Pa11y ou Lighthouse pour les vérifications en navigateur. Cet outil
détecte ce qu'un navigateur ne voit jamais.

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
