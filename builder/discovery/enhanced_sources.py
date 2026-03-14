"""Enhanced Discovery Sources - 다양한 소스에서 아이디어 발굴

Product Hunt, Reddit, Hacker News, 한국 보안 뉴스 등 추가 소스
"""

import logging
import json
import re
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

from builder.discovery.base import DiscoverySource
from builder.models import DiscoverySource as DS

logger = logging.getLogger('builder-agent.discovery.enhanced')


class ProductHuntSource(DiscoverySource):
    """Product Hunt에서 트렌딩 프로덕트 발굴"""

    def __init__(self, config=None):
        super().__init__(config)
        self.max_results = getattr(config, 'max_results', 5) if config else 5

    def discover(self) -> List[Dict]:
        """Product Hunt API에서 트렌딩 프로덕트 조회"""
        if not self.enabled:
            return []

        ideas = []

        try:
            # Product Hunt GraphQL API (무료)
            query = '''
            {
                posts(first: 10, order: RANKING) {
                    edges {
                        node {
                            name
                            tagline
                            url
                            votesCount
                            topics {
                                edges {
                                    node {
                                        name
                                    }
                                }
                            }
                        }
                    }
                }
            }
            '''

            req = urllib.request.Request(
                'https://api.producthunt.com/v2/api/graphql',
                data=json.dumps({'query': query}).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            )

            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode())

            for edge in data['data']['posts']['edges'][:self.max_results]:
                post = edge['node']

                # 개발/보안 관련 토픽 필터링
                topics = [t['node']['name'] for t in post['topics']['edges']]
                keywords = ['developer tools', 'security', 'productivity', 'automation', 'api']

                if any(kw in ' '.join(topics).lower() for kw in keywords):
                    ideas.append({
                        'title': f"Clone: {post['name']}",
                        'description': post['tagline'][:200],
                        'source': 'product_hunt',
                        'url': post['url'],
                        'votes': post['votesCount'],
                        'topics': topics,
                        'complexity': 'medium',
                        'priority': 'high' if post['votesCount'] > 500 else 'medium',
                        'discovered_at': datetime.now().isoformat()
                    })

            logger.info("Product Hunt: %d ideas found", len(ideas))

        except Exception as e:
            logger.warning("Product Hunt API error: %s", e)

        return ideas


class HackerNewsSource(DiscoverySource):
    """Hacker News에서 트렌딩 스토리 발굴"""

    def __init__(self, config=None):
        super().__init__(config)
        self.max_results = getattr(config, 'max_results', 10) if config else 10

    def discover(self) -> List[Dict]:
        """Hacker News Top Stories 조회"""
        if not self.enabled:
            return []

        ideas = []

        try:
            # Top Stories ID 가져오기
            with urllib.request.urlopen(
                'https://hacker-news.firebaseio.com/v0/topstories.json',
                timeout=10
            ) as response:
                story_ids = json.loads(response.read().decode())[:self.max_results]

            # 각 스토리 조회
            for story_id in story_ids:
                try:
                    with urllib.request.urlopen(
                        f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json',
                        timeout=5
                    ) as response:
                        story = json.loads(response.read().decode())

                    if not story or 'title' not in story:
                        continue

                    # 개발/보안 관련 키워드 필터링
                    title = story.get('title', '').lower()
                    keywords = ['security', 'vulnerability', 'tool', 'library', 'framework',
                               'api', 'cli', 'automation', 'scanner', 'monitor']

                    if any(kw in title for kw in keywords):
                        ideas.append({
                            'title': f"HN: {story['title'][:60]}",
                            'description': f"Trending on Hacker News with {story.get('score', 0)} points",
                            'source': 'hacker_news',
                            'url': story.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                            'score': story.get('score', 0),
                            'comments': story.get('descendants', 0),
                            'complexity': 'medium',
                            'priority': 'high' if story.get('score', 0) > 200 else 'medium',
                            'discovered_at': datetime.now().isoformat()
                        })

                except Exception as e:
                    logger.debug("HN story %s error: %s", story_id, e)
                    continue

            logger.info("Hacker News: %d ideas found", len(ideas))

        except Exception as e:
            logger.warning("Hacker News API error: %s", e)

        return ideas


