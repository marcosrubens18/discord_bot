# anuncios.py — Sistema de Anuncios completo
import discord
import asyncio
from datetime import datetime, timedelta
from db import get_pool

# ─── CORES DISPONIVEIS ────────────────────────────────────────────
CORES = {
    "dourado":   0xE4AF3C,
    "roxo":      0x7F77DD,
    "verde":     0x1D9E75,
    "azul":      0x378ADD,
    "vermelho":  0xE24B4A,
    "laranja":   0xD85A30,
    "cinza":     0x888780,
    "preto":     0x23272A,
}

# ─── MODAL ANUNCIO SIMPLES ────────────────────────────────────────

class AnuncioModal(discord.ui.Modal, title="Criar Anuncio"):
    titulo = discord.ui.TextInput(
        label="Titulo",
        placeholder="Ex: Manutencao programada",
        max_length=80
    )
    mensagem = discord.ui.TextInput(
        label="Mensagem",
        style=discord.TextStyle.paragraph,
        placeholder="Conteudo do anuncio...",
        max_length=1500
    )
    imagem_url = discord.ui.TextInput(
        label="URL da Imagem (opcional)",
        placeholder="https://i.imgur.com/...",
        required=False,
        max_length=200
    )
    rodape = discord.ui.TextInput(
        label="Rodape (opcional)",
        placeholder="Ex: Villa Eldoria — Staff",
        required=False,
        max_length=100
    )

    def __init__(self, canal: discord.TextChannel, cor: int, ping_cargo: discord.Role = None):
        super().__init__()
        self.canal      = canal
        self.cor        = cor
        self.ping_cargo = ping_cargo

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        embed = discord.Embed(
            title=str(self.titulo),
            description=str(self.mensagem),
            color=self.cor
        )
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url
        )
        if str(self.imagem_url):
            embed.set_image(url=str(self.imagem_url))
        if str(self.rodape):
            embed.set_footer(text=str(self.rodape))
        else:
            embed.set_footer(text=f"Villa Eldoria • {datetime.utcnow().strftime('%d/%m/%Y %H:%M')} UTC")

        ping_txt = ""
        if self.ping_cargo:
            if self.ping_cargo.name == "@everyone":
                ping_txt = "@everyone"
            else:
                ping_txt = self.ping_cargo.mention

        await self.canal.send(content=ping_txt or None, embed=embed)
        await interaction.followup.send(
            f"✅ Anuncio enviado em {self.canal.mention}!",
            ephemeral=True
        )


# ─── MODAL ANUNCIO DE EVENTO ──────────────────────────────────────

class AnuncioEventoModal(discord.ui.Modal, title="Anuncio de Evento"):
    titulo = discord.ui.TextInput(
        label="Titulo do Evento",
        placeholder="Ex: Torneio de Natal 2026",
        max_length=80
    )
    descricao = discord.ui.TextInput(
        label="Descricao",
        style=discord.TextStyle.paragraph,
        placeholder="Detalhes do evento, regras, premios...",
        max_length=1000
    )
    premio = discord.ui.TextInput(
        label="Premio",
        placeholder="Ex: 10.000 moedas + Classe Dracomante",
        max_length=200
    )
    data_hora = discord.ui.TextInput(
        label="Data e Hora (DD/MM HH:MM)",
        placeholder="Ex: 25/12 20:00",
        max_length=20
    )
    imagem_url = discord.ui.TextInput(
        label="URL da Imagem (opcional)",
        required=False,
        max_length=200
    )

    def __init__(self, canal: discord.TextChannel, ping_cargo: discord.Role = None):
        super().__init__()
        self.canal      = canal
        self.ping_cargo = ping_cargo

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # Tenta parsear a data
        data_str = str(self.data_hora).strip()
        timestamp_txt = data_str
        try:
            ano = datetime.utcnow().year
            dt = datetime.strptime(f"{data_str} {ano}", "%d/%m %H:%M %Y")
            ts = int(dt.timestamp()) + 3*3600  # UTC-3
            timestamp_txt = f"<t:{ts}:F> (<t:{ts}:R>)"
        except:
            pass

        embed = discord.Embed(
            title=f"🎉 {str(self.titulo)}",
            description=str(self.descricao),
            color=0xE4AF3C
        )
        embed.add_field(name="🏆 Premio",       value=str(self.premio),    inline=False)
        embed.add_field(name="📅 Data e Hora",  value=timestamp_txt,       inline=False)
        embed.add_field(name="📋 Como Participar", value="Use `/eventos` para ver detalhes e participar!", inline=False)
        embed.set_author(
            name=f"Villa Eldoria — Evento Oficial",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else discord.Embed.Empty
        )
        embed.set_footer(text="Boa sorte a todos! • Villa Eldoria RPG")
        if str(self.imagem_url):
            embed.set_image(url=str(self.imagem_url))

        ping_txt = ""
        if self.ping_cargo:
            ping_txt = "@everyone" if self.ping_cargo.name == "@everyone" else self.ping_cargo.mention

        await self.canal.send(content=ping_txt or None, embed=embed)
        await interaction.followup.send(
            f"✅ Anuncio de evento enviado em {self.canal.mention}!",
            ephemeral=True
        )


