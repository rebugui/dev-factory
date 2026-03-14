"""Frontend Design Integration - 웹 프로젝트 UI 자동화

frontend-design 스킬과 통합하여 웹 프로젝트에 고품질 UI 자동 생성
"""

import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger('builder-agent.frontend_integration')


class FrontendDesignIntegration:
    """frontend-design 스킬을 활용한 UI 자동화"""

    # 프로젝트 타입별 디자인 템플릿
    DESIGN_TEMPLATES = {
        'security-dashboard': {
            'aesthetic': 'brutalist/raw',
            'colors': {'primary': '#1a1a1a', 'accent': '#ff3333', 'background': '#0a0a0a'},
            'typography': {'display': 'Space Mono', 'body': 'IBM Plex Sans'},
            'features': ['real-time updates', 'charts', 'tables', 'alerts']
        },
        'vulnerability-scanner': {
            'aesthetic': 'industrial/utilitarian',
            'colors': {'primary': '#2d2d2d', 'accent': '#00ff00', 'background': '#1a1a1a'},
            'typography': {'display': 'JetBrains Mono', 'body': 'Source Sans Pro'},
            'features': ['form inputs', 'results display', 'export buttons', 'progress bars']
        },
        'monitoring-tool': {
            'aesthetic': 'minimal/refined',
            'colors': {'primary': '#ffffff', 'accent': '#0066ff', 'background': '#f5f5f5'},
            'typography': {'display': 'Inter', 'body': 'Inter'},
            'features': ['metrics cards', 'charts', 'logs viewer', 'settings panel']
        },
        'api-documentation': {
            'aesthetic': 'editorial/magazine',
            'colors': {'primary': '#333333', 'accent': '#6366f1', 'background': '#ffffff'},
            'typography': {'display': 'Playfair Display', 'body': 'Lora'},
            'features': ['navigation sidebar', 'code blocks', 'interactive examples', 'search']
        }
    }

    def __init__(self, project_path: Path, project_type: str):
        """초기화
        
        Args:
            project_path: 프로젝트 경로
            project_type: 프로젝트 타입 (security-dashboard, vulnerability-scanner, etc.)
        """
        self.project_path = project_path
        self.project_type = project_type
        self.design_template = self.DESIGN_TEMPLATES.get(
            project_type,
            self.DESIGN_TEMPLATES['security-dashboard']
        )

    def generate_ui(self, feature_description: str, tech_stack: List[str]) -> Dict:
        """UI 자동 생성
        
        Args:
            feature_description: 기능 설명
            tech_stack: 기술 스택 (예: ['react', 'typescript', 'tailwind'])
            
        Returns:
            UI 생성 결과 (files, instructions 등)
        """
        logger.info("Generating UI for %s project", self.project_type)

        # 1. 디자인 방향 결정
        design_brief = self._create_design_brief(feature_description)

        # 2. UI 코드 생성 (frontend-design 스킬 호출)
        ui_code = self._call_frontend_design(design_brief, tech_stack)

        if not ui_code:
            logger.warning("Failed to call frontend-design, using template fallback")
            ui_code = self._generate_template_ui(feature_description, tech_stack)

        # 3. 파일 저장
        files_created = self._save_ui_files(ui_code, tech_stack)

        # 4. 스타일 가이드 생성
        style_guide = self._create_style_guide()

        return {
            'success': True,
            'files': files_created,
            'style_guide': style_guide,
            'design_brief': design_brief
        }

    def _create_design_brief(self, feature_description: str) -> Dict:
        """디자인 브리프 생성"""
        template = self.design_template

        return {
            'project_type': self.project_type,
            'feature': feature_description,
            'aesthetic_direction': template['aesthetic'],
            'color_palette': template['colors'],
            'typography': template['typography'],
            'key_features': template['features'],
            'mood_keywords': self._extract_mood_keywords(template['aesthetic'])
        }

    def _extract_mood_keywords(self, aesthetic: str) -> List[str]:
        """미학적 방향에서 무드 키워드 추출"""
        mood_map = {
            'brutalist': ['raw', 'bold', 'industrial', 'unpolished'],
            'minimal': ['clean', 'simple', 'elegant', 'refined'],
            'industrial': ['functional', 'stark', 'technical', 'utilitarian'],
            'editorial': ['sophisticated', 'structured', 'professional', 'polished']
        }

        for key, keywords in mood_map.items():
            if key in aesthetic.lower():
                return keywords

        return ['modern', 'professional', 'clean']

    def _call_frontend_design(self, design_brief: Dict, tech_stack: List[str]) -> Optional[Dict]:
        """frontend-design 스킬 호출
        
        실제로는 sessions_spawn으로 코딩 에이전트를 호출해야 하지만,
        여기서는 직접 구현으로 대체
        """
        # TODO: sessions_spawn으로 frontend-design 에이전트 호출
        # 현재는 템플릿 기반 생성으로 대체
        
        return None

    def _generate_template_ui(self, feature_description: str, tech_stack: List[str]) -> Dict:
        """템플릿 기반 UI 생성 (fallback)"""
        template = self.design_template
        colors = template['colors']
        fonts = template['typography']

        # React + TypeScript + Tailwind 조합
        if 'react' in [ts.lower() for ts in tech_stack]:
            return self._generate_react_ui(feature_description, colors, fonts)
        # Vanilla HTML/CSS/JS
        else:
            return self._generate_vanilla_ui(feature_description, colors, fonts)

    def _generate_react_ui(self, feature: str, colors: Dict, fonts: Dict) -> Dict:
        """React UI 컴포넌트 생성"""
        component_name = self._to_component_name(feature)

        # 메인 컴포넌트
        main_component = f'''import React from 'react';
import {{ motion }} from 'framer-motion';

/**
 * {feature}
 * Design: {self.design_template['aesthetic']}
 */

export const {component_name}: React.FC = () => {{
  return (
    <div className="min-h-screen" style={{{{ 
      backgroundColor: '{colors['background']}',
      color: '{colors['primary']}',
      fontFamily: '{fonts['body']}, sans-serif'
    }}}}>
      <motion.div
        initial={{{{ opacity: 0, y: 20 }}}}
        animate={{{{ opacity: 1, y: 0 }}}}
        transition={{{{ duration: 0.5 }}}}
        className="container mx-auto px-6 py-12"
      >
        <header className="mb-12">
          <h1 
            className="text-5xl font-bold mb-4"
            style={{{{ 
              fontFamily: '{fonts['display']}, monospace',
              color: '{colors['accent']}'
            }}}}
          >
            {feature}
          </h1>
          <p className="text-xl opacity-80">
            Professional security tool with {self.design_template['aesthetic']} design
          </p>
        </header>

        <main className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {{/* Main content area */}}
          <div className="bg-opacity-10 backdrop-blur-sm rounded-lg p-8 border border-opacity-20"
               style={{{{ borderColor: '{colors['accent']}' }}}}>
            <h2 className="text-2xl font-bold mb-6">Dashboard</h2>
            <div className="space-y-4">
              <div className="p-4 rounded" style={{{{ backgroundColor: '{colors['primary']}20' }}}}>
                <p className="text-sm opacity-60">Status</p>
                <p className="text-2xl font-bold" style={{{{ color: '{colors['accent']}' }}}}>
                  Active
                </p>
              </div>
            </div>
          </div>

          {{/* Sidebar */}}
          <div className="space-y-6">
            <div className="p-6 rounded-lg" style={{{{ 
              backgroundColor: '{colors['primary']}10',
              borderLeft: `4px solid {colors['accent']}`
            }}}}>
              <h3 className="font-bold mb-2">Quick Actions</h3>
              <div className="space-y-2">
                <button 
                  className="w-full text-left px-4 py-2 rounded hover:bg-opacity-20 transition-colors"
                  style={{{{ backgroundColor: '{colors['accent']}20' }}}}
                >
                  Scan Now
                </button>
                <button 
                  className="w-full text-left px-4 py-2 rounded hover:bg-opacity-20 transition-colors"
                  style={{{{ backgroundColor: '{colors['accent']}20' }}}}
                >
                  Export Results
                </button>
              </div>
            </div>
          </div>
        </main>
      </motion.div>
    </div>
  );
}};
'''

        # 스타일 파일
        styles = f'''/* Global styles for {self.project_type} */

@import url('https://fonts.googleapis.com/css2?family={fonts['display'].replace(' ', '+')}&family={fonts['body'].replace(' ', '+')}&display=swap');

:root {{
  --color-primary: {colors['primary']};
  --color-accent: {colors['accent']};
  --color-background: {colors['background']};
  --font-display: '{fonts['display']}', monospace;
  --font-body: '{fonts['body']}', sans-serif;
}}

body {{
  font-family: var(--font-body);
  background-color: var(--color-background);
  color: var(--color-primary);
}}

h1, h2, h3, h4, h5, h6 {{
  font-family: var(--font-display);
}}
'''

        return {
            'components': {
                f'{component_name}.tsx': main_component
            },
            'styles': {
                'globals.css': styles
            }
        }

    def _generate_vanilla_ui(self, feature: str, colors: Dict, fonts: Dict) -> Dict:
        """Vanilla HTML/CSS/JS UI 생성"""
        component_name = self._to_component_name(feature)

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{feature}</title>
  <link rel="stylesheet" href="styles.css">
  <link href="https://fonts.googleapis.com/css2?family={fonts['display'].replace(' ', '+')}&family={fonts['body'].replace(' ', '+')}&display=swap" rel="stylesheet">
