# dupla.py — Sistema de batalha e dungeon em dupla
import discord
import asyncio
import random
from db import get_pool
from batalha import (
    BATALHAS_ATIVAS, calc_dano, BatalhaView, get_pocoes_inv, get_skills_eq,
    barra_hp, processar_efeitos_turno, add_efeito, efeito_ativo,
    Passiva, PassivaRacial, aplicar_efeito_pocao, remover_pocao,
    calcular_bonus_equip, get_arma_equipada, get_armadura_equipada,
    EMOJI_CLASSE, MONSTROS, ARENAS, salvar_resultado
)
from catalogo import SKILLS_COMPLETAS, get_rank
from guildas import dar_xp_guilda, atualizar_missao_guilda, get_guilda_do_jogador

async def get_personagem(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM personagens WHERE user_id=$1", user_id)

async def rodar_treino_dupla(interaction: discord.Interaction, p1, p2, monstro, arena,
                              membro1: discord.Member, membro2: discord.Member):
    """Batalha em dupla contra monstro com HP dobrado."""
    uid1 = p1["user_id"]; uid2 = p2["user_id"]
    BATALHAS_ATIVAS.add(uid1); BATALHAS_ATIVAS.add(uid2)

    # Setup P1
    ids1    = await get_skills_eq(uid1)
    skills1 = [s for sid in ids1 for s in SKILLS_COMPLETAS.get(p1["classe_id"],[]) if s["id"]==sid] or SKILLS_COMPLETAS.get(p1["classe_id"],[])[:4]
    arma1, arm1 = await get_arma_equipada(uid1), await get_armadura_equipada(uid1)
    batk1, bdfs1 = calcular_bonus_equip(p1["classe_id"], arma1, arm1)
    passiva1     = Passiva(p1["classe_id"])
    racial1      = PassivaRacial(p1.get("raca_id","humano"))
    hp1 = p1["hp_atual"]; hp1mx = p1["hp_max"]
    mana1 = p1["mana_atual"] or 100; mana1mx = p1["mana_max"] or 100
    ef1   = {}; e1 = EMOJI_CLASSE.get(p1["classe_id"],"⚔️")
    vivo1 = True

    # Setup P2
    ids2    = await get_skills_eq(uid2)
    skills2 = [s for sid in ids2 for s in SKILLS_COMPLETAS.get(p2["classe_id"],[]) if s["id"]==sid] or SKILLS_COMPLETAS.get(p2["classe_id"],[])[:4]
    arma2, arm2 = await get_arma_equipada(uid2), await get_armadura_equipada(uid2)
    batk2, bdfs2 = calcular_bonus_equip(p2["classe_id"], arma2, arm2)
    passiva2     = Passiva(p2["classe_id"])
    racial2      = PassivaRacial(p2.get("raca_id","humano"))
    hp2 = p2["hp_atual"]; hp2mx = p2["hp_max"]
    mana2 = p2["mana_atual"] or 100; mana2mx = p2["mana_max"] or 100
    ef2   = {}; e2 = EMOJI_CLASSE.get(p2["classe_id"],"⚔️")
    vivo2 = True

    # Monstro com HP dobrado para dupla
    hp_m  = monstro["hp"] * 2
    hp_mmx = hp_m
    ef_m  = {}

    turno = 1
    msgs  = []
    timeout1 = timeout2 = 0

    def barra():
        v1 = f"{e1} **{p1['nome']}** ❤️`{barra_hp(hp1,hp1mx)}`**{hp1}/{hp1mx}**" if vivo1 else f"{e1} ~~{p1['nome']}~~ 💀"
        v2 = f"{e2} **{p2['nome']}** ❤️`{barra_hp(hp2,hp2mx)}`**{hp2}/{hp2mx}**" if vivo2 else f"{e2} ~~{p2['nome']}~~ 💀"
        vm = f"{monstro['emoji']} **{monstro['nome']}** ❤️`{barra_hp(hp_m,hp_mmx)}`**{hp_m}/{hp_mmx}**"
        return f"{v1}\n{v2}\n{vm}"

    # Embed inicial
    embed_ini = discord.Embed(
        title=f"⚔️ Batalha em Dupla! — {arena['emoji']} {arena['nome']}",
        description=f"{membro1.mention} + {membro2.mention} vs {monstro['emoji']} **{monstro['nome']}** (HP x2!)\n\n{barra()}",
        color=0x7F77DD
    )
    if arena.get("img"): embed_ini.set_image(url=arena["img"])
    msgs.append(await interaction.followup.send(embed=embed_ini, wait=True))
    await asyncio.sleep(1)

    while hp_m > 0 and (vivo1 or vivo2):

        # Efeitos status
        de1,me1,ef1 = processar_efeitos_turno(ef1)
        if de1 > 0 and vivo1: hp1 = max(0, hp1-de1)
        de2,me2,ef2 = processar_efeitos_turno(ef2)
        if de2 > 0 and vivo2: hp2 = max(0, hp2-de2)
        de_m,me_m,ef_m = processar_efeitos_turno(ef_m)
        if de_m > 0: hp_m = max(0, hp_m-de_m)
        if hp_m <= 0: break

        # ── TURNO P1 ──────────────────────────────────────────
        if vivo1:
            pocoes1 = await get_pocoes_inv(uid1)
            v1 = BatalhaView(uid1, skills1, pocoes1, nivel=p1["nivel"])
            em_v1 = discord.Embed(
                title=f"Turno {turno} — {e1} {p1['nome']}, sua vez!",
                description=barra(), color=0x378ADD
            )
            msg_v1 = await interaction.followup.send(content=membro1.mention, embed=em_v1, view=v1, wait=True)
            msgs.append(msg_v1)
            await v1.wait()
            try: await msg_v1.edit(view=None)
            except: pass
            acao1, val1 = v1.acao or ("timeout", None)

            if acao1 == "timeout":
                timeout1 += 1
                if timeout1 >= 3:
                    await interaction.followup.send(f"{e1} {p1['nome']} foi expulso por inatividade!")
                    vivo1 = False
                else:
                    await interaction.followup.send(embed=discord.Embed(
                        description=f"⏰ {p1['nome']} perdeu o turno! ({timeout1}/3)", color=0xE4AF3C))
            elif acao1 == "fugir":
                await interaction.followup.send(f"{e1} {p1['nome']} fugiu da batalha!")
                vivo1 = False
            else:
                timeout1 = 0
                linha1 = await _processar_acao(acao1, val1, p1, monstro, hp_m, hp_mmx, mana1, mana1mx, hp1, hp1mx, ef1, ef_m, skills1, batk1, passiva1, uid1)
                if isinstance(linha1, tuple):
                    hp_m, mana1, hp1, linha1_txt = linha1
                else:
                    linha1_txt = linha1
                await interaction.followup.send(embed=discord.Embed(
                    description=f"{e1} {linha1_txt}\n\n{barra()}", color=0x7F77DD))

            if hp_m <= 0: break

        # ── TURNO P2 ──────────────────────────────────────────
        if vivo2:
            pocoes2 = await get_pocoes_inv(uid2)
            v2 = BatalhaView(uid2, skills2, pocoes2, nivel=p2["nivel"])
            em_v2 = discord.Embed(
                title=f"Turno {turno} — {e2} {p2['nome']}, sua vez!",
                description=barra(), color=0x9B59B6
            )
            msg_v2 = await interaction.followup.send(content=membro2.mention, embed=em_v2, view=v2, wait=True)
            msgs.append(msg_v2)
            await v2.wait()
            try: await msg_v2.edit(view=None)
            except: pass
            acao2, val2 = v2.acao or ("timeout", None)

            if acao2 == "timeout":
                timeout2 += 1
                if timeout2 >= 3:
                    await interaction.followup.send(f"{e2} {p2['nome']} foi expulso por inatividade!")
                    vivo2 = False
                else:
                    await interaction.followup.send(embed=discord.Embed(
                        description=f"⏰ {p2['nome']} perdeu o turno! ({timeout2}/3)", color=0xE4AF3C))
            elif acao2 == "fugir":
                await interaction.followup.send(f"{e2} {p2['nome']} fugiu da batalha!")
                vivo2 = False
            else:
                timeout2 = 0
                linha2 = await _processar_acao(acao2, val2, p2, monstro, hp_m, hp_mmx, mana2, mana2mx, hp2, hp2mx, ef2, ef_m, skills2, batk2, passiva2, uid2)
                if isinstance(linha2, tuple):
                    hp_m, mana2, hp2, linha2_txt = linha2
                else:
                    linha2_txt = linha2
                await interaction.followup.send(embed=discord.Embed(
                    description=f"{e2} {linha2_txt}\n\n{barra()}", color=0x9B59B6))

            if hp_m <= 0: break

        if not vivo1 and not vivo2: break

        # ── ATAQUE DO MONSTRO ──────────────────────────────────
        alvos = [(uid1,p1,hp1,hp1mx,ef1,bdfs1,racial1,membro1,e1,vivo1),
                 (uid2,p2,hp2,hp2mx,ef2,bdfs2,racial2,membro2,e2,vivo2)]
        for uid_a, p_a, hp_a, hp_amx, ef_a, bdfs_a, racial_a, mem_a, e_a, vivo_a in alvos:
            if not vivo_a: continue
            dano_m = calc_dano(monstro["ataque"], p_a["defesa"], bonus_atk=bdfs_a)
            # Aplica reducao racial de dano
            reducao = racial_a.reducao_dano()
            if reducao > 0: dano_m = max(1, int(dano_m * (1 - reducao)))
            if efeito_ativo(ef_a, "defesa_basica") or efeito_ativo(ef_a, "defesa"):
                dano_m = max(1, dano_m // 5)
            if uid_a == uid1: hp1 = max(0, hp1 - dano_m)
            else:             hp2 = max(0, hp2 - dano_m)

        # Regenera mana
        mana1 = min(mana1mx, mana1 + 8)
        mana2 = min(mana2mx, mana2 + 8)

        await interaction.followup.send(embed=discord.Embed(
            description=f"{monstro['emoji']} **{monstro['nome']}** ataca!\n\n{barra()}",
            color=0xE24B4A))

        # Verifica mortes
        if hp1 <= 0 and vivo1:
            vivo1 = False
            await interaction.followup.send(f"💀 {e1} **{p1['nome']}** foi derrotado! {e2} {p2['nome']} continua lutando...")
        if hp2 <= 0 and vivo2:
            vivo2 = False
            await interaction.followup.send(f"💀 {e2} **{p2['nome']}** foi derrotado! {e1} {p1['nome']} continua lutando...")

        turno += 1

    # ── RESULTADO ─────────────────────────────────────────────
    BATALHAS_ATIVAS.discard(uid1); BATALHAS_ATIVAS.discard(uid2)
    vitoria = hp_m <= 0

    if vitoria:
        # Bonus de 20% por batalha em dupla
        xp_base    = monstro.get("xp", 15)
        moedas_base = monstro.get("moedas", 10)
        xp_bonus    = int(xp_base * 1.2)
        moedas_bonus= int(moedas_base * 1.2)

        for uid_v, p_v, vivo_v in [(uid1,p1,vivo1),(uid2,p2,vivo2)]:
            if vivo_v or True:  # todos que participaram recebem
                await salvar_resultado(uid_v, p_v["hp_atual"], xp_bonus, moedas_bonus, True, p_v["classe_id"], p_v["nivel"])
                # XP para guilda
                g_v, _ = await get_guilda_do_jogador(uid_v)
                if g_v: await dar_xp_guilda(g_v["id"], 10, interaction.guild)
                await atualizar_missao_guilda(uid_v, "vitorias_treino")

        embed_fim = discord.Embed(
            title="🏆 Vitória em Dupla!",
            description=(
                f"{membro1.mention} + {membro2.mention} derrotaram **{monstro['emoji']} {monstro['nome']}**!\n\n"
                f"+{xp_bonus} XP | +{moedas_bonus} 🪙 (+20% bonus dupla)"
            ),
            color=0x1D9E75
        )
    else:
        embed_fim = discord.Embed(
            title="💀 Derrota...",
            description=f"**{monstro['emoji']} {monstro['nome']}** foi forte demais para a dupla!",
            color=0xE24B4A
        )

    await interaction.followup.send(embed=embed_fim)
    for m in msgs:
        try: await m.delete()
        except: pass

async def _processar_acao(acao, val, p, monstro, hp_m, hp_mmx, mana, mana_mx, hp_j, hp_jmx, ef_j, ef_m, skills, batk, passiva, uid):
    """Processa acao do jogador e retorna linha descritiva."""
    if acao == "atk_basico":
        mult = 1.0 + (p["nivel"]//10)*0.1
        dano = calc_dano(p["ataque"], monstro["defesa"], mult, bonus_atk=batk)
        hp_m = max(0, hp_m - dano)
        return (hp_m, mana, hp_j, f"Ataque Basico: **{dano} de dano**!")
    elif acao == "defesa_basica":
        add_efeito(ef_j, "defesa_basica", 1)
        return (hp_m, mana, hp_j, "Postura defensiva!")
    elif acao == "skill" and val is not None:
        sk = skills[val] if val < len(skills) else skills[0]
        if mana >= sk.get("mana",0):
            mana -= sk.get("mana",0)
            dano = calc_dano(p["ataque"], monstro["defesa"], sk.get("dano",1.0), bonus_atk=batk)
            dano = int(dano * passiva.multiplicador_dano())
            hp_m = max(0, hp_m - dano)
            return (hp_m, mana, hp_j, f"{sk['emoji']} **{sk['nome']}**: **{dano} de dano**!")
        else:
            dano = calc_dano(p["ataque"], monstro["defesa"], bonus_atk=batk)
            hp_m = max(0, hp_m - dano)
            return (hp_m, mana, hp_j, f"Sem mana! Ataque basico: **{dano} de dano**.")
    elif acao == "pocao" and val:
        hp_j, mana, linha = aplicar_efeito_pocao(val, hp_j, hp_jmx, mana, mana_mx)
        await remover_pocao(uid, val)
        return (hp_m, mana, hp_j, linha)
    else:
        dano = calc_dano(p["ataque"], monstro["defesa"], bonus_atk=batk)
        hp_m = max(0, hp_m - dano)
        return (hp_m, mana, hp_j, f"Ataque: **{dano} de dano**!")
