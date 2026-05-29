# missoes import handled in bot.py to avoid circular imports
from skills_sistema import SKILLS as SKILLS_DB, get_skill as get_skill_db
# -*- coding: utf-8 -*-
import discord
from discord import app_commands
import asyncio, random, os
from db import get_pool


# ─── ARENAS ──────────────────────────────────────────────────────
ARENAS = [
    {"id":"floresta", "nome":"Floresta Sombria",  "emoji":"🌲","bonus":"magia +15%", "cor":0x1D9E75,"img":"https://i.imgur.com/VdFyqem.jpeg"},
    {"id":"vulcao",   "nome":"Cratera Vulcanica", "emoji":"🌋","bonus":"fogo +20%",  "cor":0xD85A30,"img":"https://i.imgur.com/hlwTOAc.jpeg"},
    {"id":"gelo",     "nome":"Pico de Gelo",      "emoji":"❄️","bonus":"defesa +10%","cor":0x378ADD,"img":"https://i.imgur.com/R2i14Fb.jpeg"},
    {"id":"ruinas",   "nome":"Ruinas Arcanas",    "emoji":"🏚️","bonus":"crit +10%",  "cor":0x7F77DD,"img":"https://i.imgur.com/x9GPdiy.jpeg"},
    {"id":"coloseu",  "nome":"Coloseu Real",      "emoji":"🏟️","bonus":"neutro",     "cor":0xE4AF3C,"img":"https://i.imgur.com/imBvfqX.jpeg"},
]

# ─── POCOES ──────────────────────────────────────────────────────
POCOES = {
    "pocao_hp_p":   {"nome":"Pocao de Cura P",  "emoji":"🧪","tipo":"hp",  "valor":30,  "preco":50},
    "pocao_hp_m":   {"nome":"Pocao de Cura M",  "emoji":"💊","tipo":"hp",  "valor":60,  "preco":100},
    "pocao_hp_g":   {"nome":"Pocao de Cura G",  "emoji":"❤️","tipo":"hp",  "valor":120, "preco":200},
    "pocao_mana_p": {"nome":"Pocao de Mana P",  "emoji":"🔵","tipo":"mana","valor":20,  "preco":60},
    "pocao_mana_m": {"nome":"Pocao de Mana M",  "emoji":"💙","tipo":"mana","valor":50,  "preco":120},
    "elixir":       {"nome":"Elixir Supremo",   "emoji":"✨","tipo":"full", "valor":999, "preco":500},
}

# ─── LOJA ────────────────────────────────────────────────────────
LOJA_ITENS = {
    "armas": [
        {"id":"espada_prata",  "nome":"Espada de Prata", "emoji":"⚔️","raridade":"Incomum","preco":300, "desc":"Dano +5"},
        {"id":"cajado_magico", "nome":"Cajado Magico",   "emoji":"🪄","raridade":"Raro",   "preco":600, "desc":"Magia +10"},
        {"id":"arco_elfico",   "nome":"Arco Elfico",     "emoji":"🏹","raridade":"Raro",   "preco":550, "desc":"Critico +15%"},
        {"id":"lanca_sagrada", "nome":"Lanca Sagrada",   "emoji":"🔱","raridade":"Epico",  "preco":1200,"desc":"Sagrado +20"},
    ],
    "armaduras": [
        {"id":"armadura_couro","nome":"Armadura de Couro","emoji":"🥋","raridade":"Comum",  "preco":150,"desc":"Defesa +3"},
        {"id":"cota_malha",    "nome":"Cota de Malha",   "emoji":"🛡️","raridade":"Incomum","preco":400,"desc":"Defesa +8"},
        {"id":"armadura_plena","nome":"Armadura Plena",  "emoji":"⚙️","raridade":"Raro",   "preco":900,"desc":"Defesa +15"},
    ],
    "pocoes": [
        {"id":k,"nome":v["nome"],"emoji":v["emoji"],"raridade":"Comum","preco":v["preco"],
         "desc":f"Recupera {v['valor']} {'HP' if v['tipo']=='hp' else 'Mana'}"}
        for k,v in POCOES.items()
    ],
}

# ─── FERREIRO ────────────────────────────────────────────────────
RECEITAS = [
    {"id":"espada_orc",    "nome":"Espada Orc",       "emoji":"🗡️","tipo":"arma",    "raridade":"Raro",    "desc":"Forjada com metal orc",           "materiais":{"dente_orc":2,"minerio_ferro":3},"preco_forja":100},
    {"id":"armadura_escama","nome":"Armadura de Escama","emoji":"🐉","tipo":"armadura","raridade":"Epico",   "desc":"Resistente como escamas de dragao","materiais":{"escama_dragao":1,"fragmento_golem":2},"preco_forja":300},
    {"id":"cajado_osso2",  "nome":"Cajado Osseo+",    "emoji":"💀","tipo":"arma",    "raridade":"Raro",    "desc":"Amplifica magia negra",            "materiais":{"dente_orc":1,"sangue_anciao":1},"preco_forja":200},
    {"id":"elmo_dragao",   "nome":"Elmo do Dragao",   "emoji":"🪖","tipo":"armadura","raridade":"Lendario","desc":"Protecao maxima",                  "materiais":{"escama_dragao":2,"olho_dragao":1},"preco_forja":500},
]

# ─── MONSTROS ────────────────────────────────────────────────────
MONSTROS = [
    {"id":"goblin",  "nome":"Goblin",        "emoji":"👺","nivel":1, "hp":40, "ataque":6, "defesa":2, "xp":20, "moedas":10,"dificuldade":"facil",
     "skills":[{"nome":"Mordida","emoji":"🦷","dano":8},{"nome":"Arranhao","emoji":"💢","dano":5}],
     "loot":[("pedra_suja","Pedra Suja","material","Comum","🪨","Pedra qualquer")]},
    {"id":"lobo",    "nome":"Lobo Selvagem", "emoji":"🐺","nivel":3, "hp":65, "ataque":10,"defesa":4, "xp":35, "moedas":18,"dificuldade":"facil",
     "skills":[{"nome":"Mordida Feroz","emoji":"🦷","dano":14},{"nome":"Investida","emoji":"💨","dano":10}],
     "loot":[("pele_lobo","Pele de Lobo","material","Comum","🐾","Util para armaduras")]},
    {"id":"orc",     "nome":"Orc Guerreiro", "emoji":"👹","nivel":7, "hp":120,"ataque":18,"defesa":10,"xp":70, "moedas":40,"dificuldade":"medio",
     "skills":[{"nome":"Machado","emoji":"🪓","dano":22},{"nome":"Grito","emoji":"😤","dano":12}],
     "loot":[("dente_orc","Dente de Orc","material","Incomum","🦷","Ingrediente"),("machado_ferro","Machado de Ferro","arma","Incomum","🪓","Machado pesado")]},
    {"id":"golem",   "nome":"Golem de Pedra","emoji":"🗿","nivel":12,"hp":200,"ataque":22,"defesa":20,"xp":120,"moedas":65,"dificuldade":"medio",
     "skills":[{"nome":"Soco de Pedra","emoji":"👊","dano":30},{"nome":"Terremoto","emoji":"🌋","dano":20}],
     "loot":[("fragmento_golem","Fragmento de Golem","material","Raro","🪨","Material magico"),("nucleo_pedra","Nucleo de Pedra","material","Raro","💎","Nucleo magico")]},
    {"id":"vampiro", "nome":"Vampiro Anciao","emoji":"🧛","nivel":20,"hp":280,"ataque":35,"defesa":18,"xp":200,"moedas":120,"dificuldade":"dificil",
     "skills":[{"nome":"Drenar Sangue","emoji":"🩸","dano":40},{"nome":"Hipnose","emoji":"👁️","dano":15}],
     "loot":[("capa_vampiro","Capa de Vampiro","armadura","Epico","🧛","Absorve magia"),("sangue_anciao","Sangue Anciao","material","Raro","🩸","Pocao rara")]},
    {"id":"dragao",  "nome":"Dragao Jovem",  "emoji":"🐉","nivel":35,"hp":500,"ataque":60,"defesa":35,"xp":450,"moedas":300,"dificuldade":"lendario",
     "skills":[{"nome":"Baforada","emoji":"🔥","dano":70},{"nome":"Garra","emoji":"🐾","dano":50},{"nome":"Tempestade","emoji":"🌪️","dano":40}],
     "loot":[("escama_dragao","Escama de Dragao","material","Lendario","🐉","Lendario"),("dente_dragao","Dente de Dragao","material","Lendario","🦷","Lendario"),("olho_dragao","Olho de Dragao","material","Epico","👁️","Raro")]},
]

