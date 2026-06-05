# systems/dungeon.py — Sistema de Dungeons

import discord
import asyncio
import random

from database.db import get_pool
from database.queries import get_personagem, get_skills_equipadas, get_pocoes_inv, get_arma_equipada, get_armadura_equipada
from data.dungeons import RANKS_DUNGEON
from data.skills import SKILLS_COMPLETAS, get_skill_by_id
from data.constantes import EMOJI_CLASSE, COR_RAR, IMG_DUNGEON, IMG_DUNGEON_MONSTRO, IMG_VITORIA, IMG_DERROTA
from systems.combate import Passiva, PassivaRacial, processar_efeitos_turno, efeito_ativo, add_efeito
from systems.combate import calcular_bonus_equip, aplicar_efeito_pocao, calc_dano, barra_hp
from utils.locks import get_user_lock
from views.batalha_view import DungeonBatalhaView
from utils.helpers import atualizar_todos_cargos


POCOES_DEF = {
    "pocao_hp_p": {"nome": "Poção de Cura P", "emoji": "🧪", "tipo": "hp", "valor": 30},
    "pocao_hp_m": {"nome": "Poção de Cura M", "emoji": "💊", "tipo": "hp", "valor": 60},
    "pocao_hp_g": {"nome": "Poção de Cura G", "emoji": "❤️", "tipo": "hp", "valor": 120},
    "pocao_mana_p": {"nome": "Poção de Mana P", "emoji": "🔵", "tipo": "mana", "valor": 20},
    "pocao_mana_m": {"nome": "Poção de Mana M", "emoji": "💙", "tipo": "mana", "valor": 50},
    "elixir": {"nome": "Elixir Supremo", "emoji": "✨", "tipo": "full", "valor": 999},
}


def get_skills_jogador(p, ids):
    """Retorna as skills do jogador baseado nos IDs equipados"""
    skills = []
    for sid in ids:
        sk = get_skill_by_id(sid)
        if sk:
            skills.append(sk)
    if not skills:
        cls = SKILLS_COMPLETAS.get(p["classe_id"], [])
        skills = cls[:4] if cls else []
    return skills


