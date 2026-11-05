# sprezzature-accessibility

[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%C3%A0%203.13-blue.svg)](https://www.python.org/)

🇫🇷 LISEZMOI.md · [🇬🇧 README.md](README.md)

[![logo](assets/logo.png)](https://sprezzature.ai/)

Une page web est accessible quand une personne qui utilise un lecteur d'écran, qui
navigue au clavier seul (sans souris), ou qui a activé le réglage « mouvement réduit »
de son navigateur, peut malgré tout s'en servir. Ce paquet relit le code source HTML
à la recherche des erreurs qui cassent le plus souvent cette expérience, et rédige le
contenu que ces erreurs laissent le plus souvent de côté : une balise `<img>` sans
texte alternatif est aussi invisible pour un lecteur d'écran que si l'image n'existait
pas sur la page.

La moitié audit est un linter statique : vingt règles issues des WCAG (*Web Content
Accessibility Guidelines*, la norme du W3C qui définit ce que « accessible » veut
dire pour le web) et de WAI-ARIA (*Web Accessibility Initiative, Accessible Rich
Internet Applications* : le vocabulaire d'attributs, `role`, `aria-label` et
consorts, qui permet à un composant fait maison de se décrire aux logiciels
d'assistance), chacune décidable à la seule lecture du texte HTML. Aucun navigateur
ne s'ouvre, aucune page ne s'affiche, aucun JavaScript ne s'exécute : il n'y a donc
pas de DOM (*Document Object Model*, l'arbre d'éléments qu'un navigateur construit
en affichant une page) à inspecter. Le lint n'importe que la bibliothèque standard de
Python, et c'est ce qui le rend assez rapide pour un crochet de pré-commit ou une
étape d'intégration continue (CI) : une porte déterministe avant que la moindre
modification n'atteigne la production.

Les règles couvrent les textes alternatifs manquants, les champs de formulaire sans
étiquette, les boutons vides, les `<div>` cliquables qu'un clavier ne peut pas
atteindre, les fenêtres de dialogue sans moyen de les fermer au clavier, l'attribut
`lang` absent (ce qui casse la prononciation du lecteur d'écran), les niveaux de
titre qui sautent au lieu de s'emboîter dans l'ordre, l'état montré par la seule
couleur (un rouge et un vert qu'une personne daltonienne ne distingue pas), les
animations sans garde de mouvement réduit, l'espacement des lettres resserré sur du
texte de lecture (ce qui ralentit la lecture des personnes dyslexiques), et cinq
contrôles sur les médias temporels : sous-titres, transcriptions, lecture
automatique non muette, commandes au clavier et langue de la piste de sous-titres.
Six de ces vingt règles disposent en plus d'une correction automatique mécanique
(`--fix`), pour que la porte répare elle-même ce qu'elle peut réparer sans risque,
au lieu de se contenter de le signaler.

La moitié fabrication rédige le texte alternatif manquant avec un modèle de vision
local (`qwen3-vl:8b` par Ollama), en suivant l'arbre de décision du W3C sur la
fonction des images. `--fix-alt` le fait sur place, à partir de l'image et du texte
qui l'entoure sur la même page. Rien ne quitte la machine, et chaque proposition
reste un brouillon : une personne la relit avant qu'elle ne soit enregistrée.

Ce paquet ne lit que du code source : il ne peut donc pas détecter ce qui n'apparaît
qu'une fois la page affichée dans un navigateur, l'ordre de parcours au clavier, le
minutage des annonces du lecteur d'écran, le contraste des couleurs sur un fond
réel. Associez-le à axe-core, Pa11y ou Lighthouse, qui pilotent un vrai navigateur,
pour cette couche-là. Les deux approches se complètent : celle-ci est la porte
rapide sans navigateur ; les autres sont la passe plus lente mais fidèle au rendu
réel.

## Comment ça marche

![Schéma de flux. En haut, le HTML que vous tenez alimente deux voies. La voie de gauche fabrique : elle lit la page autour d'une image, interroge un modèle de vision local, et réécrit l'attribut alt dans la page. La voie de droite contrôle : elle lit la source sans navigateur, tranche vingt règles, et rend ses constats en texte ou en JSON, avec le code de sortie 1 dès qu'il y en a un. Les deux voies se rejoignent en un seul résultat, une page qu'un lecteur d'écran lit et qu'un clavier atteint.](https://raw.githubusercontent.com/warith-harchaoui/sprezzature-accessibility/main/assets/comment-ca-marche.svg)

## Fonctionnalités

- 20 règles couvrant img, a, button, div/span, input, dialog, html, tabindex, aria,
  l'ordre des titres, l'état par couleur seule, les gardes motion-reduce,
  l'espacement des lettres sur le texte de lecture, et les médias temporels :
  sous-titres vidéo, transcription audio, lecture automatique non muette,
  commandes au clavier et langue de la piste de sous-titres.
- Correction automatique pour 6 règles (`--fix`) : détection et insertion du
  `lang`, suppression d'aria redondant, rétrogradation du tabindex, suppression
  d'aria-hidden, ajout de la garde motion-reduce, suppression du resserrement de
  lettres. Idempotente : un second passage n'applique rien.
- Rédaction de textes alternatifs (`--fix-alt` pour une page entière,
  `sprezzature-accessibility-alt` pour une image) : six fonctions d'image
  (informative, décorative, fonctionnelle, texte, complexe, groupe), le texte de la
  page comme contexte, une sortie plafonnée à 150 caractères, des résultats mis en
  cache sur disque.
- `sprezzature-accessibility-text-spacing` : le pendant « fabrication » de la règle
  d'espacement des lettres. Il génère un bloc CSS optionnel « lecture confortable »
  aux minima WCAG 1.4.12, pour les pages qui veulent proposer la correction comme
  un réglage visible par le lecteur.
- Sortie texte et JSON, composable avec jq ou tout parseur de CI.
- Code de sortie 1 sur tout constat, 0 si la page est propre : utilisable comme
  porte de pré-commit.
- Python 3.10 à 3.13. Le chemin du lint n'importe que la bibliothèque standard,
  plus `langdetect` s'il est installé (le correcteur de `html-missing-lang` s'en
  sert pour deviner la langue de la page).

## Installation

Une ligne, et c'est tout : le lint, le rédacteur de textes alternatifs, la
détection de langue, l'API HTTP et le serveur MCP.

```bash
pip install sprezzature-accessibility
```

`pip install 'sprezzature-accessibility[dev]'` ajoute l'outillage de test (pytest,
ruff) et rien d'autre.

Le rédacteur a aussi besoin d'Ollama et du modèle sur la machine. Une commande
installe Ollama s'il manque (Homebrew, l'installateur officiel sous Linux, ou winget
sous Windows), démarre son démon et télécharge `qwen3-vl:8b` :

```bash
sprezzature-accessibility-install-alt
```

Les images sont réduites avant d'être envoyées au modèle : `--resize N` limite le
plus grand côté à N pixels (1024 par défaut, 0 envoie les octets d'origine).

### Pour un crochet de pré-commit : deux paquets

Le lint a besoin de la bibliothèque standard plus click, et c'est pour cela qu'il
tient dans un crochet de pré-commit : il tourne en quelques millisecondes, sans
navigateur ni modèle derrière lui. L'essentiel d'une installation complète, ce sont
les surfaces HTTP et MCP, qui ne servent à rien dans un crochet. Donc un crochet
installe le lint et rien d'autre :

```bash
pip install --no-deps sprezzature-accessibility
pip install click
```

Cela fait deux paquets au-dessus d'un venv neuf : click, et celui-ci. C'est énoncé
comme un delta et non comme un total, exprès : ce que `venv` sème est l'affaire de
l'interpréteur, et ça diffère (3.11 ajoute setuptools, 3.13 non). Le delta est ce
que ce paquet peut promettre. Sur une telle installation, `--fix` ne peut pas
deviner la langue d'une page (pas de `langdetect`) : il laisse `html-missing-lang`
à corriger par une personne.

C'est testé à chaque poussée.
`tests/test_the_hook_install_is_the_lint_and_nothing_else.py` construit exactement
ce venv, vérifie par leur nom les paquets qui y ont atterri, et lance la commande
`sprezzature-accessibility-lint` livrée contre une page portant un défaut connu. Et
`tests/test_the_lint_stays_out_of_the_extra.py` vérifie que rien sur le chemin du
lint n'importe les dépendances de rédaction.

## Démarrage rapide

```bash
# Lint d'une page unique
sprezzature-accessibility-lint public/index.html

# Lint récursif d'un répertoire, sortie 1 sur tout constat
sprezzature-accessibility-lint public/

# Sortie JSON pour une chaîne CI
sprezzature-accessibility-lint --format json public/index.html

# Ignorer deux règles
sprezzature-accessibility-lint --ignore heading-skip,motion-no-reduce-guard public/

# Corriger automatiquement ce qui peut l'être
sprezzature-accessibility-lint --fix public/

# Prévisualiser ce que --fix changerait, sans écrire (sortie toujours 0)
sprezzature-accessibility-lint --fix --dry-run public/

# Rédiger sur place les textes alternatifs manquants, puis appliquer les corrections mécaniques
sprezzature-accessibility-lint --fix-alt public/

# Idem, avec des textes alternatifs rédigés en français
sprezzature-accessibility-lint --fix-alt --alt-lang fr public/
```

`--fix-alt` rédige un texte alternatif pour chaque `<img>` qui n'en a pas, en la
traitant comme une image informative, à partir du texte qui entoure cette image dans
le même document et des noms propres qu'on y trouve. Sans `--alt-lang`, la langue
est celle du `<html lang>` de la page, à défaut celle détectée dans le texte de la
page, à défaut la locale de l'environnement (`ALT_LANG`, puis `LC_ALL`, puis
`LANG`). Les images distantes, les images absentes du disque et les
balises qui s'étendent sur plusieurs lignes sont laissées telles quelles et
signalées. Ce passage tourne avant les corrections mécaniques, si bien qu'une seule
invocation laisse la page dans son état final.

### Une image à la fois

```bash
sprezzature-accessibility-alt --kind informative photo.jpg
sprezzature-accessibility-alt --kind functional --context "Submit form" icon.png
sprezzature-accessibility-alt --kind complex --longdesc --in docs/chart.md chart.png
```

Le texte alternatif sort sur stdout. `--kind decorative` n'imprime rien et
n'appelle aucun modèle : une image décorative prend `alt=""`. `--longdesc` écrit en
plus une description longue dans `<image>.longdesc.md`. `--in DOC`, `--vocab FILE`,
`--vocab-from PATH` et `--auto-project` donnent au modèle l'orthographe des noms
propres du projet ; sans `--lang`, la langue est détectée à partir de ce texte.
`--no-cache` contourne le cache pour un passage. `make-alt` est un autre nom de la
même commande.

## Les cinq surfaces

Le même moteur répond sur cinq surfaces.

| Surface | Point d'entrée |
|---|---|
| Bibliothèque | `import sprezzature_accessibility` |
| Ligne de commande | `sprezzature-accessibility` (alias `make-a11y`) et une commande par outil |
| API HTTP (FastAPI) | `uvicorn sprezzature_accessibility.api:app`, ou `docker compose up` |
| Serveur MCP | `sprezzature-accessibility-mcp` |
| Skill d'agent | `SKILL.md`, tenu dans le dépôt central [sprezzature](https://github.com/warith-harchaoui/sprezzature) |

### Bibliothèque

```python
from pathlib import Path

from sprezzature_accessibility import describe, fix_file, lint_file

for f in lint_file(Path("public/index.html")):
    print(f.line, f.rule, f.message)

applied, skipped, remaining = fix_file(Path("public/index.html"), set(), dry_run=True)

alt = describe("hero.jpg", kind="informative", lang="fr", context="Careers page hero")
```

`KINDS` liste les six fonctions d'image. `describe_long` rédige la description
longue d'une image complexe. Les noms de la rédaction (`describe`, `describe_long`,
`detect_lang`, `surrounding_text` et le reste de `__all__`) sont chargés au premier
usage, si bien que `import sprezzature_accessibility` reste aussi léger que le lint.

### Ligne de commande

Une porte d'entrée, construite sur click, avec deux orthographes et quatre outils :

```bash
sprezzature-accessibility --help          # les quatre outils, et ce que fait chacun
sprezzature-accessibility tools           # quels outils peuvent tourner sur cette machine
sprezzature-accessibility lint public/    # identique à sprezzature-accessibility-lint public/
make-a11y lint public/                    # l'orthographe historique de la même commande
```

| Ce qu'elle fait | Sous-commande | Commande propre |
|---|---|---|
| Lint du HTML ; `--fix`, `--fix-alt`, `--dry-run`, `--format`, `--ignore`, `--alt-lang` | `lint` | `sprezzature-accessibility-lint` |
| Génère le CSS de lecture confortable WCAG 1.4.12 | `text-spacing` | `sprezzature-accessibility-text-spacing` |
| Rédige le texte alternatif d'une image | `alt` | `sprezzature-accessibility-alt` (alias `make-alt`) |
| Installe Ollama, le démarre, télécharge `qwen3-vl:8b` | `install-alt` | `sprezzature-accessibility-install-alt` |

Les deux orthographes de la porte d'entrée résolvent vers le même appelable, sur
une table unique (`sprezzature_accessibility/_tools.py`), donc un outil ne peut pas
apparaître dans l'une et manquer dans l'autre. Les commandes propres à chaque outil
sont ce qu'un script ou un crochet devrait appeler. La complétion pour bash et zsh
est imprimée à la fin de `sprezzature-accessibility --help`. Toutes les commandes,
celles de chaque outil et le serveur MCP compris, sont en click : une seule mise en
page de l'aide, `-h` et `-V`, et le code de sortie 2 sur une erreur d'usage.

### API HTTP

```bash
uvicorn sprezzature_accessibility.api:app --host 127.0.0.1 --port 8000
curl -s -X POST localhost:8000/v1/lint \
  -H 'content-type: application/json' \
  -d '{"html": "<img src=\"a.png\">"}'
```

| Route | operation_id | Ce qu'elle renvoie |
|---|---|---|
| `GET /health` | `health` | `{"status": "ok"}` |
| `GET /v1/rules` | `list_rules` | Chaque règle, avec sa sévérité |
| `POST /v1/lint` | `lint_html` | Les constats sur une chaîne HTML, avec le nombre d'erreurs et d'avertissements |
| `GET /v1/kinds` | `list_kinds` | Les six fonctions d'image, chacune avec son usage |
| `POST /v1/alt` | `draft_alt_text` | Un texte alternatif rédigé, et une description longue sur demande |

L'API lint une chaîne, jamais une URL : aller chercher une page pour le compte de
l'appelant en ferait un proxy ouvert. `POST /v1/alt` répond 502 quand le modèle
local est injoignable, 503 quand il manque à l'installation le client du modèle,
et 404 quand le fichier image n'existe pas. La documentation
interactive est sur `/docs`.

Avec Docker, `docker compose up -d` construit l'image et sert l'API sur le port
8000, avec `./work` monté sur `/work`. `docker compose --profile alt up -d` démarre
en plus un conteneur Ollama pour le rédacteur, et le compose pose
`OLLAMA_URL=http://ollama:11434` : le rédacteur envoie chaque appel au modèle à
l'adresse de `OLLAMA_URL` (`http://localhost:11434` si elle est absente), et une
erreur nomme cette même adresse. Le conteneur lance
`sprezzature-accessibility-mcp` : le même port répond aux routes HTTP et au point
MCP sur `/mcp`.

### Serveur MCP

MCP (*Model Context Protocol*) permet à un hôte d'agent d'appeler ces routes comme
des outils.

```bash
sprezzature-accessibility-mcp                      # 127.0.0.1:8000
sprezzature-accessibility-mcp --host 0.0.0.0 --port 9000
```

Il sert la même application FastAPI, avec le point MCP monté sur `/mcp`. Les cinq
outils sont les cinq routes ci-dessus, nommés par leur `operation_id` : `health`,
`list_rules`, `lint_html`, `list_kinds`, `draft_alt_text`. Les valeurs par défaut
viennent de `SPREZZATURE_ACCESSIBILITY_HOST` et `SPREZZATURE_ACCESSIBILITY_PORT`
quand elles sont définies.

## Les règles

| Règle | Sévérité | Description |
|---|---|---|
| `img-missing-alt` | erreur | `<img>` sans attribut alt |
| `img-redundant-aria` | avertissement | `alt=""` avec un role/aria-hidden redondant |
| `a-missing-href` | erreur | `<a>` sans href (utiliser `<button>`) |
| `a-empty` | erreur | `<a>` sans nom accessible |
| `button-empty` | erreur | `<button>` sans nom accessible |
| `div-onclick` | erreur | div/span avec onclick, sans role ni tabindex |
| `input-missing-label` | erreur | `<input>` sans label associé |
| `dialog-missing-close` | erreur | `<dialog>` sans moyen de fermeture |
| `html-missing-lang` | erreur | `<html>` sans attribut lang |
| `tabindex-positive` | erreur | tabindex ≥ 1 casse l'ordre du DOM |
| `aria-hidden-interactive` | erreur | aria-hidden sur un élément interactif encore focalisable |
| `heading-skip` | erreur | les titres sautent un niveau vers le bas |
| `color-only-state` | avertissement | jeton rouge/vert sans icône ni texte |
| `motion-no-reduce-guard` | avertissement | animation sans pair motion-reduce |
| `body-text-tracking-tight` | avertissement | interlettrage resserré sur du texte de lecture |
| `video-missing-captions` | erreur | `<video>` avec du son et sans `<track kind="captions">` (WCAG 1.2.2) |
| `audio-missing-transcript` | erreur | `<audio>` sans alternative textuelle (WCAG 1.2.1) |
| `track-missing-srclang` | avertissement | `<track>` sans `srclang` : langue des sous-titres inconnue |
| `media-missing-controls` | erreur | `<video>`/`<audio>` sans rien à actionner au clavier (WCAG 2.1.1) |
| `media-autoplay-sound` | erreur | `autoplay` non muet, qui couvre un lecteur d'écran (WCAG 1.4.2) |

La sévérité est celle que rapporte l'API HTTP. La ligne de commande sort en 1 sur
tout constat, avertissements compris. Six de ces règles portent aussi un correcteur
mécanique, appliqué par `--fix`.

## Licence

BSD-3-Clause. Copyright 2026 Warith HARCHAOUI.
