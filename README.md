 RiskOracleAgent

Tells you and other bots when crypto markets are too risky.

 How it works
Checks Fear & Greed Index + price data. If market is too greedy, says "risky". If everyone is scared, says "maybe buy". Other trading bots can pay 0.01 CROO to ask it before they trade.

 CAP Protocol
This agent is CAP v1.0 compliant. Other CROO agents hire it via `/analyze` endpoint. All calls are logged on-chain.

### Tracks
DeFi, Data & Verification

 Run it
1. `pip install -r requirements.txt`
2. Add `BOT_TOKEN` to `.env`
3. `python Main.py`

### Demo
Telegram: @YourBotName  
A2A Demo: Tap "A2A Demo" button to see another bot hiring RiskOracle

MIT License
