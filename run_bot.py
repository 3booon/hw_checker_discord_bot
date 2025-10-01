#!/usr/bin/env python3
"""
Discord 리포트 체크 봇 실행 스크립트
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from discord_bot import bot, DISCORD_BOT_TOKEN
    
    if not DISCORD_BOT_TOKEN:
        print("❌ 오류: DISCORD_BOT_TOKEN이 설정되지 않았습니다.")
        print("📝 .env 파일을 생성하고 봇 토큰을 설정해주세요.")
        print("📋 env_template.txt 파일을 참고하세요.")
        sys.exit(1)
    
    print("🚀 Discord 리포트 체크 봇을 시작합니다...")
    print("📝 매일 10:00에 자동으로 리포트 상태를 확인합니다.")
    print("⚡ 수동 확인: !check_reports")
    print("🕐 시간 테스트: !test_time")
    print("⏹️  종료하려면 Ctrl+C를 누르세요.")
    
    bot.run(DISCORD_BOT_TOKEN)
    
except KeyboardInterrupt:
    print("\n👋 봇을 종료합니다.")
except Exception as e:
    print(f"❌ 오류가 발생했습니다: {e}")
    sys.exit(1)
