"""Prépare la copie des créneaux occupés du planning de la mobilisation, à partir de sa page publique.

Usage : python3 -I outils/occupations.py INDEX_HTML_MOBILISATION FICHIER_SORTIE
INDEX_HTML_MOBILISATION est le fichier index.html du dépôt mobilisation-nanterre/planning.
Écrit {maj, source, creneaux:[{date, debut, fin, salle, batiment}]} pour le document « externe/occupations »
du planning d'anthropologie. Seuls la salle, le jour et les horaires sont recopiés, à partir de la veille.
"""
import json, sys, pathlib, datetime, re

page = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
m = re.search(r"window\.__SNAPSHOT=(.*?);</script>", page, re.S)
if not m:
    sys.exit("Page publique de la mobilisation illisible.")
snap = json.loads(m.group(1).replace("<\\/", "</"))
salles = {s["id"]: s.get("data", {}) for s in snap.get("salles", [])}
depuis = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
creneaux = []
for r in snap.get("reservations", []):
    d = r.get("data", {})
    if d.get("statut") == "Annulée" or not isinstance(d.get("date"), str) or d["date"] < depuis:
        continue
    s = salles.get(d.get("salleId") or "", {})
    nom = (s.get("nom") or d.get("salle") or "").strip()
    if not nom or not d.get("debut") or not d.get("fin"):
        continue
    creneaux.append({"date": d["date"], "debut": d["debut"], "fin": d["fin"], "salle": nom,
                     "batiment": (s.get("batiment") or d.get("batiment") or "").strip()})
creneaux.sort(key=lambda c: (c["date"], c["debut"], c["salle"]))
doc = {"maj": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
       "source": snap.get("genere"), "creneaux": creneaux}
pathlib.Path(sys.argv[2]).write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
print(f"{len(creneaux)} créneaux occupés recopiés (page publique de la mobilisation du {snap.get('genere')})")
