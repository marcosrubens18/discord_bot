# -*- coding: utf-8 -*-
import sys, io, os, random, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import discord
from discord import app_commands
from discord.ext import commands

from db import get_pool, init_db
from catalogo import (
    get_rank, CARGOS_RANK, calcular_mana_max,
    get_armas_classe, get_armaduras_classe,
    get_catalogo_completo, get_item_por_chave, get_itens_por_categoria
)
from utils import atualizar_cargo_nivel, atualizar_cargo_rank, atualizar_todos_cargos
from setup_cmd import cmd_setup
from dungeon import cmd_dungeon
from party import register_party_commands, init_db_party
from hospital import cmd_hospital, cmd_girar, cmd_set_giros, init_db_hospital, COR_RAR, EMOJI_FICHA
from batalha import (
    rodar_pvp, rodar_treino, MONSTROS, SKILLS_POR_CLASSE, BATALHAS_ATIVAS,
    get_skills_eq, get_skills_desbloq, GerenciarSkillsView,
    AceitarDueloView, EscolherArenaView, init_db_batalha,
    ARENAS, LOJA_ITENS, RECEITAS, POCOES
)
from missoes import cmd_missoes, cmd_ranking, init_db_missoes, atualizar_progresso
from conquistas import cmd_conquistas, init_conquistas, verificar_conquistas
from eventos import cmd_criar_evento, cmd_eventos, cmd_evento_info, cmd_encerrar_evento, cmd_add_pontos, init_db_eventos
from anuncios import cmd_anunciar, cmd_anunciar_evento, cmd_agendar_anuncio, CORES
from loja_sazonal import (cmd_loja_sazonal, cmd_loja_sazonal_remover, LojaItemModal, LojaRotativaModal, init_db_loja_sazonal)
from guildas import (cmd_guilda_criar, cmd_guilda_info, cmd_guilda_convidar, cmd_guilda_sair,
    cmd_guilda_expulsar, cmd_guilda_promover, cmd_guilda_depositar, cmd_guilda_retirar,
    cmd_guilda_ranking, cmd_guilda_missoes, init_db_guildas, dar_xp_guilda, atualizar_missao_guilda)
from dupla import rodar_treino_dupla
from torneio import (cmd_torneio_criar, cmd_torneio_status, cmd_torneio_lutar,
    cmd_torneio_fechar_inscricoes, cmd_torneio_cancelar, init_db_torneio)
from dungeon_evento import (DungeonEventoCriarModal, AdicionarAndarModal,
    cmd_dungeon_evento_ativar, cmd_dungeon_evento_info,
    cmd_dungeon_evento_fechar, init_db_dungeon_evento)
from mercado import cmd_mercador, cmd_mercado_vender
from racas import RACAS, RACAS_BASICAS, get_raca, PassivaRacial, COR_RAR_RACA

# ─── EXPEDIÇÃO (SISTEMA SIMPLIFICADO) ───────────────────────────
from expedicao import register_expedicao_commands, init_db_expedicao

# Configuração de imagens (desabilitadas para evitar erros)
IMG_PERFIL = IMG_SETUP = IMG_INVENTARIO = IMG_SKILLS = IMG_AJUDA = ""
IMG_LOJA = IMG_FERREIRO = IMG_HOSPITAL = IMG_MERCADO = IMG_MERCADOR = ""
IMG_MISSOES = IMG_RANKING = IMG_CONQUISTAS = IMG_ROLETA = ""
IMG_BANNER_GERAL = IMG_VITORIA = IMG_DERROTA = IMG_LEVEL_UP = ""
IMG_CLASSE = {}

# ─── DADOS ───────────────────────────────────────────────────────
def calcular_stats(poder_valor, destino_id, nivel=1):
    hp = 80 + poder_valor*2 + nivel*5
    atk = 8 + poder_valor//5 + nivel*2
    dfs = 5 + poder_valor//6 + nivel*1
    if destino_id == "prodigio":    atk = int(atk*1.12); dfs = int(dfs*0.95)
    elif destino_id == "guardiao":  dfs = int(dfs*1.12); atk = int(atk*0.95)
    elif destino_id == "abencado":  hp=int(hp*1.08); atk=int(atk*1.05); dfs=int(dfs*1.05)
    elif destino_id == "maldito":   atk=int(atk*0.85); dfs=int(dfs*0.85)
    elif destino_id == "amaldicoado": atk=random.randint(5,atk+5); dfs=random.randint(3,dfs+3)
    return hp, atk, dfs

