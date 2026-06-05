# systems/economia/mercador.py — Mercador Obscuro (Trocas)

import discord
import asyncio
import random

from database.db import get_pool
from database.queries import get_personagem
from data.ranks import get_rank
from data.itens import MATERIAIS_CAT
from data.constantes import IMG_MERCADOR


# ==================================================
# CONSTANTES
# ==================================================

COR_MERCADOR = 0x1a0a2e

RANK_ORDEM = ["F", "E", "D", "C", "B", "A", "S", "SS"]

# Itens exclusivos do Mercador
CATALOGO_MERCADOR = [
    # Rank F/E — Tônicos Básicos
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

    # Rank D/C — Elixires
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

    # Rank B/A — Itens Raros
    ("dado_destino",   "Dado do Destino",      "🎲",
     "Rerola seu Destino aleatoriamente",
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
     "Aumenta seu Poder base em +8",
     "poder_valor", 8, "A",
     [("escama_dragao", 3), ("olho_dragao", 2)]),

    # Rank S/SS — Itens Lendários
    ("essencia_classe","Essência de Classe",   "💊",
     "30% de chance de trocar sua classe aleatoriamente",
     "reroll_classe", 0, "S",
     [("essencia_lich", 1), ("escama_dragao", 3), ("olho_dragao", 2)]),

    ("ficha_lendaria", "Ficha Lendária",       "🟧",
     "Concede uma Ficha de Roleta Lendária garantida",
     "ficha_lendaria", 0, "S",
     [("essencia_lich", 1), ("corno_quimera", 1)]),

    ("elixir_supremo_p","Elixir do Transcendente","✨",
     "Aumenta ATK +10, DEF +10, HP +200, Mana +100",
     "tudo", 0, "SS",
     [("essencia_criador", 1), ("escama_dragao", 3), ("olho_dragao", 2)]),

    ("poder_absoluto", "Poder Absoluto",       "💎",
     "Aumenta Poder base em +20",
     "poder_valor", 20, "SS",
     [("essencia_criador", 1), ("fragmento_titan", 2), ("olho_dragao", 3)]),
]


# ==================================================
# FUNÇÕES AUXILIARES
# ==================================================

