# Site web — VRoid MCP Bridge

Site statique du projet **VRoid MCP Bridge**. Aucun build, aucune dépendance : HTML, CSS et JavaScript natifs.

## Langues

- Anglais par défaut : `website/index.html`
- Français : `website/fr/index.html`
- 日本語 : `website/ja/index.html`
- 简体中文 : `website/zh/index.html`
- Sélecteur **EN / FR / JA / ZH** dans l'en-tête, avec `hreflang` et Open Graph localisés.

## Aperçu local

Depuis la racine du dépôt :

```powershell
python -m http.server 8000 --directory website
```

Puis ouvrir <http://localhost:8000> (anglais) ou <http://localhost:8000/fr/> (français).

## Structure

```
website/
├── index.html                 page anglaise (par défaut)
├── fr/index.html              page française
├── ja/index.html              page japonaise
├── zh/index.html              page chinoise simplifiée
├── privacy/index.html         politique de confidentialité (EN)
├── fr/privacy/index.html      politique de confidentialité (FR)
├── 404.html                   page d'erreur anglaise (+ lien FR)
├── site.webmanifest           icônes / installation PWA
├── robots.txt
├── sitemap.xml                pages + alternates hreflang
├── .nojekyll
├── publish.ps1                publication après validation
└── assets/
    ├── css/style.css
    ├── js/main.js
    ├── js/consent.js          bandeau RGPD / chargement conditionnel de GA4
    └── img/                   images optimisées, OG EN/FR, icônes
```

## Publication (après confirmation)

Le site est prévu pour GitHub Pages via GitHub Actions (`.github/workflows/pages.yml`).

1. Vérifier le rendu local (EN et FR).
2. Lancer, une fois la publication validée :

   ```powershell
   powershell -ExecutionPolicy Bypass -File website/publish.ps1 -Go
   ```

3. Le workflow publie `website/` sur <https://mcjo79.github.io/vroid-mcp/>.
   Si GitHub Pages n'est pas encore activé, aller dans **Settings → Pages → Source : GitHub Actions**
   (le workflow tente de l'activer automatiquement).

Sans `-Go`, le script affiche seulement ce qui serait publié — aucun commit, aucun push.

## Notes

- Les images viennent de la session VRoid du test de création de personnage ; elles sont déjà optimisées et versionnées dans `assets/img/`.
- Le brief du test (en anglais) est dans [`docs/CHARACTER_PROMPT.md`](../docs/CHARACTER_PROMPT.md) et dans la section « The test » / « Le test ».
- Crédits : pont développé avec Claude Code ; test du personnage et site réalisés avec DeepSeek, via un client MCP indépendant.
- **Google Analytics 4** (`G-2NDE82V29F`) fonctionne en **advanced consent mode** : `gtag-init.js` charge la balise immédiatement avec tous les signaux en `denied` ; aucun cookie de mesure ni identifiant n'est déposé avant « Accepter », mais Google peut recevoir une requête de mesure sans cookie. `consent.js` met ensuite `analytics_storage` à `granted` et supprime les cookies en cas de refus. Le choix est conservé 180 jours dans `localStorage` (`vroid-consent-v1`), puis la question est reposée.
- Les cookies GA4 sont des **cookies de session** (`cookie_expires: 0`) et le domaine est fixé à l'hôte courant (`cookie_domain: location.hostname`). Sans cela, GA tente `Domain=github.io` — rejeté par Chrome car `github.io` est un suffixe public — et réécrit `expires` deux fois dans le même cookie, ce qui produit les avertissements « domaine invalide » et « expires écrasé ».
- **Debug** : `?gtm_debug=...`, `?ga_debug=1` ou `?debug_mode=1` active `debug_mode` dans GA4 et rouvre le bandeau. Dans ce mode, un choix « Accepter » déjà stocké est volontairement **ignoré** : Tag Assistant part du refus par défaut et ne voit la mise à jour qu'après le clic. **Ce paramètre ne vaut jamais consentement** : sans ce clic, `analytics_storage` reste refusé et aucun cookie de mesure n'est déposé.
- Le bandeau propose **Accepter** et **Refuser** avec la même visibilité, sans case pré-cochée ni cookie wall. Le lien **Gérer les cookies** du pied de page permet de revenir sur son choix.
- La politique de confidentialité est disponible en [`privacy/`](privacy/index.html) et [`fr/privacy/`](fr/privacy/index.html) : responsable, données, cookies, base légale, destinataires, conservation, droits et CNIL.
- L'identité de l'éditeur est indiquée comme **mcjo79** avec contact via GitHub. Si le site devient professionnel, compléter avec l'identité légale et l'adresse postale de l'éditeur.
- Open Graph et JSON-LD sont localisés (anglais à la racine, français dans `fr/`).
