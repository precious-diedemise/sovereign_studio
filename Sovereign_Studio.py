import streamlit as st
import whisper
import os
from streamlit_mic_recorder import mic_recorder
from pydub import AudioSegment, effects

# Modern MoviePy 2.0+ Imports
from moviepy.video.VideoClip import ColorClip, TextClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

# --- PAGE CONFIG ---
st.set_page_config(page_title="Sovereign Studio", page_icon="🎙️", layout="wide")
st.title("🎙️ Sovereign Studio")

# --- CORE AUDIO ENGINE ---
def process_audio(voice_path, music_path, music_volume, noise_reduction):
    # Load and Normalize Voice
    voice = AudioSegment.from_file(voice_path)
    voice = effects.normalize(voice)
    
    # Apply Noise Reduction (High Pass Filter)
    if noise_reduction > 0:
        voice = voice.high_pass_filter(noise_reduction)
    
    # Handle Background Music
    if os.path.exists(music_path) and os.path.getsize(music_path) > 0:
        try:
            bg = AudioSegment.from_file(music_path)
            
            # Multiplication loops the audio until it's longer than the voice
            repeats = (len(voice) // len(bg)) + 1
            bg_repeated = bg * repeats
            
            # Trim music to match voice exactly and adjust volume
            bg_final = bg_repeated[:len(voice)] + music_volume
            
            # Merge voice and music
            final_mix = voice.overlay(bg_final)
        except Exception as e:
            st.error(f"Music Mix Error: {e}")
            final_mix = voice
    else:
        final_mix = voice
        
    output_path = "processed_audio.mp3"
    final_mix.export(output_path, format="mp3", bitrate="192k")
    return output_path

# --- CORE VIDEO ENGINE ---
def create_video(audio_path, transcript):
    audio = AudioFileClip(audio_path)
    duration = min(audio.duration, 60)
    
    # Background: Sovereign Dark Aesthetic
    bg = ColorClip(size=(1080, 1920), color=(20, 20, 20)).set_duration(duration)
    
    # Caption: Sovereign Gold Text
    txt = TextClip(
        text=transcript[:150] + "...", 
        font_size=70, 
        color='gold', 
        method='caption',
        size=(900, None)
    ).set_duration(duration).set_position('center')
    
    video = CompositeVideoClip([bg, txt]).set_audio(audio.subclip(0, duration))
    video_path = "promo_snippet.mp4"
    
    # Exporting Video
    video.write_videofile(video_path, fps=24, codec="libx264", audio_codec="aac")
    return video_path

# --- APP INTERFACE (TABS) ---
tab1, tab2, tab3 = st.tabs(["1. Record/Upload", "2. Mix & Transcribe", "3. Export Video"])

with tab1:
    st.subheader("🎤 Step 1: Input Voice")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Live Record**")
        audio_record = mic_recorder(start_prompt="🔴 Start", stop_prompt="⏹️ Stop", key='recorder')
        if audio_record:
            with open("raw_audio.wav", "wb") as f: f.write(audio_record['bytes'])
            st.success("Voice captured!")
    with col2:
        st.write("**Upload Audio**")
        up_voice = st.file_uploader("Choose voice file", type=["mp3", "wav"])
        if up_voice:
            with open("raw_audio.wav", "wb") as f: f.write(up_voice.getbuffer())
            st.success("File uploaded!")

with tab2:
    if os.path.exists("raw_audio.wav"):
        st.subheader("🎚️ The Studio Mixer")
        up_bg = st.file_uploader("Upload Background Music (MP3)", type=["mp3"])
        if up_bg:
            with open("background.mp3", "wb") as f: f.write(up_bg.getbuffer())
            st.success("Music loaded!")

        col_v, col_n = st.columns(2)
        with col_v:
            vol = st.slider("Music Volume", -40, -10, -25)
        with col_n:
            noise = st.selectbox("Noise Cleanup", [0, 80, 150], format_func=lambda x: "None" if x==0 else "Standard")
        
        if st.button("✨ Mix & Transcribe"):
            with st.spinner("AI Processing..."):
                final_audio = process_audio("raw_audio.wav", "background.mp3", vol, noise)
                model = whisper.load_model("small")
                result = model.transcribe("raw_audio.wav", fp16=False, language='en')
                st.session_state['transcript'] = result['text']
                st.audio(final_audio)
        
        if 'transcript' in st.session_state:
            st.session_state['transcript'] = st.text_area("Edit Transcript:", value=st.session_state['transcript'], height=200)
    else:
        st.info("Record or upload your voice in Tab 1 first.")

with tab3:
    if 'transcript' in st.session_state:
        if st.button("🎬 Generate Video Snippet"):
            with st.spinner("Rendering..."):
                v_file = create_video("processed_audio.mp3", st.session_state['transcript'])
                st.video(v_file)
                with open(v_file, "rb") as f:
                    st.download_button("Download Video", f, "sovereign_promo.mp4")
