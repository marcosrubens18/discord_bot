# commands/tutorial.py — Comandos de tutorial e ajuda

import discord
from discord import app_commands

from data.constantes import COR_PRIMARY


TUTORIAL_SECOES = {
    "personagem": ("✨ Seu Personagem", 0x7F77DD,
        "`/perfil` - Ver sua ficha completa\n"
        "`/inventario` - Ver seus itens\n"
        "`/skills` - Ver suas habilidades\n"
        "`/setup` - Equipar armas e armaduras\n\n"
        "Ganhe XP para subir de nível e evoluir.\n"
        "Cada nível aumenta HP, Mana, ATK e DEF automaticamente."),
    "combate": ("⚔️ Sistema de Combate", 0xE24B4A,
        "`/treinar [dificuldade]` - Batalhar contra monstros\n"
        "`/desafiar @jogador` - Duelo PvP\n"
        "`/treinar-dupla @parceiro` - Batalha em dupla (+20%)\n\n"
        "Durante a batalha: use skills, se defenda,\n"
        "use poções da mochila ou fuja.\n\n"
        "**Dificuldades:** Fácil > Médio > Difícil > Lendário"),
    "dungeons": ("🏰 Dungeons", 0x7F77DD,
        "`/dungeon` - Entrar em uma dungeon\n\n"
        "Cada dungeon tem andares com monstros diferentes.\n"
        "Derrote todos para avançar e ganhar loot.\n"
        "Se morrer, perde as recompensas do run.\n\n"
        "Masmorras vão do Rank F ao Rank SS."),
    "loja": ("🛒 Inventário e Loja", 0x1D9E75,
        "`/inventario` - Ver seus itens\n"
        "`/loja` - Comprar armas, armaduras e poções\n"
        "`/loja-sazonal` - Itens especiais e ofertas do dia\n"
        "`/ferreiro` - Forjar equipamentos raros\n"
        "`/mercado` - Vender seus itens\n\n"
        "Equipe sempre a melhor arma e armadura para sua classe!"),
    "hospital": ("🏥 Hospital e Recuperação", 0x3498DB,
        "`/hospital` - Acessar o hospital\n\n"
        "Opções de cura:\n"
        "- Comprar cura com moedas\n"
        "- Descanso grátis de 30 minutos\n"
        "- Poções durante batalhas\n\n"
        "Use o descanso grátis sempre que possível!"),
    "guildas": ("⚔️ Guildas", 0xE4AF3C,
        "`/guilda-info` - Ver informações da sua guilda\n"
        "`/guilda-missoes` - Ver missões semanais\n"
        "`/guilda-depositar` - Depositar no banco\n\n"
        "Benefícios: bônus de XP/moedas, missões semanais,\n"
        "batalhas em dupla e canal exclusivo.\n\n"
        "Para criar: `/guilda-criar` (custa 5000 moedas)"),
    "ranking": ("🏆 Rankings e Conquistas", 0xE4AF3C,
        "`/ranking` - Ver ranking do servidor\n"
        "`/conquistas` - Ver suas conquistas\n"
        "`/missoes` - Ver missões diárias\n"
        "`/historico` - Ver histórico de batalhas\n\n"
        "Rankings: nível, vitórias, rico, dungeons, torneios.\n"
        "Complete conquistas para ganhar recompensas!"),
    "eventos": ("🎉 Eventos e Torneios", 0xD85A30,
        "`/eventos` - Ver eventos ativos\n"
        "`/evento-info` - Detalhes e ranking\n\n"
        "Tipos: torneios PvP, dungeons de evento,\n"
        "eventos especiais com prêmios exclusivos.\n\n"
        "Fique de olho nos canais de anúncio!"),
    "dicas": ("💡 Dicas para Iniciantes", 0x1D9E75,
        "**Por onde começar:**\n"
        "1. Use `/loja` e compre uma arma\n"
        "2. Use `/treinar fácil` para ganhar XP\n"
        "3. Complete as `/missoes` diárias\n"
        "4. Entre numa guilda para bônus de XP\n"
        "5. Explore `/dungeon` quando estiver forte\n\n"
        "**Como evoluir rápido:**\n"
        "Faça missões diárias, participe de eventos,\n"
        "use o descanso grátis do hospital e jogue em dupla!"),
}