SKILLS_POR_CLASSE = {
    "guerreiro": [
        {"id":"golpe_basico", "nome":"Golpe Basico", "nivel":1, "emoji":"⚔️","dano":1.0,"mana":0, "desc":"Ataque simples"},
        {"id":"escudo",       "nome":"Escudo",        "nivel":5, "emoji":"🛡️","dano":0,  "mana":10,"desc":"Defesa +50% por 1 turno","efeito":"defesa"},
        {"id":"golpe_brutal", "nome":"Golpe Brutal",  "nivel":10,"emoji":"💥","dano":2.0,"mana":20,"desc":"Dano dobrado"},
        {"id":"furia",        "nome":"Furia",          "nivel":35,"emoji":"🔥","dano":1.5,"mana":30,"desc":"ULTIMATE +50% atk 3 turnos","efeito":"buff_ataque"},
    ],
    "mago": [
        {"id":"bola_fogo",    "nome":"Bola de Fogo",  "nivel":1, "emoji":"🔥","dano":1.3,"mana":15,"desc":"Dano magico"},
        {"id":"escudo_arcano","nome":"Escudo Arcano",  "nivel":5, "emoji":"💜","dano":0,  "mana":20,"desc":"Absorve 1 ataque","efeito":"escudo"},
        {"id":"raio",         "nome":"Raio",            "nivel":10,"emoji":"⚡","dano":1.6,"mana":25,"desc":"Dano alto"},
        {"id":"sobrecarga",   "nome":"Sobrecarga",     "nivel":35,"emoji":"✨","dano":3.0,"mana":50,"desc":"ULTIMATE dano x3"},
    ],
    "arqueiro": [
        {"id":"tiro_preciso", "nome":"Tiro Preciso",  "nivel":1, "emoji":"🎯","dano":1.0,"mana":0, "desc":"+30% critico"},
        {"id":"esquiva",      "nome":"Esquiva",         "nivel":5, "emoji":"💨","dano":0,  "mana":15,"desc":"Evita 1 ataque","efeito":"esquiva"},
        {"id":"tiro_multiplo","nome":"Tiro Multiplo",  "nivel":10,"emoji":"🏹","dano":0.6,"mana":20,"desc":"2 ataques"},
        {"id":"chuva_flechas","nome":"Chuva Flechas",  "nivel":35,"emoji":"☄️","dano":0.4,"mana":40,"desc":"ULTIMATE 5 ataques"},
    ],
    "paladino": [
        {"id":"golpe_sagrado","nome":"Golpe Sagrado",  "nivel":1, "emoji":"⚡","dano":1.2,"mana":10,"desc":"Fisico+magico"},
        {"id":"cura",         "nome":"Cura",            "nivel":5, "emoji":"💚","dano":0,  "mana":25,"desc":"Recupera 30% HP","efeito":"cura"},
        {"id":"aura_sagrada", "nome":"Aura Sagrada",   "nivel":10,"emoji":"🌟","dano":0,  "mana":30,"desc":"+stats 3 turnos","efeito":"buff_all"},
        {"id":"juizo_final",  "nome":"Juizo Final",    "nivel":35,"emoji":"☀️","dano":2.5,"mana":50,"desc":"ULTIMATE sagrado"},
    ],
    "necromante": [
        {"id":"drenar_vida",  "nome":"Drenar Vida",    "nivel":1, "emoji":"🌑","dano":1.1,"mana":10,"desc":"Rouba HP","efeito":"dreno"},
        {"id":"invocar_morto","nome":"Invocar Morto",  "nivel":8, "emoji":"💀","dano":0.8,"mana":20,"desc":"Esqueleto ataca"},
        {"id":"maldicao",     "nome":"Maldicao",        "nivel":15,"emoji":"🩸","dano":0.7,"mana":15,"desc":"Veneno","efeito":"veneno"},
        {"id":"exercito",     "nome":"Exercito Morto", "nivel":35,"emoji":"☠️","dano":2.0,"mana":50,"desc":"ULTIMATE 3 mortos"},
    ],
    "dracomante": [
        {"id":"baforada",     "nome":"Baforada",        "nivel":1, "emoji":"🔥","dano":1.4,"mana":15,"desc":"Fogo continuo"},
        {"id":"escamas",      "nome":"Escamas",          "nivel":10,"emoji":"🐉","dano":0,  "mana":20,"desc":"-30% dano recebido","efeito":"armadura"},
        {"id":"forma_menor",  "nome":"Forma Menor",    "nivel":20,"emoji":"🌋","dano":0,  "mana":35,"desc":"+30% stats 3t","efeito":"buff_all"},
        {"id":"dragao_eterno","nome":"Dragao Eterno",  "nivel":42,"emoji":"💎","dano":3.5,"mana":60,"desc":"ULTIMATE forma dragao"},
    ],
    "arcano": [
        {"id":"faisca",       "nome":"Faisca Arcana",  "nivel":1, "emoji":"✨","dano":1.2,"mana":10,"desc":"Arcano puro"},
        {"id":"campo_forca",  "nome":"Campo de Forca", "nivel":5, "emoji":"🔮","dano":0,  "mana":20,"desc":"Reflete 20% dano","efeito":"reflexo"},
        {"id":"distorcao",    "nome":"Distorcao",       "nivel":10,"emoji":"🌀","dano":0.5,"mana":15,"desc":"Confunde -40% precisao","efeito":"confusao"},
        {"id":"singularidade","nome":"Singularidade",  "nivel":35,"emoji":"⭐","dano":4.0,"mana":60,"desc":"ULTIMATE colapso"},
    ],
}

COR_RAR = {"Comum":0x888780,"Incomum":0x1D9E75,"Raro":0x378ADD,"Epico":0x7F77DD,"Lendario":0xD85A30}

# ─── PASSIVAS POR CLASSE ─────────────────────────────────────────

