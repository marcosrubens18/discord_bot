# -*- coding: utf-8 -*-
import discord
from discord import app_commands
import aiosqlite, asyncio, random

DB_PATH = "rpg.db"

EMOJI_CLASSE = {"guerreiro":"🗡️","mago":"🔮","arqueiro":"🏹","paladino":"⚡","necromante":"🌑","dracomante":"🐉","arcano":"✨"}
COR_RAR = {"Comum":0x888780,"Incomum":0x1D9E75,"Raro":0x378ADD,"Epico":0x7F77DD,"Lendario":0xD85A30}

SKILLS_POR_CLASSE = {
    "guerreiro": [
        {"id":"golpe_basico","nome":"Golpe Basico","nivel":1,"emoji":"⚔️","dano":1.0,"mana":0,"desc":"Ataque simples"},
        {"id":"escudo","nome":"Escudo","nivel":5,"emoji":"🛡️","dano":0,"mana":10,"desc":"Defesa +50%","efeito":"defesa"},
        {"id":"golpe_brutal","nome":"Golpe Brutal","nivel":10,"emoji":"💥","dano":2.0,"mana":20,"desc":"Dano dobrado"},
        {"id":"furia","nome":"Furia","nivel":35,"emoji":"🔥","dano":1.5,"mana":30,"desc":"ULTIMATE","efeito":"buff_ataque"},
    ],
    "mago": [
        {"id":"bola_fogo","nome":"Bola de Fogo","nivel":1,"emoji":"🔥","dano":1.3,"mana":15,"desc":"Dano magico"},
        {"id":"escudo_arcano","nome":"Escudo Arcano","nivel":5,"emoji":"💜","dano":0,"mana":20,"desc":"Absorve 1 ataque","efeito":"escudo"},
        {"id":"raio","nome":"Raio","nivel":10,"emoji":"⚡","dano":1.6,"mana":25,"desc":"Dano alto"},
        {"id":"sobrecarga","nome":"Sobrecarga","nivel":35,"emoji":"✨","dano":3.0,"mana":50,"desc":"ULTIMATE"},
    ],
    "arqueiro": [
        {"id":"tiro_preciso","nome":"Tiro Preciso","nivel":1,"emoji":"🎯","dano":1.0,"mana":0,"desc":"+30% critico"},
        {"id":"esquiva","nome":"Esquiva","nivel":5,"emoji":"💨","dano":0,"mana":15,"desc":"Evita 1 ataque","efeito":"esquiva"},
        {"id":"tiro_multiplo","nome":"Tiro Multiplo","nivel":10,"emoji":"🏹","dano":0.6,"mana":20,"desc":"2 ataques"},
        {"id":"chuva_flechas","nome":"Chuva Flechas","nivel":35,"emoji":"☄️","dano":0.4,"mana":40,"desc":"ULTIMATE"},
    ],
    "paladino": [
        {"id":"golpe_sagrado","nome":"Golpe Sagrado","nivel":1,"emoji":"⚡","dano":1.2,"mana":10,"desc":"Fisico+magico"},
        {"id":"cura","nome":"Cura","nivel":5,"emoji":"💚","dano":0,"mana":25,"desc":"Recupera 30% HP","efeito":"cura"},
        {"id":"aura_sagrada","nome":"Aura Sagrada","nivel":10,"emoji":"🌟","dano":0,"mana":30,"desc":"+stats","efeito":"buff_all"},
        {"id":"juizo_final","nome":"Juizo Final","nivel":35,"emoji":"☀️","dano":2.5,"mana":50,"desc":"ULTIMATE"},
    ],
    "necromante": [
        {"id":"drenar_vida","nome":"Drenar Vida","nivel":1,"emoji":"🌑","dano":1.1,"mana":10,"desc":"Rouba HP","efeito":"dreno"},
        {"id":"invocar_morto","nome":"Invocar Morto","nivel":8,"emoji":"💀","dano":0.8,"mana":20,"desc":"Esqueleto ataca"},
        {"id":"maldicao","nome":"Maldicao","nivel":15,"emoji":"🩸","dano":0.7,"mana":15,"desc":"Veneno"},
        {"id":"exercito","nome":"Exercito Morto","nivel":35,"emoji":"☠️","dano":2.0,"mana":50,"desc":"ULTIMATE"},
    ],
    "dracomante": [
        {"id":"baforada","nome":"Baforada","nivel":1,"emoji":"🔥","dano":1.4,"mana":15,"desc":"Fogo continuo"},
        {"id":"escamas","nome":"Escamas","nivel":10,"emoji":"🐉","dano":0,"mana":20,"desc":"-30% dano","efeito":"armadura"},
        {"id":"forma_menor","nome":"Forma Menor","nivel":20,"emoji":"🌋","dano":0,"mana":35,"desc":"+30% stats","efeito":"buff_all"},
        {"id":"dragao_eterno","nome":"Dragao Eterno","nivel":42,"emoji":"💎","dano":3.5,"mana":60,"desc":"ULTIMATE"},
    ],
    "arcano": [
        {"id":"faisca","nome":"Faisca Arcana","nivel":1,"emoji":"✨","dano":1.2,"mana":10,"desc":"Arcano puro"},
        {"id":"campo_forca","nome":"Campo de Forca","nivel":5,"emoji":"🔮","dano":0,"mana":20,"desc":"Reflete 20%","efeito":"reflexo"},
        {"id":"distorcao","nome":"Distorcao","nivel":10,"emoji":"🌀","dano":0.5,"mana":15,"desc":"Confunde"},
        {"id":"singularidade","nome":"Singularidade","nivel":35,"emoji":"⭐","dano":4.0,"mana":60,"desc":"ULTIMATE"},
    ],
}

# ─── RANKS DE DUNGEON ────────────────────────────────────────────

