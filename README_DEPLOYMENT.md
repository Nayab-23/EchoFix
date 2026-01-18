# 🚀 EchoFix Deployment - READ THIS FIRST

## ⚡ Super Quick Start (3 Commands)

```bash
cd /Users/severinspagnola/Desktop/EchoFix
cp backend/.env.example backend/.env && echo "DEMO_MODE=true" >> backend/.env
./deploy.sh
```

**Done!** Access at http://localhost:8000 and http://localhost:5678

---

## 📋 Bring Up & Bring Down

### 🛑 Bring Down (Stop)
```bash
./stop.sh              # Stops services, keeps data
./teardown.sh          # ⚠️ Deletes everything
```

### 🚀 Bring Up (Start)
```bash
./deploy.sh            # Start everything
./restart.sh           # Quick restart
```

---

## 🎮 All Commands

```bash
./deploy.sh            # Deploy/start everything
./stop.sh              # Stop (keeps data)
./restart.sh           # Restart
./status.sh            # Check health
./logs.sh [service]    # View logs
./rebuild.sh           # Rebuild after code changes
./teardown.sh          # Delete everything
```

---

## 📍 Service URLs

- Backend: http://localhost:8000
- Health: http://localhost:8000/health
- n8n: http://localhost:5678

---

## 📚 Documentation

| File | Description |
|------|-------------|
| [QUICKSTART.md](QUICKSTART.md) | 3-step setup |
| [BRING_UP_DOWN.md](BRING_UP_DOWN.md) | **Detailed up/down commands** |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Complete guide |
| [ALL_COMMANDS.md](ALL_COMMANDS.md) | Every command |
| [CHEATSHEET.txt](CHEATSHEET.txt) | Print this! |

---

## 🔧 Troubleshooting

```bash
# Check what's wrong
./status.sh

# View logs
./logs.sh backend

# Fresh start
./teardown.sh && ./deploy.sh
```

---

**Need help?** See [BRING_UP_DOWN.md](BRING_UP_DOWN.md) for detailed up/down commands!
