import os
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
from telegram import Update
import speech_recognition as sr
from pydub import AudioSegment
from transformers import pipeline

# Initialize a summarization pipeline from Hugging Face
summarizer = pipeline("summarization")

def convert_ogg_to_wav(ogg_path: str, wav_path: str):
    """
    Converts an .ogg audio file to .wav format using pydub.
    """
    audio = AudioSegment.from_file(ogg_path, format="ogg")
    audio.export(wav_path, format="wav")

def transcribe_audio(wav_path: str) -> str:
    """
    Transcribes a WAV file to text using SpeechRecognition.
    """
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
    try:
        # Uses Google's free API; note this may require internet access
        text = recognizer.recognize_google(audio_data)
        return text
    except sr.UnknownValueError:
        return "Sorry, I could not understand the audio."
    except sr.RequestError as e:
        return f"Could not request results; {e}"

def voice_message_handler(update: Update, context: CallbackContext):
    """
    Handles incoming voice messages: downloads the file, converts, transcribes, and summarizes.
    """
    voice = update.message.voice
    file_id = voice.file_id
    new_file = context.bot.get_file(file_id)
    ogg_path = "voice_message.ogg"
    wav_path = "voice_message.wav"
    
    # Download the voice message from Telegram
    new_file.download(ogg_path)
    
    # Convert the .ogg file to .wav for transcription
    convert_ogg_to_wav(ogg_path, wav_path)
    
    # Transcribe the audio file
    transcription = transcribe_audio(wav_path)
    
    # Create a summary if the transcription is sufficiently long
    if len(transcription.split()) > 30:
        # Adjust max_length/min_length parameters based on your needs
        summary_result = summarizer(transcription, max_length=50, min_length=25, do_sample=False)
        summary = summary_result[0]['summary_text']
    else:
        summary = "Audio too short for summarization."
    
    # Prepare the response message
    response_message = f"Transcription:\n{transcription}\n\nSummary:\n{summary}"
    update.message.reply_text(response_message)
    
    # Clean up temporary files
    os.remove(ogg_path)
    os.remove(wav_path)

def main():
    # Replace 'YOUR_TELEGRAM_BOT_TOKEN' with your actual Telegram Bot token
    updater = Updater("YOUR_TELEGRAM_BOT_TOKEN", use_context=True)
    dp = updater.dispatcher

    # Add a handler to process voice messages
    dp.add_handler(MessageHandler(Filters.voice, voice_message_handler))
    
    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
