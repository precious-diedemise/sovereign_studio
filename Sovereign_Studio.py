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

# --- CORE FUNCTIONS ---
def process_audio(file_path, bg_music_path, music_volume, noise_reduction):
    voice = AudioSegment.from_file(file_path)
    voice = effects.normalize(voice)
    
    # Noise Reduction Filter
    if noise_reduction > 0:
        voice = voice.high_pass_filter(noise_reduction)
    
    # Mix Background Music
    if bg_music_path and os.path.exists(bg_music_path):
        try:
            bg = AudioSegment.from_file(bg_music_path)
            bg = bg.loop(duration=len(voice)) + music_volume 
            final_mix = voice.overlay(bg)
        except Exception:
            final_mix = voice # Fallback if audio file is corrupted
    else:
        final_mix = voice
        
    output_path = "processed_audio.mp3"
    final_mix.export(output_path, format="mp3", bitrate="192k")
    return output_path

def create_video(audio_path, transcript):
    audio = AudioFileClip(audio_path)
    duration = min(audio.duration, 60)
    
    # Background: Sovereign Brand (Dark Grey/Black)
    bg = ColorClip(size=(1080, 1920), color=(20, 20, 20)).set_duration(duration)
    
    # Caption Overlay: Sovereign Gold Text
    txt = TextClip(
        text=transcript[:150] + "...", 
        font_size=70, 
        color='gold', 
        method='caption',
        size=(900, None)
    ).set_duration(duration).set_position('center')
    
    video = CompositeVideoClip([bg, txt]).set_audio(audio.subclip(0, duration))
    video_path = "promo_snippet.mp4"
    video.write_videofile(video_path, fps=24, codec="libx264", audio_codec="aac")
    return video_path

# --- APP TABS ---
tab1, tab2, tab3 = st.tabs(["1. Input Audio", "2. Mix & Transcribe", "3. Export Video"])

with tab1:
    st.subheader("🎤 Step 1: Capture or Upload Voice")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Option A: Live Record**")
        audio_record = mic_recorder(
            start_prompt="🔴 Start Recording",
            stop_prompt="⏹️ Stop Recording",
            key='recorder'
        )
        if audio_record:
            with open("raw_audio.wav", "wb") as f:
                f.write(audio_record['bytes'])
            st.success("Voice recording captured!")

    with col2:
        st.write("**Option B: Upload File**")
        uploaded_voice = st.file_uploader("Upload voice memo (.mp3/wav)", type=["mp3", "wav"])
        if uploaded_voice:
            with open("raw_audio.wav", "wb") as f:
                f.write(uploaded_voice.getbuffer())
            st.success("Voice file uploaded!")

    st.divider()
    st.subheader("🎵 Step 2: Background Music")
    uploaded_bg = st.file_uploader("Upload music file (e.g., 2face - Nobody)", type=["mp3"])
    if uploaded_bg:
        with open("background.mp3", "wb") as f:
            f.write(uploaded_bg.getbuffer())
        st.success("Background music ready!")

with tab2:
    if os.path.exists("raw_audio.wav"):
        st.subheader("🎚️ The Studio Mixer")
        vol = st.slider("Music Volume (Voice remains at 100%)", -40, -10, -25)
        noise = st.selectbox("Noise Cleanup Intensity", [0, 80, 150], 
                             format_func=lambda x: "None" if x==0 else ("Standard" if x==80 else "Strong"))
        
        if st.button("✨ Mix Audio & Transcribe"):
            with st.spinner("AI is processing (Small model for high accuracy)..."):
                # 1. Process Audio
                final_audio = process_audio("raw_audio.wav", "background.mp3", vol, noise)
                
                # 2. AI Transcription (Smarter Model)
                model = whisper.load_model("small")
                result = model.transcribe("raw_audio.wav", fp16=False, language='en')
                st.session_state['transcript'] = result['text']
                
                # 3. Playback
                st.audio(final_audio)
                st.success("Mixing Complete!")
        
        if 'transcript' in st.session_state:
            st.subheader("📝 Edit Transcript")
            st.session_state['transcript'] = st.text_area("Correct your words here:", value=st.session_state['transcript'], height=200)
    else:
        st.info("Please provide voice input in Tab 1 first.")

with tab3:
    if 'transcript' in st.session_state:
        st.subheader("🎬 Final Video Export")
        if st.button("Generate MP4 Snippet"):
            with st.spinner("Rendering Video..."):
                video_file = create_video("processed_audio.mp3", st.session_state['transcript'])
                st.video(video_file)
                with open(video_file, "rb") as f:
                    st.download_button("Download Snippet", f, "sovereign_promo.mp4")
    else:
        st.info("Process your audio in Tab 2 to enable video generation.")