async def batalha_dungeon(interaction, p, monstro, skills, hp_j, mana_j, hp_jmx, mana_jmx, msgs):
    """Executa uma batalha de dungeon contra um monstro"""
    hp_m = monstro["hp"]
    hp_mmx = monstro["hp"]
    turno = 1
    efeitos = {}
    emoji_j = EMOJI_CLASSE.get(p["classe_id"], "⚔️")
    nivel_p = p["nivel"]
    timeout_count = 0

    try:
        arma_eq = await get_arma_equipada(p["user_id"])
        arm_eq = await get_armadura_equipada(p["user_id"])
        bonus_atk, bonus_dfs = calcular_bonus_equip(p["classe_id"], arma_eq, arm_eq)
    except Exception:
        bonus_atk, bonus_dfs = 1.0, 1.0

    def _mult_basico(nv):
        if nv <= 9: return 1.0
        elif nv <= 19: return 1.1
        elif nv <= 29: return 1.2
        elif nv <= 39: return 1.3
        elif nv <= 49: return 1.4
        elif nv <= 59: return 1.5
        elif nv <= 74: return 1.6
        else: return 1.8

    def status():
        return (
            f"{emoji_j} **{p['nome']}** ❤️`{barra_hp(hp_j, hp_jmx)}`{hp_j}/{hp_jmx} 💙{mana_j}\n"
            f"{monstro['emoji']} **{monstro['nome']}** ❤️`{barra_hp(hp_m, hp_mmx)}`{hp_m}/{hp_mmx}"
        )

    while hp_j > 0 and hp_m > 0:
        pocoes = await get_pocoes_inv(p["user_id"])
        view = DungeonBatalhaView(p["user_id"], skills, pocoes)

        embed_vez = discord.Embed(
            title=f"⚔️ Turno {turno} — Sua vez!",
            description=status(),
            color=0x7F77DD
        )
        msg_vez = await interaction.followup.send(embed=embed_vez, view=view, wait=True)
        msgs.append(msg_vez)
        await view.wait()

        try:
            await msg_vez.edit(view=None)
        except:
            pass

        acao, val = view.acao or ("timeout", None)

        if acao == "timeout":
            timeout_count += 1
            if timeout_count >= 3:
                return hp_j, mana_j, False, False
            else:
                aviso = discord.Embed(
                    title=f"Turno perdido! ({timeout_count}/3)",
                    description=f"Sem acao em 30s — turno ignorado. Mais {3 - timeout_count}x = expulso!",
                    color=0xE4AF3C
                )
                await msg_vez.edit(embed=aviso, view=None)
                continue

        timeout_count = 0

        if acao == "fugir":
            return hp_j, mana_j, False, True

        linha = ""
        cor = 0x378ADD

        if acao == "atk_basico":
            dano = calc_dano(p["ataque"], monstro["defesa"], _mult_basico(nivel_p),
                             bonus_atk=bonus_atk, nivel=nivel_p, hp_max_monstro=hp_mmx)
            hp_m = max(0, hp_m - dano)
            linha = f"⚔️ **Ataque Básico**: **{dano} de dano**! *(sem mana)*"
            cor = 0x888780

        elif acao == "defesa_basica":
            efeitos["defesa_basica"] = 1
            linha = f"🛡️ **Postura Defensiva!** 60% de chance de reduzir 80% do próximo dano. *(sem mana)*"
            cor = 0x378ADD

        elif acao == "pocao" and val:
            pd = POCOES_DEF.get(val)
            if pd:
                await remover_pocao(p["user_id"], val)
                if pd["tipo"] == "hp":
                    ganho = pd["valor"]
                    hp_j = min(hp_jmx, hp_j + ganho)
                    linha = f"🧪 **{pd['nome']}**: +{ganho} HP!"
                    cor = 0x1D9E75
                elif pd["tipo"] == "mana":
                    ganho = pd["valor"]
                    mana_j = min(mana_jmx, mana_j + ganho)
                    linha = f"🔵 **{pd['nome']}**: +{ganho} Mana!"
                elif pd["tipo"] == "full":
                    hp_j = hp_jmx
                    mana_j = mana_jmx
                    linha = "✨ **Elixir Supremo**: tudo restaurado!"
                    cor = 0xE4AF3C

        elif acao == "skill" and val is not None and val < len(skills):
            sk = skills[val]
            efeito = sk.get("efeito", "")
            custo = sk.get("mana", 0)
            if custo > mana_j:
                dano = calc_dano(p["ataque"], monstro["defesa"], _mult_basico(nivel_p),
                                 bonus_atk=bonus_atk, nivel=nivel_p, hp_max_monstro=hp_mmx)
                hp_m -= dano
                linha = f"⚔️ Sem mana! Ataque básico: **{dano} dano**"
                cor = 0x888780
            elif efeito == "cura":
                mana_j -= custo
                cura = int(hp_jmx * 0.30)
                hp_j = min(hp_jmx, hp_j + cura)
                linha = f"{sk['emoji']} **{sk['nome']}**: +{cura} HP!"
                cor = 0x1D9E75
            elif efeito in ("escudo", "esquiva", "armadura", "reflexo"):
                mana_j -= custo
                efeitos[efeito] = 2
                linha = f"{sk['emoji']} **{sk['nome']}**: efeito ativo!"
                cor = 0x7F77DD
            elif efeito == "dreno":
                mana_j -= custo
                dano = calc_dano(p["ataque"], monstro["defesa"], sk.get("dano", 1.0),
                                 bonus_atk=bonus_atk, nivel=nivel_p, hp_max_monstro=hp_mmx)
                roubo = dano // 2
                hp_m -= dano
                hp_j = min(hp_jmx, hp_j + roubo)
                linha = f"{sk['emoji']} **{sk['nome']}**: {dano} dano! +{roubo} HP drenado!"
                cor = 0x1D9E75
            else:
                mana_j -= custo
                crit = random.random() < 0.15
                dano = calc_dano(p["ataque"], monstro["defesa"], sk.get("dano", 1.0),
                                 crit, bonus_atk=bonus_atk, nivel=nivel_p, hp_max_monstro=hp_mmx)
                hp_m -= dano
                linha = f"{sk['emoji']} **{sk['nome']}**: **{dano} dano!**{'  💥 CRITICO!' if crit else ''}"
                cor = 0xD85A30 if crit else 0x378ADD
        else:
            dano = calc_dano(p["ataque"], monstro["defesa"])
            hp_m -= dano
            linha = f"⚔️ Ataque basico: **{dano} dano**"
            cor = 0x888780

        hp_m = max(0, hp_m)

        msg_a = await interaction.followup.send(
            embed=discord.Embed(title=f"{emoji_j} {p['nome']} agiu!", description=f"{linha}\n\n{status()}", color=cor),
            wait=True
        )
        msgs.append(msg_a)
        if hp_m <= 0:
            break

        await asyncio.sleep(1.0)

        sk_m = random.choice(monstro["skills"])
        dano_m = calc_dano(monstro["ataque"], p["defesa"], nivel=nivel_p)
        cor_m = 0xE24B4A

        if efeitos.get("defesa_basica", 0) > 0:
            efeitos["defesa_basica"] = 0
            if random.random() < 0.60:
                dano_red = max(1, int(dano_m * 0.20))
                hp_j = max(0, hp_j - dano_red)
                linha_m = f"{monstro['emoji']} **{monstro['nome']}** usou **{sk_m['nome']}**: **{dano_red} dano** (🛡️ Defesa funcionou! -80%!)"
                cor_m = 0x378ADD
            else:
                hp_j = max(0, hp_j - dano_m)
                linha_m = f"{monstro['emoji']} **{monstro['nome']}** usou **{sk_m['nome']}**: **{dano_m} dano** (❌ Defesa falhou! Dano total!)"
                cor_m = 0xE24B4A

        elif efeitos.get("esquiva", 0) > 0:
            linha_m = f"{monstro['emoji']} **{monstro['nome']}** usou **{sk_m['nome']}**... mas você **esquivou!** 💨"
            efeitos["esquiva"] -= 1
            cor_m = 0x888780

        elif efeitos.get("escudo", 0) > 0:
            linha_m = f"{monstro['emoji']} **{monstro['nome']}** usou **{sk_m['nome']}**... mas o **escudo absorveu!** 💜"
            efeitos["escudo"] -= 1
            cor_m = 0x7F77DD

        elif efeitos.get("armadura", 0) > 0:
            dano_red = max(1, int(dano_m * 0.65))
            hp_j = max(0, hp_j - dano_red)
            linha_m = f"{monstro['emoji']} **{monstro['nome']}** usou **{sk_m['nome']}**: **{dano_red} dano** (🐉 Armadura -35%!)"
            efeitos["armadura"] -= 1
            cor_m = 0xE67E22

        else:
            hp_j = max(0, hp_j - dano_m)
            linha_m = f"{monstro['emoji']} **{monstro['nome']}** usou **{sk_m['nome']}**: **{dano_m} dano!**"
            cor_m = 0xE24B4A

        regen = 8
        mana_j = min(mana_jmx, mana_j + regen)

        msg_m = await interaction.followup.send(
            embed=discord.Embed(
                title=f"{monstro['emoji']} {monstro['nome']} atacou!",
                description=f"{linha_m}\n\n{status()}\n💙 +{regen} mana ({mana_j}/{mana_jmx})",
                color=cor_m
            ),
            wait=True
        )
        msgs.append(msg_m)
        turno += 1
        await asyncio.sleep(0.8)

    vitoria = hp_m <= 0
    return hp_j, mana_j, vitoria, False


