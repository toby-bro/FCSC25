# Un cercle est un carré

[Lien vers le challenge](https://hackropole.fr/fr/challenges/misc/fcsc2025-misc-un-cercle-est-un-carre/)

Ce problème a été de loin celui qui m'a le plus fait m'arracher des cheveux lors de ce FCSC.

Je passerai les détails mais après avoir passé plus d'une journée à faire des projections de segments sur des plans diagonaux puis sur des arrêtes pour refaire une sorte de projection cubique à la manière d'une projection sphérique du segment $\[P, Q\]$ et avoir vu que c'était pas la solution exacte mais une bonne approximation... J'ai enragé et j'ai cherché sur internet et je suis tombé sur

## La méthode de la fourmi paresseuse

Étapes à suivre

- déplier le cube
- tracer un trait entre P et Q
- mesurer le trait

...

Voilà c'était tout simple...

Bon maintenant il fallait implémenter ça en python, et l'implémentation est loin d'être triviale, désolé pour tous ceux qui n'ont pas fait d'algèbre, ça risque de piquer un peu.

L'algorithme en soi n'est pas très compliqué, c'est un dépliage récursif

- Déplier récursivement le cube en commençant par la face de P
  - Est ce que Q est sur cette face
  - Dans notre dépliage peut-on encore déplier une face voisine
    - La déplier
      - ...

Bon vient la partie coriace. Je me suis posé la question de comment savoir où atterirait le point Q après le dépliage, comment garder en mémoire les transformations et comment les appliquer. Je sais que ce seront des rotations, mais conserver l'axe, la direction, l'angle... était compliqué. Je me suis dit qu'en fait on était en dimension 3, dans un espace métrique, que les rotations sont des endomorphismes linéaires, et qu'en utilisant cela, la résultante de toutes mes transformations n'est que le produit de toutes mes matrices de rotations pour chacun des plis. Rien de bien sorcier. Toujours est-il que mon fichier de tests unitaires est plus long que mon programme pour résoudre le problème...

Bref je peux témoigner que le :cat: n'a pas de vision dans l'espace, et ne peut pas résoudre les challs comme certains arguaient sur le discord un matin très tôt ! Bon ça aide pas qu'il faille en plus représenter les translations car non seulement on a une rotation mais en plus deux translations, une pour placer l'axe de rotation dans l'origine du repère, et une pour en revenir. On a donc décidé d'utiliser des coordonnées homogènes (et donc des matrices 4x4) pour représenter ces transformations.

Ce qu'il se passe en détail est donc :
On commence de la face de P

- Est ce que Q est sur la face si oui on arrête et on calcule la distance
  - Pour chaque face voisine qui n'a pas encore été visitée
    - On déplie la face (on calcule la matrice associée à cette transformation), est ce que Q est sur la face -> si oui on calcule sa nouvelle position $Q'$ une fois déplié en composant toutes les matrices de rotation $Q' := R_1 R_2 ... R_n Q$
    - On poursuit la récursivité jusqu'à ce qu'on ne puisse plus déplier de face supplémentaire et on renvoie toutes les coordonnées de Q que l'on a trouvé.

En ce qui concerne la matrice de la rotation on la détermine de la façon suivante :

- On détermine le vecteur représentant l'axe de rotation si le cube n'avait pas été déplié
- On détermine les vecteurs normaux des faces (pointant vers l'extérieur du cube), avant le dépliage
- On applique la matrice de tous les dépliages jusqu'à présent à ces vecteurs, pour obtenir leur vraies positions dans l'espace après tant de dépliages successifs.
- On translate l'ensemble vers l'origine du repère
- On détermine la matrice de rotation
- On l'orthonormalise
- On vérifie que son déterminant est bien positif
- On effectue le changement de base dans l'autre sens et on retourne aux véritables positions
- On renvoie la nouvelle valeur de la matrice de rotation que l'on va multiplier à toutes les précédentes pour avoir la matrice représentant le dépliage de la prochaine face.

Attention il faut noter que chaque face à une matrice de dépliage différente car aucune ne subit les mêmes dépliages avant d'arriver dans le plan de P.

A chaque façon de déplier on va tomber sur la face avec Q, donc on va obtenir plein de positions de Q une fois sur la face de P et donc calculer plein de distances. Yapuka renvoyer la plus courte, rajouter un peu de pexpect pour interragir avec le serveur netcat, ouvrir un ticket parce que le RTT entre mon ordi et le serveur est trop élevé pour valider dans les temps, remercier les orgas, valider le chall.

tl;dr les fourmis sont sacrément fortes en algèbre, écrivez des units tests, l'algèbre c'est cool, déplier une feuille de papier c'est pas toujours trivial.

Vous trouverez le code sur mon [repo git](https://github.com/toby-bro/FCSC25/tree/main/misc/Un_cercle_est_un_carre)
[solve.py](./solve.py)
[minimum_distance.py](./minimum_distance.py)
[minimum_distance_test.py](./minimum_distance_test.py)
