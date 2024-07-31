import asyncio
from pyrogram import Client, filters
import os
from pydub import AudioSegment
import speech_recognition as sr
from pydub.utils import which
from traceback import format_exc as _format_exc
import subprocess
import json
from vllm import LLM, SamplingParams

llm = LLM(model="MehdiHosseiniMoghadam/AVA-Llama-3-V2", gpu_memory_utilization=0.9, trust_remote_code=True)

def generate_car_json(product):
    # Define the prompt
    prompt = """Here is a car introduction from an Iranian marketplace.
Please extract the Product Entity and all relevant Attributes of this product in Persian language.
mileage is the distance that a car has gone, e.g: 130KM and so on
Provide the output in this JSON format in Persian:
{'product_entity': '<product entity>', 'attributes': {'<attribute_name>': '<attribute_value>', ...}}.
Ensure to include 'brand' as one of the common brands in the world such as Benz, Honda, Golf, Hyundai, and so on based on the context provided in the text.
Ensure that all attributes, including 'price', are present and correctly formatted if it is mentioned.
body_conditions include Driver side door, passenger side door, chisses, font and rear chassis and so on.
Ensure to report body_conditions.
The JSON format must be in Farsi language.
Don't make assumptions about what values to plug into JSON. Just provide the JSON without any additional text.
\nProduct title:"""

    user_prompt_template = '### Introduction: '
    response_template = """### attributes:
    {
    "product_entity": "سمند سورن ۱۴۰۲",
    "attributes": {
    "brand": "سمند",
    "model": "سورن",
    "year": "۱۴۰۲",
    "color": "مشکی",
    "body_conditions": "شاسی جلو خورده و درب عقب رنگ شدگی دارد و در جلو لکه گیری",
    "options": "سنسور و دربین عقب، صندلی گرم کن ، رادار تشخیص خطوط و کروز کنترل",
    "audio_system": "ضبط صوت جی بی ال",
    "price": "سه میلیار و ششصد"
    }
    }"""

    # Combine the prompt and the product title
    input_text = prompt + product
    full_prompt = f'{user_prompt_template}{input_text}\n{response_template}'

    # Define initial max_tokens
    max_tokens = 200
    sampling_params = SamplingParams(temperature=0.0, max_tokens=200)
# Combine the prompt and the product title
    input_text = prompt + product
    prompt = f'{user_prompt_template} {prompt}{product}\n {response_template}'
    outputs = llm.generate(prompt, sampling_params)

    return outputs[0].outputs[0].text


# AudioSegment.converter = which("ffmpeg") or which("avconv")
app = Client("my_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

async def progress(current, total):
    print(f"{current * 100 / total:.1f}%")

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("""
    سلام!
لطفا یک فایل صوتی بفرستید.""")

@app.on_message(filters.audio | filters.voice)
async def handle_audio(client, message):
    processing_message = await message.reply('لطفا منتظر بمانید ...')
    basePath = '/content/downloads'
    for item in os.listdir(basePath):
        os.remove(os.path.join(basePath, item))
    await app.download_media(message, progress=progress)
    audio_path = os.listdir(basePath)[0]
    print('Path: ', os.path.join(basePath, audio_path))
    audio = AudioSegment.from_file(os.path.join(basePath, audio_path))
    audio.export(os.path.join(basePath, 'audio.wav'), format='wav')
    r = sr.Recognizer()
    try:
        # Now use the WAV file with SpeechRecognition
        with sr.AudioFile(os.path.join(basePath, 'audio.wav')) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data, language='fa-IR')
    except Exception as e:
        print(f"Error recognizing audio: {e}")
        text = ''
    await processing_message.delete()
    product_text = f"\n{text}\n"  # Ensure the text is formatted correctly
    finalData = generate_car_json(product_text)
    await message.reply_text('وویس به متن: ' + text)
    await message.reply_text('استخراج ویژگی ها: ' + finalData)
    for item in os.listdir(basePath):
        os.remove(os.path.join(basePath, item))

app.run()
