import streamlit as st
import whisper
import os
from streamlit_mic_recorder import mic_recorder
from pydub import AudioSegment, effects

# --- PAGE CONFIG ---
st.set_page_config(page_title="Sovereign Studio", page_icon="🎙️", layout="wide")
st.title("🎙️ Sovereign Studio")

# --- AUDIO ENGINE ---
def process_audio(file_path, bg_music_path, music_volume, noise_reduction):
    # 1. Load Voice
    voice = AudioSegment.from_file(file_path)
    voice = effects.normalize(voice)
    
    # 2. Apply Noise Reduction (High Pass Filter)
    if noise_reduction > 0:
        voice = voice.high_pass_filter(noise_reduction)
    
    # 3. Handle Background Music
    if bg_music_path and os.path.exists(bg_music_path):
        bg = AudioSegment.from_file(bg_music_path)
        # Loop music to match voice length and apply volume slider
        bg = bg.loop(duration=len(voice)) + music_volume 
        final_mix = voice.overlay(bg)
    else:
        final_mix = voice
        
    output_path = "final_podcast.mp3"
    final_mix.export(output_path, format="mp3")
    return output_path

# --- STEP 1: CAPTURE ---
tab1, tab2 = st.tabs(["1. Record/Upload", "2. Edit & Transcribe"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Live Recording")
        audio_record = mic_recorder(start_prompt="🔴 Start", stop_prompt="⏹️ Stop", key='recorder')
        if audio_record:
            with open("raw_audio.wav", "wb") as f:
                f.write(audio_record['bytes'])
            st.success("Voice Captured!")
    
    with col2:
        st.subheader("Online / Upload")
        uploaded_bg = st.file_uploader("Upload Background Music (.mp3)", type=["mp3"])
        if uploaded_bg:
            with open("background.mp3", "wb") as f:
                f.write(uploaded_bg.getbuffer())
            st.success("Music Ready!")

# --- STEP 2: EDIT & TRANSCRIBE ---
with tab2:
    if os.path.exists("raw_audio.wav"):
        st.subheader("🎚️ The Mixer")
        
        # SLIDERS FOR BALANCE
        vol = st.slider("Music Volume (Lower is quieter)", -40, 0, -25)
        noise = st.selectbox("Noise Cleanup Strength", [0, 80, 150], format_func=lambda x: "None" if x==0 else ("Standard" if x==80 else "Strong"))
        
        if st.button("✨ Process & Transcribe"):
            with st.spinner("Mixing your masterpiece..."):
                # Run the mixing engine
                final_path = process_audio("raw_audio.wav", "background.mp3", vol, noise)
                
                # Run AI Transcription
                model = whisper.load_model("base")
                result = model.transcribe("raw_audio.wav")
                st.session_state['transcript'] = result['text']
                
                st.audio(final_path)
        
        if 'transcript' in st.session_state:
            st.subheader("📝 Editable Transcription")
            edited_text = st.text_area("Edit your words here:", value=st.session_state['transcript'], height=200)
            st.download_button("Download Transcript", edited_text, file_name="transcript.txt")
    else:
        st.info("Please record audio in Tab 1 first.")