CLASSES = [
    {"id":"guerreiro","nome":"Guerreiro","emoji":"🗡️","raridade":"Comum","peso":30,"desc":"Combate corpo a corpo. Alta defesa."},
    {"id":"arqueiro","nome":"Arqueiro","emoji":"🏹","raridade":"Comum","peso":25,"desc":"Precisao e criticos frequentes."},
    {"id":"mago","nome":"Mago","emoji":"🔮","raridade":"Comum","peso":20,"desc":"Dano magico crescente por turno."},
    {"id":"paladino","nome":"Paladino","emoji":"⚡","raridade":"Incomum","peso":12,"desc":"Hibrido: cura e combate."},
    {"id":"necromante","nome":"Necromante","emoji":"🌑","raridade":"Raro","peso":8,"desc":"Drena vida dos inimigos."},
    {"id":"dracomante","nome":"Dracomante","emoji":"🐉","raridade":"Lendario","peso":2,"desc":"Sangue de dragao. Resistencia maxima."},
    {"id":"arcano","nome":"Arcano","emoji":"✨","raridade":"Epico","peso":3,"desc":"Dano arcano que ignora defesa."},
]
PODERES = [
    {"id":"fraquinho","nome":"Fraquinho","emoji":"💀","valor":10},
    {"id":"mediano","nome":"Mediano","emoji":"⚖️","valor":18},
    {"id":"acima","nome":"Acima da media","emoji":"📈","valor":26},
    {"id":"forte","nome":"Forte","emoji":"💪","valor":35},
    {"id":"epico","nome":"Epico","emoji":"⚡","valor":48},
    {"id":"absurdo","nome":"Absurdo","emoji":"🔥","valor":65},
]
PESOS_PODER = [20,30,25,15,7,3]
DESTINOS = [
    {"id":"equilibrado","nome":"Equilibrado","emoji":"⚖️"},
    {"id":"prodigio","nome":"Prodigio","emoji":"🔥"},
    {"id":"maldito","nome":"Maldito","emoji":"💀"},
    {"id":"guardiao","nome":"Guardiao","emoji":"🛡️"},
    {"id":"abencado","nome":"Abencado","emoji":"🌟"},
    {"id":"amaldicoado","nome":"Amaldicoado","emoji":"☠️"},
    {"id":"filho_caos","nome":"Filho do Caos","emoji":"🌀"},
]
EMOJI_CLASSE = {"guerreiro":"🗡️","mago":"🔮","arqueiro":"🏹","paladino":"⚡","necromante":"🌑","dracomante":"🐉","arcano":"✨"}
COR_RAR_BOT = {"Comum":0x888780,"Incomum":0x1D9E75,"Raro":0x378ADD,"Epico":0x7F77DD,"Lendario":0xD85A30}

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ─── HELPERS ─────────────────────────────────────────────────────

async def get_treino_uso(user_id):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow('SELECT * FROM treino_uso WHERE user_id=$1', user_id)
            if not row: return 0, None
            from datetime import datetime
            if row['reset_em'] and datetime.utcnow() >= row['reset_em']:
                await conn.execute('UPDATE treino_uso SET count=0, reset_em=NULL WHERE user_id=$1', user_id)
                return 0, None
            return row['count'], row['reset_em']
    except Exception as e:
        print(f'Erro get_treino_uso: {e}')
        return 0, None

async def incrementar_treino(user_id):
    try:
        from datetime import datetime, timedelta
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow('SELECT count FROM treino_uso WHERE user_id=$1', user_id)
            novo = (row['count'] if row else 0) + 1
            reset_em = datetime.utcnow() + timedelta(hours=2) if novo >= 20 else None
            await conn.execute(
                'INSERT INTO treino_uso(user_id,count,reset_em) VALUES($1,$2,$3) ON CONFLICT(user_id) DO UPDATE SET count=$2, reset_em=COALESCE($3, treino_uso.reset_em)',
                user_id, novo, reset_em)
    except Exception as e:
        print(f'Erro incrementar_treino: {e}')

def sortear_peso(lista, pesos):
    return random.choices(lista, weights=pesos, k=1)[0]

