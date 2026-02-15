import streamlit as st
import whisper
import os
from streamlit_mic_recorder import mic_recorder
from pydub import AudioSegment, effects

# NEW MOVIEPY 2.0 IMPORTS
from moviepy.video.VideoClip import ColorClip, TextClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

# --- PAGE CONFIG ---
st.set_page_config(page_title="Sovereign Studio", page_icon="🎙️", layout="wide")
st.title("🎙️ Sovereign Studio")

# ... (keep your process_audio function as is) ...

# --- UPDATED VIDEO ENGINE ---
def create_video(audio_path, transcript):
    audio = AudioFileClip(audio_path)
    duration = min(audio.duration, 60)
    
    # Background
    bg = ColorClip(size=(1080, 1920), color=(20, 20, 20)).set_duration(duration)
    
    # Caption (Sovereign Gold)
    txt = TextClip(
        text=transcript[:150] + "...", 
        font_size=70, 
        color='gold', 
        method='caption',
        size=(900, None)
    ).set_duration(duration).set_position('center')
    
    video = CompositeVideoClip([bg, txt]).set_audio(audio.subclip(0, duration))
    video_path = "promo_snippet.mp4"
    
    # Video write
    video.write_videofile(video_path, fps=24, codec="libx264", audio_codec="aac")
    return video_path
    
