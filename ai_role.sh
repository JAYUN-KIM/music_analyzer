#!/bin/bash

# 1. 경로 정의 (현재 tree 구조 반영)
PROJECT_ROOT="/home/ansible-admin/music-analyzer"
SRC_DIR="$PROJECT_ROOT/src"
VENV_PATH="$PROJECT_ROOT/venv"

echo ">>> [1/3] 시스템 환경 점검 및 라이브러리 설치..."
# libsndfile 패키지명 CentOS 9용으로 교정
sudo dnf install -y ffmpeg libsndfile python3-pip python3-devel

# 가상환경이 없으면 생성
if [ ! -d "$VENV_PATH" ]; then
    python3 -m venv $VENV_PATH
fi

echo ">>> [2/3] 의존성 라이브러리 설치 (용량 다이어트 모드)..."
$VENV_PATH/bin/pip install --no-cache-dir \
    librosa numpy fastapi uvicorn python-multipart transformers \
    torch --extra-index-url https://download.pytorch.org/whl/cpu

echo ">>> [3/3] API 서버 실행 (src/ 폴더 기준)..."
# 기존 프로세스 종료
pkill -f "uvicorn api:app" || true

# 환경변수: __pycache__ 생성 방지 및 CPU 강제
export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=-1

# 핵심: PYTHONPATH를 src로 지정하여 analyze.py 로드 문제 해결
export PYTHONPATH=$SRC_DIR

# 실행 경로를 src로 이동하여 실행하거나, 모듈 경로 지정
cd $SRC_DIR
nohup $VENV_PATH/bin/python3 api.py > ../server.log 2>&1 &

echo "--------------------------------------------------"
echo ">>> 배포 성공! 서버가 백그라운드에서 실행 중입니다."
echo ">>> 로그 확인: tail -f ../server.log"
echo "--------------------------------------------------"
