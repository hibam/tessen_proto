#!/usr/bin/env python3
"""
로그 파일의 타임스탬프를 현재 시간으로 업데이트
"""

import time
import re
from datetime import datetime

def get_current_timestamp():
    """현재 시간을 YYYY-MM-DD HH:MM 형식으로 반환"""
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M")

def update_timestamps_in_file(file_path):
    """파일의 타임스탬프를 현재 시간으로 업데이트"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 2025-01-07 또는 2024-12-19 패턴을 현재 날짜로 변경
        current_date = datetime.now().strftime("%Y-%m-%d")

        # 날짜 패턴 찾아서 교체
        content = re.sub(r'2025-01-07|2024-12-19', current_date, content)

        # 마지막 업데이트 시간도 현재 시간으로 변경
        content = re.sub(
            r'\*\*마지막 업데이트\*\*: \d{4}-\d{2}-\d{2}',
            f'**마지막 업데이트**: {current_date}',
            content
        )

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ {file_path} 타임스탬프 업데이트 완료")

    except Exception as e:
        print(f"❌ {file_path} 업데이트 실패: {e}")

def main():
    """메인 함수"""
    print("🕐 로그 파일 타임스탬프 업데이트 시작...")
    print(f"현재 시간: {get_current_timestamp()}")
    print("=" * 50)

    # 업데이트할 파일들
    files_to_update = [
        'shared/status.md',
        'shared/debug_log.md',
        'shared/communication.md'
    ]

    for file_path in files_to_update:
        update_timestamps_in_file(file_path)

    print("=" * 50)
    print("🎉 모든 로그 파일 타임스탬프 업데이트 완료!")

if __name__ == "__main__":
    main()
