import discord
from discord.ext import commands

@commands.command()
async def reload(ctx):
    """Recharge toutes les commandes (Admin uniquement)"""
    if ctx.author.guild_permissions.administrator:
        try:
            # Réimportez et rechargez les commandes
            from all_commands import setup_commands
            import importlib
            importlib.reload(importlib.import_module('all_commands'))
            
            # Supprimez toutes les commandes actuelles
            for cog in list(ctx.bot.cogs):
                ctx.bot.remove_cog(cog)
            
            # Rechargez les commandes
            setup_commands(ctx.bot)
            
            await ctx.send("✅ Toutes les commandes ont été rechargées !")
        except Exception as e:
            await ctx.send(f"❌ Erreur lors du rechargement : {e}")
    else:
        await ctx.send("❌ Vous n'avez pas les permissions requises.")