class Passiva:
    """Controla o estado da passiva de cada jogador em batalha."""
    def __init__(self, classe_id):
        self.classe_id = classe_id
        self.turno     = 0
        # Guerreiro
        self.bonus_def_acum  = 0
        # Mago
        self.bonus_mag_acum  = 0.0
        # Necromante
        self.bonus_dreno     = 1.0
        # Arcano
        self.arcano_acum     = 0.0
        self.arcano_turnos_sem_dano = 0

    def inicio_turno(self, hp_j, hp_jmx):
        """Chamado no inicio do turno do jogador. Retorna cura passiva (int)."""
        self.turno += 1
        cura = 0

        # Paladino: se HP < 30%, cura 15 por turno
        if self.classe_id == "paladino":
            if hp_j / max(1, hp_jmx) < 0.30:
                cura = 15

        # Mago: acumula bonus de dano magico +8% por turno (max 40%)
        if self.classe_id == "mago":
            self.bonus_mag_acum = min(0.40, self.bonus_mag_acum + 0.08)

        return cura

    def apos_critico(self):
        """Chamado quando o jogador acerta critico. Retorna mana recuperada."""
        if self.classe_id == "arqueiro":
            return 8
        return 0

    def apos_dreno(self):
        """Chamado apos usar dreno. Retorna novo multiplicador de dreno."""
        if self.classe_id == "necromante":
            self.bonus_dreno = min(2.0, self.bonus_dreno + 0.10)
        return self.bonus_dreno

    def apos_tomar_dano(self):
        """Chamado quando o jogador toma dano."""
        if self.classe_id == "arcano":
            self.arcano_acum = 0.0
            self.arcano_turnos_sem_dano = 0

    def fim_turno_sem_dano(self):
        """Chamado quando o jogador NAO tomou dano no turno."""
        if self.classe_id == "arcano":
            self.arcano_turnos_sem_dano += 1
            self.arcano_acum = min(0.50, self.arcano_turnos_sem_dano * 0.10)

    def bonus_defesa(self):
        """Retorna bonus de defesa passivo."""
        b = 0
        # Guerreiro: +3 DEF a cada 3 turnos
        if self.classe_id == "guerreiro":
            b += (self.turno // 3) * 3
            b = min(b, 30)  # cap 30
        # Dracomante: -10% dano recebido (retorna como reducao)
        return b

    def reducao_dano(self):
        """Retorna reducao percentual de dano recebido (0.0 a 1.0)."""
        if self.classe_id == "dracomante":
            return 0.10  # 10% de reducao
        return 0.0

    def imune_status(self, status):
        """Retorna True se a classe e imune ao status."""
        if self.classe_id == "dracomante":
            return status in ("queimadura", "veneno")
        return False

    def multiplicador_dano(self):
        """Retorna multiplicador de dano extra da passiva."""
        if self.classe_id == "mago":
            return 1.0 + self.bonus_mag_acum
        if self.classe_id == "arcano":
            return 1.0 + self.arcano_acum
        return 1.0

    def desc_passiva(self):
        """Retorna descricao atual da passiva para mostrar no embed."""
        if self.classe_id == "guerreiro":
            b = (self.turno // 3) * 3
            return f"🗡️ Passiva: +{min(b,30)} DEF acumulado"
        if self.classe_id == "arqueiro":
            return "🏹 Passiva: Critico recupera 8 mana"
        if self.classe_id == "mago":
            return f"🔮 Passiva: Dano magico +{int(self.bonus_mag_acum*100)}%"
        if self.classe_id == "paladino":
            return "⚡ Passiva: Cura 15 HP/turno se HP < 30%"
        if self.classe_id == "necromante":
            return f"🌑 Passiva: Dreno x{self.bonus_dreno:.1f}"
        if self.classe_id == "dracomante":
            return "🐉 Passiva: -10% dano, imune veneno/queimadura"
        if self.classe_id == "arcano":
            return f"✨ Passiva: Dano arcano +{int(self.arcano_acum*100)}%"
        return ""

EMOJI_CLASSE = {"guerreiro":"🗡️","mago":"🔮","arqueiro":"🏹","paladino":"⚡","necromante":"🌑","dracomante":"🐉","arcano":"✨"}

# ─── DB ──────────────────────────────────────────────────────────

async def get_p(user_id):
    pool = await get_pool()
    async with pool.acquire() as db:
        return await db.fetchrow("SELECT * FROM personagens WHERE user_id=$1", user_id)

async def get_skills_eq(user_id):
    pool = await get_pool()
    pool = await get_pool()
    async with pool.acquire() as db:
        rows = await db.fetch("SELECT skill_id FROM skills_equipadas WHERE user_id=$1 ORDER BY slot", user_id)
        return [r["skill_id"] for r in rows]
async def get_skills_desbloq(user_id):
    pool = await get_pool()
    async with pool.acquire() as db:
        rows = await db.fetch("SELECT skill_id FROM skills_desbloqueadas WHERE user_id=$1", user_id)
        return [r["skill_id"] for r in rows]





    pool = await get_pool()
    async with pool.acquire() as db:
        return await db.fetch(
            "SELECT * FROM inventario WHERE user_id=$1 AND (item_id LIKE 'pocao%' OR item_id='elixir')",
            user_id
        )

async def remover_pocao(user_id, item_id):
    pool = await get_pool()
    async with pool.acquire() as db:
        row = await db.fetchrow(
            "SELECT id, quantidade FROM inventario WHERE user_id=$1 AND item_id=$2",
            user_id, item_id
        )
        if row:
            if row["quantidade"] > 1:
                await db.execute("UPDATE inventario SET quantidade=quantidade-1 WHERE id=$1", row["id"])
            else:
                await db.execute("DELETE FROM inventario WHERE id=$1", row["id"])

async def get_pocoes_inv(user_id):
    """Busca pocoes do inventario."""
    pool = await get_pool()
    async with pool.acquire() as db:
        return await db.fetch(
            "SELECT * FROM inventario WHERE user_id=$1 AND (item_id LIKE 'pocao%' OR item_id='elixir')",
            user_id
        )


async def equipar_skills_iniciais(user_id, classe_id):
    """Equipa as 4 primeiras skills desbloqueadas automaticamente."""
    skills_desbloq = await get_skills_desbloq(user_id)
    skills_classe = SKILLS_POR_CLASSE.get(classe_id, [])
    para_equipar = [s["id"] for s in skills_classe if s["id"] in skills_desbloq][:4]
    if not para_equipar and skills_classe:
        para_equipar = [skills_classe[0]["id"]]
    pool = await get_pool()
    async with pool.acquire() as db:
        await db.execute("DELETE FROM skills_equipadas WHERE user_id=$1", user_id)
        for slot, sid in enumerate(para_equipar):
            await db.execute(
                "INSERT OR REPLACE INTO skills_equipadas(user_id,skill_id,slot) VALUES(?,?,?)",
                (user_id, sid, slot)
            )

async def salvar_resultado(user_id, hp, xp, moedas, vitoria, classe_id, nivel_atual):
    pool = await get_pool()
    async with pool.acquire() as db:
        p = await db.fetchrow("SELECT xp,nivel,hp_max,ataque,defesa FROM personagens WHERE user_id=$1", user_id)
        if not p: return 0
        novo_xp = p["xp"] + xp
        nv = p["nivel"]
        levelups = 0
        needed = 100 + (nv-1)*50
        while novo_xp >= needed:
            novo_xp -= needed
            nv += 1
            needed = 100 + (nv-1)*50
            levelups += 1
        hp_max = p["hp_max"] + levelups*5
        atk = p["ataque"] + levelups*2
        dfs = p["defesa"] + levelups*1
        hp_final = max(1, min(hp, hp_max))
        await db.execute("""
            UPDATE personagens SET hp_atual=$1,hp_max=$2,xp=$3,nivel=$4,ataque=$5,defesa=$6,
            moedas=moedas+$7,vitorias=vitorias+$8,derrotas=derrotas+$9 WHERE user_id=$10
        """, (hp_final,hp_max,novo_xp,nv,atk,dfs,moedas,
              1 if vitoria else 0, 0 if vitoria else 1, user_id))
        for s in SKILLS_POR_CLASSE.get(classe_id, []):
            if s["nivel"] <= nv:
                await db.execute(
                    "INSERT INTO skills_desbloqueadas(user_id,skill_id) VALUES(?,?)",
                    (user_id, s["id"])
                )
        return levelups

async def add_loot(user_id, loot):
    pool = await get_pool()
    async with pool.acquire() as db:
        for it in loot:
            iid,nome,tipo,rar,emoji,desc = it
            ex = await db.fetchrow("SELECT id,quantidade FROM inventario WHERE user_id=$1 AND item_id=$2", (user_id,iid))
            if ex:
                await db.execute("UPDATE inventario SET quantidade=quantidade+1 WHERE id=$1", ex["id"])
            else:
                await db.execute("INSERT INTO inventario(user_id,item_id,nome,tipo,raridade,emoji,descricao) VALUES($1,$2,$3,$4,$5,$6,$7)",
                                 (user_id,iid,nome,tipo,rar,emoji,desc))

async def init_db_batalha():
    pass  # tabelas criadas no db.py











# ─── HELPERS ─────────────────────────────────────────────────────

def calc_dano(atk, dfs, mult=1.0, crit=False):
    base = max(1, atk - dfs//2)
    d = int(base * mult) + random.randint(-2, 3)
    return max(1, int(d*1.5) if crit else d)

def barra_hp(cur, mx):
    if mx <= 0: return "░░░░░░░░░░"
    p = max(0.0, cur/mx)
    f = int(p * 10)
    if p > 0.6:   char = "█"
    elif p > 0.3: char = "▓"
    else:         char = "▒"
    return char * f + "░" * (10-f)

def get_skill(classe_id, skill_id):
    # Tenta no novo sistema primeiro
    sk = SKILLS_DB.get(skill_id)
    if sk:
        return {
            "id": skill_id,
            "nome": sk["nome"],
            "emoji": sk["emoji"],
            "mana": sk["mana"],
            "dano": sk["dano_mult"],
            "dano_mult": sk["dano_mult"],
            "efeito": sk.get("efeito"),
            "desc": sk["desc"],
            "hits": sk.get("hits", 1),
        }
    # Fallback no sistema antigo
    for s in SKILLS_POR_CLASSE.get(classe_id, []):
        if s["id"] == skill_id: return s
    return None

async def get_arma_equipada(user_id):
    pool = await get_pool()
    async with pool.acquire() as db:
        return await db.fetchrow(
            "SELECT * FROM inventario WHERE user_id=$1 AND tipo='arma' AND equipado=1 LIMIT 1",
            user_id
        )

async def get_armadura_equipada(user_id):
    pool = await get_pool()
    async with pool.acquire() as db:
        return await db.fetchrow(
            "SELECT * FROM inventario WHERE user_id=$1 AND tipo='armadura' AND equipado=1 LIMIT 1",
            user_id
        )



# Afinidade arma por classe
AFINIDADE_ARMA = {
    "guerreiro":  ["espada_ferro","espada_prata","espada_orc","lanca_sagrada","garra_dragao"],
    "arqueiro":   ["arco_madeira","arco_elfico"],
    "mago":       ["cajado_pinho","cajado_magico","cajado_osso2"],
    "paladino":   ["lanca_sagrada","espada_prata"],
    "necromante": ["cajado_osso2","cajado_pinho"],
    "dracomante": ["garra_dragao","espada_ferro"],
    "arcano":     ["cajado_magico","cajado_pinho"],
}

AFINIDADE_ARMADURA = {
    "guerreiro":  ["armadura_plena","cota_malha","elmo_dragao","armadura_titan"],
    "arqueiro":   ["armadura_couro","cota_malha"],
    "mago":       ["armadura_couro"],
    "paladino":   ["armadura_plena","armadura_escama"],
    "necromante": ["capa_vampiro","armadura_couro"],
    "dracomante": ["armadura_escama","elmo_dragao"],
    "arcano":     ["armadura_couro","cota_malha"],
}

def calcular_bonus_equip(classe_id, arma, armadura):
    """Retorna (bonus_ataque, bonus_defesa) baseado na afinidade"""
    bonus_atk = 1.0
    bonus_dfs = 1.0

    if arma:
        arma_id = arma["item_id"]
        if arma_id in AFINIDADE_ARMA.get(classe_id, []):
            bonus_atk = 1.15  # +15% dano
        else:
            bonus_atk = 0.85  # -15% dano

    if armadura:
        arm_id = armadura["item_id"]
        if arm_id in AFINIDADE_ARMADURA.get(classe_id, []):
            bonus_dfs = 1.10  # +10% defesa
        else:
            bonus_dfs = 0.90  # -10% defesa

    return bonus_atk, bonus_dfs

def get_skills_jogador(p, ids_equipadas):
    """Retorna lista de skills equipadas, com fallback para primeiras da classe."""
    skills = [get_skill(p["classe_id"], sid) for sid in ids_equipadas if get_skill(p["classe_id"], sid)]
    if not skills:
        cls = SKILLS_POR_CLASSE.get(p["classe_id"], [])
        skills = cls[:4] if cls else []
    return skills

# ─── EMBED DE BATALHA ────────────────────────────────────────────

def build_embed(
    titulo, arena,
    nome1, emoji1, hp1, hp1mx, mana1, mana1mx,
    nome2, emoji2, hp2, hp2mx, mana2, mana2mx,
    turno, vez_nome, vez_emoji,
    log_lista, cor, pvp=True
):
    # Destaque visual de quem é a vez
    seta1 = "▶️ " if vez_nome == nome1 else "　"
    seta2 = "▶️ " if vez_nome == nome2 else "　"
    tempo_txt = "⏰ 30 segundos" if pvp else "sem limite"

    embed = discord.Embed(
        title=titulo,
        color=cor
    )
    embed.set_image(url=arena["img"])

    # Campo jogador 1
    embed.add_field(
        name=f"{seta1}{emoji1} {nome1}",
        value=(
            f"❤️ `{barra_hp(hp1,hp1mx)}` **{hp1}/{hp1mx}**\n"
            f"💙 `{barra_hp(mana1,mana1mx)}` {mana1}/{mana1mx}"
        ),
        inline=True
    )

    # Campo arena (centro)
    embed.add_field(
        name=f"{arena['emoji']} Arena",
        value=f"*{arena['nome']}*\n+{arena['bonus']}",
        inline=True
    )

    # Campo jogador 2
    embed.add_field(
        name=f"{seta2}{emoji2} {nome2}",
        value=(
            f"❤️ `{barra_hp(hp2,hp2mx)}` **{hp2}/{hp2mx}**\n"
            f"💙 `{barra_hp(mana2,mana2mx)}` {mana2}/{mana2mx}"
        ),
        inline=True
    )

    # Log dos últimos turnos
    if log_lista:
        embed.add_field(
            name="📜 Últimos eventos",
            value="\n".join(log_lista[-5:]),
            inline=False
        )

    embed.set_footer(text=f"Turno {turno} • Vez de {vez_emoji} {vez_nome} • {tempo_txt} • {arena['nome']}")
    return embed

# ─── VIEW DE BATALHA ─────────────────────────────────────────────

class MochilaView(discord.ui.View):
    """View secundária que aparece ao clicar em Mochila."""
    def __init__(self, user_id, pocoes, parent_view):
        super().__init__(timeout=20)
        self.user_id     = user_id
        self.parent_view = parent_view

        if not pocoes:
            return

        opcoes = [
            discord.SelectOption(
                label=f"{p['emoji']} {p['nome']} (x{p['quantidade']})",
                value=p["item_id"],
                description=f"Recupera {'HP' if POCOES.get(p['item_id'],{}).get('tipo')!='mana' else 'Mana'}"
            )
            for p in pocoes[:10]
        ]
        sel = discord.ui.Select(placeholder="Qual pocao usar?", options=opcoes)
        sel.callback = self._usar
        self.add_item(sel)

    async def _usar(self, inter: discord.Interaction):
        if inter.user.id != self.user_id:
            await inter.response.send_message("Nao e sua vez!", ephemeral=True)
            return
        if self.parent_view.acao_feita:
            await inter.response.defer()
            return
        await inter.response.defer()
        self.parent_view.acao_feita = True
        self.parent_view.acao = ("pocao", inter.data["values"][0])
        self.parent_view.stop()
        self.stop()


class BatalhaView(discord.ui.View):
    def __init__(self, user_id, skills, pocoes, pvp=False):
        super().__init__(timeout=30 if pvp else None)
        self.user_id    = user_id
        self.acao       = None
        self.acao_feita = False
        self._pocoes    = list(pocoes) if pocoes else []
        self._skills    = list(skills) if skills else []

        for i, sk in enumerate(skills[:4]):
            mana_txt = f" ({sk.get('mana',0)}💙)" if sk.get("mana",0) > 0 else ""
            btn = discord.ui.Button(
                label=f"{sk['emoji']} {sk['nome']}{mana_txt}",
                style=discord.ButtonStyle.primary,
                row=0 if i < 2 else 1,
                custom_id=f"skill_{i}"
            )
            btn.callback = self._fazer_skill(i)
            self.add_item(btn)

        mochila_btn = discord.ui.Button(
            label=f"🎒 Mochila ({len(self._pocoes)})" if self._pocoes else "🎒 Mochila (vazia)",
            style=discord.ButtonStyle.secondary,
            disabled=len(self._pocoes) == 0,
            row=2,
            custom_id="mochila"
        )
        mochila_btn.callback = self._abrir_mochila
        self.add_item(mochila_btn)

        fugir_btn = discord.ui.Button(
            label="🏃 Fugir",
            style=discord.ButtonStyle.danger,
            row=2,
            custom_id="fugir"
        )
        fugir_btn.callback = self._fugir
        self.add_item(fugir_btn)

    def _fazer_skill(self, idx):
        async def callback(inter: discord.Interaction):
            # Responde IMEDIATAMENTE antes de qualquer verificacao
            try:
                await inter.response.defer()
            except Exception:
                pass
            if inter.user.id != self.user_id:
                return
            if self.acao_feita:
                return
            self.acao_feita = True
            self.acao = ("skill", idx)
            self.stop()
        return callback

    async def _abrir_mochila(self, inter: discord.Interaction):
        if inter.user.id != self.user_id:
            try:
                await inter.response.send_message("Nao e sua vez!", ephemeral=True)
            except Exception:
                pass
            return
        if self.acao_feita:
            try:
                await inter.response.defer()
            except Exception:
                pass
            return
        if not self._pocoes:
            try:
                await inter.response.send_message("Mochila vazia!", ephemeral=True)
            except Exception:
                pass
            return
        opcoes = [
            discord.SelectOption(
                label=f"{p['emoji']} {p['nome']} (x{p['quantidade']})",
                value=p["item_id"]
            )
            for p in self._pocoes[:10]
        ]
        sel = discord.ui.Select(placeholder="Qual pocao usar?", options=opcoes)
        parent = self

        async def usar(inter2: discord.Interaction):
            try:
                await inter2.response.defer()
            except Exception:
                pass
            if inter2.user.id != parent.user_id:
                return
            if parent.acao_feita:
                return
            parent.acao_feita = True
            parent.acao = ("pocao", sel.values[0])
            parent.stop()

        sel.callback = usar
        v = discord.ui.View(timeout=20)
        v.add_item(sel)
        try:
            await inter.response.send_message("🎒 Escolha uma pocao:", view=v, ephemeral=True)
        except Exception:
            pass

    async def _fugir(self, inter: discord.Interaction):
        try:
            await inter.response.defer()
        except Exception:
            pass
        if inter.user.id != self.user_id:
            return
        if self.acao_feita:
            return
        self.acao_feita = True
        self.acao = ("fugir", None)
        self.stop()

    async def on_timeout(self):
        if not self.acao_feita:
            self.acao = ("timeout", None)
            self.stop()

# ─── VIEW ESCOLHER ARENA ─────────────────────────────────────────

class EscolherArenaView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.arena   = None
        opcoes = [
            discord.SelectOption(
                label=f"{a['emoji']} {a['nome']}",
                value=a["id"],
                description=f"Bonus: {a['bonus']}"
            ) for a in ARENAS
        ]
        sel = discord.ui.Select(placeholder="Escolha a arena...", options=opcoes)
        sel.callback = self._escolher
        self.add_item(sel)

    async def _escolher(self, inter: discord.Interaction):
        if inter.user.id != self.user_id:
            await inter.response.send_message("Nao e voce!", ephemeral=True)
            return
        self.arena = next(a for a in ARENAS if a["id"] == inter.data["values"][0])
        embed = discord.Embed(
            title=f"{self.arena['emoji']} Arena: {self.arena['nome']}",
            description=f"Bonus: {self.arena['bonus']}\n\nPreparando a batalha...",
            color=self.arena["cor"]
        )
        await inter.response.edit_message(embed=embed, view=None)
        self.stop()

    async def on_timeout(self):
        if not self.arena:
            self.arena = random.choice(ARENAS)
            self.stop()

# ─── VIEW ACEITAR DUELO ──────────────────────────────────────────

class AceitarDueloView(discord.ui.View):
    def __init__(self, desafiante_id, desafiado_id):
        super().__init__(timeout=300)
        self.desafiante_id = desafiante_id
        self.desafiado_id  = desafiado_id
        self.resposta      = None

    @discord.ui.button(label="Aceitar duelo ⚔️", style=discord.ButtonStyle.success)
    async def aceitar(self, inter: discord.Interaction, b):
        if inter.user.id != self.desafiado_id:
            await inter.response.send_message("Nao e pra voce!", ephemeral=True)
            return
        self.resposta = True
        self.stop()
        await inter.response.defer()

    @discord.ui.button(label="Recusar ❌", style=discord.ButtonStyle.danger)
    async def recusar(self, inter: discord.Interaction, b):
        if inter.user.id != self.desafiado_id:
            await inter.response.send_message("Nao e pra voce!", ephemeral=True)
            return
        self.resposta = False
        self.stop()
        await inter.response.defer()

    async def on_timeout(self):
        self.resposta = None
        self.stop()

# ─── VIEW GERENCIAR SKILLS ───────────────────────────────────────

class GerenciarSkillsView(discord.ui.View):
    def __init__(self, user_id, skills_disponiveis, equipadas_ids):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.skills  = skills_disponiveis
        opcoes = [
            discord.SelectOption(
                label=f"{s['emoji']} {s['nome']}",
                value=s["id"],
                description=f"{s['desc']} | Mana: {s.get('mana',0)}"[:50],
                default=s["id"] in equipadas_ids
            ) for s in skills_disponiveis
        ]
        if opcoes:
            sel = discord.ui.Select(
                placeholder="Escolha ate 4 skills...",
                min_values=1,
                max_values=min(4, len(opcoes)),
                options=opcoes
            )
            sel.callback = self._sel
            self.add_item(sel)

    async def _sel(self, inter: discord.Interaction):
        if inter.user.id != self.user_id:
            await inter.response.send_message("Nao sao suas skills!", ephemeral=True)
            return
        selecionadas = inter.data["values"][:4]
        selecionadas = inter.data["values"][:4]
        pool = await get_pool()
        async with pool.acquire() as db:
            await db.execute("DELETE FROM skills_equipadas WHERE user_id=$1", self.user_id)
            for slot, sid in enumerate(selecionadas):
                await db.execute(
                    "INSERT INTO skills_equipadas(user_id,skill_id,slot) VALUES($1,$2,$3) ON CONFLICT(user_id,slot) DO UPDATE SET skill_id=EXCLUDED.skill_id",
                    self.user_id, sid, slot
                )
        nomes = [s["nome"] for s in self.skills if s["id"] in selecionadas]
        await inter.response.edit_message(
            embed=discord.Embed(
                title="Skills atualizadas!",
                description="\n".join([f"• {n}" for n in nomes]),
                color=0x1D9E75
            ),
            view=None
        )
# ─── ENGINE TREINO ───────────────────────────────────────────────

async def rodar_treino(interaction, p, monstro, arena):
    ids_eq = await get_skills_eq(p["user_id"])
    if not ids_eq:
        await equipar_skills_iniciais(p["user_id"], p["classe_id"])
        ids_eq = await get_skills_eq(p["user_id"])
    skills = get_skills_jogador(p, ids_eq)

    # Equipamento e bonus de afinidade
    arma    = await get_arma_equipada(p["user_id"])
    armadura= await get_armadura_equipada(p["user_id"])
    bonus_atk, bonus_dfs = calcular_bonus_equip(p["classe_id"], arma, armadura)

    # Info de equipamento para mostrar no embed
    arma_txt = f"{arma['emoji']} {arma['nome']}" if arma else "Sem arma"
    arm_txt  = f"{armadura['emoji']} {armadura['nome']}" if armadura else "Sem armadura"
    bonus_atk_txt = f"+15%" if bonus_atk > 1 else ("-15%" if bonus_atk < 1 else "0%")
    bonus_dfs_txt = f"+10%" if bonus_dfs > 1 else ("-10%" if bonus_dfs < 1 else "0%")

    hp_j    = p["hp_atual"]
    hp_jmx  = p["hp_max"]
    mana_j  = p["mana_atual"] if "mana_atual" in p.keys() else 100
    mana_jmx= p["mana_max"]   if "mana_max"   in p.keys() else 100
    hp_m    = monstro["hp"]
    hp_mmx  = monstro["hp"]
    turno   = 1
    efeitos = {}
    emoji_j = EMOJI_CLASSE.get(p["classe_id"], "⚔️")
    msgs_batalha = []
    passiva = Passiva(p["classe_id"])
    tomou_dano_turno = False

    def barra_status():
        return (
            f"{emoji_j} **{p['nome']}** "
            f"❤️`{barra_hp(hp_j,hp_jmx)}`{hp_j}/{hp_jmx} "
            f"💙{mana_j}/{mana_jmx}\n"
            f"{monstro['emoji']} **{monstro['nome']}** "
            f"❤️`{barra_hp(hp_m,hp_mmx)}`{hp_m}/{hp_mmx}"
        )

    # Mensagem inicial
    embed_inicio = discord.Embed(
        title=f"⚔️ Batalha iniciada!",
        description=f"**{emoji_j} {p['nome']}** vs **{monstro['emoji']} {monstro['nome']}**\n\n{barra_status()}",
        color=arena["cor"]
    )
    embed_inicio.set_image(url=arena["img"])
    embed_inicio.set_footer(text=f"{arena['emoji']} {arena['nome']} • {arena['bonus']}")
    msg_tmp = await interaction.followup.send(embed=embed_inicio, wait=True)
    msgs_batalha.append(msg_tmp)

    while hp_j > 0 and hp_m > 0:
        # Mensagem SUA VEZ com botoes
        pocoes = await get_pocoes_inv(p["user_id"])
        view   = BatalhaView(p["user_id"], skills, pocoes, pvp=False)

        embed_vez = discord.Embed(
            title=f"🎮 Turno {turno} — Sua vez!",
            description=barra_status(),
            color=0x7F77DD
        )
        embed_vez.set_footer(text=f"Escolha sua acao • {arena['nome']}")
        msg_vez = await interaction.followup.send(embed=embed_vez, view=view, wait=True)
        msgs_batalha.append(msg_vez)
        await view.wait()

        acao, val = view.acao or ("timeout", None)

        try:
            await msg_vez.edit(view=None)
        except Exception:
            pass

        # Passiva inicio do turno
        tomou_dano_turno = False
        cura_passiva = passiva.inicio_turno(hp_j, hp_jmx)
        if cura_passiva > 0:
            hp_j = min(hp_jmx, hp_j + cura_passiva)
            msgs_batalha.append(await interaction.followup.send(
                embed=discord.Embed(
                    description=f"⚡ **Passiva Paladino:** Cura {cura_passiva} HP automaticamente! ({hp_j}/{hp_jmx})",
                    color=0x1D9E75
                ), wait=True
            ))

        if acao == "fugir":
            for m in msgs_batalha:
                try:
                    await m.delete()
                except Exception:
                    pass
            await interaction.followup.send(embed=discord.Embed(
                title="🏃 Você fugiu!",
                description="Voce escapou da batalha e voltou para a cidade.",
                color=0x888780
            ))
            return

        # Processa acao do jogador
        linha_jogador = ""
        cor_acao = 0x378ADD

        if acao == "pocao" and val:
            pd = POCOES.get(val)
            if pd:
                await remover_pocao(p["user_id"], val)
                if pd["tipo"] == "hp":
                    ganho = pd["valor"]
                    hp_j  = min(hp_jmx, hp_j + ganho)
                    linha_jogador = f"🧪 Usou **{pd['nome']}** e recuperou **+{ganho} HP!**"
                    cor_acao = 0x1D9E75
                elif pd["tipo"] == "mana":
                    ganho  = pd["valor"]
                    mana_j = min(mana_jmx, mana_j + ganho)
                    linha_jogador = f"🔵 Usou **{pd['nome']}** e recuperou **+{ganho} Mana!**"
                    cor_acao = 0x378ADD
                elif pd["tipo"] == "full":
                    hp_j   = hp_jmx
                    mana_j = mana_jmx
                    linha_jogador = f"✨ Usou **Elixir Supremo!** HP e Mana totalmente restaurados!"
                    cor_acao = 0xE4AF3C

        elif acao == "skill" and val is not None and val < len(skills):
            sk     = skills[val]
            efeito = sk.get("efeito", "")
            custo  = sk.get("mana", 0)

            if custo > mana_j:
                dano  = calc_dano(p["ataque"], monstro["defesa"])
                hp_m -= dano
                linha_jogador = f"⚔️ Sem mana para **{sk['nome']}**! Usou ataque básico causando **{dano} de dano!**"
                cor_acao = 0x888780
            elif efeito == "cura":
                mana_j -= custo
                cura    = int(hp_jmx * 0.30)
                hp_j    = min(hp_jmx, hp_j + cura)
                linha_jogador = f"{sk['emoji']} Usou **{sk['nome']}** e recuperou **+{cura} HP!**"
                cor_acao = 0x1D9E75
            elif efeito in ("escudo","esquiva","armadura","reflexo"):
                mana_j -= custo
                efeitos[efeito] = 2
                nomes = {"escudo":"Escudo Arcano ativado! Absorvera o proximo ataque.",
                         "esquiva":"Esquiva preparada! Evitara o proximo ataque.",
                         "armadura":"Escamas ativas! -30% de dano recebido.",
                         "reflexo":"Campo de Forca ativo! Reflete 20% do dano."}
                linha_jogador = f"{sk['emoji']} Usou **{sk['nome']}**! {nomes.get(efeito,'Efeito ativo!')}"
                cor_acao = 0x7F77DD
            elif efeito == "dreno":
                mana_j -= custo
                dano    = calc_dano(p["ataque"], monstro["defesa"], sk["dano"], bonus_atk=bonus_atk)
                roubo   = dano // 2
                hp_m   -= dano
                hp_j    = min(hp_jmx, hp_j + roubo)
                linha_jogador = f"{sk['emoji']} **{sk['nome']}** causou **{dano} de dano** e drenou **+{roubo} HP!**"
                cor_acao = 0x1D9E75
            elif sk["id"] == "tiro_multiplo":
                mana_j -= custo
                d1 = calc_dano(p["ataque"], monstro["defesa"], sk["dano"])
                d2 = calc_dano(p["ataque"], monstro["defesa"], sk["dano"])
                hp_m -= d1 + d2
                linha_jogador = f"{sk['emoji']} **{sk['nome']}** — 2 ataques: {d1} + {d2} = **{d1+d2} de dano total!**"
                cor_acao = 0xD85A30
            elif sk["id"] == "chuva_flechas":
                mana_j -= custo
                hits   = [calc_dano(p["ataque"], monstro["defesa"], sk["dano"]) for _ in range(5)]
                total  = sum(hits)
                hp_m  -= total
                linha_jogador = f"{sk['emoji']} **{sk['nome']}** — 5 flechas! {'+'.join(str(h) for h in hits)} = **{total} de dano total!**"
                cor_acao = 0xD85A30
            else:
                mana_j -= custo
                crit    = random.random() < 0.15
                dano    = calc_dano(p["ataque"], monstro["defesa"], sk["dano"], crit)
                hp_m   -= dano
                efetividade = "foi **SUPER EFETIVO!** 💥" if crit else "causou dano!"
                linha_jogador = f"{sk['emoji']} **{sk['nome']}** {efetividade} **{dano} de dano** em {monstro['emoji']} {monstro['nome']}!"
                cor_acao = 0xD85A30 if crit else 0x378ADD
        else:
            dano  = calc_dano(p["ataque"], monstro["defesa"])
            hp_m -= dano
            linha_jogador = f"⚔️ Ataque basico causou **{dano} de dano** em {monstro['emoji']} {monstro['nome']}!"
            cor_acao = 0x888780

        hp_m = max(0, hp_m)

        # Manda mensagem do que o jogador fez
        embed_acao_j = discord.Embed(
            title=f"{emoji_j} {p['nome']} agiu!",
            description=f"{linha_jogador}\n\n{barra_status()}",
            color=cor_acao
        )
        embed_acao_j.set_footer(text=f"Turno {turno}")
        msg_tmp = await interaction.followup.send(embed=embed_acao_j, wait=True)
        msgs_batalha.append(msg_tmp)

        if hp_m <= 0:
            break

        await asyncio.sleep(1.2)

        # Monstro ataca
        sk_m    = random.choice(monstro["skills"])
        dano_m  = calc_dano(monstro["ataque"], p["defesa"])
        linha_monstro = ""
        cor_monstro   = 0xE24B4A

        if "esquiva" in efeitos and efeitos["esquiva"] > 0:
            linha_monstro = f"{monstro['emoji']} **{monstro['nome']}** usou **{sk_m['emoji']} {sk_m['nome']}**... mas voce **esquivou!** 💨 Nenhum dano!"
            efeitos["esquiva"] -= 1
            cor_monstro = 0x888780
        elif "escudo" in efeitos and efeitos["escudo"] > 0:
            linha_monstro = f"{monstro['emoji']} **{monstro['nome']}** usou **{sk_m['emoji']} {sk_m['nome']}**... mas o **escudo absorveu!** 💜 Nenhum dano!"
            efeitos["escudo"] -= 1
            cor_monstro = 0x7F77DD
        else:
            hp_j -= dano_m
            hp_j  = max(0, hp_j)
            efetividade = "foi **DEVASTADOR!** 💀" if dano_m > p["ataque"] * 1.5 else "causou dano!"
            linha_monstro = f"{monstro['emoji']} **{monstro['nome']}** usou **{sk_m['emoji']} {sk_m['nome']}** e {efetividade} **{dano_m} de dano** em {emoji_j} {p['nome']}!"

        embed_monstro = discord.Embed(
            title=f"{monstro['emoji']} {monstro['nome']} atacou!",
            description=f"{linha_monstro}\n\n{barra_status()}",
            color=cor_monstro
        )
        embed_monstro.set_footer(text=f"Turno {turno}")
        msg_tmp = await interaction.followup.send(embed=embed_monstro, wait=True)
        msgs_batalha.append(msg_tmp)

        mana_j = min(mana_jmx, mana_j + 5)
        turno += 1
        await asyncio.sleep(1.0)

    # Resultado
    vitoria = hp_m <= 0
    if vitoria:
        loot   = [random.choice(monstro["loot"])] if random.random() < 0.6 else []
        lvlups = await salvar_resultado(p["user_id"], hp_j, monstro["xp"], monstro["moedas"], True, p["classe_id"], p["nivel"])
        if loot: await add_loot(p["user_id"], loot)
        desc = f"🏆 Voce derrotou **{monstro['emoji']} {monstro['nome']}**!\n\n✨ **+{monstro['xp']} XP** | 💰 **+{monstro['moedas']} moedas**"
        if loot: desc += f"\n🎁 Loot: {loot[0][4]} **{loot[0][1]}**"
        if lvlups: desc += f"\n\n🎉 **LEVEL UP! Voce chegou ao nivel {p['nivel']+lvlups}!**"
        cor = 0x1D9E75
        titulo = "🏆 Vitória!"
    else:
        await salvar_resultado(p["user_id"], 10, 0, 0, False, p["classe_id"], p["nivel"])
        desc = f"💀 Voce foi derrotado por **{monstro['emoji']} {monstro['nome']}**...\nAcordou na cidade com 10 HP.",
        cor  = 0xE24B4A
        titulo = "💀 Derrota..."

    # Deleta todas as mensagens da batalha
    for m in msgs_batalha:
        try:
            await m.delete()
        except Exception:
            pass

    fim = discord.Embed(title=titulo, description=desc, color=cor)
    fim.set_image(url=arena["img"])
    await interaction.followup.send(embed=fim)


async def rodar_pvp(channel, p1, p2, m1, m2, arena, duelo_msg=None):
    """PvP com mensagens por turno igual ao treino."""

    # Garante skills equipadas para ambos
    for p in (p1, p2):
        ids = await get_skills_eq(p["user_id"])
        if not ids:
            await equipar_skills_iniciais(p["user_id"], p["classe_id"])

    ids1 = await get_skills_eq(p1["user_id"])
    ids2 = await get_skills_eq(p2["user_id"])
    sk1  = get_skills_jogador(p1, ids1)
    sk2  = get_skills_jogador(p2, ids2)

    hp1,  hp2   = p1["hp_atual"], p2["hp_atual"]
    hp1mx,hp2mx = p1["hp_max"],   p2["hp_max"]
    mana1  = p1["mana_atual"] if "mana_atual" in p1.keys() else 100
    mana2  = p2["mana_atual"] if "mana_atual" in p2.keys() else 100
    mana1mx = mana2mx = 100
    vez     = p1["user_id"]
    turno   = 1
    efeitos1, efeitos2 = {}, {}
    e1 = EMOJI_CLASSE.get(p1["classe_id"], "⚔️")
    e2 = EMOJI_CLASSE.get(p2["classe_id"], "⚔️")
    msgs = []

    def status():
        return (
            f"{e1} **{p1['nome']}** ❤️`{barra_hp(hp1,hp1mx)}`{hp1}/{hp1mx} 💙{mana1}\n"
            f"{e2} **{p2['nome']}** ❤️`{barra_hp(hp2,hp2mx)}`{hp2}/{hp2mx} 💙{mana2}"
        )

    def vez_nome():
        return p1["nome"] if vez == p1["user_id"] else p2["nome"]
    def vez_emoji():
        return e1 if vez == p1["user_id"] else e2
    def vez_member():
        return m1 if vez == p1["user_id"] else m2

    # Mensagem de início
    embed_inicio = discord.Embed(
        title=f"⚔️ DUELO: {p1['nome']} vs {p2['nome']}",
        description=(
            f"{m1.mention} vs {m2.mention}\n\n"
            f"{status()}\n\n"
            f"{arena['emoji']} **Arena:** {arena['nome']} — {arena['bonus']}"
        ),
        color=arena["cor"]
    )
    embed_inicio.set_image(url=arena["img"])
    msg_ini = await channel.send(embed=embed_inicio)
    msgs.append(msg_ini)

    while hp1 > 0 and hp2 > 0:
        atk_p   = p1 if vez == p1["user_id"] else p2
        dfs_p   = p2 if vez == p1["user_id"] else p1
        sk_vez  = sk1 if vez == p1["user_id"] else sk2
        ef_atk  = efeitos1 if vez == p1["user_id"] else efeitos2

        poc  = await get_pocoes_inv(vez)
        view = BatalhaView(vez, sk_vez, poc, pvp=True)

        embed_vez = discord.Embed(
            title=f"🎮 Turno {turno} — Vez de {vez_emoji()} {vez_nome()}!",
            description=status(),
            color=arena["cor"]
        )
        embed_vez.set_footer(text=f"⏰ 30 segundos para agir • {vez_member().mention}")
        msg_vez = await channel.send(embed=embed_vez, view=view)
        msgs.append(msg_vez)
        await view.wait()

        try: await msg_vez.edit(view=None)
        except: pass

        acao, val = view.acao or ("timeout", None)
        linha = ""; cor_acao = arena["cor"]

        if acao == "fugir":
            venc   = p2 if vez == p1["user_id"] else p1
            perd   = p1 if vez == p1["user_id"] else p2
            m_venc = m2  if vez == p1["user_id"] else m1
            m_perd = m1  if vez == p1["user_id"] else m2
            hp_v   = hp2 if vez == p1["user_id"] else hp1
            await salvar_resultado(venc["user_id"], hp_v, 80, 60, True, venc["classe_id"], venc["nivel"])
            await salvar_resultado(perd["user_id"], 10, 0, 0, False, perd["classe_id"], perd["nivel"])
            for m in msgs:
                try: await m.delete()
                except: pass
            await channel.send(embed=discord.Embed(
                title="🏃 Fuga!",
                description=f"**{perd['nome']}** fugiu!\n**{venc['nome']}** vence por W.O.!\n\n+80 XP | +60 🪙 para {m_venc.mention}",
                color=0xE4AF3C
            ))
            return

        elif acao == "timeout":
            linha = f"⏰ {vez_member().display_name} perdeu o turno por timeout!"
            cor_acao = 0x888780

        elif acao == "pocao" and val:
            pd = POCOES.get(val)
            if pd:
                await remover_pocao(vez, val)
                if pd["tipo"] == "hp":
                    if vez == p1["user_id"]: hp1 = min(hp1mx, hp1+pd["valor"])
                    else:                    hp2 = min(hp2mx, hp2+pd["valor"])
                    linha = f"🧪 **{pd['nome']}**: +{pd['valor']} HP!"
                    cor_acao = 0x1D9E75
                elif pd["tipo"] == "mana":
                    if vez == p1["user_id"]: mana1 = min(mana1mx, mana1+pd["valor"])
                    else:                    mana2 = min(mana2mx, mana2+pd["valor"])
                    linha = f"🔵 **{pd['nome']}**: +{pd['valor']} Mana!"
                elif pd["tipo"] == "full":
                    if vez == p1["user_id"]: hp1=hp1mx; mana1=mana1mx
                    else:                    hp2=hp2mx; mana2=mana2mx
                    linha = "✨ **Elixir Supremo**: tudo restaurado!"
                    cor_acao = 0xE4AF3C

        elif acao == "skill" and val is not None and val < len(sk_vez):
            sk     = sk_vez[val]
            custo  = sk.get("mana", 0)
            efeito = sk.get("efeito", "")
            mana_v = mana1 if vez == p1["user_id"] else mana2

            if custo > mana_v:
                dano = calc_dano(atk_p["ataque"], dfs_p["defesa"])
                if vez == p1["user_id"]: hp2 -= dano
                else:                    hp1 -= dano
                linha = f"⚔️ Sem mana! Ataque basico: **{dano} dano**"
                cor_acao = 0x888780
            elif efeito == "cura":
                cura = int(atk_p["hp_max"]*0.30)
                if vez == p1["user_id"]: hp1=min(hp1mx,hp1+cura); mana1-=custo
                else:                    hp2=min(hp2mx,hp2+cura); mana2-=custo
                linha = f"{sk['emoji']} **{sk['nome']}**: +{cura} HP recuperado!"
                cor_acao = 0x1D9E75
            elif efeito in ("escudo","esquiva","armadura","defesa","reflexo"):
                ef_atk[efeito] = 2
                if vez == p1["user_id"]: mana1 -= custo
                else:                    mana2 -= custo
                linha = f"{sk['emoji']} **{sk['nome']}**: efeito ativo por 2 turnos!"
                cor_acao = 0x7F77DD
            elif efeito == "dreno":
                dano  = calc_dano(atk_p["ataque"], dfs_p["defesa"], sk.get("dano",1.0))
                roubo = dano // 2
                if vez == p1["user_id"]: hp2-=dano; mana1-=custo; hp1=min(hp1mx,hp1+roubo)
                else:                    hp1-=dano; mana2-=custo; hp2=min(hp2mx,hp2+roubo)
                linha = f"{sk['emoji']} **{sk['nome']}**: {dano} dano! +{roubo} HP drenado!"
                cor_acao = 0x1D9E75
            else:
                crit = random.random() < 0.12
                dano = calc_dano(atk_p["ataque"], dfs_p["defesa"], sk.get("dano",1.0), crit)
                if vez == p1["user_id"]: hp2-=dano; mana1-=custo
                else:                    hp1-=dano; mana2-=custo
                efetividade = "foi **SUPER EFETIVO!** 💥" if crit else "causou dano!"
                linha = f"{vez_emoji()} **{sk['nome']}** {efetividade} **{dano} de dano** em {e2 if vez==p1['user_id'] else e1}!"
                cor_acao = 0xD85A30 if crit else arena["cor"]
        else:
            dano = calc_dano(atk_p["ataque"], dfs_p["defesa"])
            if vez == p1["user_id"]: hp2 -= dano
            else:                    hp1 -= dano
            linha = f"⚔️ Ataque basico: **{dano} dano**"
            cor_acao = 0x888780

        hp1 = max(0, hp1); hp2 = max(0, hp2)

        msg_acao = await channel.send(
            embed=discord.Embed(
                title=f"{vez_emoji()} {vez_nome()} agiu!",
                description=f"{linha}\n\n{status()}",
                color=cor_acao
            )
        )
        msgs.append(msg_acao)

        if hp1 <= 0 or hp2 <= 0:
            break

        await asyncio.sleep(1.0)
        mana1 = min(mana1mx, mana1+5)
        mana2 = min(mana2mx, mana2+5)
        turno += 1
        vez = p2["user_id"] if vez == p1["user_id"] else p1["user_id"]

    # Resultado
    venc   = p1 if hp1 > 0 else p2
    perd   = p2 if hp1 > 0 else p1
    m_venc = m1 if hp1 > 0 else m2
    m_perd = m2 if hp1 > 0 else m1
    hp_v   = hp1 if hp1 > 0 else hp2
    xp_v   = 100 + perd["nivel"]*5
    mo_v   = 80  + perd["nivel"]*3

    await salvar_resultado(venc["user_id"], hp_v, xp_v, mo_v, True, venc["classe_id"], venc["nivel"])
    await salvar_resultado(perd["user_id"], 10, 20, 0, False, perd["classe_id"], perd["nivel"])

    # Limpa mensagens
    for m in msgs:
        try: await m.delete()
        except: pass

    fim = discord.Embed(
        title=f"🏆 {venc['nome']} vence o duelo!",
        description=(
            f"{m_venc.mention} derrotou {m_perd.mention}!\n\n"
            f"+{xp_v} XP | +{mo_v} 🪙 para o vencedor\n"
            f"+20 XP para o derrotado"
        ),
        color=0xE4AF3C
    )
    fim.set_image(url=arena["img"])
    await channel.send(embed=fim)