class RedditSource(DiscoverySource):
    """Reddit에서 개발/보안 관련 포스트 발굴"""

    SUBREDDITS = [
        'programming',
        'python',
        'security',
        'netsec',
        'devops',
        'automation'
    ]

    def __init__(self, config=None):
        super().__init__(config)
        self.max_results = getattr(config, 'max_results', 15) if config else 15

    def discover(self) -> List[Dict]:
        """Reddit Hot Posts 조회"""
        if not self.enabled:
            return []

        ideas = []

        try:
            for subreddit in self.SUBREDDITS[:3]:  # 상위 3개만
                try:
                    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=10"
                    req = urllib.request.Request(url)
                    req.add_header('User-Agent', 'Builder-Agent-Discovery/1.0')

                    with urllib.request.urlopen(req, timeout=10) as response:
                        data = json.loads(response.read().decode())

                    for post in data['data']['children'][:5]:
                        post_data = post['data']

                        # 셀프 포스트(토론) 제외, 링크 포스트만
                        if post_data.get('is_self', True):
                            continue

                        ideas.append({
                            'title': f"Reddit: {post_data['title'][:60]}",
                            'description': f"r/{subreddit} - {post_data.get('selftext', '')[:150]}",
                            'source': 'reddit',
                            'url': post_data['url'],
                            'subreddit': subreddit,
                            'upvotes': post_data['ups'],
                            'comments': post_data['num_comments'],
                            'complexity': 'medium',
                            'priority': 'high' if post_data['ups'] > 500 else 'medium',
                            'discovered_at': datetime.now().isoformat()
                        })

                except Exception as e:
                    logger.debug("Reddit r/%s error: %s", subreddit, e)
                    continue

            logger.info("Reddit: %d ideas found", len(ideas))

        except Exception as e:
            logger.warning("Reddit API error: %s", e)

        return ideas


class KoreanSecurityNewsSource(DiscoverySource):
    """한국 보안 뉴스 발굴 (KISA, 보호나라, 데일리시큐)"""

    SOURCES = {
        'kisa': {
            'name': 'KISA',
            'url': 'https://www.krcert.or.kr/krcert/secNoticeList.do',
            'keywords': ['취약점', '보안', '악성코드', '해킹']
        },
        'boho': {
            'name': '보호나라',
            'url': 'https://www.boho.or.kr/krcert/secNoticeList.do',
            'keywords': ['취약점', '랜섬웨어', '피싱']
        },
        'dailysecu': {
            'name': '데일리시큐',
            'url': 'https://www.dailysecu.com/news/articleList.html',
            'keywords': ['보안', '취약점', '해킹']
        }
    }

    def __init__(self, config=None):
        super().__init__(config)
        self.max_results = getattr(config, 'max_results', 10) if config else 10

    def discover(self) -> List[Dict]:
        """한국 보안 뉴스 스크래핑 (RSS 또는 agent-browser)"""
        if not self.enabled:
            return []

        ideas = []

        # agent-browser 사용 시도
        try:
            import subprocess

            for source_key, source_info in self.SOURCES.items():
                try:
                    # agent-browser로 페이지 접근
                    subprocess.run(
                        ['agent-browser', 'open', source_info['url']],
                        capture_output=True, timeout=15, check=False
                    )

                    import time
                    time.sleep(2)

                    # 스냅샷
                    result = subprocess.run(
                        ['agent-browser', 'snapshot', '-c'],
                        capture_output=True, text=True, timeout=10
                    )

                    snapshot = result.stdout

                    # 뉴스 헤드라인 추출
                    headlines = self._extract_headlines(snapshot, source_info['keywords'])

                    for headline in headlines[:5]:
                        ideas.append({
                            'title': f"[{source_info['name']}] {headline[:60]}",
                            'description': f"한국 보안 뉴스 - {headline}",
                            'source': 'korean_security_news',
                            'url': source_info['url'],
                            'provider': source_info['name'],
                            'complexity': 'medium',
                            'priority': 'high',
                            'discovered_at': datetime.now().isoformat()
                        })

                    # 브라우저 정리
                    subprocess.run(['agent-browser', 'close'],
                                 capture_output=True, timeout=5)

                except Exception as e:
                    logger.debug("%s scraping error: %s", source_info['name'], e)
                    continue

            logger.info("Korean Security News: %d ideas found", len(ideas))

        except Exception as e:
            logger.warning("Korean Security News error: %s", e)

        return ideas

    def _extract_headlines(self, snapshot: str, keywords: List[str]) -> List[str]:
        """스냅샷에서 헤드라인 추출"""
        headlines = []

        # 간단한 텍스트 추출
        lines = snapshot.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 20 and len(line) < 150:
                # 키워드 매칭
                if any(kw in line for kw in keywords):
                    headlines.append(line)

        return list(set(headlines))  # 중복 제거


