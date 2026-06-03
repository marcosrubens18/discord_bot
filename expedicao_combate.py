# expedicao_combate.py — Sistema de combate em grupo para Expedições
import discord
import asyncio
import random
from db import get_pool
from batalha import (
    BATALHAS_ATIVAS, calc_dano, BatalhaView, get_pocoes_inv, get_skills_eq,
    barra_hp, processar_efeitos_turno, add_efeito, efeito_ativo,
    Passiva, PassivaRacial, aplicar_efeito_pocao, remover_pocao,
    calcular_bonus_equip, get_arma_equipada, get_armadura_equipada,
    EMOJI_CLASSE, MONSTROS
)
from catalogo import SKILLS_COMPLETAS

def get_monstro_por_nome(nome: str) -> dict:
    """Busca monstro pelo nome (case insensitive)."""
    nome_lower = nome.lower().strip()
    for m in MONSTROS:
        if m["nome"].lower() == nome_lower or nome_lower in m["nome"].lower():
            return m
    return MONSTROS[0]

async def setup_jogador(user_id: int, p: dict) -> dict:
    """Prepara stats completos do jogador para o combate."""
    ids_eq = await get_skills_eq(user_id)
    skills = [s for sid in ids_eq for s in SKILLS_COMPLETAS.get(p["classe_id"], []) if s["id"] == sid]
    if not skills:
        skills = SKILLS_COMPLETAS.get(p["classe_id"], [])[:4]
    arma = await get_arma_equipada(user_id)
    armadura = await get_armadura_equipada(user_id)
    batk, bdfs = calcular_bonus_equip(p["classe_id"], arma, armadura)
    return {
        "user_id": user_id,
        "nome": p["nome"],
        "classe_id": p["classe_id"],
        "nivel": p["nivel"],
        "hp": p["hp_atual"],
        "hp_max": p["hp_max"],
        "mana": p["mana_atual"] or 100,
        "mana_max": p["mana_max"] or 100,
        "ataque": p["ataque"],
        "defesa": p["defesa"],
        "efeitos": {},
        "passiva": Passiva(p["classe_id"]),
        "racial": PassivaRacial(p.get("raca_id", "humano")),
        "skills": skills,
        "batk": batk,
        "bdfs": bdfs,
        "emoji": EMOJI_CLASSE.get(p["classe_id"], "⚔️"),
        "vivo": True,
    }

def barra_status_grupo(jogadores: list, hp_m: int, hp_mmx: int, monstro: dict) -> str:
    linhas = []
    for j in jogadores:
        if j["vivo"]:
            linhas.append(f"{j['emoji']} **{j['nome']}** ❤️`{barra_hp(j['hp'], j['hp_max'])}`**{j['hp']}/{j['hp_max']}**")
        else:
            linhas.append(f"💀 ~~{j['nome']}~~")
    linhas.append(f"{monstro['emoji']} **{monstro['nome']}** ❤️`{barra_hp(hp_m, hp_mmx)}`**{hp_m}/{hp_mmx}**")
    return "\n".join(linhas)

