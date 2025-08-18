"""
Frontend Worker Agents for MAOS

Specialized workers for atomic frontend tasks including HTML, CSS, JavaScript,
and framework-specific implementations.
"""

from typing import Dict, Any, List
from agents.worker_agent import WorkerAgent, WorkerSpecialty
from core.state import Task
from core.logger import get_logger

logger = get_logger("frontend_workers")


class HTMLWorker(WorkerAgent):
    """
    Worker specializing in HTML structure and semantic markup.
    
    Handles:
    - HTML5 semantic structure
    - Accessibility markup
    - Meta tags and SEO
    - Form structures
    - Component templates
    """
    
    def __init__(self, agent_id: str, config, project_state):
        """Initialize HTML specialist worker."""
        super().__init__(
            agent_id=agent_id,
            specialty=WorkerSpecialty.HTML_SPECIALIST,
            team_type="frontend",
            config=config,
            project_state=project_state
        )
    
    def _build_atomic_prompt(self, task: Task) -> str:
        """Build HTML-specific atomic prompt."""
        return f"""
You are an HTML specialist worker focused on creating semantic, accessible HTML structures.

ATOMIC TASK: {task.description}
PROJECT CONTEXT: {self.project_state.objective}

Requirements:
- Create semantic HTML5 structure
- Include proper ARIA labels and roles
- Ensure valid HTML that passes W3C validation
- Add appropriate meta tags for SEO and mobile
- Use meaningful element names and IDs

IMPORTANT: Use Claude Code's Write tool to create the HTML file directly.
Create index.html or update existing HTML files as needed.

Focus only on HTML structure - do not include inline CSS or JavaScript.
"""
    
    def _validate_task_for_specialty(self, task: Task) -> bool:
        """Validate task is HTML-related."""
        html_keywords = ["html", "structure", "semantic", "markup", "template", "layout", "form"]
        task_lower = task.description.lower()
        return any(keyword in task_lower for keyword in html_keywords)


class CSSWorker(WorkerAgent):
    """
    Worker specializing in CSS styling and responsive design.
    
    Handles:
    - CSS3 styling
    - Responsive design
    - Animations and transitions
    - CSS Grid and Flexbox
    - Performance optimization
    """
    
    def __init__(self, agent_id: str, config, project_state):
        """Initialize CSS specialist worker."""
        super().__init__(
            agent_id=agent_id,
            specialty=WorkerSpecialty.CSS_SPECIALIST,
            team_type="frontend",
            config=config,
            project_state=project_state
        )
    
    def _build_atomic_prompt(self, task: Task) -> str:
        """Build CSS-specific atomic prompt."""
        return f"""
You are a CSS specialist worker focused on creating beautiful, responsive styles.

ATOMIC TASK: {task.description}
PROJECT CONTEXT: {self.project_state.objective}

Requirements:
- Create mobile-first responsive CSS
- Use CSS custom properties for theming
- Implement smooth animations and transitions
- Ensure cross-browser compatibility
- Optimize for performance (minimal specificity)

IMPORTANT: Use Claude Code's Write tool to create styles.css or update existing CSS files.

Focus only on CSS - create clean, maintainable stylesheets.
"""
    
    def _validate_task_for_specialty(self, task: Task) -> bool:
        """Validate task is CSS-related."""
        css_keywords = ["css", "style", "design", "responsive", "animation", "layout", "theme", "color"]
        task_lower = task.description.lower()
        return any(keyword in task_lower for keyword in css_keywords)


class JavaScriptWorker(WorkerAgent):
    """
    Worker specializing in JavaScript functionality and interactivity.
    
    Handles:
    - Vanilla JavaScript
    - DOM manipulation
    - Event handling
    - AJAX/Fetch operations
    - Performance optimization
    """
    
    def __init__(self, agent_id: str, config, project_state):
        """Initialize JavaScript specialist worker."""
        super().__init__(
            agent_id=agent_id,
            specialty=WorkerSpecialty.JS_SPECIALIST,
            team_type="frontend",
            config=config,
            project_state=project_state
        )
    
    def _build_atomic_prompt(self, task: Task) -> str:
        """Build JavaScript-specific atomic prompt."""
        return f"""
You are a JavaScript specialist worker focused on creating interactive functionality.

ATOMIC TASK: {task.description}
PROJECT CONTEXT: {self.project_state.objective}

Requirements:
- Write clean, modern ES6+ JavaScript
- Implement proper event handling
- Ensure code is performant and efficient
- Add error handling and validation
- Follow best practices for maintainability

IMPORTANT: Use Claude Code's Write tool to create script.js or update existing JavaScript files.

Focus only on JavaScript functionality - create modular, reusable code.
"""
    
    def _validate_task_for_specialty(self, task: Task) -> bool:
        """Validate task is JavaScript-related."""
        js_keywords = ["javascript", "js", "script", "interaction", "event", "function", "ajax", "fetch", "dom"]
        task_lower = task.description.lower()
        return any(keyword in task_lower for keyword in js_keywords)


class ReactWorker(WorkerAgent):
    """
    Worker specializing in React component development.
    
    Handles:
    - React components
    - State management
    - Hooks implementation
    - Component lifecycle
    - Performance optimization
    """
    
    def __init__(self, agent_id: str, config, project_state):
        """Initialize React specialist worker."""
        super().__init__(
            agent_id=agent_id,
            specialty=WorkerSpecialty.REACT_SPECIALIST,
            team_type="frontend",
            config=config,
            project_state=project_state
        )
    
    def _build_atomic_prompt(self, task: Task) -> str:
        """Build React-specific atomic prompt."""
        return f"""
You are a React specialist worker focused on creating React components.

ATOMIC TASK: {task.description}
PROJECT CONTEXT: {self.project_state.objective}

Requirements:
- Create functional React components with hooks
- Implement proper state management
- Ensure components are reusable and composable
- Add PropTypes or TypeScript types
- Follow React best practices

IMPORTANT: Use Claude Code's Write tool to create component files (e.g., Component.jsx).

Focus on creating clean, efficient React components.
"""
    
    def _validate_task_for_specialty(self, task: Task) -> bool:
        """Validate task is React-related."""
        react_keywords = ["react", "component", "jsx", "hooks", "state", "props", "render"]
        task_lower = task.description.lower()
        return any(keyword in task_lower for keyword in react_keywords)


class FrontendWorkerFactory:
    """Factory for creating appropriate frontend workers based on task requirements."""
    
    @staticmethod
    def create_worker_for_task(task: Task, config, project_state) -> WorkerAgent:
        """Create the most appropriate frontend worker for a given task."""
        task_lower = task.description.lower()
        
        # Determine best worker based on task description
        if any(keyword in task_lower for keyword in ["react", "component", "jsx"]):
            return ReactWorker(None, config, project_state)
        elif any(keyword in task_lower for keyword in ["javascript", "js", "script", "interaction", "event"]):
            return JavaScriptWorker(None, config, project_state)
        elif any(keyword in task_lower for keyword in ["css", "style", "design", "responsive", "animation"]):
            return CSSWorker(None, config, project_state)
        else:
            # Default to HTML worker for structure tasks
            return HTMLWorker(None, config, project_state)
    
    @staticmethod
    def create_worker_team(config, project_state) -> List[WorkerAgent]:
        """Create a team of frontend workers for parallel execution."""
        return [
            HTMLWorker(None, config, project_state),
            CSSWorker(None, config, project_state),
            JavaScriptWorker(None, config, project_state)
        ]