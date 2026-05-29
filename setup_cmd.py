# setup_cmd.py — Sistema de setup completo do personagem
import discord
import aiosqlite
import random

DB_PATH = "rpg.db"

EMOJI_CLASSE = {
    "guerreiro":"🗡️","mago":"🔮","arqueiro":"🏹",
    "paladino":"⚡","necromante":"🌑","dracomante":"🐉","arcano":"✨"
}
COR_RAR = {
    "Comum":0x888780,"Incomum":0x1D9E75,"Raro":0x378ADD,
    "Epico":0x7F77DD,"Lendario":0xD85A30
}
EMOJI_RAR = {
    "Comum":"⬜","Incomum":"🟩","Raro":"🟦","Epico":"🟪","Lendario":"🟧"
}

# Afinidade arma/armadura por classe
AFINIDADE_ARMA = {
    "guerreiro":  ["espada_ferro","espada_prata","espada_orc","lanca_sagrada","garra_dragao"],
    "arqueiro":   ["arco_madeira","arco_elfico"],
    "mago":       ["cajado_pinho","cajado_magico","cajado_osso2"],
    "paladino":   ["lanca_sagrada","espada_prata","maca_sagrada"],
    "necromante": ["cajado_osso2","cajado_pinho"],
    "dracomante": ["garra_dragao","espada_ferro"],
    "arcano":     ["cajado_magico","cajado_pinho","orbe_arcano"],
}
AFINIDADE_ARMADURA = {
    "guerreiro":  ["armadura_plena","cota_malha","elmo_dragao","armadura_titan"],
    "arqueiro":   ["armadura_couro","cota_malha"],
    "mago":       ["armadura_couro"],
    "paladino":   ["armadura_plena","armadura_escama","cota_malha"],
    "necromante": ["capa_vampiro","armadura_couro"],
    "dracomante": ["armadura_escama","elmo_dragao"],
    "arcano":     ["armadura_couro","cota_malha"],
}

# Bônus numérico de cada arma/armadura
BONUS_ARMA = {
    "espada_ferro":  {"atk": 5,  "desc": "Espada de Ferro"},
    "arco_madeira":  {"atk": 4,  "desc": "Arco de Madeira"},
    "cajado_pinho":  {"atk": 4,  "desc": "Cajado de Pinho"},
    "maca_sagrada":  {"atk": 6,  "desc": "Maca Sagrada"},
    "orbe_arcano":   {"atk": 8,  "desc": "Orbe Arcano"},
    "garra_dragao":  {"atk": 12, "desc": "Garra de Dragao"},
    "espada_prata":  {"atk": 10, "desc": "Espada de Prata"},
    "arco_elfico":   {"atk": 14, "desc": "Arco Elfico"},
    "cajado_magico": {"atk": 15, "desc": "Cajado Magico"},
    "lanca_sagrada": {"atk": 18, "desc": "Lanca Sagrada"},
    "espada_orc":    {"atk": 16, "desc": "Espada Orc"},
    "cajado_osso2":  {"atk": 14, "desc": "Cajado Osseo+"},
    "machado_ferro": {"atk": 12, "desc": "Machado de Ferro"},
}
BONUS_ARMADURA = {
    "armadura_couro":  {"def": 5,  "desc": "Armadura de Couro"},
    "cota_malha":      {"def": 10, "desc": "Cota de Malha"},
    "armadura_plena":  {"def": 18, "desc": "Armadura Plena"},
    "armadura_escama": {"def": 25, "desc": "Armadura de Escama"},
    "elmo_dragao":     {"def": 32, "desc": "Elmo do Dragao"},
    "capa_vampiro":    {"def": 12, "desc": "Capa de Vampiro"},
    "armadura_titan":  {"def": 45, "desc": "Armadura do Titan"},
}

