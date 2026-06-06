# commands/setup_cmd.py — Comando /setup para equipar itens e skills

import discord
from discord import app_commands

from database.db import get_pool
from database.queries import get_personagem, get_skills_equipadas, get_skills_desbloqueadas
from data.skills import SKILLS_COMPLETAS, get_skill_by_id
from data.armas import get_armas_classe, get_bonus_arma
from data.armaduras import get_armaduras_classe, get_bonus_armadura
from data.constantes import EMOJI_CLASSE, COR_RAR
from utils.calculos import calcular_mana_max


async def get_magias_suporte_inv(user_id: int):
    """Retorna skills de suporte desbloqueadas"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT skill_id FROM skills_desbloqueadas 
            WHERE user_id = $1 AND skill_id IN ('bencao_divina', 'cura_universal', 'escudo_magico', 'frenesi', 'muralha', 'ressurreicao_sup')
        """, user_id)
        return {r["skill_id"]: {} for r in rows}


class SetupView(discord.ui.View):
    def __init__(self, user_id, p, skills_eq, skills_desbloq, arma, armadura, magia_sup_id, magias_inv, armas_inv, armaduras_inv):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.p = p
        self.skills_eq = list(skills_eq)
        self.skills_desbloq = list(skills_desbloq)
        self.arma = arma
        self.armadura = armadura
        self.magia_sup_id = magia_sup_id
        self.magias_inv = magias_inv
        self.armas_inv = list(armas_inv)
        self.armaduras_inv = list(armaduras_inv)
        self.msg = None
        self._montar_menus()

    def _montar_menus(self):
        self.clear_items()
        
        # Skills da classe
        todas_skills = {}
        for cid, lista in SKILLS_COMPLETAS.items():
            for sk in lista:
                todas_skills[sk["id"]] = dict(sk, classe_origem=cid)

        opcoes_sk = []
        for sid in self.skills_desbloq:
            sk = todas_skills.get(sid)
            if not sk:
                continue
            mana_t = f" 💙{sk['mana']}" if sk.get("mana", 0) > 0 else ""
            compat = "✅" if sk.get("classe_origem") == self.p["classe_id"] else "⚠️"
            opcoes_sk.append(discord.SelectOption(
                label=f"{compat} {sk['emoji']} {sk['nome']}{mana_t}",
                value=sid,
                description=sk["desc"][:50],
                default=sid in self.skills_eq
            ))
        if opcoes_sk:
            sel_sk = discord.ui.Select(placeholder="⚡ Selecione até 4 skills...", min_values=0, max_values=min(4, len(opcoes_sk)), options=opcoes_sk[:25], row=0)
            sel_sk.callback = self._on_skills
            self.add_item(sel_sk)

        # Arma
        opcoes_arma = [discord.SelectOption(label="❌ Sem arma", value="none", default=self.arma is None)]
        armas_cls = get_armas_classe(self.p["classe_id"])
        armas_cls_ids = {a["id"] for a in armas_cls}
        
        for a in self.armas_inv:
            aid = a["item_id"]
            # Busca o bônus da arma no catálogo
            bonus, compat = get_bonus_arma(aid, self.p["classe_id"])
            compat_text = "✅" if compat is True else ("❌" if compat is False else "⚠️")
            opcoes_arma.append(discord.SelectOption(
                label=f"{compat_text} {a['emoji']} {a['nome']} (+{bonus} ATK)",
                value=aid,
                description=f"{a['raridade']}",
                default=self.arma is not None and self.arma["item_id"] == aid
            ))
        if len(opcoes_arma) > 1:
            sel_arma = discord.ui.Select(placeholder="⚔️ Selecione uma arma...", options=opcoes_arma[:25], row=1)
            sel_arma.callback = self._on_arma
            self.add_item(sel_arma)

        # Armadura
        opcoes_arm = [discord.SelectOption(label="❌ Sem armadura", value="none", default=self.armadura is None)]
        armaduras_cls = get_armaduras_classe(self.p["classe_id"])
        armaduras_cls_ids = {a["id"] for a in armaduras_cls}
        
        for a in self.armaduras_inv:
            aid = a["item_id"]
            bonus, compat = get_bonus_armadura(aid, self.p["classe_id"])
            compat_text = "✅" if compat is True else ("❌" if compat is False else "⚠️")
            opcoes_arm.append(discord.SelectOption(
                label=f"{compat_text} {a['emoji']} {a['nome']} (+{bonus} DEF)",
                value=aid,
                description=f"{a['raridade']}",
                default=self.armadura is not None and self.armadura["item_id"] == aid
            ))
        if len(opcoes_arm) > 1:
            sel_arm = discord.ui.Select(placeholder="🛡️ Selecione uma armadura...", options=opcoes_arm[:25], row=2)
            sel_arm.callback = self._on_armadura
            self.add_item(sel_arm)

    def _calcular_stats(self):
        """Calcula os stats finais com equipamentos"""
        atk_final = self.p["ataque"]
        dfs_final = self.p["defesa"]
        
        if self.arma:
            bonus, _ = get_bonus_arma(self.arma["item_id"], self.p["classe_id"])
            atk_final += bonus
        
        if self.armadura:
            bonus, _ = get_bonus_armadura(self.armadura["item_id"], self.p["classe_id"])
            dfs_final += bonus
        
        return atk_final, dfs_final

    def _build_embed(self):
        atk_final, dfs_final = self._calcular_stats()
        emoji_j = EMOJI_CLASSE.get(self.p["classe_id"], "⚔️")
        
        embed = discord.Embed(
            title=f"{emoji_j} Setup de {self.p['nome']}",
            description=f"**Classe:** {self.p['classe_id'].title()} — *{self.p.get('raridade', 'Comum')}*",
            color=COR_RAR.get(self.p.get("raridade", "Comum"), 0x7F77DD)
        )
        
        # Skills equipadas
        todas_skills = {}
        for cid, lista in SKILLS_COMPLETAS.items():
            for sk in lista:
                todas_skills[sk["id"]] = sk
        
        sk_txt = ""
        for i, sid in enumerate(self.skills_eq[:4]):
            sk = todas_skills.get(sid)
            if sk:
                sk_txt += f"`{i+1}` {sk['emoji']} **{sk['nome']}**\n"
        if not sk_txt:
            sk_txt = "*Nenhuma skill equipada.*"
        embed.add_field(name=f"⚡ Skills ({len(self.skills_eq[:4])}/4)", value=sk_txt, inline=False)
        
        # Arma
        if self.arma:
            bonus, compat = get_bonus_arma(self.arma["item_id"], self.p["classe_id"])
            compat_txt = "✅" if compat is True else ("❌" if compat is False else "⚠️")
            arma_txt = f"{compat_txt} {self.arma['emoji']} **{self.arma['nome']}** (+{bonus} ATK)"
        else:
            arma_txt = "*Sem arma*"
        embed.add_field(name="⚔️ Arma", value=arma_txt, inline=True)
        
        # Armadura
        if self.armadura:
            bonus, compat = get_bonus_armadura(self.armadura["item_id"], self.p["classe_id"])
            compat_txt = "✅" if compat is True else ("❌" if compat is False else "⚠️")
            armadura_txt = f"{compat_txt} {self.armadura['emoji']} **{self.armadura['nome']}** (+{bonus} DEF)"
        else:
            armadura_txt = "*Sem armadura*"
        embed.add_field(name="🛡️ Armadura", value=armadura_txt, inline=True)
        
        # Stats finais
        embed.add_field(name="📊 Stats Finais", value=f"ATK: **{atk_final}** | DEF: **{dfs_final}**", inline=False)
        
        return embed

    async def _atualizar(self, inter):
        try:
            await inter.response.defer()
        except:
            pass
        self._montar_menus()
        if self.msg:
            try:
                await self.msg.edit(embed=self._build_embed(), view=self)
            except:
                pass

    async def _on_skills(self, inter: discord.Interaction):
        if inter.user.id != self.user_id:
            await inter.response.send_message("❌ Não é seu setup!", ephemeral=True)
            return
        self.skills_eq = inter.data["values"][:4]
        await self._salvar_skills()
        await self._atualizar(inter)

    async def _on_arma(self, inter: discord.Interaction):
        if inter.user.id != self.user_id:
            await inter.response.send_message("❌ Não é seu setup!", ephemeral=True)
            return
        val = inter.data["values"][0]
        await self._salvar_equip("arma", val)
        self.arma = None if val == "none" else next((a for a in self.armas_inv if a["item_id"] == val), None)
        await self._atualizar(inter)

    async def _on_armadura(self, inter: discord.Interaction):
        if inter.user.id != self.user_id:
            await inter.response.send_message("❌ Não é seu setup!", ephemeral=True)
            return
        val = inter.data["values"][0]
        await self._salvar_equip("armadura", val)
        self.armadura = None if val == "none" else next((a for a in self.armaduras_inv if a["item_id"] == val), None)
        await self._atualizar(inter)

    async def _salvar_skills(self):
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM skills_equipadas WHERE user_id = $1 AND slot != 99", self.user_id)
            for slot, sid in enumerate(self.skills_eq[:4]):
                await conn.execute("""
                    INSERT INTO skills_equipadas(user_id, skill_id, slot)
                    VALUES($1, $2, $3)
                    ON CONFLICT(user_id, slot) DO UPDATE SET skill_id = EXCLUDED.skill_id
                """, self.user_id, sid, slot)

    async def _salvar_equip(self, tipo: str, item_id: str):
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("UPDATE inventario SET equipado = 0 WHERE user_id = $1 AND tipo = $2", self.user_id, tipo)
            if item_id and item_id != "none":
                await conn.execute("UPDATE inventario SET equipado = 1 WHERE user_id = $1 AND item_id = $2", self.user_id, item_id)

    async def on_timeout(self):
        if self.msg:
            try:
                await self.msg.edit(view=None)
            except:
                pass