</head>
<body>
  <div class="container">
    <header class="header">
      <h1 class="title">{feature}</h1>
      <p class="subtitle">Professional security tool with {self.design_template['aesthetic']} design</p>
    </header>

    <main class="main-content">
      <section class="dashboard">
        <h2>Dashboard</h2>
        <div class="status-card">
          <p class="label">Status</p>
          <p class="value">Active</p>
        </div>
      </section>

      <aside class="sidebar">
        <div class="action-panel">
          <h3>Quick Actions</h3>
          <button class="action-btn">Scan Now</button>
          <button class="action-btn">Export Results</button>
        </div>
      </aside>
    </main>
  </div>

  <script src="main.js"></script>
</body>
</html>
'''

        css = f'''/* Styles for {self.project_type} */

:root {{
  --color-primary: {colors['primary']};
  --color-accent: {colors['accent']};
  --color-background: {colors['background']};
  --font-display: '{fonts['display']}', monospace;
  --font-body: '{fonts['body']}', sans-serif;
}}

* {{
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}}

body {{
  font-family: var(--font-body);
  background-color: var(--color-background);
  color: var(--color-primary);
  min-height: 100vh;
}}

.container {{
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}}

.header {{
  margin-bottom: 3rem;
  animation: fadeIn 0.5s ease-out;
}}

