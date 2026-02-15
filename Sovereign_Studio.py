import streamlit as st
import whisper
import os
import requests
from streamlit_mic_recorder import mic_recorder
from pydub import AudioSegment, effects
from moviepy.video.VideoClip import ColorClip, TextClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

# --- PAGE CONFIG ---
st.set_page_config(page_title="Sovereign Studio", page_icon="🎙️", layout="wide")
st.title("🎙️ Sovereign Studio")
st.markdown("### *Professional Finance Media Lab*")

# --- FUNCTIONS ---
def process_audio(file_path, bg_music_path, music_volume, noise_reduction):
    voice = AudioSegment.from_file(file_path)
    voice = effects.normalize(voice)
    
    # Noise Reduction
    if noise_reduction > 0:
        voice = voice.high_pass_filter(noise_reduction)
    
    # Mix Background Music
    if bg_music_path and os.path.exists(bg_music_path):
        try:
            bg = AudioSegment.from_file(bg_music_path)
            bg = bg.loop(duration=len(voice)) + music_volume 
            final_mix = voice.overlay(bg)
        except:
            final_mix = voice # Fallback if music file is corrupt
    else:
        final_mix = voice
        
    output_path = "processed_audio.mp3"
    final_mix.export(output_path, format="mp3")
    return output_path

def create_video(audio_path, transcript):
    audio = AudioFileClip(audio_path)
    duration = min(audio.duration, 60)
    
    # Background: Dark Theme
    bg = ColorClip(size=(1080, 1920), color=(20, 20, 20)).set_duration(duration)
    
    # Caption Overlay (Gold text for the Sovereign Brand)
    txt = TextClip(
        text=transcript[:150] + "...", 
        font_size=70, 
        color='gold', 
        method='caption',
        size=(900, None)
    ).set_duration(duration).set_position('center')
    
    video = CompositeVideoClip([bg, txt]).set_audio(audio.subclip(0, duration))
    video_path = "promo_snippet.mp4"
    video.write_videofile(video_path, fps=24, codec="libx264")
    return video_path

# --- APP TABS ---
tab1, tab2, tab3 = st.tabs(["1. Record & Upload", "2. Mix & Transcribe", "3. Export Video"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🎤 Voice")
        audio_record = mic_recorder(start_prompt="🔴 Start Recording", stop_prompt="⏹️ Stop", key='recorder')
        if audio_record:
            with open("raw_audio.wav", "wb") as f:
                f.write(audio_record['bytes'])
            st.success("Voice captured!")
            st.audio(audio_record['bytes'])

    with col2:
        st.subheader("🎵 Background Music")
        music_url = st.text_input("Paste Music URL (Direct Link):", placeholder="https://example.com/beat.mp3")
        uploaded_bg = st.file_uploader("Or Upload MP3", type=["mp3"])
        
        if uploaded_bg:
            with open("background.mp3", "wb") as f:
                f.write(uploaded_bg.getbuffer())
            st.success("Music uploaded!")
        elif music_url:
            if st.button("Download Music"):
                with st.spinner("Fetching audio..."):
                    r = requests.get(music_url)
                    with open("background.mp3", "wb") as f:
                        f.write(r.content)
                st.success("Music downloaded!")

with tab2:
    if os.path.exists("raw_audio.wav"):
        st.subheader("🎚️ Studio Mixer")
        vol = st.slider("Music Volume (Lower = Quieter)", -40, -10, -25)
        noise = st.selectbox("Noise Cleanup", [0, 80, 150], format_func=lambda x: "None" if x==0 else "Standard")
        
        if st.button("✨ Process & Transcribe"):
            with st.spinner("AI is listening (using 'small' model for accuracy)..."):
                # Mix Audio
                final_audio = process_audio("raw_audio.wav", "background.mp3", vol, noise)
                
                # Transcribe Voice Only (Better accuracy)
                model = whisper.load_model("small")
                result = model.transcribe("raw_audio.wav", fp16=False)
                st.session_state['transcript'] = result['text']
                st.audio(final_audio)
        
        if 'transcript' in st.session_state:
            st.subheader("📝 Edit Transcript")
            st.session_state['transcript'] = st.text_area("Correct any errors here:", value=st.session_state['transcript'], height=200)
    else:
        st.info("Record your voice in Tab 1 first.")

with tab3:
    if 'transcript' in st.session_state:
        st.subheader("🎬 Video Snippet")
        if st.button("Generate MP4"):
            with st.spinner("Rendering Video..."):
                video_file = create_video("processed_audio.mp3", st.session_state['transcript'])
                st.video(video_file)
                with open(video_file, "rb") as f:
                    st.download_button("Download Snippet", f, "sovereign_promo.mp4")
    else:
        st.info("Complete the transcription in Tab 2 first.")
