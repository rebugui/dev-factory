"""GitHub Trend Analyzer - 트렌드 분석 기반 아이디어 선정

GitHub Trending을 분석해서:
1. 인기 카테고리 파악
2. 뜨는 기술 스택 식별
3. 트렌드 기반 차별화된 아이디어 제안
"""

import logging
import json
import re
import urllib.request
from datetime import datetime
from typing import List, Dict, Tuple
from collections import Counter, defaultdict

logger = logging.getLogger('builder-agent.discovery.trend_analyzer')


class GitHubTrendAnalyzer:
    """GitHub Trending 트렌드 분석기"""

    # 분석할 언어들
    LANGUAGES = ['python', 'javascript', 'typescript', 'go', 'rust', 'kotlin', 'swift']
    
    # 분석할 기간
    PERIODS = ['daily', 'weekly', 'monthly']

    # 프로젝트 카테고리 키워드
    CATEGORIES = {
        'AI/ML': ['ai', 'machine-learning', 'deep-learning', 'neural', 'llm', 'gpt', 'chatgpt'],
        'DevTools': ['cli', 'tool', 'developer-tools', 'productivity', 'automation'],
        'Web': ['web', 'frontend', 'backend', 'api', 'framework', 'react', 'vue', 'next'],
        'Data': ['data', 'analytics', 'visualization', 'database', 'sql', 'etl'],
        'Security': ['security', 'vulnerability', 'encryption', 'auth', 'firewall'],
        'DevOps': ['docker', 'kubernetes', 'ci-cd', 'infrastructure', 'cloud', 'terraform'],
        'Mobile': ['mobile', 'android', 'ios', 'flutter', 'react-native'],
        'Blockchain': ['blockchain', 'crypto', 'web3', 'defi', 'nft'],
        'Gaming': ['game', 'gaming', 'unity', 'unreal', 'godot'],
        'IoT': ['iot', 'embedded', 'arduino', 'raspberry-pi', 'hardware'],
    }

    def __init__(self):
        self.trending_data = defaultdict(list)  # {language: [repos]}
        self.category_stats = Counter()  # {category: count}
        self.tech_stack_stats = Counter()  # {tech: count}
        self.keyword_stats = Counter()  # {keyword: count}

    def analyze(self) -> Dict:
        """전체 트렌드 분석 실행"""
        logger.info("=" * 70)
        logger.info("GitHub Trending 분석 시작")
        logger.info("=" * 70)

        # 1. 데이터 수집
        self._collect_trending_data()

        # 2. 카테고리 분석
        self._analyze_categories()

        # 3. 기술 스택 분석
        self._analyze_tech_stacks()

        # 4. 트렌드 요약
        trend_summary = self._generate_trend_summary()

        # 5. 아이디어 제안
        ideas = self._generate_trend_based_ideas(trend_summary)

        return {
            'summary': trend_summary,
            'ideas': ideas,
            'stats': {
                'total_repos': sum(len(repos) for repos in self.trending_data.values()),
                'categories': dict(self.category_stats.most_common(10)),
                'tech_stacks': dict(self.tech_stack_stats.most_common(10)),
                'keywords': dict(self.keyword_stats.most_common(20))
            }
        }

    def _collect_trending_data(self):
        """GitHub Trending 데이터 수집"""
        logger.info("1. 트렌딩 데이터 수집 중...")

        for lang in self.LANGUAGES[:5]:  # 상위 5개 언어만
            try:
                url = f"https://github.com/trending/{lang}?since=daily"
                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'Mozilla/5.0')

                with urllib.request.urlopen(req, timeout=15) as response:
                    html = response.read().decode('utf-8')

                # 레포 추출
                repo_pattern = r'<h2[^>]*>.*?<a[^>]*href="/([^"]+)"[^>]*>([^<]+)</a>'
                desc_pattern = r'<p[^>]*class="col-9[^"]*"[^>]*>([^<]+)</p>'
                
                repos = re.findall(repo_pattern, html, re.DOTALL)
                descs = re.findall(desc_pattern, html, re.DOTALL)

                for i, (repo_path, repo_name) in enumerate(repos[:10]):
                    description = descs[i].strip() if i < len(descs) else ''
                    
                    self.trending_data[lang].append({
                        'path': repo_path,
                        'name': repo_name.strip(),
                        'description': description,
                        'url': f"https://github.com/{repo_path}"
                    })

                logger.info(f"  {lang}: {len(repos[:10])}개 레포 수집")

            except Exception as e:
                logger.warning(f"  {lang} 수집 실패: {e}")

    def _analyze_categories(self):
        """카테고리 분석"""
        logger.info("2. 카테고리 분석 중...")

        for lang, repos in self.trending_data.items():
            for repo in repos:
                text = f"{repo['name']} {repo['description']}".lower()

                # 카테고리 매칭
                for category, keywords in self.CATEGORIES.items():
                    if any(kw in text for kw in keywords):
                        self.category_stats[category] += 1

    def _analyze_tech_stacks(self):
        """기술 스택 분석"""
        logger.info("3. 기술 스택 분석 중...")

        # 기술 스택 키워드
        tech_keywords = {
            'React': ['react', 'reactjs'],
            'Vue': ['vue', 'vuejs'],
            'Next.js': ['nextjs', 'next.js'],
            'TypeScript': ['typescript', 'ts'],
            'Python': ['python'],
            'Rust': ['rust', 'rustlang'],
            'Go': ['golang', 'go'],
            'Docker': ['docker', 'container'],
            'Kubernetes': ['kubernetes', 'k8s'],
            'AI/LLM': ['llm', 'gpt', 'openai', 'chatgpt', 'ai'],
            'API': ['api', 'rest', 'graphql'],
            'CLI': ['cli', 'command-line', 'terminal'],
        }

        for lang, repos in self.trending_data.items():
            for repo in repos:
                text = f"{repo['name']} {repo['description']}".lower()

                # 기술 스택 매칭
                for tech, keywords in tech_keywords.items():
                    if any(kw in text for kw in keywords):
                        self.tech_stack_stats[tech] += 1

                # 키워드 추출
                words = re.findall(r'\b[a-z]{3,}\b', text)
                for word in words:
                    self.keyword_stats[word] += 1

    def _generate_trend_summary(self) -> Dict:
        """트렌드 요약 생성"""
        logger.info("4. 트렌드 요약 생성 중...")

        # Top 카테고리
        top_categories = self.category_stats.most_common(5)

        # Top 기술 스택
        top_tech = self.tech_stack_stats.most_common(5)

        # Top 키워드 (불용어 제거)
        stopwords = {'the', 'for', 'and', 'with', 'from', 'this', 'that', 'your', 'you', 'are', 'has', 'have', 'been', 'will', 'can', 'all', 'more', 'some', 'into', 'than', 'them', 'they', 'their'}
        top_keywords = [
            (kw, count) for kw, count in self.keyword_stats.most_common(30)
            if kw not in stopwords and count > 1
        ][:10]

        return {
            'top_categories': top_categories,
            'top_tech_stacks': top_tech,
            'top_keywords': top_keywords,
            'insights': self._generate_insights(top_categories, top_tech, top_keywords)
        }

    def _generate_insights(self, categories, tech, keywords) -> List[str]:
        """인사이트 생성"""
        insights = []

        # 카테고리 기반 인사이트
        if categories:
            top_cat = categories[0][0]
            insights.append(f"🔥 가장 인기 있는 카테고리: {top_cat}")

        # 기술 스택 기반 인사이트
        if tech:
            top_techs = [t[0] for t in tech[:3]]
            insights.append(f"💡 뜨는 기술 스택: {', '.join(top_techs)}")

        # 키워드 기반 인사이트
        if keywords:
            top_kws = [k[0] for k in keywords[:5]]
            insights.append(f"📝 핫 키워드: {', '.join(top_kws)}")

        return insights

    def _generate_trend_based_ideas(self, summary: Dict) -> List[Dict]:
        """트렌드 기반 아이디어 생성"""
        logger.info("5. 트렌드 기반 아이디어 생성 중...")

        ideas = []

        # 1. Top 카테고리 기반
        for category, count in summary['top_categories'][:3]:
            ideas.append({
                'title': f"Trending {category} Tool",
                'description': f"{category} 분야의 트렌딩한 문제를 해결하는 도구",
                'source': 'github_trend_analysis',
                'category': category,
                'trend_score': count,
                'complexity': 'medium',
                'priority': 'high',
                'rationale': f"GitHub Trending에서 {category} 카테고리가 {count}회 등장"
            })

        # 2. 기술 스택 조합
        if len(summary['top_tech_stacks']) >= 2:
            tech1 = summary['top_tech_stacks'][0][0]
            tech2 = summary['top_tech_stacks'][1][0]
            
            ideas.append({
                'title': f"{tech1} + {tech2} Integration Tool",
                'description': f"{tech1}와 {tech2}를 결합한 생산성 도구",
                'source': 'github_trend_analysis',
                'category': 'DevTools',
                'trend_score': summary['top_tech_stacks'][0][1] + summary['top_tech_stacks'][1][1],
                'complexity': 'medium',
                'priority': 'high',
                'rationale': f"인기 기술 {tech1}과 {tech2}의 조합"
            })

        # 3. 키워드 기반
        for keyword, count in summary['top_keywords'][:5]:
            ideas.append({
                'title': f"{keyword.title()} Automation Tool",
                'description': f"{keyword} 관련 작업을 자동화하는 CLI 도구",
                'source': 'github_trend_analysis',
                'category': 'DevTools',
                'trend_score': count,
                'complexity': 'simple',
                'priority': 'medium',
                'rationale': f"'{keyword}' 키워드가 {count}회 등장"
            })

        # 점수 기반 정렬
        ideas.sort(key=lambda x: x['trend_score'], reverse=True)

        return ideas[:10]