# Magias de suporte disponíveis
MAGIAS_SUPORTE = {
    "cura_universal":    {"nome": "Cura Universal",    "emoji": "💗", "raridade": "Incomum", "desc": "Restaura 50% HP em batalha",             "mana": 40},
    "bencao_divina":     {"nome": "Bencao Divina",     "emoji": "🙏", "raridade": "Incomum", "desc": "+20% todos os stats por 3 turnos",       "mana": 30},
    "escudo_magico":     {"nome": "Escudo Magico",     "emoji": "🛡️", "raridade": "Raro",    "desc": "Absorve o proximo ataque recebido",      "mana": 35},
    "frenesi":           {"nome": "Frenesi",           "emoji": "🔥", "raridade": "Raro",    "desc": "+50% ATK por 2 turnos",                  "mana": 35},
    "muralha":           {"nome": "Muralha",           "emoji": "🪨", "raridade": "Epico",   "desc": "Bloqueia os proximos 3 ataques",          "mana": 50},
    "ressurreicao_sup":  {"nome": "Ressurreicao",      "emoji": "✝️", "raridade": "Epico",   "desc": "Volta com 50% HP se morrer (uso unico)", "mana": 80},
}

# Skills do sistema antigo (fallback)
SKILLS_POR_CLASSE = {
    "guerreiro": [
        {"id":"golpe_basico","nome":"Golpe Basico","nivel":1,"emoji":"⚔️","mana":0,"dano_mult":1.0,"desc":"Ataque simples"},
        {"id":"escudo","nome":"Escudo","nivel":5,"emoji":"🛡️","mana":10,"dano_mult":0,"desc":"Defesa +50%","efeito":"defesa"},
        {"id":"golpe_brutal","nome":"Golpe Brutal","nivel":10,"emoji":"💥","mana":20,"dano_mult":2.0,"desc":"Dano dobrado"},
        {"id":"furia","nome":"Furia","nivel":35,"emoji":"🔥","mana":30,"dano_mult":1.5,"desc":"ULTIMATE"},
    ],
    "mago": [
        {"id":"bola_fogo","nome":"Bola de Fogo","nivel":1,"emoji":"🔥","mana":15,"dano_mult":1.3,"desc":"Dano magico"},
        {"id":"escudo_arcano","nome":"Escudo Arcano","nivel":5,"emoji":"💜","mana":20,"dano_mult":0,"desc":"Absorve 1 ataque","efeito":"escudo"},
        {"id":"raio","nome":"Raio","nivel":10,"emoji":"⚡","mana":25,"dano_mult":1.6,"desc":"Dano alto"},
        {"id":"sobrecarga","nome":"Sobrecarga","nivel":35,"emoji":"✨","mana":50,"dano_mult":3.0,"desc":"ULTIMATE"},
    ],
    "arqueiro": [
        {"id":"tiro_preciso","nome":"Tiro Preciso","nivel":1,"emoji":"🎯","mana":0,"dano_mult":1.0,"desc":"+30% critico"},
        {"id":"esquiva","nome":"Esquiva","nivel":5,"emoji":"💨","mana":15,"dano_mult":0,"desc":"Evita 1 ataque","efeito":"esquiva"},
        {"id":"tiro_multiplo","nome":"Tiro Multiplo","nivel":10,"emoji":"🏹","mana":20,"dano_mult":0.6,"desc":"2 ataques"},
        {"id":"chuva_flechas","nome":"Chuva Flechas","nivel":35,"emoji":"☄️","mana":40,"dano_mult":0.4,"desc":"ULTIMATE"},
    ],
    "paladino": [
        {"id":"golpe_sagrado","nome":"Golpe Sagrado","nivel":1,"emoji":"⚡","mana":10,"dano_mult":1.2,"desc":"Fisico+magico"},
        {"id":"cura","nome":"Cura","nivel":5,"emoji":"💚","mana":25,"dano_mult":0,"desc":"Recupera 30% HP","efeito":"cura"},
        {"id":"aura_sagrada","nome":"Aura Sagrada","nivel":10,"emoji":"🌟","mana":30,"dano_mult":0,"desc":"+stats","efeito":"buff_all"},
        {"id":"juizo_final","nome":"Juizo Final","nivel":35,"emoji":"☀️","mana":50,"dano_mult":2.5,"desc":"ULTIMATE"},
    ],
    "necromante": [
        {"id":"drenar_vida","nome":"Drenar Vida","nivel":1,"emoji":"🌑","mana":10,"dano_mult":1.1,"desc":"Rouba HP","efeito":"dreno"},
        {"id":"invocar_morto","nome":"Invocar Morto","nivel":8,"emoji":"💀","mana":20,"dano_mult":0.8,"desc":"Esqueleto ataca"},
        {"id":"maldicao","nome":"Maldicao","nivel":15,"emoji":"🩸","mana":15,"dano_mult":0.7,"desc":"Veneno"},
        {"id":"exercito","nome":"Exercito Morto","nivel":35,"emoji":"☠️","mana":50,"dano_mult":2.0,"desc":"ULTIMATE"},
    ],
    "dracomante": [
        {"id":"baforada","nome":"Baforada","nivel":1,"emoji":"🔥","mana":15,"dano_mult":1.4,"desc":"Fogo continuo"},
        {"id":"escamas","nome":"Escamas","nivel":10,"emoji":"🐉","mana":20,"dano_mult":0,"desc":"-30% dano","efeito":"armadura"},
        {"id":"forma_menor","nome":"Forma Menor","nivel":20,"emoji":"🌋","mana":35,"dano_mult":0,"desc":"+30% stats","efeito":"buff_all"},
        {"id":"dragao_eterno","nome":"Dragao Eterno","nivel":42,"emoji":"💎","mana":60,"dano_mult":3.5,"desc":"ULTIMATE"},
    ],
    "arcano": [
        {"id":"faisca","nome":"Faisca Arcana","nivel":1,"emoji":"✨","mana":10,"dano_mult":1.2,"desc":"Arcano puro"},
        {"id":"campo_forca","nome":"Campo de Forca","nivel":5,"emoji":"🔮","mana":20,"dano_mult":0,"desc":"Reflete 20%","efeito":"reflexo"},
        {"id":"distorcao","nome":"Distorcao","nivel":10,"emoji":"🌀","mana":15,"dano_mult":0.5,"desc":"Confunde"},
        {"id":"singularidade","nome":"Singularidade","nivel":35,"emoji":"⭐","mana":60,"dano_mult":4.0,"desc":"ULTIMATE"},
    ],
}

