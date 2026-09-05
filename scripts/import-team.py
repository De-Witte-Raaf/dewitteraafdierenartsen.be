#!/usr/bin/env python3
import urllib.request
import re
from pathlib import Path
from bs4 import BeautifulSoup

team_info = [
    {
        "slug": "dr-bart-pieters",
        "url": "https://dewitteraafdierenartsen.be/over-ons/bart-pieters/",
        "name": "Dr. Bart Pieters",
        "role": "Dierenarts / Mede-Eigenaar",
        "category": "dierenartsen",
        "order": 1
    },
    {
        "slug": "dr-jacqueline-van-der-esch",
        "url": "https://dewitteraafdierenartsen.be/jacqueline-van-der-esch/",
        "name": "Jacqueline van der Esch",
        "role": "Dierenarts / Mede-Eigenaar",
        "category": "dierenartsen",
        "order": 2
    },
    {
        "slug": "dr-milou-toetenel",
        "url": "https://dewitteraafdierenartsen.be/milou-toetenel/",
        "name": "Milou Toetenel",
        "role": "Dierenarts",
        "category": "dierenartsen",
        "order": 3
    },
    {
        "slug": "dr-olga-kopilova",
        "url": "https://dewitteraafdierenartsen.be/olga-kopilova/",
        "name": "Olga Kopilova",
        "role": "Dierenarts",
        "category": "dierenartsen",
        "order": 4
    },
    {
        "slug": "dr-evelien-holvoet",
        "url": "https://dewitteraafdierenartsen.be/evelien-holvoet/",
        "name": "Evelien Holvoet",
        "role": "Dierenarts",
        "category": "dierenartsen",
        "order": 5
    },
    {
        "slug": "dr-laura-schouppe",
        "url": "https://dewitteraafdierenartsen.be/laura-schouppe",
        "name": "Laura Schouppe",
        "role": "Dierenarts",
        "category": "dierenartsen",
        "order": 6
    },
    {
        "slug": "sofie-van-vynckt",
        "url": "https://dewitteraafdierenartsen.be/sofie-van-vynckt/",
        "name": "Sofie Van Vynckt",
        "role": "Dierenartsassistente",
        "category": "assistenten",
        "order": 7
    },
    {
        "slug": "tine-cornand",
        "url": "https://dewitteraafdierenartsen.be/tine-cornand/",
        "name": "Tine Cornand",
        "role": "Dierenartsassistente",
        "category": "assistenten",
        "order": 8
    },
    {
        "slug": "sofie-vermoesen",
        "url": "https://dewitteraafdierenartsen.be/sofie-vermoesen/",
        "name": "Sofie Vermoesen",
        "role": "Dierenartsassistente",
        "category": "assistenten",
        "order": 9
    },
    {
        "slug": "karen-van-eeckhoudt",
        "url": "https://dewitteraafdierenartsen.be/karen-van-eeckhoudt/",
        "name": "Karen Van Eeckhoudt",
        "role": "Dierenartsassistente",
        "category": "assistenten",
        "order": 10
    },
    {
        "slug": "robin-schepens",
        "url": "https://www.dewitteraafdierenartsen.be/robin-schepens-4/",
        "name": "Robin Schepens",
        "role": "Dierenartsassistent",
        "category": "assistenten",
        "order": 11
    },
    {
        "slug": "clara-daese",
        "url": "https://dewitteraafdierenartsen.be/clara-daese",
        "name": "Clara Daese",
        "role": "Jobstudent hulp dierenzorg",
        "category": "studenten",
        "order": 12
    },
    {
        "slug": "yentl-jacob",
        "url": "",
        "name": "Yentl Jacob",
        "role": "Jobstudent hulp dierenzorg",
        "category": "studenten",
        "order": 13
    }
]

out_dir = Path("_team")
out_dir.mkdir(exist_ok=True)

for m in team_info:
    slug = m["slug"]
    url = m["url"]
    name = m["name"]
    role = m["role"]
    cat = m["category"]
    order = m["order"]

    bio_text = ""
    accreditation = ""
    interests = []
    education = []
    pets = []

    if url:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            html = urllib.request.urlopen(req, timeout=10).read().decode("utf-8")
            soup = BeautifulSoup(html, "html.parser")
            for s in soup(["script", "style", "noscript"]):
                s.decompose()
            
            main = soup.find("main") or soup.find("article") or soup.find("body")
            
            # Look for headings like Accreditatie, Interesses, etc.
            for h in main.find_all(["h2", "h3", "h4", "p", "strong"]):
                txt = h.get_text(strip=True).lower()
                nxt = h.find_next_sibling()
                nxt_txt = nxt.get_text(strip=True) if nxt else ""
                
                if "accreditatie" in txt and not accreditation:
                    accreditation = nxt_txt
                elif "interesse" in txt and not interests:
                    if nxt and nxt.name == "ul":
                        interests = [li.get_text(strip=True) for li in nxt.find_all("li")]
                    elif nxt_txt:
                        interests = [line.strip("- *") for line in nxt_txt.split("\n") if line.strip()]
                elif "opleiding" in txt and not education:
                    if nxt and nxt.name == "ul":
                        education = [li.get_text(strip=True) for li in nxt.find_all("li")]
                    elif nxt_txt:
                        education = [line.strip("- *") for line in nxt_txt.split("\n") if line.strip()]
                elif ("huisdier" in txt or "thuis" in txt) and not pets:
                    if nxt and nxt.name == "ul":
                        pets = [li.get_text(strip=True) for li in nxt.find_all("li")]
                    elif nxt_txt:
                        pets = [line.strip("- *") for line in nxt_txt.split("\n") if line.strip()]

            # Look for bio / experience paragraphs
            paras = [p.get_text(strip=True) for p in main.find_all("p") if len(p.get_text(strip=True)) > 50]
            bio_candidates = [p for p in paras if not any(k in p.lower() for k in ["wachtdienst", "privacy", "cookie", "09/352"])]
            bio_text = "\n\n".join(bio_candidates[:3])
        except Exception as e:
            print(f"Error scraping {slug}: {e}")

    # Fallbacks if scraping was minimal
    if not bio_text:
        bio_text = f"{name} is werkzaam als {role.lower()} bij Dierenartsencentrum De Witte Raaf en zet zich dagelijks in met passie en toewijding voor de beste zorg voor uw huisdier."

    md_content = f"""---
name: "{name}"
role: "{role}"
category: "{cat}"
order: {order}
slug: "{slug}"
photo: "/assets/images/team/{slug}.jpg"
"""
    if accreditation:
        md_content += f'accreditation: "{accreditation}"\n'
    if interests:
        md_content += "interests:\n" + "\n".join([f'  - "{i}"' for i in interests]) + "\n"
    if education:
        md_content += "education:\n" + "\n".join([f'  - "{e}"' for e in education]) + "\n"
    if pets:
        md_content += "pets:\n" + "\n".join([f'  - "{p}"' for p in pets]) + "\n"

    md_content += f"---\n\n{bio_text}\n"

    out_file = out_dir / f"{slug}.md"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Written {out_file}")

print("Team import complete!")
