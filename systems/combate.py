# systems/combate.py — Sistema de combate completo (PVE + PVP + Passivas Raciais)

import discord
import asyncio
import random
from typing import Optional, Tuple, List, Callable, Any
from datetime import datetime, timezone

from database.db import get_pool
from database.queries import (
    get_personagem, get_skills_equipadas, get_pocoes_inv, get_arma_equipada, get_armadura_equipada,
    add_item, remover_pocao, desbloquear_skill
)
from data.constantes import EMOJI_CLASSE, COR_RAR, ARENAS, COOLDOWN_BATALHA
from data.skills import get_skill_by_id, SKILLS_COMPLETAS
from data.armas import get_bonus_arma
from data.armaduras import get_bonus_armadura
from data.monstros import MONSTROS
from data.ranks import get_rank, RANK_BONUS
from data.racas import get_raca, RACAS
from utils.calculos import calc_dano, barra_hp, calcular_mana_max
from utils.helpers import atualizar_todos_cargos
from utils.cooldown import cooldown_manager
from systems.personagem import salvar_resultado

# Import para views
from views.batalha_view import BatalhaView, EscolherArenaView, AceitarDueloView

# ==================================================
# CONSTANTES DE COMBATE
# ==================================================

BATALHAS_ATIVAS: set = set()

# ==================================================
# FUNÇÕES AUXILIARES
# ==================================================

def get_mult_basico(nivel: int) -> float:
    """Retorna o multiplicador de ataque básico baseado no nível"""
    if nivel <= 9:
        return 1.0
    elif nivel <= 19:
        return 1.1
    elif nivel <= 29:
        return 1.2
    elif nivel <= 39:
        return 1.3
    elif nivel <= 49:
        return 1.4
    elif nivel <= 59:
        return 1.5
    elif nivel <= 74:
        return 1.6
    else:
        return 1.8


def processar_efeitos_turno(efeitos: dict) -> Tuple[int, List[str], dict]:
    """Processa efeitos de status no início do turno"""
    dano_total = 0
    msgs = []
    novos_efeitos = {}

    for ef, dados in efeitos.items():
        if isinstance(dados, dict):
            duracao = dados.get("duracao", 0)
            valor = dados.get("valor", 0)
        else:
            duracao = dados
            valor = 0

        if duracao <= 0:
            continue

        duracao -= 1

        if ef == "veneno":
            dano_total += valor
            msgs.append(f"☠️ Veneno causou **{valor}** de dano!")
        elif ef == "queimadura":
            dano_total += valor
            msgs.append(f"🔥 Queimadura causou **{valor}** de dano!")
        elif ef == "regeneracao":
            msgs.append(f"💚 Regeneracao: +{valor} HP!")
        elif ef in ("defesa", "escudo", "esquiva", "escudo_total", "armadura", "reflexo",
                    "buff_ataque", "buff_all", "berserker", "congelar", "paralisia",
                    "atordoado", "confusao", "terror", "enfraquecer"):
            pass

        if duracao > 0:
            novos_efeitos[ef] = {"duracao": duracao, "valor": valor}

    return dano_total, msgs, novos_efeitos


def efeito_ativo(efeitos: dict, nome: str) -> bool:
    """Verifica se um efeito está ativo"""
    ef = efeitos.get(nome)
    if ef is None:
        return False
    if isinstance(ef, dict):
        return ef.get("duracao", 0) > 0
    return ef > 0


def add_efeito(efeitos: dict, nome: str, duracao: int, valor: int = 0) -> None:
    """Adiciona um efeito ao dicionário"""
    efeitos[nome] = {"duracao": duracao, "valor": valor}


# ==================================================
# PASSIVAS DAS CLASSES
# ==================================================