# ─── DB HELPERS ──────────────────────────────────────────────────

async def get_personagem(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM personagens WHERE user_id=?", (user_id,)) as c:
            return await c.fetchone()

async def get_skills_eq(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT skill_id FROM skills_equipadas WHERE user_id=? ORDER BY slot", (user_id,)
        ) as c:
            return [r["skill_id"] for r in await c.fetchall()]

async def get_skills_desbloq(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT skill_id FROM skills_desbloqueadas WHERE user_id=?", (user_id,)
        ) as c:
            return [r["skill_id"] for r in await c.fetchall()]

async def get_magia_suporte(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT skill_id FROM skills_equipadas WHERE user_id=? AND slot=99", (user_id,)
        ) as c:
            row = await c.fetchone()
            return row["skill_id"] if row else None

async def get_inv_tipo(user_id, tipo):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM inventario WHERE user_id=? AND tipo=?", (user_id, tipo)
        ) as c:
            return await c.fetchall()

async def get_equipado(user_id, tipo):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM inventario WHERE user_id=? AND tipo=? AND equipado=1 LIMIT 1",
            (user_id, tipo)
        ) as c:
            return await c.fetchone()

async def get_magias_suporte_inv(user_id):
    """Retorna magias de suporte que o jogador possui (no inventario ou desbloqueadas)"""
    desbloq = await get_skills_desbloq(user_id)
    return {sid: info for sid, info in MAGIAS_SUPORTE.items() if sid in desbloq}

async def salvar_skills(user_id, skill_ids):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM skills_equipadas WHERE user_id=? AND slot!=99", (user_id,)
        )
        for slot, sid in enumerate(skill_ids[:4]):
            await db.execute(
                "INSERT OR REPLACE INTO skills_equipadas(user_id,skill_id,slot) VALUES(?,?,?)",
                (user_id, sid, slot)
            )
        await db.commit()

async def salvar_magia_suporte(user_id, magia_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM skills_equipadas WHERE user_id=? AND slot=99", (user_id,)
        )
        if magia_id and magia_id != "none":
            await db.execute(
                "INSERT OR REPLACE INTO skills_equipadas(user_id,skill_id,slot) VALUES(?,?,99)",
                (user_id, magia_id)
            )
        await db.commit()

async def salvar_equip(user_id, tipo, item_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE inventario SET equipado=0 WHERE user_id=? AND tipo=?", (user_id, tipo)
        )
        if item_id and item_id != "none":
            await db.execute(
                "UPDATE inventario SET equipado=1 WHERE user_id=? AND item_id=?",
                (user_id, item_id)
            )
        await db.commit()

