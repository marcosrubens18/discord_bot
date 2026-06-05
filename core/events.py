# core/events.py — Eventos do bot

import discord
from config import COR_PRIMARY


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
                    "Villa Eldoria e um RPG textual de fantasia medieval!\n\n"
                    "**O que te espera:**\n"
                    "Combate com skills e equipamentos\n"
                    "Dungeons com varios andares e chefes\n"
                    "Torneios PvP, eventos e rankings\n"
                    "Guildas com missoes semanais\n"
                    "Roletas para desbloquear racas e classes raras\n\n"
                    "**Para comecar:** Use `/criar_personagem`!\n"
                    "Apos criar seu personagem voce recebera um canal privado com guia completo."
                ),
                color=COR_PRIMARY
            )
            embed.set_footer(text="Villa Eldoria RPG — Sua jornada comeca agora!")
            await canal_bv.send(content=member.mention, embed=embed)
        except Exception as e:
            print(f"Erro boas-vindas: {e}")