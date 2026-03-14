"""GitHub Integration - PR 자동화, CI/CD 연동

github 스킬과 통합하여 자동화된 PR 생성, CI 모니터링, 실패 시 자동 수정
"""

import subprocess
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger('builder-agent.github_integration')


class GitHubIntegration:
    """github 스킬을 활용한 자동화"""

    def __init__(self, repo: str = None):
        """초기화
        
        Args:
            repo: 저장소 (owner/repo 형식). None이면 현재 디렉토리에서 감지
        """
        self.repo = repo or self._detect_repo()
        self.gh_available = self._check_gh_cli()

    def _detect_repo(self) -> Optional[str]:
        """현재 디렉토리에서 저장소 감지"""
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                # https://github.com/owner/repo.git → owner/repo
                url = result.stdout.strip()
                if 'github.com' in url:
                    parts = url.split('github.com/')[-1].replace('.git', '')
                    return parts
        except Exception:
            pass
        return None

    def _check_gh_cli(self) -> bool:
        """gh CLI 사용 가능 여부 확인"""
        try:
            result = subprocess.run(
                ['gh', '--version'],
                capture_output=True, timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    # ──────────────────────────────────────────────
    # PR 자동화
    # ──────────────────────────────────────────────

    def create_pr(self, project_path: Path, title: str, body: str,
                  labels: List[str] = None, draft: bool = False) -> Dict:
        """PR 자동 생성
        
        Args:
            project_path: 프로젝트 경로
            title: PR 제목
            body: PR 본문
            labels: 라벨 리스트
            draft: draft PR 여부
            
        Returns:
            PR 생성 결과 (url, number 등)
        """
        if not self.gh_available:
            logger.warning("gh CLI not available")
            return {'success': False, 'error': 'gh CLI not available'}

        try:
            # 1. 브랜치 생성
            branch_name = f"feature/{title.lower().replace(' ', '-')[:50]}"
            
            subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                cwd=str(project_path),
                check=True,
                capture_output=True
            )

            # 2. 변경사항 커밋
            subprocess.run(
                ['git', 'add', '.'],
                cwd=str(project_path),
                check=True,
                capture_output=True
            )

            subprocess.run(
                ['git', 'commit', '-m', f'🤖 Auto-generated: {title}'],
                cwd=str(project_path),
                check=True,
                capture_output=True
            )

            # 3. 푸시
            subprocess.run(
                ['git', 'push', '-u', 'origin', branch_name],
                cwd=str(project_path),
                check=True,
                capture_output=True
            )

            # 4. PR 생성
            cmd = [
                'gh', 'pr', 'create',
                '--title', title,
                '--body', body
            ]

            if self.repo:
                cmd.extend(['--repo', self.repo])

            if draft:
                cmd.append('--draft')

            if labels:
                cmd.extend(['--label', ','.join(labels)])

            result = subprocess.run(
                cmd,
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                logger.error("PR creation failed: %s", result.stderr)
                return {
                    'success': False,
                    'error': result.stderr
                }

            # PR URL에서 번호 추출
            pr_url = result.stdout.strip()
            pr_number = int(pr_url.split('/')[-1])

            logger.info("PR created: %s", pr_url)

            return {
                'success': True,
                'url': pr_url,
                'number': pr_number,
                'branch': branch_name
            }

        except subprocess.CalledProcessError as e:
            logger.error("Git command failed: %s", e.stderr)
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error("PR creation error: %s", e)
            return {
                'success': False,
                'error': str(e)
            }

    # ──────────────────────────────────────────────
    # CI/CD 모니터링
    # ──────────────────────────────────────────────

    def monitor_ci(self, pr_number: int, timeout: int = 600) -> Dict:
        """CI 상태 모니터링
        
        Args:
            pr_number: PR 번호
            timeout: 타임아웃 (초)
            
        Returns:
            CI 결과 (status, checks 등)
        """
        if not self.gh_available:
            return {'success': False, 'error': 'gh CLI not available'}

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # PR 체크 상태 확인
                cmd = ['gh', 'pr', 'checks', str(pr_number)]
                if self.repo:
                    cmd.extend(['--repo', self.repo])

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0:
                    # 모든 체크 통과
                    logger.info("CI passed for PR #%d", pr_number)
                    return {
                        'success': True,
                        'status': 'passed',
                        'output': result.stdout
                    }

                # 진행 중인지 실패인지 확인
                output = result.stdout.lower()
                if 'fail' in output or 'error' in output:
                    logger.warning("CI failed for PR #%d", pr_number)
                    return {
                        'success': False,
                        'status': 'failed',
                        'output': result.stdout
                    }

                # 아직 진행 중
                logger.debug("CI in progress for PR #%d", pr_number)
                time.sleep(30)

            except subprocess.TimeoutExpired:
                logger.warning("CI check timeout")
            except Exception as e:
                logger.warning("CI check error: %s", e)
                time.sleep(10)

        # 타임아웃
        logger.error("CI monitoring timeout for PR #%d", pr_number)
        return {
            'success': False,
            'status': 'timeout',
            'error': f'CI did not complete within {timeout}s'
        }

    def get_failed_workflow_logs(self, pr_number: int) -> Optional[str]:
        """실패한 워크플로우 로그 가져오기
        
        Args:
            pr_number: PR 번호
            
        Returns:
            실패 로그 (없으면 None)
        """
        if not self.gh_available:
            return None

        try:
            # 실패한 워크플로우 조회
            cmd = ['gh', 'run', 'list', '--branch', f'feature/pr-{pr_number}']
            if self.repo:
                cmd.extend(['--repo', self.repo])
            cmd.extend(['--status', 'failure', '--limit', '1', '--json', 'id'])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return None

            runs = json.loads(result.stdout)
            if not runs:
                return None

            run_id = runs[0]['id']

            # 실패한 스텝 로그 가져오기
            cmd = ['gh', 'run', 'view', str(run_id)]
            if self.repo:
                cmd.extend(['--repo', self.repo])
            cmd.append('--log-failed')

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return result.stdout

        except Exception as e:
            logger.warning("Failed to get workflow logs: %s", e)

        return None

    # ──────────────────────────────────────────────
    # 이슈 기반 개발
    # ──────────────────────────────────────────────

    def get_good_first_issues(self, max_issues: int = 5) -> List[Dict]:
        """good first issue, help wanted 라벨 이슈 가져오기
        
        Args:
            max_issues: 최대 이슈 수
            
        Returns:
            이슈 리스트
        """
        if not self.gh_available or not self.repo:
            return []

        try:
            # good first issue + help wanted 이슈 검색
            result = subprocess.run([
                'gh', 'issue', 'list',
                '--repo', self.repo,
                '--label', 'good first issue,help wanted',
                '--limit', str(max_issues),
                '--json', 'number,title,body,labels,state',
                '--state', 'open'
            ], capture_output=True, text=True, timeout=15)

            if result.returncode != 0:
                logger.warning("Issue fetch failed: %s", result.stderr)
                return []

            issues = json.loads(result.stdout)
            
            return [
                {
                    'number': issue['number'],
                    'title': issue['title'],
                    'body': issue.get('body', ''),
                    'labels': [label['name'] for label in issue.get('labels', [])],
                    'url': f"https://github.com/{self.repo}/issues/{issue['number']}"
                }
                for issue in issues
            ]

        except Exception as e:
            logger.warning("Issue fetch error: %s", e)
            return []

    # ──────────────────────────────────────────────
    # 자동 수정
    # ──────────────────────────────────────────────

    def auto_fix_ci_failure(self, pr_number: int, project_path: Path) -> Dict:
        """CI 실패 시 자동 수정
        
        Args:
            pr_number: PR 번호
            project_path: 프로젝트 경로
            
        Returns:
            수정 결과
        """
        # 1. 실패 로그 가져오기
        logs = self.get_failed_workflow_logs(pr_number)
        if not logs:
            return {
                'success': False,
                'error': 'Could not get failure logs'
            }

        # 2. 에러 분석 (ErrorAnalyzer 사용)
        from builder.correction.analyzer import ErrorAnalyzer
        analyzer = ErrorAnalyzer()
        error = analyzer.analyze(logs)

        if not error:
            return {
                'success': False,
                'error': 'Could not analyze error'
            }

        logger.info("Analyzed error: %s", error.type)

        # 3. 코드 수정 (CodeFixer 사용)
        from builder.correction.fixer import CodeFixer
        fixer = CodeFixer()
        fixed = fixer.fix(error, project_path, 'medium')

        if not fixed:
            return {
                'success': False,
                'error': 'Could not fix error'
            }

        # 4. 변경사항 커밋 & 푸시
        try:
            subprocess.run(
                ['git', 'add', '.'],
                cwd=str(project_path),
                check=True,
                capture_output=True
            )

            subprocess.run(
                ['git', 'commit', '-m', f'🔧 Fix CI failure: {error.type}'],
                cwd=str(project_path),
                check=True,
                capture_output=True
            )

            subprocess.run(
                ['git', 'push'],
                cwd=str(project_path),
                check=True,
                capture_output=True
            )

            logger.info("Auto-fixed CI failure for PR #%d", pr_number)

            return {
                'success': True,
                'error_type': error.type,
                'fix_applied': True
            }

        except Exception as e:
            logger.error("Auto-fix commit failed: %s", e)
            return {
                'success': False,
                'error': str(e)
            }

    # ──────────────────────────────────────────────
    # 리포트
    # ──────────────────────────────────────────────

    def get_pr_status(self, pr_number: int) -> Dict:
        """PR 상태 조회"""
        if not self.gh_available:
            return {'error': 'gh CLI not available'}

        try:
            cmd = ['gh', 'pr', 'view', str(pr_number), '--json']
            if self.repo:
                cmd.extend(['--repo', self.repo])
            cmd.extend(['title,state,mergeable,statusCheckRollup'])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {'error': result.stderr}

        except Exception as e:
            return {'error': str(e)}


# ──────────────────────────────────────────────
# 편의 함수
# ──────────────────────────────────────────────

def create_pr_for_project(project_path: Path, title: str, description: str) -> Dict:
    """프로젝트 PR 생성 (편의 함수)"""
    github = GitHubIntegration()
    return github.create_pr(
        project_path=project_path,
        title=title,
        body=description,
        labels=['auto-generated', 'builder-agent']
    )


def monitor_and_fix(pr_number: int, project_path: Path, max_retries: int = 3) -> Dict:
    """CI 모니터링 및 실패 시 자동 수정
    
    Args:
        pr_number: PR 번호
        project_path: 프로젝트 경로
        max_retries: 최대 재시도 횟수
        
    Returns:
        최종 결과
    """
    github = GitHubIntegration()

    for attempt in range(max_retries):
        logger.info("Monitoring PR #%d (attempt %d/%d)", pr_number, attempt + 1, max_retries)

        # CI 모니터링
        ci_result = github.monitor_ci(pr_number)

        if ci_result['success']:
            return {
                'success': True,
                'attempts': attempt + 1,
                'status': 'passed'
            }

        # 실패 시 자동 수정
        if ci_result['status'] == 'failed':
            fix_result = github.auto_fix_ci_failure(pr_number, project_path)

            if not fix_result['success']:
                logger.warning("Auto-fix failed on attempt %d", attempt + 1)
                continue

            # 수정 후 재모니터링
            time.sleep(10)
        else:
            # 타임아웃이나 기타 오류
            logger.warning("CI monitoring failed: %s", ci_result.get('error'))
            break

    return {
        'success': False,
        'attempts': attempt + 1,
        'status': 'failed_after_retries'
    }
