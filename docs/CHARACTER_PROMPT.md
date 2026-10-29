# Test de création — brief

**Prompt (anglais)**

> Young Japanese businesswoman, purple hair, 155 cm, dark green suit.

Traduction : jeune cadre japonaise, cheveux violets, 1,55 m, tailleur vert foncé.

Test réalisé dans VRoid Studio 2.14 via le pont MCP, **sans image de référence** : le personnage est construit à partir du brief texte uniquement.

## Crédits

- Pont MCP : développé avec Claude Code.
- Test du personnage et site : réalisés avec DeepSeek, via un client MCP indépendant ; le pont est agnostique du client.

## Étapes

1. Modèle N00, silhouette féminine à 155 cm.
2. Coiffure : preset `HairSet/001` (longs lisses, raie sur le côté), passé en édition de texture (`vroid_begin_hair_edit`) puis recoloré en violet — texture et calotte (`Level1BaseHair_OverlayColor`).
3. Tailleur : vêtements par défaut retirés (`vroid_remove_item`), blazer + chemise, pantalon vert foncé, escarpins. Le beige du blazer est repeint en vert forêt par export/import de texture.
4. Visage : `FaceSet/002`, blush, lèvres et sourcils, puis caméra (`vroid_camera`) et captures.

Aucune image de référence n'est utilisée ni publiée avec ce test.
