"""GitHub Trending 발굴 (agent-browser 통합 버전)"""

import logging
import subprocess
import json
import re
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from builder.discovery.base import DiscoverySource
from builder.models import DiscoverySource as DS

logger = logging.getLogger('builder-agent.discovery.github_enhanced')


class GitHubTrendingEnhancedSource(DiscoverySource):
    """agent-browser를 활용한 정교한 GitHub Trending 발굴"""

    def __init__(self, config=None):
        super().__init__(config)
        self.language = getattr(config, 'language', 'python') if config else "python"
        self.since = getattr(config, 'since', 'daily') if config else "daily"
        self.max_results = getattr(config, 'max_results', 5) if config else 5
        self.use_api = getattr(config, 'use_github_api', False) if config else False
        self.github_token = self._get_github_token()

    def _get_github_token(self) -> Optional[str]:
        """GitHub 토큰 가져오기"""
        try:
            # .env에서 토큰 읽기
            env_file = Path.home() / '.openclaw' / 'workspace' / '.env'
            if env_file.exists():
                content = env_file.read_text()
                for line in content.split('\n'):
                    if line.startswith('GITHUB_TOKEN='):
                        return line.split('=', 1)[1].strip()
        except Exception:
            pass
        return None

    def discover(self) -> List[Dict]:
        """GitHub Trending에서 아이디어 발굴
        
        전략:
        1. GitHub API 사용 (가장 정확)
        2. agent-browser 사용 (API 제한 시)
        3. 정규식 파싱 (fallback)
        """
        if not self.enabled:
            return []

        ideas = []

        # 전략 1: GitHub API (가장 정확)
        if self.use_api and self.github_token:
            ideas = self._discover_via_api()
            if ideas:
                logger.info("GitHub API: %d ideas", len(ideas))
                return ideas

        # 전략 2: agent-browser (정확)
        ideas = self._discover_via_agent_browser()
        if ideas:
            logger.info("agent-browser: %d ideas", len(ideas))
            return ideas

        # 전략 3: 정규식 (fallback)
        ideas = self._discover_via_regex()
        logger.info("Regex parsing: %d ideas", len(ideas))

        return ideas

    def _discover_via_api(self) -> List[Dict]:
        """GitHub Search API 사용"""
        import requests

        try:
            # 최근 일주일 내 인기 Python 저장소 검색
            url = "https://api.github.com/search/repositories"
            params = {
                'q': f'language:{self.language} created:>2024-01-01',
                'sort': 'stars',
                'order': 'desc',
                'per_page': self.max_results
            }
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            ideas = []

            for repo in data.get('items', [])[:self.max_results]:
                # 보안/DevOps 관련 필터링
                if self._is_security_related(repo):
                    ideas.append({
                        'title': f"Clone/Improve: {repo['full_name']}",
                        'description': repo.get('description', 'No description')[:200],
                        'source': DS.GITHUB_TRENDING.value,
                        'url': repo['html_url'],
                        'stars': repo['stargazers_count'],
                        'language': repo.get('language', 'Unknown'),
                        'complexity': self._estimate_complexity(repo),
                        'priority': 'high' if repo['stargazers_count'] > 1000 else 'medium',
                        'discovered_at': datetime.now().isoformat()
                    })

            return ideas

        except Exception as e:
            logger.warning("GitHub API failed: %s", e)
            return []

    def _discover_via_agent_browser(self) -> List[Dict]:
        """agent-browser CLI 사용"""
        try:
            # agent-browser가 설치되어 있는지 확인
            check = subprocess.run(
                ['which', 'agent-browser'],
                capture_output=True, text=True
            )
            if check.returncode != 0:
                logger.debug("agent-browser not installed")
                return []

            # GitHub Trending 페이지 열기
            url = f"https://github.com/trending/{self.language}?since={self.since}"
            
            # snapshot -i로 interactive elements 추출
            result = subprocess.run(
                ['agent-browser', 'open', url],
                capture_output=True, text=True, timeout=15
            )

            if result.returncode != 0:
                logger.warning("agent-browser open failed")
                return []

            # 페이지 스냅샷
            result = subprocess.run(
                ['agent-browser', 'snapshot', '-i', '--json'],
                capture_output=True, text=True, timeout=15
            )

            if result.returncode != 0:
                logger.warning("agent-browser snapshot failed")
                return []

            # JSON 파싱
            snapshot = json.loads(result.stdout)
            ideas = []

            # 레포지토리 링크 추출
            for element in snapshot.get('elements', []):
                if 'href' in element and '/repo/' in element.get('role', ''):
                    repo_url = element['href']
                    repo_name = repo_url.split('/')[-2:]
                    repo_full_name = '/'.join(repo_name)

                    # 레포 정보 가져오기
                    ideas.append({
                        'title': f"Clone/Improve: {repo_full_name}",
                        'description': element.get('text', 'No description')[:200],
                        'source': DS.GITHUB_TRENDING.value,
                        'url': f"https://github.com/{repo_full_name}",
                        'complexity': 'medium',
                        'priority': 'medium',
                        'discovered_at': datetime.now().isoformat()
                    })

                    if len(ideas) >= self.max_results:
                        break

            # 브라우저 닫기
            subprocess.run(['agent-browser', 'close'], capture_output=True)

            return ideas

        except subprocess.TimeoutExpired:
            logger.warning("agent-browser timeout")
            return []
        except json.JSONDecodeError as e:
            logger.warning("agent-browser JSON parse error: %s", e)
            return []
        except Exception as e:
            logger.warning("agent-browser error: %s", e)
            return []

    def _discover_via_regex(self) -> List[Dict]:
        """정규식 파싱 (fallback)"""
        import urllib.request

        try:
            url = f"https://github.com/trending/{self.language}?since={self.since}"
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')

            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode('utf-8')

            # 간단한 정규식으로 레포 추출
            repo_pattern = r'<h2[^>]*>.*?<a[^>]*href="/([^"]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(repo_pattern, html, re.DOTALL)[:self.max_results]

            ideas = []
            for repo_path, repo_name in matches:
                ideas.append({
                    'title': f"Clone/Improve: {repo_path}",
                    'description': f"Trending {self.language} repository",
                    'source': DS.GITHUB_TRENDING.value,
                    'url': f"https://github.com/{repo_path}",
                    'complexity': 'medium',
                    'priority': 'medium',
                    'discovered_at': datetime.now().isoformat()
                })

            return ideas

        except Exception as e:
            logger.warning("Regex parsing failed: %s", e)
            return []

    def _is_security_related(self, repo: Dict) -> bool:
        """보안/DevOps 관련 저장소인지 확인"""
        keywords = [
            'security', 'scanner', 'vulnerability', 'pentest',
            'cli', 'tool', 'automation', 'devops', 'monitoring',
            'analysis', 'detector', 'analyzer'
        ]
        
        text = f"{repo.get('description', '')} {repo.get('name', '')}".lower()
        return any(kw in text for kw in keywords)

    def _estimate_complexity(self, repo: Dict) -> str:
        """저장소 복잡도 추정"""
        size = repo.get('size', 0)  # KB
        forks = repo.get('forks_count', 0)
        
        if size > 10000 or forks > 500:  # 10MB+ or 500+ forks
            return 'complex'
        elif size > 1000 or forks > 50:  # 1MB+ or 50+ forks
            return 'medium'
        else:
            return 'simple'