.title {{
  font-family: var(--font-display);
  font-size: 3rem;
  font-weight: bold;
  color: var(--color-accent);
  margin-bottom: 0.5rem;
}}

.subtitle {{
  font-size: 1.25rem;
  opacity: 0.8;
}}

.main-content {{
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 2rem;
}}

.dashboard {{
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border-radius: 0.5rem;
  padding: 2rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
}}

.status-card {{
  background: rgba(0, 0, 0, 0.2);
  padding: 1rem;
  border-radius: 0.25rem;
  margin-top: 1rem;
}}

.label {{
  font-size: 0.875rem;
  opacity: 0.6;
}}

.value {{
  font-size: 2rem;
  font-weight: bold;
  color: var(--color-accent);
}}

.sidebar {{
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}}

.action-panel {{
  background: rgba(255, 255, 255, 0.05);
  padding: 1.5rem;
  border-radius: 0.5rem;
  border-left: 4px solid var(--color-accent);
}}

.action-panel h3 {{
  margin-bottom: 1rem;
}}

.action-btn {{
  width: 100%;
  text-align: left;
  padding: 0.75rem 1rem;
  margin-bottom: 0.5rem;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 0.25rem;
  color: inherit;
  cursor: pointer;
  transition: background 0.2s;
}}

.action-btn:hover {{
  background: rgba(255, 255, 255, 0.2);
}}

@keyframes fadeIn {{
  from {{
    opacity: 0;
    transform: translateY(20px);
  }}
  to {{
    opacity: 1;
    transform: translateY(0);
  }}
}}
'''

        js = f'''// Main JavaScript for {self.project_type}

