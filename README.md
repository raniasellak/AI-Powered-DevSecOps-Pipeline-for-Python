# AI-Powered-DevSecOps-Pipeline-for-Python

> Plateforme de facturation et de paiement pour freelances et entreprises, avec traçabilité blockchain et détection de fraude par IA.

---

## À propos

InvoicePay relie l'offre, la mission, la facture, le paiement et la preuve dans un seul flux fiable : les entreprises paient leurs freelances avec une traçabilité complète, et les freelances construisent un historique de missions vérifiable.

La v2 étend la v1 (freelance → client) en ajoutant :
- L'**acteur Entreprise** avec gestion multi-membres (RBAC)
- Le **module Offres** : publication, candidatures, sélection
- L'**historique des missions** : dossier vérifiable ancré sur blockchain

> Le travail est livré hors application (email, Drive, GitHub…). InvoicePay gère uniquement l'offre, la mission, la facture et la transaction bancaire.

---

## Acteurs

| Acteur | Rôle |
|---|---|
| Freelance | Consulte les offres, postule, réalise les missions, crée les factures, suit ses paiements, consulte son historique |
| Client (particulier) | Reçoit un lien de facture et paie, avec ou sans compte |
| Entreprise | Publie des offres, choisit des freelances, valide les livraisons, paie, suit toutes ses dépenses |
| Admin | Supervise utilisateurs, transactions, alertes fraude, journal d'audit et gestion des bans |

### Rôles internes d'une entreprise (RBAC)

- **Propriétaire / Manager** – crée l'espace, invite les membres, gère les paramètres, publie les offres, choisit les freelances, confirme les livraisons
- **Responsable finance** – approuve et déclenche les paiements, exporte la comptabilité

---

## Flux complet

```
1. Connexion (mot de passe + MFA)
2. L'entreprise publie une offre (ou invite un freelance en privé)
3. Les freelances postulent → l'entreprise choisit → une mission est créée
4. Le freelance livre hors app et marque la mission « livrée » → l'entreprise confirme
5. La facture PDF est générée depuis la mission, son hash est ancré sur blockchain
6. Le payeur paie via le prestataire (sandbox, 3-D Secure) — aucune donnée de carte ne transite par nos serveurs
7. Webhook signé reçu → score de fraude IA calculé
8. Mission → « payée », reçu envoyé, historique freelance et dépenses entreprise mis à jour, tout journalisé
```

---

## Module Offres

### Cycle de vie d'une offre

```
Brouillon → Publiée → Candidatures reçues → Freelance choisi
→ Mission en cours → Livrée → Confirmée → Facturée → Payée → Clôturée
```

États alternatifs : `Annulée`, `Expirée`, `Litige`

### Contenu d'une offre

| Champ | Exemple |
|---|---|
| Titre et description | Logo + charte graphique |
| Catégorie / compétences | Design, Illustrator |
| Budget | 2 000 MAD (fixe) ou fourchette |
| Délai de livraison | 10 jours |
| Date limite de candidature | 15 octobre |
| Visibilité | Publique ou privée (freelances invités) |

### Candidatures

Le freelance envoie un message, son tarif et un délai. Il suit son statut : `en attente`, `retenue`, `refusée`. L'entreprise compare les candidatures et consulte le profil et l'historique vérifié de chaque candidat.

### De l'offre à la facture

- L'acceptation d'une candidature crée automatiquement une **mission** avec montant, délai et description figés
- La facture générée doit correspondre exactement au montant de la mission (validation côté serveur)
- Option : **jalons** (ex. 30 % au début, 70 % à la livraison)

---

## Historique des missions

Chaque freelance dispose d'un dossier alimenté automatiquement dès qu'une mission est payée.

### Contenu d'une entrée

- Titre de la mission, entreprise/client
- Dates : début, livraison, paiement
- Montant, statut
- Lien vers la facture PDF
- Preuve blockchain (hash vérifiable)
- Avis vérifié (optionnel, uniquement après paiement)

### Fonctionnalités

- Filtres par année, client, statut, montant
- Statistiques : total encaissé, nombre de missions, clients récurrents, délai moyen de paiement
- **Attestation PDF** exportable avec QR code de vérification
- Confidentialité contrôlée par le freelance (masquer montants ou nom du client)

> Règle d'intégrité : une entrée ne peut être créée que par une mission réellement payée. Le freelance ne peut ni l'inventer ni la modifier.

---

## Schéma de données (simplifié)

```
Utilisateur
Organisation (entreprise)
Membre (utilisateur + organisation + rôle)
Offre  ──────────────────────► appartient à une Organisation
Candidature  ────────────────► relie un Freelance à une Offre
Mission  ────────────────────► créée depuis une Offre acceptée
Facture  ────────────────────► générée depuis une Mission
Paiement + Preuve blockchain ► créés depuis une Facture
Historique  ─────────────────► alimenté par une Mission payée
Avis
Journal d'audit
```

---

## Sécurité