def setup_tutorial_commands(bot):
    """Registra os comandos de tutorial e ajuda"""

    @bot.tree.command(name="tutorial", description="Guia completo do servidor — escolha uma seção")
    @app_commands.describe(secao="Qual seção você quer ver?")
    @app_commands.choices(secao=[
        app_commands.Choice(name="✨ Personagem — perfil, skills e progressão", value="personagem"),
        app_commands.Choice(name="⚔️ Combate — treino, PvP e batalha em dupla", value="combate"),
        app_commands.Choice(name="🏰 Dungeons — masmorras e recompensas", value="dungeons"),
        app_commands.Choice(name="🛒 Loja e Inventário — itens e equipamentos", value="loja"),
        app_commands.Choice(name="🏥 Hospital — cura e recuperação", value="hospital"),
        app_commands.Choice(name="⚔️ Guildas — unir forças", value="guildas"),
        app_commands.Choice(name="🏆 Rankings e Conquistas", value="ranking"),
        app_commands.Choice(name="🎉 Eventos e Torneios", value="eventos"),
        app_commands.Choice(name="💡 Dicas para Iniciantes", value="dicas"),
    ])
    async def tutorial(interaction: discord.Interaction, secao: str = "dicas"):
        titulo, cor, desc = TUTORIAL_SECOES.get(secao, TUTORIAL_SECOES["dicas"])
        embed = discord.Embed(title=titulo, description=desc, color=cor)
        embed.set_footer(text="Villa Eldoria RPG | Use /tutorial novamente para ver outra seção")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="ajuda", description="Lista todos os comandos do RPG")
    async def ajuda(interaction: discord.Interaction):
        embed = discord.Embed(title="📋 Comandos — Villa Eldoria RPG", color=COR_PRIMARY)
        embed.add_field(name="✨ Personagem", value="`/criar_personagem` `/perfil` `/skills` `/setup` `/deletar_personagem`", inline=False)
        embed.add_field(name="📦 Inventário", value="`/inventario` `/equipar` `/jogar-fora` `/dar`", inline=False)
        embed.add_field(name="⚔️ Batalha", value="`/treinar` `/desafiar` `/dungeon` `/treinar-dupla`", inline=False)
        embed.add_field(name="💰 Economia", value="`/loja` `/loja-sazonal` `/ferreiro` `/hospital` `/mercado` `/mercador`", inline=False)
        embed.add_field(name="📈 Progresso", value="`/missoes` `/conquistas` `/ranking` `/girar`", inline=False)
        embed.add_field(name="👑 Admin", value="`/set-item` `/set-moedas` `/set-nivel` `/set-giros`", inline=False)
        embed.add_field(name="🎉 Eventos", value="`/criar-evento` `/eventos` `/evento-info` `/encerrar-evento` `/add-pontos`", inline=False)
        embed.add_field(name="📢 Anúncios", value="`/anunciar` `/anunciar-evento` `/agendar-anuncio`", inline=False)
        embed.add_field(name="⚔️ Guildas", value="`/guilda-criar` `/guilda-info` `/guilda-missoes` `/guilda-convidar` `/guilda-sair` `/guilda-promover` `/guilda-depositar` `/guilda-retirar` `/guilda-ranking`", inline=False)
        embed.add_field(name="🏆 Torneio", value="`/torneio_criar` `/torneio_inscrever` `/torneio_fechar` `/torneio_lutar` `/torneio_status` `/torneio_cancelar`", inline=False)
        embed.add_field(name="🏰 Party", value="`/party-criar` `/party-info` `/party-convidar` `/party-sair` `/party-expulsar` `/party-lider` `/party-encerrar` `/party-painel` `/party-convites`", inline=False)
        embed.add_field(name="🎫 Passe", value="`/passe_ver` `/passe_resgatar` `/passe_ranking` `/passe_recompensas`", inline=False)
        embed.add_field(name="🏆 Arena", value="`/arena_desafiar` `/arena_ranking` `/arena_meuperfil` `/arena_recompensas` `/arena_temporada`", inline=False)
        embed.add_field(name="🎲 Sorteios", value="`/sorteio_criar` `/sorteio_sortear` `/sorteio_cancelar` `/sorteio_info` `/sorteios`", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)