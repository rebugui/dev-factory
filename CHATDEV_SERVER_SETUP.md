# ChatDev 2.0 서버 설정 가이드

## 개요

ChatDev 2.0은 7개 에이전트가 협업하여 자동으로 소프트웨어를 개발하는 시스템입니다.

## 설치 방법

### 1. ChatDev 클론

```bash
cd ~/.openclaw/workspace
git clone --recursive https://github.com/OpenBMB/ChatDev.git chatdev-v2
cd chatdev-v2
```

### 2. Python 가상환경 생성

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 또는 venv\Scripts\activate (Windows)
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

`.env` 파일 생성:
```bash
# GLM API 설정
GLM_API_KEY=your_glm_api_key_here
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4

# 또는 OpenAI 사용
# OPENAI_API_KEY=your_openai_key
# OPENAI_BASE_URL=https://api.openai.com/v1
```

### 5. ChatDev 서버 실행

```bash
# 서버 시작 (기본 포트: 6400)
python server_main.py --port 6400

# 또는 GLM-5 사용
python server_main.py --port 6400 --model glm-5
```

서버가 실행되면:
- API URL: http://localhost:6400
- Health Check: http://localhost:6400/health

## Builder Agent 설정

### config.yaml 수정

```yaml
chatdev:
  server_url: "http://localhost:6400"
  glm_api_key: "${BUILDER_GLM_API_KEY}"
  model: "glm-5"  # 또는 "glm-4-plus"
  timeout_seconds: 1800  # 30분
  max_retries: 3
```

## ChatDev 서버 API

### 1. 헬스체크
```bash
curl http://localhost:6400/health
```

### 2. 프로젝트 생성
```bash
curl -X POST http://localhost:6400/create \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create a password generator CLI",
    "model": "glm-5",
    "tech_stack": ["python"]
  }'
```

### 3. 상태 확인
```bash
curl http://localhost:6400/status/{task_id}
```

## Builder Agent에서 사용

### Python 코드
```python
from builder.orchestrator import HybridOrchestrator
from builder.models import ProjectIdea
from pathlib import Path

# ChatDev 서버 사용
orchestrator = HybridOrchestrator()

idea = ProjectIdea(
    title="Password Generator",
    description="Secure password generator",
    tech_stack=["python"],
    complexity="simple"
)

result = orchestrator.develop(idea, Path("/tmp/password-gen"))
```

### 통합 파이프라인
```python
from builder.unified_pipeline import run_unified_pipeline

result = run_unified_pipeline(
    idea={
        'title': 'My Tool',
        'tech_stack': ['python']
    },
    project_path=Path('/tmp/my-tool'),
    publish=True  # GitHub PR 자동 생성
)
```

## 트러블슈팅

### 서버 실행 실패
```bash
# 포트 사용 중인지 확인
lsof -i :6400

# 다른 포트 사용
python server_main.py --port 6401
```

### GLM API 에러
- API 키 확인
- Rate limit 확인 (잠시 대기)
- 모델 이름 확인 (glm-4-plus 또는 glm-5)

### 의존성 에러
```bash
pip install --upgrade -r requirements.txt
```

## 백그라운드 실행

### systemd (Linux)
```bash
# 서비스 파일 생성
sudo nano /etc/systemd/system/chatdev.service

[Unit]
Description=ChatDev Server
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/home/yourusername/.openclaw/workspace/chatdev-v2
ExecStart=/home/yourusername/.openclaw/workspace/chatdev-v2/venv/bin/python server_main.py --port 6400
Restart=on-failure

[Install]
WantedBy=multi-user.target

# 서비스 시작
sudo systemctl start chatdev
sudo systemctl enable chatdev
```

### launchd (macOS)
```bash
# plist 파일 생성
nano ~/Library/LaunchAgents/com.chatdev.server.plist

<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.chatdev.server</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/yourusername/.openclaw/workspace/chatdev-v2/venv/bin/python</string>
        <string>server_main.py</string>
        <string>--port</string>
        <string>6400</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/yourusername/.openclaw/workspace/chatdev-v2</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>

# 로드
launchctl load ~/Library/LaunchAgents/com.chatdev.server.plist
```

## 성능 최적화

### 1. 캐싱 활성화
```yaml
chatdev:
  cache_enabled: true
  cache_ttl_seconds: 3600
```

### 2. 병렬 처리
```yaml
features:
  parallel_builds: true
```

### 3. GPU 사용 (가능한 경우)
```bash
python server_main.py --port 6400 --device cuda
```

## 모니터링

### 로그 확인
```bash
tail -f /tmp/builder-agent/builder.log
```

### 상태 대시보드
```bash
# ChatDev 서버 상태
curl http://localhost:6400/metrics

# Builder Agent 상태
python -c "from builder.pipeline import BuilderPipeline; print(BuilderPipeline().get_status())"
```

---

**다음 단계**: ChatDev 서버가 실행되면 Builder Agent가 자동으로 연결됩니다.
