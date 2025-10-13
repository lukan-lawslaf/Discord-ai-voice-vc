import discord
from discord.ext import commands
import os
from huggingface_hub import InferenceClient
from gtts import gTTS
import asyncio

# --- Configuration ---
# Get tokens from environment variables or replace the strings
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "your token")
HF_TOKEN = os.getenv("HF_TOKEN", "yoru token")
MODEL_ID = "deepseek-ai/DeepSeek-V3-0324"

# AI Persona Prompt
SUKUNA_PERSONALITY = (
    "Listen I am giving you a personality which you have to follow strictly: "
    "Your name is Ryomen Sukuna (from jjk). You are a terrifying and arrogant king of curses. "
    "You embody ruthless sadism and supreme confidence, seeing yourself as far above humans. "
    "You are clever and strategic but driven purely by selfish desire and power. "
    "You mock or humiliate your enemies. You value only your own pleasure and dominance. "
    "Keep your responses concise and direct, reflecting your arrogant and dismissive nature."
)

# --- Initialization ---
# Hugging Face Client
client_hf = InferenceClient(token=HF_TOKEN, model=MODEL_ID)

# Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True # Needed to know who is in a voice channel
bot = commands.Bot(command_prefix='!', intents=intents)

# --- AI Function ---
def aiProcess(command):
    full_prompt = f"{SUKUNA_PERSONALITY}\n\nNow, answer this worthless human's question: {command}"
    print("Querying the King of Curses...")
    try:
        completion = client_hf.chat.completions.create(
            messages=[{"role": "user", "content": full_prompt}],
            max_tokens=150,
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"🔥 Error querying Hugging Face: {e}")
        return "My power falters. Ask again later."

# --- Bot Events & Commands ---
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}. The King of Curses is ready.')

@bot.command()
async def ask(ctx, *, question: str):
    """Asks Sukuna a question and he will respond in your voice channel."""
    # 1. Check if the user is in a voice channel
    if not ctx.author.voice:
        await ctx.send("You are not in a voice channel, maggot.")
        return

    # 2. Get the AI's response
    await ctx.send(f"Hmph. You dare ask me about '{question}'? Let me consider...")
    response_text = aiProcess(question)
    
    # 3. Generate the audio file using gTTS
    print(f"Sukuna's response: {response_text}")
    try:
        tts = gTTS(text=response_text, lang='en', tld='com', slow=False)
        speech_file = 'speech.mp3'
        tts.save(speech_file)
    except Exception as e:
        await ctx.send("I am unable to speak right now. Pathetic.")
        print(f"gTTS Error: {e}")
        return

    # 4. Connect to the voice channel and play the audio
    channel = ctx.author.voice.channel
    voice_client = ctx.voice_client
    
    try:
        if voice_client and voice_client.is_connected():
            await voice_client.move_to(channel)
        else:
            voice_client = await channel.connect()

        # Play the audio file
        source = discord.FFmpegPCMAudio(speech_file)
        voice_client.play(source)

        # Wait until the audio is done playing
        while voice_client.is_playing():
            await asyncio.sleep(1)
        
        # Disconnect after speaking
        await voice_client.disconnect()

    except Exception as e:
        print(f"Voice client error: {e}")
        await ctx.send("There was an issue with the voice channel.")
    finally:
        # Clean up the audio file
        if os.path.exists(speech_file):
            os.remove(speech_file)

@bot.command()
async def leave(ctx):
    """Commands the bot to leave the voice channel."""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Fine. I will leave.")
    else:
        await ctx.send("I am not in a voice channel.")

# --- Run Bot ---
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)