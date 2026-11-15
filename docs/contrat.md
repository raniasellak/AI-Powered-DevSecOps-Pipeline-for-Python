 # Contrat Facture ↔ Paiement

- Table `payments` : colonnes `id`, `invoice_id`, `status` (pending / succeeded / failed)
- Le webhook de P4 appelle `mark_invoice_paid(invoice_id)` (code de P3)
- P3 est seul à écrire dans `invoices` et `invoice_history`
- Le montant de la facture est égal au montant de la mission