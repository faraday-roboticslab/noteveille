"""
Agent de veille concurrentielle - Secteur Assurance
=====================================================
Surveille : AXA, Allianz, MMA, Luko, Leocare + presse spécialisée
Contenu    : Nouveaux produits, communiqués de presse, articles, recrutements
Livraison  : Fichier texte horodaté (+ PDF optionnel)

Usage :
  - Lancement manuel  : python veille_assurance.py
  - Lancement auto    : décommenter le bloc schedule en bas du fichier
"""

import os
import datetime
import requests
from bs4 import BeautifulSoup
import anthropic

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "sk-ant-VOTRE_CLE_ICI")

# Sources à surveiller
SOURCES = {
    "AXA – Actualités": "https://www.axa.fr/conseils-et-actualites/actualites.html",
    "Allianz – Presse": "https://www.allianz.fr/le-groupe-allianz/presse.html",
    "MMA – Actualités": "https://www.mma.fr/actualites.html",
    "Luko – Blog": "https://www.luko.eu/fr/blog",
    "Leocare – Blog": "https://leocare.eu/blog/",
    "L'Argus de l'Assurance": "https://www.argusdelassurance.com/",
    "News Assurances Pro": "https://www.newsassurancespro.com/",
}

# Mots-clés de filtrage (garder uniquement le contenu pertinent)
MOTS_CLES = [
    "assurance", "garantie", "offre", "produit", "lancement", "partenariat",
    "recrutement", "embauche", "croissance", "innovation", "digital",
    "auto", "habitation", "santé", "vie", "prévoyance", "sinistre"
]

# Dossier de sortie
OUTPUT_DIR = "./notes_veille"


# ─────────────────────────────────────────────
# ÉTAPE 1 — SCRAPING
# ─────────────────────────────────────────────

def scraper_source(nom, url):
    """Récupère le texte brut d'une page web."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; VeilleBot/1.0)"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Supprimer les scripts, styles, nav
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        texte = soup.get_text(separator="\n", strip=True)

        # Garder uniquement les lignes avec au moins un mot-clé
        lignes_pertinentes = [
            ligne for ligne in texte.split("\n")
            if len(ligne) > 40 and any(mot in ligne.lower() for mot in MOTS_CLES)
        ]

        contenu = "\n".join(lignes_pertinentes[:80])  # max 80 lignes par source
        return f"=== {nom} ===\n{contenu}\n"

    except Exception as e:
        return f"=== {nom} ===\n[Erreur de scraping : {e}]\n"


def collecter_toutes_sources():
    """Lance le scraping sur toutes les sources."""
    print("🔍 Scraping des sources en cours...")
    contenu_global = ""
    for nom, url in SOURCES.items():
        print(f"   → {nom}")
        contenu_global += scraper_source(nom, url)
    return contenu_global


# ─────────────────────────────────────────────
# ÉTAPE 2 — ANALYSE PAR CLAUDE
# ─────────────────────────────────────────────

def analyser_avec_claude(contenu_brut):
    """Envoie le contenu à Claude pour générer la note de veille."""
    print("🧠 Analyse Claude en cours...")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""
Tu es un analyste spécialisé dans le secteur des assurances en France.
À partir des contenus web suivants collectés aujourd'hui, rédige une note de veille concurrentielle professionnelle.

CONTENU COLLECTÉ :
{contenu_brut}

STRUCTURE DE LA NOTE :
1. RÉSUMÉ EXÉCUTIF (5 lignes max, les faits saillants)
2. NOUVEAUX PRODUITS & OFFRES (par acteur si pertinent)
3. COMMUNIQUÉS & ACTUALITÉS PRESSE
4. SIGNAUX RECRUTEMENT (indique les tendances stratégiques que ça révèle)
5. POINTS DE VIGILANCE (ce que l'équipe marketing doit surveiller)

RÈGLES :
- Sois factuel, concis, orienté décision
- Ignore les contenus sans intérêt stratégique
- Si une source n'a rien de notable, ne la mentionne pas
- Date de la note : {datetime.date.today().strftime("%d/%m/%Y")}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


# ─────────────────────────────────────────────
# ÉTAPE 3 — LIVRAISON (fichier texte)
# ─────────────────────────────────────────────

def sauvegarder_note(note):
    """Sauvegarde la note dans un fichier texte horodaté."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    date_str = datetime.datetime.now().strftime("%Y-%m-%d_%Hh%M")
    nom_fichier = f"{OUTPUT_DIR}/veille_assurance_{date_str}.txt"

    with open(nom_fichier, "w", encoding="utf-8") as f:
        f.write(f"NOTE DE VEILLE CONCURRENTIELLE — ASSURANCE\n")
        f.write(f"Générée le {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')}\n")
        f.write("=" * 60 + "\n\n")
        f.write(note)

    print(f"✅ Note sauvegardée : {nom_fichier}")
    return nom_fichier


# ─────────────────────────────────────────────
# PIPELINE PRINCIPAL
# ─────────────────────────────────────────────

def lancer_veille():
    print("\n🚀 Lancement de la veille concurrentielle assurance")
    print(f"   {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')}\n")

    # 1. Scraper
    contenu_brut = collecter_toutes_sources()

    # 2. Analyser
    note = analyser_avec_claude(contenu_brut)

    # 3. Sauvegarder
    fichier = sauvegarder_note(note)

    print("\n📋 Aperçu de la note :")
    print("-" * 40)
    print(note[:500] + "...")
    print("-" * 40)
    print(f"\n✔ Terminé. Fichier complet : {fichier}\n")


# ─────────────────────────────────────────────
# LANCEMENT
# ─────────────────────────────────────────────

if __name__ == "__main__":

    # ── Option A : lancement manuel (défaut) ──
    lancer_veille()

    # ── Option B : lancement automatique ──
    # Décommenter les lignes ci-dessous pour une exécution planifiée
    #
    # import schedule, time
    # schedule.every().monday.at("08:00").do(lancer_veille)
    # schedule.every().thursday.at("08:00").do(lancer_veille)
    # print("⏰ Agent planifié — lundi et jeudi à 08h00")
    # while True:
    #     schedule.run_pending()
    #     time.sleep(60)
