import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timedelta, time
import pytz
import logging
from config import *

# Discord.py 로그 레벨 설정
logging.basicConfig(level=logging.INFO)

# 봇 설정
intents = discord.Intents.default()
intents.message_content = True  # 메시지 내용 읽기 위해 필요
intents.guilds = True
intents.members = True  # 서버 멤버 정보 읽기 위해 필요

bot = commands.Bot(command_prefix='!', intents=intents)

# 봇이 준비되었는지 확인하는 변수
bot_ready = False

class ReportChecker:
    def __init__(self):
        self.target_channel = None
        self.report_keyword = REPORT_KEYWORD
        self.target_user_count = TARGET_USER_COUNT
        
    async def setup_target_channel(self):
        """대상 채널을 설정합니다."""
        if TARGET_CHANNEL_ID:
            self.target_channel = bot.get_channel(TARGET_CHANNEL_ID)
            if not self.target_channel:
                print(f"채널 ID {TARGET_CHANNEL_ID}를 찾을 수 없습니다.")
        else:
            print("TARGET_CHANNEL_ID가 설정되지 않았습니다.")

    def is_within_check_period(self, message_time):
        kst = pytz.timezone('Asia/Seoul')

        if message_time.tzinfo is None:
            message_time = pytz.utc.localize(message_time)
        message_time_kst = message_time.astimezone(kst)

        # 오늘 날짜
        today = datetime.now(kst).date()

        # 시작 시간은 전날 4시
        start_time = kst.localize(datetime.combine(today - timedelta(days=1), time(
            CHECK_START_HOUR, CHECK_START_MINUTE, CHECK_START_SECOND)))

        # 종료 시간은 오늘 3:59:59
        end_time = kst.localize(datetime.combine(today, time(
            CHECK_END_HOUR, CHECK_END_MINUTE, CHECK_END_SECOND)))

        return start_time <= message_time_kst <= end_time

    async def check_reports_in_threads(self):
        if not self.target_channel:
            await self.setup_target_channel()
            if not self.target_channel:
                logging.error("❌ 대상 채널을 찾을 수 없습니다.")
                return None, None

        guild = self.target_channel.guild

        # 제외할 사용자 ID 목록 불러오기 (config.py에서)
        exclude_ids = EXCLUDE_USER_IDS if 'EXCLUDE_USER_IDS' in globals() else []

        # 전체 서버 멤버 중 봇이 아니고 제외 대상도 아닌 사람만 포함
        all_members = [
            member for member in guild.members
            if not member.bot and member.id not in exclude_ids
        ]
        logging.info(f"👥 제출 대상 인원 (봇 제외 & 제외 리스트 제외): {len(all_members)}명")

        submitted_users = set()

        # 채널의 모든 쓰레드 가져오기 (비아카이브된 것만)
        threads = [thread for thread in self.target_channel.threads if not thread.archived]
        logging.info(f"📋 확인할 쓰레드 수: {len(threads)}개")

        for thread in threads:
            logging.info(f"📝 쓰레드 '{thread.name}' 확인 중...")

            try:
                async for message in thread.history(limit=None):
                    # 메시지 시간 UTC -> KST 변환
                    if message.created_at.tzinfo is None:
                        message_time_utc = pytz.utc.localize(message.created_at)
                    else:
                        message_time_utc = message.created_at
                    message_time_kst = message_time_utc.astimezone(pytz.timezone('Asia/Seoul'))

                    is_within = self.is_within_check_period(message.created_at)

                    if is_within:
                        if self.report_keyword in message.content:
                            submitted_users.add(message.author)
                            logging.info(
                                f"[{thread.name}] ✅ {message.author.display_name}의 리포트 발견! 시간(KST): {message_time_kst.strftime('%Y-%m-%d %H:%M:%S')}")

            except Exception as e:
                logging.error(f"❌ 쓰레드 '{thread.name}'({thread.id})에서 메시지 읽는 중 오류: {e}")

        # 제출 안 한 멤버 계산
        not_submitted_users = set(all_members) - submitted_users

        logging.info(f"📊 결과: 제출 {len(submitted_users)}명, 미제출 {len(not_submitted_users)}명")

        return submitted_users, not_submitted_users

    async def send_daily_report(self):
        """매일 리포트 상태를 전송합니다."""
        logging.info("📊 리포트 상태 확인을 시작합니다...")
        submitted_users, not_submitted_users = await self.check_reports_in_threads()
        
        if submitted_users is None:
            logging.error("❌ 리포트 확인 중 오류가 발생했습니다.")
            await self.target_channel.send("❌ 리포트 확인 중 오류가 발생했습니다.")
            return
        
        # 한국 시간으로 현재 시간 표시
        kst = pytz.timezone('Asia/Seoul')
        now = datetime.now(kst)
        
        embed = discord.Embed(
            title="📊 일일 리포트 제출 현황",
            description=f"**확인 시간:** {now.strftime('%Y-%m-%d %H:%M:%S')} (KST)\n**확인 기간:** 어제 04:00:00 ~ 03:59:59",
            color=0x00ff00 if len(submitted_users) == self.target_user_count else 0xff0000
        )
        
        # 제출한 사용자 목록
        if submitted_users:
            submitted_list = "\n".join([f"✅ {user.display_name}" for user in submitted_users])
            embed.add_field(
                name=f"📝 제출 완료 ({len(submitted_users)}명)",
                value=submitted_list,
                inline=False
            )
        else:
            embed.add_field(
                name="📝 제출 완료 (0명)",
                value="제출한 사용자가 없습니다.",
                inline=False
            )
        
        # 제출하지 않은 사용자 목록
        if not_submitted_users:
            not_submitted_list = "\n".join([f"❌ {user.display_name}" for user in not_submitted_users])
            embed.add_field(
                name=f"⏰ 미제출 ({len(not_submitted_users)}명)",
                value=not_submitted_list,
                inline=False
            )
        
        # 전체 요약
        total_members = len(submitted_users) + len(not_submitted_users)
        embed.add_field(
            name="📈 요약",
            value=f"전체: {total_members}명 | 제출: {len(submitted_users)}명 | 미제출: {len(not_submitted_users)}명",
            inline=False
        )
        
        logging.info(f"📤 리포트 전송 중... (제출: {len(submitted_users)}명, 미제출: {len(not_submitted_users)}명)")
        await self.target_channel.send(embed=embed)
        logging.info("✅ 리포트 전송 완료!")

