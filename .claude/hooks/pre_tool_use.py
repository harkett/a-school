import re

# Protection maximale : tout ce qui touche .env est interdit
BLOCKED = [
    r"\.env",          # fichier .env
    r"dotenv",         # libs dotenv
    r"env",            # fallback large
]

# Liste blanche minimale pour Bash (sécurité béton)
SAFE_BASH = [
    r"pwd",
    r"ls$",
    r"ls -la$",
    r"echo",
]

def on_pre_tool_use(tool_name, tool_input):
    text = str(tool_input).lower()

    # 1. Blocage total de .env (lecture, écriture, grep, cat, etc.)
    for pattern in BLOCKED:
        if re.search(pattern, text):
            return {
                "allowed": False,
                "message": "Accès refusé : .env est protégé par le hook PreToolUse."
            }

    # 2. Sécurité Bash : tout ce qui n'est pas dans la whitelist est refusé
    if tool_name.lower() == "bash":
        cmd = text.strip()
        if not any(re.match(p, cmd) for p in SAFE_BASH):
            return {
                "allowed": False,
                "message": f"Commande Bash interdite : {cmd}"
            }

    # 3. Sinon, autoriser
    return {"allowed": True}
