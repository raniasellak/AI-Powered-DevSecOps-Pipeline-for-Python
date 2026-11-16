"""
Génération du PDF de facture avec ReportLab.
"""
import io
from datetime import datetime, timezone

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from .models import Invoice, Mission


def generate_invoice_pdf(invoice: Invoice, mission: Mission) -> bytes:
    """
    Génère le PDF d'une facture et retourne les bytes.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # En-tête
    c.setFont("Helvetica-Bold", 18)
    c.drawString(2 * cm, height - 2 * cm, "InvoicePay")

    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, height - 2.7 * cm, "Plateforme de facturation sécurisée")

    # Numéro et date
    c.setFont("Helvetica-Bold", 13)
    c.drawString(2 * cm, height - 4 * cm, f"Facture  {invoice.number}")

    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, height - 4.8 * cm,
                 f"Date : {invoice.created_at.strftime('%d/%m/%Y')}")

    # Mission
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, height - 6.5 * cm, "Mission")
    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, height - 7.2 * cm, f"Titre    : {mission.title}")
    if mission.description:
        c.drawString(2 * cm, height - 7.8 * cm, f"Détail   : {mission.description}")

    # Montants
    ht = float(invoice.amount)
    tax = float(invoice.tax_rate)
    tva = round(ht * tax, 2)
    ttc = round(ht + tva, 2)

    y = height - 10 * cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, "Détail financier")
    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, y - 0.8 * cm, f"Montant HT  :  {ht:.2f} MAD")
    c.drawString(2 * cm, y - 1.5 * cm, f"TVA ({int(tax*100)} %)  :  {tva:.2f} MAD")
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y - 2.3 * cm, f"Total TTC   :  {ttc:.2f} MAD")

    # Hash blockchain
    c.setFont("Helvetica", 8)
    c.drawString(2 * cm, 3 * cm, "Preuve d'intégrité (SHA-256) :")
    c.drawString(2 * cm, 2.4 * cm, invoice.content_hash or "—")

    c.setFont("Helvetica", 7)
    c.drawString(2 * cm, 1.5 * cm,
                 f"Document généré le {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')} UTC")

    c.save()
    buffer.seek(0)
    return buffer.read()
