# Paysage

Les outils d'accessibilité se répartissent en deux familles selon leur façon
d'inspecter une page. Un outil **statique** lit le texte source HTML, comme
le ferait un œil humain ; il n'ouvre jamais de navigateur. Un outil **DOM
dynamique** pilote un vrai navigateur, le laisse afficher la page en entier
pour construire un DOM (l'arbre d'éléments qu'un navigateur assemble en
affichant une page), puis inspecte cet arbre vivant, ce qui permet de
détecter des problèmes qu'une simple lecture du source ne révèle pas, au
prix d'avoir besoin d'un moteur de navigateur pour fonctionner. Voici la
comparaison entre `sprezzature-accessibility`, un outil statique, et les
principaux outils de test d'accessibilité disponibles aujourd'hui, la
plupart fonctionnant en DOM dynamique.

## Comparaison des outils

| Outil | Type | Navigateur requis | Correctif auto | Compatible CI | Python |
|---|---|---|---|---|---|
| **sprezzature-accessibility** | Linter statique | Non | Oui (5 règles) | Oui | Oui |
| axe-core | DOM dynamique | Oui | Non | Oui (via CLI) | Non |
| Pa11y | DOM dynamique | Oui (Chromium) | Non | Oui | Non |
| WAVE | Extension navigateur | Oui | Non | Non | Non |
| htmlhint | HTML statique | Non | Non | Oui | Non |

### Notes par dimension

| Dimension | sprezzature-accessibility | axe-core | Pa11y | WAVE |
|---|---|---|---|---|
| Couverture des règles | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Vitesse (CI) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| Installation sans dépendance | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ | N/A |
| Correction automatique | ⭐⭐⭐ | ⭐ | ⭐ | ⭐ |
| Faux positifs | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

D'autres fichiers PAYSAGE de cette suite passent leur table dans
[`standpoint`](https://github.com/warith-harchaoui/standpoint) et montrent une carte de
positionnement. Celui-ci non, et la raison tient à la taille de la table : quatre options
ne portent au plus que trois directions indépendantes, donc deux axes en gardent deux sur
trois. La projection a été faite pour vérifier : elle annonce **99,4 % de la variance** —
un chiffre qui se lit comme un résultat fort et qui n'est qu'une arithmétique sur le fait
de n'avoir presque rien eu à projeter. La table ci-dessus est assez petite pour être lue
directement, et c'est le meilleur instrument ici.

## Quand utiliser quoi

Utilisez `sprezzature-accessibility` comme **première porte** dans
pre-commit et CI : il détecte les violations évidentes en quelques
millisecondes, sans Chromium à démarrer. Complétez avec axe-core ou
Pa11y dans un job de tests navigateur séparé pour la couverture DOM
dynamique.

WAVE convient mieux aux audits manuels et à l'exploration : il fournit
une surimpression visuelle qui aide un humain à comprendre le problème
en contexte.

htmlhint vérifie la syntaxe HTML et quelques règles structurelles, pas
l'accessibilité. Les deux outils sont complémentaires.
