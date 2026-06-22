"""
Agent de veille concurrentielle - Secteur Assurance
Envoi automatique par email via Resend
"""

import os
import datetime
import requests
from bs4 import BeautifulSoup
import anthropic

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
EMAIL_DESTINATAIRE = "elongwilliam@gmail.com"

SOURCES = {
    "Le Monde – Assurances": "https://www.lemonde.fr/argent/assurances/",
    "Les Echos – Banque/Assurance": "https://www.lesechos.fr/finance-marches/banque-assurances/",
    "BFM Business – Assurance": "https://www.bfmtv.com/economie/patrimoine/assurance/",
    "MoneyVox Assurance": "https://www.moneyvox.fr/assurance/",
}

MOTS_CLES = [
    "assurance", "garantie", "offre", "produit", "lancement", "partenariat",
    "recrutement", "innovation", "auto", "habitation", "santé", "prévoyance"
]

def scraper(nom, url):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        texte = soup.get_text(separator="\n", strip=True)
        lignes = [l for l in texte.split("\n") if len(l) > 40 and any(m in l.lower() for m in MOTS_CLES)]
        return f"=== {nom} ===\n" + "\n".join(lignes[:60]) + "\n"
    except Exception as e:
        return f"=== {nom} ===\n[Erreur : {e}]\n"

def generer_note(contenu):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": f"""
Tu es analyste assurance en France. Rédige une note de veille concurrentielle professionnelle.

{contenu}

Structure :
1. RÉSUMÉ EXÉCUTIF
2. NOUVEAUX PRODUITS & OFFRES
3. ACTUALITÉS PRESSE
4. SIGNAUX RECRUTEMENT
5. POINTS DE VIGILANCE

Date : {datetime.date.today().strftime('%d/%m/%Y')}
Sois factuel, concis, orienté décision.
"""}]
    )
    return response.content[0].text

def envoyer_email(note):
    date_str = datetime.date.today().strftime('%d/%m/%Y')
    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "from": "Veille Assurance <onboarding@resend.dev>",
            "to": [EMAIL_DESTINATAIRE],
            "subject": f"Note de veille concurrentielle — {date_str}",
            "text": note
        }
    )
    if response.status_code == 200:
        print(f"✅ Email envoyé à {EMAIL_DESTINATAIRE}")
    else:
        print(f"❌ Erreur envoi email : {response.text}")

def lancer_veille():
    print(f"\n🚀 Veille lancée — {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')}")

    contenu = ""
    for nom, url in SOURCES.items():
        print(f"  → {nom}")
        contenu += scraper(nom, url)

    print("🧠 Analyse Claude...")
    note = generer_note(contenu)

    print("📧 Envoi email...")
    envoyer_email(note)

    print("\n✔ Terminé.")

if __name__ == "__main__":
    lancer_veille()