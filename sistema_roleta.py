# sistema_roleta.py — Sistema de Roletas e Gacha (separado do hospital)

import discord
import asyncio
import random
from typing import Optional

from db import get_pool
from data_racas import RACAS_ROLETA
from data_classes import CLASSES, PODERES
from data_skills import get_skills_classe
from data_armas import get_armas_classe
from data_armaduras import get_armaduras_classe
from constants import COR_RAR, EMOJI_FICHA, RARIDADES
from imagens import IMG_HOSPITAL


# ==================================================
# ROLETAS DISPONÍVEIS
# ==================================================

ROLETAS = {
    "classe": {
        "nome": "Classe", "emoji": "🎭",
        "pool": [
            {"id": c["id"], "nome": c["nome"], "emoji": c["emoji"], "raridade": c["raridade"], "desc": c["desc"]}
            for c in CLASSES
        ],
    },
    "skill": {
        "nome": "Skill", "emoji": "⚡",
        "pool": [],
    },
    "arma": {
        "nome": "Arma", "emoji": "⚔️",
        "pool": [],
    },
    "armadura": {
        "nome": "Armadura", "emoji": "🛡️",
        "pool": [],
    },
    "raca": {
        "nome": "Raça", "emoji": "🧬",
        "pool": [
            {"id": r["id"], "nome": r["nome"], "emoji": r["emoji"], "raridade": r["raridade"], "desc": r["desc"]}
            for r in RACAS_ROLETA
        ],
    },
    "poder": {
        "nome": "Poder base", "emoji": "💪",
        "pool": [
            {"id": p["id"], "nome": p["nome"], "emoji": p["emoji"], "valor": p["valor"], 
             "raridade": "Comum" if p["valor"] <= 18 else "Incomum" if p["valor"] <= 26 else "Raro" if p["valor"] <= 35 else "Epico" if p["valor"] <= 48 else "Lendario", 
             "desc": p.get("desc", "")}
            for p in PODERES
        ],
    },
}


# ==================================================
# FUNÇÕES AUXILIARES
# ==================================================

async def get_giros(user_id: int) -> dict:
    """Retorna os giros disponíveis do usuário"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT roleta_id, raridade, quantidade FROM giros WHERE user_id = $1 AND quantidade > 0",
            user_id
        )
    result = {}
    for r in rows:
        key = f"{r['roleta_id']}_{r['raridade']}"
        result[key] = {"roleta_id": r["roleta_id"], "raridade": r["raridade"], "quantidade": r["quantidade"]}
    return result


async def adicionar_giro(user_id: int, roleta_id: str, raridade: str, quantidade: int = 1) -> bool:
    """Adiciona giros para o usuário"""
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO giros (user_id, roleta_id, raridade, quantidade)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id, roleta_id, raridade)
                DO UPDATE SET quantidade = giros.quantidade + $4
            """, user_id, roleta_id, raridade, quantidade)
        return True
    except Exception as e:
        print(f"Erro ao adicionar giro: {e}")
        return False


