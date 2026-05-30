# mercado.py — Mercador Obscuro (trocas) + Mercado do Jogador (venda)
import discord
import asyncio
import random
from db import get_pool
from catalogo import get_rank
from imagens import IMG_MERCADOR, IMG_MERCADO

# ─── CORES E TEMA ────────────────────────────────────────────────
COR_MERCADOR = 0x1a0a2e
COR_MERCADO  = 0xE4AF3C
COR_RAR = {
    "Comum":0x888780,"Incomum":0x1D9E75,"Raro":0x378ADD,
    "Epico":0x7F77DD,"Lendario":0xD85A30
}
EMOJI_RAR = {
    "Comum":"⬜","Incomum":"🟩","Raro":"🟦","Epico":"🟪","Lendario":"🟧"
}

# ─── PRECO JUSTO DE VENDA ────────────────────────────────────────
PRECO_BASE = {
    "Comum":   80,
    "Incomum": 200,
    "Raro":    450,
    "Epico":   1000,
    "Lendario":3000,
}
PCT_VENDA = {
    "Comum":0.50,"Incomum":0.55,"Raro":0.60,"Epico":0.65,"Lendario":0.70
}

def calcular_preco_venda(raridade):
    base = PRECO_BASE.get(raridade, 80)
    pct  = PCT_VENDA.get(raridade, 0.50)
    return int(base * pct)

# ─── ITENS EXCLUSIVOS DO MERCADOR ────────────────────────────────
# (id, nome, emoji, desc, efeito, valor_efeito, rank_min, custo_itens)
# custo_itens = [(item_id, quantidade), ...]
CATALOGO_MERCADOR = [
    # ── Rank F/E — Tônicos Básicos ────────────────────────────────
    ("tonico_hp_p",    "Tônico Vital I",       "❤️",
     "Aumenta HP máximo permanentemente em +20",
     "hp_max", 20, "F",
     [("pele_lobo", 3), ("pedra_suja", 5)]),

    ("tonico_mana_p",  "Tônico de Mana I",     "💙",
     "Aumenta mana máxima permanentemente em +15",
     "mana_max", 15, "F",
     [("pele_lobo", 2), ("pedra_suja", 4)]),

    ("tonico_atk_p",   "Tônico de Força I",    "💪",
     "Aumenta ATK permanentemente em +2",
     "ataque", 2, "F",
     [("dente_orc", 1), ("pedra_suja", 3)]),

    ("tonico_def_p",   "Tônico de Ferro I",    "🛡️",
     "Aumenta DEF permanentemente em +2",
     "defesa", 2, "F",
     [("osso_oco", 2), ("pedra_suja", 3)]),

    # ── Rank D/C — Elixires ───────────────────────────────────────
    ("elixir_hp",      "Elixir Vital",         "🧪",
     "Aumenta HP máximo permanentemente em +50",
     "hp_max", 50, "D",
     [("fragmento_golem", 2), ("dente_orc", 3)]),

    ("elixir_mana",    "Elixir de Mana",       "🧿",
     "Aumenta mana máxima permanentemente em +30",
     "mana_max", 30, "D",
     [("sangue_anciao", 1), ("dente_orc", 2)]),

    ("elixir_atk",     "Elixir de Força",      "⚔️",
     "Aumenta ATK permanentemente em +5",
     "ataque", 5, "C",
     [("fragmento_golem", 1), ("sangue_anciao", 1)]),

    ("elixir_def",     "Elixir de Aço",        "🛡️",
     "Aumenta DEF permanentemente em +5",
     "defesa", 5, "C",
     [("nucleo_pedra", 1), ("fragmento_golem", 2)]),

    ("tonico_hp_m",    "Tônico Vital II",      "❤️",
     "Aumenta HP máximo permanentemente em +80",
     "hp_max", 80, "C",
     [("sangue_anciao", 2), ("fragmento_golem", 3)]),

    ("tonico_mana_m",  "Tônico de Mana II",    "💙",
     "Aumenta mana máxima permanentemente em +50",
     "mana_max", 50, "C",
     [("sangue_anciao", 1), ("nucleo_pedra", 1)]),

    # ── Rank B/A — Itens Raros ────────────────────────────────────
    ("dado_destino",   "Dado do Destino",      "🎲",
     "Rerola seu Destino aleatoriamente (pode melhorar ou piorar!)",
     "reroll_destino", 0, "B",
     [("escama_dragao", 1), ("sangue_anciao", 2)]),

    ("carta_obscura",  "Carta Obscura",        "🃏",
     "Concede uma Ficha de Roleta Épica garantida",
     "ficha_epica", 0, "B",
     [("olho_dragao", 1), ("escama_dragao", 1)]),

    ("elixir_hp_g",    "Grande Elixir Vital",  "❤️",
     "Aumenta HP máximo permanentemente em +150",
     "hp_max", 150, "A",
     [("escama_dragao", 2), ("olho_dragao", 1)]),

    ("elixir_mana_g",  "Grande Elixir de Mana","💙",
     "Aumenta mana máxima permanentemente em +80",
     "mana_max", 80, "A",
     [("olho_dragao", 1), ("sangue_anciao", 2), ("escama_dragao", 1)]),

    ("fragmento_poder","Fragmento de Poder",   "🌟",
     "Aumenta seu Poder base em +8 (ATK, DEF e HP escalam junto)",
     "poder_valor", 8, "A",
     [("escama_dragao", 3), ("olho_dragao", 2)]),

    # ── Rank S/SS — Itens Lendários ───────────────────────────────
    ("essencia_classe","Essência de Classe",   "💊",
     "30% de chance de trocar sua classe aleatoriamente mantendo o nível",
     "reroll_classe", 0, "S",
     [("essencia_lich", 1), ("escama_dragao", 3), ("olho_dragao", 2)]),

    ("ficha_lendaria", "Ficha Lendária",       "🟧",
     "Concede uma Ficha de Roleta Lendária garantida",
     "ficha_lendaria", 0, "S",
     [("essencia_lich", 1), ("corno_quimera", 1)]),

    ("elixir_supremo_p","Elixir do Transcendente","✨",
     "Aumenta ATK +10, DEF +10, HP +200, Mana +100 permanentemente",
     "tudo", 0, "SS",
     [("essencia_criador", 1), ("escama_dragao", 3), ("olho_dragao", 2)]),

    ("poder_absoluto", "Poder Absoluto",       "💎",
     "Aumenta Poder base em +20 — O maior tônico existente",
     "poder_valor", 20, "SS",
     [("essencia_criador", 1), ("fragmento_titan", 2), ("olho_dragao", 3)]),
]

