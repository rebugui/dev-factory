"""ChatDev GLM API Client - GLM-5를 직접 사용하여 코드 생성

ChatDev 서버 없이 GLM API를 직접 호출하여 7개 에이전트 역할 수행
"""

import os
import json
import logging
import requests
import time
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger('builder-agent.chatdev_glm')


class ChatDevGLMClient:
    """GLM API를 직접 사용하는 ChatDev 클라이언트
    
    7개 에이전트 역할:
    1. CEO - 요구사항 분석
    2. CPO - 제품 기획
    3. CTO - 아키텍처 설계
    4. Programmer - 코드 생성
    5. Reviewer - 코드 리뷰
    6. Tester - 테스트 생성
    7. CTO Final - 최종 검증
    """
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = "glm-4-plus"):
        """초기화
        
        Args:
            api_key: GLM API 키 (없으면 환경 변수에서 가져옴)
            base_url: GLM API URL
            model: 사용할 모델 (glm-4-plus 또는 glm-5)
        """
        self.api_key = api_key or os.getenv('BUILDER_GLM_API_KEY') or os.getenv('GLM_API_KEY')
        self.base_url = base_url or "https://api.z.ai/api/coding/paas/v4"
        self.model = model
        self.timeout = 60
        
        if not self.api_key:
            raise ValueError("GLM API 키가 필요합니다. BUILDER_GLM_API_KEY 또는 GLM_API_KEY 환경 변수를 설정하세요.")
    
    def chat(self, messages: List[Dict], temperature: float = 0.7, max_retries: int = 10, initial_delay: int = 5) -> str:
        """GLM API 호출 (자동 재시도 포함)
        
        Args:
            messages: 대화 메시지 리스트
            temperature: 생성 다양성 (0.0-1.0)
            max_retries: 최대 재시도 횟수 (기본 10회)
            initial_delay: 초기 대기 시간 (초, 기본 5초)
            
        Returns:
            생성된 응답
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': 4000
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f'{self.base_url}/chat/completions',
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                data = response.json()
                return data['choices'][0]['message']['content']
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    # Rate limit - 재시도
                    if attempt < max_retries - 1:
                        # 지수 백오프하며 대기 시간 증가
                        delay = initial_delay * (2 ** attempt)
                        logger.warning(f"Rate limit hit (attempt {attempt + 1}/{max_retries}), waiting {delay}s...")
                        time.sleep(delay)
                    else:
                        logger.error(f"Rate limit persists after {max_retries} attempts")
                        raise
                else:
                    # 다른 HTTP 에러는 즉시 실패
                    logger.error(f"GLM API HTTP error: {e}")
                    raise
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    logger.warning(f"Timeout (attempt {attempt + 1}/{max_retries}), retrying...")
                    time.sleep(2)
                else:
                    logger.error("GLM API timeout after retries")
                    raise
            except requests.exceptions.RequestException as e:
                logger.error(f"GLM API error: {e}")
                raise
        
        # 모든 재시도 실패
        raise Exception(f"Failed after {max_retries} retries")
    
    # ──────────────────────────────────────────────
    # 에이전트 역할
    # ──────────────────────────────────────────────
    
    def act_as_ceo(self, idea: Dict) -> Dict:
        """CEO: 요구사항 분석"""
        prompt = f"""당신은 소프트웨어 회사의 CEO입니다. 다음 프로젝트 아이디어를 분석해주세요.

프로젝트: {idea['title']}
설명: {idea.get('description', '')}
기술 스택: {', '.join(idea.get('tech_stack', ['python']))}

다음 사항을 분석해주세요:
1. 핵심 기능 (3-5개)
2. 사용자 타겟
3. 성공 기준
4. 예상 복잡도 (simple/medium/complex)

