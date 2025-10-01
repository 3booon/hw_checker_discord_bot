# Discord 리포트 체크 봇

매일 특정 시간대에 디스코드 채널의 쓰레드에서 리포트 제출 현황을 자동으로 확인하고 알려주는 봇입니다.

## 기능

- 📝 매일 04:30에 자동으로 리포트 제출 현황 확인
- 🕐 오늘 04:00:00부터 내일 03:59:59까지의 메시지 중 `[리포트]` 키워드 탐지
- 🧵 특정 채널의 모든 쓰레드에서 메시지 확인
- 📊 제출한 사용자와 미제출 사용자 목록을 임베드로 표시
- ⚡ 수동으로도 리포트 상태 확인 가능

## 설치 및 설정

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정
`env_template.txt` 파일을 참고하여 `.env` 파일을 생성하고 다음 정보를 입력하세요:

```
DISCORD_BOT_TOKEN=your_bot_token_here
TARGET_CHANNEL_ID=your_channel_id_here
REPORT_KEYWORD=[리포트]
```

### 3. Discord 봇 토큰 생성
1. [Discord Developer Portal](https://discord.com/developers/applications)에 접속
2. 새 애플리케이션 생성
3. Bot 탭에서 토큰 생성
4. Privileged Gateway Intents에서 다음 권한 활성화:
   - Server Members Intent
   - Message Content Intent

### 4. 봇 권한 설정
봇이 다음 권한을 가져야 합니다:
- 채널 읽기
- 메시지 읽기
- 쓰레드 읽기
- 메시지 보내기
- 임베드 링크

### 5. 채널 ID 확인
1. Discord에서 개발자 모드 활성화 (설정 > 고급 > 개발자 모드)
2. 대상 채널을 우클릭하여 "ID 복사"

## 사용법

### 봇 실행
```bash
python discord_bot.py
```

### 명령어

- `!check_reports`: 수동으로 리포트 상태 확인
- `!test_time`: 현재 시간과 체크 기간 테스트

## 설정 변경

`config.py` 파일에서 다음 설정을 변경할 수 있습니다:

- `CHECK_START_HOUR`, `CHECK_START_MINUTE`, `CHECK_START_SECOND`: 체크 시작 시간 (기본: 04:00:00)
- `CHECK_END_HOUR`, `CHECK_END_MINUTE`, `CHECK_END_SECOND`: 체크 종료 시간 (기본: 03:59:59, 다음날)
- `TARGET_USER_COUNT`: 대상 사용자 수 (기본: 6명)
- `REPORT_KEYWORD`: 리포트 키워드 (기본: `[리포트]`)

## 시간대 설정

봇은 한국 시간(KST)을 기준으로 동작합니다. 다른 시간대를 사용하려면 `discord_bot.py`의 `pytz.timezone('Asia/Seoul')` 부분을 수정하세요.

## 문제 해결

### 봇이 메시지를 읽지 못하는 경우
1. 봇이 채널에 접근 권한이 있는지 확인
2. 채널 ID가 올바른지 확인
3. 봇이 온라인 상태인지 확인

### 시간대 문제
- 한국 시간대가 아닌 경우 `pytz` 라이브러리를 사용하여 올바른 시간대로 설정

### 쓰레드 접근 문제
- 봇이 쓰레드에 접근할 수 있는 권한이 있는지 확인
- 쓰레드가 아카이브되지 않았는지 확인