RANK_ORDEM = ["F","E","D","C","B","A","S","SS"]

# ─── DB HELPERS ──────────────────────────────────────────────────

async def get_personagem(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM personagens WHERE user_id=$1", user_id)

async def get_inventario_completo(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM inventario WHERE user_id=$1 ORDER BY raridade DESC, nome",
            user_id
        )

async def get_qtd_item(user_id, item_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT quantidade FROM inventario WHERE user_id=$1 AND item_id=$2",
            user_id, item_id
        )
        return row["quantidade"] if row else 0

async def remover_item(conn, user_id, item_id, quantidade=1):
    row = await conn.fetchrow(
        "SELECT id, quantidade FROM inventario WHERE user_id=$1 AND item_id=$2",
        user_id, item_id
    )
    if not row:
        return False
    if row["quantidade"] <= quantidade:
        await conn.execute("DELETE FROM inventario WHERE id=$1", row["id"])
    else:
        await conn.execute(
            "UPDATE inventario SET quantidade=quantidade-$1 WHERE id=$2",
            quantidade, row["id"]
        )
    return True

# ─── APLICAR EFEITO DO ITEM MERCADOR ─────────────────────────────

async def aplicar_efeito(user_id, item_id, efeito, valor, p):
    pool = await get_pool()
    async with pool.acquire() as conn:
        if efeito in ("hp_max","mana_max","ataque","defesa","poder_valor"):
            await conn.execute(
                f"UPDATE personagens SET {efeito}={efeito}+$1 WHERE user_id=$2",
                valor, user_id
            )
            # Se aumentou hp_max, restaura hp_atual junto
            if efeito == "hp_max":
                await conn.execute(
                    "UPDATE personagens SET hp_atual=hp_max WHERE user_id=$1",
                    user_id
                )
            if efeito == "mana_max":
                await conn.execute(
                    "UPDATE personagens SET mana_atual=mana_max WHERE user_id=$1",
                    user_id
                )
            return f"+{valor} {efeito.replace('_',' ').title()} permanente!"

        elif efeito == "tudo":
            await conn.execute("""
                UPDATE personagens
                SET ataque=ataque+10, defesa=defesa+10,
                    hp_max=hp_max+200, hp_atual=hp_max+200,
                    mana_max=mana_max+100, mana_atual=mana_max+100
                WHERE user_id=$1
            """, user_id)
            return "+10 ATK | +10 DEF | +200 HP | +100 Mana — tudo permanente!"

        elif efeito == "ficha_epica":
            await conn.execute("""
                INSERT INTO giros (user_id, roleta_id, raridade, quantidade)
                VALUES ($1, 'skill', 'Epico', 1)
                ON CONFLICT (user_id, roleta_id, raridade)
                DO UPDATE SET quantidade = giros.quantidade + 1
            """, user_id)
            return "Ficha de Roleta Épica adicionada! Use /girar"

        elif efeito == "ficha_lendaria":
            await conn.execute("""
                INSERT INTO giros (user_id, roleta_id, raridade, quantidade)
                VALUES ($1, 'skill', 'Lendario', 1)
                ON CONFLICT (user_id, roleta_id, raridade)
                DO UPDATE SET quantidade = giros.quantidade + 1
            """, user_id)
            return "Ficha de Roleta Lendária adicionada! Use /girar"

        elif efeito == "reroll_destino":
            DESTINOS = ["equilibrado","prodigio","maldito","guardiao","abencado","amaldicoado","filho_caos"]
            novo = random.choice([d for d in DESTINOS if d != p["destino_id"]])
            await conn.execute(
                "UPDATE personagens SET destino_id=$1 WHERE user_id=$2",
                novo, user_id
            )
            return f"Destino alterado para **{novo.replace('_',' ').title()}**!"

        elif efeito == "reroll_classe":
            if random.random() < 0.30:
                CLASSES = ["guerreiro","arqueiro","mago","paladino","necromante","arcano","dracomante"]
                nova = random.choice([c for c in CLASSES if c != p["classe_id"]])
                RARIDADE_CLASSE = {
                    "guerreiro":"Comum","arqueiro":"Comum","mago":"Comum",
                    "paladino":"Incomum","necromante":"Raro","arcano":"Epico","dracomante":"Lendario"
                }
                await conn.execute(
                    "UPDATE personagens SET classe_id=$1, raridade=$2 WHERE user_id=$3",
                    nova, RARIDADE_CLASSE[nova], user_id
                )
                return f"Classe alterada para **{nova.title()}**! (30% de chance — você teve sorte!)"
            else:
                return "A essência não reagiu... sua classe permanece a mesma. (Tentou, mas não teve sorte desta vez)"

    return "Efeito aplicado!"

# ─── CMD MERCADOR OBSCURO ────────────────────────────────────────

async def cmd_mercador(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True)
        return

    rank_atual = get_rank(p["nivel"])["rank"]
    rank_idx   = RANK_ORDEM.index(rank_atual)

    # Filtra itens disponíveis pelo rank
    disponiveis = [
        it for it in CATALOGO_MERCADOR
        if RANK_ORDEM.index(it[6]) <= rank_idx
    ]

    embed = discord.Embed(
        title="🕵️ O Mercador Sombrio",
        description=(
            f"*\"Psst... aventureiro. Tenho coisas que nenhuma loja comum oferece...\"\n\n"
            f"Seu Rank: **{rank_atual}** | Nível: **{p['nivel']}**\n\n"
            f"Estes itens não podem ser comprados com moedas.\n"
            f"**Só aceito trocas por materiais raros.**\n\n"
            f"*Itens com rank maior desbloqueiam conforme você evolui.*"
        ),
        color=COR_MERCADOR
    )
    embed.set_image(url=IMG_MERCADOR)

    # Lista itens com custo
    for it in disponiveis:
        iid, nome, emoji, desc, efeito, valor, rank_min, custo = it
        custo_txt = " + ".join([f"{qtd}x {mid.replace('_',' ').title()}" for mid, qtd in custo])
        rank_e = {"F":"🟫","E":"🟩","D":"🟦","C":"🟨","B":"🟧","A":"🟥","S":"⭐","SS":"💎"}.get(rank_min,"")
        embed.add_field(
            name=f"{emoji} {nome} {rank_e}",
            value=f"*{desc}*\n**Custo:** {custo_txt}",
            inline=False
        )

    if not disponiveis:
        embed.description += "\n\n*Nenhum item disponível para seu rank ainda...*"
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    # Select para escolher item
    opcoes = [
        discord.SelectOption(
            label=f"{it[2]} {it[1]}",
            value=it[0],
            description=f"Rank {it[6]}+ | {it[3][:50]}"
        ) for it in disponiveis[:25]
    ]
    sel = discord.ui.Select(placeholder="🕵️ Escolha o que deseja trocar...", options=opcoes)

    async def trocar(inter: discord.Interaction):
        if inter.user.id != interaction.user.id:
            await inter.response.send_message("Não é você!", ephemeral=True); return
        await inter.response.defer()

        item_sel = next((it for it in disponiveis if it[0] == sel.values[0]), None)
        if not item_sel: return

        iid, nome, emoji, desc, efeito, valor, rank_min, custo = item_sel

        # Verifica se tem os materiais
        pool = await get_pool()
        async with pool.acquire() as conn:
            faltando = []
            for mat_id, qtd in custo:
                row = await conn.fetchrow(
                    "SELECT quantidade FROM inventario WHERE user_id=$1 AND item_id=$2",
                    inter.user.id, mat_id
                )
                tem = row["quantidade"] if row else 0
                if tem < qtd:
                    faltando.append(f"{qtd}x {mat_id.replace('_',' ').title()} (tem {tem})")

            if faltando:
                await inter.followup.send(
                    embed=discord.Embed(
                        title="❌ Materiais insuficientes!",
                        description=f"*\"Você não tem o suficiente, aventureiro...\"*\n\n**Faltam:**\n" + "\n".join(f"• {f}" for f in faltando),
                        color=0xE24B4A
                    ),
                    ephemeral=True
                )
                return

            # Remove materiais
            for mat_id, qtd in custo:
                await remover_item(conn, inter.user.id, mat_id, qtd)

        # Aplica efeito
        p2 = await get_personagem(inter.user.id)
        resultado = await aplicar_efeito(inter.user.id, iid, efeito, valor, p2)

        embed_ok = discord.Embed(
            title=f"✅ Troca realizada! {emoji} {nome}",
            description=(
                f"*\"Excelente escolha... foi um prazer negociar.\"*\n\n"
                f"**Resultado:** {resultado}\n\n"
                f"*Os materiais foram consumidos pelo Mercador Sombrio.*"
            ),
            color=COR_MERCADOR
        )
        msg = await inter.followup.send(embed=embed_ok, wait=True)
        await asyncio.sleep(300)
        try: await msg.delete()
        except: pass

    sel.callback = trocar
    v = discord.ui.View(timeout=120)
    v.add_item(sel)
    msg = await interaction.followup.send(embed=embed, view=v, wait=True)
    await asyncio.sleep(300)
    try: await msg.delete()
    except: pass


# ─── CMD MERCADO JOGADOR ─────────────────────────────────────────

async def cmd_mercado_vender(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True); return

    itens = await get_inventario_completo(interaction.user.id)
    vendaveis = [i for i in itens if not i["equipado"]]

    if not vendaveis:
        await interaction.followup.send(
            embed=discord.Embed(
                title="🏪 Mercado — Vender Item",
                description="Você não tem itens disponíveis para venda.\n*(Itens equipados não podem ser vendidos)*",
                color=0x888780
            ),
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="🏪 Mercado — Vender Item",
        description=(
            f"Selecione um item para vender.\n"
            f"Os preços são calculados pelo mercado com base na raridade.\n\n"
            f"Moedas atuais: **{p['moedas']} 🪙**"
        ),
        color=COR_MERCADO
    )
    embed.set_image(url=IMG_MERCADO)

    # Mostra tabela de preços
    preco_txt = " | ".join([f"{EMOJI_RAR[r]} {calcular_preco_venda(r)}🪙" for r in ["Comum","Incomum","Raro","Epico","Lendario"]])
    embed.add_field(name="📊 Preços de mercado", value=preco_txt, inline=False)

    opcoes = []
    for it in vendaveis[:25]:
        preco = calcular_preco_venda(it["raridade"])
        rar_e = EMOJI_RAR.get(it["raridade"], "⬜")
        qtd_txt = f" (x{it['quantidade']})" if it["quantidade"] > 1 else ""
        opcoes.append(discord.SelectOption(
            label=f"{it['emoji']} {it['nome']}{qtd_txt}",
            value=str(it["id"]),
            description=f"{rar_e} {it['raridade']} — Vende por {preco} 🪙"
        ))

    sel = discord.ui.Select(placeholder="Escolha o item para vender...", options=opcoes)

    async def confirmar_venda(inter: discord.Interaction):
        if inter.user.id != interaction.user.id:
            await inter.response.send_message("Não é você!", ephemeral=True); return
        await inter.response.defer()

        item_id_db = int(sel.values[0])
        item = next((i for i in vendaveis if i["id"] == item_id_db), None)
        if not item:
            await inter.followup.send("Item não encontrado!", ephemeral=True); return

        preco = calcular_preco_venda(item["raridade"])
        rar_e = EMOJI_RAR.get(item["raridade"], "⬜")

        # Botão de confirmação
        embed_conf = discord.Embed(
            title="⚠️ Confirmar venda?",
            description=(
                f"{item['emoji']} **{item['nome']}**\n"
                f"{rar_e} {item['raridade']}\n\n"
                f"Você receberá: **{preco} 🪙**\n\n"
                f"*Esta ação não pode ser desfeita!*"
            ),
            color=0xE4AF3C
        )

        class ConfView(discord.ui.View):
            def __init__(self): super().__init__(timeout=30)

            @discord.ui.button(label="✅ Confirmar", style=discord.ButtonStyle.success)
            async def sim(self, inter2: discord.Interaction, b):
                if inter2.user.id != interaction.user.id: return
                await inter2.response.defer()
                pool = await get_pool()
                async with pool.acquire() as conn:
                    row = await conn.fetchrow("SELECT id, quantidade FROM inventario WHERE id=$1", item_id_db)
                    if not row:
                        await inter2.followup.send("Item não encontrado!", ephemeral=True); return
                    if row["quantidade"] > 1:
                        await conn.execute("UPDATE inventario SET quantidade=quantidade-1 WHERE id=$1", item_id_db)
                    else:
                        await conn.execute("DELETE FROM inventario WHERE id=$1", item_id_db)
                    await conn.execute("UPDATE personagens SET moedas=moedas+$1 WHERE user_id=$2", preco, inter2.user.id)

                p3 = await get_personagem(inter2.user.id)
                embed_ok = discord.Embed(
                    title="✅ Item vendido!",
                    description=(
                        f"{item['emoji']} **{item['nome']}** vendido!\n\n"
                        f"+**{preco} 🪙** recebidos\n"
                        f"Saldo atual: **{p3['moedas']} 🪙**"
                    ),
                    color=0x1D9E75
                )
                msg_ok = await inter2.followup.send(embed=embed_ok, wait=True)
                await asyncio.sleep(300)
                try: await msg_ok.delete()
                except: pass
                self.stop()

            @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.danger)
            async def nao(self, inter2: discord.Interaction, b):
                if inter2.user.id != interaction.user.id: return
                await inter2.response.edit_message(content="Cancelado.", embed=None, view=None)
                self.stop()

        await inter.followup.send(embed=embed_conf, view=ConfView(), ephemeral=True)

    sel.callback = confirmar_venda
    v = discord.ui.View(timeout=120)
    v.add_item(sel)
    msg = await interaction.followup.send(embed=embed, view=v, wait=True)
    await asyncio.sleep(300)
    try: await msg.delete()
    except: pass