# ─── CÁLCULO DE STATS ────────────────────────────────────────────

def calcular_stats_setup(p, arma, armadura, classe_id):
    atk_base = p["ataque"]
    dfs_base = p["defesa"]

    bonus_atk_num = 0
    bonus_dfs_num = 0
    bonus_atk_pct = 1.0
    bonus_dfs_pct = 1.0

    arma_compat    = None
    armadura_compat = None

    if arma:
        aid = arma["item_id"]
        bonus_atk_num = BONUS_ARMA.get(aid, {}).get("atk", 0)
        if aid in AFINIDADE_ARMA.get(classe_id, []):
            bonus_atk_pct  = 1.15
            arma_compat    = True
        else:
            bonus_atk_pct  = 0.85
            arma_compat    = False

    if armadura:
        armid = armadura["item_id"]
        bonus_dfs_num = BONUS_ARMADURA.get(armid, {}).get("def", 0)
        if armid in AFINIDADE_ARMADURA.get(classe_id, []):
            bonus_dfs_pct   = 1.10
            armadura_compat = True
        else:
            bonus_dfs_pct   = 0.90
            armadura_compat = False

    atk_final = int((atk_base + bonus_atk_num) * bonus_atk_pct)
    dfs_final = int((dfs_base + bonus_dfs_num) * bonus_dfs_pct)

    return {
        "atk_base":      atk_base,
        "dfs_base":      dfs_base,
        "bonus_atk_num": bonus_atk_num,
        "bonus_dfs_num": bonus_dfs_num,
        "bonus_atk_pct": bonus_atk_pct,
        "bonus_dfs_pct": bonus_dfs_pct,
        "atk_final":     atk_final,
        "dfs_final":     dfs_final,
        "arma_compat":   arma_compat,
        "armadura_compat": armadura_compat,
    }

def avaliar_setup(skills_eq, arma_compat, armadura_compat):
    nota = 0
    if len(skills_eq) == 4: nota += 2
    elif len(skills_eq) >= 2: nota += 1
    if arma_compat is True:  nota += 2
    elif arma_compat is None: nota += 1
    if armadura_compat is True:  nota += 2
    elif armadura_compat is None: nota += 1

    ratings = {
        6: ("⭐⭐⭐", "Setup perfeito! Voce esta pronto para qualquer batalha."),
        5: ("⭐⭐",   "Muito bom! Pequenos ajustes podem melhorar ainda mais."),
        4: ("⭐⭐",   "Bom setup! Tente equipar mais skills ou melhorar o equipamento."),
        3: ("⭐",    "Razoavel. Verifique a afinidade dos equipamentos com sua classe."),
        2: ("⚠️",   "Setup fraco. Troque arma ou armadura por itens compativeis."),
        1: ("❌",    "Setup muito fraco. Equipamentos incompativeis penalizam seus stats."),
        0: ("❌",    "Sem setup configurado. Use os menus abaixo para equipar tudo."),
    }
    return ratings.get(nota, ratings[0])

# ─── BUILD EMBED ─────────────────────────────────────────────────

