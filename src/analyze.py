import librosa
import numpy as np
import json
import os
import argparse
import sys
import shutil
import subprocess
import warnings
import tarfile
from datetime import datetime

# 경고 메시지 무시 (Librosa 관련 불필요한 출력 방지)
warnings.filterwarnings('ignore')

# =============================
# [설정] 경로 및 환경 설정
# =============================
GIT_REPO_PATH = "/home/ansible-admin/project"
GIT_WEB_DIR = os.path.join(GIT_REPO_PATH, "web")

# --- NAS 경로 추가 ---
NAS_DIR = "/mnt/NAS/result/"
# ---------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
AUDIO_DIR = os.path.join(ROOT_DIR, "audio")
INPUT_AUDIO = os.path.join(AUDIO_DIR, "input.mp3")
TEMP_WAV = os.path.join(AUDIO_DIR, "temp.wav")
COUNT_FILE = os.path.join(ROOT_DIR, "commit_count.txt")

OUTPUT_JSON = os.path.join(GIT_WEB_DIR, "theme.json")
PROJECT_JS = os.path.join(GIT_WEB_DIR, "theme.generated.js")
PROJECT_CSS = os.path.join(GIT_WEB_DIR, "theme.generated.css")

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(GIT_WEB_DIR, exist_ok=True)

# AI 모델 로딩 (성능 최적화: 필요한 순간에만 로드하도록 설정 가능하나 여기선 유지)
USE_AI_MODEL = True
try:
    from transformers import pipeline
    emotion_model = pipeline(
        "audio-classification",
        model="superb/wav2vec2-base-superb-er",
        device=-1
    )
except Exception:
    print("[WARN] AI 모델 로드 실패 → Rule-based 모드로 전환합니다.")
    USE_AI_MODEL = False

# =============================
# [핵심] 고도화된 음악 분석 엔진
# =============================
def analyze_music_advanced(y, sr):
    """
    단순한 특징 추출을 넘어 웹 UI에 직관적인 시각적 파라미터를 제공함
    """
    # 1. 기본 특징 (Tempo, Energy)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(tempo[0]) if isinstance(tempo, np.ndarray) else float(tempo)
    rms = librosa.feature.rms(y=y)[0]
    energy = float(np.mean(rms))
    
    # 2. 청각적 밝기 및 질감 (Spectral 특징)
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    brightness = float(np.mean(centroid))
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
    complexity = float(np.mean(librosa.feature.spectral_flatness(y=y))) # 0~1 (1에 가까울수록 시끄러움)

    # 3. 조성(Key) 분석 - 색상 매칭의 핵심
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    mean_chroma = np.mean(chroma, axis=1)
    key_index = int(np.argmax(mean_chroma))
    # C=0, C#=1, ... B=11 (음악 이론의 5도권/보색 대비 활용 가능)
    
    # 4. 드라마틱한 수치 계산 (0.0 ~ 1.0 스케일링)
    intensity = min(1.0, energy * 5) # 에너지 증폭
    speed_factor = max(0.2, min(2.0, tempo / 120)) # 120BPM 기준 속도비
    
    return {
        "tempo": round(tempo, 1),
        "energy": round(energy, 4),
        "brightness": round(brightness, 2),
        "complexity": round(complexity, 4),
        "key_index": key_index,
        "intensity": round(intensity, 2),
        "speed_factor": round(speed_factor, 2)
    }

def get_vibe_palette(features):
    """
    분석된 특징을 바탕으로 웹사이트에 적용할 '분위기 테마' 결정
    """
    f = features
    # 감정/분위기 조합 로직
    if f['energy'] > 0.08 and f['complexity'] > 0.02:
        vibe = "Cyberpunk"
        colors = {"main": "#ff0055", "sub": "#00ffcc", "bg": "#0a0a12", "font": "'Orbitron', sans-serif"}
    elif f['brightness'] > 2500:
        vibe = "Ethereal"
        colors = {"main": "#fdfbfb", "sub": "#ebedee", "bg": "#ffffff", "font": "'Noto Sans KR', sans-serif"}
    elif f['energy'] < 0.03:
        vibe = "Minimalist"
        colors = {"main": "#2c3e50", "sub": "#bdc3c7", "bg": "#ecf0f1", "font": "'Nanum Myeongjo', serif"}
    else:
        vibe = "Midnight"
        colors = {"main": "#4facfe", "sub": "#00f2fe", "bg": "#090909", "font": "'Pretendard', sans-serif"}
    
    return vibe, colors