async def rodar_combate_expedicao(canal: discord.TextChannel, participantes_ids: list,
                                   nome_monstro: str, quantidade: int = 1) -> dict:
    """Executa combate em grupo para Expedição Narrativa."""
    pool = await get_pool()

    # Carrega personagens
    jogadores = []
    async with pool.acquire() as conn:
        for uid in participantes_ids:
            p = await conn.fetchrow("SELECT * FROM personagens WHERE user_id=$1", uid)
            if p and uid not in BATALHAS_ATIVAS:
                j = await setup_jogador(uid, p)
                jogadores.append(j)
                BATALHAS_ATIVAS.add(uid)

    if not jogadores:
        return {"sucesso": False, "sobreviventes": [], "derrotados": participantes_ids,
                "sobreviventes_nomes": [], "derrotados_nomes": []}

    monstro_base = get_monstro_por_nome(nome_monstro)
    monstro = dict(monstro_base)
    monstro["nome"] = nome_monstro
    hp_m = monstro["hp"] * max(1, len(jogadores) // 2 + 1) * quantidade
    hp_mmx = hp_m
    timeout_count = {}

    embed_ini = discord.Embed(
        title=f"⚔️ COMBATE — {monstro['emoji']} {monstro['nome']}",
        description=f"Os aventureiros enfrentam **{quantidade}x {monstro['nome']}**!\n\n{barra_status_grupo(jogadores, hp_m, hp_mmx, monstro)}",
        color=0xE24B4A
    )
    await canal.send(embed=embed_ini)
    await asyncio.sleep(1)

    turno = 1

    while hp_m > 0 and any(j["vivo"] for j in jogadores):
        vivos = [j for j in jogadores if j["vivo"]]

        for j in vivos:
            if hp_m <= 0:
                break
            uid = j["user_id"]
            tc = timeout_count.get(uid, 0)

            pocoes = await get_pocoes_inv(uid)
            view = BatalhaView(uid, j["skills"], pocoes, nivel=j["nivel"])
            embed_vez = discord.Embed(
                title=f"Turno {turno} — {j['emoji']} {j['nome']}, sua vez!",
                description=barra_status_grupo(jogadores, hp_m, hp_mmx, monstro),
                color=0x378ADD
            )
            membro = canal.guild.get_member(uid)
            msg_v = await canal.send(content=membro.mention if membro else "", embed=embed_vez, view=view)
            await view.wait()
            try:
                await msg_v.edit(view=None)
            except:
                pass

            acao, val = view.acao or ("timeout", None)

            if acao == "timeout":
                tc += 1
                timeout_count[uid] = tc
                if tc >= 3:
                    await canal.send(f"💤 **{j['nome']}** foi expulso por inatividade!")
                    j["vivo"] = False
                    BATALHAS_ATIVAS.discard(uid)
                    continue
                await canal.send(embed=discord.Embed(description=f"⏰ {j['nome']} perdeu o turno! ({tc}/3)", color=0xE4AF3C))
                continue
            else:
                timeout_count[uid] = 0

            dano_j = 0
            linha = ""
            if acao == "fugir":
                await canal.send(f"🏃 **{j['nome']}** fugiu do combate!")
                j["vivo"] = False
                BATALHAS_ATIVAS.discard(uid)
                continue
            elif acao == "atk_basico":
                mult = 1.0 + (j["nivel"] // 10) * 0.1
                dano_j = calc_dano(j["ataque"], monstro["defesa"], mult, bonus_atk=j["batk"])
                hp_m = max(0, hp_m - dano_j)
                linha = f"{j['emoji']} **{j['nome']}** — Ataque Básico: **{dano_j} de dano**!"
            elif acao == "defesa_basica":
                add_efeito(j["efeitos"], "defesa_basica", 1)
                linha = f"{j['emoji']} **{j['nome']}** — Postura defensiva!"
            elif acao == "skill" and val is not None:
                sk = j["skills"][val] if val < len(j["skills"]) else j["skills"][0]
                if j["mana"] >= sk.get("mana", 0):
                    j["mana"] -= sk.get("mana", 0)
                    dano_j = calc_dano(j["ataque"], monstro["defesa"], sk.get("dano", 1.0), bonus_atk=j["batk"])
                    dano_j = int(dano_j * j["passiva"].multiplicador_dano())
                    hp_m = max(0, hp_m - dano_j)
                    linha = f"{j['emoji']} **{j['nome']}** — {sk['emoji']} **{sk['nome']}**: **{dano_j} de dano**!"
                else:
                    dano_j = calc_dano(j["ataque"], monstro["defesa"], bonus_atk=j["batk"])
                    hp_m = max(0, hp_m - dano_j)
                    linha = f"{j['emoji']} **{j['nome']}** — Sem mana! Ataque: **{dano_j} de dano**."
            elif acao == "pocao" and val:
                j["hp"], j["mana"], linha = aplicar_efeito_pocao(val, j["hp"], j["hp_max"], j["mana"], j["mana_max"])
                await remover_pocao(uid, val)
                linha = f"{j['emoji']} **{j['nome']}** — {linha}"

            if linha:
                cor = 0x1D9E75 if hp_m <= 0 else 0x378ADD
                await canal.send(embed=discord.Embed(description=f"{linha}\n\n{barra_status_grupo(jogadores, hp_m, hp_mmx, monstro)}", color=cor))

            if hp_m <= 0:
                break

        if hp_m <= 0:
            break

        vivos = [j for j in jogadores if j["vivo"]]
        if not vivos:
            break

        linhas_m = []
        for j in vivos:
            dano_m = calc_dano(monstro["ataque"], j["defesa"], bonus_atk=j["bdfs"])
            red = j["racial"].reducao_dano()
            if red > 0:
                dano_m = max(1, int(dano_m * (1 - red)))
            if efeito_ativo(j["efeitos"], "defesa_basica") or efeito_ativo(j["efeitos"], "defesa"):
                dano_m = max(1, dano_m // 5)
            j["hp"] = max(0, j["hp"] - dano_m)
            j["mana"] = min(j["mana_max"], j["mana"] + 8)
            linhas_m.append(f"{monstro['emoji']} → {j['emoji']} **{j['nome']}**: **{dano_m} de dano**")
            if j["hp"] <= 0:
                j["vivo"] = False
                BATALHAS_ATIVAS.discard(j["user_id"])
                linhas_m.append(f"💀 **{j['nome']}** foi derrotado!")

        await canal.send(embed=discord.Embed(
            title=f"{monstro['emoji']} {monstro['nome']} contra-ataca!",
            description="\n".join(linhas_m) + f"\n\n{barra_status_grupo(jogadores, hp_m, hp_mmx, monstro)}",
            color=0xE24B4A))

        turno += 1
        await asyncio.sleep(0.5)

    for j in jogadores:
        BATALHAS_ATIVAS.discard(j["user_id"])

    sobreviventes = [j for j in jogadores if j["vivo"]]
    derrotados = [j for j in jogadores if not j["vivo"]]
    sucesso = hp_m <= 0

    embed_res = discord.Embed(
        title="🏆 Vitória!" if sucesso else "💀 Derrota...",
        description=(f"O {monstro['nome']} foi derrotado!\n\n" if sucesso else f"O grupo foi derrotado pelo {monstro['nome']}...\n\n") +
        f"**Sobreviventes:** {', '.join([j['nome'] for j in sobreviventes]) or 'Nenhum'}\n"
        f"**Derrotados:** {', '.join([j['nome'] for j in derrotados]) or 'Nenhum'}",
        color=0x1D9E75 if sucesso else 0xE24B4A
    )
    await canal.send(embed=embed_res)

    return {
        "sucesso": sucesso,
        "sobreviventes": [j["user_id"] for j in sobreviventes],
        "derrotados": [j["user_id"] for j in derrotados],
        "sobreviventes_nomes": [j["nome"] for j in sobreviventes],
        "derrotados_nomes": [j["nome"] for j in derrotados],
    }