# 리포트 체커 인스턴스 생성
report_checker = ReportChecker()

@bot.event
async def on_ready():
    global bot_ready
    bot_ready = True
    logging.info("=" * 50)
    logging.info("🚀 ON_READY 이벤트 실행됨!")
    logging.info(f'✅ {bot.user}가 로그인했습니다!')
    logging.info(f'📊 서버 수: {len(bot.guilds)}')
    logging.info(f'👥 사용자 수: {len(bot.users)-1}')
    logging.info("=" * 50)
    
    await report_checker.setup_target_channel()

    # 슬래시 명령어 동기화
    try:
        synced = await bot.tree.sync()
        logging.info(f"✅ {len(synced)}개의 슬래시 명령어가 동기화되었습니다.")
    except Exception as e:
        logging.error(f"❌ 슬래시 명령어 동기화 실패: {e}")
    
    # 매일 17:00에 리포트 확인 (한국 시간)
    logging.info('⏰ 자동 리포트 체크 스케줄을 시작합니다...')
    check_time_and_report.start()
    
    logging.info('✅ 봇이 완전히 준비되었습니다!')

@tasks.loop(minutes=1)
async def check_time_and_report():
    """매분마다 시간을 확인하고 10:00이 되면 리포트를 전송합니다."""
    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst)
    
    # 17:00이면 리포트 전송
    if now.hour == 10 and now.minute == 0:
        logging.info("🕐 10:00이 되었습니다! 리포트를 전송합니다...")
        await report_checker.send_daily_report()
    else:
        logging.info(f"🕐 현재 시간: {now.strftime('%H:%M:%S')} (리포트 전송 대기 중...)")

@bot.command(name='check_reports')
# @bot.tree.command(name="check_reports", description="수동으로 리포트 상태를 확인합니다")
async def manual_check_reports(ctx):
    """수동으로 리포트 상태를 확인합니다."""
    await report_checker.send_daily_report()

@bot.command(name='start_schedule')
async def start_schedule(ctx):
    """스케줄을 시작합니다."""
    if daily_report_check.is_running():
        await ctx.send("⚠️ 스케줄이 이미 실행 중입니다.")
    else:
        daily_report_check.start()
        await ctx.send("✅ 스케줄을 시작했습니다!")

@bot.command(name='stop_schedule')
async def stop_schedule(ctx):
    """스케줄을 중지합니다."""
    if daily_report_check.is_running():
        daily_report_check.stop()
        await ctx.send("⏹️ 스케줄을 중지했습니다!")
    else:
        await ctx.send("⚠️ 스케줄이 실행 중이 아닙니다.")

@bot.command(name='test_time')
async def test_time(ctx):
    """현재 시간과 체크 기간을 테스트합니다."""
    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst)
    
    embed = discord.Embed(
        title="🕐 시간 테스트",
        description=f"현재 시간 (KST): {now.strftime('%Y-%m-%d %H:%M:%S')}",
        color=0x0099ff
    )
    
    # 체크 기간 계산
    today = now.date()
    
    start_time = kst.localize(datetime.combine(today, datetime.min.time().replace(
        hour=CHECK_START_HOUR, 
        minute=CHECK_START_MINUTE, 
        second=CHECK_START_SECOND
    )))
    end_time = kst.localize(datetime.combine(today, datetime.min.time().replace(
        hour=CHECK_END_HOUR, 
        minute=CHECK_END_MINUTE, 
        second=CHECK_END_SECOND
    )))
    
    embed.add_field(
        name="체크 기간",
        value=f"시작: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n끝: {end_time.strftime('%Y-%m-%d %H:%M:%S')}",
        inline=False
    )
    
    embed.add_field(
        name="현재 시간이 체크 기간 내인가?",
        value="✅ 예" if report_checker.is_within_check_period(now) else "❌ 아니오",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command(name='status')
async def bot_status(ctx):
    """봇 상태를 확인합니다."""
    embed = discord.Embed(
        title="🤖 봇 상태",
        color=0x00ff00 if bot_ready else 0xff0000
    )
    
    embed.add_field(
        name="봇 준비 상태",
        value="✅ 준비됨" if bot_ready else "❌ 준비되지 않음",
        inline=False
    )
    
    embed.add_field(
        name="봇 사용자",
        value=f"{bot.user}" if bot.user else "알 수 없음",
        inline=False
    )
    
    embed.add_field(
        name="서버 수",
        value=f"{len(bot.guilds)}",
        inline=False
    )
    
    embed.add_field(
        name="스케줄 상태",
        value="✅ 실행 중" if daily_report_check.is_running() else "❌ 중지됨",
        inline=False
    )
    
    # 현재 시간 표시
    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst)
    embed.add_field(
        name="현재 시간 (KST)",
        value=now.strftime('%Y-%m-%d %H:%M:%S'),
        inline=False
    )
    
    await ctx.send(embed=embed)

if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("DISCORD_BOT_TOKEN이 설정되지 않았습니다. .env 파일을 확인해주세요.")
    else:
        bot.run(DISCORD_BOT_TOKEN)