async def get_personagem(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM personagens WHERE user_id=$1", user_id)

def em_batalha(uid): return uid in BATALHAS_ATIVAS

async def checar_batalha(inter):
    if em_batalha(inter.user.id):
        try: await inter.response.send_message("Voce esta em batalha! Termine primeiro.", ephemeral=True)
        except: pass
        return False
    return True

async def atualizar_cargo_rank(guild, member, rank):
    for nome_c, rank_c in CARGOS_RANK.items():
        cargo = discord.utils.get(guild.roles, name=nome_c)
        if cargo:
            try:
                if nome_c == rank_c:
                    await member.add_roles(cargo)
                else:
                    if cargo in member.roles:
                        await member.remove_roles(cargo)
            except: pass

async def criar_canal_privado(guild, member, nome, classe):
    try:
        cat = (discord.utils.get(guild.categories, name="MEU PERFIL") or
               discord.utils.get(guild.categories, name="Meu Perfil") or
               discord.utils.get(guild.categories, name="PERFIL") or
               discord.utils.get(guild.categories, name="perfil"))
        if not cat:
            cat = await guild.create_category("MEU PERFIL")
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        nome_canal = f"{classe['emoji']}│{nome.lower()[:20]}"
        canal = await guild.create_text_channel(nome_canal, category=cat, overwrites=overwrites)
        cor = COR_RAR_BOT.get(classe.get("raridade","Comum"), 0x7F77DD)
        await canal.send(content=member.mention)

        secoes = [
            ("Bem-vindo a Villa Eldoria!", cor,
             "Este e o seu canal privado - so voce e o bot tem acesso aqui.\n\n"
             "Aqui estao todas as informacoes para sua jornada.\n"
             "**Leia tudo antes de comecar!**\n\n"
             "Use `/tutorial` a qualquer momento para rever qualquer secao.", "1/11"),

            ("Seu Personagem", 0x7F77DD,
             "**Comandos essenciais:**\n"
             "`/perfil` - Ver sua ficha completa\n"
             "`/inventario` - Ver seus itens\n"
             "`/skills` - Ver suas habilidades\n"
             "`/setup` - Equipar armas e armaduras\n\n"
             "Ganhe XP para subir de nivel e evoluir seu personagem.\n"
             "Cada nivel aumenta HP, Mana, ATK e DEF automaticamente.", "2/11"),

            ("Roletas do Destino", 0x9B59B6,
             "`/girar` - Girar a roleta usando fichas\n\n"
             "As roletas podem conceder:\n"
             "- Novas classes raras (Dracomante, Arcano...)\n"
             "- Racas especiais\n"
             "- Itens e recompensas exclusivas\n\n"
             "Fichas sao obtidas em eventos, missoes e conquistas.", "3/11"),

            ("Sistema de Combate", 0xE24B4A,
             "`/treinar [dificuldade]` - Batalhar contra monstros\n"
             "`/desafiar @jogador` - Duelo PvP\n"
             "`/treinar-dupla @parceiro` - Batalha em dupla (+20% recompensa)\n\n"
             "Durante a batalha voce pode usar skills, se defender,\n"
             "usar pocoes da mochila ou fugir.\n\n"
             "**Dificuldades:** Facil > Medio > Dificil > Lendario", "4/11"),

            ("Dungeons", 0x7F77DD,
             "`/dungeon` - Entrar em uma dungeon\n\n"
             "Cada dungeon tem andares com monstros diferentes.\n"
             "Derrote todos para avancar e ganhar loot.\n"
             "Se morrer perde todas as recompensas do run.\n\n"
             "Masmorras vao do Rank F ao Rank SS.\n"
             "Cada rank e mais desafiador e recompensador.", "5/11"),

            ("Inventario e Loja", 0x1D9E75,
             "`/inventario` - Ver seus itens\n"
             "`/loja` - Comprar armas, armaduras e pocoes\n"
             "`/loja-sazonal` - Itens especiais e ofertas do dia\n"
             "`/ferreiro` - Forjar equipamentos raros\n"
             "`/mercado` - Vender seus itens\n\n"
             "Dica: Equipe sempre a melhor arma e armadura para sua classe!\n"
             "Use `/setup` para equipar ou clique em Equipar no `/inventario`.", "6/11"),

            ("Hospital e Recuperacao", 0x3498DB,
             "`/hospital` - Acessar o hospital\n\n"
             "Opcoes de cura:\n"
             "- Comprar cura com moedas\n"
             "- Descanso gratis de 30 minutos (recupera tudo)\n"
             "- Pocoes de cura do inventario durante batalhas\n\n"
             "Dica: Use o descanso gratis sempre que possivel!", "7/11"),

            ("Guildas", 0xE4AF3C,
             "`/guilda-info` - Ver informacoes da sua guilda\n"
             "`/guilda-missoes` - Ver missoes semanais\n"
             "`/guilda-depositar` - Depositar no banco da guilda\n\n"
             "Beneficios de ter guilda:\n"
             "- Bonus de XP e moedas conforme o nivel da guilda\n"
             "- Missoes semanais com recompensas para todos\n"
             "- Batalhas em dupla com membros\n\n"
             "Para criar uma guilda: `/guilda-criar` (custa 5000 moedas)", "8/11"),

            ("Rankings e Conquistas", 0xE4AF3C,
             "`/ranking` - Ver ranking do servidor\n"
             "`/conquistas` - Ver suas conquistas\n"
             "`/missoes` - Ver missoes diarias\n"
             "`/historico` - Ver historico de batalhas\n\n"
             "Rankings: Maior nivel, mais vitorias, mais rico,\n"
             "dungeons concluidas e torneios vencidos.\n\n"
             "Complete conquistas para ganhar recompensas!", "9/11"),

            ("Eventos e Torneios", 0xD85A30,
             "`/eventos` - Ver eventos ativos\n"
             "`/evento-info` - Detalhes e ranking do evento\n\n"
             "Tipos de eventos:\n"
             "- Torneios PvP com chaves e premios\n"
             "- Dungeons de evento com monstros customizados\n"
             "- Eventos especiais com premios exclusivos\n\n"
             "Fique de olho nos canais de anuncio!", "10/11"),

            ("Dicas para Iniciantes", 0x1D9E75,
             "**Por onde comecar:**\n"
             "1. Use `/loja` e compre uma arma para sua classe\n"
             "2. Use `/treinar facil` para ganhar XP e moedas\n"
             "3. Complete as `/missoes` diarias\n"
             "4. Entre numa guilda para bonus de XP\n"
             "5. Explore `/dungeon` quando estiver mais forte\n\n"
             "**Como evoluir rapido:**\n"
             "- Faca missoes diarias todos os dias\n"
             "- Participe de todos os eventos\n"
             "- Use o descanso gratis do hospital\n"
             "- Jogue em dupla para +20% de recompensa\n\n"
             "Use `/tutorial` para rever qualquer secao!", "11/11"),
        ]

        for titulo, cor_s, desc, secao in secoes:
            e = discord.Embed(title=titulo, description=desc, color=cor_s)
            e.set_footer(text=f"Villa Eldoria RPG — Secao {secao}")
            await canal.send(embed=e)
            await asyncio.sleep(0.4)

    except Exception as e:
        print(f"Erro ao criar canal privado: {e}")

# ─── AUTOCOMPLETE FUNCTIONS ──────────────────────────────────────

async def autocomplete_item_categoria(interaction: discord.Interaction, current: str):
    try:
        categoria = str(interaction.namespace.categoria or "")
    except:
        categoria = ""
    itens = get_itens_por_categoria(categoria) if categoria else get_catalogo_completo()
    filtrado = [i for i in itens if current.lower() in i["nome"].lower() or current.lower() in i["raridade"].lower()]
    return [
        app_commands.Choice(
            name=f"{i['emoji']} {i['nome']} [{i['raridade']}]"[:100],
            value=i["chave"]
        )
        for i in filtrado[:25]
    ]

async def autocomplete_item_todos(interaction: discord.Interaction, current: str):
    itens = get_catalogo_completo()
    filtrado = [i for i in itens if current.lower() in i["nome"].lower() or current.lower() in i["raridade"].lower() or current.lower() in i["tipo"].lower()]
    return [
        app_commands.Choice(
            name=f"{i['emoji']} {i['nome']} [{i['raridade']}] — {i['tipo']}{' ('+i['classe']+')' if i['classe'] else ''}"[:100],
            value=i["chave"]
        )
        for i in filtrado[:25]
    ]

async def autocomplete_materiais(interaction: discord.Interaction, current: str):
    itens = get_catalogo_completo()
    filtrado = [i for i in itens if i["tipo"] in ("material","pocao") and (current.lower() in i["nome"].lower() or not current)]
    return [
        app_commands.Choice(
            name=f"{i['emoji']} {i['nome']} [{i['raridade']}]"[:100],
            value=i["chave"]
        )
        for i in filtrado[:25]
    ]

async def autocomplete_item_premio(interaction: discord.Interaction, current: str):
    try:
        premio_tipo = str(interaction.namespace.premio_tipo or "")
    except:
        premio_tipo = ""
    if premio_tipo == "item":
        itens = get_catalogo_completo()
        filtrado = [i for i in itens if current.lower() in i["nome"].lower() or not current]
        return [
            app_commands.Choice(
                name=f"{i['emoji']} {i['nome']} [{i['raridade']}]"[:100],
                value=f"{i['id']}|{i['nome']}|{i['tipo']}|{i['raridade']}|{i['emoji']}|{i.get('desc','')}"[:100]
            )
            for i in filtrado[:25]
        ]
    elif premio_tipo == "moedas":
        exemplos = ["1000","2000","5000","10000","20000","50000"]
        return [app_commands.Choice(name=f"{v} moedas", value=v) for v in exemplos if current in v]
    elif premio_tipo == "xp":
        exemplos = ["500","1000","2000","5000","10000"]
        return [app_commands.Choice(name=f"{v} XP", value=v) for v in exemplos if current in v]
    elif premio_tipo == "ficha":
        exemplos = ["1","2","3","5","10"]
        return [app_commands.Choice(name=f"{v} ficha(s)", value=v) for v in exemplos if current in v]
    elif premio_tipo == "cargo":
        return [app_commands.Choice(name="Nome do cargo (ex: Campiao)", value=current or "Campiao")]
    elif premio_tipo == "classe":
        classes = ["guerreiro","arqueiro","mago","paladino","necromante","dracomante","arcano"]
        EMOJI_CLS = {"guerreiro":"🗡️","arqueiro":"🏹","mago":"🔮","paladino":"⚡","necromante":"🌑","dracomante":"🐉","arcano":"✨"}
        return [app_commands.Choice(name=f"{EMOJI_CLS[cl]} {cl.title()}", value=cl) for cl in classes if current.lower() in cl]
    return [app_commands.Choice(name=current or "Digite o valor do premio", value=current or "")]

async def autocomplete_canal(interaction: discord.Interaction, current: str):
    if not interaction.guild: return []
    canais = [
        ch for ch in interaction.guild.channels
        if isinstance(ch, (discord.TextChannel, discord.ForumChannel))
        and (not current or current.lower() in ch.name.lower())
    ]
    canais.sort(key=lambda ch: ch.name)
    return [
        app_commands.Choice(name=f"#{ch.name}", value=str(ch.id))
        for ch in canais[:25]
    ]

def resolver_canal(guild, canal):
    if canal is None: return None
    if hasattr(canal, 'id'):
        return guild.get_channel(canal.id) or canal
    canal_str = str(canal)
    if canal_str.isdigit():
        return guild.get_channel(int(canal_str))
    return discord.utils.get(guild.channels, name=canal_str.lstrip('#'))

# ─── TODOS OS COMANDOS EXISTENTES (criar_personagem, perfil, inventario, etc.) ───
# ... (mantenha todos os seus comandos existentes aqui) ...

# ─── /ajuda ──────────────────────────────────────────────────────

@bot.tree.command(name="ajuda", description="Lista todos os comandos do RPG")
async def ajuda(interaction: discord.Interaction):
    embed = discord.Embed(title="Comandos — Villa Eldoria RPG", color=0x7F77DD)
    embed.add_field(name="Personagem", value="`/criar_personagem` `/perfil` `/skills` `/setup` `/deletar_personagem`", inline=False)
    embed.add_field(name="Inventario", value="`/inventario` `/equipar` `/jogar-fora` `/dar`", inline=False)
    embed.add_field(name="Batalha",    value="`/treinar` `/desafiar` `/dungeon` `/treinar-dupla`", inline=False)
    embed.add_field(name="Economia",   value="`/loja` `/loja-sazonal` `/ferreiro` `/hospital` `/mercado` `/mercador`", inline=False)
    embed.add_field(name="Progresso",  value="`/missoes` `/conquistas` `/ranking` `/girar`", inline=False)
    embed.add_field(name="Admin",      value="`/set-item` `/set-moedas` `/set-nivel` `/set-giros`", inline=False)
    embed.add_field(name="Eventos",    value="`/criar-evento` `/eventos` `/evento-info` `/encerrar-evento` `/add-pontos`", inline=False)
    embed.add_field(name="Anuncios",   value="`/anunciar` `/anunciar-evento` `/agendar-anuncio`", inline=False)
    embed.add_field(name="Guildas",    value="`/guilda-criar` `/guilda-info` `/guilda-missoes` `/guilda-convidar` `/guilda-sair` `/guilda-promover` `/guilda-depositar` `/guilda-retirar` `/guilda-ranking`", inline=False)
    embed.add_field(name="Torneio",    value="`/torneio-criar` `/torneio-status` `/torneio-lutar` `/torneio-fechar-inscricoes` `/torneio-cancelar`", inline=False)
    embed.add_field(name="Dungeon Evento", value="`/dungeon-evento-criar` `/dungeon-evento-configurar` `/dungeon-evento-ativar` `/dungeon-evento-info` `/dungeon-evento-fechar`", inline=False)
    embed.add_field(name="Expedição",  value="`/expedicao_criar` `/expedicao_add_capitulo` `/expedicao_add_recompensa` `/expedicao_publicar` `/expedicao_ver` `/expedicao_listar` `/expedicao_inscrever` `/expedicao_iniciar`", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ─── REGISTRO DOS COMANDOS DE EXPEDIÇÃO ──────────────────────────
# IMPORTANTE: Isso deve ser chamado DEPOIS de todos os comandos e ANTES do sync
register_expedicao_commands(bot)
register_party_commands(bot)

# ─── SYNC MANUAL ─────────────────────────────────────────────────

@bot.command(name="sync")
async def sync_cmd(ctx):
    try:
        guild_id = int(os.getenv("GUILD_ID","0"))
        total = 0
        if guild_id:
            guild_obj = discord.Object(id=guild_id)
            bot.tree.copy_global_to(guild=guild_obj)
            s = await bot.tree.sync(guild=guild_obj)
            total += len(s)
        s2 = await bot.tree.sync()
        total += len(s2)
        await ctx.send(f"✅ {total} comandos sincronizados!")
    except Exception as e:
        await ctx.send(f"❌ Erro: {e}")

# ─── EVENTOS ─────────────────────────────────────────────────────

_synced = False

@bot.event
async def on_ready():
    global _synced
    print(f"Bot: {bot.user}")
    cmds_no_tree = len(bot.tree.get_commands())
    print(f"Comandos no tree: {cmds_no_tree}")

    # DB
    try:
        await init_db()
        await init_db_batalha()
        await init_db_hospital()
        await init_db_missoes()
        await init_conquistas()
        await init_db_eventos()
        await init_db_loja_sazonal()
        await init_db_guildas()
        await init_db_torneio()
        await init_db_dungeon_evento()
        await init_db_expedicao()  # ← Inicializa banco da expedição
        await init_db_party()
        print("DB OK!")
    except Exception as e:
        print(f"ERRO DB: {e}")

    if not _ed:
        try:
            guild_id = int(os.getenv("GUILD_ID","0"))
            if guild_id:
                guild_obj = discord.Object(id=guild_id)
                bot.tree.copy_global_to(guild=guild_obj)
                guild_ed = await bot.tree.(guild=guild_obj)
                print(f"Comandos no servidor: {len(guild_ed)}")
            else:
                global_ed = await bot.tree.sync()
                print(f"Comandos globais: {len(global_synced)}")
            _synced = True
        except Exception as e:
            print(f"ERRO sync: {e}")
    else:
        print("Sync ignorado — ja sincronizado anteriormente")

    print("Bot pronto!")

@bot.event
async def on_member_join(member: discord.Member):
    cargo = discord.utils.get(member.guild.roles, name="🌱 Recem-chegado")
    if cargo:
        try: await member.add_roles(cargo)
        except: pass

    try:
        canal_bv = (
            discord.utils.get(member.guild.text_channels, name="📌┃boas-vindas") or
            discord.utils.get(member.guild.text_channels, name="boas-vindas") or
            discord.utils.get(member.guild.text_channels, name="bem-vindo") or
            discord.utils.get(member.guild.text_channels, name="welcome")
        )
        if not canal_bv: return

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
            color=0xE4AF3C
        )
        embed.set_footer(text="Villa Eldoria RPG — Sua jornada comeca agora!")
        await canal_bv.send(content=member.mention, embed=embed)
    except Exception as e:
        print(f"Erro boas-vindas: {e}")

# ─── MAIN ────────────────────────────────────────────────────────

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN","")
    if not token:
        try:
            with open("config.txt") as f:
                for l in f:
                    if l.startswith("DISCORD_TOKEN="):
                        token = l.split("=",1)[1].strip()
        except: pass
    if not token:
        print("ERRO: Token nao encontrado."); exit(1)
    bot.run(token)