def build_embed_setup(p, skills_eq_ids, skills_desbloq_ids, arma, armadura,
                      magia_sup_id, magias_inv, stats):
    emoji_j  = EMOJI_CLASSE.get(p["classe_id"], "⚔️")
    classe_s = SKILLS_POR_CLASSE.get(p["classe_id"], [])

    cor = COR_RAR.get(p["raridade"], 0x7F77DD)
    embed = discord.Embed(
        title=f"{emoji_j} Setup de {p['nome']}",
        color=cor
    )

    # ── Skills equipadas ──────────────────────────────────────
    sk_txt = ""
    for i, sid in enumerate(skills_eq_ids):
        sk = next((s for s in classe_s if s["id"] == sid), None)
        if sk:
            rar_e = EMOJI_RAR.get("Comum", "⬜")
            mana_t = f" 💙{sk['mana']}" if sk["mana"] > 0 else ""
            sk_txt += f"`{i+1}` {sk['emoji']} **{sk['nome']}**{mana_t} — *{sk['desc']}*\n"
    if not sk_txt:
        sk_txt = "*Nenhuma skill equipada. Use o menu Skills abaixo.*"
    embed.add_field(name=f"⚡ Skills ({len(skills_eq_ids)}/4)", value=sk_txt, inline=False)

    # ── Arma ─────────────────────────────────────────────────
    if arma:
        compat  = "✅" if stats["arma_compat"] else "❌"
        pct_txt = "+15%" if stats["arma_compat"] else "-15%"
        num_txt = f"+{stats['bonus_atk_num']}" if stats["bonus_atk_num"] > 0 else "0"
        arma_txt = (
            f"{compat} {arma['emoji']} **{arma['nome']}**\n"
            f"ATK base {stats['atk_base']} + {num_txt} (arma) × {pct_txt} = **{stats['atk_final']} ATK final**"
        )
    else:
        arma_txt = "*Sem arma equipada.*\nATK final = **{stats['atk_base']}** (sem bonus)"
        arma_txt = f"*Sem arma equipada.*\nATK final = **{stats['atk_base']}** (sem bonus)"
    embed.add_field(name="⚔️ Arma", value=arma_txt, inline=True)

    # ── Armadura ─────────────────────────────────────────────
    if armadura:
        compat  = "✅" if stats["armadura_compat"] else "❌"
        pct_txt = "+10%" if stats["armadura_compat"] else "-10%"
        num_txt = f"+{stats['bonus_dfs_num']}" if stats["bonus_dfs_num"] > 0 else "0"
        arm_txt = (
            f"{compat} {armadura['emoji']} **{armadura['nome']}**\n"
            f"DEF base {stats['dfs_base']} + {num_txt} (arm) × {pct_txt} = **{stats['dfs_final']} DEF final**"
        )
    else:
        arm_txt = f"*Sem armadura equipada.*\nDEF final = **{stats['dfs_base']}** (sem bonus)"
    embed.add_field(name="🛡️ Armadura", value=arm_txt, inline=True)

    # ── Magia de suporte ──────────────────────────────────────
    if magia_sup_id and magia_sup_id in MAGIAS_SUPORTE:
        ms = MAGIAS_SUPORTE[magia_sup_id]
        rar_e = EMOJI_RAR.get(ms["raridade"], "⬜")
        ms_txt = f"{rar_e} {ms['emoji']} **{ms['nome']}** 💙{ms['mana']}\n*{ms['desc']}*"
    else:
        ms_txt = "*Nenhuma magia de suporte equipada.*"
    embed.add_field(name="🔮 Magia de Suporte", value=ms_txt, inline=False)

    # ── Stats finais ──────────────────────────────────────────
    stats_txt = (
        f"❤️ HP: **{p['hp_atual']}/{p['hp_max']}** | "
        f"⚔️ ATK: **{stats['atk_final']}** | "
        f"🛡️ DEF: **{stats['dfs_final']}** | "
        f"💙 Mana: **{p['mana_atual'] if 'mana_atual' in p.keys() else 100}/{p['mana_max'] if 'mana_max' in p.keys() else 100}**"
    )
    embed.add_field(name="📊 Stats finais", value=stats_txt, inline=False)

    # ── Avaliação ─────────────────────────────────────────────
    estrelas, msg = avaliar_setup(
        skills_eq_ids,
        stats["arma_compat"],
        stats["armadura_compat"]
    )
    embed.add_field(name=f"Avaliacao: {estrelas}", value=msg, inline=False)

    embed.set_footer(text=f"Nivel {p['nivel']} • Use os menus abaixo para ajustar seu setup")
    return embed

# ─── VIEW PRINCIPAL ──────────────────────────────────────────────

