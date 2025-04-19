# 🎤 IELTS-Speaking-Bot
An AI-powered interactive bot that simulates a full IELTS Speaking test (Parts 1, 2, and 3) using voice input and spoken responses. The bot evaluates English proficiency, provides real-time grammar corrections, and gives a detailed band score breakdown based on user responses.

## ✨ Features
🎙️ Voice Input & Output: Speak your answers and hear the examiner’s questions using speech_recognition and ElevenLabs TTS.

🤖 IELTS-style Interactions: Mimics a real IELTS speaking test with realistic examiner questions for Parts 1, 2, and 3.

🧠 Smart Feedback: Detects and corrects grammatical errors using the Groq LLM (llama3-8b).

📊 Band Score Evaluation: Calculates band scores for fluency, grammar, vocabulary, and pronunciation (inferred), and provides an overall score.

📝 Transcript & Logs: Saves your answers and corrections for review after the session.

## 📦 Tech Stack
- Python
- Groq LLM (LLaMA3) – for question generation, correction, and evaluation
- ElevenLabs API – for text-to-speech responses
- SpeechRecognition + Google Speech API – for converting user speech to text
- Pydub – to play audio responses
- dotenv – for managing API keys

## 🚀 How It Works
- The bot starts with Part 1 and asks typical warm-up questions.
- After 5 questions, it transitions to Part 2 with a cue card and preparation time.
- It then proceeds to Part 3 with abstract follow-up questions.
- At the end, it calculates and speaks out your IELTS band evaluation.


## 🛠️ Setup
Clone the repository:
- git clone https://github.com/yourusername/ielts-speaking-bot.git
- cd ielts-speaking-bot

Create a .env file and add your API keys:
- GROQ_API_KEY=your_groq_key
- ELEVENLABS_API_KEY=your_elevenlabs_key

Install dependencies:
- pip install -r requirements.txt

Run the bot:
- python main.py


## 📁 Output
- ielts_log.txt – Records all user inputs and grammar corrections.
- ielts_transcript.txt – Saves a transcript of the user's full test responses.

## 🧠 Ideal For
- IELTS aspirants looking for practice with AI
- Language learners aiming to improve spoken fluency
- Developers exploring voice + LLM integrations
