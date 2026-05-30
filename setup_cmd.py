# setup_cmd.py — PostgreSQL version
import discord
import asyncio
from db import get_pool
from imagens import IMG_SETUP
from catalogo import get_rank, calcular_mana_max, get_armas_classe, get_armaduras_classe, SKILLS_COMPLETAS as SKILLS_COMPLETAS_CAT

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
# Bonus gerados automaticamente do catalogo
from catalogo import get_bonus_arma as _get_bonus_arma, get_bonus_armadura as _get_bonus_armadura, ARMAS_POR_CLASSE as _ARMAS, ARMADURAS_POR_CLASSE as _ARMS

BONUS_ARMA = {}
for _cls, _itens in _ARMAS.items():
    for _it in _itens:
        BONUS_ARMA[_it["id"]] = {"atk": _it["atk_bonus"]}

BONUS_ARMADURA = {}
for _cls, _itens in _ARMS.items():
    for _it in _itens:
        BONUS_ARMADURA[_it["id"]] = {"def": _it["def_bonus"]}
MAGIAS_SUPORTE = {
    "cura_universal":   {"nome":"Cura Universal",   "emoji":"💗","raridade":"Incomum","desc":"Restaura 50% HP em batalha",             "mana":40},
    "bencao_divina":    {"nome":"Bencao Divina",    "emoji":"🙏","raridade":"Incomum","desc":"+20% todos os stats por 3 turnos",       "mana":30},
    "escudo_magico":    {"nome":"Escudo Magico",    "emoji":"🛡️","raridade":"Raro",   "desc":"Absorve o proximo ataque recebido",      "mana":35},
    "frenesi":          {"nome":"Frenesi",          "emoji":"🔥","raridade":"Raro",   "desc":"+50% ATK por 2 turnos",                  "mana":35},
    "muralha":          {"nome":"Muralha",          "emoji":"🪨","raridade":"Epico",  "desc":"Bloqueia os proximos 3 ataques",          "mana":50},
    "ressurreicao_sup": {"nome":"Ressurreicao",     "emoji":"✝️","raridade":"Epico",  "desc":"Volta com 50% HP se morrer (uso unico)", "mana":80},
}
SKILLS_POR_CLASSE = {
    "guerreiro": [
        {"id":"golpe_basico","nome":"Golpe Basico","nivel":1,"emoji":"⚔️","mana":0,"dano_mult":1.0,"desc":"Ataque simples"},
        {"id":"escudo","nome":"Escudo","nivel":5,"emoji":"🛡️","mana":10,"dano_mult":0,"desc":"Defesa +50%"},
        {"id":"golpe_brutal","nome":"Golpe Brutal","nivel":10,"emoji":"💥","mana":20,"dano_mult":2.0,"desc":"Dano dobrado"},
        {"id":"furia","nome":"Furia","nivel":35,"emoji":"🔥","mana":30,"dano_mult":1.5,"desc":"ULTIMATE"},
    ],
    "mago": [
        {"id":"bola_fogo","nome":"Bola de Fogo","nivel":1,"emoji":"🔥","mana":15,"dano_mult":1.3,"desc":"Dano magico"},
        {"id":"escudo_arcano","nome":"Escudo Arcano","nivel":5,"emoji":"💜","mana":20,"dano_mult":0,"desc":"Absorve 1 ataque"},
        {"id":"raio","nome":"Raio","nivel":10,"emoji":"⚡","mana":25,"dano_mult":1.6,"desc":"Dano alto"},
        {"id":"sobrecarga","nome":"Sobrecarga","nivel":35,"emoji":"✨","mana":50,"dano_mult":3.0,"desc":"ULTIMATE"},
    ],
    "arqueiro": [
        {"id":"tiro_preciso","nome":"Tiro Preciso","nivel":1,"emoji":"🎯","mana":0,"dano_mult":1.0,"desc":"+30% critico"},
        {"id":"esquiva","nome":"Esquiva","nivel":5,"emoji":"💨","mana":15,"dano_mult":0,"desc":"Evita 1 ataque"},
        {"id":"tiro_multiplo","nome":"Tiro Multiplo","nivel":10,"emoji":"🏹","mana":20,"dano_mult":0.6,"desc":"2 ataques"},
        {"id":"chuva_flechas","nome":"Chuva Flechas","nivel":35,"emoji":"☄️","mana":40,"dano_mult":0.4,"desc":"ULTIMATE"},
    ],
    "paladino": [
        {"id":"golpe_sagrado","nome":"Golpe Sagrado","nivel":1,"emoji":"⚡","mana":10,"dano_mult":1.2,"desc":"Fisico+magico"},
        {"id":"cura","nome":"Cura","nivel":5,"emoji":"💚","mana":25,"dano_mult":0,"desc":"Recupera 30% HP"},
        {"id":"aura_sagrada","nome":"Aura Sagrada","nivel":10,"emoji":"🌟","mana":30,"dano_mult":0,"desc":"+stats"},
        {"id":"juizo_final","nome":"Juizo Final","nivel":35,"emoji":"☀️","mana":50,"dano_mult":2.5,"desc":"ULTIMATE"},
    ],
    "necromante": [
        {"id":"drenar_vida","nome":"Drenar Vida","nivel":1,"emoji":"🌑","mana":10,"dano_mult":1.1,"desc":"Rouba HP"},
        {"id":"invocar_morto","nome":"Invocar Morto","nivel":8,"emoji":"💀","mana":20,"dano_mult":0.8,"desc":"Esqueleto ataca"},
        {"id":"maldicao","nome":"Maldicao","nivel":15,"emoji":"🩸","mana":15,"dano_mult":0.7,"desc":"Veneno"},
        {"id":"exercito","nome":"Exercito Morto","nivel":35,"emoji":"☠️","mana":50,"dano_mult":2.0,"desc":"ULTIMATE"},
    ],
    "dracomante": [
        {"id":"baforada","nome":"Baforada","nivel":1,"emoji":"🔥","mana":15,"dano_mult":1.4,"desc":"Fogo continuo"},
        {"id":"escamas","nome":"Escamas","nivel":10,"emoji":"🐉","mana":20,"dano_mult":0,"desc":"-30% dano"},
        {"id":"forma_menor","nome":"Forma Menor","nivel":20,"emoji":"🌋","mana":35,"dano_mult":0,"desc":"+30% stats"},
        {"id":"dragao_eterno","nome":"Dragao Eterno","nivel":42,"emoji":"💎","mana":60,"dano_mult":3.5,"desc":"ULTIMATE"},
    ],
    "arcano": [
        {"id":"faisca","nome":"Faisca Arcana","nivel":1,"emoji":"✨","mana":10,"dano_mult":1.2,"desc":"Arcano puro"},
        {"id":"campo_forca","nome":"Campo de Forca","nivel":5,"emoji":"🔮","mana":20,"dano_mult":0,"desc":"Reflete 20%"},
        {"id":"distorcao","nome":"Distorcao","nivel":10,"emoji":"🌀","mana":15,"dano_mult":0.5,"desc":"Confunde"},
        {"id":"singularidade","nome":"Singularidade","nivel":35,"emoji":"⭐","mana":60,"dano_mult":4.0,"desc":"ULTIMATE"},
    ],
}

