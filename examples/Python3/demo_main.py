import snowboydecoder
import sys
import signal
import speech_recognition as sr
import os
import requests
import shutil

"""
This demo file shows you how to use the new_message_callback to interact with
the recorded audio after a keyword is spoken. It uses the speech recognition
library in order to convert the recorded audio into text.

Information on installing the speech recognition library can be found at:
https://pypi.python.org/pypi/SpeechRecognition/
"""


interrupted = False
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=0)
session.mount('http://', adapter)

def audioRecorderCallback(fname):
    local_filename_base = 'output'
    try:
        with open(fname, 'rb') as f_input:
            with requests.post('http://dinglantec.x3322.net:221/smart_voice',files={'file': f_input},stream=True) as r:
                r.raise_for_status()
                with open(f'{local_filename_base}.zip', 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): 
                        # If you have chunk encoded response uncomment if
                        # and set chunk_size parameter to None.
                        #if chunk: 
                        f.write(chunk)
        shutil.unpack_archive(f'{local_filename_base}.zip')
        snowboydecoder.play_audio_file(f'{local_filename_base}.wav')
    except Exception as e:
        print(e)
    # print("converting audio to text")
    # r = sr.Recognizer()
    # with sr.AudioFile(fname) as source:
    #     audio = r.record(source)  # read the entire audio file
    # # recognize speech using Google Speech Recognition
    # try:
    #     # for testing purposes, we're just using the default API key
    #     # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
    #     # instead of `r.recognize_google(audio)`
    #     print(r.recognize_google(audio))
    # except sr.UnknownValueError:
    #     print("Google Speech Recognition could not understand audio")
    # except sr.RequestError as e:
    #     print("Could not request results from Google Speech Recognition service; {0}".format(e))

    os.remove(fname)

# audioRecorderCallback('output1689931722.wav')
# exit()


def detectedCallback():
  print('recording audio...', end='', flush=True)
  snowboydecoder.play_audio_file(snowboydecoder.DETECT_DING)
  snowboydecoder.play_audio_file(snowboydecoder.DETECT_DONG)

def signal_handler(signal, frame):
    global interrupted
    interrupted = True


def interrupt_callback():
    global interrupted
    return interrupted

if len(sys.argv) == 1:
    print("Error: need to specify model name")
    print("Usage: python demo.py your.model")
    sys.exit(-1)

model = sys.argv[1]

# capture SIGINT signal, e.g., Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

detector = snowboydecoder.HotwordDetector(model, sensitivity=[0.8,0.80],apply_frontend=True)
print('Listening... Press Ctrl+C to exit')

# main loop
detector.start(detected_callback=detectedCallback,
               audio_recorder_callback=audioRecorderCallback,
               interrupt_check=interrupt_callback,
               sleep_time=0.1,silent_count_threshold=6,
              recording_timeout=80)

detector.terminate()




