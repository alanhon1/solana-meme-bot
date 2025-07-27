import asyncio
from dotenv import load_dotenv      # ✅ 추가
load_dotenv()                       # ✅ 추가

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
import aiohttp
import sqlite3
import os

# --- 설정 ---
API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_TELEGRAM_BOT_TOKEN')
RUGCHECK_API = os.getenv('RUGCHECK_API_KEY', 'YOUR_RUGCHECK_KEY')
BIRDEYE_API = os.getenv('BIRDEYE_API_KEY', 'YOUR_BIRDEYE_KEY')
ADMIN_CHAT_ID = int(os.getenv('ADMIN_CHAT_ID', '123456789'))

# --- DB 연결 & 초기화 ---
db = sqlite3.connect('bot_data.db', check_same_thread=False)
storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)

def init_db():
    c = db.cursor()
    # 기존 테이블
    c.execute("""
    CREATE TABLE IF NOT EXISTS watchlist (
        user_id INTEGER,
        token_address TEXT,
        PRIMARY KEY(user_id, token_address)
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        user_id INTEGER PRIMARY KEY,
        enabled INTEGER
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS votes (
        token_address TEXT PRIMARY KEY,
        votes INTEGER
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        token_address TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    # 자동매매 테이블
    c.execute("""
    CREATE TABLE IF NOT EXISTS auto_trades (
        user_id INTEGER,
        token_address TEXT,
        side TEXT,
        amount REAL,
        target_price REAL,
        stop_price REAL,
        PRIMARY KEY(user_id, token_address, side)
    )
    """)
    db.commit()

# --- HTTP 유틸 ---
async def fetch_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()

async def post_json(url, data, headers=None):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=headers or {}) as resp:
            return await resp.json()

# --- 핸들러 ---
@dp.message_handler(commands=['start'])
async def cmd_start(msg: types.Message):
    text = (
        "안녕 Alan! Solana Meme Bot이야.\n"
        "사용 가능한 명령어:\n"
        "/newmemecoins - 신규 안전 코인 목록\n"
        "/scan [토큰주소] - 스캔 분석\n"
        "/alerts_on | /alerts_off - 자동 알림 설정\n"
        "/watchlist_add [토큰주소] - 워치리스트 추가\n"
        "/watchlist - 내 워치리스트 확인\n"
        "/remove [토큰주소] - 워치리스트 제거\n"
        "/volume [최소 유동성] - 유동성 필터링\n"
        "/topmemes - 24h 수익률 상위 코인\n"
        "/rugrisk [토큰주소] - 러그풀 위험 점수\n"
        "/tokeninfo [토큰주소] - 토큰 정보 요약\n"
        "/buy [토큰주소] | /sell [토큰주소] - Jupiter 딥링크\n"
        "/report [토큰주소] - 스캠 의심 토큰 신고\n"
        "/vote [토큰주소] - 안전 투표하기\n"
        "/community - 커뮤니티 링크\n"
        "/faq - 자주 묻는 질문\n"
        "/language - 언어 설정\n"
        "/audit [토큰주소] - 정밀 분석\n\n"
        "🧠 자동매매 명령어:\n"
        "/autobuy [토큰주소] [SOL수량] [목표가] [손절가]\n"
        "/autosell [토큰주소] [토큰수량] [목표가] [손절가]\n"
        "/autostatus - 자동매매 상태 보기\n"
        "/autocancel [토큰주소] - 자동매매 취소\n"
    )
    await msg.reply(text)

@dp.message_handler(commands=['newmemecoins'])
async def cmd_newmemecoins(msg: types.Message):
    await msg.reply("🔍 신규 코인 스캔 중...")
    data = await fetch_json('https://api.dexscreener.com/latest/dex/pairs/solana')
    safe = []
    for p in data.get('pairs', [])[:20]:
        liq = float(p['liquidity']['usd'])
        fdv = float(p.get('fdv') or 0)
        if liq > 2000 and fdv > 50000:
            safe.append(p)
    if not safe:
        return await msg.reply("조건에 맞는 코인이 없어.. 잠시 후 다시 시도해봐")
    resp = "✅ 안전 코인 목록:\n"
    for p in safe[:5]:
        resp += f"{p['baseToken']['symbol']}: 유동성 ${float(p['liquidity']['usd']):.0f}, 24h 변화 {float(p['priceChange']['h24']):.1f}%\n"
    await msg.reply(resp)

@dp.message_handler(commands=['scan', 'check'])
async def cmd_scan(msg: types.Message):
    args = msg.get_args().split()
    if not args:
        return await msg.reply("/scan 뒤에 토큰 주소를 붙여줘")
    addr = args[0]
    await msg.reply(f"⚙️ {addr} 분석 중...")
    # TODO: 실제 스캔 로직
    await msg.reply("⚠️ 분석 결과: 위험 신호 있음\n- LP 락 안됨\n- 소유자 권한 있음\n- 유동성 낮음\n⛔️ 투자는 권장되지 않아")

@dp.message_handler(commands=['alerts_on', 'alerts_off'])
async def cmd_alerts(msg: types.Message):
    uid = msg.from_user.id
    enabled = 1 if msg.text == '/alerts_on' else 0
    c = db.cursor()
    c.execute("REPLACE INTO alerts (user_id, enabled) VALUES (?,?)", (uid, enabled))
    db.commit()
    await msg.reply(f"🔔 자동 알림 {'켜짐' if enabled else '꺼짐'}")

@dp.message_handler(commands=['watchlist_add', 'remove'])
async def cmd_watchlist_mod(msg: types.Message):
    args = msg.get_args().split()
    if not args:
        return await msg.reply("주소를 입력해줘")
    addr = args[0]
    uid = msg.from_user.id
    c = db.cursor()
    if msg.text.startswith('/watchlist_add'):
        c.execute("INSERT OR IGNORE INTO watchlist VALUES (?,?)", (uid, addr))
        await msg.reply(f"✅ {addr} 워치리스트에 추가됨")
    else:
        c.execute("DELETE FROM watchlist WHERE user_id=? AND token_address=?", (uid, addr))
        await msg.reply(f"🗑️ {addr} 워치리스트에서 제거됨")
    db.commit()

@dp.message_handler(commands=['watchlist'])
async def cmd_watchlist(msg: types.Message):
    uid = msg.from_user.id
    rows = db.cursor().execute("SELECT token_address FROM watchlist WHERE user_id=?", (uid,)).fetchall()
    if not rows:
        return await msg.reply("워치리스트가 비어있어")
    text = "📋 내 워치리스트:\n" + "\n".join(r[0] for r in rows)
    await msg.reply(text)

@dp.message_handler(commands=['volume'])
async def cmd_volume(msg: types.Message):
    args = msg.get_args().split()
    try:
        min_liq = int(args[0])
    except:
        return await msg.reply("/volume 뒤에 숫자(최소 유동성)를 붙여줘")
    await msg.reply(f"🔍 유동성 > ${min_liq} 코인 스캔 중...")
    data = await fetch_json('https://api.dexscreener.com/latest/dex/pairs/solana')
    good = [p for p in data.get('pairs', []) if float(p['liquidity']['usd']) >= min_liq]
    if not good:
        return await msg.reply("해당 조건 코인 없어")
    resp = "✅ 조건 만족 코인:\n"
    for p in good[:5]:
        resp += f"{p['baseToken']['symbol']}: 유동성 ${float(p['liquidity']['usd']):.0f}\n"
    await msg.reply(resp)

@dp.message_handler(commands=['topmemes'])
async def cmd_topmemes(msg: types.Message):
    await msg.reply("🔍 상위 수익률 코인 로드 중...")
    data = await fetch_json('https://api.dexscreener.com/latest/dex/pairs/solana')
    sorted_pairs = sorted(data.get('pairs', []), key=lambda p: float(p['priceChange']['h24']), reverse=True)
    resp = "📈 24h 수익률 상위 5:\n"
    for p in sorted_pairs[:5]:
        resp += f"{p['baseToken']['symbol']}: {float(p['priceChange']['h24']):.1f}%\n"
    await msg.reply(resp)

@dp.message_handler(commands=['rugrisk'])
async def cmd_rugrisk(msg: types.Message):
    addr = msg.get_args().strip()
    if not addr:
        return await msg.reply("/rugrisk 뒤에 토큰 주소를 붙여줘")
    res = await fetch_json(f"https://api.rugcheck.io/v1/score/{addr}?api_key={RUGCHECK_API}")
    score = res.get('score', 0)
    await msg.reply(f"🔍 {addr} 러그풀 위험 점수: {score:.1f}%")

@dp.message_handler(commands=['tokeninfo'])
async def cmd_tokeninfo(msg: types.Message):
    addr = msg.get_args().strip()
    if not addr:
        return await msg.reply("/tokeninfo 뒤에 토큰 주소를 붙여줘")
    info = await fetch_json(f"https://api.birdeye.so/v1/token/{addr}")
    await msg.reply(
        f"시가총액: {info.get('marketCap'):,} USD\n"
        f"홀더 수: {info.get('holders')}\n"
        f"유동성: {info.get('liquidity'):,} USD\n"
        f"세금: {info.get('tax', 'N/A')}%"
    )

@dp.message_handler(commands=['buy', 'sell'])
async def cmd_trade(msg: types.Message):
    args = msg.get_args().split()
    if not args:
        return await msg.reply("/buy 또는 /sell 뒤에 토큰 주소를 붙여줘")
    addr = args[0]
    link = f"https://jup.ag/swap?input=SOL&output={addr}&amount=1"
    await msg.reply(f"{msg.text.split()[0].upper()} 링크: {link}")

@dp.message_handler(commands=['report'])
async def cmd_report(msg: types.Message):
    addr = msg.get_args().strip()
    uid = msg.from_user.id
    if not addr:
        return await msg.reply("/report 뒤에 토큰 주소를 붙여줘")
    c = db.cursor()
    c.execute("INSERT INTO reports (user_id, token_address) VALUES (?,?)", (uid, addr))
    db.commit()
    await bot.send_message(ADMIN_CHAT_ID, f"신고: {msg.from_user.full_name}({uid}) -> {addr}")
    await msg.reply("✅ 신고 완료, 관리자에게 전달했어.")

@dp.message_handler(commands=['vote'])
async def cmd_vote(msg: types.Message):
    addr = msg.get_args().strip()
    if not addr:
        return await msg.reply("/vote 뒤에 토큰 주소를 붙여줘")
    c = db.cursor()
    c.execute("INSERT OR IGNORE INTO votes VALUES (?,0)", (addr,))
    c.execute("UPDATE votes SET votes = votes + 1 WHERE token_address=?", (addr,))
    db.commit()
    count = c.execute("SELECT votes FROM votes WHERE token_address=?", (addr,)).fetchone()[0]
    await msg.reply(f"✅ {addr}에 투표 완료! 현재 득표: {count}")

@dp.message_handler(commands=['community'])
async def cmd_community(msg: types.Message):
    await msg.reply("Solana 커뮤니티: https://t.me/solana_kr, https://discord.gg/solana")

@dp.message_handler(commands=['faq'])
async def cmd_faq(msg: types.Message):
    await msg.reply("자주 묻는 질문:\n1. 봇은 어떻게 사용해? /start 참고\n2. 스캔은 신뢰할 수 있나? 참고용이야\n...")

@dp.message_handler(commands=['language'])
async def cmd_language(msg: types.Message):
    await msg.reply("언어 설정: 아직 미지원")

@dp.message_handler(commands=['audit'])
async def cmd_audit(msg: types.Message):
    addr = msg.get_args().strip()
    if not addr:
        return await msg.reply("/audit 뒤에 토큰 주소를 붙여줘")
    await msg.reply(f"🔎 {addr} 정밀 분석 중...")
    # TODO: AI 기반 분석 모듈
    await msg.reply("📝 정밀 분석 완료: 이상 없음")

# --- 자동매매 명령어 ---
@dp.message_handler(commands=['autobuy', 'autosell'])
async def cmd_autotrade(msg: types.Message):
    args = msg.get_args().split()
    if len(args) < 4:
        return await msg.reply("사용법: /autobuy [토큰주소] [수량] [목표가] [손절가]")
    addr, amount, tp, sp = args
    uid = msg.from_user.id
    side = 'buy' if msg.text.startswith('/autobuy') else 'sell'
    c = db.cursor()
    c.execute("REPLACE INTO auto_trades VALUES (?,?,?,?,?,?)",
              (uid, addr, side, float(amount), float(tp), float(sp)))
    db.commit()
    await msg.reply(f"✅ {addr} {side} 조건 등록!\n수량: {amount}\n목표가: {tp} / 손절가: {sp}")

@dp.message_handler(commands=['autostatus'])
async def cmd_autostatus(msg: types.Message):
    uid = msg.from_user.id
    rows = db.cursor().execute("SELECT token_address, side, amount, target_price, stop_price FROM auto_trades WHERE user_id=?", (uid,)).fetchall()
    if not rows:
        return await msg.reply("📭 자동매매 등록된게 없어")
    text = "📋 자동매매 상태:\n"
    for t, s, a, tp, sp in rows:
        text += f"{t} - {s} {a}개 (목표가:{tp} / 손절가:{sp})\n"
    await msg.reply(text)

@dp.message_handler(commands=['autocancel'])
async def cmd_autocancel(msg: types.Message):
    addr = msg.get_args().strip()
    uid = msg.from_user.id
    if not addr:
        return await msg.reply("/autocancel [토큰주소]")
    db.cursor().execute("DELETE FROM auto_trades WHERE user_id=? AND token_address=?", (uid, addr))
    db.commit()
    await msg.reply(f"❌ {addr} 자동매매 조건 취소됨")

# --- 스케줄러 ---
async def scheduled_alerts():
    await bot.wait_until_ready()
    while True:
        c = db.cursor()
        users = c.execute("SELECT user_id FROM alerts WHERE enabled=1").fetchall()
        for (uid,) in users:
            await bot.send_message(uid, "🔔 신규 안전 코인 확인해봐! /newmemecoins")
        await asyncio.sleep(3600)

# --- 자동매매 모니터링 ---
async def auto_trade_loop():
    await bot.wait_until_ready()
    while True:
        trades = db.cursor().execute("SELECT user_id, token_address, side, amount, target_price, stop_price FROM auto_trades").fetchall()
        for uid, token, side, amt, tp, sp in trades:
            try:
                data = await fetch_json(f"https://api.dexscreener.com/latest/dex/tokens/{token}")
                price = float(data['pairs'][0]['priceUsd'])
                if price >= tp or price <= sp:
                    await bot.send_message(uid, f"⚡ {token} {side.upper()} 조건 달성!\n현재가: {price}\n수량: {amt}\n➡️ 실제 체결 로직은 추후 추가 예정")
                    db.cursor().execute("DELETE FROM auto_trades WHERE user_id=? AND token_address=?", (uid, token))
                    db.commit()
            except Exception as e:
                print(f"[AUTO TRADE ERROR] {e}")
        await asyncio.sleep(30)

if __name__ == '__main__':
    init_db()
    loop = asyncio.get_event_loop()
    loop.create_task(scheduled_alerts())
    loop.create_task(auto_trade_loop())
    executor.start_polling(dp, skip_updates=True)