RANKS = {
    "F": {
        "nome":"Dungeon Rank F","emoji":"🟫","nivel_min":1,"cor":0x888780,
        "desc":"Para iniciantes. Monstros fracos mas boa fonte de XP.",
        "recompensa_andar":{"xp":30,"moedas":15},
        "recompensa_chefe":{"xp":150,"moedas":80},
        "andares": [
            {"andar":1,"nome":"Caverna Rasa",      "emoji":"🕳️","monstro":{"nome":"Goblin",       "emoji":"👺","hp":50, "ataque":7, "defesa":2,"skills":[{"nome":"Mordida","emoji":"🦷","dano":8}]}},
            {"andar":2,"nome":"Floresta Escura",   "emoji":"🌲","monstro":{"nome":"Lobo Selvagem", "emoji":"🐺","hp":70, "ataque":11,"defesa":4,"skills":[{"nome":"Investida","emoji":"💨","dano":12}]}},
            {"andar":3,"nome":"Pântano Podre",     "emoji":"🌿","monstro":{"nome":"Sapo Gigante",  "emoji":"🐸","hp":85, "ataque":9, "defesa":6,"skills":[{"nome":"Veneno","emoji":"🟢","dano":10}]}},
            {"andar":4,"nome":"Ruínas Abandonadas","emoji":"🏚️","monstro":{"nome":"Esqueleto",     "emoji":"💀","hp":95, "ataque":13,"defesa":5,"skills":[{"nome":"Golpe de Osso","emoji":"🦴","dano":14}]}},
            {"andar":5,"nome":"Salão das Sombras", "emoji":"🌑","monstro":{"nome":"Sombra Menor",  "emoji":"👤","hp":110,"ataque":15,"defesa":7,"skills":[{"nome":"Toque Sombrio","emoji":"🌑","dano":16}]}},
        ],
        "chefe":{"nome":"Rei Goblin","emoji":"👑","hp":250,"ataque":20,"defesa":10,
                 "skills":[{"nome":"Grito Real","emoji":"📣","dano":18},{"nome":"Garras","emoji":"🦷","dano":22},{"nome":"Invocar Gobelins","emoji":"👺","dano":15}],
                 "loot_raro":("anel_goblin","Anel do Rei Goblin","especial","Raro","💍","Aumenta chance de loot em 10%"),
                 "loot_epico":None},
    },
    "E": {
        "nome":"Dungeon Rank E","emoji":"🟩","nivel_min":5,"cor":0x1D9E75,
        "desc":"Monstros com habilidades especiais. Requer preparo.",
        "recompensa_andar":{"xp":60,"moedas":30},
        "recompensa_chefe":{"xp":300,"moedas":180},
        "andares": [
            {"andar":1,"nome":"Mina Abandonada",   "emoji":"⛏️","monstro":{"nome":"Orc Minerador",  "emoji":"👹","hp":130,"ataque":18,"defesa":10,"skills":[{"nome":"Picareta","emoji":"⛏️","dano":20}]}},
            {"andar":2,"nome":"Floresta Maldita",  "emoji":"🌳","monstro":{"nome":"Treant",          "emoji":"🌳","hp":160,"ataque":15,"defesa":18,"skills":[{"nome":"Galhos","emoji":"🌿","dano":17}]}},
            {"andar":3,"nome":"Lago Envenenado",   "emoji":"💧","monstro":{"nome":"Hidra",            "emoji":"🐍","hp":180,"ataque":22,"defesa":12,"skills":[{"nome":"Mordida Tripla","emoji":"🐍","dano":24}]}},
            {"andar":4,"nome":"Fortaleza em Ruinas","emoji":"🏰","monstro":{"nome":"Golem de Pedra",  "emoji":"🗿","hp":220,"ataque":20,"defesa":25,"skills":[{"nome":"Soco de Pedra","emoji":"👊","dano":28}]}},
            {"andar":5,"nome":"Câmara Proibida",   "emoji":"🚪","monstro":{"nome":"Feiticeiro Renegado","emoji":"🧙","hp":200,"ataque":28,"defesa":10,"skills":[{"nome":"Feitico Negro","emoji":"🔮","dano":30}]}},
        ],
        "chefe":{"nome":"Senhor das Trevas",  "emoji":"🧛","hp":500,"ataque":35,"defesa":20,
                 "skills":[{"nome":"Drenar Alma","emoji":"🩸","dano":32},{"nome":"Nuvem de Morcegos","emoji":"🦇","dano":25},{"nome":"Hipnose","emoji":"👁️","dano":20}],
                 "loot_raro":("capa_trevas","Capa das Trevas","armadura","Raro","🧛","Defesa +12, esquiva +5%"),
                 "loot_epico":("espada_maldita","Espada Maldita","arma","Epico","⚔️","Ataque +18, drena HP")},
    },
    "D": {
        "nome":"Dungeon Rank D","emoji":"🟦","nivel_min":10,"cor":0x378ADD,
        "desc":"Perigo real. Venha preparado com pocoes.",
        "recompensa_andar":{"xp":100,"moedas":55},
        "recompensa_chefe":{"xp":500,"moedas":350},
        "andares": [
            {"andar":1,"nome":"Cripta Antiga",     "emoji":"⚰️","monstro":{"nome":"Lich Menor",     "emoji":"💀","hp":250,"ataque":30,"defesa":15,"skills":[{"nome":"Raio de Morte","emoji":"💀","dano":33}]}},
            {"andar":2,"nome":"Vulcão Ativo",      "emoji":"🌋","monstro":{"nome":"Elemental de Fogo","emoji":"🔥","hp":280,"ataque":35,"defesa":12,"skills":[{"nome":"Explosao","emoji":"💥","dano":38}]}},
            {"andar":3,"nome":"Abismo Gelado",     "emoji":"❄️","monstro":{"nome":"Yeti",             "emoji":"🦴","hp":320,"ataque":28,"defesa":28,"skills":[{"nome":"Rajada de Gelo","emoji":"❄️","dano":30}]}},
            {"andar":4,"nome":"Floresta Sangrenta","emoji":"🌹","monstro":{"nome":"Vampiro Anciao",   "emoji":"🧛","hp":350,"ataque":40,"defesa":20,"skills":[{"nome":"Drenar Sangue","emoji":"🩸","dano":42}]}},
            {"andar":5,"nome":"Torre do Caos",     "emoji":"🗼","monstro":{"nome":"Mago do Caos",    "emoji":"🌀","hp":380,"ataque":45,"defesa":15,"skills":[{"nome":"Explosao Arcana","emoji":"✨","dano":48}]}},
        ],
        "chefe":{"nome":"Hidra das Profundezas","emoji":"🐲","hp":900,"ataque":55,"defesa":30,
                 "skills":[{"nome":"Mordida Venenosa","emoji":"🐍","dano":50},{"nome":"Cauda","emoji":"🐲","dano":45},{"nome":"Regenerar","emoji":"💚","dano":0}],
                 "loot_raro":("escudo_hidra","Escudo da Hidra","armadura","Raro","🛡️","Defesa +20, imune a veneno"),
                 "loot_epico":("veneno_hidra","Veneno da Hidra","material","Epico","🧪","Material lendario de forja")},
    },
    "C": {
        "nome":"Dungeon Rank C","emoji":"🟨","nivel_min":20,"cor":0xE4AF3C,
        "desc":"Apenas guerreiros experientes sobrevivem aqui.",
        "recompensa_andar":{"xp":180,"moedas":100},
        "recompensa_chefe":{"xp":900,"moedas":600},
        "andares": [
            {"andar":1,"nome":"Cemitério Amaldicoado","emoji":"🪦","monstro":{"nome":"Banshee",        "emoji":"👻","hp":400,"ataque":50,"defesa":20,"skills":[{"nome":"Grito Mortal","emoji":"😱","dano":55}]}},
            {"andar":2,"nome":"Pântano Demoníaco",  "emoji":"😈","monstro":{"nome":"Demônio Menor",   "emoji":"😈","hp":450,"ataque":55,"defesa":25,"skills":[{"nome":"Garras do Inferno","emoji":"🔥","dano":60}]}},
            {"andar":3,"nome":"Caverna de Cristal", "emoji":"💎","monstro":{"nome":"Golem de Cristal", "emoji":"💎","hp":500,"ataque":48,"defesa":45,"skills":[{"nome":"Fragmento","emoji":"💎","dano":52}]}},
            {"andar":4,"nome":"Templo Profanado",   "emoji":"⛩️","monstro":{"nome":"Sacerdote Corrompido","emoji":"🙏","hp":480,"ataque":60,"defesa":28,"skills":[{"nome":"Maldicao Divina","emoji":"☠️","dano":65}]}},
            {"andar":5,"nome":"Salão do Rei Morto", "emoji":"👑","monstro":{"nome":"Cavaleiro Negro",  "emoji":"🏇","hp":600,"ataque":65,"defesa":40,"skills":[{"nome":"Golpe Sombrio","emoji":"⚔️","dano":70}]}},
        ],
        "chefe":{"nome":"Rei Lich","emoji":"💀","hp":1500,"ataque":80,"defesa":45,
                 "skills":[{"nome":"Colapso de Mana","emoji":"💀","dano":75},{"nome":"Exercito dos Mortos","emoji":"☠️","dano":60},{"nome":"Ressurreicao","emoji":"💚","dano":0}],
                 "loot_raro":("cetro_lich","Cetro do Lich","arma","Epico","💀","Ataque +25, +15% dano magico"),
                 "loot_epico":("coroa_lich","Coroa do Rei Lich","armadura","Lendario","👑","Defesa +30, imune a magia negra")},
    },
    "B": {
        "nome":"Dungeon Rank B","emoji":"🟧","nivel_min":30,"cor":0xD85A30,
        "desc":"Elite dos aventureiros. Recompensas extraordinarias.",
        "recompensa_andar":{"xp":300,"moedas":180},
        "recompensa_chefe":{"xp":1500,"moedas":1000},
        "andares": [
            {"andar":1,"nome":"Dimensao Proibida",  "emoji":"🌀","monstro":{"nome":"Criatura Dimensional","emoji":"👾","hp":700,"ataque":75,"defesa":40,"skills":[{"nome":"Distorcao","emoji":"🌀","dano":80}]}},
            {"andar":2,"nome":"Floresta Eterna",    "emoji":"🌿","monstro":{"nome":"Anciao da Floresta","emoji":"🌲","hp":800,"ataque":70,"defesa":60,"skills":[{"nome":"Raizes","emoji":"🌿","dano":75}]}},
            {"andar":3,"nome":"Oceano de Lava",     "emoji":"🌋","monstro":{"nome":"Titan de Fogo",     "emoji":"🔥","hp":900,"ataque":90,"defesa":50,"skills":[{"nome":"Erupcao","emoji":"🌋","dano":95}]}},
            {"andar":4,"nome":"Tempestade Arcana",  "emoji":"⚡","monstro":{"nome":"Elemental Arcano",  "emoji":"✨","hp":850,"ataque":85,"defesa":45,"skills":[{"nome":"Tempestade","emoji":"⚡","dano":90}]}},
            {"andar":5,"nome":"Trono das Sombras",  "emoji":"🖤","monstro":{"nome":"Assassino das Sombras","emoji":"🗡️","hp":950,"ataque":100,"defesa":55,"skills":[{"nome":"Golpe Fatal","emoji":"🗡️","dano":105}]}},
        ],
        "chefe":{"nome":"Titan Primordial","emoji":"🗿","hp":3000,"ataque":120,"defesa":70,
                 "skills":[{"nome":"Terremoto","emoji":"🌋","dano":110},{"nome":"Rugido Primordial","emoji":"😤","dano":90},{"nome":"Crush","emoji":"💥","dano":130}],
                 "loot_raro":("fragmento_titan","Fragmento do Titan","material","Epico","🗿","Material rarissimo"),
                 "loot_epico":("armadura_titan","Armadura do Titan","armadura","Lendario","🗿","Defesa +45, +20% HP max")},
    },
    "A": {
        "nome":"Dungeon Rank A","emoji":"🟥","nivel_min":40,"cor":0xE24B4A,
        "desc":"Apenas lendas entram aqui. Recompensas unicas.",
        "recompensa_andar":{"xp":500,"moedas":300},
        "recompensa_chefe":{"xp":2500,"moedas":2000},
        "andares": [
            {"andar":1,"nome":"Portal do Inferno",  "emoji":"🔴","monstro":{"nome":"Arquidemônio",    "emoji":"😈","hp":1200,"ataque":130,"defesa":70,"skills":[{"nome":"Chamas do Inferno","emoji":"🔥","dano":140}]}},
            {"andar":2,"nome":"Reino dos Mortos",   "emoji":"💀","monstro":{"nome":"Senhor dos Mortos","emoji":"💀","hp":1400,"ataque":120,"defesa":80,"skills":[{"nome":"Toque da Morte","emoji":"💀","dano":130}]}},
            {"andar":3,"nome":"Abismo Eterno",      "emoji":"🕳️","monstro":{"nome":"Leviatã",          "emoji":"🐉","hp":1600,"ataque":150,"defesa":75,"skills":[{"nome":"Devorar","emoji":"🌊","dano":160}]}},
            {"andar":4,"nome":"Fortaleza Celeste",  "emoji":"☁️","monstro":{"nome":"Anjo Caido",       "emoji":"👼","hp":1500,"ataque":145,"defesa":90,"skills":[{"nome":"Espadada Divina","emoji":"⚔️","dano":155}]}},
            {"andar":5,"nome":"Sala do Julgamento", "emoji":"⚖️","monstro":{"nome":"Juiz Eterno",      "emoji":"⚖️","hp":1800,"ataque":160,"defesa":85,"skills":[{"nome":"Sentenca","emoji":"⚖️","dano":170}]}},
        ],
        "chefe":{"nome":"Deus da Destruicao","emoji":"💥","hp":6000,"ataque":200,"defesa":100,
                 "skills":[{"nome":"Apocalipse","emoji":"💥","dano":190},{"nome":"Destrocar Realidade","emoji":"🌀","dano":170},{"nome":"Pulso Divino","emoji":"✨","dano":210}],
                 "loot_raro":("olho_deus","Olho do Deus","material","Lendario","👁️","Material divino rarissimo"),
                 "loot_epico":("skill_apocalipse","Apocalipse","skill_especial","Lendario","💥","Skill UNICA: dano massivo em area")},
    },
    "S": {
        "nome":"Dungeon Rank S","emoji":"⭐","nivel_min":50,"cor":0x7F77DD,
        "desc":"A dungeon mais perigosa. Recompensas UNICAS no servidor.",
        "recompensa_andar":{"xp":800,"moedas":500},
        "recompensa_chefe":{"xp":5000,"moedas":5000},
        "andares": [
            {"andar":1,"nome":"Vazio Absoluto",     "emoji":"🌌","monstro":{"nome":"Entidade do Vazio", "emoji":"🌌","hp":2000,"ataque":200,"defesa":120,"skills":[{"nome":"Nulificar","emoji":"🌌","dano":210}]}},
            {"andar":2,"nome":"Tempo Partido",      "emoji":"⏳","monstro":{"nome":"Guardiao do Tempo", "emoji":"⏳","hp":2200,"ataque":190,"defesa":140,"skills":[{"nome":"Paradoxo","emoji":"⏳","dano":200}]}},
            {"andar":3,"nome":"Realidade Distorcida","emoji":"🔮","monstro":{"nome":"Espelho do Caos",  "emoji":"🔮","hp":2500,"ataque":220,"defesa":130,"skills":[{"nome":"Reflexo","emoji":"🔮","dano":230}]}},
            {"andar":4,"nome":"Nucleo do Mundo",    "emoji":"🌍","monstro":{"nome":"Guardiao do Nucleo","emoji":"🌍","hp":2800,"ataque":240,"defesa":150,"skills":[{"nome":"Terremoto Total","emoji":"🌍","dano":250}]}},
            {"andar":5,"nome":"Portal da Eternidade","emoji":"🌟","monstro":{"nome":"Ser Eterno",       "emoji":"🌟","hp":3000,"ataque":260,"defesa":160,"skills":[{"nome":"Raio Eterno","emoji":"🌟","dano":270}]}},
        ],
        "chefe":{"nome":"O Criador","emoji":"🌟","hp":15000,"ataque":350,"defesa":200,
                 "skills":[{"nome":"Big Bang","emoji":"💥","dano":320},{"nome":"Singularidade","emoji":"⭐","dano":300},{"nome":"Recriar","emoji":"🌟","dano":0}],
                 "loot_raro":("titulo_conquistador","Titulo: Conquistador S","titulo","Lendario","🌟","Titulo exclusivo no servidor"),
                 "loot_epico":("classe_deus","Classe: Deus da Guerra","classe_especial","Lendario","⚔️","CLASSE UNICA — obtida apenas aqui")},
    },
}