async def remover_pocao(user_id, item_id):
    """Remove uma poção do inventário"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, quantidade FROM inventario WHERE user_id = $1 AND item_id = $2",
            user_id, item_id
        )
        if row:
            if row["quantidade"] > 1:
                await conn.execute("UPDATE inventario SET quantidade = quantidade - 1 WHERE id = $1", row["id"])
            else:
                await conn.execute("DELETE FROM inventario WHERE id = $1", row["id"])


async def xp_needed_rank(nivel):
    """Calcula XP necessário para o próximo rank"""
    base = 100 + (nivel - 1) * 50
    if nivel >= 60:
        return int(base * 3.0)
    if nivel >= 40:
        return int(base * 2.0)
    if nivel >= 20:
        return int(base * 1.5)
    return base


async def salvar_resultado_dungeon(user_id, hp_final, xp_total, classe_id, nivel):
    """Salva o resultado da dungeon (XP, level up)"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        p = await conn.fetchrow(
            "SELECT xp, nivel, hp_max, ataque, defesa, poder_valor, destino_id FROM personagens WHERE user_id = $1",
            user_id
        )
        if not p:
            return 0, nivel
        
        novo_xp = p["xp"] + xp_total
        nv = p["nivel"]
        levelups = 0
        needed = await xp_needed_rank(nv)
        
        while novo_xp >= needed:
            novo_xp -= needed
            nv += 1
            needed = await xp_needed_rank(nv)
            levelups += 1
        
        hp_max = p["hp_max"] + levelups * 6
        atk = p["ataque"] + levelups * 2
        dfs = p["defesa"] + levelups * 1
        
        from utils.calculos import calcular_mana_max
        mana_max = calcular_mana_max(classe_id, nv, p["poder_valor"], p["destino_id"])
        hp_f = max(1, min(hp_final, hp_max))
        
        await conn.execute("""
            UPDATE personagens
            SET hp_atual = $1, hp_max = $2, xp = $3, nivel = $4,
                ataque = $5, defesa = $6, mana_max = $7,
                vitorias = vitorias + 1
            WHERE user_id = $8
        """, hp_f, hp_max, novo_xp, nv, atk, dfs, mana_max, user_id)
        
        # Desbloqueia skills do novo nível
        for s in SKILLS_COMPLETAS.get(classe_id, []):
            if s["nivel"] <= nv:
                await conn.execute(
                    "INSERT INTO skills_desbloqueadas(user_id, skill_id) VALUES($1, $2) ON CONFLICT DO NOTHING",
                    user_id, s["id"]
                )
        
        # Registra no passe
        try:
            from passe_temporada import adicionar_pontos_batalha
            await adicionar_pontos_batalha(user_id, True, "dungeon")
        except:
            pass
        
        # Registra no evento
        try:
            from eventos import registrar_dungeon_evento
            await registrar_dungeon_evento(user_id)
        except:
            pass
        
        return levelups, nv


