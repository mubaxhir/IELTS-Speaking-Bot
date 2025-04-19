import os
import speech_recognition as sr
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime
import time
import requests
from elevenlabs import ElevenLabs, VoiceSettings
from pydub import AudioSegment
from pydub.playback import play
import io

# Load environment variables
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")

# Initialize Groq client
client = Groq(api_key=groq_api_key)

# Initialize ElevenLabs client
elevenlabs_client = ElevenLabs(api_key=elevenlabs_api_key)

# Initialize speech recognizer
recognizer = sr.Recognizer()

# Global state variables
question_count = 0
part = 1
topic_history = []
user_responses = []

LOG_FILE = "ielts_log.txt"
TRANSCRIPT_FILE = "ielts_transcript.txt"

def log_interaction(user_input, correction, part):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"\n[{timestamp}] PART {part}\nUser: {user_input}\nCorrection: {correction}\n")

def listen_to_user():
    """Listen to the user's voice and convert it to text."""
    with sr.Microphone() as source:
        print("Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        recognizer.energy_threshold = 300
        recognizer.pause_threshold = 1.5  # Increased pause tolerance

        print("Listening... You can speak for up to 90 seconds.")
        try:
            audio = recognizer.listen(source, timeout=15, phrase_time_limit=90)
        except Exception as e:
            print(f"Listening error: {e}")
            return None

    try:
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Could not understand the audio.")
        return None
    except sr.RequestError as e:
        print(f"API error: {e}")
        return None

def correct_english(user_input):
    prompt = f"""
    You are an IELTS Speaking tutor providing brief, professional feedback.
    
    The candidate said: "{user_input}"
    
    If the English is correct, simply state "Correct."
    If there are errors, only provide the corrected version of what they said without explanation.
    Do not use emojis, praise, or extended commentary.
    """
    
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100
    )
    return response.choices[0].message.content.strip()

def generate_response(user_input, part=1, topic=None):
    prompt = f"""
    As an IELTS Examiner for Part {part}, respond to: "{user_input}"
    
    RULES:
    - Keep questions concise and realistic
    - Use natural examiner phrasing
    - Ask only ONE question per response
    - No praise, feedback, or commentary
    
    For Part 1: Ask direct questions about familiar personal topics (home, family, work, hobbies).
    For Part 2: If no topic given, provide a concise cue card with 3-4 bullet points.
    For Part 3: Ask follow-up abstract/opinion questions related to the Part 2 topic.
    
    Response should be only the examiner's next question or cue card.
    """
    
    if topic:
        prompt += f"\nCurrent topic: {topic}"

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150
    )
    return response.choices[0].message.content.strip()

def speak(text):
    """Convert text to speech using ElevenLabs API and play the audio."""
    try:
        # Generate audio using ElevenLabs
        audio_stream = elevenlabs_client.text_to_speech.convert(
            voice_id="pNInz6obpgDQGcFmaJgB",  # Example voice ID (Adam); replace with your preferred voice
            text=text,
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.5,
                style=0.0,
                use_speaker_boost=True
            )
        )

        # Save audio to a temporary file
        audio_file = "temp_audio.mp3"
        with open(audio_file, "wb") as f:
            for chunk in audio_stream:
                f.write(chunk)

        # Play audio using pydub
        audio = AudioSegment.from_file(audio_file)
        play(audio)

        # Clean up temporary file
        os.remove(audio_file)

    except Exception as e:
        print(f"ElevenLabs TTS error: {e}")
        # Fallback: Print the text if TTS fails
        print(f"Fallback (text): {text}")

def evaluate_band_score(responses):
    joined = "\n".join(responses)
    prompt = f"""
    Evaluate this IELTS Speaking test transcript:

    {joined}

    Provide:
    1. Band scores (0-9) for:
       - Fluency and Coherence
       - Lexical Resource
       - Grammatical Range and Accuracy
       - Pronunciation (inferred from language use)
    2. Overall band score with brief explanation
    
    Be concise and realistic in your assessment.
    """
    
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    return response.choices[0].message.content.strip()

def save_transcript(responses):
    with open(TRANSCRIPT_FILE, "w", encoding="utf-8") as f:
        for i, r in enumerate(responses, 1):
            f.write(f"Response {i}: {r}\n")

def main():
    global question_count, part

    print("IELTS Practice Bot started!")
    speak("Let's begin with Part 1. Can you tell me your full name, please?")

    retry_count = 0
    current_topic = None
    waiting_for_part2_response = False
    part2_prep_done = False

    while True:
        user_input = listen_to_user()

        if user_input is None:
            retry_count += 1
            if retry_count >= 3:
                speak("There seems to be an issue with the microphone. Let's end the session.")
                break
            speak("I didn't catch that. Could you please repeat?")
            continue
        
        retry_count = 0

        if "exit" in user_input.lower() or "stop" in user_input.lower():
            speak("Thank you for your time. This concludes the speaking test.")
            break

        user_responses.append(user_input)

        # Process correction quietly
        correction = correct_english(user_input)
        # Only speak correction if it's not just "Correct."
        if correction.lower() != "correct." and correction.lower() != "correct":
            speak(correction)
            print(f"Correction: {correction}")
            time.sleep(1)  # Brief pause after correction

        log_interaction(user_input, correction, part)

        # Special handling for part 2
        if part == 2:
            # First time entering Part 2
            if not current_topic:
                current_topic = generate_response("", part)
                speak(current_topic)
                print(f"Examiner (Part 2 Topic): {current_topic}")
                topic_history.append(current_topic)
                
                # Give preparation time
                speak("You have one minute to prepare. You can make notes if you wish.")
                print("Preparation time: 1 minute")
                time.sleep(5)  # Shortened for testing (would be 60 seconds in real test)
                
                speak("Now, please begin speaking.")
                waiting_for_part2_response = True
                continue
            
            # After candidate has given their Part 2 monologue
            elif waiting_for_part2_response:
                # Check if user signaled they're done or just continue after a reasonable response
                if "done" in user_input.lower() or "finish" in user_input.lower() or len(user_input) > 100:
                    part = 3
                    waiting_for_part2_response = False
                    question_count = 0
                    
                    speak("Thank you. Now, let's discuss some more questions related to this topic.")
                    response = generate_response("", part, topic=current_topic)
                    speak(response)
                    print(f"Examiner (Part 3): {response}")
                    continue
                else:
                    # If response was too short, prompt them to continue
                    speak("Please continue with your response.")
                    continue

        # Normal progression between parts
        question_count += 1
        
        # Move from Part 1 to Part 2 after sufficient questions
        if part == 1 and question_count >= 5:
            part = 2
            question_count = 0
            current_topic = None  # Reset topic to trigger Part 2 cue card
            speak("Thank you. Now, let's move on to Part 2.")
            continue
            
        # End test after sufficient Part 3 questions
        elif part == 3 and question_count >= 5:
            speak("Thank you. That is the end of the speaking test.")
            break

        # Normal flow for Parts 1 and 3
        response = generate_response(user_input, part, topic=current_topic)
        speak(response)
        print(f"Examiner (Part {part}): {response}")

    if user_responses:
        print("\nCalculating your band score...")
        score = evaluate_band_score(user_responses)
        print("\n=== IELTS Band Evaluation ===")
        print(score)
        speak("Here is your IELTS band evaluation.")
        speak(score)
        save_transcript(user_responses)
        print("\nTranscript saved to:", TRANSCRIPT_FILE)

if __name__ == "__main__":
    main()