from flask import request, render_template, jsonify
import os
import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import which

# Set ffmpeg executable path
AudioSegment.converter = which("ffmpeg")

def init_routes(app):
    @app.route('/')
    def login():
        return render_template('registration.html')

    @app.route('/registration')
    def registration():
        return render_template('registration.html')

    @app.route('/index')
    def index():
        return render_template('index.html')

    @app.route('/upload', methods=['POST'])
    def upload_file():
        if 'audioFile' not in request.files:
            return jsonify({"error": "No file part"}), 400
        file = request.files['audioFile']
        keywords = request.form.get('keywords')  # Space-separated keywords

        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        valid_extensions = ['wav', 'mp3', 'flac', 'ogg']
        if not any(file.filename.endswith(ext) for ext in valid_extensions):
            return jsonify({"error": "Unsupported file type"}), 400

        original_file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(original_file_path)

        try:
            # Convert to WAV if necessary
            if not file.filename.endswith('.wav'):
                wav_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'converted.wav')
                audio = AudioSegment.from_file(original_file_path)
                audio.export(wav_file_path, format='wav')
                file_path = wav_file_path
            else:
                file_path = original_file_path

            recognizer = sr.Recognizer()
            with sr.AudioFile(file_path) as source:
                audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)

            # Split keywords by space, remove extra spaces, and check detection
            keyword_list = [kw.strip().lower() for kw in keywords.split()]
            detected_keywords = [kw for kw in keyword_list if kw in text.lower()]
            not_detected_keywords = [kw for kw in keyword_list if kw not in text.lower()]

            return jsonify({
                "text": text,
                "detectedKeywords": detected_keywords,
                "notDetectedKeywords": not_detected_keywords
            })
        except sr.UnknownValueError:
            return jsonify({"error": "Could not understand audio"}), 500
        except sr.RequestError as e:
            return jsonify({"error": f"Could not request results; {e}"}), 500
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
        finally:
            # Clean up uploaded files
            if os.path.exists(original_file_path):
                os.remove(original_file_path)
            if 'wav_file_path' in locals() and os.path.exists(wav_file_path):
                os.remove(wav_file_path)