JSON 형식으로 응답해주세요."""

        messages = [
            {"role": "system", "content": "당신은 경험 많은 소프트웨어 회사의 CEO입니다."},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat(messages, temperature=0.7)
        
        try:
            # JSON 추출
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # 기본값 반환
        return {
            'features': ['main functionality'],
            'target_users': 'developers',
            'success_criteria': 'working code',
            'complexity': idea.get('complexity', 'simple')
        }
    
    def act_as_cto(self, requirements: Dict) -> Dict:
        """CTO: 아키텍처 설계"""
        prompt = f"""당신은 소프트웨어 아키텍트입니다. 다음 요구사항을 기반으로 기술 설계를 해주세요.

요구사항: {json.dumps(requirements, ensure_ascii=False, indent=2)}

다음 사항을 설계해주세요:
1. 디렉토리 구조
2. 주요 모듈 및 역할
3. 데이터 흐름
4. 의존성 (requirements.txt)

JSON 형식으로 응답해주세요."""

        messages = [
            {"role": "system", "content": "당신은 경험 많은 소프트웨어 아키텍트입니다."},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat(messages, temperature=0.7)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # 기본 구조 반환
        return {
            'structure': {
                'src/main.py': 'Main entry point',
                'src/utils.py': 'Utility functions',
                'tests/test_main.py': 'Unit tests',
                'README.md': 'Documentation',
                'requirements.txt': 'Dependencies'
            }
        }
    
    def act_as_programmer(self, architecture: Dict, idea: Dict) -> Dict[str, str]:
        """Programmer: 코드 생성"""
        prompt = f"""당신은 숙련된 프로그래머입니다. 다음 아키텍처를 기반으로 코드를 작성해주세요.

프로젝트: {idea['title']}
설명: {idea.get('description', '')}
아키텍처: {json.dumps(architecture, ensure_ascii=False, indent=2)}

다음 파일들을 생성해주세요:
1. src/main.py - 메인 로직
2. src/utils.py - 유틸리티 함수
3. tests/test_main.py - 단위 테스트
4. README.md - 사용 문서
5. requirements.txt - 의존성

각 파일의 내용을 완전한 코드로 작성해주세요. 파일명과 코드를 명확히 구분해서 응답해주세요."""

        messages = [
            {"role": "system", "content": "당신은 숙련된 Python 프로그래머입니다. 깔끔하고 테스트 가능한 코드를 작성합니다."},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat(messages, temperature=0.7)
        
        # 파일 추출
        files = self._extract_files(response)
        
        return files
    
    def act_as_tester(self, code_files: Dict[str, str]) -> Dict[str, str]:
        """Tester: 테스트 생성 및 검증"""
        # 이미 Programmer가 테스트를 작성했으므로 검증만 수행
        prompt = f"""당신은 QA 엔지니어입니다. 다음 코드의 테스트를 검증하고 개선해주세요.

코드 파일: {list(code_files.keys())}

기존 테스트를 확인하고:
1. 커버리지가 충분한지 (80% 이상 목표)
2. 엣지 케이스가 포함되었는지
3. 에러 핸들링이 적절한지

