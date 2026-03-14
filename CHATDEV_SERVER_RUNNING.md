# ChatDev 2.0 서버 실행 완료

**실행 일시**: 2026-03-14 20:41
**상태**: ✅ 정상 실행 중
**URL**: http://localhost:6400
**Health Check**: {"status":"healthy"}

---

## 🎉 서버 실행 성공

### 프로세스 정보
```
PID: 81887
Python: 3.11.15
Port: 6400
Command: python3.11 server_main.py --port 6400
```

### Health Check 결과
```bash
curl http://localhost:6400/health
# {"status":"healthy"}
```

### API 엔드포인트
- **Health**: http://localhost:6400/health
- **Create Project**: POST http://localhost:6400/create
- **Status**: GET http://localhost:6400/status/{task_id}

---

## 📝 Builder Agent 설정

### config.yaml 확인
```yaml
chatdev:
  server_url: "http://localhost:6400"
  glm_api_key: "${BUILDER_GLM_API_KEY}"
  model: "glm-4-plus"  # 또는 "glm-5"
  timeout_seconds: 1800
  max_retries: 3
```

---

## 🧪 테스트 방법

### 1. 간단한 프로젝트 생성 테스트
```bash
curl -X POST http://localhost:6400/create \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create a password generator CLI tool in Python",
    "model": "glm-4-plus",
    "tech_stack": ["python"]
  }'
```

### 2. Builder Agent에서 사용
```python
from builder.orchestrator import HybridOrchestrator
from builder.models import ProjectIdea
from pathlib import Path

orchestrator = HybridOrchestrator()

idea = ProjectIdea(
    title="Password Generator",
    description="Secure password generator",
    tech_stack=["python"],
    complexity="simple"
)

result = orchestrator.develop(idea, Path("/tmp/password-gen"))
print(f"Success: {result.success}")
```

### 3. 통합 파이프라인 실행
```python
from builder.unified_pipeline import run_unified_pipeline
from pathlib import Path

result = run_unified_pipeline(
    idea={
        'title': 'My Tool',
        'tech_stack': ['python']
    },
    project_path=Path('/tmp/my-tool'),
    publish=True  # GitHub PR 자동 생성
)
```

---

## 🔄 서버 관리

### 중지
```bash
kill 81887
```

### 재시작
```bash
cd ~/.openclaw/workspace/chatdev-v2
source venv/bin/activate
python3.11 server_main.py --port 6400 > /tmp/chatdev-server.log 2>&1 &
```

### 로그 확인
```bash
tail -f /tmp/chatdev-server.log
```

---

## 🎯 다음 단계

1. **간단한 프로젝트 테스트** - Password Generator
2. **통합 파이프라인 테스트** - Discovery → Build → Test → Publish
3. **GLM-5 모델 테스트** - 더 높은 품질

---

**Server Status**: ✅ Running on port 6400
**Ready for**: Development automation
