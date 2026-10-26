# Sous-workflow `verify-cfs` : contrat

Vérifie qu'une ou plusieurs offres CFS du catalogue satisfont les exigences d'un client, en interrogeant l'ontologie RDF par SPARQL.

## Entrée

Un item par capacité à vérifier :

| Champ | Type | Description |
|---|---|---|
| `candidateId` | `string` ou `string[]` | Identifiant(s) du ou des CFS candidats. Avec plusieurs ids, les candidats sont classés |
| `requirements` | `array`, ou `string` JSON | Liste des exigences (voir ci-dessous) |
| `ref` | `string` | Identifiant de la capacité côté appelant, renvoyé tel quel |
| `sparql` | `string` (optionnel) | Requête **pré-construite par l'appelant**. Si elle est fournie, elle est utilisée telle quelle (mode « passe-plat ») |

Format d'une exigence :

```json
{ "kpi": "latency", "label": "Latence", "op": "<=", "value": 10, "unit": "ms", "blocking": true }
```

- `op` : `=`, `!=`, `<`, `<=`, `>`, `>=` pour les KPI numériques ; `=`, `!=` ou `contains` pour les KPI textuels.
- `blocking` : `true` par défaut. Un écart non bloquant n'entraîne pas de `FAIL`.

## Deux modes de génération SPARQL

1. **Passe-plat (v4).** L'appelant fournit `sparql`. C'est le cas de l'assistant : il connaît les noms exacts des caractéristiques, les unités du catalogue (`tmf:unitOfMeasure`) et les codes de zone.
2. **Génération interne.** Pour une liste fermée de KPI, la requête est construite ici :
   - un sous-`SELECT … SAMPLE … GROUP BY` par KPI, pour éviter le produit cartésien quand un CFS porte plusieurs valeurs pour une caractéristique ;
   - une conversion numérique tolérante (`"99,999 %"` → `99.999`, `"10 ms"` → `10`, notation scientifique acceptée) ;
   - `VALUES ?candidate { … }` pour évaluer plusieurs candidats en une seule requête.

## Statuts par exigence

| Statut | Signification |
|---|---|
| `PASS` | Conforme |
| `FAIL` | Non conforme |
| `MISSING` | Caractéristique non documentée dans l'ontologie |
| `UNPARSABLE` | Valeur illisible |
| `MISSING_UNIT` / `UNKNOWN_UNIT` | Comparaison impossible faute d'unité exploitable |

## Verdict

| Verdict | Règle |
|---|---|
| `FAIL` | Au moins une exigence **bloquante** en `FAIL` |
| `PASS_WITH_GAPS` | Aucun `FAIL` bloquant, mais un `FAIL` non bloquant ou une exigence non vérifiable |
| `PASS` | Toutes les exigences en `PASS` |
| `SKIPPED` | Vérification non effectuée : pas de candidat, pas d'exigence ou erreur de construction |
| `ERROR` | L'ontologie n'a renvoyé aucune ligne pour ce CFS |

Toutes les exigences comptent dans le verdict. Le caractère bloquant ne change que la gravité : un KPI non documenté ne peut donc pas produire un faux `PASS`.

## Sortie

```json
{
  "ref": "BC-002",
  "candidateId": "<id du meilleur CFS>",
  "verdict": "PASS_WITH_GAPS",
  "checks": [ { "kpi": "...", "expected": 10, "actual": "5", "status": "PASS", "blocking": true } ],
  "satisfied": ["Latence"],
  "unsatisfied": [],
  "soft_unsatisfied": [],
  "undocumented": ["Disponibilité"],
  "message": "🟠 Le CFS proposé ne contredit aucune exigence bloquante, mais tout n'est pas garanti : …",
  "ranking": [ { "candidate": "...", "verdict": "PASS_WITH_GAPS", "score": 1 } ]
}
```

Les valeurs ci-dessus sont des exemples de format, pas des données réelles.

## Robustesse

Le sous-workflow **ne lève jamais d'exception**. Un cas impossible produit un item `SKIPPED` ou `ERROR`, accompagné d'une requête neutre (`SELECT ?skip …`). Ainsi, chaque entrée produit exactement une sortie, et le pipeline parent peut toujours réassembler ses résultats. Un branchement `IF` autour de l'appel HTTP aurait fait exécuter deux fois le nœud de formatage et cassé cet appariement.