# ─── DB ──────────────────────────────────────────────────────────

async def get_personagem(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM personagens WHERE user_id=?", (user_id,)) as c:
            return await c.fetchone()

async def get_skills_eq(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT skill_id FROM skills_equipadas WHERE user_id=? ORDER BY slot", (user_id,)) as c:
            return [r["skill_id"] for r in await c.fetchall()]

async def get_pocoes_inv(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM inventario WHERE user_id=? AND (item_id LIKE 'pocao%' OR item_id='elixir')",
            (user_id,)
        ) as c:
            return await c.fetchall()

async def remover_pocao(user_id, item_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id,quantidade FROM inventario WHERE user_id=? AND item_id=?", (user_id,item_id)) as c:
            row = await c.fetchone()
        if row:
            if row[1] > 1:
                await db.execute("UPDATE inventario SET quantidade=quantidade-1 WHERE id=?", (row[0],))
            else:
                await db.execute("DELETE FROM inventario WHERE id=?", (row[0],))
        await db.commit()

async def salvar_resultado_dungeon(user_id, hp_final, xp_total, moedas_total, classe_id, nivel):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT xp,nivel,hp_max,ataque,defesa FROM personagens WHERE user_id=?", (user_id,)) as c:
            p = await c.fetchone()
        if not p: return 0
        novo_xp = p["xp"] + xp_total
        nv = p["nivel"]
        levelups = 0
        needed = 100 + (nv-1)*50
        while novo_xp >= needed:
            novo_xp -= needed; nv += 1; needed = 100+(nv-1)*50; levelups += 1
        hp_max = p["hp_max"] + levelups*5
        atk = p["ataque"] + levelups*2
        dfs = p["defesa"] + levelups*1
        hp_f = max(1, min(hp_final, hp_max))
        await db.execute("""
            UPDATE personagens SET hp_atual=?,hp_max=?,xp=?,nivel=?,ataque=?,defesa=?,moedas=moedas+?,vitorias=vitorias+1
            WHERE user_id=?
        """, (hp_f, hp_max, novo_xp, nv, atk, dfs, moedas_total, user_id))
        for s in SKILLS_POR_CLASSE.get(classe_id, []):
            if s["nivel"] <= nv:
                await db.execute("INSERT OR IGNORE INTO skills_desbloqueadas(user_id,skill_id) VALUES(?,?)", (user_id,s["id"]))
        await db.commit()
        return levelups

async def add_item_dungeon(user_id, item):
    iid, nome, tipo, rar, emoji, desc = item
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id,quantidade FROM inventario WHERE user_id=? AND item_id=?", (user_id,iid)) as c:
            ex = await c.fetchone()
        if ex:
            await db.execute("UPDATE inventario SET quantidade=quantidade+1 WHERE id=?", (ex[0],))
        else:
            await db.execute("INSERT INTO inventario(user_id,item_id,nome,tipo,raridade,emoji,descricao) VALUES(?,?,?,?,?,?,?)",
                             (user_id,iid,nome,tipo,rar,emoji,desc))
        await db.commit()

# ─── HELPERS ─────────────────────────────────────────────────────

POCOES_DEF = {
    "pocao_hp_p":  {"nome":"Pocao de Cura P", "emoji":"🧪","tipo":"hp",  "valor":30},
    "pocao_hp_m":  {"nome":"Pocao de Cura M", "emoji":"💊","tipo":"hp",  "valor":60},
    "pocao_hp_g":  {"nome":"Pocao de Cura G", "emoji":"❤️","tipo":"hp",  "valor":120},
    "pocao_mana_p":{"nome":"Pocao de Mana P", "emoji":"🔵","tipo":"mana","valor":20},
    "pocao_mana_m":{"nome":"Pocao de Mana M", "emoji":"💙","tipo":"mana","valor":50},
    "elixir":      {"nome":"Elixir Supremo",  "emoji":"✨","tipo":"full","valor":999},
}

def calc_dano(atk, dfs, mult=1.0, crit=False):
    base = max(1, atk - dfs//2)
    d = int(base*mult) + random.randint(-2,3)
    return max(1, int(d*1.5) if crit else d)

def barra_hp(cur, mx):
    if mx <= 0: return "░░░░░░░░░░"
    p = max(0.0, cur/mx)
    f = int(p*10)
    c = "█" if p>0.6 else ("▓" if p>0.3 else "▒")
    return c*f + "░"*(10-f)

def get_skill(classe_id, skill_id):
    for s in SKILLS_POR_CLASSE.get(classe_id,[]):
        if s["id"] == skill_id: return s
    return None

def get_skills_jogador(p, ids):
    skills = [get_skill(p["classe_id"],sid) for sid in ids if get_skill(p["classe_id"],sid)]
    if not skills:
        cls = SKILLS_POR_CLASSE.get(p["classe_id"],[])
        skills = cls[:4] if cls else []
    return skills

# ─── VIEW DE BATALHA ─────────────────────────────────────────────

class DungeonBatalhaView(discord.ui.View):
    def __init__(self, user_id, skills, pocoes):
        super().__init__(timeout=None)
        self.user_id    = user_id
        self.acao       = None
        self.acao_feita = False
        self._pocoes    = list(pocoes) if pocoes else []

        for i, sk in enumerate(skills[:4]):
            mana_txt = f"({sk.get('mana',0)}💙)" if sk.get("mana",0)>0 else ""
            btn = discord.ui.Button(
                label=f"{sk['emoji']} {sk['nome']} {mana_txt}".strip(),
                style=discord.ButtonStyle.primary,
                row=0 if i<2 else 1,
                custom_id=f"sk_{i}"
            )
            btn.callback = self._sk(i)
            self.add_item(btn)

        mochila = discord.ui.Button(
            label=f"🎒 Mochila ({len(self._pocoes)})" if self._pocoes else "🎒 Mochila (vazia)",
            style=discord.ButtonStyle.secondary,
            disabled=not self._pocoes,
            row=2, custom_id="mochila"
        )
        mochila.callback = self._mochila
        self.add_item(mochila)

        fugir = discord.ui.Button(label="🏃 Fugir da Dungeon", style=discord.ButtonStyle.danger, row=2, custom_id="fugir")
        fugir.callback = self._fugir
        self.add_item(fugir)

    def _sk(self, idx):
        async def cb(inter: discord.Interaction):
            try: await inter.response.defer()
            except: pass
            if inter.user.id != self.user_id or self.acao_feita: return
            self.acao_feita = True
            self.acao = ("skill", idx)
            self.stop()
        return cb

    async def _mochila(self, inter: discord.Interaction):
        if inter.user.id != self.user_id or self.acao_feita:
            try: await inter.response.defer()
            except: pass
            return
        if not self._pocoes:
            try: await inter.response.send_message("Mochila vazia!", ephemeral=True)
            except: pass
            return
        opcoes = [discord.SelectOption(label=f"{p['emoji']} {p['nome']} (x{p['quantidade']})", value=p["item_id"]) for p in self._pocoes[:10]]
        sel = discord.ui.Select(placeholder="Usar pocao...", options=opcoes)
        parent = self
        async def usar(inter2: discord.Interaction):
            try: await inter2.response.defer()
            except: pass
            if inter2.user.id != parent.user_id or parent.acao_feita: return
            parent.acao_feita = True
            parent.acao = ("pocao", sel.values[0])
            parent.stop()
        sel.callback = usar
        v = discord.ui.View(timeout=20); v.add_item(sel)
        try: await inter.response.send_message("🎒 Escolha uma pocao:", view=v, ephemeral=True)
        except: pass

    async def _fugir(self, inter: discord.Interaction):
        try: await inter.response.defer()
        except: pass
        if inter.user.id != self.user_id or self.acao_feita: return
        self.acao_feita = True
        self.acao = ("fugir", None)
        self.stop()

# ─── ENGINE DE BATALHA DA DUNGEON ────────────────────────────────

async def batalha_dungeon(interaction, p, monstro, skills, hp_j, mana_j, hp_jmx, mana_jmx, msgs):
    """Batalha contra um andar/chefe. Retorna (hp_j, mana_j, vitoria)"""
    hp_m   = monstro["hp"]
    hp_mmx = monstro["hp"]
    turno  = 1
    efeitos = {}
    emoji_j = EMOJI_CLASSE.get(p["classe_id"],"⚔️")

    def status():
        return (
            f"{emoji_j} **{p['nome']}** ❤️`{barra_hp(hp_j,hp_jmx)}`{hp_j}/{hp_jmx} 💙{mana_j}\n"
            f"{monstro['emoji']} **{monstro['nome']}** ❤️`{barra_hp(hp_m,hp_mmx)}`{hp_m}/{hp_mmx}"
        )

    while hp_j > 0 and hp_m > 0:
        pocoes = await get_pocoes_inv(p["user_id"])
        view   = DungeonBatalhaView(p["user_id"], skills, pocoes)

        embed_vez = discord.Embed(
            title=f"⚔️ Turno {turno} — Sua vez!",
            description=status(),
            color=0x7F77DD
        )
        msg_vez = await interaction.followup.send(embed=embed_vez, view=view, wait=True)
        msgs.append(msg_vez)
        await view.wait()

        try: await msg_vez.edit(view=None)
        except: pass

        acao, val = view.acao or ("timeout", None)

        if acao == "fugir":
            return hp_j, mana_j, False, True  # hp, mana, vitoria, fugiu

        linha = ""
        cor   = 0x378ADD

        if acao == "pocao" and val:
            pd = POCOES_DEF.get(val)
            if pd:
                await remover_pocao(p["user_id"], val)
                if pd["tipo"] == "hp":
                    ganho = pd["valor"]; hp_j = min(hp_jmx, hp_j+ganho)
                    linha = f"🧪 **{pd['nome']}**: +{ganho} HP!"
                    cor = 0x1D9E75
                elif pd["tipo"] == "mana":
                    ganho = pd["valor"]; mana_j = min(mana_jmx, mana_j+ganho)
                    linha = f"🔵 **{pd['nome']}**: +{ganho} Mana!"
                elif pd["tipo"] == "full":
                    hp_j=hp_jmx; mana_j=mana_jmx
                    linha = "✨ **Elixir Supremo**: tudo restaurado!"
                    cor = 0xE4AF3C

        elif acao == "skill" and val is not None and val < len(skills):
            sk = skills[val]; efeito = sk.get("efeito",""); custo = sk.get("mana",0)
            if custo > mana_j:
                dano = calc_dano(p["ataque"], monstro["defesa"]); hp_m -= dano
                linha = f"⚔️ Sem mana! Ataque basico: **{dano} dano**"
                cor = 0x888780
            elif efeito == "cura":
                mana_j -= custo; cura = int(hp_jmx*0.30); hp_j = min(hp_jmx, hp_j+cura)
                linha = f"{sk['emoji']} **{sk['nome']}**: +{cura} HP!"
                cor = 0x1D9E75
            elif efeito in ("escudo","esquiva","armadura","reflexo"):
                mana_j -= custo; efeitos[efeito] = 2
                linha = f"{sk['emoji']} **{sk['nome']}**: efeito ativo!"
                cor = 0x7F77DD
            elif efeito == "dreno":
                mana_j -= custo; dano = calc_dano(p["ataque"],monstro["defesa"],sk["dano"])
                roubo = dano//2; hp_m -= dano; hp_j = min(hp_jmx, hp_j+roubo)
                linha = f"{sk['emoji']} **{sk['nome']}**: {dano} dano! +{roubo} HP drenado!"
                cor = 0x1D9E75
            else:
                mana_j -= custo; crit = random.random()<0.15
                dano = calc_dano(p["ataque"], monstro["defesa"], sk["dano"], crit)
                hp_m -= dano
                linha = f"{sk['emoji']} **{sk['nome']}**: **{dano} dano!**{'  💥 CRITICO!' if crit else ''}"
                cor = 0xD85A30 if crit else 0x378ADD
        else:
            dano = calc_dano(p["ataque"], monstro["defesa"]); hp_m -= dano
            linha = f"⚔️ Ataque basico: **{dano} dano**"; cor = 0x888780

        hp_m = max(0, hp_m)

        msg_a = await interaction.followup.send(
            embed=discord.Embed(title=f"{emoji_j} {p['nome']} agiu!", description=f"{linha}\n\n{status()}", color=cor),
            wait=True
        )
        msgs.append(msg_a)
        if hp_m <= 0: break

        await asyncio.sleep(1.0)

        # Monstro ataca
        sk_m = random.choice(monstro["skills"]); dano_m = calc_dano(monstro["ataque"], p["defesa"])
        if "esquiva" in efeitos and efeitos["esquiva"]>0:
            linha_m = f"{monstro['emoji']} **{monstro['nome']}** usou **{sk_m['nome']}**... mas voce **esquivou!** 💨"
            efeitos["esquiva"] -= 1; cor_m = 0x888780
        elif "escudo" in efeitos and efeitos["escudo"]>0:
            linha_m = f"{monstro['emoji']} **{monstro['nome']}** usou **{sk_m['nome']}**... mas o **escudo absorveu!** 💜"
            efeitos["escudo"] -= 1; cor_m = 0x7F77DD
        else:
            hp_j -= dano_m; hp_j = max(0, hp_j)
            linha_m = f"{monstro['emoji']} **{monstro['nome']}** usou **{sk_m['emoji']} {sk_m['nome']}**: **{dano_m} dano!**"
            cor_m = 0xE24B4A

        msg_m = await interaction.followup.send(
            embed=discord.Embed(title=f"{monstro['emoji']} {monstro['nome']} atacou!", description=f"{linha_m}\n\n{status()}", color=cor_m),
            wait=True
        )
        msgs.append(msg_m)
        mana_j = min(mana_jmx, mana_j+5)
        turno += 1
        await asyncio.sleep(0.8)

    vitoria = hp_m <= 0
    return hp_j, mana_j, vitoria, False

# ─── COMANDO PRINCIPAL: /dungeon ─────────────────────────────────

async def cmd_dungeon(interaction: discord.Interaction, rank: str):
    await interaction.response.defer()

    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True)
        return

    dungeon = RANKS.get(rank.upper())
    if not dungeon:
        await interaction.followup.send("Rank invalido!", ephemeral=True)
        return

    if p["nivel"] < dungeon["nivel_min"]:
        await interaction.followup.send(
            embed=discord.Embed(
                title="Nivel insuficiente!",
                description=f"A **{dungeon['nome']}** requer nivel **{dungeon['nivel_min']}**.\nSeu nivel: **{p['nivel']}**",
                color=0xE24B4A
            ),
            ephemeral=True
        )
        return

    # Pega skills
    ids_eq = await get_skills_eq(p["user_id"])
    skills = get_skills_jogador(p, ids_eq)
    if not skills:
        cls = SKILLS_POR_CLASSE.get(p["classe_id"], [])
        skills = cls[:4] if cls else []

    hp_j    = p["hp_atual"]
    hp_jmx  = p["hp_max"]
    mana_j  = p["mana_atual"] if "mana_atual" in p.keys() else 100
    mana_jmx= p["mana_max"]   if "mana_max"   in p.keys() else 100
    emoji_j = EMOJI_CLASSE.get(p["classe_id"],"⚔️")

    xp_total     = 0
    moedas_total = 0
    msgs_global  = []

    # ── Mensagem de entrada ──────────────────────────────────────
    embed_entrada = discord.Embed(
        title=f"{dungeon['emoji']} {dungeon['nome']}",
        description=(
            f"{dungeon['desc']}\n\n"
            f"**{emoji_j} {p['nome']}** entrou na dungeon!\n\n"
            f"❤️ HP: **{hp_j}/{hp_jmx}**\n"
            f"💙 Mana: **{mana_j}/{mana_jmx}**\n\n"
            f"🏆 **5 andares + 1 chefe final**\n"
            f"💀 Se morrer, perde tudo que ganhou aqui!"
        ),
        color=dungeon["cor"]
    )
    embed_entrada.set_footer(text=f"Nivel minimo: {dungeon['nivel_min']} • Seu nivel: {p['nivel']}")
    msg_ent = await interaction.followup.send(embed=embed_entrada, wait=True)
    msgs_global.append(msg_ent)
    await asyncio.sleep(2)

    # ── Loop dos andares ─────────────────────────────────────────
    for info_andar in dungeon["andares"]:
        andar  = info_andar["andar"]
        monstro = info_andar["monstro"]

        # Anuncia o andar
        embed_andar = discord.Embed(
            title=f"Andar {andar}/5 — {info_andar['emoji']} {info_andar['nome']}",
            description=(
                f"Um **{monstro['emoji']} {monstro['nome']}** bloqueia seu caminho!\n\n"
                f"❤️ HP inimigo: **{monstro['hp']}**\n"
                f"⚔️ Ataque: **{monstro['ataque']}** | 🛡️ Defesa: **{monstro['defesa']}**"
            ),
            color=dungeon["cor"]
        )
        msg_an = await interaction.followup.send(embed=embed_andar, wait=True)
        msgs_global.append(msg_an)
        await asyncio.sleep(1.5)

        msgs_batalha = []
        hp_j, mana_j, vitoria, fugiu = await batalha_dungeon(
            interaction, p, monstro, skills, hp_j, mana_j, hp_jmx, mana_jmx, msgs_batalha
        )
        msgs_global.extend(msgs_batalha)

        # Limpa mensagens do andar
        await asyncio.sleep(0.5)
        for m in msgs_batalha:
            try: await m.delete()
            except: pass

        if fugiu:
            # Limpa tudo e anuncia fuga
            for m in msgs_global:
                try: await m.delete()
                except: pass
            await interaction.followup.send(embed=discord.Embed(
                title="🏃 Fugiu da Dungeon!",
                description=f"**{p['nome']}** saiu da dungeon no andar {andar}.\nNenhuma recompensa foi obtida.",
                color=0x888780
            ))
            return

        if not vitoria:
            # Morreu — perde tudo
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE personagens SET hp_atual=10, derrotas=derrotas+1 WHERE user_id=?", (p["user_id"],))
                await db.commit()
            for m in msgs_global:
                try: await m.delete()
                except: pass
            await interaction.followup.send(embed=discord.Embed(
                title=f"💀 {p['nome']} foi derrotado no Andar {andar}!",
                description=(
                    f"Voce foi derrotado por **{monstro['emoji']} {monstro['nome']}** no andar {andar}.\n\n"
                    f"❌ **Perdeu todas as recompensas da dungeon!**\n"
                    f"Acordou na cidade com 10 HP."
                ),
                color=0xE24B4A
            ))
            return

        # Vitoria no andar — recompensa
        xp_andar     = dungeon["recompensa_andar"]["xp"]
        moedas_andar = dungeon["recompensa_andar"]["moedas"]
        xp_total     += xp_andar
        moedas_total += moedas_andar
        mana_j        = min(mana_jmx, mana_j + 15)  # recupera um pouco de mana

        msg_vit = await interaction.followup.send(embed=discord.Embed(
            title=f"✅ Andar {andar} concluido!",
            description=(
                f"**{monstro['emoji']} {monstro['nome']}** foi derrotado!\n\n"
                f"+{xp_andar} XP | +{moedas_andar} 🪙\n"
                f"❤️ HP restante: **{hp_j}/{hp_jmx}**\n\n"
                f"{'➡️ Proximo andar...' if andar < 5 else '⚔️ O CHEFE FINAL AGUARDA!'}"
            ),
            color=0x1D9E75
        ), wait=True)
        msgs_global.append(msg_vit)
        await asyncio.sleep(2)

    # ── CHEFE FINAL ──────────────────────────────────────────────
    chefe = dungeon["chefe"]

    embed_chefe = discord.Embed(
        title=f"👑 CHEFE FINAL: {chefe['emoji']} {chefe['nome']}",
        description=(
            f"O guardiao desta dungeon se revela!\n\n"
            f"❤️ HP: **{chefe['hp']}**\n"
            f"⚔️ Ataque: **{chefe['ataque']}** | 🛡️ Defesa: **{chefe['defesa']}**\n\n"
            f"⚠️ **Esta e sua ultima chance. Nao falhe!**"
        ),
        color=0xE24B4A
    )
    msg_ch = await interaction.followup.send(embed=embed_chefe, wait=True)
    msgs_global.append(msg_ch)
    await asyncio.sleep(2)

    msgs_chefe = []
    hp_j, mana_j, vitoria, fugiu = await batalha_dungeon(
        interaction, p, chefe, skills, hp_j, mana_j, hp_jmx, mana_jmx, msgs_chefe
    )
    msgs_global.extend(msgs_chefe)

    for m in msgs_chefe:
        try: await m.delete()
        except: pass

    if fugiu or not vitoria:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE personagens SET hp_atual=10, derrotas=derrotas+1 WHERE user_id=?", (p["user_id"],))
            await db.commit()
        for m in msgs_global:
            try: await m.delete()
            except: pass
        titulo = "🏃 Fugiu do chefe!" if fugiu else f"💀 Derrotado pelo chefe!"
        await interaction.followup.send(embed=discord.Embed(
            title=titulo,
            description=f"Tao perto... mas voce falhou.\n❌ **Todas as recompensas foram perdidas!**",
            color=0xE24B4A
        ))
        return

    # ── VITÓRIA TOTAL ────────────────────────────────────────────
    xp_total     += dungeon["recompensa_chefe"]["xp"]
    moedas_total += dungeon["recompensa_chefe"]["moedas"]

    # Loot
    loot_obtido = []
    # Loot raro garantido
    if chefe["loot_raro"]:
        await add_item_dungeon(p["user_id"], chefe["loot_raro"])
        loot_obtido.append(f"{chefe['loot_raro'][4]} **{chefe['loot_raro'][1]}** [{chefe['loot_raro'][3]}]")
    # Loot épico com 40% de chance
    if chefe["loot_epico"] and random.random() < 0.40:
        await add_item_dungeon(p["user_id"], chefe["loot_epico"])
        loot_obtido.append(f"{chefe['loot_epico'][4]} **{chefe['loot_epico'][1]}** [{chefe['loot_epico'][3]}] 🎉")

    lvlups = await salvar_resultado_dungeon(p["user_id"], hp_j, xp_total, moedas_total, p["classe_id"], p["nivel"])

    # Limpa todas as mensagens
    for m in msgs_global:
        try: await m.delete()
        except: pass

    loot_txt = "\n".join(loot_obtido) if loot_obtido else "Nenhum item"
    desc_final = (
        f"🏆 **{dungeon['nome']} COMPLETADA!**\n\n"
        f"**{emoji_j} {p['nome']}** derrotou **{chefe['emoji']} {chefe['nome']}**!\n\n"
        f"✨ **+{xp_total} XP total**\n"
        f"💰 **+{moedas_total} moedas**\n\n"
        f"🎁 **Itens obtidos:**\n{loot_txt}"
    )
    if lvlups:
        desc_final += f"\n\n🎉 **LEVEL UP! +{lvlups} nivel(is)!**"

    await interaction.followup.send(embed=discord.Embed(
        title=f"🏆 Dungeon Concluida!",
        description=desc_final,
        color=dungeon["cor"]
    ))
