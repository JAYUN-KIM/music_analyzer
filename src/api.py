from fastapi import FastAPI, UploadFile, File, HTTPException
import shutil
import os
import uvicorn
import sys
import traceback

# -----------------------------
# 1. 모듈 경로 설정 및 import
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
sys.path.append(BASE_DIR)

analyze = None
try:
    import analyze 
    print("[API] analyze.py 모듈 로드 성공")
except Exception as e:
    print(f"[ERROR] analyze.py 로드 실패!")
    print(f"상세 원인: {e}") # 여기서 librosa가 없는지, 파일이 없는지 알려줍니다.
    # traceback.print_exc() # 더 자세한 에러 추적을 원하면 주석 해제

app = FastAPI(title="MRDW Music Analyzer API")

# -----------------------------
# 2. 경로 설정
# -----------------------------
ROOT_DIR = os.path.dirname(BASE_DIR)
AUDIO_DIR = os.path.join(ROOT_DIR, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

@app.post("/upload")
async def upload_music(file: UploadFile = File(...)):
    input_path = os.path.join(AUDIO_DIR, "input.mp3")

    try:
        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        print(f"\n[API] 파일 수신 성공: {input_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 저장 실패: {str(e)}")

    # [중요] analyze.py 안에 'analyze'라는 이름의 함수가 있어야 실행됩니다.
    if analyze and hasattr(analyze, 'analyze'):
        try:
            print("[API] 분석 엔진 가동...")
            analyze.analyze() # analyze.py의 analyze() 함수 호출
            print("[API] 프로세스 완료")
        except Exception as e:
            print(f"[API] 분석 에러: {str(e)}")
            return {"status": "warning", "message": str(e)}
    else:
        # 이 로그가 뜬다면 analyze.py에 def analyze(): 가 있는지 확인해야 합니다.
        msg = "analyze 모듈이 없거나 analyze() 함수를 찾을 수 없습니다."
        print(f"[API] 경고: {msg}")
        return {"status": "error", "message": msg}

    return {"status": "success", "message": "성공", "file_name": file.filename}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
