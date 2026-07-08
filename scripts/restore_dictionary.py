#!/usr/bin/env python3
"""Insert the 17 dev-jargon word replacements into VoiceInk's dictionary store.
Run only while VoiceInk is quit. Safe to re-run: aborts if rows already exist."""
import sqlite3, time, uuid
from pathlib import Path

REPLACEMENTS = [
    ("cloud code, clod code, clawed code, claud code", "Claude Code"),
    ("voice ink, voice inc", "VoiceInk"),
    ("oh llama, o llama, olama", "Ollama"),
    ("whisper cpp, whisper c p p", "whisper.cpp"),
    ("pair a keet, para keet", "Parakeet"),
    ("get hub, git hub", "GitHub"),
    ("jason", "JSON"),
    ("yammel, yamel", "YAML"),
    ("ex code, x code", "Xcode"),
    ("type script", "TypeScript"),
    ("java script", "JavaScript"),
    ("swift ui, swift you eye, swift u i", "SwiftUI"),
    ("local host", "localhost"),
    ("c g event, see gee event", "CGEvent"),
    ("re factor", "refactor"),
    ("ghost tea, ghosty", "Ghostty"),
    ("wispr flow, whisper flow", "wisprFlow"),
]

db = Path.home() / "Library/Application Support/com.prakashjoshipax.VoiceInk/dictionary.store"
con = sqlite3.connect(db)
cur = con.cursor()
row = cur.execute("SELECT Z_ENT, Z_MAX FROM Z_PRIMARYKEY WHERE Z_NAME='WordReplacement'").fetchone()
assert row, "WordReplacement entity missing"
z_ent, z_max = row
existing = cur.execute("SELECT COUNT(*) FROM ZWORDREPLACEMENT").fetchone()[0]
assert existing == 0, f"{existing} rows already present - aborting to avoid duplicates"
now = time.time() - 978307200  # Core Data epoch: 2001-01-01
pk = z_max
for orig, repl in REPLACEMENTS:
    pk += 1
    cur.execute(
        "INSERT INTO ZWORDREPLACEMENT (Z_PK,Z_ENT,Z_OPT,ZISENABLED,ZDATEADDED,ZORIGINALTEXT,ZREPLACEMENTTEXT,ZID) "
        "VALUES (?,?,1,1,?,?,?,?)",
        (pk, z_ent, now, orig, repl, uuid.uuid4().bytes),
    )
cur.execute("UPDATE Z_PRIMARYKEY SET Z_MAX=? WHERE Z_NAME='WordReplacement'", (pk,))
con.commit()
print("inserted:", cur.execute("SELECT COUNT(*) FROM ZWORDREPLACEMENT WHERE ZISENABLED=1").fetchone()[0])
con.close()
print("DONE")
