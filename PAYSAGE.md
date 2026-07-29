# Paysage

Comparaison de `sprezzature-accessibility` avec les principaux outils
de test d'accessibilité.

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
