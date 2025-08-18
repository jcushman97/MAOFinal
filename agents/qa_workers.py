"""
QA Worker specialists for atomic testing tasks in the MAOS system.
Handles different types of testing with timeout management and granular validation.
"""

from typing import Dict, Any, Optional, List
from agents.worker_agent import WorkerAgent, WorkerSpecialty
from core.state import Task

class HTMLValidationWorker(WorkerAgent):
    """Specialist for HTML structure and accessibility validation"""
    
    def __init__(self, agent_id: str, team_type: str, config, project_state, model_preference: Optional[str] = None):
        super().__init__(
            agent_id=agent_id,
            specialty=WorkerSpecialty.QA_HTML,
            team_type=team_type,
            config=config,
            project_state=project_state,
            model_preference=model_preference
        )
    
    def _build_atomic_prompt(self, task: Task) -> str:
        return f"""You are an HTML validation specialist focused on semantic markup, accessibility, and standards compliance.

ATOMIC TASK: {task.description}

Your focus areas:
- HTML5 semantic structure validation
- ARIA accessibility compliance (WCAG 2.1 AA)
- Cross-browser compatibility
- Performance implications of markup

VALIDATION CHECKLIST:
1. Semantic HTML5 elements used correctly
2. All images have alt attributes
3. Form elements have proper labels
4. Heading hierarchy is logical (h1->h2->h3)
5. ARIA roles and properties are appropriate
6. No deprecated HTML elements

IMPORTANT: 
- Use Claude Code's Read tool to examine existing HTML files
- Focus on one specific validation aspect per task
- Provide concrete, actionable feedback
- Keep validation atomic and time-bounded (max 3 minutes)

Limit your response to 3-5 specific findings with actionable recommendations."""

class CSSValidationWorker(WorkerAgent):
    """Specialist for CSS performance and cross-browser validation"""
    
    def __init__(self, agent_id: str, team_type: str, config, project_state, model_preference: Optional[str] = None):
        super().__init__(
            agent_id=agent_id,
            specialty=WorkerSpecialty.QA_CSS,
            team_type=team_type,
            config=config,
            project_state=project_state,
            model_preference=model_preference
        )
    
    def _build_atomic_prompt(self, task: Task) -> str:
        return f"""You are a CSS validation specialist focused on performance, browser compatibility, and maintainability.

ATOMIC TASK: {task.description}

Your focus areas:
- CSS performance optimization
- Cross-browser compatibility
- Responsive design validation
- Modern CSS best practices

VALIDATION CHECKLIST:
1. CSS selectors are efficient (avoid universal selectors)
2. Media queries follow mobile-first approach
3. Custom properties (CSS variables) used effectively
4. Animations use GPU-accelerated properties
5. No unused CSS rules
6. Proper fallbacks for modern features

IMPORTANT:
- Use Claude Code's Read tool to examine existing CSS files
- Focus on one specific validation aspect per task
- Provide performance impact assessment
- Keep validation atomic and time-bounded (max 3 minutes)

Limit your response to 3-5 specific findings with performance metrics where possible."""

class JavaScriptValidationWorker(WorkerAgent):
    """Specialist for JavaScript functionality and performance validation"""
    
    def __init__(self, agent_id: str, team_type: str, config, project_state, model_preference: Optional[str] = None):
        super().__init__(
            agent_id=agent_id,
            specialty=WorkerSpecialty.QA_JS,
            team_type=team_type,
            config=config,
            project_state=project_state,
            model_preference=model_preference
        )
    
    def _build_atomic_prompt(self, task: Task) -> str:
        return f"""You are a JavaScript validation specialist focused on functionality, performance, and error handling.

ATOMIC TASK: {task.description}

Your focus areas:
- JavaScript functionality validation
- Error handling and edge cases
- Performance optimization
- Modern ES6+ best practices

VALIDATION CHECKLIST:
1. Event listeners are properly attached
2. Form validation handles edge cases
3. No console errors or warnings
4. Performance APIs used correctly
5. Proper error handling for failed operations
6. Memory leaks prevention

IMPORTANT:
- Use Claude Code's Read tool to examine existing JavaScript files
- Test specific functionality aspects
- Focus on one validation area per task
- Keep validation atomic and time-bounded (max 3 minutes)

Limit your response to 3-5 specific findings with suggested improvements."""

class PerformanceTestWorker(WorkerAgent):
    """Specialist for web performance and optimization validation"""
    
    def __init__(self, agent_id: str, team_type: str, config, project_state, model_preference: Optional[str] = None):
        super().__init__(
            agent_id=agent_id,
            specialty=WorkerSpecialty.QA_PERFORMANCE,
            team_type=team_type,
            config=config,
            project_state=project_state,
            model_preference=model_preference
        )
    
    def _build_atomic_prompt(self, task: Task) -> str:
        return f"""You are a web performance testing specialist focused on Core Web Vitals and optimization.

ATOMIC TASK: {task.description}

Your focus areas:
- Core Web Vitals assessment
- Resource loading optimization
- Runtime performance analysis
- Bundle size optimization

VALIDATION CHECKLIST:
1. Critical resources are properly prioritized
2. Images are optimized and properly sized
3. CSS/JS are minified and compressed
4. No render-blocking resources
5. Proper caching strategies implemented
6. Performance budget compliance

PERFORMANCE TARGETS:
- First Contentful Paint: < 1.8s
- Largest Contentful Paint: < 2.5s
- Cumulative Layout Shift: < 0.1
- First Input Delay: < 100ms

IMPORTANT:
- Use Claude Code's Read tool to examine all web files
- Provide specific performance recommendations
- Focus on measurable improvements
- Keep analysis atomic and time-bounded (max 3 minutes)

Limit your response to 3-5 critical performance findings with optimization suggestions."""

class QAWorkerFactory:
    """Factory for creating appropriate QA worker agents"""
    
    @staticmethod
    def create_worker(task: Task, project_state, config) -> WorkerAgent:
        """Create the most appropriate QA worker for the given task"""
        task_lower = task.description.lower()
        
        # Determine QA specialty based on task description
        if any(keyword in task_lower for keyword in ['html', 'markup', 'semantic', 'accessibility', 'aria']):
            worker_id = f"worker_html_validator_{task.id[:8]}"
            return HTMLValidationWorker(worker_id, "qa", config, project_state)
        
        elif any(keyword in task_lower for keyword in ['css', 'style', 'responsive', 'animation', 'layout']):
            worker_id = f"worker_css_validator_{task.id[:8]}"
            return CSSValidationWorker(worker_id, "qa", config, project_state)
        
        elif any(keyword in task_lower for keyword in ['javascript', 'js', 'interactive', 'functionality', 'form']):
            worker_id = f"worker_js_validator_{task.id[:8]}"
            return JavaScriptValidationWorker(worker_id, "qa", config, project_state)
        
        elif any(keyword in task_lower for keyword in ['performance', 'speed', 'optimization', 'load', 'metrics']):
            worker_id = f"worker_performance_tester_{task.id[:8]}"
            return PerformanceTestWorker(worker_id, "qa", config, project_state)
        
        # Default to HTML validation for general testing tasks
        worker_id = f"worker_html_validator_{task.id[:8]}"
        return HTMLValidationWorker(worker_id, "qa", config, project_state)

# Export all QA workers
__all__ = [
    'HTMLValidationWorker',
    'CSSValidationWorker', 
    'JavaScriptValidationWorker',
    'PerformanceTestWorker',
    'QAWorkerFactory'
]