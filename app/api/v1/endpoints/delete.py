# tts_test.py
import io
import wave
import os
from google import genai
from google.genai import types

from dotenv import load_dotenv


# Убедись, что установлена переменная окружения с ключом:
# export GENAI_API_KEY="твой_ключ_от_Google_GenerativeAI"
load_dotenv()
print(os.getenv("GOOGLE_API_KEY"))
# Настройка клиента
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Функция для сохранения WAV файла
def save_wav(filename: str, pcm: bytes, channels=1, rate=24000, sample_width=2):
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)
    print(f"✅ Аудио сохранено в {filename}, длина {len(pcm)} байт")

# Текст для озвучивания
text_to_speak = "Prepáčte, nerozumela som. Môžete zopakovať?"

# Генерация TTS
response = client.models.generate_content(
    model="gemini-2.5-flash-preview-tts",
    contents=text_to_speak,
    config=types.GenerateContentConfig(
        response_modalities=["AUDIO"],  # важно для TTS
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Kore"  # можно выбрать другой голос
                )
            )
        )
    )
)

# Получаем аудиоданные
audio_bytes = response.candidates[0].content.parts[0].inline_data.data

# Сохраняем в WAV
save_wav("repeat.wav", audio_bytes)