# ─── DB HELPERS ──────────────────────────────────────────────────

async def get_personagem(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM personagens WHERE user_id=$1", user_id)

async def get_skills_eq(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT skill_id FROM skills_equipadas WHERE user_id=$1 AND slot!=99 ORDER BY slot", user_id)
        return [r["skill_id"] for r in rows]

async def get_skills_desbloq(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT skill_id FROM skills_desbloqueadas WHERE user_id=$1", user_id)
        return [r["skill_id"] for r in rows]

async def get_magia_suporte(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT skill_id FROM skills_equipadas WHERE user_id=$1 AND slot=99", user_id)
        return row["skill_id"] if row else None

async def get_inv_tipo(user_id, tipo):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("SELECT * FROM inventario WHERE user_id=$1 AND tipo=$2", user_id, tipo)

async def get_equipado(user_id, tipo):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM inventario WHERE user_id=$1 AND tipo=$2 AND equipado=1 LIMIT 1", user_id, tipo)

async def get_magias_suporte_inv(user_id):
    desbloq = await get_skills_desbloq(user_id)
    return {sid: info for sid, info in MAGIAS_SUPORTE.items() if sid in desbloq}

async def salvar_skills(user_id, skill_ids):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM skills_equipadas WHERE user_id=$1 AND slot!=99", user_id)
        for slot, sid in enumerate(skill_ids[:4]):
            await conn.execute(
                "INSERT INTO skills_equipadas(user_id,skill_id,slot) VALUES($1,$2,$3) ON CONFLICT(user_id,slot) DO UPDATE SET skill_id=EXCLUDED.skill_id",
                user_id, sid, slot
            )

async def salvar_magia_suporte(user_id, magia_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM skills_equipadas WHERE user_id=$1 AND slot=99", user_id)
        if magia_id and magia_id != "none":
            await conn.execute(
                "INSERT INTO skills_equipadas(user_id,skill_id,slot) VALUES($1,$2,99) ON CONFLICT(user_id,slot) DO UPDATE SET skill_id=EXCLUDED.skill_id",
                user_id, magia_id
            )

async def salvar_equip(user_id, tipo, item_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE inventario SET equipado=0 WHERE user_id=$1 AND tipo=$2", user_id, tipo)
        if item_id and item_id != "none":
            await conn.execute("UPDATE inventario SET equipado=1 WHERE user_id=$1 AND item_id=$2", user_id, item_id)

# ─── CALCULOS ────────────────────────────────────────────────────

def calcular_stats_setup(p, arma, armadura, classe_id):
    atk_base = p["ataque"]; dfs_base = p["defesa"]
    bonus_atk_num = 0; bonus_dfs_num = 0
    bonus_atk_pct = 1.0; bonus_dfs_pct = 1.0
    arma_compat = None; armadura_compat = None

    if arma:
        aid = arma["item_id"]
        bonus_atk_num = BONUS_ARMA.get(aid, {}).get("atk", 0)
        # Verifica afinidade via catalogo
        armas_cls = {a["id"] for a in get_armas_classe(classe_id)}
        if aid in armas_cls:
            bonus_atk_pct = 1.15; arma_compat = True
        else:
            bonus_atk_pct = 0.85; arma_compat = False

    if armadura:
        armid = armadura["item_id"]
        bonus_dfs_num = BONUS_ARMADURA.get(armid, {}).get("def", 0)
        armaduras_cls = {a["id"] for a in get_armaduras_classe(classe_id)}
        if armid in armaduras_cls:
            bonus_dfs_pct = 1.10; armadura_compat = True
        else:
            bonus_dfs_pct = 0.90; armadura_compat = False

    return {
        "atk_base": atk_base, "dfs_base": dfs_base,
        "bonus_atk_num": bonus_atk_num, "bonus_dfs_num": bonus_dfs_num,
        "bonus_atk_pct": bonus_atk_pct, "bonus_dfs_pct": bonus_dfs_pct,
        "atk_final": int((atk_base + bonus_atk_num) * bonus_atk_pct),
        "dfs_final": int((dfs_base + bonus_dfs_num) * bonus_dfs_pct),
        "arma_compat": arma_compat, "armadura_compat": armadura_compat,
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
        4: ("⭐⭐",   "Bom setup! Tente equipar mais skills ou melhorar os itens."),
        3: ("⭐",    "Razoavel. Verifique a afinidade dos equipamentos."),
        2: ("⚠️",   "Setup fraco. Troque por itens compativeis com sua classe."),
        1: ("❌",    "Setup muito fraco. Equipamentos incompativeis penalizam seus stats."),
        0: ("❌",    "Sem setup configurado. Use os menus abaixo para equipar tudo."),
    }
    return ratings.get(nota, ratings[0])

def build_embed_setup(p, skills_eq_ids, skills_desbloq_ids, arma, armadura, magia_sup_id, magias_inv, stats):
    emoji_j  = EMOJI_CLASSE.get(p["classe_id"], "⚔️")
    rank_inf = get_rank(p["nivel"])
    mana_mx  = calcular_mana_max(p["classe_id"], p["nivel"], p.get("poder_valor",10), p.get("destino_id","equilibrado"))

    # Mapa de todas as skills para busca
    todas_skills = {}
    for cid, lista in SKILLS_COMPLETAS_CAT.items():
        for sk in lista:
            todas_skills[sk["id"]] = dict(sk, classe_origem=cid)

    PASSIVA_DESC = {
        "guerreiro":  "🗡️ A cada 3 turnos +3 DEF permanente (cap 30)",
        "arqueiro":   "🏹 Critico recupera 8 de mana",
        "mago":       "🔮 Dano magico +8% por turno (cap 40%)",
        "paladino":   "⚡ HP<30%: cura 15 HP/turno automaticamente",
        "necromante": "🌑 Cada dreno aumenta o proximo em +10% (cap x2.0)",
        "dracomante": "🐉 -10% dano recebido, imune veneno/queimadura",
        "arcano":     "✨ Sem tomar dano: acumula +10% dano arcano (cap 50%)",
    }
    passiva_txt = PASSIVA_DESC.get(p["classe_id"], "")
    COR_CLASSE  = {"guerreiro":0x888780,"arqueiro":0x888780,"mago":0x888780,"paladino":0x1D9E75,"necromante":0x378ADD,"dracomante":0xD85A30,"arcano":0x7F77DD}

    embed = discord.Embed(
        title=f"{emoji_j} Setup de {p['nome']}",
        description=(
            f"**Classe:** {emoji_j} {p['classe_id'].title()} — *{p['raridade']}*\n"
            f"**Rank:** {rank_inf['emoji']} {rank_inf['rank']} | **Nível:** {p['nivel']}\n"
            f"**Mana máx:** {mana_mx} 💙\n"
            f"**Passiva:** {passiva_txt}"
        ),
        color=COR_CLASSE.get(p["classe_id"], 0x7F77DD)
    )

    # Skills
    sk_txt = ""
    for i, sid in enumerate(skills_eq_ids):
        sk = todas_skills.get(sid)
        if sk:
            mana_t = f" 💙{sk['mana']}" if sk.get("mana", 0) > 0 else ""
            compat = "✅" if sk.get("classe_origem") == p["classe_id"] else "⚠️"
            sk_txt += f"`{i+1}` {compat} {sk['emoji']} **{sk['nome']}**{mana_t} — *{sk['desc']}*\n"
    if not sk_txt:
        sk_txt = "*Nenhuma skill equipada. Use o menu Skills abaixo.*"
    embed.add_field(name=f"⚡ Skills ({len(skills_eq_ids)}/4)", value=sk_txt, inline=False)

    # Arma
    if arma:
        compat = "✅" if stats["arma_compat"] else "❌"
        pct_txt = "+15%" if stats["arma_compat"] else "-15%"
        num_txt = f"+{stats['bonus_atk_num']}" if stats["bonus_atk_num"] > 0 else "0"
        arma_txt = f"{compat} {arma['emoji']} **{arma['nome']}**\nATK base {stats['atk_base']} + {num_txt} x {pct_txt} = **{stats['atk_final']} ATK final**"
    else:
        arma_txt = f"*Sem arma equipada.*\nATK final = **{stats['atk_base']}**"
    embed.add_field(name="⚔️ Arma", value=arma_txt, inline=True)

    # Armadura
    if armadura:
        compat = "✅" if stats["armadura_compat"] else "❌"
        pct_txt = "+10%" if stats["armadura_compat"] else "-10%"
        num_txt = f"+{stats['bonus_dfs_num']}" if stats["bonus_dfs_num"] > 0 else "0"
        arm_txt = f"{compat} {armadura['emoji']} **{armadura['nome']}**\nDEF base {stats['dfs_base']} + {num_txt} x {pct_txt} = **{stats['dfs_final']} DEF final**"
    else:
        arm_txt = f"*Sem armadura equipada.*\nDEF final = **{stats['dfs_base']}**"
    embed.add_field(name="🛡️ Armadura", value=arm_txt, inline=True)

    # Magia de suporte
    if magia_sup_id and magia_sup_id in MAGIAS_SUPORTE:
        ms = MAGIAS_SUPORTE[magia_sup_id]
        rar_e = EMOJI_RAR.get(ms["raridade"], "⬜")
        ms_txt = f"{rar_e} {ms['emoji']} **{ms['nome']}** 💙{ms['mana']}\n*{ms['desc']}*"
    else:
        ms_txt = "*Nenhuma magia de suporte equipada.*"
    embed.add_field(name="🔮 Magia de Suporte", value=ms_txt, inline=False)

    # Stats finais
    mana_a = p["mana_atual"] if p["mana_atual"] else 100
    mana_m = p["mana_max"]   if p["mana_max"]   else 100
    stats_txt = (
        f"❤️ HP: **{p['hp_atual']}/{p['hp_max']}** | "
        f"⚔️ ATK: **{stats['atk_final']}** | "
        f"🛡️ DEF: **{stats['dfs_final']}** | "
        f"💙 Mana: **{mana_a}/{mana_m}**"
    )
    embed.add_field(name="📊 Stats finais", value=stats_txt, inline=False)

    # Avaliacao
    estrelas, msg = avaliar_setup(skills_eq_ids, stats["arma_compat"], stats["armadura_compat"])
    dicas = []
    if stats["arma_compat"] is False:
        dicas.append(f"⚔️ Troque para uma arma compativel com {p['classe_id'].title()}")
    if stats["armadura_compat"] is False:
        dicas.append(f"🛡️ Troque para uma armadura compativel com {p['classe_id'].title()}")
    if len(skills_eq_ids) < 4:
        dicas.append(f"⚡ Equipe mais {4-len(skills_eq_ids)} skill(s)")
    avaliacao = f"**Avaliacao: {estrelas}** — {msg}"
    if dicas:
        avaliacao += "\n\n**Dicas:**\n" + "\n".join([f"• {d}" for d in dicas])
    embed.add_field(name="📊 Analise", value=avaliacao, inline=False)
    embed.set_footer(text=f"Nivel {p['nivel']} • Use os menus abaixo para ajustar seu setup")
    return embed

# ─── VIEW PRINCIPAL ──────────────────────────────────────────────

class SetupView(discord.ui.View):
    def __init__(self, user_id, p, skills_eq, skills_desbloq, arma, armadura, magia_sup_id, magias_inv, armas_inv, armaduras_inv):
        super().__init__(timeout=180)
        self.user_id       = user_id
        self.p             = p
        self.skills_eq     = list(skills_eq)
        self.skills_desbloq = list(skills_desbloq)
        self.arma          = arma
        self.armadura      = armadura
        self.magia_sup_id  = magia_sup_id
        self.magias_inv    = magias_inv
        self.armas_inv     = list(armas_inv)
        self.armaduras_inv = list(armaduras_inv)
        self.msg           = None
        self._montar_menus()

    def _montar_menus(self):
        self.clear_items()
        todas_skills = {}
        for cid, lista in SKILLS_COMPLETAS_CAT.items():
            for sk in lista:
                todas_skills[sk["id"]] = dict(sk, classe_origem=cid)

        # Skills
        opcoes_sk = []
        for sid in self.skills_desbloq:
            sk = todas_skills.get(sid)
            if not sk: continue
            mana_t = f" 💙{sk['mana']}" if sk.get("mana", 0) > 0 else ""
            compat = "✅" if sk.get("classe_origem") == self.p["classe_id"] else "⚠️"
            opcoes_sk.append(discord.SelectOption(
                label=f"{compat} {sk['emoji']} {sk['nome']}{mana_t}",
                value=sid,
                description=sk["desc"][:50],
                default=sid in self.skills_eq
            ))
        if opcoes_sk:
            sel_sk = discord.ui.Select(placeholder="⚡ Selecione ate 4 skills...", min_values=0, max_values=min(4, len(opcoes_sk)), options=opcoes_sk[:25], row=0)
            sel_sk.callback = self._on_skills
            self.add_item(sel_sk)

        # Arma
        opcoes_arma = [discord.SelectOption(label="Sem arma", value="none", default=self.arma is None)]
        armas_cls_ids = {a["id"] for a in get_armas_classe(self.p["classe_id"])}
        for a in self.armas_inv:
            aid = a["item_id"]
            compat = "✅" if aid in armas_cls_ids else "❌"
            bonus = BONUS_ARMA.get(aid, {}).get("atk", 0)
            pct = "+15%" if compat == "✅" else "-15%"
            opcoes_arma.append(discord.SelectOption(
                label=f"{compat} {a['emoji']} {a['nome']}",
                value=aid,
                description=f"ATK +{bonus} | {pct} | [{a['raridade']}]",
                default=self.arma is not None and self.arma["item_id"] == aid
            ))
        if len(opcoes_arma) > 1:
            sel_arma = discord.ui.Select(placeholder="⚔️ Selecione uma arma...", options=opcoes_arma[:25], row=1)
            sel_arma.callback = self._on_arma
            self.add_item(sel_arma)

        # Armadura
        opcoes_arm = [discord.SelectOption(label="Sem armadura", value="none", default=self.armadura is None)]
        armaduras_cls_ids = {a["id"] for a in get_armaduras_classe(self.p["classe_id"])}
        for a in self.armaduras_inv:
            armid = a["item_id"]
            compat = "✅" if armid in armaduras_cls_ids else "❌"
            bonus = BONUS_ARMADURA.get(armid, {}).get("def", 0)
            pct = "+10%" if compat == "✅" else "-10%"
            opcoes_arm.append(discord.SelectOption(
                label=f"{compat} {a['emoji']} {a['nome']}",
                value=armid,
                description=f"DEF +{bonus} | {pct} | [{a['raridade']}]",
                default=self.armadura is not None and self.armadura["item_id"] == armid
            ))
        if len(opcoes_arm) > 1:
            sel_arm = discord.ui.Select(placeholder="🛡️ Selecione uma armadura...", options=opcoes_arm[:25], row=2)
            sel_arm.callback = self._on_armadura
            self.add_item(sel_arm)

        # Magia de suporte
        opcoes_ms = [discord.SelectOption(label="Sem magia de suporte", value="none", default=self.magia_sup_id is None)]
        for mid, ms in self.magias_inv.items():
            rar_e = EMOJI_RAR.get(ms["raridade"], "⬜")
            opcoes_ms.append(discord.SelectOption(
                label=f"{rar_e} {ms['emoji']} {ms['nome']} 💙{ms['mana']}",
                value=mid,
                description=ms["desc"][:50],
                default=self.magia_sup_id == mid
            ))
        if len(opcoes_ms) > 1:
            sel_ms = discord.ui.Select(placeholder="🔮 Selecione magia de suporte...", options=opcoes_ms[:25], row=3)
            sel_ms.callback = self._on_magia
            self.add_item(sel_ms)

    def _calcular_e_buildar(self):
        stats = calcular_stats_setup(self.p, self.arma, self.armadura, self.p["classe_id"])
        return build_embed_setup(self.p, self.skills_eq, self.skills_desbloq, self.arma, self.armadura, self.magia_sup_id, self.magias_inv, stats)

    async def _atualizar(self, inter):
        try: await inter.response.defer()
        except: pass
        self._montar_menus()
        if self.msg:
            try: await self.msg.edit(embed=self._calcular_e_buildar(), view=self)
            except: pass

    async def _on_skills(self, inter: discord.Interaction):
        if inter.user.id != self.user_id:
            await inter.response.send_message("Nao e seu setup!", ephemeral=True); return
        self.skills_eq = inter.data["values"][:4]
        await salvar_skills(self.user_id, self.skills_eq)
        await self._atualizar(inter)

    async def _on_arma(self, inter: discord.Interaction):
        if inter.user.id != self.user_id:
            await inter.response.send_message("Nao e seu setup!", ephemeral=True); return
        val = inter.data["values"][0]
        await salvar_equip(self.user_id, "arma", val)
        self.arma = None if val == "none" else next((a for a in self.armas_inv if a["item_id"] == val), None)
        await self._atualizar(inter)

    async def _on_armadura(self, inter: discord.Interaction):
        if inter.user.id != self.user_id:
            await inter.response.send_message("Nao e seu setup!", ephemeral=True); return
        val = inter.data["values"][0]
        await salvar_equip(self.user_id, "armadura", val)
        self.armadura = None if val == "none" else next((a for a in self.armaduras_inv if a["item_id"] == val), None)
        await self._atualizar(inter)

    async def _on_magia(self, inter: discord.Interaction):
        if inter.user.id != self.user_id:
            await inter.response.send_message("Nao e seu setup!", ephemeral=True); return
        val = inter.data["values"][0]
        self.magia_sup_id = None if val == "none" else val
        await salvar_magia_suporte(self.user_id, val)
        await self._atualizar(inter)

    async def on_timeout(self):
        if self.msg:
            try: await self.msg.edit(view=None)
            except: pass

# ─── COMANDO PRINCIPAL ────────────────────────────────────────────

async def cmd_setup(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro com `/criar_personagem`!", ephemeral=True); return

    skills_eq      = await get_skills_eq(interaction.user.id)
    skills_desbloq = await get_skills_desbloq(interaction.user.id)
    arma           = await get_equipado(interaction.user.id, "arma")
    armadura       = await get_equipado(interaction.user.id, "armadura")
    magia_sup_id   = await get_magia_suporte(interaction.user.id)
    magias_inv     = await get_magias_suporte_inv(interaction.user.id)
    armas_inv      = await get_inv_tipo(interaction.user.id, "arma")
    armaduras_inv  = await get_inv_tipo(interaction.user.id, "armadura")
    skills_eq_filtradas = [s for s in skills_eq if s != magia_sup_id]

    stats = calcular_stats_setup(p, arma, armadura, p["classe_id"])
    embed = build_embed_setup(p, skills_eq_filtradas, skills_desbloq, arma, armadura, magia_sup_id, magias_inv, stats)

    view = SetupView(
        user_id=interaction.user.id, p=p,
        skills_eq=skills_eq_filtradas, skills_desbloq=skills_desbloq,
        arma=arma, armadura=armadura,
        magia_sup_id=magia_sup_id, magias_inv=magias_inv,
        armas_inv=armas_inv, armaduras_inv=armaduras_inv,
    )
    embed.set_image(url=IMG_SETUP)
    msg = await interaction.followup.send(embed=embed, view=view, ephemeral=True, wait=True)
    view.msg = msg