class SetupView(discord.ui.View):
    def __init__(self, user_id, p, skills_eq, skills_desbloq,
                 arma, armadura, magia_sup_id, magias_inv,
                 armas_inv, armaduras_inv):
        super().__init__(timeout=180)
        self.user_id      = user_id
        self.p            = p
        self.skills_eq    = list(skills_eq)
        self.skills_desbloq = list(skills_desbloq)
        self.arma         = arma
        self.armadura     = armadura
        self.magia_sup_id = magia_sup_id
        self.magias_inv   = magias_inv
        self.armas_inv    = list(armas_inv)
        self.armaduras_inv = list(armaduras_inv)
        self.msg          = None  # referencia a mensagem para editar

        self._montar_menus()

    def _montar_menus(self):
        self.clear_items()
        classe_s = SKILLS_POR_CLASSE.get(self.p["classe_id"], [])

        # ── Dropdown de Skills (TODAS desbloqueadas) ──────────
        # Coleta todas as skills do jogo em um dict
        todas_skills_flat = {}
        for cid, lista in SKILLS_POR_CLASSE.items():
            for sk in lista:
                todas_skills_flat[sk["id"]] = dict(sk, classe_origem=cid)

        opcoes_sk = []
        for sid in self.skills_desbloq:
            sk = todas_skills_flat.get(sid)
            if not sk:
                continue
            mana_t  = f" 💙{sk['mana']}" if sk.get("mana", 0) > 0 else ""
            classe_orig = sk.get("classe_origem", self.p["classe_id"])
            compat  = "✅" if classe_orig == self.p["classe_id"] else "⚠️"
            opcoes_sk.append(discord.SelectOption(
                label=f"{compat} {sk['emoji']} {sk['nome']}{mana_t}",
                value=sid,
                description=sk["desc"][:50],
                default=sid in self.skills_eq
            ))

        if opcoes_sk:
            sel_sk = discord.ui.Select(
                placeholder="⚡ Selecione ate 4 skills...",
                min_values=0,
                max_values=min(4, len(opcoes_sk)),
                options=opcoes_sk[:25],
                row=0
            )
            sel_sk.callback = self._on_skills
            self.add_item(sel_sk)

        # ── Dropdown de Arma ─────────────────────────────────
        opcoes_arma = [discord.SelectOption(
            label="Sem arma",
            value="none",
            description="Remover arma equipada",
            default=self.arma is None
        )]
        for a in self.armas_inv:
            aid    = a["item_id"]
            compat = "✅" if aid in AFINIDADE_ARMA.get(self.p["classe_id"], []) else "❌"
            bonus  = BONUS_ARMA.get(aid, {})
            num    = bonus.get("atk", 0)
            pct    = "+15%" if compat == "✅" else "-15%"
            opcoes_arma.append(discord.SelectOption(
                label=f"{compat} {a['emoji']} {a['nome']}",
                value=aid,
                description=f"ATK +{num} | {pct} | [{a['raridade']}]",
                default=self.arma is not None and self.arma["item_id"] == aid
            ))

        if len(opcoes_arma) > 1:
            sel_arma = discord.ui.Select(
                placeholder="⚔️ Selecione uma arma...",
                options=opcoes_arma[:25],
                row=1
            )
            sel_arma.callback = self._on_arma
            self.add_item(sel_arma)

        # ── Dropdown de Armadura ──────────────────────────────
        opcoes_arm = [discord.SelectOption(
            label="Sem armadura",
            value="none",
            description="Remover armadura equipada",
            default=self.armadura is None
        )]
        for a in self.armaduras_inv:
            armid  = a["item_id"]
            compat = "✅" if armid in AFINIDADE_ARMADURA.get(self.p["classe_id"], []) else "❌"
            bonus  = BONUS_ARMADURA.get(armid, {})
            num    = bonus.get("def", 0)
            pct    = "+10%" if compat == "✅" else "-10%"
            opcoes_arm.append(discord.SelectOption(
                label=f"{compat} {a['emoji']} {a['nome']}",
                value=armid,
                description=f"DEF +{num} | {pct} | [{a['raridade']}]",
                default=self.armadura is not None and self.armadura["item_id"] == armid
            ))

        if len(opcoes_arm) > 1:
            sel_arm = discord.ui.Select(
                placeholder="🛡️ Selecione uma armadura...",
                options=opcoes_arm[:25],
                row=2
            )
            sel_arm.callback = self._on_armadura
            self.add_item(sel_arm)

        # ── Dropdown de Magia de Suporte ──────────────────────
        opcoes_ms = [discord.SelectOption(
            label="Sem magia de suporte",
            value="none",
            description="Remover magia equipada",
            default=self.magia_sup_id is None
        )]
        for mid, ms in self.magias_inv.items():
            rar_e = EMOJI_RAR.get(ms["raridade"], "⬜")
            opcoes_ms.append(discord.SelectOption(
                label=f"{rar_e} {ms['emoji']} {ms['nome']} 💙{ms['mana']}",
                value=mid,
                description=ms["desc"][:50],
                default=self.magia_sup_id == mid
            ))

        if len(opcoes_ms) > 1:
            sel_ms = discord.ui.Select(
                placeholder="🔮 Selecione magia de suporte...",
                options=opcoes_ms[:25],
                row=3
            )
            sel_ms.callback = self._on_magia
            self.add_item(sel_ms)

    def _calcular_e_buildar(self):
        stats = calcular_stats_setup(
            self.p, self.arma, self.armadura, self.p["classe_id"]
        )
        magias = self.magias_inv
        return build_embed_setup(
            self.p, self.skills_eq, self.skills_desbloq,
            self.arma, self.armadura, self.magia_sup_id, magias, stats
        )

    async def _atualizar(self, inter):
        try:
            await inter.response.defer()
        except Exception:
            pass
        self._montar_menus()
        if self.msg:
            try:
                await self.msg.edit(embed=self._calcular_e_buildar(), view=self)
            except Exception:
                pass

    async def _on_skills(self, inter: discord.Interaction):
        if inter.user.id != self.user_id:
            await inter.response.send_message("Nao e seu setup!", ephemeral=True)
            return
        self.skills_eq = inter.data["values"][:4]
        await salvar_skills(self.user_id, self.skills_eq)
        await self._atualizar(inter)

    async def _on_arma(self, inter: discord.Interaction):
        if inter.user.id != self.user_id:
            await inter.response.send_message("Nao e seu setup!", ephemeral=True)
            return
        val = inter.data["values"][0]
        await salvar_equip(self.user_id, "arma", val)
        if val == "none":
            self.arma = None
        else:
            self.arma = next(
                (a for a in self.armas_inv if a["item_id"] == val), None
            )
        await self._atualizar(inter)

    async def _on_armadura(self, inter: discord.Interaction):
        if inter.user.id != self.user_id:
            await inter.response.send_message("Nao e seu setup!", ephemeral=True)
            return
        val = inter.data["values"][0]
        await salvar_equip(self.user_id, "armadura", val)
        if val == "none":
            self.armadura = None
        else:
            self.armadura = next(
                (a for a in self.armaduras_inv if a["item_id"] == val), None
            )
        await self._atualizar(inter)

    async def _on_magia(self, inter: discord.Interaction):
        if inter.user.id != self.user_id:
            await inter.response.send_message("Nao e seu setup!", ephemeral=True)
            return
        val = inter.data["values"][0]
        self.magia_sup_id = None if val == "none" else val
        await salvar_magia_suporte(self.user_id, val)
        await self._atualizar(inter)

    async def on_timeout(self):
        if self.msg:
            try:
                await self.msg.edit(view=None)
            except Exception:
                pass

