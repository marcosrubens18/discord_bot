# commands/jogador.py — Comandos de personagem

import discord
from discord import app_commands

from database.queries import get_personagem, get_skills_desbloqueadas, get_skills_equipadas
from data.racas import get_raca
from data.classes import CLASSES
from data.skills import SKILLS_COMPLETAS
from data.constantes import EMOJI_CLASSE, COR_RAR, IMG_PERFIL
from data.ranks import get_rank
from systems.personagem import criar_personagem
from systems.inventario import cmd_inventario, cmd_equipar, cmd_jogar_fora, cmd_dar
from systems.combate import GerenciarSkillsView


def setup_jogador_commands(bot):
    """Registra todos os comandos de jogador"""

    @bot.tree.command(name="criar_personagem", description="Crie seu personagem para começar a jogar!")
    async def criar_personagem_cmd(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        sucesso, raca, classe = await criar_personagem(interaction)
        if sucesso:
            await interaction.followup.send("✅ Personagem criado com sucesso! Use `/perfil` para ver seus dados.", ephemeral=True)
        else:
            # Mensagem já foi enviada dentro da função
            pass

    @bot.tree.command(name="perfil", description="Mostra a ficha do seu personagem")
    @app_commands.describe(jogador="Jogador (opcional)")
    async def perfil(interaction: discord.Interaction, jogador: discord.Member = None):
        await interaction.response.defer()
        alvo = jogador or interaction.user
        p = await get_personagem(alvo.id)
        if not p:
            await interaction.followup.send("Personagem não encontrado!", ephemeral=True)
            return
        
        cls = next((c for c in CLASSES if c["id"] == p["classe_id"]), None)
        raca_p = get_raca(p["raca_id"] if p["raca_id"] else "humano")
        rank_i = get_rank(p["nivel"])
        
        pool = await get_pool()
        async with pool.acquire() as conn:
            arma = await conn.fetchrow("SELECT * FROM inventario WHERE user_id = $1 AND tipo = 'arma' AND equipado = 1", alvo.id)
            arm = await conn.fetchrow("SELECT * FROM inventario WHERE user_id = $1 AND tipo = 'armadura' AND equipado = 1", alvo.id)
            ids_eq = await conn.fetch("SELECT skill_id FROM skills_equipadas WHERE user_id = $1 ORDER BY slot", alvo.id)
        
        sk_nomes = []
        for r in ids_eq:
            for sk in SKILLS_COMPLETAS.get(p["classe_id"], []):
                if sk["id"] == r["skill_id"]:
                    sk_nomes.append(f"{sk['emoji']} {sk['nome']}")
                    break
        
        xp_need = 100 + (p["nivel"] - 1) * 50
        
        embed = discord.Embed(
            title=f"{cls['emoji'] if cls else '?'} {p['nome']}",
            description=(
                f"**Raça:** {raca_p['emoji']} {raca_p['nome']}\n"
                f"**Classe:** {cls['nome'] if cls else p['classe_id']} — *{p['raridade']}*\n"
                f"**Rank:** {rank_i['emoji']} {rank_i['rank']} — {rank_i['nome']}\n"
                f"**Nível:** {p['nivel']} | XP: {p['xp']}/{xp_need}"
            ),
            color=COR_RAR.get(p["raridade"], 0x888780)
        )
        embed.add_field(name="📊 Stats", value=f"❤️ {p['hp_atual']}/{p['hp_max']} | ⚔️ {p['ataque']} | 🛡️ {p['defesa']} | 💙 {p['mana_atual']}/{p['mana_max']}", inline=False)
        embed.add_field(name="⚔️ Equipamento", value=f"⚔️ {arma['nome'] if arma else 'Sem arma'} | 🛡️ {arm['nome'] if arm else 'Sem armadura'}", inline=False)
        if sk_nomes:
            embed.add_field(name="✨ Skills", value=" | ".join(sk_nomes), inline=False)
        embed.add_field(name=f"{raca_p['emoji']} Passiva Racial", value=raca_p['passiva_desc'], inline=False)
        embed.add_field(name="💰 Moedas", value=f"{p['moedas']} 🪙", inline=True)
        embed.add_field(name="🏆 Vitórias", value=str(p.get('vitorias', 0)), inline=True)
        embed.set_thumbnail(url=alvo.display_avatar.url)
        embed.set_image(url=IMG_PERFIL)
        
        await interaction.followup.send(embed=embed)

    @bot.tree.command(name="inventario", description="Mostra seu inventário completo")
    @app_commands.describe(jogador="Jogador (opcional)")
    async def inventario(interaction: discord.Interaction, jogador: discord.Member = None):
        await cmd_inventario(interaction, jogador)

    @bot.tree.command(name="equipar", description="Equipa um item do inventário pelo nome")
    @app_commands.describe(item="Nome do item a equipar")
    async def equipar(interaction: discord.Interaction, item: str):
        await cmd_equipar(interaction, item)

    @bot.tree.command(name="jogar-fora", description="Descarta um item do inventário")
    @app_commands.describe(item="Nome do item a descartar")
    async def jogar_fora(interaction: discord.Interaction, item: str):
        await cmd_jogar_fora(interaction, item)

    @bot.tree.command(name="dar", description="Dá um item para outro jogador")
    @app_commands.describe(jogador="Jogador que recebe", item="Nome do item")
    async def dar(interaction: discord.Interaction, jogador: discord.Member, item: str):
        await cmd_dar(interaction, jogador, item)

    @bot.tree.command(name="skills", description="Veja e gerencie suas skills equipadas")
    async def skills(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        p = await get_personagem(interaction.user.id)
        if not p:
            await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True)
            return
        
        todas = SKILLS_COMPLETAS.get(p["classe_id"], [])
        ids_desbloq = await get_skills_desbloqueadas(interaction.user.id)
        ids_eq = await get_skills_equipadas(interaction.user.id)
        
        disp = [s for s in todas if s["id"] in ids_desbloq]
        if not disp:
            await interaction.followup.send("Nenhuma skill desbloqueada ainda!", ephemeral=True)
            return
        
        view = GerenciarSkillsView(interaction.user.id, disp, ids_eq)
        embed = discord.Embed(title="✨ Gerenciar Skills", description="Selecione até 4 skills para equipar:", color=0x7F77DD)
        for s in disp:
            mana_txt = f" | {s['mana']} mana" if s.get('mana') else ''
            embed.add_field(name=f"{s['emoji']} {s['nome']} (Nv{s['nivel']})", value=f"{s['desc']}{mana_txt}", inline=True)
        
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @bot.tree.command(name="deletar_personagem", description="Deleta seu personagem permanentemente")
    async def deletar_personagem(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        p = await get_personagem(interaction.user.id)
        if not p:
            await interaction.followup.send("Você não tem personagem!", ephemeral=True)
            return
        
        class ConfView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)
                self.ok = None
            
            @discord.ui.button(label="✅ Confirmar deleção", style=discord.ButtonStyle.danger)
            async def sim(self, inter, b):
                if inter.user.id != interaction.user.id:
                    return
                self.ok = True
                await inter.response.defer()
                self.stop()
            
            @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
            async def nao(self, inter, b):
                self.ok = False
                await inter.response.defer()
                self.stop()
        
        v = ConfView()
        await interaction.followup.send("⚠️ **ATENÇÃO:** Isso apaga seu personagem permanentemente! Confirma?", view=v, ephemeral=True)
        await v.wait()
        
        if not v.ok:
            await interaction.followup.send("❌ Deleção cancelada.", ephemeral=True)
            return
        
        pool = await get_pool()
        async with pool.acquire() as conn:
            for t in ["skills_equipadas", "skills_desbloqueadas", "inventario", "missoes_diarias", "conquistas", "giros"]:
                try:
                    await conn.execute(f"DELETE FROM {t} WHERE user_id = $1", interaction.user.id)
                except:
                    pass
            await conn.execute("DELETE FROM personagens WHERE user_id = $1", interaction.user.id)
        
        await interaction.followup.send("🗑️ Personagem deletado. Use `/criar_personagem` para recomeçar.", ephemeral=True)


# Import necessário para get_pool
from database.db import get_pool