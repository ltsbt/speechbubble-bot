import os
import discord
import aiohttp
import io
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageSequence
from dotenv import load_dotenv

load_dotenv()

# CHANGE THIS TO YOUR PREFIX
COMMAND_PREFIX = "$"

# SET YOUR BOT TOKEN IN THE .env FILE
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)


def create_speech_bubble_image(image_path, output_path):
    with Image.open(image_path) as im:
        speech_bubble = Image.open("speech_bubble.png").convert("RGBA")
        speech_bubble = speech_bubble.resize(
            (im.width, im.height // 3), Image.ANTIALIAS
        )

        if im.format == "GIF":
            frames = []
            for frame in ImageSequence.Iterator(im):
                frame = frame.convert("RGBA")
                frame.paste(
                    speech_bubble, (0, 0), speech_bubble
                )
                frames.append(frame)

            frames[0].save(
                output_path,
                save_all=True,
                append_images=frames[1:],
                duration=im.info["duration"],
                loop=0,
            )
        else:
            im.paste(speech_bubble, (0, 0), speech_bubble)
            im.save(output_path)


async def process_url_image(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                buffer = io.BytesIO(await resp.read())
                buffer.seek(0)
                return buffer
            else:
                return None


async def process_image(ctx, attachment):
    image_path = f"images/{attachment.filename}"
    output_path = f"images/modified_{attachment.filename}"

    await attachment.save(image_path)
    create_speech_bubble_image(image_path, output_path)

    with open(output_path, "rb") as f:
        await ctx.send(file=discord.File(f))


def cleanup(image_path, output_path):
    try:
        os.remove(image_path)
        os.remove(output_path)
    except Exception as e:
        print(f"Error during cleanup: {e}")


@bot.command()
async def sb(ctx):
    if ctx.message.attachments:
        await process_image(ctx, ctx.message.attachments[0])
        cleanup(image_path, output_path)
    elif ctx.message.embeds and ctx.message.embeds[0].type in ('image', 'gifv'):
        buffer = await process_url_image(ctx.message.embeds[0].url)
        if buffer:
            image_path = f'images/url_image_{ctx.message.embeds[0].url.rsplit(".", 1)[-1]}'
            output_path = f'images/modified_url_image_{ctx.message.embeds[0].url.rsplit(".", 1)[-1]}'

            with open(image_path, 'wb') as f:
                f.write(buffer.getbuffer())

            create_speech_bubble_image(image_path, output_path)

            with open(output_path, 'rb') as f:
                await ctx.send(file=discord.File(f))
            cleanup(image_path, output_path)
        else:
            await ctx.send("The image could not be fetched.")
    elif ctx.message.reference:
        referenced_message = await ctx.channel.fetch_message(
            ctx.message.reference.message_id
        )

        if referenced_message.attachments:
            await process_image(ctx, referenced_message.attachments[0])
        elif referenced_message.embeds and referenced_message.embeds[0].type in ("image", "gifv"):
            buffer = await process_url_image(referenced_message.embeds[0].url)
            if buffer:
                image_path = f'images/url_image_{referenced_message.embeds[0].url.rsplit(".", 1)[-1]}'
                output_path = f'images/modified_url_image_{referenced_message.embeds[0].url.rsplit(".", 1)[-1]}'

                with open(image_path, "wb") as f:
                    f.write(buffer.getbuffer())

                create_speech_bubble_image(image_path, output_path)

                with open(output_path, "rb") as f:
                    await ctx.send(file=discord.File(f))
                cleanup(image_path, output_path)
            else:
                await ctx.send("The image could not be fetched.")
        else:
            await ctx.send("The replied message doesn't contain an image.")
    else:
        await ctx.send(
            "Please reply to a message containing an image with the command $sb."
        )


bot.run(TOKEN)