async def cmd_dungeon(interaction: discord.Interaction, rank: str):
    """Comando /dungeon - Entra em uma dungeon"""
    user_id = interaction.user.id
    
    async with get_user_lock(user_id):
        await interaction.response.defer()

        p = await get_personagem(interaction.user.id)
        if not p:
            await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True)
            return

        dungeon = RANKS_DUNGEON.get(rank.upper())
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

        ids_eq = await get_skills_equipadas(p["user_id"])
        skills = get_skills_jogador(p, ids_eq)
        if not skills:
            cls = SKILLS_COMPLETAS.get(p["classe_id"], [])
            skills = cls[:4] if cls else []

        hp_j = p["hp_atual"]
        hp_jmx = p["hp_max"]
        mana_j = p.get("mana_atual", 100)
        mana_jmx = p.get("mana_max", 100)
        emoji_j = EMOJI_CLASSE.get(p["classe_id"], "⚔️")

        xp_total = 0
        moedas_total = 0
        msgs_global = []

        img_dg = IMG_DUNGEON.get(rank.upper(), IMG_DUNGEON["F"])
        embed_entrada = discord.Embed(
            title=f"{dungeon['emoji']} {dungeon['nome']}",
            description=(
                f"{dungeon['desc']}\n\n"
                f"**{emoji_j} {p['nome']}** entrou na dungeon!\n\n"
                f"❤️ HP: **{hp_j}/{hp_jmx}**\n"
                f"💙 Mana: **{mana_j}/{mana_jmx}**\n\n"
                f"🏆 **{len(dungeon['andares'])} andares + 1 chefe final**\n"
                f"💀 Se morrer, perde tudo que ganhou aqui!"
            ),
            color=dungeon["cor"]
        )
        embed_entrada.set_footer(text=f"Nivel minimo: {dungeon['nivel_min']} • Seu nivel: {p['nivel']}")
        msg_ent = await interaction.followup.send(embed=embed_entrada, wait=True)
        msgs_global.append(msg_ent)
        await asyncio.sleep(2)

        for info_andar in dungeon["andares"]:
            andar = info_andar["andar"]
            monstro = info_andar["monstro"]

            img_m = IMG_DUNGEON_MONSTRO.get(monstro["nome"], IMG_DUNGEON_MONSTRO["default"])
            embed_andar = discord.Embed(
                title=f"Andar {andar}/{len(dungeon['andares'])} — {info_andar['emoji']} {info_andar['nome']}",
                description=(
                    f"Um **{monstro['emoji']} {monstro['nome']}** bloqueia seu caminho!\n\n"
                    f"❤️ HP inimigo: **{monstro['hp']}**\n"
                    f"⚔️ Ataque: **{monstro['ataque']}** | 🛡️ Defesa: **{monstro['defesa']}**"
                ),
                color=dungeon["cor"]
            )
            embed_andar.set_thumbnail(url=img_m)
            msg_an = await interaction.followup.send(embed=embed_andar, wait=True)
            msgs_global.append(msg_an)
            await asyncio.sleep(1.5)

            msgs_batalha = []
            hp_j, mana_j, vitoria, fugiu = await batalha_dungeon(
                interaction, p, monstro, skills, hp_j, mana_j, hp_jmx, mana_jmx, msgs_batalha
            )
            msgs_global.extend(msgs_batalha)

            await asyncio.sleep(0.5)
            for m in msgs_batalha:
                try:
                    await m.delete()
                except:
                    pass

            if fugiu:
                for m in msgs_global:
                    try:
                        await m.delete()
                    except:
                        pass
                await interaction.followup.send(embed=discord.Embed(
                    title="🏃 Fugiu da Dungeon!",
                    description=f"**{p['nome']}** saiu da dungeon no andar {andar}.\nNenhuma recompensa foi obtida.",
                    color=0x888780
                ))
                return

            if not vitoria:
                pool = await get_pool()
                async with pool.acquire() as conn:
                    await conn.execute("UPDATE personagens SET hp_atual = 10, derrotas = derrotas + 1 WHERE user_id = $1", p["user_id"])
                
                from systems.combate import BATALHAS_ATIVAS
                BATALHAS_ATIVAS.discard(p["user_id"])
                
                for m in msgs_global:
                    try:
                        await m.delete()
                    except:
                        pass
                await interaction.followup.send(embed=discord.Embed(
                    title=f"💀 {p['nome']} foi derrotado no Andar {andar}!",
                    description=(
                        f"Voce foi derrotado por **{monstro['emoji']} {monstro['nome']}** no andar {andar}.\n\n"
                        "Perdeu todas as recompensas da dungeon!\n"
                        "Acordou na cidade com 10 HP."
                    ),
                    color=0xE24B4A
                ))
                return

            xp_andar = dungeon["recompensa_andar"]["xp"]
            moedas_andar = dungeon["recompensa_andar"]["moedas"]
            xp_total += xp_andar
            moedas_total += moedas_andar
            mana_j = min(mana_jmx, mana_j + 15)

            msg_vit = await interaction.followup.send(embed=discord.Embed(
                title=f"✅ Andar {andar} concluido!",
                description=(
                    f"**{monstro['emoji']} {monstro['nome']}** foi derrotado!\n\n"
                    f"+{xp_andar} XP | +{moedas_andar} 🪙\n"
                    f"❤️ HP restante: **{hp_j}/{hp_jmx}**\n\n"
                    f"{'➡️ Proximo andar...' if andar < len(dungeon['andares']) else '⚔️ O CHEFE FINAL AGUARDA!'}"
                ),
                color=0x1D9E75
            ), wait=True)
            msgs_global.append(msg_vit)
            await asyncio.sleep(2)

        chefe = dungeon["chefe"]

        img_chefe = IMG_DUNGEON_MONSTRO.get(chefe["nome"], IMG_DUNGEON_MONSTRO["default"])
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
        embed_chefe.set_thumbnail(url=img_chefe)
        msg_ch = await interaction.followup.send(embed=embed_chefe, wait=True)
        msgs_global.append(msg_ch)
        await asyncio.sleep(2)

        msgs_chefe = []
        hp_j, mana_j, vitoria, fugiu = await batalha_dungeon(
            interaction, p, chefe, skills, hp_j, mana_j, hp_jmx, mana_jmx, msgs_chefe
        )
        msgs_global.extend(msgs_chefe)

        for m in msgs_chefe:
            try:
                await m.delete()
            except:
                pass

        if fugiu or not vitoria:
            pool = await get_pool()
            async with pool.acquire() as conn:
                await conn.execute("UPDATE personagens SET hp_atual = 10, derrotas = derrotas + 1 WHERE user_id = $1", p["user_id"])
            for m in msgs_global:
                try:
                    await m.delete()
                except:
                    pass
            titulo = "Fugiu do chefe!" if fugiu else "Derrotado pelo chefe!"
            await interaction.followup.send(embed=discord.Embed(
                title=titulo,
                description="Tao perto... mas voce falhou.\n Todas as recompensas foram perdidas!",
                color=0xE24B4A
            ))
            return

        xp_total += dungeon["recompensa_chefe"]["xp"]
        moedas_total += dungeon["recompensa_chefe"]["moedas"]

        # Adiciona loot
        async def add_item_dungeon(user_id, item):
            pool = await get_pool()
            async with pool.acquire() as conn:
                ex = await conn.fetchrow(
                    "SELECT id, quantidade FROM inventario WHERE user_id = $1 AND item_id = $2",
                    user_id, item[0]
                )
                if ex:
                    await conn.execute("UPDATE inventario SET quantidade = quantidade + 1 WHERE id = $1", ex["id"])
                else:
                    await conn.execute("""
                        INSERT INTO inventario (user_id, item_id, nome, tipo, raridade, emoji, descricao)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """, user_id, item[0], item[1], item[2], item[3], item[4], item[5])

        loot_obtido = []
        if chefe.get("loot_raro"):
            await add_item_dungeon(p["user_id"], chefe["loot_raro"])
            loot_obtido.append(f"{chefe['loot_raro'][4]} **{chefe['loot_raro'][1]}** [{chefe['loot_raro'][3]}]")
        if chefe.get("loot_epico") and random.random() < 0.40:
            await add_item_dungeon(p["user_id"], chefe["loot_epico"])
            loot_obtido.append(f"{chefe['loot_epico'][4]} **{chefe['loot_epico'][1]}** [{chefe['loot_epico'][3]}] 🎉")

        lvlups, nivel_novo_d = await salvar_resultado_dungeon(p["user_id"], hp_j, xp_total, p["classe_id"], p["nivel"])

        loot_txt = "\n".join(loot_obtido) if loot_obtido else "*Nenhum item obtido*"
        rank_obj_d = get_rank(nivel_novo_d)

        desc_final = (
            f"**{emoji_j} {p['nome']}** completou a **{dungeon['emoji']} {dungeon['nome']}**!\n\n"
            f"👑 Chefe derrotado: **{chefe['emoji']} {chefe['nome']}**\n\n"
            f"✨ **+{xp_total} XP** conquistados\n"
            f"📦 **Venda o loot no** `/mercado` **para ganhar moedas!**\n\n"
            f"🎁 **Loot obtido:**\n{loot_txt}"
        )
        if lvlups:
            rank_txt = ""
            if get_rank(p['nivel'])['rank'] != rank_obj_d['rank']:
                rank_txt = f"\n🏅 Novo rank: {rank_obj_d['emoji']} **{rank_obj_d['rank']}**!"
            desc_final += f"\n\n🎉 **LEVEL UP! Nível {nivel_novo_d}!** (+{lvlups} nível){rank_txt}"
            desc_final += f"\n+{lvlups * 6} HP | +{lvlups * 2} ATK | +{lvlups} DEF"

        embed_recomp = discord.Embed(
            title="🏆 Dungeon Concluída!",
            description=desc_final,
            color=dungeon["cor"]
        )
        embed_recomp.set_image(url=IMG_VITORIA)
        embed_recomp.set_footer(text="Venda seus itens no /mercado para ganhar moedas!")

        await interaction.followup.send(embed=embed_recomp)
        await asyncio.sleep(1.5)

        for m in msgs_global:
            try:
                await m.delete()
            except:
                pass