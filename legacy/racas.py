# racas.py — Sistema de Racas completo (REBALANCEADO TEMPORADA 2)

RACAS = {
    # ── BASICAS (escolha na criacao) ─────────────────────────────
    "humano": {
        "id": "humano", "nome": "Humano", "emoji": "👤",
        "raridade": "Comum", "peso": 0,
        "desc": "Versáteis e determinados. Ganham mais XP e moedas que outras raças.",
        "lore": "Os humanos de Villa Eldoria são conhecidos pela sua resiliência e capacidade de adaptação.",
        "passiva_desc": "+10% XP e +5% moedas em batalhas e dungeons",  # REBALANCEADO
        "bonus_xp": 0.10,      # REBALANCEADO (antes 0.15)
        "bonus_moedas": 0.05,  # NOVO
        "cor": 0x888780,
        "cargos": "👤 Humano",
    },
    "anao": {
        "id": "anao", "nome": "Anão", "emoji": "🧔",
        "raridade": "Comum", "peso": 0,
        "desc": "Resistentes como pedra. Defesa natural e resistência a atordoamento.",
        "lore": "Os anões vivem nas montanhas de ferro e forjaram as melhores armas do mundo.",
        "passiva_desc": "+5 DEF fixo, 50% de resistência a atordoamento",  # REBALANCEADO
        "bonus_def": 5,        # REBALANCEADO (antes 8)
        "resist_atordoar": 0.50,  # NOVO (antes imunidade total)
        "cor": 0xD85A30,
        "cargos": "🧔 Anão",
    },
    "elfo": {
        "id": "elfo", "nome": "Elfo", "emoji": "👂",
        "raridade": "Comum", "peso": 0,
        "desc": "Ágeis e mágicos. Alta mana e precisão nos ataques.",
        "lore": "Os elfos existem desde os primórdios do mundo, guardiões do equilíbrio.",
        "passiva_desc": "+20 mana máxima, +15% chance de crítico",
        "bonus_mana": 20,
        "bonus_crit": 0.15,
        "cor": 0x1D9E75,
        "cargos": "👂 Elfo",
    },

    # ── POR ROLETA ────────────────────────────────────────────────
    "licantropo": {
        "id": "licantropo", "nome": "Licantropo", "emoji": "🐺",
        "raridade": "Incomum", "peso": 8,
        "desc": "Amaldiçoado entre homem e fera. HP baixo desencadeia transformação.",
        "lore": "Mordidos pela lua, os licantropos carregam a maldição como um presente.",
        "passiva_desc": "HP<60%: transforma (+30% ATK, imune veneno)",  # REBALANCEADO (antes 50%)
        "cor": 0x2ecc71,
        "cargos": "🐺 Licantropo",
    },
    "elfo_floresta": {
        "id": "elfo_floresta", "nome": "Elfo da Floresta", "emoji": "🌿",
        "raridade": "Incomum", "peso": 7,
        "desc": "Em harmonia com a natureza. Regeneração passiva constante.",
        "lore": "Guardiões das florestas ancestrais, conectados com a vida ao redor.",
        "passiva_desc": "Regenera 4% do HP máximo por turno",
        "cor": 0x27ae60,
        "cargos": "🌿 Elfo da Floresta",
    },
    "gigante_gelo": {
        "id": "gigante_gelo", "nome": "Gigante do Gelo", "emoji": "🧊",
        "raridade": "Raro", "peso": 5,
        "desc": "Civilização das montanhas do norte. Frio absoluto em cada golpe.",
        "lore": "Os gigantes do gelo dominaram o norte por milênios com força bruta e magia glacial.",
        "passiva_desc": "35% chance de congelar em qualquer ataque",
        "cor": 0x3498db,
        "cargos": "🧊 Gigante do Gelo",
    },
    "djinn": {
        "id": "djinn", "nome": "Djinn", "emoji": "🧞",
        "raridade": "Raro", "peso": 4,
        "desc": "Espírito elemental do deserto. Magia que penetra qualquer defesa.",
        "lore": "Seres de pura energia elemental aprisionados em forma mortal.",
        "passiva_desc": "Todas as skills ignoram 20% da defesa do inimigo",
        "cor": 0x9b59b6,
        "cargos": "🧞 Djinn",
    },
    "morto_vivo": {
        "id": "morto_vivo", "nome": "Morto-Vivo", "emoji": "🧟",
        "raridade": "Épico", "peso": 3,
        "desc": "Entre a vida e a morte. Imune a efeitos, drena HP passivamente.",
        "lore": "Reis e guerreiros que se recusaram a morrer, mantidos por vontade pura.",
        "passiva_desc": "Imune a veneno/congelar/queimadura. Ataques drenam 6% HP",
        "cor": 0x7F77DD,
        "cargos": "🧟 Morto-Vivo",
    },
    "elfo_sombrio": {
        "id": "elfo_sombrio", "nome": "Elfo Sombrio", "emoji": "🧝",
        "raridade": "Épico", "peso": 2,
        "desc": "Banidos para as cavernas, mestres das sombras e do contra-ataque.",
        "lore": "Exilados da sociedade élfica, encontraram poder nas trevas.",
        "passiva_desc": "30% chance de contra-atacar imediatamente ao tomar dano",
        "cor": 0x6c3483,
        "cargos": "🧝 Elfo Sombrio",
    },
    "draconiano": {
        "id": "draconiano", "nome": "Draconiano", "emoji": "🐉",
        "raridade": "Épico", "peso": 1,
        "desc": "Descendentes de dragões em forma humana. Escamas e fogo nas veias.",
        "lore": "Quando dragões se uniram com mortais, nasceu uma raça entre dois mundos.",
        "passiva_desc": "-12% dano recebido, imune queimadura, +10% dano de fogo",  # REBALANCEADO (antes 20%)
        "cor": 0xE67E22,
        "cargos": "🐉 Draconiano",
    },
    "anjo": {
        "id": "anjo", "nome": "Anjo", "emoji": "😇",
        "raridade": "Lendário", "peso": 1,
        "desc": "Ser celestial descendido. Ressurreição divina e aura protetora.",
        "lore": "Anjos que desceram ao mundo mortal para cumprir uma missão divina.",
        "passiva_desc": "Ressuscita com 40% HP (1x/batalha). Escudo sagrado a cada 5 turnos",
        "cor": 0xF1C40F,
        "cargos": "😇 Anjo",
    },
    "demonio": {
        "id": "demonio", "nome": "Demônio", "emoji": "😈",
        "raridade": "Lendário", "peso": 1,
        "desc": "Ser das profundezas infernais. Poder cresce nos primeiros turnos.",
        "lore": "Demônios que escaparam do inferno trazem o poder das trevas absolutas.",
        "passiva_desc": "Primeiros 10 turnos: +5% dano/turno (max +50%). Ataques causam queimadura",  # REBALANCEADO
        "cor": 0xC0392B,
        "cargos": "😈 Demônio",
    },
}

