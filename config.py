# config.py — Configurações centralizadas do bot

import os

# ==================================================
# DISCORD
# ==================================================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# ==================================================
# DATABASE
# ==================================================

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/railway")

# ==================================================
# IMAGENS (URLs) - serão carregadas do imagens.py
# ==================================================

# As imagens estão centralizadas no arquivo imagens.py