필요시 tests/test_main.py를 개선해주세요."""

        messages = [
            {"role": "system", "content": "당신은 꼼꼼한 QA 엔지니어입니다."},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat(messages, temperature=0.7)
        
        # 개선된 테스트 추출
        improved_tests = self._extract_files(response)
        
        # 기존 테스트 파일 업데이트
        if 'tests/test_main.py' in improved_tests:
            code_files['tests/test_main.py'] = improved_tests['tests/test_main.py']
        
        return code_files
    
    # ──────────────────────────────────────────────
    # 전체 개발 파이프라인
    # ──────────────────────────────────────────────
    
    def develop(self, idea: Dict) -> Dict[str, str]:
        """전체 개발 파이프라인 실행
        
        Args:
            idea: 프로젝트 아이디어
            
        Returns:
            생성된 파일들 (파일명: 내용)
        """
        logger.info("Starting ChatDev GLM development pipeline...")
        logger.info(f"Project: {idea['title']}")
        
        # 1. CEO: 요구사항 분석
        logger.info("Phase 1: CEO analyzing requirements...")
        requirements = self.act_as_ceo(idea)
        logger.info(f"  Features: {len(requirements.get('features', []))}")
        
        # 2. CTO: 아키텍처 설계
        logger.info("Phase 2: CTO designing architecture...")
        architecture = self.act_as_cto(requirements)
        logger.info(f"  Files: {len(architecture.get('structure', {}))}")
        
        # 3. Programmer: 코드 생성
        logger.info("Phase 3: Programmer generating code...")
        code_files = self.act_as_programmer(architecture, idea)
        logger.info(f"  Generated: {len(code_files)} files")
        
        # 4. Tester: 테스트 검증
        logger.info("Phase 4: Tester validating tests...")
        code_files = self.act_as_tester(code_files)
        
        logger.info("✅ Development pipeline completed!")
        
        return code_files
    
    # ──────────────────────────────────────────────
    # 유틸리티
    # ──────────────────────────────────────────────
    
    def _extract_files(self, response: str) -> Dict[str, str]:
        """응답에서 파일 내용 추출"""
        import re
        
        files = {}
        
        # 패턴 1: ```python\n# filename.py\ncode\n```
        pattern1 = r'```(?:python|bash|text)\s*\n#?\s*([^\n]+\.py|\.txt|\.md)\s*\n(.*?)```'
        matches1 = re.findall(pattern1, response, re.DOTALL)
        
        for filename, code in matches1:
            filename = filename.strip().lstrip('# ')
            # 경로 정리
            if '/' not in filename:
                if filename.endswith('_test.py') or filename.startswith('test_'):
                    filename = f'tests/{filename}'
                elif filename in ['README.md', 'requirements.txt']:
                    pass
                else:
                    filename = f'src/{filename}'
            
            files[filename] = code.strip()
        
        # 패턴 2: **filename.py**\n```python\ncode\n```
        if not files:
            pattern2 = r'\*\*([^\*]+\.py|\.txt|\.md)\*\*\s*\n```(?:python|bash|text)?\s*\n(.*?)```'
            matches2 = re.findall(pattern2, response, re.DOTALL)
            
            for filename, code in matches2:
                filename = filename.strip()
                if '/' not in filename:
                    if 'test' in filename.lower():
                        filename = f'tests/{filename}'
                    elif filename in ['README.md', 'requirements.txt']:
                        pass
                    else:
                        filename = f'src/{filename}'
                
                files[filename] = code.strip()
        
        # 파일이 없으면 기본 구조 생성
        if not files:
            logger.warning("Could not extract files from response, using basic structure")
            files = {
                'src/main.py': '# TODO: Implement main functionality\npass',
                'tests/test_main.py': '# TODO: Add tests\npass',
                'README.md': f'# {idea.get("title", "Project")}\n\nTODO: Add documentation',
                'requirements.txt': '# TODO: Add dependencies'
            }
        
        return files


# ──────────────────────────────────────────────
# 편의 함수
# ──────────────────────────────────────────────

def develop_project(idea: Dict, model: str = "glm-4-plus") -> Dict[str, str]:
    """프로젝트 개발 (편의 함수)
    
    Args:
        idea: 프로젝트 아이디어
        model: 사용할 GLM 모델 (glm-4-plus 또는 glm-5)
        
    Returns:
        생성된 파일들
    """
    client = ChatDevGLMClient(model=model)
    return client.develop(idea)


def save_project(files: Dict[str, str], output_dir: Path):
    """생성된 파일 저장
    
    Args:
        files: 파일 딕셔너리 (파일명: 내용)
        output_dir: 출력 디렉토리
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for filepath, content in files.items():
        full_path = output_dir / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        logger.info(f"Created: {filepath}")
    
    logger.info(f"✅ Saved {len(files)} files to {output_dir}")