class TrendingRepositoriesSource(DiscoverySource):
    """GitHub Trending 다양한 언어/기간 조회"""

    LANGUAGES = ['python', 'javascript', 'typescript', 'go', 'rust']
    PERIODS = ['daily', 'weekly', 'monthly']

    def __init__(self, config=None):
        super().__init__(config)
        self.max_results = getattr(config, 'max_results', 10) if config else 10

    def discover(self) -> List[Dict]:
        """GitHub Trending 다양한 조합 조회"""
        if not self.enabled:
            return []

        ideas = []

        try:
            # Python daily만 (기존)
            # 추가로 Go, Rust 등 시스템 언어도 조회
            for lang in ['go', 'rust']:
                try:
                    url = f"https://github.com/trending/{lang}?since=daily"

                    req = urllib.request.Request(url)
                    req.add_header('User-Agent', 'Mozilla/5.0')

                    with urllib.request.urlopen(req, timeout=15) as response:
                        html = response.read().decode('utf-8')

                    # 레포 추출
                    repo_pattern = r'<h2[^>]*>.*?<a[^>]*href="/([^"]+)"[^>]*>([^<]+)</a>'
                    matches = re.findall(repo_pattern, html, re.DOTALL)[:3]

                    for repo_path, repo_name in matches:
                        ideas.append({
                            'title': f"GitHub Trending [{lang}]: {repo_path}",
                            'description': f"Trending {lang} repository",
                            'source': DS.GITHUB_TRENDING.value,
                            'url': f"https://github.com/{repo_path}",
                            'language': lang,
                            'complexity': 'medium',
                            'priority': 'medium',
                            'discovered_at': datetime.now().isoformat()
                        })

                except Exception as e:
                    logger.debug("GitHub Trending [%s] error: %s", lang, e)
                    continue

            logger.info("GitHub Trending (multi-lang): %d ideas found", len(ideas))

        except Exception as e:
            logger.warning("GitHub Trending error: %s", e)

        return ideas