# =============================
# [출력] 시각적 자산 생성 (CSS/JS)
# =============================
def generate_advanced_assets(features, ai_emotion):
    vibe, palette = get_vibe_palette(features)
    
    # 1. CSS 변수 생성 (이 부분이 웹사이트의 극적인 변화를 만듦)
    # 애니메이션 속도를 BPM에 맞춤 (1박자 주기)
    beat_duration = round(60 / features['tempo'], 3)
    
    css_content = f"""
:root {{
    --mrdw-vibe: "{vibe}";
    --mrdw-main-color: {palette['main']};
    --mrdw-sub-color: {palette['sub']};
    --mrdw-bg-color: {palette['bg']};
    --mrdw-font-family: {palette['font']};
    --mrdw-beat-duration: {beat_duration}s;
    --mrdw-intensity: {features['intensity']};
    --mrdw-brightness: {features['brightness'] / 5000};
    --mrdw-glow: rgba({int(features['intensity']*255)}, 100, 255, 0.5);
}}

body {{
    background-color: var(--mrdw-bg-color);
    color: var(--mrdw-main-color);
    font-family: var(--mrdw-font-family);
    transition: all 1.2s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    justify-content: center;
    align-items: center;
    overflow: hidden;
}}

/* 박자에 맞춰 맥동하는 효과 */
.beat-box {{
    animation: mrdw-pulse var(--mrdw-beat-duration) infinite alternate;
    box-shadow: 0 0 calc(var(--mrdw-intensity) * 50px) var(--mrdw-glow);
}}

@keyframes mrdw-pulse {{
    from {{ transform: scale(1); filter: brightness(1); }}
    to {{ transform: scale(calc(1 + var(--mrdw-intensity) * 0.1)); filter: brightness(1.5); }}
}}
"""
    with open(PROJECT_CSS, "w", encoding="utf-8") as f:
        f.write(css_content.strip())

    # 2. JS 데이터 생성
    theme_data = {
        "analysis": features,
        "emotion": ai_emotion,
        "vibe": vibe,
        "generated_at": subprocess.check_output(["date"]).decode().strip()
    }
    
    js_content = f"window.MRDW_DATA = {json.dumps(theme_data, indent=4)};"
    with open(PROJECT_JS, "w", encoding="utf-8") as f:
        f.write(js_content)
    
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(theme_data, f, indent=4)
  
    # 수정된 압축 로직 (방법 1 적용)
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"음악분석 파일_{timestamp}.tar.gz"
        nas_archive_path = os.path.join(NAS_DIR, archive_name)

        with tarfile.open(nas_archive_path, "w:gz") as tar:
            for f in [PROJECT_CSS, PROJECT_JS, OUTPUT_JSON]:
                tar.add(f, arcname=os.path.basename(f))
        
        print(f">>> [성공] NAS에 압축 파일 생성 완료: {archive_name}")
    except Exception as e:
        print(f">>> [오류] NAS 압축 생성 실패: {e}")

# =============================
# [Git] 자동 배포 로직 (기존 유지 및 강화)
# =============================
def sync_to_git():
    print(f"\n>>> Git Push 프로세스 시작: {GIT_REPO_PATH}")
    try:
        status = subprocess.check_output(["git", "status", "--porcelain"], cwd=GIT_REPO_PATH).decode()
        if not status:
            print(" - 변경 내용 없음. Push를 종료합니다.")
            return

        if os.path.exists(COUNT_FILE):
            with open(COUNT_FILE, "r") as f:
                try: count = int(f.read().strip())
                except: count = 0
        else: count = 0
        
        new_count = count + 1
        commit_message = f"Update Theme: Music Vibe {new_count}"
        
        for cmd in [["git", "add", "."], ["git", "commit", "-m", commit_message], ["git", "push", "origin", "main"]]:
            subprocess.run(cmd, cwd=GIT_REPO_PATH, check=True, capture_output=True)
        
        with open(COUNT_FILE, "w") as f: f.write(str(new_count))
        print(f">>> Git Push 성공! ({commit_message})")
    except Exception as e:
        print(f"[ERROR] Git 자동화 실패: {e}")

# =============================
# 메인 실행 엔진
# =============================
def analyze():
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=100)
    args = parser.parse_args(args=[])

    if not os.path.exists(INPUT_AUDIO):
        print(f"[ERROR] 파일을 찾을 수 없습니다: {INPUT_AUDIO}")
        return

    print(">>> 1. 오디오 변환 및 로드 (Fast Mode)")
    try:
        # 가벼운 분석을 위해 22050Hz로 로드
        subprocess.run(["ffmpeg", "-y", "-ss", "0", "-t", str(args.duration), "-i", INPUT_AUDIO, "-ar", "22050", TEMP_WAV],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        y, sr = librosa.load(TEMP_WAV, sr=22050)
        
        print(">>> 2. 다차원 음악 데이터 분석 중...")
        features = analyze_music_advanced(y, sr)

        print(">>> 3. AI 감정 추론 중...")
        ai_res = {"primary": "Unknown", "confidence": 0}
        if USE_AI_MODEL:
            try:
                # AI 모델은 파일 경로를 직접 받음
                results = emotion_model(TEMP_WAV)
                top = results[0]
                ai_res = {"primary": top['label'], "confidence": round(top['score'], 3)}
            except: pass

        print(">>> 4. 시각적 자산(CSS/JS) 생성...")
        generate_advanced_assets(features, ai_res)
        
        print(">>> 5. 저장소 동기화...")
        sync_to_git()
        
        print("\n[성공] 모든 분석과 배포가 완료되었습니다.")

    finally:
        if os.path.exists(TEMP_WAV): os.remove(TEMP_WAV)

if __name__ == "__main__":
    analyze()
