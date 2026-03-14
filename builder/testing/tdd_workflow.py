"""Test Runner Integration - TDD 워크플로우, 커버리지 보장

test-runner 스킬과 통합하여 자동화된 테스트 생성, TDD 워크플로우, 커버리지 보장
"""

import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger('builder-agent.testing_integration')


class TestRunnerIntegration:
    """test-runner 스킬을 활용한 자동화된 테스트"""

    # 프레임워크 선택 기준
    FRAMEWORK_MAP = {
        ('python',): 'pytest',
        ('typescript', 'javascript'): 'vitest',
        ('typescript', 'javascript', 'react'): 'vitest + @testing-library/react',
        ('swift',): 'XCTest',
    }

    def __init__(self, project_path: Path, tech_stack: List[str]):
        """초기화
        
        Args:
            project_path: 프로젝트 경로
            tech_stack: 기술 스택 리스트
        """
        self.project_path = project_path
        self.tech_stack = [ts.lower() for ts in tech_stack]
        self.framework = self._select_framework()
        self.min_coverage = 0.8  # 80% 커버리지 목표

    def _select_framework(self) -> str:
        """프로젝트에 맞는 테스트 프레임워크 선택"""
        for stack_tuple, framework in self.FRAMEWORK_MAP.items():
            if all(ts in self.tech_stack for ts in stack_tuple):
                return framework
        
        # 기본값
        if 'python' in self.tech_stack:
            return 'pytest'
        else:
            return 'vitest'

    # ──────────────────────────────────────────────
    # TDD 워크플로우
    # ──────────────────────────────────────────────

    def run_tdd_cycle(self, feature_description: str, implementation_code: str) -> Dict:
        """TDD 사이클 실행 (Red-Green-Refactor)
        
        Args:
            feature_description: 기능 설명
            implementation_code: 구현 코드
            
        Returns:
            TDD 사이클 결과
        """
        results = {
            'red': None,
            'green': None,
            'refactor': None,
            'success': False
        }

        # 1. Red: 실패하는 테스트 작성
        logger.info("TDD Phase 1: RED - Writing failing test")
        test_code = self._generate_test(feature_description)
        self._write_test(test_code)

        # 테스트 실행 (실패해야 함)
        red_result = self._run_tests()
        if red_result['success']:
            logger.warning("Test passed initially - test might be too simple")
            results['red'] = {'status': 'warning', 'message': 'Test passed (should fail)'}
        else:
            logger.info("✓ Test failed as expected (RED)")
            results['red'] = {'status': 'success', 'message': 'Test failed as expected'}

        # 2. Green: 최소 구현으로 테스트 통과
        logger.info("TDD Phase 2: GREEN - Writing minimal implementation")
        self._write_implementation(implementation_code)

        # 테스트 실행 (성공해야 함)
        green_result = self._run_tests()
        if green_result['success']:
            logger.info("✓ Test passed (GREEN)")
            results['green'] = {'status': 'success', 'message': 'Test passed'}
        else:
            logger.error("✗ Test still failing after implementation")
            results['green'] = {
                'status': 'failed',
                'message': 'Test still failing',
                'output': green_result['output']
            }
            return results

        # 3. Refactor: 코드 개선
        logger.info("TDD Phase 3: REFACTOR - Improving code quality")
        refactored_code = self._refactor_code(implementation_code)
        self._write_implementation(refactored_code)

        # 회귀 테스트 (여전히 통과해야 함)
        refactor_result = self._run_tests()
        if refactor_result['success']:
            logger.info("✓ Refactoring successful - tests still pass")
            results['refactor'] = {'status': 'success', 'message': 'Refactored'}
            results['success'] = True
        else:
            logger.warning("✗ Refactoring broke tests - reverting")
            self._write_implementation(implementation_code)
            results['refactor'] = {
                'status': 'warning',
                'message': 'Refactoring broke tests - reverted'
            }
            results['success'] = True  # 원래 코드로 되돌렸으므로 성공으로 간주

        return results

    # ──────────────────────────────────────────────
    # 테스트 생성
    # ──────────────────────────────────────────────

    def _generate_test(self, feature_description: str) -> str:
        """기능 설명에서 테스트 코드 생성"""
        if self.framework == 'pytest':
            return self._generate_pytest(feature_description)
        elif 'vitest' in self.framework:
            return self._generate_vitest(feature_description)
        else:
            raise ValueError(f"Unsupported framework: {self.framework}")

    def _generate_pytest(self, feature_description: str) -> str:
        """pytest 테스트 생성"""
        # 간단한 템플릿 기반 생성
        return f'''"""
Test: {feature_description}
"""

import pytest
from src.main import main  # TODO: adjust import


def test_basic_functionality():
    """Test basic functionality"""
    # Arrange
    # TODO: Set up test data
    
    # Act
    # result = main()
    
    # Assert
    # assert result is not None
    assert False  # Remove this and implement test


def test_edge_cases():
    """Test edge cases"""
    # Arrange
    # TODO: Set up edge case data
    
    # Act & Assert
    # TODO: Test edge cases
    pass


def test_error_handling():
    """Test error handling"""
    # Arrange
    # TODO: Set up invalid input
    
    # Act & Assert
    # with pytest.raises(ExpectedException):
    #     main(invalid_input)
    pass
'''

    def _generate_vitest(self, feature_description: str) -> str:
        """Vitest 테스트 생성"""
        return f'''/**
 * Test: {feature_description}
 */

import {{ describe, it, expect }} from 'vitest'
// import {{ main }} from '../src/main'  // TODO: adjust import

describe('{feature_description}', () => {{
  it('should handle basic functionality', () => {{
    // Arrange
    // TODO: Set up test data

    // Act
    // const result = main()

    // Assert
    // expect(result).toBeDefined()
    expect(true).toBe(false)  // Remove this and implement test
  }})

  it('should handle edge cases', () => {{
    // TODO: Test edge cases
  }})

  it('should handle errors gracefully', () => {{
    // TODO: Test error handling
  }})
}})
'''

    # ──────────────────────────────────────────────
    # 커버리지 관리
    # ──────────────────────────────────────────────

    def ensure_coverage(self) -> Dict:
        """테스트 커버리지 보장 (80% 이상)
        
        Returns:
            커버리지 결과
        """
        logger.info("Checking test coverage (target: %d%%)", int(self.min_coverage * 100))

        # 1. 커버리지 측정
        coverage_result = self._run_coverage()

        if coverage_result['success']:
            coverage_pct = coverage_result['coverage']
            
            if coverage_pct >= self.min_coverage:
                logger.info("✓ Coverage target met: %.1f%%", coverage_pct * 100)
                return {
                    'success': True,
                    'coverage': coverage_pct,
                    'message': f'Coverage {coverage_pct:.1%} meets target {self.min_coverage:.0%}'
                }
            else:
                logger.warning("Coverage below target: %.1f%% < %.1f%%", 
                             coverage_pct * 100, self.min_coverage * 100)

                # 2. 미커버 코드 분석
                uncovered = self._analyze_uncovered_code(coverage_result)

                # 3. 추가 테스트 생성
                additional_tests = self._generate_missing_tests(uncovered)
                self._write_test(additional_tests, append=True)

                # 4. 재측정
                logger.info("Retesting with additional tests...")
                retry_result = self._run_coverage()

                if retry_result['success'] and retry_result['coverage'] >= self.min_coverage:
                    logger.info("✓ Coverage improved to %.1f%%", retry_result['coverage'] * 100)
                    return {
                        'success': True,
                        'coverage': retry_result['coverage'],
                        'message': 'Coverage improved with additional tests'
                    }

                return {
                    'success': False,
                    'coverage': retry_result.get('coverage', 0),
                    'message': 'Could not reach coverage target'
                }

        return {
            'success': False,
            'coverage': 0,
            'message': coverage_result.get('error', 'Coverage measurement failed')
        }

    def _run_coverage(self) -> Dict:
        """커버리지 측정 실행"""
        try:
            if self.framework == 'pytest':
                cmd = [
                    'python3', '-m', 'pytest',
                    '--cov=src',
                    '--cov-report=json',
                    '--cov-report=term',
                    f'--cov-fail-under={int(self.min_coverage * 100)}',
                    'tests/'
                ]
            elif 'vitest' in self.framework:
                cmd = [
                    'npx', 'vitest', 'run',
                    '--coverage'
                ]
            else:
                return {'success': False, 'error': f'Unsupported framework: {self.framework}'}

            result = subprocess.run(
                cmd,
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                timeout=60
            )

            # 커버리지 데이터 파싱
            coverage_pct = self._parse_coverage(result.stdout, result.stderr)

            return {
                'success': coverage_pct >= self.min_coverage,
                'coverage': coverage_pct,
                'output': result.stdout + result.stderr
            }

        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Coverage measurement timeout'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _parse_coverage(self, stdout: str, stderr: str) -> float:
        """커버리지 결과 파싱"""
        output = stdout + stderr

        # pytest-cov 포맷
        import re
        match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', output)
        if match:
            return int(match.group(1)) / 100.0

        # vitest coverage 포맷
        match = re.search(r'All files\s+\|\s+[\d.]+\s+\|\s+[\d.]+\s+\|\s+[\d.]+\s+\|\s+([\d.]+)', output)
        if match:
            return float(match.group(1)) / 100.0

        # JSON 리포트에서 읽기
        coverage_file = self.project_path / 'coverage' / 'coverage-summary.json'
        if coverage_file.exists():
            try:
                data = json.loads(coverage_file.read_text())
                total = data.get('total', {})
                lines = total.get('lines', {})
                return lines.get('pct', 0) / 100.0
            except Exception:
                pass

        return 0.0

    def _analyze_uncovered_code(self, coverage_result: Dict) -> List[Dict]:
        """미커버 코드 분석"""
        # 실제로는 coverage 리포트에서 미커버 라인 추출
        # 간단히 템플릿 반환
        return [
            {
                'file': 'src/main.py',
                'lines': '10-20',
                'function': 'process_data',
                'reason': 'Branch not covered'
            }
        ]

    def _generate_missing_tests(self, uncovered: List[Dict]) -> str:
        """미커버 코드에 대한 테스트 생성"""
        tests = []

        for item in uncovered:
            test = f'''
def test_{item['function']}_coverage():
    """Test coverage for {item['function']}"""
    # TODO: Test uncovered branch
    # File: {item['file']}, Lines: {item['lines']}
    # Reason: {item['reason']}
    pass
'''
            tests.append(test)

        return '\n'.join(tests)

    # ──────────────────────────────────────────────
    # 유틸리티
    # ──────────────────────────────────────────────

    def _run_tests(self) -> Dict:
        """테스트 실행"""
        try:
            if self.framework == 'pytest':
                cmd = ['python3', '-m', 'pytest', 'tests/', '-v']
            elif 'vitest' in self.framework:
                cmd = ['npx', 'vitest', 'run']
            else:
                return {'success': False, 'error': f'Unsupported framework: {self.framework}'}

            result = subprocess.run(
                cmd,
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                timeout=60
            )

            return {
                'success': result.returncode == 0,
                'output': result.stdout + result.stderr
            }

        except subprocess.TimeoutExpired:
            return {'success': False, 'output': 'Test timeout'}
        except Exception as e:
            return {'success': False, 'output': str(e)}

    def _write_test(self, test_code: str, append: bool = False):
        """테스트 파일 작성"""
        tests_dir = self.project_path / 'tests'
        tests_dir.mkdir(exist_ok=True)

        if self.framework == 'pytest':
            test_file = tests_dir / 'test_main.py'
        else:
            test_file = tests_dir / 'main.test.ts'

        mode = 'a' if append else 'w'
        with open(test_file, mode) as f:
            f.write(test_code)

        logger.debug("Test written to %s", test_file)

    def _write_implementation(self, code: str):
        """구현 파일 작성"""
        src_dir = self.project_path / 'src'
        src_dir.mkdir(exist_ok=True)

        impl_file = src_dir / 'main.py' if 'python' in self.tech_stack else src_dir / 'main.ts'
        impl_file.write_text(code)

        logger.debug("Implementation written to %s", impl_file)

    def _refactor_code(self, code: str) -> str:
        """코드 리팩토링 (간단한 개선만)"""
        # 실제로는 더 정교한 리팩토링 로직 필요
        # 여기서는 기본적인 정리만 수행
        
        lines = code.split('\n')
        refactored = []
        
        for line in lines:
            # 불필요한 공백 제거
            stripped = line.rstrip()
            if stripped:
                refactored.append(stripped)
            else:
                refactored.append('')

        return '\n'.join(refactored)


# ──────────────────────────────────────────────
# 편의 함수
# ──────────────────────────────────────────────

def run_tdd_for_feature(project_path: Path, tech_stack: List[str],
                        feature: str, implementation: str) -> Dict:
    """기능에 대한 TDD 사이클 실행 (편의 함수)"""
    runner = TestRunnerIntegration(project_path, tech_stack)
    return runner.run_tdd_cycle(feature, implementation)


def ensure_test_coverage(project_path: Path, tech_stack: List[str],
                         min_coverage: float = 0.8) -> Dict:
    """테스트 커버리지 보장 (편의 함수)"""
    runner = TestRunnerIntegration(project_path, tech_stack)
    runner.min_coverage = min_coverage
    return runner.ensure_coverage()