class RSSNewsSource(DiscoverySource):
    """RSS 피드에서 뉴스 발굴 (보안, 개발 관련)"""

    RSS_FEEDS = [
        'https://www.bleepingcomputer.com/feed/',
        'https://threatpost.com/feed/',
        'https://www.reddit.com/r/netsec/.rss',
        'https://feeds.feedburner.com/TheHackersNews',
    ]

    def __init__(self, config=None):
        super().__init__(config)
        self.max_results = getattr(config, 'max_results', 10) if config else 10

    def discover(self) -> List[Dict]:
        """RSS 피드에서 보안 뉴스 수집"""
        if not self.enabled:
            return []

        ideas = []

        try:
            import feedparser
        except ImportError:
            logger.debug("feedparser not installed, skipping RSS feeds")
            return ideas

        for feed_url in self.RSS_FEEDS[:2]:  # 상위 2개만
            try:
                feed = feedparser.parse(feed_url)

                for entry in feed.entries[:5]:
                    title = entry.get('title', '')

                    # 보안/개발 키워드 필터링
                    keywords = ['security', 'vulnerability', 'hack', 'malware',
                               'tool', 'scanner', 'api', 'cli']

                    if any(kw in title.lower() for kw in keywords):
                        ideas.append({
                            'title': f"RSS: {title[:60]}",
                            'description': entry.get('summary', '')[:200],
                            'source': 'rss_feed',
                            'url': entry.get('link', ''),
                            'feed': feed.feed.get('title', 'Unknown'),
                            'complexity': 'medium',
                            'priority': 'medium',
                            'discovered_at': datetime.now().isoformat()
                        })

            except Exception as e:
                logger.debug("RSS feed error %s: %s", feed_url, e)
                continue

        logger.info("RSS News: %d ideas found", len(ideas))
        return ideas


# ──────────────────────────────────────────────
# 통합 Discovery Manager
# ──────────────────────────────────────────────

class EnhancedDiscoveryManager:
    """향상된 Discovery 관리자 - 모든 소스 통합"""

    def __init__(self, config=None):
        self.config = config

        # 기존 소스
        from builder.discovery.github_trending_enhanced import GitHubTrendingEnhancedSource
        from builder.discovery.cve_database import CVEDatabaseSource
        from builder.discovery.security_news import SecurityNewsSource

        # 새로운 소스
        self.sources = [
            # 기존
            GitHubTrendingEnhancedSource(getattr(config, 'github', None) if config else None),
            CVEDatabaseSource(getattr(config, 'cve', None) if config else None),
            SecurityNewsSource(getattr(config, 'security_news', None) if config else None),

            # 새로운
            ProductHuntSource(getattr(config, 'product_hunt', None) if config else None),
            HackerNewsSource(getattr(config, 'hacker_news', None) if config else None),
            RedditSource(getattr(config, 'reddit', None) if config else None),
            KoreanSecurityNewsSource(getattr(config, 'korean_news', None) if config else None),
            TrendingRepositoriesSource(getattr(config, 'github_multi', None) if config else None),
        ]

    def discover_all(self, max_ideas: int = 50) -> List[Dict]:
        """모든 소스에서 아이디어 발굴"""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        all_ideas = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(source.discover): source.__class__.__name__
                for source in self.sources if source.enabled
            }

            for future in as_completed(futures, timeout=120):
                source_name = futures[future]
                try:
                    ideas = future.result(timeout=30)
                    all_ideas.extend(ideas)
                    logger.info("%s: %d ideas", source_name, len(ideas))
                except Exception as e:
                    logger.warning("%s failed: %s", source_name, e)

        # 중복 제거
        unique_ideas = self._remove_duplicates(all_ideas)

        # 점수 기반 정렬
        scored_ideas = self._score_ideas(unique_ideas)

        return scored_ideas[:max_ideas]

    def _remove_duplicates(self, ideas: List[Dict]) -> List[Dict]:
        """중복 아이디어 제거"""
        seen = set()
        unique = []

        for idea in ideas:
            # 제목 기반 중복 체크
            key = idea['title'].lower().strip()

            if key not in seen:
                seen.add(key)
                unique.append(idea)

        return unique

    def _score_ideas(self, ideas: List[Dict]) -> List[Dict]:
        """아이디어 점수화"""
        from builder.discovery.scorer import IdeaScorer

        scorer = IdeaScorer()

        for idea in ideas:
            idea['score'] = scorer.score(idea, ideas)

        return sorted(ideas, key=lambda x: x['score'], reverse=True)