class Passiva:
    def __init__(self, classe_id: str):
        self.classe_id = classe_id
        self.turno = 0
        self.bonus_dreno = 1.0
        self.bonus_mag_acum = 0.0
        self.arcano_turnos = 0
        self.arcano_acum = 0.0
        self.arcano_skills_usadas = 0

    def inicio_turno(self, hp_j: int, hp_jmx: int) -> int:
        self.turno += 1
        cura = 0
        if self.classe_id == "paladino" and hp_jmx > 0 and (hp_j / hp_jmx) < 0.40:
            cura = 20
        if self.classe_id == "mago":
            self.bonus_mag_acum = min(0.40, self.bonus_mag_acum + 0.08)
        return cura

    def incrementar_skill_arcano(self) -> None:
        if self.classe_id == "arcano":
            self.arcano_skills_usadas += 1
            self.arcano_acum = min(0.50, self.arcano_skills_usadas * 0.05)

    def apos_critico(self) -> int:
        return 8 if self.classe_id == "arqueiro" else 0

    def apos_dreno(self) -> float:
        if self.classe_id == "necromante":
            self.bonus_dreno = min(2.5, self.bonus_dreno + 0.15)
        return self.bonus_dreno

    def apos_tomar_dano(self) -> None:
        if self.classe_id == "arcano":
            pass

    def fim_turno_sem_dano(self) -> None:
        if self.classe_id == "arcano":
            pass

    def bonus_defesa_fixa(self) -> int:
        if self.classe_id == "guerreiro":
            return min(50, (self.turno // 2) * 5)
        return 0

    def reducao_dano(self) -> float:
        return 0.10 if self.classe_id == "dracomante" else 0.0

    def imune_status(self, status: str) -> bool:
        return self.classe_id == "dracomante" and status in ("queimadura", "veneno")

    def multiplicador_dano(self) -> float:
        if self.classe_id == "mago":
            return 1.0 + self.bonus_mag_acum
        if self.classe_id == "arcano":
            return 1.0 + self.arcano_acum
        return 1.0

    def desc_passiva(self) -> str:
        if self.classe_id == "guerreiro":
            return f"🗡️ DEF passiva: +{self.bonus_defesa_fixa()}"
        if self.classe_id == "arqueiro":
            return "🏹 Crítico recupera 8 mana"
        if self.classe_id == "mago":
            return f"🔮 Dano mágico +{int(self.bonus_mag_acum * 100)}%"
        if self.classe_id == "paladino":
            return "⚡ Cura auto 20 HP/turno se HP<40%"
        if self.classe_id == "necromante":
            return f"🌑 Dreno x{self.bonus_dreno:.1f}"
        if self.classe_id == "dracomante":
            return "🐉 -10% dano, imune veneno/queimadura"
        if self.classe_id == "arcano":
            return f"✨ Dano arcano +{int(self.arcano_acum * 100)}% (por skill usada)"
        return ""


# ==================================================
# PASSIVA RACIAL
# ==================================================

class PassivaRacial:
    def __init__(self, raca_id: str):
        self.raca_id = raca_id
        self.turno = 0
        self.ressuscitou = False
        self.escudo_anjo = 0
        self.bonus_demonio = 0.0
        self.transformado = False

    def inicio_turno(self, hp_j: int, hp_jmx: int) -> Tuple[int, bool]:
        self.turno += 1
        cura = 0
        escudo = False

        if self.raca_id == "elfo_floresta":
            cura = max(1, int(hp_jmx * 0.04))

        if self.raca_id == "demonio":
            if self.turno <= 10:
                self.bonus_demonio = min(0.50, self.bonus_demonio + 0.05)

        if self.raca_id == "anjo":
            if self.turno % 5 == 0:
                escudo = True

        if self.raca_id == "licantropo":
            self.transformado = (hp_j / max(1, hp_jmx)) < 0.60

        return cura, escudo

    def multiplicador_dano(self) -> float:
        if self.raca_id == "demonio":
            return 1.0 + self.bonus_demonio
        if self.raca_id == "licantropo" and self.transformado:
            return 1.30
        if self.raca_id == "draconiano":
            return 1.10
        return 1.0

    def reducao_dano(self) -> float:
        if self.raca_id == "draconiano":
            return 0.12
        if self.raca_id == "anao":
            return 0.05
        return 0.0

    def bonus_defesa_fixa(self) -> int:
        if self.raca_id == "anao":
            return 5
        return 0

    def bonus_critico(self) -> float:
        if self.raca_id == "elfo":
            return 0.15
        return 0.0

    def bonus_mana_max(self) -> int:
        if self.raca_id == "elfo":
            return 20
        return 0

    def bonus_xp(self) -> float:
        if self.raca_id == "humano":
            return 0.10
        return 0.0

    def bonus_moedas(self) -> float:
        if self.raca_id == "humano":
            return 0.05
        return 0.0

    def imune_status(self, status: str) -> bool:
        imunidades = {
            "demonio": ["veneno", "queimadura", "congelar"],
            "draconiano": ["queimadura"],
            "morto_vivo": ["veneno", "congelar", "queimadura", "atordoar"],
            "licantropo": ["veneno"] if self.transformado else [],
        }
        return status in imunidades.get(self.raca_id, [])

    def resist_atordoar(self) -> float:
        if self.raca_id == "anao":
            return 0.50
        return 0.0

    def apos_tomar_dano(self, dano: int, hp_j: int, hp_jmx: int, atk_inimigo: int) -> Tuple[int, int]:
        contra = 0
        dreno = 0

        if self.raca_id == "elfo_sombrio" and random.random() < 0.30:
            contra = max(5, int(atk_inimigo * 0.40))

        if self.raca_id == "morto_vivo":
            dreno = max(1, int(hp_jmx * 0.06))

        return contra, dreno

    def congelar_ao_atacar(self) -> bool:
        if self.raca_id == "gigante_gelo":
            return random.random() < 0.35
        return False

    def ignorar_defesa(self) -> float:
        if self.raca_id == "djinn":
            return 0.20
        return 0.0

    def tentar_ressuscitar(self, hp_j: int) -> bool:
        if self.raca_id == "anjo" and hp_j <= 0 and not self.ressuscitou:
            self.ressuscitou = True
            return True
        return False

    def modificar_dano_recebido(self, dano: int) -> Tuple[int, str]:
        reducao = self.reducao_dano()
        if reducao > 0:
            dano_final = max(1, int(dano * (1 - reducao)))
            return dano_final, f"🛡️ Redução de dano: -{int(reducao*100)}%"
        return dano, ""

    def desc_passiva(self) -> str:
        raca = get_raca(self.raca_id)
        desc = raca.get("passiva_desc", "")
        extras = []
        if self.raca_id == "demonio" and self.bonus_demonio > 0:
            extras.append(f"+{int(self.bonus_demonio*100)}% dano acumulado")
        if self.raca_id == "licantropo" and self.transformado:
            extras.append("🐺 TRANSFORMADO")
        if extras:
            desc += f" | {' | '.join(extras)}"
        return f"{raca['emoji']} Passiva racial: {desc}"


# ==================================================
# FUNÇÕES AUXILIARES DE COMBATE
# ==================================================

async def get_skills_jogador(user_id: int, classe_id: str) -> list:
    """Retorna as skills equipadas do jogador"""
    ids_eq = await get_skills_equipadas(user_id)
    skills = []
    for sid in ids_eq:
        sk = get_skill_by_id(sid)
        if sk:
            skills.append(sk)
    if not skills:
        skills = SKILLS_COMPLETAS.get(classe_id, [])[:4]
    return skills


def calcular_bonus_equip(classe_id: str, arma: dict, armadura: dict) -> Tuple[float, float]:
    """Calcula bônus de equipamento"""
    bonus_atk = 1.0
    bonus_dfs = 1.0
    if arma:
        arma_id = arma["item_id"]
        _, compat = get_bonus_arma(arma_id, classe_id)
        if compat is True:
            bonus_atk = 1.15
        elif compat is False:
            bonus_atk = 0.85
    if armadura:
        arm_id = armadura["item_id"]
        _, compat = get_bonus_armadura(arm_id, classe_id)
        if compat is True:
            bonus_dfs = 1.10
        elif compat is False:
            bonus_dfs = 0.90
    return bonus_atk, bonus_dfs


async def aplicar_efeito_pocao(item_id: str, hp: int, hp_max: int, mana: int, mana_max: int) -> Tuple[int, int, str]:
    """Aplica o efeito de uma poção"""
    from data.itens import POCOES_BATALHA
    
    poc = POCOES_BATALHA.get(item_id)
    if not poc:
        return hp, mana, "Poção desconhecida."
    if poc["tipo"] == "hp":
        ganho = min(poc["valor"], hp_max - hp)
        return hp + ganho, mana, f"{poc['emoji']} {poc['nome']} usada! +{ganho} HP ❤️"
    elif poc["tipo"] == "mana":
        ganho = min(poc["valor"], mana_max - mana)
        return hp, mana + ganho, f"{poc['emoji']} {poc['nome']} usada! +{ganho} Mana 💙"
    else:
        return hp_max, mana_max, f"{poc['emoji']} Elixir Supremo! HP e Mana restaurados! ✨"


# ==================================================
# VIEW PARA GERENCIAR SKILLS
# ==================================================

class GerenciarSkillsView(discord.ui.View):
    def __init__(self, user_id, skills, skills_eq):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.skills = skills
        opcoes = [
            discord.SelectOption(
                label=f"{s['emoji']} {s['nome']} (Nv{s['nivel']})",
                value=s["id"],
                description=s["desc"][:50],
                default=s["id"] in skills_eq
            ) for s in skills[:25]
        ]
        if opcoes:
            sel = discord.ui.Select(
                placeholder="Selecione ate 4 skills...",
                min_values=1, max_values=min(4, len(opcoes)),
                options=opcoes
            )
            sel.callback = self._sel
            self.add_item(sel)

    async def _sel(self, inter: discord.Interaction):
        if inter.user.id != self.user_id:
            await inter.response.send_message("Nao e seu personagem!", ephemeral=True)
            return
        selecionadas = inter.data["values"][:4]
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM skills_equipadas WHERE user_id=$1", self.user_id)
            for slot, sid in enumerate(selecionadas):
                await conn.execute(
                    "INSERT INTO skills_equipadas(user_id, skill_id, slot) VALUES($1,$2,$3) ON CONFLICT(user_id,slot) DO UPDATE SET skill_id=EXCLUDED.skill_id",
                    self.user_id, sid, slot
                )
        nomes = [s["nome"] for s in self.skills if s["id"] in selecionadas]
        await inter.response.edit_message(
            embed=discord.Embed(
                title="Skills atualizadas!",
                description="\n".join([f"• {n}" for n in nomes]),
                color=0x1D9E75
            ),
            view=None
        )


# ==================================================
# ENGINE DE TREINO (PVE) - CORRIGIDA
# ==================================================

async def rodar_treino(interaction: discord.Interaction, p: dict, monstro: dict, arena: dict):
    """Executa uma batalha de treino contra um monstro"""
    uid = p["user_id"]

    pode, tempo = cooldown_manager.check(uid, "treinar", COOLDOWN_BATALHA)
    if not pode:
        await interaction.followup.send(f"⏰ Aguarde **{tempo} segundos** antes de treinar novamente!", ephemeral=True)
        return

    BATALHAS_ATIVAS.add(uid)

    skills = await get_skills_jogador(uid, p["classe_id"])
    arma = await get_arma_equipada(uid)
    armadura = await get_armadura_equipada(uid)
    bonus_atk, bonus_dfs = calcular_bonus_equip(p["classe_id"], arma, armadura)

    hp_j = p["hp_atual"]
    hp_jmx = p["hp_max"]
    mana_j = p.get("mana_atual", 100)
    mana_jmx = p.get("mana_max", 100)
    hp_m = monstro["hp"]
    hp_mmx = monstro["hp"]
    turno = 1
    efeitos_j = {}
    efeitos_m = {}
    passiva = Passiva(p["classe_id"])
    passiva_racial = PassivaRacial(p.get("raca_id", "humano"))
    emoji_j = EMOJI_CLASSE.get(p["classe_id"], "⚔️")
    msgs_batalha = []
    timeout_count = 0

    def barra_status():
        return (
            f"{emoji_j} **{p['nome']}** ❤️`{barra_hp(hp_j, hp_jmx)}`**{hp_j}/{hp_jmx}** 💙{mana_j}/{mana_jmx}\n"
            f"{monstro['emoji']} **{monstro['nome']}** ❤️`{barra_hp(hp_m, hp_mmx)}`**{hp_m}/{hp_mmx}**"
        )

    embed_inicio = discord.Embed(
        title=f"{monstro['emoji']} {monstro['nome']} aparece!",
        description=barra_status(),
        color=arena["cor"]
    )
    msgs_batalha.append(await interaction.followup.send(embed=embed_inicio, wait=True))
    await asyncio.sleep(1)

    while hp_j > 0 and hp_m > 0:
        mana_antes = mana_j

        dano_ef, msgs_ef, efeitos_j = processar_efeitos_turno(efeitos_j)
        if dano_ef > 0:
            hp_j = max(0, hp_j - dano_ef)
        dano_ef_m, msgs_ef_m, efeitos_m = processar_efeitos_turno(efeitos_m)
        if dano_ef_m > 0:
            hp_m = max(0, hp_m - dano_ef_m)

        cura_passiva = passiva.inicio_turno(hp_j, hp_jmx)
        if cura_passiva > 0:
            hp_j = min(hp_jmx, hp_j + cura_passiva)

        if hp_m <= 0:
            break

        pocoes = await get_pocoes_inv(uid)
        view = BatalhaView(uid, skills, pocoes, nivel=p["nivel"])

        embed_vez = discord.Embed(
            title=f"🎮 Turno {turno} — Sua vez!",
            description=barra_status() + (f"\n{passiva.desc_passiva()}" if passiva.desc_passiva() else ""),
            color=0x7F77DD
        )
        msg_vez = await interaction.followup.send(embed=embed_vez, view=view, wait=True)
        msgs_batalha.append(msg_vez)
        await view.wait()

        acao, val = view.acao or ("timeout", None)
        try:
            await msg_vez.edit(view=None)
        except:
            pass

        if acao == "timeout":
            timeout_count += 1
            if timeout_count >= 3:
                embed_exp = discord.Embed(title="💤 Expulso por inatividade!", color=0x888780)
                await interaction.followup.send(embed=embed_exp)
                BATALHAS_ATIVAS.discard(uid)
                for m in msgs_batalha:
                    try:
                        await m.delete()
                    except:
                        pass
                return
            else:
                aviso = discord.Embed(title=f"⏰ Turno perdido! ({timeout_count}/3)", color=0xE4AF3C)
                await interaction.followup.send(embed=aviso)
                turno += 1
                continue
        else:
            timeout_count = 0

        linha_jogador = ""
        cor_acao = arena["cor"]

        if acao == "fugir":
            embed_fuga = discord.Embed(title="🏃 Voce fugiu!", color=0x888780)
            await interaction.followup.send(embed=embed_fuga)
            BATALHAS_ATIVAS.discard(uid)
            for m in msgs_batalha:
                try:
                    await m.delete()
                except:
                    pass
            return

        elif acao == "atk_basico":
            dano = calc_dano(p["ataque"], monstro["defesa"], get_mult_basico(p["nivel"]),
                             bonus_atk=bonus_atk, nivel=p["nivel"], hp_max_monstro=hp_mmx)
            hp_m = max(0, hp_m - dano)
            linha_jogador = f"⚔️ **Ataque Básico**: **{dano} de dano**!"
            cor_acao = 0x888780

        elif acao == "defesa_basica":
            add_efeito(efeitos_j, "defesa_basica", 1)
            linha_jogador = "🛡️ **Postura Defensiva!**"
            cor_acao = 0x378ADD

        elif acao == "pocao" and val:
            hp_j, mana_j, linha_jogador = await aplicar_efeito_pocao(val, hp_j, hp_jmx, mana_j, mana_jmx)
            await remover_pocao(uid, val)
            cor_acao = 0x2ecc71

        elif acao == "skill" and val is not None and val < len(skills):
            sk = skills[val]
            custo = sk.get("mana", 0)
            efeito = sk.get("efeito")

            if p["classe_id"] == "arcano":
                passiva.incrementar_skill_arcano()

            if mana_j < custo:
                dano = calc_dano(p["ataque"], monstro["defesa"], 1.0, bonus_atk=bonus_atk)
                hp_m = max(0, hp_m - dano)
                linha_jogador = f"⚠️ Mana insuficiente! Ataque básico: **{dano} de dano**."
            else:
                mana_j -= custo

                if efeito == "cura":
                    cura = int(hp_jmx * 0.35)
                    hp_j = min(hp_jmx, hp_j + cura)
                    linha_jogador = f"{sk['emoji']} **{sk['nome']}**: +{cura} HP! ❤️"
                elif efeito == "cura_grande":
                    cura = int(hp_jmx * 0.60)
                    hp_j = min(hp_jmx, hp_j + cura)
                    linha_jogador = f"{sk['emoji']} **{sk['nome']}**: +{cura} HP! ❤️"
                elif efeito in ("defesa", "escudo", "esquiva", "escudo_total", "armadura", "reflexo"):
                    duracao = 2 if efeito == "escudo_total" else (3 if efeito == "armadura" else 1)
                    add_efeito(efeitos_j, efeito, duracao)
                    linha_jogador = f"{sk['emoji']} **{sk['nome']}**! Efeito ativo por {duracao} turno(s)."
                elif efeito == "dreno":
                    mult_dreno = passiva.apos_dreno()
                    dano = calc_dano(p["ataque"], monstro["defesa"], sk.get("dano", 1.0), bonus_atk=bonus_atk, nivel=p["nivel"], hp_max_monstro=hp_mmx)
                    roubo = int(dano // 2 * mult_dreno)
                    hp_m = max(0, hp_m - dano)
                    hp_j = min(hp_jmx, hp_j + roubo)
                    linha_jogador = f"{sk['emoji']} **{sk['nome']}**: **{dano} de dano**! Drenou +{roubo} HP! (x{mult_dreno:.1f})"
                elif efeito in ("buff_ataque", "buff_all", "berserker"):
                    add_efeito(efeitos_j, efeito, 3)
                    linha_jogador = f"{sk['emoji']} **{sk['nome']}**: Buff ativo por 3 turnos!"
                elif efeito in ("queimadura", "veneno"):
                    dano = calc_dano(p["ataque"], monstro["defesa"], sk.get("dano", 1.0), bonus_atk=bonus_atk)
                    dano = int(dano * passiva.multiplicador_dano() * passiva_racial.multiplicador_dano())
                    hp_m = max(0, hp_m - dano)
                    if not passiva.imune_status(efeito) and not passiva_racial.imune_status(efeito):
                        add_efeito(efeitos_m, efeito, 3, valor=max(5, dano // 4))
                    linha_jogador = f"{sk['emoji']} **{sk['nome']}**: **{dano} de dano**! Inimigo com {efeito}!"
                elif efeito in ("atordoar", "paralisia", "congelar"):
                    dano = calc_dano(p["ataque"], monstro["defesa"], sk.get("dano", 1.0), bonus_atk=bonus_atk, nivel=p["nivel"], hp_max_monstro=hp_mmx)
                    hp_m = max(0, hp_m - dano)
                    if random.random() < 0.40:
                        add_efeito(efeitos_m, "atordoado", 1)
                        linha_jogador = f"{sk['emoji']} **{sk['nome']}**: **{dano} de dano** + atordoado!"
                    else:
                        linha_jogador = f"{sk['emoji']} **{sk['nome']}**: **{dano} de dano**!"
                elif efeito in ("hits2", "hits3", "hits4", "hits5"):
                    n_hits = int(efeito.replace("hits", ""))
                    dano_total = 0
                    for _ in range(n_hits):
                        d = calc_dano(p["ataque"], monstro["defesa"], sk.get("dano", 0.6), bonus_atk=bonus_atk, nivel=p["nivel"])
                        dano_total += min(d, int(hp_mmx * 0.20))
                    hp_m = max(0, hp_m - min(dano_total, int(hp_mmx * 0.70)))
                    linha_jogador = f"{sk['emoji']} **{sk['nome']}**: {n_hits} golpes → **{dano_total} de dano**!"
                elif efeito == "ignorar_defesa":
                    dano = calc_dano(p["ataque"], monstro["defesa"], sk.get("dano", 1.0), bonus_atk=bonus_atk, ignorar_defesa=True, nivel=p["nivel"], hp_max_monstro=hp_mmx)
                    hp_m = max(0, hp_m - dano)
                    linha_jogador = f"{sk['emoji']} **{sk['nome']}**: **{dano} de dano** (ignora defesa)!"
                elif efeito == "critico_bonus":
                    crit = random.random() < 0.55
                    dano = calc_dano(p["ataque"], monstro["defesa"], sk.get("dano", 1.0), crit=crit, bonus_atk=bonus_atk, nivel=p["nivel"], hp_max_monstro=hp_mmx)
                    hp_m = max(0, hp_m - dano)
                    if crit:
                        mana_j = min(mana_jmx, mana_j + passiva.apos_critico())
                    linha_jogador = f"{sk['emoji']} **{sk['nome']}**: **{dano} de dano**{'💥 CRÍTICO!' if crit else ''}!"
                elif efeito == "singularidade_v2":
                    mana_perdida = int(mana_j * 0.30)
                    mana_j = max(0, mana_j - mana_perdida)
                    dano = calc_dano(p["ataque"], monstro["defesa"], sk.get("dano", 1.0), bonus_atk=bonus_atk, nivel=p["nivel"], hp_max_monstro=hp_mmx)
                    hp_m = max(0, hp_m - dano)
                    linha_jogador = f"{sk['emoji']} **{sk['nome']}**: **{dano} de dano**! Perdeu {mana_perdida} mana!"
                else:
                    crit = random.random() < 0.15
                    dano = calc_dano(p["ataque"], monstro["defesa"], sk.get("dano", 1.0), crit=crit, bonus_atk=bonus_atk)
                    hp_m = max(0, hp_m - dano)
                    if crit:
                        mana_j = min(mana_jmx, mana_j + passiva.apos_critico())
                    linha_jogador = f"{sk['emoji']} **{sk['nome']}**: **{dano} de dano**{'💥 CRÍTICO!' if crit else ''}!"

        embed_acao = discord.Embed(
            title=f"⚔️ {emoji_j} {p['nome']} age!",
            description=f"{linha_jogador}\n\n{barra_status()}",
            color=cor_acao
        )
        msgs_batalha.append(await interaction.followup.send(embed=embed_acao, wait=True))

        if hp_m <= 0:
            break

        await asyncio.sleep(1.2)

        # Turno do monstro
        sk_m = random.choice(monstro["skills"])
        def_total = int(p["defesa"] * bonus_dfs) + passiva.bonus_defesa_fixa() + passiva_racial.bonus_defesa_fixa()
        dano_m_base = calc_dano(monstro["ataque"], def_total)
        reducao = passiva.reducao_dano() + passiva_racial.reducao_dano()
        dano_m = max(1, int(dano_m_base * (1.0 - reducao)))

        if efeito_ativo(efeitos_j, "defesa_basica"):
            if random.random() < 0.60:
                dano_m = max(1, int(dano_m * 0.20))
            efeitos_j["defesa_basica"]["duracao"] = 0
        elif efeito_ativo(efeitos_j, "escudo") or efeito_ativo(efeitos_j, "escudo_total"):
            dano_m = 0
            ef_key = "escudo_total" if efeito_ativo(efeitos_j, "escudo_total") else "escudo"
            efeitos_j[ef_key]["duracao"] -= 1
        elif efeito_ativo(efeitos_j, "reflexo"):
            refletido = int(dano_m * 0.40)
            hp_m = max(0, hp_m - refletido)
            dano_m = int(dano_m * 0.60)

        hp_j = max(0, hp_j - dano_m)

        regen = 8
        mana_j = min(mana_jmx, mana_j + regen)

        embed_m = discord.Embed(
            title=f"{monstro['emoji']} {monstro['nome']} age!",
            description=f"{sk_m['nome']}: **{dano_m} de dano**!\n\n{barra_status()}\n💙 +{regen} mana ({mana_j}/{mana_jmx})",
            color=0xE24B4A
        )
        msgs_batalha.append(await interaction.followup.send(embed=embed_m, wait=True))

        turno += 1
        await asyncio.sleep(1.0)

    BATALHAS_ATIVAS.discard(uid)
    vitoria = hp_m <= 0

    xp_base = monstro["xp"]
    moedas_base = monstro["moedas"]
    
    # Salva resultado (XP, level up, etc)
    lvlups, nivel_novo, rank_mudou, rank_obj = await salvar_resultado(
        uid, hp_j, xp_base, moedas_base, vitoria, p["classe_id"], p["nivel"], mana_j
    )

    # ==================================================
    # REGISTROS PARA EVENTOS, MISSÕES E PASSE
    # ==================================================
    
    if vitoria:
        print(f"[DEBUG] Vitória registrada para {uid}")
        
        # 1. Registrar para EVENTOS
        try:
            from systems.eventos import registrar_batalha_evento
            await registrar_batalha_evento(uid)
            print(f"[DEBUG] Evento registrado para {uid}")
        except Exception as e:
            print(f"[ERRO] Falha ao registrar evento: {e}")
        
        # 2. Registrar para PASSE
        try:
            from systems.passe import adicionar_pontos_batalha
            resultado_passe = await adicionar_pontos_batalha(uid, True, "treino")
            if resultado_passe:
                print(f"[DEBUG] Passe atualizado: +{resultado_passe.get('pontos_ganhos', 0)} pontos")
        except Exception as e:
            print(f"[ERRO] Falha ao registrar passe: {e}")
        
        # 3. Registrar para MISSÕES
        try:
            from systems.missoes import atualizar_progresso
            # Missão de vitórias em treino
            recomps = await atualizar_progresso(uid, "vitorias_treino")
            print(f"[DEBUG] Missão vitorias_treino atualizada: {len(recomps)} recompensas")
            
            # Missão de treino difícil/lendário
            if monstro["dificuldade"] in ("dificil", "lendario"):
                await atualizar_progresso(uid, "treino_hard")
                print(f"[DEBUG] Missão treino_hard atualizada")
            
            # Missão de skills usadas
            await atualizar_progresso(uid, "skills_usadas", 1)
            
            # Missão de loot coletado (se o monstro dropou algo)
            if random.random() < 0.3:
                await atualizar_progresso(uid, "loots_coletados")
                print(f"[DEBUG] Missão loots_coletados atualizada")
                
        except Exception as e:
            print(f"[ERRO] Falha ao registrar missão: {e}")
        
        # 4. Registrar para CONQUISTAS
        try:
            from systems.conquistas import verificar_conquistas
            pool = await get_pool()
            async with pool.acquire() as conn:
                p_atual = await conn.fetchrow(
                    "SELECT vitorias, moedas FROM personagens WHERE user_id = $1", uid
                )
            if p_atual:
                await verificar_conquistas(uid, "vitorias", p_atual["vitorias"])
                await verificar_conquistas(uid, "moedas", p_atual["moedas"])
                print(f"[DEBUG] Conquistas verificadas: {p_atual['vitorias']} vitórias, {p_atual['moedas']} moedas")
        except Exception as e:
            print(f"[ERRO] Falha ao verificar conquistas: {e}")

    # ==================================================
    # MENSAGEM FINAL
    # ==================================================

    titulo = "🏆 Vitória!" if vitoria else "💀 Você foi derrotado!"
    cor = 0x1D9E75 if vitoria else 0xE24B4A
    desc = f"Você derrotou **{monstro['emoji']} {monstro['nome']}**!\n\n✨ **+{xp_base} XP** | 💰 **+{moedas_base} moedas**" if vitoria else "Você foi derrotado..."

    fim = discord.Embed(title=titulo, description=desc, color=cor)
    msg_fim = await interaction.followup.send(embed=fim, wait=True)

    await asyncio.sleep(1.5)
    for m in msgs_batalha:
        try:
            await m.delete()
        except:
            pass
    await asyncio.sleep(300)
    try:
        await msg_fim.delete()
    except:
        pass

    cooldown_manager.set(uid, "treinar", COOLDOWN_BATALHA)


# ==================================================
# ENGINE PVP (DUELO)
# ==================================================

async def rodar_pvp(channel, p1, p2, m1, m2, arena, callback: Callable = None):
    """Executa uma batalha PvP entre dois jogadores"""
    from data.skills import get_skill_by_id
    from data.constantes import ARENAS
    from utils.calculos import calc_dano, barra_hp
    from systems.personagem import salvar_resultado
    from views.batalha_view import BatalhaView
    
    uid1, uid2 = p1["user_id"], p2["user_id"]

    async def pegar_skills(p, uid):
        from database.queries import get_skills_equipadas
        ids = await get_skills_equipadas(uid)
        sks = [get_skill_by_id(sid) for sid in ids if get_skill_by_id(sid)]
        if not sks:
            from data.skills import SKILLS_COMPLETAS
            sks = SKILLS_COMPLETAS.get(p["classe_id"], [])[:4]
        return sks

    skills1 = await pegar_skills(p1, uid1)
    skills2 = await pegar_skills(p2, uid2)

    arma1 = await get_arma_equipada(uid1)
    armadura1 = await get_armadura_equipada(uid1)
    arma2 = await get_arma_equipada(uid2)
    armadura2 = await get_armadura_equipada(uid2)

    bonus_atk1, bonus_dfs1 = calcular_bonus_equip(p1["classe_id"], arma1, armadura1)
    bonus_atk2, bonus_dfs2 = calcular_bonus_equip(p2["classe_id"], arma2, armadura2)

    hp1 = p1["hp_atual"]
    hp1mx = p1["hp_max"]
    hp2 = p2["hp_atual"]
    hp2mx = p2["hp_max"]
    mana1 = p1.get("mana_atual", 100)
    mana1mx = p1.get("mana_max", 100)
    mana2 = p2.get("mana_atual", 100)
    mana2mx = p2.get("mana_max", 100)
    turno = 1
    efeitos1 = {}
    efeitos2 = {}
    passiva1 = Passiva(p1["classe_id"])
    passiva2 = Passiva(p2["classe_id"])
    passiva_racial1 = PassivaRacial(p1.get("raca_id", "humano"))
    passiva_racial2 = PassivaRacial(p2.get("raca_id", "humano"))
    msgs = []
    e1 = EMOJI_CLASSE.get(p1["classe_id"], "⚔️")
    e2 = EMOJI_CLASSE.get(p2["classe_id"], "⚔️")
    timeout1 = 0
    timeout2 = 0

    def barra_status_pvp():
        return (
            f"{e1} **{p1['nome']}** ❤️`{barra_hp(hp1, hp1mx)}`**{hp1}/{hp1mx}** 💙{mana1}/{mana1mx}\n"
            f"{e2} **{p2['nome']}** ❤️`{barra_hp(hp2, hp2mx)}`**{hp2}/{hp2mx}** 💙{mana2}/{mana2mx}"
        )

    embed_ini = discord.Embed(
        title=f"⚔️ Duelo PvP — {arena['emoji']} {arena['nome']}",
        description=f"**{m1.mention}** vs **{m2.mention}**\n\n{barra_status_pvp()}",
        color=arena["cor"]
    )
    msgs.append(await channel.send(embed=embed_ini))

    for t in range(1, 21):
        if hp1 <= 0 or hp2 <= 0:
            break

        # Turno p1
        if hp1 > 0:
            pocoes1 = await get_pocoes_inv(uid1)
            view1 = BatalhaView(uid1, skills1, pocoes1, nivel=p1["nivel"])
            embed_v1 = discord.Embed(
                title=f"🎮 Turno {t} — {e1} {p1['nome']}, sua vez!",
                description=barra_status_pvp(),
                color=0x7F77DD
            )
            msg_v1 = await channel.send(content=m1.mention, embed=embed_v1, view=view1)
            msgs.append(msg_v1)
            await view1.wait()

            try:
                await msg_v1.edit(view=None)
            except:
                pass

            acao1, val1 = view1.acao or ("timeout", None)
            linha = ""

            if acao1 == "atk_basico":
                mult = get_mult_basico(p1["nivel"])
                dano = calc_dano(p1["ataque"], p2["defesa"], mult, bonus_atk=bonus_atk1, nivel=p1["nivel"])
                hp2 = max(0, hp2 - dano)
                linha = f"{e1} Ataque Básico: **{dano} de dano**!"
            elif acao1 == "defesa_basica":
                add_efeito(efeitos1, "defesa_basica", 1)
                linha = f"{e1} Postura defensiva!"
            elif acao1 == "skill" and val1 is not None and val1 < len(skills1):
                sk = skills1[val1]
                if mana1 >= sk.get("mana", 0):
                    mana1 -= sk.get("mana", 0)
                    dano = calc_dano(p1["ataque"], p2["defesa"], sk.get("dano", 1.0), bonus_atk=bonus_atk1)
                    dano = int(dano * passiva1.multiplicador_dano() * passiva_racial1.multiplicador_dano())
                    hp2 = max(0, hp2 - dano)
                    linha = f"{e1} {sk['emoji']} **{sk['nome']}**: **{dano} de dano**!"
                else:
                    dano = calc_dano(p1["ataque"], p2["defesa"], 1.0, bonus_atk=bonus_atk1)
                    hp2 = max(0, hp2 - dano)
                    linha = f"{e1} Sem mana! Ataque básico: **{dano} de dano**."
            elif acao1 == "pocao" and val1:
                hp1, mana1, linha = await aplicar_efeito_pocao(val1, hp1, hp1mx, mana1, mana1mx)
                await remover_pocao(uid1, val1)
            elif acao1 == "fugir":
                embed_f = discord.Embed(title=f"{e1} {p1['nome']} fugiu!", description=f"Vitória de **{p2['nome']}**!", color=0x888780)
                await channel.send(embed=embed_f)
                for m in msgs:
                    try:
                        await m.delete()
                    except:
                        pass
                if callback:
                    await callback(p2["user_id"], p1["user_id"])
                return
            elif acao1 == "timeout":
                timeout1 += 1
                if timeout1 >= 3:
                    embed_f = discord.Embed(title=f"💤 {p1['nome']} foi expulso!", color=0x888780)
                    await channel.send(embed=embed_f)
                    if callback:
                        await callback(p2["user_id"], p1["user_id"])
                    return
                else:
                    dano = calc_dano(p1["ataque"], p2["defesa"], 1.0, bonus_atk=bonus_atk1)
                    hp2 = max(0, hp2 - dano)
                    linha = f"⏰ Auto ({timeout1}/3): **{dano} de dano**!"
            else:
                dano = calc_dano(p1["ataque"], p2["defesa"], 1.0, bonus_atk=bonus_atk1)
                hp2 = max(0, hp2 - dano)
                linha = f"⚔️ Ataque: **{dano} de dano**!"

            mana1 = min(mana1mx, mana1 + 8)
            embed_a1 = discord.Embed(
                title=f"{e1} {p1['nome']} age!",
                description=f"{linha}\n\n{barra_status_pvp()}",
                color=arena["cor"]
            )
            msgs.append(await channel.send(embed=embed_a1))

        if hp2 <= 0:
            break

        await asyncio.sleep(1.0)

        # Turno p2
        if hp2 > 0:
            pocoes2 = await get_pocoes_inv(uid2)
            view2 = BatalhaView(uid2, skills2, pocoes2, nivel=p2["nivel"])
            embed_v2 = discord.Embed(
                title=f"🎮 Turno {t} — {e2} {p2['nome']}, sua vez!",
                description=barra_status_pvp(),
                color=0xD85A30
            )
            msg_v2 = await channel.send(content=m2.mention, embed=embed_v2, view=view2)
            msgs.append(msg_v2)
            await view2.wait()

            try:
                await msg_v2.edit(view=None)
            except:
                pass

            acao2, val2 = view2.acao or ("timeout", None)
            linha = ""

            if acao2 == "atk_basico":
                mult = get_mult_basico(p2["nivel"])
                dano = calc_dano(p2["ataque"], p1["defesa"], mult, bonus_atk=bonus_atk2, nivel=p2["nivel"])
                hp1 = max(0, hp1 - dano)
                linha = f"{e2} Ataque Básico: **{dano} de dano**!"
            elif acao2 == "defesa_basica":
                add_efeito(efeitos2, "defesa_basica", 1)
                linha = f"{e2} Postura defensiva!"
            elif acao2 == "skill" and val2 is not None and val2 < len(skills2):
                sk = skills2[val2]
                if mana2 >= sk.get("mana", 0):
                    mana2 -= sk.get("mana", 0)
                    dano = calc_dano(p2["ataque"], p1["defesa"], sk.get("dano", 1.0), bonus_atk=bonus_atk2)
                    dano = int(dano * passiva2.multiplicador_dano() * passiva_racial2.multiplicador_dano())
                    hp1 = max(0, hp1 - dano)
                    linha = f"{e2} {sk['emoji']} **{sk['nome']}**: **{dano} de dano**!"
                else:
                    dano = calc_dano(p2["ataque"], p1["defesa"], 1.0, bonus_atk=bonus_atk2)
                    hp1 = max(0, hp1 - dano)
                    linha = f"{e2} Sem mana! Ataque básico: **{dano} de dano**."
            elif acao2 == "pocao" and val2:
                hp2, mana2, linha = await aplicar_efeito_pocao(val2, hp2, hp2mx, mana2, mana2mx)
                await remover_pocao(uid2, val2)
            elif acao2 == "fugir":
                embed_f = discord.Embed(title=f"{e2} {p2['nome']} fugiu!", description=f"Vitória de **{p1['nome']}**!", color=0x888780)
                await channel.send(embed=embed_f)
                for m in msgs:
                    try:
                        await m.delete()
                    except:
                        pass
                if callback:
                    await callback(p1["user_id"], p2["user_id"])
                return
            elif acao2 == "timeout":
                timeout2 += 1
                if timeout2 >= 3:
                    embed_f = discord.Embed(title=f"💤 {p2['nome']} foi expulso!", color=0x888780)
                    await channel.send(embed=embed_f)
                    if callback:
                        await callback(p1["user_id"], p2["user_id"])
                    return
                else:
                    dano = calc_dano(p2["ataque"], p1["defesa"], 1.0, bonus_atk=bonus_atk2)
                    hp1 = max(0, hp1 - dano)
                    linha = f"⏰ Auto ({timeout2}/3): **{dano} de dano**!"
            else:
                dano = calc_dano(p2["ataque"], p1["defesa"], 1.0, bonus_atk=bonus_atk2)
                hp1 = max(0, hp1 - dano)
                linha = f"⚔️ Ataque: **{dano} de dano**!"

            mana2 = min(mana2mx, mana2 + 8)
            embed_a2 = discord.Embed(
                title=f"{e2} {p2['nome']} age!",
                description=f"{linha}\n\n{barra_status_pvp()}",
                color=arena["cor"]
            )
            msgs.append(await channel.send(embed=embed_a2))

        await asyncio.sleep(1.0)

    # Resultado PvP
    if hp1 > hp2:
        vencedor, perdedor, mv, mp = p1, p2, m1, m2
        hp_v = hp1
    else:
        vencedor, perdedor, mv, mp = p2, p1, m2, m1
        hp_v = hp2

    xp_v = 80
    mo_v = 60
    await salvar_resultado(vencedor["user_id"], hp_v, xp_v, mo_v, True, vencedor["classe_id"], vencedor["nivel"])
    await salvar_resultado(perdedor["user_id"], 10, 20, 0, False, perdedor["classe_id"], perdedor["nivel"])

    # Registrar vitória PvP para eventos, missões e passe
    try:
        from systems.eventos import registrar_batalha_evento
        await registrar_batalha_evento(vencedor["user_id"])
        print(f"[DEBUG] Evento PvP registrado para {vencedor['user_id']}")
    except Exception as e:
        print(f"[ERRO] Falha ao registrar evento PvP: {e}")
    
    try:
        from systems.passe import adicionar_pontos_batalha
        await adicionar_pontos_batalha(vencedor["user_id"], True, "arena")
        print(f"[DEBUG] Passe PvP registrado para {vencedor['user_id']}")
    except Exception as e:
        print(f"[ERRO] Falha ao registrar passe PvP: {e}")
    
    try:
        from systems.missoes import atualizar_progresso
        await atualizar_progresso(vencedor["user_id"], "pvp_vitorias")
        print(f"[DEBUG] Missão pvp_vitorias atualizada para {vencedor['user_id']}")
    except Exception as e:
        print(f"[ERRO] Falha ao registrar missão PvP: {e}")

    fim = discord.Embed(
        title=f"🏆 {vencedor['nome']} vence o duelo!",
        description=f"{mv.mention} derrotou {mp.mention}!\n\n+{xp_v} XP | +{mo_v} 🪙",
        color=0xE4AF3C
    )
    await channel.send(embed=fim)

    await asyncio.sleep(1.5)
    for m in msgs:
        try:
            await m.delete()
        except:
            pass

    if callback:
        await callback(vencedor["user_id"], perdedor["user_id"])