# ─── FUNÇÃO PRINCIPAL ─────────────────────────────────────────────

async def cmd_setup(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send(
            "Crie seu personagem primeiro com `/criar_personagem`!", ephemeral=True
        )
        return

    skills_eq      = await get_skills_eq(interaction.user.id)
    skills_desbloq = await get_skills_desbloq(interaction.user.id)
    arma           = await get_equipado(interaction.user.id, "arma")
    armadura       = await get_equipado(interaction.user.id, "armadura")
    magia_sup_id   = await get_magia_suporte(interaction.user.id)
    magias_inv     = await get_magias_suporte_inv(interaction.user.id)
    armas_inv      = await get_inv_tipo(interaction.user.id, "arma")
    armaduras_inv  = await get_inv_tipo(interaction.user.id, "armadura")

    # Remove magia de suporte da lista de skills normais
    skills_eq_filtradas = [s for s in skills_eq if s != magia_sup_id]

    stats = calcular_stats_setup(p, arma, armadura, p["classe_id"])
    embed = build_embed_setup(
        p, skills_eq_filtradas, skills_desbloq,
        arma, armadura, magia_sup_id, magias_inv, stats
    )

    view = SetupView(
        user_id       = interaction.user.id,
        p             = p,
        skills_eq     = skills_eq_filtradas,
        skills_desbloq= skills_desbloq,
        arma          = arma,
        armadura      = armadura,
        magia_sup_id  = magia_sup_id,
        magias_inv    = magias_inv,
        armas_inv     = armas_inv,
        armaduras_inv = armaduras_inv,
    )

    msg = await interaction.followup.send(embed=embed, view=view, ephemeral=True, wait=True)
    view.msg = msg