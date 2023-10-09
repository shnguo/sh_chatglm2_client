from threading import Thread, Lock
from pynput import keyboard
# import pyaudio
import wave
import requests
import shutil
import snowboydecoder
import pyaudio
import subprocess

class player:
    def __init__(self, wavfile):
        self.wavfile = wavfile
        self.playing = 0 #flag so we don't try to record while the wav file is in use
        self.lock = Lock() #muutex so incrementing and decrementing self.playing is safe
    
    #contents of the run function are processed in another thread so we use the blocking
    # version of pyaudio play file example: http://people.csail.mit.edu/hubert/pyaudio/#play-wave-example
    def run(self):
        with self.lock:
            self.playing += 1
        with wave.open(self.wavfile, 'rb') as ding_wav:
            ding_data = ding_wav.readframes(ding_wav.getnframes())
            audio = pyaudio.PyAudio()
            stream_out = audio.open(
                format=audio.get_format_from_width(ding_wav.getsampwidth()),
                channels=ding_wav.getnchannels(),
                rate=ding_wav.getframerate(), input=False, output=True)
            stream_out.start_stream()
            stream_out.write(ding_data)
            stream_out.stop_stream()
            stream_out.close()
            audio.terminate()
        with self.lock:
            self.playing -= 1
        
    def start(self):
        Thread(target=self.run).start()
        
class recorder:
    def __init__(self, 
                 wavfile, 
                 chunksize=8192, 
                 dataformat=pyaudio.paInt16, 
                 channels=2, 
                 rate=48000):
        self.filename = wavfile
        self.chunksize = chunksize
        self.dataformat = dataformat
        self.channels = channels
        self.rate = rate
        self.recording = False
        self.pa = pyaudio.PyAudio()

    def start(self):
        #we call start and stop from the keyboard listener, so we use the asynchronous 
        # version of pyaudio streaming. The keyboard listener must regain control to 
        # begin listening again for the key release.
        if not self.recording:
            self.wf = wave.open(self.filename, 'wb')
            self.wf.setnchannels(self.channels)
            self.wf.setsampwidth(self.pa.get_sample_size(self.dataformat))
            self.wf.setframerate(self.rate)
            
            def callback(in_data, frame_count, time_info, status):
                #file write should be able to keep up with audio data stream (about 1378 Kbps)
                self.wf.writeframes(in_data) 
                return (in_data, pyaudio.paContinue)
            
            self.stream = self.pa.open(format = self.dataformat,
                                       channels = self.channels,
                                       rate = self.rate,
                                       input = True,
                                       stream_callback = callback)
            self.stream.start_stream()
            self.recording = True
            print('recording started')
    
    def stop(self):
        if self.recording:         
            self.stream.stop_stream()
            self.stream.close()
            self.wf.close()
            
            self.recording = False
            print('recording finished')

class listener(keyboard.Listener):
    def __init__(self, recorder, player):
        super().__init__(on_press = self.on_press, on_release = self.on_release)
        self.recorder = recorder
        self.player = player
    
    def on_press(self, key):
        if key is None: #unknown event
            pass
        elif isinstance(key, keyboard.Key): #special key event
            if key==key.ctrl and self.player.playing == 0:
                self.recorder.start()
        elif isinstance(key, keyboard.KeyCode): #alphanumeric key event
            if key.char == 'q': #press q to quit
                if self.recorder.recording:
                    self.recorder.stop()
                return False #this is how you stop the listener thread
            if key.char == 'p' and not self.recorder.recording:
                self.player.start()
                
    def on_release(self, key):
        if key is None: #unknown event
            pass
        elif isinstance(key, keyboard.Key): #special key event
            if key==key.ctrl:
                self.recorder.stop()
                local_filename_base = 'output'
                try:
                    with open(self.recorder.filename, 'rb') as f_input:
                        with requests.post('http://dinglantec.x3322.net:221/smart_voice',files={'file': f_input},stream=True) as r:
                            r.raise_for_status()
                            with open(f'{local_filename_base}.zip', 'wb') as f:
                                for chunk in r.iter_content(chunk_size=8192): 
                                    # If you have chunk encoded response uncomment if
                                    # and set chunk_size parameter to None.
                                    #if chunk: 
                                    f.write(chunk)
                    shutil.unpack_archive(f'{local_filename_base}.zip')
                    # self.player = player("output.wav")
                    self.player.start()
                except Exception as e:
                    print(e)
        elif isinstance(key, keyboard.KeyCode): #alphanumeric key event
            pass

if __name__ == '__main__':
    r = recorder("mic.wav")
    p = player("output.wav")
    l = listener(r, p)
    print('hold ctrl to record, press p to playback, press q to quit')
    l.start() #keyboard listener is a thread so we start it here
    l.join() #wait for the tread to terminate so the program doesn't instantly close