RACAS_BASICAS   = ["humano", "anao", "elfo"]
RACAS_ROLETA    = [r for r in RACAS.values() if r["peso"] > 0]
EMOJI_RAR_RACA  = {"Comum":"⬜","Incomum":"🟩","Raro":"🟦","Épico":"🟪","Lendário":"🟧"}
COR_RAR_RACA    = {"Comum":0x888780,"Incomum":0x1D9E75,"Raro":0x378ADD,"Épico":0x7F77DD,"Lendário":0xD85A30}

def get_raca(raca_id):
    return RACAS.get(raca_id, RACAS["humano"])

# ─── PASSIVA RACIAL (REBALANCEADA) ──────────────────────────────

class PassivaRacial:
    def __init__(self, raca_id):
        self.raca_id   = raca_id
        self.turno     = 0
        self.ressuscitou = False  # anjo
        self.escudo_anjo = 0     # anjo - turnos ate proximo escudo
        self.bonus_demonio = 0.0 # demonio - acumulo de dano (limitado a 10 turnos)
        self.transformado  = False # licantropo

    def inicio_turno(self, hp_j, hp_jmx):
        """Retorna (cura_passiva, escudo_ativo)"""
        self.turno += 1
        cura = 0
        escudo = False

        # Elfo da Floresta — regenera 4% HP/turno
        if self.raca_id == "elfo_floresta":
            cura = max(1, int(hp_jmx * 0.04))

        # Demônio — acumula +5% dano por turno (apenas primeiros 10 turnos, cap 50%)
        if self.raca_id == "demonio":
            if self.turno <= 10:
                self.bonus_demonio = min(0.50, self.bonus_demonio + 0.05)

        # Anjo — escudo a cada 5 turnos
        if self.raca_id == "anjo":
            if self.turno % 5 == 0:
                escudo = True

        # Licantropo — transforma se HP < 60% (REBALANCEADO)
        if self.raca_id == "licantropo":
            self.transformado = (hp_j / max(1, hp_jmx)) < 0.60

        return cura, escudo

    def multiplicador_dano(self):
        """Multiplicador adicional de dano racial"""
        if self.raca_id == "demonio":
            return 1.0 + self.bonus_demonio
        if self.raca_id == "licantropo" and self.transformado:
            return 1.30
        if self.raca_id == "draconiano":
            return 1.10  # +10% fogo
        return 1.0

    def reducao_dano(self):
        """Redução de dano recebido"""
        if self.raca_id == "draconiano":
            return 0.12  # REBALANCEADO (antes 0.20)
        if self.raca_id == "anao":
            return 0.05
        return 0.0

    def bonus_defesa_fixa(self):
        """Bônus fixo de DEF"""
        if self.raca_id == "anao":
            return 5  # REBALANCEADO (antes 8)
        return 0

    def bonus_critico(self):
        """Chance extra de crítico"""
        if self.raca_id == "elfo":
            return 0.15
        return 0.0

    def bonus_mana_max(self):
        """Bônus de mana máxima"""
        if self.raca_id == "elfo":
            return 20
        return 0

    def bonus_xp(self):
        """Multiplicador de XP ganho"""
        if self.raca_id == "humano":
            return 0.10  # REBALANCEADO (antes 0.15)
        return 0.0

    def bonus_moedas(self):
        """Multiplicador de moedas ganhas"""
        if self.raca_id == "humano":
            return 0.05  # NOVO
        return 0.0

    def imune_status(self, status):
        """Status que a raça é imune"""
        imunidades = {
            "demonio":    ["veneno", "queimadura", "congelar"],
            "draconiano": ["queimadura"],
            "morto_vivo": ["veneno", "congelar", "queimadura", "atordoar"],
            "anao":       [],  # Anão não é mais imune, apenas resistente
            "licantropo": ["veneno"] if self.transformado else [],
        }
        return status in imunidades.get(self.raca_id, [])

    def resist_atordoar(self):
        """Chance de resistir a atordoamento (Anão)"""
        if self.raca_id == "anao":
            return 0.50  # NOVO - 50% de chance de resistir
        return 0.0

    def apos_tomar_dano(self, dano, hp_j, hp_jmx, atk_inimigo):
        """Retorna (contra_ataque_dano, dreno_hp)"""
        contra = 0
        dreno = 0

        # Elfo Sombrio — 30% contra-ataque
        if self.raca_id == "elfo_sombrio" and __import__("random").random() < 0.30:
            contra = max(5, int(atk_inimigo * 0.40))

        # Morto-Vivo — drena 6% do HP ao atacar
        if self.raca_id == "morto_vivo":
            dreno = max(1, int(hp_jmx * 0.06))

        return contra, dreno

    def congelar_ao_atacar(self):
        """Gigante do Gelo — 35% chance de congelar"""
        if self.raca_id == "gigante_gelo":
            return __import__("random").random() < 0.35
        return False

    def ignorar_defesa(self):
        """Djinn — ignora 20% da defesa"""
        if self.raca_id == "djinn":
            return 0.20
        return 0.0

    def tentar_ressuscitar(self, hp_j):
        """Anjo — ressurreição única"""
        if self.raca_id == "anjo" and hp_j <= 0 and not self.ressuscitou:
            self.ressuscitou = True
            return True
        return False

    def modificar_dano_recebido(self, dano):
        """Aplica redução de dano e retorna (dano_final, mensagem)"""
        reducao = self.reducao_dano()
        if reducao > 0:
            dano_final = max(1, int(dano * (1 - reducao)))
            return dano_final, f"🛡️ Redução de dano: -{int(reducao*100)}%"
        return dano, ""

    def desc_passiva(self):
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
