#!/usr/bin/env python3
"""Recreate Phase 2+3 in-app state: custom prompts, Claude Code type-out mode,
and the dev-jargon word replacements. App must be quit before running."""
import json, plistlib, sqlite3, subprocess, sys, time, uuid
from pathlib import Path

DOMAIN = "com.prakashjoshipax.VoiceInk"

LIGHT_ID = str(uuid.uuid4()).upper()
CLAUDE_ID = str(uuid.uuid4()).upper()

GENERAL_PROMPT = ("You clean up dictated speech. Remove filler words (um, uh, like), fix grammar, "
                  "punctuation, and capitalization. Preserve the speaker's meaning and wording. "
                  "Output ONLY the cleaned text.")
TERMINAL_PROMPT = ("You clean up a spoken instruction to a coding assistant. Remove filler words and "
                   "fix punctuation and capitalization only. Do NOT rephrase, summarize, translate to "
                   "prose, or add markdown/code fences. Preserve technical terms, file paths, command "
                   "names, and identifiers exactly as heard. Output ONLY the cleaned instruction.")

def defaults_write_data(key, obj):
    hexdata = json.dumps(obj, ensure_ascii=False).encode("utf-8").hex()
    subprocess.run(["defaults", "write", DOMAIN, key, "-data", hexdata], check=True)

# --- 0. preflight: abort before writing anything ---
raw = subprocess.run(["defaults", "export", DOMAIN, "-"], check=True, capture_output=True).stdout
plist = plistlib.loads(raw)
if "modeConfigurationsV2" not in plist:
    sys.exit("FATAL: no modes found - launch VoiceInk and complete onboarding first")
modes = json.loads(plist["modeConfigurationsV2"])
assert any(m["name"] == "Dictation" for m in modes), "Dictation mode missing - aborting"
assert not any(m["name"] == "Claude Code" for m in modes), "Claude Code mode already exists - aborting"

# --- 1. customPrompts ---
prompts = [
    {"id": LIGHT_ID, "title": "Light cleanup", "promptText": GENERAL_PROMPT,
     "useSystemInstructions": False},
    {"id": CLAUDE_ID, "title": "Claude Code terminal", "promptText": TERMINAL_PROMPT,
     "useSystemInstructions": False},
]
defaults_write_data("customPrompts", prompts)
print("customPrompts written:", LIGHT_ID, CLAUDE_ID)

# --- 2. modeConfigurationsV2: attach prompt to Dictation, append Claude Code mode ---
for m in modes:
    if m["name"] == "Dictation":
        m["selectedPrompt"] = LIGHT_ID
        m["selectedAIProvider"] = "Ollama"

TERMINALS = [
    ("com.apple.Terminal", "Terminal"),
    ("com.googlecode.iterm2", "iTerm2"),
    ("co.zeit.hyper", "Hyper"),
    ("com.mitchellh.ghostty", "Ghostty"),
    ("com.microsoft.VSCode", "Visual Studio Code"),
    ("com.todesktop.230313mzl4w4u92", "Cursor"),
]
claude_mode = {
    "id": str(uuid.uuid4()).upper(),
    "name": "Claude Code",
    "icon": {"kind": "symbol", "value": "terminal"},
    "appConfigs": [
        {"id": str(uuid.uuid4()).upper(), "bundleIdentifier": bid, "appName": name}
        for bid, name in TERMINALS
    ],
    "isAIEnhancementEnabled": True,
    "selectedPrompt": CLAUDE_ID,
    "selectedTranscriptionModelName": "parakeet-tdt-0.6b-v3",
    "isRealtimeTranscriptionEnabled": True,
    "selectedLanguage": "en",
    "isTextFormattingEnabled": False,
    "useClipboardContext": False,
    "useSelectedTextContext": False,
    "useScreenCapture": False,
    "selectedAIProvider": "Ollama",
    "selectedAIModel": "wispr-cleanup:latest",
    "outputMode": "typeOut",
    "autoSendKey": "none",
    "isEnabled": True,
    "isDefault": False,
}
modes.append(claude_mode)
defaults_write_data("modeConfigurationsV2", modes)
print("modeConfigurationsV2 written: Dictation+prompt, Claude Code (typeOut)")

# --- 3. Word replacements in the SwiftData dictionary store ---
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
db_path = Path.home() / "Library/Application Support/com.prakashjoshipax.VoiceInk/dictionary.store"
con = sqlite3.connect(db_path)
cur = con.cursor()
cur.execute("PRAGMA wal_checkpoint(TRUNCATE)")
row = cur.execute("SELECT Z_ENT, Z_MAX FROM Z_PRIMARYKEY WHERE Z_NAME='WordReplacement'").fetchone()
if row is None:
    sys.exit("FATAL: WordReplacement entity not found in Z_PRIMARYKEY")
z_ent, z_max = row
existing = cur.execute("SELECT COUNT(*) FROM ZWORDREPLACEMENT").fetchone()[0]
print(f"dictionary.store: Z_ENT={z_ent}, Z_MAX={z_max}, existing rows={existing}")
now_coredata = time.time() - 978307200  # Core Data epoch: 2001-01-01
pk = z_max
for original, replacement in REPLACEMENTS:
    pk += 1
    cur.execute(
        "INSERT INTO ZWORDREPLACEMENT (Z_PK, Z_ENT, Z_OPT, ZISENABLED, ZDATEADDED, ZORIGINALTEXT, ZREPLACEMENTTEXT, ZID) "
        "VALUES (?,?,1,1,?,?,?,?)",
        (pk, z_ent, now_coredata, original, replacement, uuid.uuid4().bytes),
    )
cur.execute("UPDATE Z_PRIMARYKEY SET Z_MAX=? WHERE Z_NAME='WordReplacement'", (pk,))
con.commit()
count = cur.execute("SELECT COUNT(*) FROM ZWORDREPLACEMENT WHERE ZISENABLED=1").fetchone()[0]
con.close()
print(f"word replacements inserted: {len(REPLACEMENTS)} (total enabled now {count})")
print("DONE")