# ─── MODAL ANUNCIO AGENDADO ───────────────────────────────────────

class AgendarAnuncioModal(discord.ui.Modal, title="Agendar Anuncio"):
    titulo = discord.ui.TextInput(label="Titulo", max_length=80)
    mensagem = discord.ui.TextInput(
        label="Mensagem",
        style=discord.TextStyle.paragraph,
        max_length=1500
    )
    quando = discord.ui.TextInput(
        label="Quando enviar? (minutos a partir de agora)",
        placeholder="Ex: 60 (daqui 1 hora) | 1440 (daqui 1 dia)",
        max_length=6
    )
    imagem_url = discord.ui.TextInput(
        label="URL da Imagem (opcional)",
        required=False,
        max_length=200
    )

    def __init__(self, canal: discord.TextChannel, cor: int):
        super().__init__()
        self.canal = canal
        self.cor   = cor

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            minutos = max(1, int(str(self.quando)))
        except:
            minutos = 60

        embed = discord.Embed(
            title=str(self.titulo),
            description=str(self.mensagem),
            color=self.cor
        )
        embed.set_footer(text=f"Villa Eldoria • Agendado por {interaction.user.display_name}")
        if str(self.imagem_url):
            embed.set_image(url=str(self.imagem_url))

        envio = datetime.utcnow() + timedelta(minutes=minutos)
        horas = minutos // 60
        mins  = minutos % 60
        tempo_txt = f"{horas}h {mins}min" if horas else f"{mins} minutos"

        await interaction.followup.send(
            f"✅ Anuncio agendado para daqui **{tempo_txt}** em {self.canal.mention}!",
            ephemeral=True
        )

        async def _enviar():
            await asyncio.sleep(minutos * 60)
            await self.canal.send(embed=embed)

        asyncio.create_task(_enviar())


# ─── COMANDOS EXPORTADOS ──────────────────────────────────────────

async def cmd_anunciar(interaction: discord.Interaction, canal: discord.TextChannel,
                        cor: str, ping: discord.Role = None):
    cor_hex = CORES.get(cor, 0x7F77DD)
    modal   = AnuncioModal(canal, cor_hex, ping)
    await interaction.response.send_modal(modal)


async def cmd_anunciar_evento(interaction: discord.Interaction, canal: discord.TextChannel,
                               ping: discord.Role = None):
    modal = AnuncioEventoModal(canal, ping)
    await interaction.response.send_modal(modal)


async def cmd_agendar_anuncio(interaction: discord.Interaction, canal: discord.TextChannel,
                               cor: str):
    cor_hex = CORES.get(cor, 0x7F77DD)
    modal   = AgendarAnuncioModal(canal, cor_hex)
    await interaction.response.send_modal(modal)