async def cmd_setup(interaction: discord.Interaction):
    """Comando /setup - Configura skills e equipamentos"""
    await interaction.response.defer(ephemeral=True)
    
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("❌ Crie seu personagem primeiro!", ephemeral=True)
        return

    skills_eq = await get_skills_equipadas(interaction.user.id)
    skills_desbloq = await get_skills_desbloqueadas(interaction.user.id)
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        arma = await conn.fetchrow("SELECT * FROM inventario WHERE user_id = $1 AND tipo = 'arma' AND equipado = 1 LIMIT 1", interaction.user.id)
        armadura = await conn.fetchrow("SELECT * FROM inventario WHERE user_id = $1 AND tipo = 'armadura' AND equipado = 1 LIMIT 1", interaction.user.id)
        
        armas_inv = await conn.fetch("SELECT * FROM inventario WHERE user_id = $1 AND tipo = 'arma'", interaction.user.id)
        armaduras_inv = await conn.fetch("SELECT * FROM inventario WHERE user_id = $1 AND tipo = 'armadura'", interaction.user.id)

    magias_inv = await get_magias_suporte_inv(interaction.user.id)
    magia_sup_id = None

    view = SetupView(
        user_id=interaction.user.id, p=p,
        skills_eq=skills_eq, skills_desbloq=skills_desbloq,
        arma=arma, armadura=armadura,
        magia_sup_id=magia_sup_id, magias_inv=magias_inv,
        armas_inv=armas_inv, armaduras_inv=armaduras_inv,
    )
    
    msg = await interaction.followup.send(embed=view._build_embed(), view=view, ephemeral=True, wait=True)
    view.msg = msg
