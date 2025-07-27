
📘 ScamCheckerSolBot 사용 설명서 (for Alan)
========================================

🤖 이 봇은 Solana 밈코인을 실시간으로 분석하고, 자동으로 수익성 있는 거래를 실행하는 Telegram 봇입니다.
Alan, 이제 PC 없이도 아이폰 Telegram에서 모든 걸 할 수 있어!

1️⃣ 설치 및 실행 (Render 기준)
-----------------------------
1. Render.com 에 가입 후 새 Web Service 생성
2. GitHub 또는 zip 업로드 방식 선택
3. 다음 파일 업로드:
   - main.py (봇 코드)
   - requirements.txt
   - .env (지갑, 토큰 등)
4. Start Command:
   ```bash
   python main.py
   ```

2️⃣ 주요 명령어 정리
-----------------------------

💬 일반 명령어:
- `/start` : 봇 기능 요약 안내
- `/newmemecoins` : 스캠 제외 + 유동성 있는 신규 코인 추천
- `/scan [토큰주소]` : 해당 토큰 스캠 여부 분석
- `/tokeninfo [토큰주소]` : 시총, 홀더, 유동성, 수수료 요약
- `/rugrisk [토큰주소]` : 러그풀 위험 점수 (0~100)
- `/volume [토큰주소]` : 거래량 변화 분석
- `/topmemes` : 수익률 상위 밈코인 목록

🧠 AI 분석 기능:
- `/ask [질문]` : GPT에게 Solana 관련 질문하기
- `/strategy` : 지금 시장에 맞는 자동매매 전략 제안

🔔 감시 및 알림:
- `/alerts_on` : 1시간마다 안전 신규 코인 자동 알림 켜기
- `/alerts_off` : 자동 알림 끄기
- `/watch [토큰주소]` : 해당 토큰 감시 등록

⚙️ 자동매매 관련:
- `/autobuy [주소] [SOL수량] [목표가] [손절가]`
- `/autosell [주소] [수량] [목표가] [손절가]`
- `/autostatus` : 등록된 자동매매 상태 확인
- `/autocancel [주소]` : 자동매매 조건 삭제

🎮 기타:
- `/report [주소]` : 스캠 신고 (관리자에게 전달)
- `/vote [주소]` : 안전한 코인에 투표
- `/community` : Solana 커뮤니티 링크 제공
- `/faq` : 자주 묻는 질문
- `/language` : 언어 설정 (예정)

3️⃣ 실제 예시 흐름
-----------------------------

Alan: `/newmemecoins`  
봇: 신규 코인 3개 추천 (유동성 + 상승률 기준)

Alan: `/scan Gqsv...LJL`  
봇: 위험 신호 분석 (락업, 소유권, 유동성 등)

Alan: `/autobuy Gqsv...LJL 0.3 0.0002 0.0001`  
봇: 조건 등록됨. 30초마다 가격 체크해서 자동 체결됨.

Alan: `/autostatus`  
봇: 현재 등록된 조건 확인

Alan: `/autocancel Gqsv...LJL`  
봇: 해당 토큰에 대한 조건 삭제

4️⃣ 주의사항 및 팁
-----------------------------
- `.env`에 지갑 키와 OpenAI 키가 저장되어 있음. 절대 유출 금지!
- Telegram만으로 모든 기능을 제어할 수 있음 (아이폰에서 완전 사용 가능)
- 30초 간격으로 자동매매 조건을 체크함
- 거래 체결은 Jupiter Aggregator를 통해 Phantom 지갑에서 실행됨
- 결과는 항상 텔레그램으로 확인 가능

5️⃣ 만든 사람
-----------------------------
Alan의 아이디어 + GPT-4 전문가 조합!

시작하려면 Render 배포 또는 로컬에서 `python main.py` 실행해봐.

🔥 이제 솔라나 밈코인 시장은 네 손 안에 있어. 수익 내보자, Alan!

