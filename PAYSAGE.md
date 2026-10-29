# Paysage

`sprezzature-accessibility` est la brique d'accessibilité de la suite
[sprezzature](https://sprezzature.ai/), dix paquets Python pour fabriquer du
contenu web de qualité publication. Elle fait deux choses que le reste du
domaine tient séparées : elle audite le source HTML sur vingt défauts WCAG
(Web Content Accessibility Guidelines, la norme du W3C qui définit ce que veut
dire « accessible » sur le web) et WAI-ARIA (Web Accessibility Initiative,
Accessible Rich Internet Applications, le vocabulaire d'attributs qui permet à
un composant sur mesure de se décrire aux outils d'assistance) décidables sans
navigateur, puis elle rédige le texte alternatif qu'elle vient de vous signaler
comme manquant.

## Sa place dans l'écosystème

```
suite sprezzature
├── sprezzature-accessibility  ← ce paquet (20 règles statiques, 6 avec correctif)
├── sprezzature-colors         (contraste, simulation des daltonismes)
├── sprezzature-ux-laws        (30 lois d'UX, 8 décidables depuis le source)
├── sprezzature-ui             (les écrans que celle-ci audite ensuite)
├── sprezzature-figures        (167 types de graphiques, SVG écrit directement)
├── sprezzature-maps           (les mêmes chiffres attachés à de vrais lieux)
├── sprezzature-cli-gui        (un formulaire web sur un outil en ligne de commande)
├── sprezzature-publish        (du Markdown à un site trouvable, narration comprise)
├── sprezzature-audio          (parole vers texte, texte vers parole)
└── sprezzature-video          (ce qu'un film affirme d'un projet, vérifié)
```

Ce qui vient avant : `sprezzature-ui` écrit le balisage, `sprezzature-publish`
transforme des documents en pages, `sprezzature-figures` écrit le SVG qu'elles
embarquent. Ce qui vient après : un moteur piloté par navigateur, axe-core,
Pa11y ou Lighthouse, pour tout ce qu'une page rendue révèle et qu'un fichier
source ne peut pas montrer. La brique sœur qui fait le travail voisin est
`sprezzature-colors` : le contraste est une question d'accessibilité à laquelle
ce paquet ne répond délibérément pas, parce qu'un rapport de contraste se
calcule sur la couleur qu'un pixel finit par prendre, et c'est un résultat de
rendu. `sprezzature-audio` tient l'autre moitié de l'histoire des médias : ce
paquet vérifie qu'une piste de sous-titres est déclarée, celui-là vérifie si
les sous-titres sont lisibles.

## Quand la choisir

- **Un crochet de pré-commit sur un dépôt de gabarits HTML.** Le lint
  n'utilise que la bibliothèque standard et lit une page typique de 16 Kio en
  2,3 ms sur un portable Apple série M. Rien à démarrer, pas de Chromium à
  télécharger, pas d'image de conteneur à faire grossir.
- **Une porte d'intégration continue (CI) dans une image Python minimale.**
  Code de sortie 1 dès qu'il y a un signalement, 0 si c'est propre, JSON pour
  tout ce qui doit relire le résultat. Aucune chaîne Node n'est nécessaire, ce
  qui compte dans un dépôt qui n'en a pas par ailleurs.
- **Une page avec de la vidéo ou de l'audio.** Cinq des vingt règles relèvent
  de WCAG 1.2 et de ses voisines : piste de sous-titres présente, transcription
  ou nom accessible sur `<audio>`, `srclang` sur chaque `<track>`, commandes
  qu'un clavier peut actionner, et `autoplay` non muet. C'est la partie de la
  norme que le reste du domaine traite comme manuelle. axe-core a déprécié sa
  règle `audio-caption` et Lighthouse n'en a jamais livré.
- **Une image sans alt, sur une page qui dit à quoi sert l'image.**
  `--fix-alt` rédige l'attribut avec un modèle de vision local, en lisant
  l'image et les quatre cents caractères de part et d'autre de ce `<img>` dans
  ce document-là, plus les noms propres qui en sont extraits. Rien ne quitte la
  machine.
- **Une discussion d'achat où le code source ne doit pas sortir de la
  maison.** L'extension d'éditeur du linter de Deque appelle un serveur
  hébergé. Celui-ci n'appelle rien, et le modèle derrière `--fix-alt` tourne
  sur votre matériel.

## Quand prendre autre chose

- **axe-core**, quand vous voulez le moteur sur lequel l'industrie s'est déjà
  entendue. Quatre-vingt-quatorze règles actives contre les vingt de ce paquet,
  une conception documentée sans faux positifs, un compartiment `incomplete`
  pour tout ce qu'il ne peut pas trancher, et des adaptateurs pour Playwright,
  Cypress, Jest, WebdriverIO et Puppeteer. C'est aussi le seul ici à avoir un
  serveur Model Context Protocol (MCP) officiel, livré en 2026. Si vous ne
  faites tourner qu'un seul outil d'accessibilité, faites tourner celui-là.
- **Pa11y**, quand vous voulez une seule commande qui garde une liste d'URL en
  CI et que les trois cents mégaoctets de Chrome qui l'accompagnent ne vous
  gênent pas. `pa11y-ci` fusionne deux moteurs, axe-core et un fork maintenu de
  HTML_CodeSniffer, et ses drapeaux `--threshold` et `--standard WCAG2AA` sont
  une meilleure ergonomie de CI que tout ce que ce paquet propose.
- **Microsoft Accessibility Insights**, quand la question est l'ordre de
  tabulation. Sa vue Tab Stops dessine le chemin du focus par-dessus la page
  vivante, et aucune lecture statique du source ne peut produire cette image.
  C'est gratuit, et c'est ce qu'il y a de plus fort en accès libre sur le seul
  mode de défaillance auquel un linter est structurellement aveugle.
- **axe DevTools Linter (Deque)**, quand le balisage est du JSX, des composants
  Vue monofichier, des gabarits Angular, du Liquid ou du HTL plutôt que du
  `.html`. Quarante-quatre règles, des intégrations éditeur et CI, une API REST,
  et une entreprise derrière. Ce paquet lit du HTML avec le `html.parser` de
  Python et n'apprendra pas la syntaxe JavaScript.
- **Biome**, quand le dépôt est déjà en JavaScript ou TypeScript. La version
  2.4 a ajouté quinze règles d'accessibilité HTML écrites en Rust, dont
  `useMediaCaption`, et il est plus rapide que tout le reste de cette table.
- **AltText.ai ou Azure AI Vision**, quand dix mille photographies de produits
  dans un système de gestion de contenu ont besoin d'un texte alternatif cette
  semaine. Un portable qui fait tourner un modèle n'est pas la bonne forme de
  machine pour ce travail.
- **Siteimprove, Level Access ou QualiBooth**, quand ce qu'il faut vraiment est
  un rapport signé, un tableau de bord qu'un responsable conformité lit, et
  quelqu'un à appeler. Rien de tout cela n'est le métier d'un linter.

## Les idées à prendre

Vingt-deux outils concurrents ont été lus pour ce document. Étudier un
concurrent sans rien en rapporter est du travail perdu ; voici donc ce qui vaut
la peine d'être pris, le meilleur rapport d'abord. Deux entrées sont des refus,
avec leur raison, ce qui est une entrée valable.

**[IBM Equal Access](https://github.com/IBMa/equal-access/blob/main-4.x/accessibility-checker/README.md) :
ce qui s'affiche et ce qui fait échouer sont deux questions distinctes.** Son
assertion de CI sépare `reportLevels` (ce qui apparaît dans la sortie) de
`failLevels` (ce qui fait échouer l'assertion), et ajoute un fichier de
référence pour qu'une page existante puisse être adoptée sans faire rougir la
porte dès le premier jour. Ici, la table des sévérités existe déjà : `_SEVERITY`
dans `sprezzature_accessibility/api.py` marque cinq des vingt règles comme des
avertissements, et la ligne de commande ne la voit pas. `lint_a11y.py` sort en 1
au moindre signalement, donc un avertissement `color-only-state` fait échouer
une construction exactement aussi durement qu'un `<img>` sans alt du tout. Le
travail : déplacer `_SEVERITY` à côté de `ALL_RULES`, donner un champ
`severity` à `Finding`, ajouter `--fail-on error`. Coût : une après-midi. C'est
en premier parce que le paquet a déjà cette idée et n'en a câblé que la moitié.

**[axe-core](https://github.com/dequelabs/axe-core) : un troisième résultat
entre le succès et l'échec.** Chaque élément testé tombe dans l'un de quatre
compartiments, `violation`, `pass`, `incomplete` ou `inapplicable`, et tout ce
que le moteur ne peut pas trancher va dans `incomplete` plutôt que dans les
violations ; cinq règles portent `reviewOnFail: true` pour qu'un échec y soit
routé par conception. C'est comme cela qu'axe tient sa réputation de zéro faux
positif sans perdre le signalement. Ici, `check_dialog_close` dans
`lint_a11y.py` reconnaît un bouton de fermeture en comparant à cinq mots codés
en dur en anglais, en français et en allemand, et `references/lint-rules.md`
admet déjà par écrit que toute autre langue produira un faux positif. Cette
règle, et `color-only-state`, appartiennent à un compartiment `review`, signalé
à part et hors du code de sortie par défaut. Coût : une demi-journée en plus de
l'entrée précédente, et ce doit être la même après-midi, parce qu'un niveau de
sévérité inventé deux fois est un niveau de sévérité qui diverge.

**[AltText.ai](https://alttext.ai/docs/webui/adding-images/) : un style maison
appliqué à chaque brouillon.** Son « Final Pass » est une instruction que le
client écrit une fois, jusqu'à 768 caractères, ajoutée à chaque texte
alternatif que le service produit ; c'est ainsi qu'une boutique obtient
« chaussure de course homme » plutôt que « une chaussure ». Ici, `--fix-alt`
n'a aucun moyen de porter une règle maison : un site de documentation qui veut
« nommer la commande, pas la capture d'écran », ou une rédaction qui veut les
noms de famille en capitales, doit modifier
`scripts/prompts/alt_short_informative.yaml` et perdre la modification à la
mise à jour suivante. Les prompts sont déjà du YAML à champs substitués, donc
un drapeau `--alt-style FICHIER` qui atterrit dans le même emplacement `{ctx}`
que `surrounding_text` tient en une demi-journée. Ce qu'AltText.ai rate mérite
d'être dit dans la même phrase : cette instruction écrite à la main est son
*seul* canal de contexte, puisque sa documentation montre que le texte courant
de la page n'est jamais envoyé au modèle.

**[Pa11y](https://github.com/pa11y/pa11y) : garder par niveau de conformité,
pas par nom de règle.** Pa11y accepte `--standard WCAG2A`, `WCAG2AA` ou
`WCAG2AAA`, donc une équipe garde le niveau A sans nommer une seule règle. Ici,
`--ignore` n'accepte que des identifiants de règles, ce qui oblige une équipe
qui veut le niveau A seul à énumérer chaque règle AA à la main et à maintenir
cette liste à mesure que des règles arrivent. La correspondance existe déjà, en
prose, dans les deux tables de `references/lint-rules.md` ; elle demande à être
un champ `wcag` sur chaque entrée d'`ALL_RULES` pour que `--level A` devienne un
sélecteur d'une ligne. Coût : une après-midi pour la correspondance, et elle est
payée deux fois, puisque l'entrée SARIF ci-dessous a besoin du même champ pour
son `helpUri`. Le `--threshold` de Pa11y est la moitié à refuser : un budget de
signalements tolérés est un budget qui ne fait que grossir.

**[axe-sarif-converter](https://github.com/microsoft/axe-sarif-converter) :
SARIF comme troisième format de sortie.** Microsoft livre un convertisseur
précisément parce qu'axe n'émet pas de SARIF (Static Analysis Results
Interchange Format, le schéma JSON que lit le code scanning de GitHub), et
SARIF est ce qui transforme des signalements en annotations posées sur les
lignes d'une demande de fusion plutôt qu'en lignes d'un journal que personne
n'ouvre. Ici : `--format sarif` à côté de `text` et `json` dans `lint_a11y.py`,
écrit avec `json.dump` et sans nouvelle dépendance. Les champs traînent déjà :
le `ruleId` est `Finding.rule`, le message est `Finding.message`, le `helpUri`
est l'ancre dans `references/lint-rules.md`. Coût : une journée, dont l'essentiel
passe à lire le schéma plutôt qu'à écrire du code.

**[html-validate](https://html-validate.org/wcag.html) : publier ce que l'outil
ne vérifie pas.** Il tient une page qui liste WCAG 2.2 critère par critère avec
sa couverture marquée, y compris les critères auxquels il ne touche pas, et
cette page fait plus pour sa crédibilité que n'importe quel décompte de règles.
Ici, `references/lint-rules.md` dit déjà cela règle par règle, ce qui est le
sens facile. La moitié qui manque est la vue inverse : les critères de succès
sans aucune règle, là où un lecteur apprend que le contraste est cédé à
`sprezzature-colors` exprès, que l'ordre du focus demande axe-core, et que
WCAG 1.4.12 est couvert ici par un proxy statique et non par un test de
conformité. Coût : une journée d'écriture, pas de code, et c'est l'honnêteté la
moins chère de cette liste.

**[axe DevTools Linter](https://docs.deque.com/linter/4.0.0/en/linter-home/) :
les types de fichiers, et pourquoi celui-ci ne suivra pas. Refusé.** Le linter
de Deque lit du JSX, du TSX, des composants Vue monofichier, des gabarits
Angular, du Liquid, du HTL et du Markdown, pas seulement du `.html`, et c'est
là que vit vraiment le balisage de la plupart des équipes. Le refus mérite
d'être énoncé plutôt que laissé implicite : l'analyseur ici est le
`html.parser` de la bibliothèque standard, et lui apprendre le JSX voudrait
dire livrer un analyseur JavaScript, c'est-à-dire la seule dépendance qui
mettrait fin à la promesse « bibliothèque standard seule » sur laquelle ce
paquet est bâti. La réponse honnête reste celle que le README donne déjà : un
gabarit qui se compile en HTML est linté après compilation.

**accessiBe et UserWay : la réparation qui ne répare rien. Refusé.** Une
surcouche rapièce le DOM vivant (Document Object Model, l'arbre qu'un
navigateur construit en affichant une page) dans le navigateur du visiteur, ce
qui laisse le défaut dans le source et le réexpédie au déploiement suivant. La
Federal Trade Commission des États-Unis a accepté un ordre de consentement
contre accessiBe en janvier 2025, définitif en avril, assorti d'un paiement
d'un million de dollars, interdisant à l'entreprise d'affirmer qu'un produit
automatique peut rendre un site conforme à WCAG sans preuve compétente et
fiable ; une action collective contre UserWay a été déposée en juillet 2024 par
un client qui avait acheté la surcouche et s'est fait assigner quand même. Ici,
le refus est déjà inscrit dans la conception, dans la docstring même de
`fill_alt.py`, et la phrase à en extraire est que `--fix-alt` écrit un brouillon
dans le fichier, là où une personne le relit, plutôt qu'un rustine dans la page,
là où personne ne le fait. Coût : rien, et c'est pour cela qu'elle a sa place
dans une liste sur le rendement.

## Comment le domaine se découpe

**Statique contre dynamique.** Un outil statique lit le texte source HTML,
comme le ferait un œil humain, et n'ouvre jamais de navigateur. Un outil
dynamique pilote un vrai navigateur, le laisse afficher la page dans un DOM, et
inspecte cet arbre vivant. La séparation ne porte pas sur la qualité, elle
porte sur ce que chacun peut prouver. Seul l'outil dynamique peut mesurer un
texte contre le fond sur lequel il atterrit, ou parcourir l'ordre du focus
qu'un clavier suivra vraiment. Seul l'outil statique peut nommer le fichier et
la ligne, tourner avant que la page existe, et finir en quelques millisecondes.
La famille dynamique est de loin la plus grande des deux : axe-core, Pa11y,
Lighthouse, WAVE, IBM Equal Access et Accessibility Insights y vivent tous, et
quatre de ces six sont axe-core habillé autrement. La famille statique est
mince, et un seul acteur commercial en possède l'essentiel.

**Détecter contre produire.** Presque tout dans cette table signale puis
s'arrête. Une seconde famille, plus récente, fait l'inverse : elle écrit le
contenu qui manque à la page, ce qui veut dire en pratique le texte alternatif.
AltText.ai, AutoAlt.ai, Azure AI Vision et les modèles à poids ouverts que vous
pouvez faire tourner vous-même s'y trouvent. Les deux familles ne se recouvrent
presque pas, et c'est cet écart que ce paquet vise. Le linter qui a trouvé
l'alt manquant est ce qu'il y a de mieux placé pour l'écrire, parce qu'il tient
déjà le document dans lequel l'image se trouve, et que ce qu'une image *fait*
sur une page est une question sur la page plutôt que sur les pixels. L'[arbre
de décision alt](https://www.w3.org/WAI/tutorials/images/decision-tree/) du W3C
trie les images par fonction, informative, décorative, fonctionnelle, texte,
complexe, groupe, et la fonction n'est lisible qu'en contexte ; le guide de
WebAIM sur le texte alternatif a une section intitulée « Context is Everything »
et donne à la même photographie quatre textes alternatifs corrects sur quatre
pages différentes.

C'est l'argument des normes, et il y en a un mesuré à côté. Nikita SRIVATSAN,
Sofia SAMANIEGO, Omar FLOREZ et Taylor BERG-KIRKPATRICK, à ICLR 2024, ont
entraîné sur 371 000 images appariées à leur texte alternatif et au message qui
les entourait : un modèle conditionné à la fois sur l'image et sur le texte
alentour dépasse de plus du double, en BLEU@4, les travaux fondés sur l'image
seule. Ananya GUBBI MOHANBABU et Amy PAVEL, à ASSETS 2024, ont soumis des
descriptions sensibles au contexte à douze personnes aveugles ou malvoyantes,
qui les ont notées significativement plus haut en qualité, en pertinence, en
capacité d'imagination et en plausibilité ; leur résumé dit platement que les
outils existants décrivent les images sans tenir compte du contexte de la page.
Les fournisseurs hébergés ne le font toujours pas. La documentation
d'AltText.ai montre que ses canaux de contexte sont un champ de mots-clés, un
champ de nom de produit et une instruction que le client tape une fois ; le
texte courant de la page n'est jamais envoyé. Le point d'entrée de légendage
d'Azure prend une image et rien d'autre.

C'est aussi là qu'un modèle local cesse d'être un compromis pour devenir
l'exigence. `qwen3-vl:8b` est un téléchargement de six gigaoctets avec une
fenêtre de contexte de 256 000 jetons, donc le paragraphe autour de l'image, le
titre de section au-dessus et le vocabulaire propre au projet tiennent tous
dans un seul prompt, sans coût par image et sans que rien ne quitte la machine.
Une interface facturée à l'image n'a aucune raison de vouloir une page de
jetons supplémentaires à chaque appel.

**Bibliothèque contre produit, et la question des surcouches.** Une troisième
séparation traverse les deux : installe-t-on une bibliothèque ou achète-t-on un
résultat ? Siteimprove, Level Access et QualiBooth vendent de la surveillance,
des tableaux de bord et quelqu'un à appeler, à quatre et cinq chiffres par an.
Les surcouches, accessiBe et UserWay, vendent la promesse qu'une balise de
script répare le site, et cette promesse coûte désormais cher en justice. Elles
sont dans la table parce qu'elles sont sur le marché, et parce qu'une
comparaison qui omet discrètement la catégorie la plus vendue de son propre
domaine n'est pas une comparaison. Elles notent mal en précision du signal et
en réparation pour des raisons que d'autres ont déjà écrites : l'Overlay Fact
Sheet, maintenu par Karl GROVES et portant plus d'un millier de signataires,
parmi lesquels des rédacteurs des spécifications WCAG, ARIA et HTML et des
contributeurs de NVDA et JAWS, énonce en une ligne que l'application
automatique de textes alternatifs aux images n'est pas fiable. UsableNet a
rapporté en 2026 qu'environ une entreprise assignée sur cinq avait déjà un
widget d'accessibilité installé.

**Le plafond dont personne ne sort.** L'étude de Deque sur environ treize mille
pages auditées place la détection automatique à environ 57 % des problèmes en
volume, et entre 20 % et 30 % quand on compte en part de critères de succès
WCAG plutôt qu'en nombre de problèmes. Un essai indépendant d'axe-core contre
le corpus de référence du W3C pour l'Accessibility Conformance Testing attrape
37,5 % des exemples en échec. Ces deux chiffres sont constamment confondus dans
la documentation commerciale, et aucun outil de cette table ne discute ce
plafond. L'édition 2026 du WebAIM Million a trouvé des échecs WCAG détectés sur
95,9 % du premier million de pages d'accueil, un texte alternatif manquant sur
53,1 % d'entre elles, et 16,2 % de toutes les images échantillonnées sans
attribut alt du tout. Le domaine ne manque pas d'outils. Il manque de pages qui
en ont fait tourner un.

## Comment elle se compare

Chaque outil est noté de 1 à 5 sur chaque critère, plus haut vaut mieux (⭐
faible à ⭐⭐⭐⭐⭐ le plus fort). Les notes sont un jugement argumenté, pas un
banc d'essai, et chaque colonne est orientée pour que plus d'étoiles veuille
dire plus fort sur ce trait : pour le coût, plus d'étoiles veut dire plus
gratuit ou plus ouvert ; pour le poids d'installation, plus d'étoiles veut dire
plus léger. Un outil qui ne fait pas du tout ce que mesure une colonne reçoit
⭐, parce que sur une échelle de capacité « ne le fait pas » vaut 1. La source
lisible par machine est [`assets/paysage.csv`](assets/paysage.csv), produite à
partir de la table ci-dessous : 23 outils sur 15 critères.

| Outil | Sans navigateur | Vitesse en intégration continue | Adapté au pré-commit | Légèreté de l'installation | Désigne la ligne source | Correction mécanique automatique | Rédige le texte alternatif manquant | Couverture des règles WCAG | Couverture des médias temporels | Détecte les défauts au rendu | Précision du signal | Gratuité ou ouverture | Local et hors ligne | Maturité et écosystème | Support commercial |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| sprezzature-accessibility | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ |
| axe-core | ⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| axe DevTools Linter | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Pa11y | ⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ |
| Lighthouse | ⭐ | ⭐⭐ | ⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ |
| WAVE | ⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| IBM Equal Access | ⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| Accessibility Insights | ⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| HTML_CodeSniffer | ⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ |
| eslint-plugin-jsx-a11y | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ |
| Biome | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| html-validate | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| htmlhint | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ |
| AccessLint | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐ |
| A11yInspect | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| Siteimprove | ⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| QualiBooth | ⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| accessiBe | ⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| UserWay | ⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| AltText.ai | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| AutoAlt.ai | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐ |
| Azure AI Vision | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Qwen3-VL via Ollama | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ |

![sprezzature-accessibility face à 22 autres outils d'accessibilité et de texte alternatif, positionnés sur deux axes issus d'une analyse en composantes principales. Ce paquet est en haut à droite, dans un groupe avec Biome, htmlhint, eslint-plugin-jsx-a11y, html-validate et le linter axe DevTools : les outils qui lisent le texte source, désignent une ligne et n'ouvrent jamais de navigateur. À l'opposé, vers la gauche, les moteurs qui affichent d'abord la page, axe-core, Pa11y, Lighthouse, IBM Equal Access et Siteimprove, qui voient beaucoup plus et coûtent beaucoup plus à faire tourner. En bas à droite, les services de texte alternatif et les surcouches, AltText.ai, AutoAlt.ai, Azure AI Vision, accessiBe et UserWay, légers à adopter et vendus plutôt qu'installés. L'axe horizontal oppose l'ampleur d'un moteur qui affiche à la légèreté d'un outil qui se contente de lire ; l'axe vertical oppose un outillage ouvert, local et au niveau de la ligne, en haut, à des résultats achetés, en bas.](assets/paysage.svg)

La source est [`assets/paysage.csv`](assets/paysage.csv), la table en étoiles
ci-dessus et rien de plus, et la carte se régénère avec :

```sh
python ../sprezzature/scripts/landscape_to_csv.py PAYSAGE.md --out assets/paysage.csv
standpoint assets/paysage.csv --outdir assets --stem paysage --check
```

`standpoint` place la première ligne de la table en haut à droite et oriente
tout le reste autour d'elle. C'est une convention de dessin, pas une
prétention de qualité : ce fichier appartient à ce paquet, donc ce paquet est
le point de référence, et la rotation appliquée pour l'y amener est de +43,1°.
La géométrie en dessous est une analyse en composantes principales (ACP) sur
corrélations, déterministe : la même table donne la même carte à chaque
exécution, quel que soit le modèle qui a nommé les pôles. Les quatre mots des
bords viennent d'un modèle de langue local ; les charges ci-dessous sont le
contrôle, et c'est la partie à croire.

**Horizontal, 33,8 % de la variance, « Fiabilité » à gauche contre « Efficacité »
à droite.** Détecte les défauts au rendu (−0,41), couverture des règles WCAG
(−0,35) et maturité et écosystème (−0,26) tirent à gauche ; sans navigateur
(+0,38), correction mécanique automatique (+0,32), légèreté de l'installation
(+0,31) et rédige le texte alternatif manquant (+0,31) tirent à droite. C'est
l'arbitrage dont tout ce document parle, et la carte l'a trouvé sans qu'on le
lui dise : un moteur qui affiche la page voit davantage, est davantage cru, et
existe depuis plus longtemps, et il coûte un navigateur à faire tourner.
`sprezzature-accessibility` est tout à droite par construction, en tant que
ligne de référence, mais c'est AltText.ai qui est désigné comme l'option la
plus forte vers ce pôle, ce qui est la carte en train de dire que le côté droit
est une catégorie et non un prix.

**Vertical, 26,6 % de la variance, « Soutien » en bas contre « Agilité » en
haut.** Gratuité ou ouverture (+0,40), local et hors ligne (+0,39), vitesse en
intégration continue (+0,39), adapté au pré-commit (+0,36) et désigne la ligne
source (+0,36) chargent ensemble vers le haut ; support commercial (−0,30) et
rédige le texte alternatif manquant (−0,21) vers le bas. Le pôle du haut est
une seule chose cohérente, un outil qu'on installe et qu'on fait tourner
soi-même sur ses propres fichiers, et le bas en est l'opposé, un résultat qu'on
achète. Biome est l'option la plus forte vers le haut, Siteimprove la plus
faible dans l'ensemble, et accessiBe, UserWay et les services de texte
alternatif sont en bas à côté d'elle.

**Deux axes portent 60,4 % de la table.** Quatre dixièmes de ce que disent ces
quinze critères ne sont pas sur cette page. La couverture des médias temporels
charge à −0,12 et +0,20, c'est-à-dire presque rien sur les deux axes : c'est la
colonne où ce paquet est le plus singulier, et une direction que seules deux ou
trois lignes parcourent n'est pas l'une des deux premières directions. C'est
vrai en sens inverse de la précision du signal, où ce paquet est le plus faible
des outils statiques. La carte est une première orientation ; la table est la
preuve.

`--check` confirme que la référence est en haut à droite et que les étiquettes
d'axes sont lisibles, et signale la figure comme non entièrement lisible :
quatre paires d'étiquettes de points risquent de se chevaucher, axe-core avec
Pa11y et avec Lighthouse, le linter axe DevTools avec AccessLint, et Biome avec
htmlhint. Ces paires se ressemblent vraiment dans leurs notes, donc le
chevauchement est la table qui est honnête plutôt que le dessin qui se trompe,
et rien n'a été déplacé pour les séparer. `standpoint` écrit aussi une
interprétation en prose à côté de la figure ; elle n'est pas reprise ici, parce
qu'un modèle qui relit des notes écrites par quelqu'un n'est pas un résultat.

## Sources

- [La description des règles d'axe-core](https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md), la liste de référence par niveau WCAG, `audio-caption` déprécié compris
- [La documentation d'axe DevTools Linter](https://docs.deque.com/linter/4.0.0/en/linter-home/), types de fichiers, intégrations, et la phrase disant qu'il analyse du source et non une application en cours d'exécution
- [Pa11y](https://github.com/pa11y/pa11y) et [pa11y-ci](https://github.com/pa11y/pa11y-ci), moteurs, normes et seuils
- [IBM Equal Access accessibility-checker](https://github.com/IBMa/equal-access/blob/main-4.x/accessibility-checker/README.md), `reportLevels`, `failLevels` et fichiers de référence
- [Accessibility Insights FastPass](https://accessibilityinsights.io/docs/web/getstarted/fastpass/), et la vue Tab Stops
- [La table de couverture WCAG 2.2 de html-validate](https://html-validate.org/wcag.html)
- [eslint-plugin-jsx-a11y](https://github.com/jsx-eslint/eslint-plugin-jsx-a11y) et [la liste des règles de HTMLHint](https://htmlhint.com/rules/)
- [Le WebAIM Million](https://webaim.org/projects/million/), l'enquête annuelle d'accessibilité sur le premier million de pages d'accueil, et [WebAIM sur le texte alternatif](https://webaim.org/techniques/alttext/), dont la section « Context is Everything » est la version en langage clair de l'argument ci-dessus
- [L'arbre de décision alt du W3C](https://www.w3.org/WAI/tutorials/images/decision-tree/), la taxonomie que `--fix-alt` met en œuvre
- SRIVATSAN, SAMANIEGO, FLOREZ et BERG-KIRKPATRICK, [*Alt-Text with Context*](https://arxiv.org/abs/2305.14779), ICLR 2024, et GUBBI MOHANBABU et PAVEL, [*Context-Aware Image Descriptions for Web Accessibility*](https://dl.acm.org/doi/10.1145/3663548.3675658), ASSETS 2024
- [La documentation d'AltText.ai sur l'ajout d'images](https://alttext.ai/docs/webui/adding-images/), où ses canaux de contexte sont énumérés
- [L'Overlay Fact Sheet](https://overlayfactsheet.com/en/), maintenu par Karl GROVES
- [ACT Rules Format 1.1](https://www.w3.org/WAI/news/2026-02-05/act-rules-11), recommandation du W3C depuis février 2026
- [L'ordre de la FTC contre accessiBe](https://www.ftc.gov/news-events/news/press-releases/2025/01/ftc-takes-action-against-accessibe-deceiving-consumers-about-its-ai-product-web-accessibility)
