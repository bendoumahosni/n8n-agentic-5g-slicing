# Choix techniques

## Ingestion RAG (workflows 01)

- **Résumé LLM avant l'embedding.** Les specs CFSS sont réduites à un *digest* compact (une ligne par caractéristique), puis résumées par un LLM local. Le prompt interdit toute caractéristique absente du digest. C'est ce résumé qui est vectorisé, ce qui améliore le matching sémantique par rapport au JSON brut.
- **Payload compatible avec le nœud Qdrant LangChain de n8n** (`pageContent` + `metadata`). Un payload « à plat » était relu vide par n8n et faisait échouer le grounding. La cause a été corrigée à l'ingestion plutôt que dans les données.
- **Collection idempotente.** La collection est créée si elle n'existe pas, avec une taille de vecteur déduite de l'embedding. L'identifiant de point est dérivé de l'id de la spec.
- **Aucune information perdue.** Les caractéristiques GST connues deviennent des métadonnées filtrables. Les autres sont signalées dans `unmapped_characteristics` au lieu d'être ignorées.

## Synchronisation des catalogues (workflow 02)

- Nettoyage de chaque spec au contrat de l'API cible (suppression des `uuid` et des valeurs `null`).
- Classification CFS / RFS par une heuristique à plusieurs niveaux : `@type`, nom, catégories, relations.
- Création uniquement (POST). Un `409 entity_already_exists` est ignoré, toute autre erreur est remontée en un seul rapport lisible.

## Vérification de conformité (workflow 03)

- Une requête générée par exigence, avec sous-`SELECT` + `SAMPLE` pour éviter les produits cartésiens.
- Conversion numérique tolérante (`"99,999 %"`, `"10 ms"`, notation scientifique).
- Classement de plusieurs candidats (`VALUES ?candidate`) et verdict sur trois niveaux. Un KPI non documenté donne `PASS_WITH_GAPS`, jamais un faux `PASS`.
- **Le sous-workflow ne lève jamais d'exception.** Une vérification impossible renvoie `SKIPPED` ou `ERROR`, et une requête neutre préserve l'appariement 1 entrée → 1 sortie.

Le contrat complet est dans [`verify-cfs.md`](verify-cfs.md).

## Assistant agentique (workflow 04)

- Routage d'intention : nouvelle demande, complément, commande, suivi.
- **Agents à responsabilité unique** (décomposition, grounding, enrichissement, recherche de bundle puis d'offres unitaires, commande, suivi), avec une **validation de contrat JSON** entre chaque étape.
- **État canonique** conservé en mémoire. Une nouvelle demande peut *compléter* la proposition en cours au lieu de la remplacer.
- **Idempotence** à trois niveaux (capacité, service générique, offre) et côté commande (TMF641) : aucune commande n'est recréée si elle existe déjà.

Le déroulé complet est décrit dans [`workflows.md`](workflows.md).