async def get_qtd_item(user_id: int, item_id: str) -> int:
    """Retorna a quantidade de um item no inventário"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT quantidade FROM inventario WHERE user_id = $1 AND item_id = $2",
            user_id, item_id
        )
        return row["quantidade"] if row else 0


async def remover_item(conn, user_id: int, item_id: str, quantidade: int = 1) -> bool:
    """Remove um item do inventário"""
    row = await conn.fetchrow(
        "SELECT id, quantidade FROM inventario WHERE user_id = $1 AND item_id = $2",
        user_id, item_id
    )
    if not row:
        return False
    if row["quantidade"] <= quantidade:
        await conn.execute("DELETE FROM inventario WHERE id = $1", row["id"])
    else:
        await conn.execute(
            "UPDATE inventario SET quantidade = quantidade - $1 WHERE id = $2",
            quantidade, row["id"]
        )
    return True


async def aplicar_efeito(user_id: int, item_id: str, efeito: str, valor: int, p: dict) -> str:
    """Aplica o efeito do item trocado"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        if efeito in ("hp_max", "mana_max", "ataque", "defesa", "poder_valor"):
            await conn.execute(
                f"UPDATE personagens SET {efeito} = {efeito} + $1 WHERE user_id = $2",
                valor, user_id
            )
            if efeito == "hp_max":
                await conn.execute("UPDATE personagens SET hp_atual = hp_max WHERE user_id = $1", user_id)
            if efeito == "mana_max":
                await conn.execute("UPDATE personagens SET mana_atual = mana_max WHERE user_id = $1", user_id)
            return f"+{valor} {efeito.replace('_', ' ').title()} permanente!"

        elif efeito == "tudo":
            await conn.execute("""
                UPDATE personagens
                SET ataque = ataque + 10, defesa = defesa + 10,
                    hp_max = hp_max + 200, hp_atual = hp_max + 200,
                    mana_max = mana_max + 100, mana_atual = mana_max + 100
                WHERE user_id = $1
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
            DESTINOS = ["equilibrado", "prodigio", "maldito", "guardiao", "abencado", "amaldicoado", "filho_caos"]
            novo = random.choice([d for d in DESTINOS if d != p["destino_id"]])
            await conn.execute("UPDATE personagens SET destino_id = $1 WHERE user_id = $2", novo, user_id)
            return f"Destino alterado para **{novo.replace('_', ' ').title()}**!"

        elif efeito == "reroll_classe":
            if random.random() < 0.30:
                CLASSES = ["guerreiro", "arqueiro", "mago", "paladino", "necromante", "arcano", "dracomante"]
                nova = random.choice([c for c in CLASSES if c != p["classe_id"]])
                RARIDADE_CLASSE = {
                    "guerreiro": "Comum", "arqueiro": "Comum", "mago": "Comum",
                    "paladino": "Incomum", "necromante": "Raro", "arcano": "Epico", "dracomante": "Lendario"
                }
                await conn.execute(
                    "UPDATE personagens SET classe_id = $1, raridade = $2 WHERE user_id = $3",
                    nova, RARIDADE_CLASSE[nova], user_id
                )
                return f"Classe alterada para **{nova.title()}**! (30% de chance — você teve sorte!)"
            else:
                return "A essência não reagiu... sua classe permanece a mesma."

    return "Efeito aplicado!"


# ==================================================
# COMANDO MERCADOR
# ==================================================

async def cmd_mercador(interaction: discord.Interaction):
    """Comando /mercador - Troca materiais por itens especiais"""
    await interaction.response.defer(ephemeral=True)
    
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True)
        return

    rank_atual = get_rank(p["nivel"])["rank"]
    rank_idx = RANK_ORDEM.index(rank_atual)

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

    for it in disponiveis:
        iid, nome, emoji, desc, efeito, valor, rank_min, custo = it
        custo_txt = " + ".join([f"{qtd}x {mid.replace('_', ' ').title()}" for mid, qtd in custo])
        rank_e = {"F": "🟫", "E": "🟩", "D": "🟦", "C": "🟨", "B": "🟧", "A": "🟥", "S": "⭐", "SS": "💎"}.get(rank_min, "")
        embed.add_field(
            name=f"{emoji} {nome} {rank_e}",
            value=f"*{desc}*\n**Custo:** {custo_txt}",
            inline=False
        )

    if not disponiveis:
        embed.description += "\n\n*Nenhum item disponível para seu rank ainda...*"
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    opcoes = [
        discord.SelectOption(
            label=f"{it[2]} {it[1]}",
            value=it[0],
            description=f"Rank {it[6]}+ | {it[3][:50]}"
        )
        for it in disponiveis[:25]
    ]
    
    sel = discord.ui.Select(placeholder="🕵️ Escolha o que deseja trocar...", options=opcoes)

    async def trocar(inter: discord.Interaction):
        if inter.user.id != interaction.user.id:
            await inter.response.send_message("Não é você!", ephemeral=True)
            return
        await inter.response.defer()

        item_sel = next((it for it in disponiveis if it[0] == sel.values[0]), None)
        if not item_sel:
            return

        iid, nome, emoji, desc, efeito, valor, rank_min, custo = item_sel

        pool = await get_pool()
        async with pool.acquire() as conn:
            faltando = []
            for mat_id, qtd in custo:
                row = await conn.fetchrow(
                    "SELECT quantidade FROM inventario WHERE user_id = $1 AND item_id = $2",
                    inter.user.id, mat_id
                )
                tem = row["quantidade"] if row else 0
                if tem < qtd:
                    faltando.append(f"{qtd}x {mat_id.replace('_', ' ').title()} (tem {tem})")

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

            for mat_id, qtd in custo:
                await remover_item(conn, inter.user.id, mat_id, qtd)

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
        try:
            await msg.delete()
        except:
            pass

    sel.callback = trocar
    v = discord.ui.View(timeout=120)
    v.add_item(sel)
    msg = await interaction.followup.send(embed=embed, view=v, wait=True)
    await asyncio.sleep(300)
    try:
        await msg.delete()
    except:
        pass