# ──────────────────────────────────────────────
# 실행 함수
# ──────────────────────────────────────────────

def analyze_github_trends() -> Dict:
    """GitHub 트렌드 분석 실행"""
    analyzer = GitHubTrendAnalyzer()
    return analyzer.analyze()


def print_trend_report(analysis: Dict):
    """트렌드 리포트 출력"""
    print("=" * 70)
    print("GitHub Trending 분석 리포트")
    print("=" * 70)
    print()

    # 인사이트
    print("📊 인사이트:")
    for insight in analysis['summary']['insights']:
        print(f"  {insight}")
    print()

    # Top 카테고리
    print("🏆 Top 카테고리:")
    for i, (cat, count) in enumerate(analysis['summary']['top_categories'], 1):
        print(f"  {i}. {cat}: {count}개")
    print()

    # Top 기술 스택
    print("💻 Top 기술 스택:")
    for i, (tech, count) in enumerate(analysis['summary']['top_tech_stacks'], 1):
        print(f"  {i}. {tech}: {count}개")
    print()

    # Top 키워드
    print("🔑 Top 키워드:")
    for i, (kw, count) in enumerate(analysis['summary']['top_keywords'], 1):
        print(f"  {i}. {kw}: {count}회")
    print()

    # 추천 아이디어
    print("💡 추천 아이디어:")
    for i, idea in enumerate(analysis['ideas'][:5], 1):
        print(f"  {i}. {idea['title']}")
        print(f"     이유: {idea['rationale']}")
        print(f"     점수: {idea['trend_score']}")
        print()

    print("=" * 70)


if __name__ == "__main__":
    # 실행
    analysis = analyze_github_trends()
    print_trend_report(analysis)
