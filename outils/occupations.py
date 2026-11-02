"""Prépare la copie des créneaux occupés du planning de la mobilisation.

Usage : python3 -I outils/occupations.py DOSSIER_EXPORT_MOBILISATION FICHIER_SORTIE
DOSSIER_EXPORT_MOBILISATION contient salles/*.json et reservations/*.json (export de la base
de la page de la mobilisation). Écrit un document JSON {maj, creneaux:[{date, debut, fin, salle, batiment}]}
destiné au document « externe/occupations » de la base du planning d'anthropologie.
Seuls la salle, le jour et les horaires sont recopiés (pas les intitulés), à partir de la veille.
"""
import json, sys, pathlib, datetime

src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])

def load(coll):
    docs = {}
    for f in sorted((src / coll).glob("*.json")):
        raw = json.loads(f.read_text(encoding="utf-8"))
        data = raw.get("data", raw) if isinstance(raw, dict) and isinstance(raw.get("data"), dict) else raw
        docs[f.stem] = data if isinstance(data, dict) else {}
    return docs

salles = load("salles")
depuis = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
creneaux = []
for r in load("reservations").values():
    if r.get("statut") == "Annulée" or not isinstance(r.get("date"), str) or r["date"] < depuis:
        continue
    salle = salles.get(r.get("salleId") or "", {})
    nom = (salle.get("nom") or r.get("salle") or "").strip()
    if not nom or not r.get("debut") or not r.get("fin"):
        continue
    creneaux.append({"date": r["date"], "debut": r["debut"], "fin": r["fin"], "salle": nom,
                     "batiment": (salle.get("batiment") or r.get("batiment") or "").strip()})
creneaux.sort(key=lambda c: (c["date"], c["debut"], c["salle"]))
doc = {"maj": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "creneaux": creneaux}
out.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
print(f"{len(creneaux)} créneaux occupés recopiés")