| Risque | Protection |
|---|---|
| Fuite de données inter-organisations | RBAC avec isolation par organisation, tests IDOR automatisés |
| Paiement frauduleux par un seul employé | Séparation des rôles recruteur / finance, double validation au-dessus d'un seuil |
| Détournement du RIB freelance | Compte de versement unique, changement protégé par MFA + délai avant effet |
| Facture gonflée | Montant figé sur la mission, validation côté serveur |
| Double paiement groupé | Clé d'idempotence par mission, verrou statut, webhook signé |
| Faux profils / faux avis | Compte vérifié (email + MFA), avis réservés aux missions payées |
| Freelance peu fiable | Un freelance peut être banni par l'admin suite à des avis négatifs répétés ou des missions non terminées — son compte est suspendu et il ne peut plus postuler |
| Collusion entreprise–freelance | Score de fraude IA étendu : fréquence, montants anormaux, paires répétées |
| Falsification de l'historique | Entrées créées uniquement par mission payée, hash blockchain, audit log immuable |
| Fuite de données personnelles | Chiffrement, minimisation, consentement, conformité loi 09-08 (CNDP) |

---

## Stack technique

- **Backend** : FastAPI (Python)
- **Frontend web / mobile** : Flutter
- **Paiement** : Prestataire tiers sandbox, 3-D Secure (aucune donnée carte sur nos serveurs)
- **Blockchain** : Ancrage du hash des factures et preuves de mission
- **IA** : Score de fraude sur les transactions

---

## Pipeline DevSecOps augmentée par IA

InvoicePay est conçu et déployé via une pipeline DevSecOps complète, où la sécurité est intégrée à chaque étape du cycle de développement — et non ajoutée après coup.

### Principe général

```
Code pushé → Pipeline déclenchée → Sécurité analysée → Build → Tests → Déploiement
         (toute faille bloque le déploiement automatiquement)
```

### Étapes de la pipeline

| Étape | Outils | Description |
|---|---|---|
| Lint & qualité | Ruff, Black | Vérification du style et de la qualité du code Python |
| Analyse statique (SAST) | Bandit, Semgrep | Détection de vulnérabilités dans le code source FastAPI |
| Scan des dépendances | Safety, pip-audit | Détection de dépendances Python avec CVE connues |
| Tests unitaires & intégration | Pytest | Couverture des endpoints FastAPI, logique métier |
| Tests d'autorisation (IDOR) | Pytest + scripts custom | Vérifie qu'un utilisateur ne peut pas accéder aux données d'une autre organisation |
| Analyse dynamique (DAST) | OWASP ZAP | Scan de l'API en cours d'exécution pour détecter les failles runtime |
| Score de risque IA | Modèle custom | Analyse le résultat des scans et priorise les alertes par criticité |
| Build & conteneurisation | Docker | Image de l'application construite uniquement si toutes les étapes passent |
| Déploiement cloud | GitHub Actions + Cloud | Déploiement automatique sur environnement cible après validation complète |
| Journalisation & audit | Logs centralisés | Chaque exécution de pipeline est tracée et conservée |

### Rôle de l'IA dans la pipeline

L'IA intervient à deux niveaux :

- **Dans la pipeline** : agrège les résultats des outils de sécurité (Bandit, ZAP, Safety…), attribue un score de risque global et génère un rapport priorisé. Une faille critique bloque le déploiement.
- **Dans l'application** : score de fraude sur les transactions (fréquence anormale, montants suspects, collusion entreprise–freelance).

### Scénario de démonstration

1. Une faille est introduite dans le code (ex. injection, IDOR)
2. La pipeline détecte la faille → déploiement bloqué
3. La faille est corrigée et un nouveau push est effectué
4. La pipeline repasse au vert → déploiement automatique
5. Sur l'app déployée : un paiement suspect est signalé par l'IA, une tentative d'accès inter-organisation est refusée

---

## Pages de l'application

| Page | Contenu | Web | Mobile |
|---|---|---|---|
| Espace entreprise | Tableau de bord : dépenses, missions en cours, à payer | ✅ | ✅ |
| Équipe | Membres et rôles | ✅ | Optionnel |
| Publier / gérer une offre | Formulaire, candidatures reçues, choix du freelance | ✅ | ✅ |
| Parcourir les offres | Liste filtrable, détail, bouton « Postuler » | ✅ | ✅ |
| Mes candidatures | Statut de chaque candidature | ✅ | ✅ |
| Mes missions | Missions en cours, livraison, facturation | ✅ | ✅ |
| Missions à payer | Sélection et paiement groupé | ✅ | Optionnel |
| Historique des missions | Dossier vérifiable, filtres, attestation PDF | ✅ | ✅ |
| Export comptable | CSV / PDF des paiements et reçus | ✅ | ❌ |

---

## Priorités d'implémentation

| Priorité | Contenu |
|---|---|
| Indispensable | Compte entreprise, offre simple, candidature, acceptation → mission, facture depuis mission, paiement, historique freelance |
| Souhaitable | Équipe avec rôles, validation à deux personnes, paiement groupé, avis vérifiés, attestation PDF avec QR code |
| Bonus | Jalons, offres privées par invitation, export comptable, page de vérification publique |


