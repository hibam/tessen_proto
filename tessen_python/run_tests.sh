#!/bin/bash
echo "🎾 TESSEN 센서 테스트 자동화 스크립트"
echo "========================================"

echo ""
echo "1. 가상환경 활성화 중..."
source tessen_env/Scripts/activate

echo ""
echo "2. 패키지 설치 확인..."
pip list | grep bleak

echo ""
echo "3. TESSEN 센서 스캔 중..."
python bt_scan_all.py

echo ""
echo "4. 디버깅 프로그램 실행..."
python tessen_debug.py

echo ""
echo "5. 메인 테스트 프로그램 실행..."
python tessen_bt_test.py

echo ""
echo "🎉 모든 테스트 완료!"
