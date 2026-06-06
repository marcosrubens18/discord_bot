# core_events.py — Eventos do bot

import discord

from constants import COR_PRIMARY


def setup_events(bot):
    """Registra os eventos do bot"""
    
    @bot.event
    async def on_member_join(member: discord.Member):
        """Quando um novo membro entra no servidor"""
        cargo = discord.utils.get(member.guild.roles, name="🌱 Recem-chegado")
        if cargo:
            try:
                await member.add_roles(cargo)
            except:
                pass

        try:
            canal_bv = (
                discord.utils.get(member.guild.text_channels, name="📌┃boas-vindas") or
                discord.utils.get(member.guild.text_channels, name="boas-vindas") or
                discord.utils.get(member.guild.text_channels, name="bem-vindo") or
                discord.utils.get(member.guild.text_channels, name="welcome")
            )
            if not canal_bv:
                return

            embed = discord.Embed(
                title=f"Bem-vindo a Villa Eldoria, {member.display_name}!",
                description=(
                    "Villa Eldoria é um RPG textual de fantasia medieval!\n\n"
                    "**O que te espera:**\n"
                    "⚔️ Combate com skills e equipamentos\n"
                    "🏰 Dungeons com vários andares e chefes\n"
                    "🏆 Torneios PvP, eventos e rankings\n"
                    "⚔️ Guildas com missões semanais\n"
                    "🎰 Roletas para desbloquear raças e classes raras\n\n"
                    "**Para começar:** Use `/criar_personagem`!\n"
                    "Após criar seu personagem você receberá um canal privado com guia completo."
                ),
                color=COR_PRIMARY
            )
            embed.set_footer(text="Villa Eldoria RPG — Sua jornada começa agora!")
            await canal_bv.send(content=member.mention, embed=embed)
        except Exception as e:
            print(f"Erro boas-vindas: {e}")