async def remover_giro(user_id: int, roleta_id: str, raridade: str) -> bool:
    """Remove UM giro do usuário"""
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE giros SET quantidade = quantidade - 1
                WHERE user_id = $1 AND roleta_id = $2 AND raridade = $3 AND quantidade > 0
            """, user_id, roleta_id, raridade)
        return True
    except Exception as e:
        print(f"Erro ao remover giro: {e}")
        return False


def build_pool_filtrado(roleta_id: str, classe_id: str, ids_ja_tem: set) -> list:
    """Retorna pool filtrado: apenas itens da classe que o jogador ainda não tem"""
    if not roleta_id or not classe_id:
        return []
    
    try:
        if roleta_id == "skill":
            skills = get_skills_classe(classe_id)
            if not skills:
                return []
            
            pool_filtrado = [
                {
                    "id": s["id"],
                    "nome": s["nome"],
                    "emoji": s["emoji"],
                    "raridade": "Comum" if s["nivel"] <= 5 else ("Incomum" if s["nivel"] <= 15 else ("Raro" if s["nivel"] <= 30 else ("Epico" if s["nivel"] <= 50 else "Lendario"))),
                    "desc": s["desc"]
                }
                for s in skills if s["id"] not in ids_ja_tem
            ]
            return pool_filtrado if pool_filtrado else []

        elif roleta_id == "arma":
            armas = get_armas_classe(classe_id)
            if not armas:
                return []
            
            pool_filtrado = [
                {
                    "id": a["id"],
                    "nome": a["nome"],
                    "emoji": a["emoji"],
                    "raridade": a["raridade"],
                    "tipo": "arma",
                    "desc": a.get("desc", "")
                }
                for a in armas if a["id"] not in ids_ja_tem
            ]
            return pool_filtrado if pool_filtrado else []

        elif roleta_id == "armadura":
            armaduras = get_armaduras_classe(classe_id)
            if not armaduras:
                return []
            
            pool_filtrado = [
                {
                    "id": a["id"],
                    "nome": a["nome"],
                    "emoji": a["emoji"],
                    "raridade": a["raridade"],
                    "tipo": "armadura",
                    "desc": a.get("desc", "")
                }
                for a in armaduras if a["id"] not in ids_ja_tem
            ]
            return pool_filtrado if pool_filtrado else []

    except Exception as e:
        print(f"Erro em build_pool_filtrado: {e}")
    
    return []


def sortear_ficha(pool_items: list, raridade_minima: str) -> Optional[dict]:
    """Sorteia um item da pool baseado na raridade mínima"""
    if not pool_items:
        return None
    
    raridade_minima = raridade_minima.replace("É", "E").replace("é", "e") if raridade_minima else "Comum"
    
    try:
        idx_min = RARIDADES.index(raridade_minima) if raridade_minima in RARIDADES else 0
    except ValueError:
        idx_min = 0
    
    disponiveis = []
    for item in pool_items:
        item_rar = item.get("raridade", "Comum").replace("É", "E").replace("é", "e")
        try:
            item_idx = RARIDADES.index(item_rar)
            if item_idx >= idx_min:
                disponiveis.append(item)
        except ValueError:
            disponiveis.append(item)
    
    if not disponiveis:
        return pool_items[0] if pool_items else None
    
    pesos_base = {"Comum": 40, "Incomum": 25, "Raro": 15, "Epico": 8, "Lendario": 3}
    pesos = []
    for item in disponiveis:
        item_rar = item.get("raridade", "Comum").replace("É", "E").replace("é", "e")
        peso = pesos_base.get(item_rar, 10)
        pesos.append(peso)
    
    total = sum(pesos)
    if total <= 0:
        return disponiveis[0] if disponiveis else None
    
    r = random.random() * total
    for i, item in enumerate(disponiveis):
        r -= pesos[i]
        if r <= 0:
            return item
    
    return disponiveis[0] if disponiveis else None


async def animar_roleta(msg: discord.Message, opcoes: list, resultado: dict, cor: int):
    """Anima a roleta antes de mostrar o resultado"""
    if not opcoes or not resultado:
        return
    
    try:
        for _ in range(8):
            op = random.choice(opcoes) if opcoes else resultado
            await msg.edit(embed=discord.Embed(description=f"**{op.get('emoji', '🎰')} {op.get('nome', '???')}**", color=0x888780))
            await asyncio.sleep(0.15)
        
        valor_txt = f" — Poder {resultado.get('valor', '')}" if "valor" in resultado else ""
        desc = resultado.get("desc", "")
        embed = discord.Embed(
            title=f"{resultado.get('emoji', '🎰')} {resultado.get('nome', '???')}{valor_txt}",
            description=f"Raridade: **{resultado.get('raridade', '?')}**\n\n*{desc}*" if desc else f"Raridade: **{resultado.get('raridade', '?')}**",
            color=cor
        )
        await msg.edit(embed=embed)
    except Exception as e:
        print(f"Erro na animação da roleta: {e}")


async def get_personagem(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM personagens WHERE user_id=$1", user_id)


# ==================================================
# COMANDO GIRAR
# ==================================================

async def cmd_girar(interaction: discord.Interaction):
    """Comando /girar - Usa fichas de roleta"""
    await interaction.response.defer()
    
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True)
        return

    giros = await get_giros(interaction.user.id)
    if not giros:
        await interaction.followup.send(
            embed=discord.Embed(
                title="Sem giros disponiveis",
                description="Voce nao tem giros no momento.\n\n**Como conseguir:**\n• Admin pode conceder com `/set-giros`\n• Completar missoes especiais",
                color=0x888780
            ),
            ephemeral=True
        )
        return

    desc_giros = ""
    opcoes = []
    
    for key, info in giros.items():
        roleta = ROLETAS.get(info["roleta_id"])
        if not roleta:
            continue
        fe = EMOJI_FICHA.get(info["raridade"], "⬜")
        opcoes.append(
            discord.SelectOption(
                label=f"{fe} {roleta['nome']} — {info['raridade']} ({info['quantidade']}x)",
                value=key,
                description=f"Sorteia itens {info['raridade']} ou acima"
            )
        )
        desc_giros += f"{fe} **{roleta['nome']} {info['raridade']}**: {info['quantidade']}x\n"

    if not opcoes:
        await interaction.followup.send("Sem giros disponiveis!", ephemeral=True)
        return

    embed = discord.Embed(
        title="🎰 Seus Giros Disponíveis",
        description=f"Escolha qual ficha usar:\n\n{desc_giros}",
        color=0x7F77DD
    )
    
    sel = discord.ui.Select(placeholder="Qual ficha usar?", options=opcoes[:25])

    async def girar(inter: discord.Interaction):
        if inter.user.id != interaction.user.id:
            await inter.response.send_message("Nao e voce!", ephemeral=True)
            return
        
        key = sel.values[0]
        info = giros.get(key)
        if not info:
            await inter.followup.send("Erro: Ficha não encontrada!", ephemeral=True)
            return
        
        roleta = ROLETAS.get(info["roleta_id"])
        raridade = info["raridade"]
        
        if not roleta:
            await inter.followup.send("Erro: Roleta não encontrada!", ephemeral=True)
            return

        p_girar = await get_personagem(inter.user.id)
        if not p_girar:
            await inter.followup.send("Erro: Personagem não encontrado!", ephemeral=True)
            return
        
        classe_id_g = p_girar.get("classe_id", "guerreiro")

        pool_db2 = await get_pool()
        async with pool_db2.acquire() as conn2:
            if info["roleta_id"] == "skill":
                rows_tem = await conn2.fetch("SELECT skill_id FROM skills_desbloqueadas WHERE user_id = $1", inter.user.id)
                ids_ja_tem = {r["skill_id"] for r in rows_tem}
            else:
                rows_tem = await conn2.fetch(
                    "SELECT item_id FROM inventario WHERE user_id = $1 AND tipo = $2",
                    inter.user.id, info["roleta_id"]
                )
                ids_ja_tem = {r["item_id"] for r in rows_tem}

        if info["roleta_id"] in ("skill", "arma", "armadura"):
            pool_filtrado = build_pool_filtrado(info["roleta_id"], classe_id_g, ids_ja_tem)
        else:
            pool_filtrado = roleta["pool"]

        if not pool_filtrado:
            await inter.followup.send(
                f"⚠️ Você não pode usar esta ficha porque já possui todos os itens disponíveis!\n"
                f"**{roleta['nome']} {raridade}** não foi consumida.\n\n"
                f"Motivo: Você já possui todos os itens disponíveis desta categoria.",
                ephemeral=True
            )
            return

        resultado = sortear_ficha(pool_filtrado, raridade)

        if resultado is None:
            await inter.followup.send(
                f"❌ Erro ao sortear! Nenhum item disponível para esta roleta.\n"
                f"**{roleta['nome']} {raridade}** não foi consumida.\n\n"
                f"Por favor, reporte este erro a um administrador.",
                ephemeral=True
            )
            return

        await remover_giro(inter.user.id, info["roleta_id"], raridade)

        cor = COR_RAR.get(resultado.get("raridade", "Comum"), 0x888780)
        msg_anim = await inter.followup.send(embed=discord.Embed(description="Girando...", color=0x888780), wait=True)
        await animar_roleta(msg_anim, pool_filtrado, resultado, cor)
        await asyncio.sleep(0.5)

        aplicado = ""
        pool_db = await get_pool()
        
        async with pool_db.acquire() as conn:
            rid = info["roleta_id"]
            
            if rid == "skill":
                await conn.execute(
                    "INSERT INTO skills_desbloqueadas(user_id, skill_id) VALUES($1, $2) ON CONFLICT DO NOTHING",
                    inter.user.id, resultado["id"]
                )
                aplicado = f"Skill **{resultado['nome']}** adicionada ao seu arsenal!"
                
            elif rid in ("arma", "armadura"):
                tipo = resultado.get("tipo", rid)
                ex = await conn.fetchrow(
                    "SELECT id, quantidade FROM inventario WHERE user_id = $1 AND item_id = $2",
                    inter.user.id, resultado["id"]
                )
                if ex:
                    await conn.execute("UPDATE inventario SET quantidade = quantidade + 1 WHERE id = $1", ex["id"])
                else:
                    await conn.execute(
                        "INSERT INTO inventario(user_id, item_id, nome, tipo, raridade, emoji, descricao) VALUES($1, $2, $3, $4, $5, $6, $7)",
                        inter.user.id, resultado["id"], resultado["nome"], tipo,
                        resultado.get("raridade", "Comum"), resultado.get("emoji", "📦"), resultado.get("desc", "")
                    )
                aplicado = f"**{resultado['nome']}** adicionada ao inventario!"
                
            elif rid == "poder":
                await conn.execute(
                    "UPDATE personagens SET poder_id = $1, poder_valor = $2 WHERE user_id = $3",
                    resultado["id"], resultado.get("valor", 10), inter.user.id
                )
                aplicado = f"Poder base alterado para **{resultado['nome']}** ({resultado.get('valor', '?')})!"
                
            elif rid == "raca":
                await conn.execute(
                    "UPDATE personagens SET raca_id = $1 WHERE user_id = $2",
                    resultado["id"], inter.user.id
                )
                
                guild = inter.guild
                if guild:
                    member = guild.get_member(inter.user.id)
                    if member:
                        from data_racas import RACAS
                        raca_obj = RACAS.get(resultado["id"])
                        if raca_obj:
                            for r in RACAS.values():
                                cargo_old = discord.utils.get(guild.roles, name=r.get("cargos", ""))
                                if cargo_old and cargo_old in member.roles:
                                    try:
                                        await member.remove_roles(cargo_old)
                                    except:
                                        pass
                            cargo_new = discord.utils.get(guild.roles, name=raca_obj.get("cargos", ""))
                            if cargo_new:
                                try:
                                    await member.add_roles(cargo_new)
                                except:
                                    pass
                
                aplicado = f"Raça alterada para **{resultado['nome']}** ({resultado.get('raridade', '?')})! Passiva racial atualizada."
                
            elif rid == "classe":
                await conn.execute(
                    "UPDATE personagens SET classe_id = $1, raridade = $2 WHERE user_id = $3",
                    resultado["id"], resultado.get("raridade", "Comum"), inter.user.id
                )
                aplicado = f"Classe alterada para **{resultado['nome']}** ({resultado.get('raridade', '?')})!"

        giros_rest = await get_giros(inter.user.id)
        total_rest = sum(v["quantidade"] for v in giros_rest.values())
        fe = EMOJI_FICHA.get(raridade, "⬜")
        desc_item = resultado.get("desc", "")
        valor_txt = f" (Poder {resultado['valor']})" if "valor" in resultado else ""
        desc_txt = f"\n*{desc_item}*" if desc_item else ""
        
        await msg_anim.edit(
            embed=discord.Embed(
                title=f"Resultado — Ficha {fe} {raridade}",
                description=f"{resultado.get('emoji', '🎰')} **{resultado.get('nome', '???')}**{valor_txt}\nRaridade: **{resultado.get('raridade', '?')}**{desc_txt}\n\n{aplicado}\n\nGiros restantes: **{total_rest}**",
                color=cor
            )
        )

    sel.callback = girar
    v = discord.ui.View(timeout=60)
    v.add_item(sel)
    await interaction.followup.send(embed=embed, view=v)


# ==================================================
# COMANDO ADMIN SET GIROS
# ==================================================

async def cmd_set_giros(interaction: discord.Interaction, jogador: discord.Member):
    """Comando /set-giros - Admin: Adiciona giros a um jogador"""
    await interaction.response.defer(ephemeral=True)
    
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        p = await conn.fetchrow("SELECT * FROM personagens WHERE user_id = $1", jogador.id)
    
    if not p:
        await interaction.followup.send(f"{jogador.display_name} nao tem personagem!", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"Dar giros para {jogador.display_name}",
        description="Escolha a roleta, raridade e quantidade:",
        color=0x7F77DD
    )
    
    sel_roleta = discord.ui.Select(
        placeholder="Escolha a roleta...",
        options=[
            discord.SelectOption(label=f"{r['emoji']} {r['nome']}", value=rid, description=f"Roleta de {r['nome']}")
            for rid, r in ROLETAS.items()
        ],
        row=0
    )
    
    sel_raridade = discord.ui.Select(
        placeholder="Raridade da ficha...",
        options=[
            discord.SelectOption(label=f"{EMOJI_FICHA[rar]} Ficha {rar}", value=rar, description=f"Sorteia {rar} ou acima")
            for rar in RARIDADES
        ],
        row=1
    )
    
    sel_qtd = discord.ui.Select(
        placeholder="Quantidade...",
        options=[
            discord.SelectOption(label=f"{i}x giro(s)", value=str(i))
            for i in [1, 2, 3, 5, 10, 20]
        ],
        row=2
    )

    escolhas = {"roleta": None, "raridade": None, "qtd": 1}
    btn = discord.ui.Button(label="Confirmar", style=discord.ButtonStyle.success, disabled=True, row=3)

    async def on_roleta(inter):
        escolhas["roleta"] = sel_roleta.values[0]
        if escolhas["roleta"] and escolhas["raridade"]:
            btn.disabled = False
        await inter.response.edit_message(view=v)
    
    async def on_raridade(inter):
        escolhas["raridade"] = sel_raridade.values[0]
        if escolhas["roleta"] and escolhas["raridade"]:
            btn.disabled = False
        await inter.response.edit_message(view=v)
    
    async def on_qtd(inter):
        escolhas["qtd"] = int(sel_qtd.values[0])
        await inter.response.edit_message(view=v)
    
    async def on_confirmar(inter):
        if inter.user.id != interaction.user.id:
            return
        
        rid = escolhas["roleta"]
        rar = escolhas["raridade"]
        qtd = escolhas["qtd"]
        
        if not rid or not rar:
            await inter.response.send_message("Selecione roleta e raridade!", ephemeral=True)
            return
        
        roleta = ROLETAS.get(rid)
        if not roleta:
            await inter.response.send_message("Roleta inválida!", ephemeral=True)
            return
        
        await adicionar_giro(jogador.id, rid, rar, qtd)
        fe = EMOJI_FICHA.get(rar, "⬜")
        
        await inter.response.edit_message(
            embed=discord.Embed(
                title="Giros adicionados!",
                description=f"{fe} **{qtd}x Ficha {rar}** de **{roleta['nome']}**\nadicionado para {jogador.mention}!",
                color=COR_RAR.get(rar, 0x888780)
            ),
            view=None
        )

    sel_roleta.callback = on_roleta
    sel_raridade.callback = on_raridade
    sel_qtd.callback = on_qtd
    btn.callback = on_confirmar
    
    v = discord.ui.View(timeout=120)
    v.add_item(sel_roleta)
    v.add_item(sel_raridade)
    v.add_item(sel_qtd)
    v.add_item(btn)
    
    await interaction.followup.send(embed=embed, view=v, ephemeral=True)