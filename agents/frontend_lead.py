"""
Frontend Team Lead Agent for MAOS

Specialized agent for frontend development, UI/UX design, and user experience tasks.
Focuses on responsive design, accessibility, and modern web technologies.
"""

from typing import Dict, Any, List
from agents.team_lead_agent import TeamLeadAgent, TeamType
from core.state import Task, LogLevel
from core.logger import get_logger

logger = get_logger("frontend_lead")


class FrontendTeamLead(TeamLeadAgent):
    """
    Frontend Team Lead Agent specializing in:
    - UI/UX development and design
    - Responsive web design
    - Accessibility compliance
    - Frontend performance optimization
    - User experience best practices
    """
    
    def __init__(self, agent_id: str, config, project_state):
        """Initialize Frontend Team Lead."""
        super().__init__(
            agent_id=agent_id,
            team_type=TeamType.FRONTEND,
            config=config,
            project_state=project_state,
            model_preference="claude"  # Claude excels at UI/UX tasks
        )
    
    def _get_expertise_areas(self) -> List[str]:
        """Frontend expertise areas."""
        return [
            "HTML5/CSS3/JavaScript",
            "React/Vue/Angular frameworks",
            "Responsive design",
            "Accessibility (WCAG 2.1)",
            "UI/UX principles",
            "Frontend performance",
            "Cross-browser compatibility",
            "Modern CSS (Grid, Flexbox)",
            "Component architecture",
            "State management",
            "Progressive Web Apps"
        ]
    
    def _get_team_best_practices(self) -> List[str]:
        """Frontend development best practices."""
        return [
            "Mobile-first responsive design",
            "Semantic HTML structure",
            "WCAG 2.1 AA accessibility compliance",
            "Progressive enhancement approach",
            "Component-based architecture",
            "Performance budgets (<3s load time)",
            "Cross-browser testing (Chrome, Firefox, Safari, Edge)",
            "Code splitting and lazy loading",
            "Optimized asset delivery",
            "User-centered design principles",
            "Consistent design system usage"
        ]
    
    def _get_common_tools(self) -> List[str]:
        """Common frontend tools and technologies."""
        return [
            "HTML5", "CSS3", "JavaScript (ES6+)",
            "React", "Vue.js", "Angular",
            "Webpack", "Vite", "Parcel",
            "Sass/SCSS", "PostCSS",
            "ESLint", "Prettier",
            "Jest", "Cypress", "Playwright",
            "Figma", "Sketch",
            "Chrome DevTools",
            "Lighthouse", "WebPageTest"
        ]
    
    def _get_quality_standards(self) -> Dict[str, str]:
        """Frontend quality standards."""
        return {
            "accessibility": "WCAG 2.1 AA compliance minimum",
            "performance": "Lighthouse score >90, <3s load time on 3G",
            "browser_support": "Modern browsers (Chrome, Firefox, Safari, Edge)",
            "responsive": "Mobile-first, supports 320px to 2560px viewports",
            "code_quality": "ESLint clean, consistent component structure",
            "user_experience": "Intuitive navigation, clear visual hierarchy",
            "progressive": "Works without JavaScript, enhanced with JS"
        }
    
    def _load_specialized_prompts(self) -> Dict[str, str]:
        """Load frontend-specific prompt templates."""
        return {
            "ui_component": """
You are a Frontend Team Lead with expertise in modern web development and user experience.

TASK: {task_description}
PROJECT CONTEXT: {project_objective}

IMPORTANT: You must generate actual working code. Do not ask for permissions or mention file creation issues. Simply provide the complete, working code that implements the requested functionality.

Create a high-quality frontend solution following these principles:

**Technical Requirements:**
- Use semantic HTML5 structure
- Apply responsive CSS (mobile-first approach)  
- Ensure WCAG 2.1 AA accessibility compliance
- Optimize for performance (<3s load time)
- Support modern browsers (Chrome, Firefox, Safari, Edge)

**UI/UX Guidelines:**
- Follow user-centered design principles
- Create clear visual hierarchy
- Ensure intuitive user interactions
- Apply consistent spacing and typography
- Use appropriate color contrast ratios

**Code Quality:**
- Write clean, maintainable code
- Use modern JavaScript (ES6+) features
- Apply component-based architecture
- Include proper error handling
- Add meaningful comments for complex logic

**Required Output Format:**
You have access to Claude Code's Write tool. Use it to create actual working files:

1. First, create the HTML file:
   Use Write tool to create index.html with complete working HTML structure

2. Then, create the CSS file:
   Use Write tool to create styles.css with complete responsive styling

3. Finally, create the JavaScript file:
   Use Write tool to create script.js with interactive functionality

After creating the files, explain your design decisions and accessibility considerations.
            """,
            
            "responsive_design": """
You are a Frontend Team Lead specializing in responsive web design.

TASK: {task_description}
PROJECT CONTEXT: {project_objective}

IMPORTANT: Generate actual working responsive code. Do not ask for permissions. Provide complete HTML, CSS, and JavaScript code.

Create a responsive solution that works across all device sizes:

**Responsive Requirements:**
- Mobile-first CSS approach (min-width media queries)
- Support viewports from 320px to 2560px
- Flexible grid layouts using CSS Grid or Flexbox
- Scalable typography with relative units (rem, em, %)
- Touch-friendly interactive elements (44px minimum)

**Performance Considerations:**
- Optimize images for different screen densities
- Use efficient CSS selectors
- Minimize layout shifts (CLS)
- Implement progressive loading for large content

**Testing Approach:**
- Design for common breakpoints: 320px, 768px, 1024px, 1200px
- Consider landscape and portrait orientations
- Test on various devices and screen sizes

**Required Output Format:**
Use Claude Code's Write tool to create responsive files:

1. Create index.html with responsive HTML structure
2. Create styles.css with mobile-first CSS and breakpoints
3. Create script.js with responsive JavaScript features

Provide complete responsive implementation with clear breakpoint strategy.
            """,
            
            "accessibility_focus": """
You are a Frontend Team Lead with accessibility expertise.

TASK: {task_description}
PROJECT CONTEXT: {project_objective}

IMPORTANT: Generate actual working accessible code. Do not ask for permissions. Provide complete HTML, CSS, and JavaScript that implements accessibility features.

Create an accessible frontend solution that works for all users:

**Accessibility Requirements (WCAG 2.1 AA):**
- Semantic HTML structure with proper heading hierarchy
- Alternative text for images and icons
- Keyboard navigation support (tab order, focus indicators)
- Color contrast ratio minimum 4.5:1 for normal text
- Form labels and error messaging
- Screen reader compatibility

**Interactive Elements:**
- Focus management for dynamic content
- ARIA labels and descriptions where needed
- Skip links for keyboard navigation
- Consistent navigation patterns

**Testing Considerations:**
- Works without JavaScript (progressive enhancement)
- Screen reader compatibility (NVDA, JAWS, VoiceOver)
- Keyboard-only navigation
- High contrast mode support

**Required Output Format:**
Use Claude Code's Write tool to create accessible files:

1. Create index.html with semantic, accessible HTML structure
2. Create styles.css with accessibility-focused styling
3. Create script.js with accessibility support features

Provide accessible implementation with explanations of accessibility features.
            """
        }
    
    def _build_specialized_prompt(self, task: Task) -> str:
        """Build frontend-specific prompt based on task characteristics."""
        task_description = task.description.lower()
        
        # Determine prompt type based on task content
        if any(keyword in task_description for keyword in ["responsive", "mobile", "breakpoint", "viewport"]):
            prompt_type = "responsive_design"
        elif any(keyword in task_description for keyword in ["accessibility", "wcag", "screen reader", "aria"]):
            prompt_type = "accessibility_focus"
        else:
            prompt_type = "ui_component"
        
        # Get the appropriate prompt template
        prompt_template = self.specialized_prompts[prompt_type]
        
        # Format with task context
        return self._format_prompt(
            prompt_template,
            {
                "task_description": task.description,
                "project_objective": self.project_state.objective
            }
        )
    
    async def _post_process_output(self, task: Task, output: str) -> str:
        """Apply frontend-specific post-processing."""
        # Add frontend-specific context and validation notes
        processed_output = f"""Frontend Team Lead Analysis:
Task: {task.description}
Team Expertise Applied: {', '.join(self.team_context['expertise_areas'][:3])}

{output}

Quality Assurance Notes:
- Responsive Design: Ensure mobile-first approach with flexible layouts
- Accessibility: Verify WCAG 2.1 AA compliance and keyboard navigation
- Performance: Optimize for <3s load time with efficient CSS and JavaScript
- Browser Support: Test across Chrome, Firefox, Safari, and Edge
- User Experience: Focus on intuitive interactions and clear visual hierarchy
"""
        return processed_output
    
    async def _process_deliverable_code(self, filename: str, code: str) -> str:
        """Apply frontend-specific processing to deliverable files."""
        file_extension = filename.split('.')[-1].lower()
        
        if file_extension == 'html':
            return self._enhance_html_code(code)
        elif file_extension == 'css':
            return self._enhance_css_code(code)
        elif file_extension == 'js':
            return self._enhance_js_code(code)
        
        return code
    
    def _enhance_html_code(self, html_code: str) -> str:
        """Add frontend best practices to HTML code."""
        # Add meta viewport if missing
        if 'viewport' not in html_code and '<head>' in html_code:
            viewport_meta = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
            html_code = html_code.replace('<head>', f'<head>\n    {viewport_meta}')
        
        # Add charset if missing
        if 'charset' not in html_code and '<head>' in html_code:
            charset_meta = '<meta charset="UTF-8">'
            html_code = html_code.replace('<head>', f'<head>\n    {charset_meta}')
        
        return html_code
    
    def _enhance_css_code(self, css_code: str) -> str:
        """Add frontend best practices to CSS code."""
        # Add box-sizing reset if not present
        if 'box-sizing' not in css_code:
            box_sizing_reset = """/* Frontend Team Lead Enhancement: Box-sizing reset */
*, *::before, *::after {
    box-sizing: border-box;
}

"""
            css_code = box_sizing_reset + css_code
        
        return css_code
    
    def _enhance_js_code(self, js_code: str) -> str:
        """Add frontend best practices to JavaScript code."""
        # Add use strict if not present
        if "'use strict'" not in js_code and '"use strict"' not in js_code:
            js_code = "'use strict';\n\n" + js_code
        
        return js_code
    
    def get_capabilities(self) -> List[str]:
        """Get frontend-specific capabilities."""
        return [
            "ui_component_development",
            "responsive_web_design",
            "accessibility_implementation",
            "frontend_performance_optimization",
            "cross_browser_compatibility",
            "user_experience_design",
            "modern_css_techniques",
            "javascript_development",
            "component_architecture",
            "progressive_web_apps",
            "worker_delegation",  # Phase 3
            "parallel_execution"  # Phase 3
        ]
    
    # Phase 3: Worker delegation implementation
    
    async def _get_worker_for_task(self, task: Task):
        """Get appropriate Frontend Worker for a specific task."""
        try:
            # Import here to avoid circular imports
            from agents.frontend_workers import FrontendWorkerFactory
            
            # Create appropriate worker based on task
            worker = FrontendWorkerFactory.create_worker_for_task(
                task, self.config, self.project_state
            )
            
            self._log(LogLevel.INFO, f"Created {worker.specialty.value} worker for task: {task.description}")
            return worker
            
        except Exception as e:
            self._log(LogLevel.ERROR, f"Failed to create worker for task: {e}")
            return None