document.addEventListener('DOMContentLoaded', () => {{
  console.log('{feature} loaded');

  // Action button handlers
  document.querySelectorAll('.action-btn').forEach(btn => {{
    btn.addEventListener('click', (e) => {{
      const action = e.target.textContent.trim();
      console.log('Action:', action);
      // TODO: Implement action handlers
    }});
  }});
}});
'''

        return {
            'html': {'index.html': html},
            'css': {'styles.css': css},
            'js': {'main.js': js}
        }

    def _save_ui_files(self, ui_code: Dict, tech_stack: List[str]) -> List[str]:
        """UI 파일 저장"""
        files_created = []

        # React 프로젝트
        if 'react' in [ts.lower() for ts in tech_stack]:
            # 컴포넌트 저장
            components_dir = self.project_path / 'src' / 'components'
            components_dir.mkdir(parents=True, exist_ok=True)

            for filename, content in ui_code.get('components', {}).items():
                file_path = components_dir / filename
                file_path.write_text(content)
                files_created.append(str(file_path))

            # 스타일 저장
            styles_dir = self.project_path / 'src' / 'styles'
            styles_dir.mkdir(parents=True, exist_ok=True)

            for filename, content in ui_code.get('styles', {}).items():
                file_path = styles_dir / filename
                file_path.write_text(content)
                files_created.append(str(file_path))

        # Vanilla 프로젝트
        else:
            # HTML 저장
            for filename, content in ui_code.get('html', {}).items():
                file_path = self.project_path / filename
                file_path.write_text(content)
                files_created.append(str(file_path))

            # CSS 저장
            for filename, content in ui_code.get('css', {}).items():
                file_path = self.project_path / filename
                file_path.write_text(content)
                files_created.append(str(file_path))

            # JS 저장
            for filename, content in ui_code.get('js', {}).items():
                file_path = self.project_path / filename
                file_path.write_text(content)
                files_created.append(str(file_path))

        logger.info("Created %d UI files", len(files_created))
        return files_created

    def _create_style_guide(self) -> str:
        """스타일 가이드 문서 생성"""
        template = self.design_template

        guide = f'''# Style Guide - {self.project_type}

## Design Direction

**Aesthetic**: {template['aesthetic']}

## Colors

- **Primary**: {template['colors']['primary']}
- **Accent**: {template['colors']['accent']}
- **Background**: {template['colors']['background']}

## Typography

- **Display Font**: {template['typography']['display']}
- **Body Font**: {template['typography']['body']}

## Key Features

{chr(10).join(f'- {f}' for f in template['features'])}

## Design Principles

1. **Bold Typography**: Use display font for headlines
2. **High Contrast**: Accent color against dark background
3. **Functional Layout**: Clear visual hierarchy
4. **Micro-interactions**: Subtle animations for feedback

## Usage Guidelines

### Headlines
```css
font-family: '{template['typography']['display']}', monospace;
color: {template['colors']['accent']};
```

### Body Text
```css
font-family: '{template['typography']['body']}', sans-serif;
color: {template['colors']['primary']};
```

### Buttons
```css
background-color: {template['colors']['accent']}20;
color: {template['colors']['primary']};
```

---
Generated by Builder Agent Frontend Integration
'''

        guide_path = self.project_path / 'STYLE_GUIDE.md'
        guide_path.write_text(guide)

        return str(guide_path)

    def _to_component_name(self, text: str) -> str:
        """텍스트를 컴포넌트 이름으로 변환"""
        # "vulnerability scanner" → "VulnerabilityScanner"
        words = text.replace('-', ' ').replace('_', ' ').split()
        return ''.join(word.capitalize() for word in words)


# ──────────────────────────────────────────────
# 편의 함수
# ──────────────────────────────────────────────

def generate_ui_for_project(project_path: Path, project_type: str,
                           feature: str, tech_stack: List[str]) -> Dict:
    """프로젝트 UI 생성 (편의 함수)"""
    integration = FrontendDesignIntegration(project_path, project_type)
    return integration.generate_ui(feature, tech_stack)


def detect_project_type(description: str) -> str:
    """프로젝트 설명에서 타입 감지"""
    desc_lower = description.lower()

    if 'dashboard' in desc_lower or 'monitor' in desc_lower:
        return 'security-dashboard'
    elif 'scanner' in desc_lower or 'vulnerability' in desc_lower:
        return 'vulnerability-scanner'
    elif 'monitoring' in desc_lower or 'metrics' in desc_lower:
        return 'monitoring-tool'
    elif 'api' in desc_lower or 'documentation' in desc_lower:
        return 'api-documentation'
    else:
        return 'security-dashboard'  # 기본값
