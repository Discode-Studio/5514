import discord
from discord.ext import commands
import os
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import subprocess

# Configuration du bot Discord
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# URL de la page Web qui diffuse l'audio
uvb_stream_url = 'http://websdr.ewi.utwente.nl:8901/?tune=5514am'

# Fonction pour capturer l'audio à partir d'une page Web avec Selenium et FFmpeg
async def play_uvb_stream(vc):
    if not vc.is_playing():
        # Configurer Selenium pour lancer un navigateur headless
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--autoplay-policy=no-user-gesture-required")
        
        driver = webdriver.Chrome(options=options)
        driver.get(uvb_stream_url)
        
        # Utiliser FFmpeg pour capturer le son du navigateur
        ffmpeg_command = [
            'ffmpeg', '-f', 'pulse', '-i', 'default', '-ac', '2', '-f', 's16le', '-ar', '48000', '-acodec', 'pcm_s16le', '-'
        ]

        process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE)

        # Utilisation de discord.PCMAudio pour streamer l'audio
        stream_source = discord.PCMAudio(process.stdout)
        vc.play(stream_source)
    else:
        print("Stream déjà en cours.")

# Event on_ready pour afficher que le bot est prêt et rejoindre le canal vocal automatiquement
@bot.event
async def on_ready():
    print(f'Connecté en tant que {bot.user.name}')

    # Parcourir tous les serveurs auxquels le bot est connecté
    for guild in bot.guilds:
        # Vérifier si un salon vocal "5514 kHz" existe
        voice_channel = discord.utils.get(guild.voice_channels, name="5514 kHz")
        
        if voice_channel:
            # Connecter le bot au salon vocal
            vc = await voice_channel.connect()

            # Diffuser le stream UVB-76
            await play_uvb_stream(vc)
        else:
            # Créer le canal "5514 kHz" s'il n'existe pas
            voice_channel = await guild.create_voice_channel("5514 kHz")
            vc = await voice_channel.connect()

            # Diffuser le stream UVB-76
            await play_uvb_stream(vc)

    # Vérifier toutes les 10 secondes si de nouveaux serveurs ont un canal "5514 kHz"
    while True:
        await asyncio.sleep(10)
        for guild in bot.guilds:
            voice_channel = discord.utils.get(guild.voice_channels, name="5514 kHz")

            if not voice_channel:
                # Si un canal vocal "5514 kHz" n'existe pas, le créer
                voice_channel = await guild.create_voice_channel("5514 kHz")
                vc = await voice_channel.connect()
                await play_uvb_stream(vc)
            else:
                # Se reconnecter si déconnecté
                if not guild.voice_client or not guild.voice_client.is_connected():
                    vc = await voice_channel.connect()
                    await play_uvb_stream(vc)

# Le token est récupéré depuis une variable d'environnement
bot.run(os.getenv('DISCORD_BOT_TOKEN'))
