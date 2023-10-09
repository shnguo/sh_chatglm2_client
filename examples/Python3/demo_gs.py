import requests
import snowboydecoder
# r = requests.get('http://192.168.0.48:30001/snowboy',stream=True)
local_filename = 'test.wav'
with requests.get('http://192.168.0.48:30001/snowboy', stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                #if chunk: 
                f.write(chunk)
snowboydecoder.play_audio_file(local_filename)

