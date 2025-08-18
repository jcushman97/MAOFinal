"""
QA Team Lead Agent for MAOS

Specialized agent for quality assurance, testing, and validation.
Focuses on comprehensive testing strategies, bug detection, and quality standards.
"""

from typing import Dict, Any, List, Optional
from agents.team_lead_agent import TeamLeadAgent, TeamType
from agents.qa_workers import QAWorkerFactory
from core.state import Task, LogLevel
from core.logger import get_logger

logger = get_logger("qa_lead")


class QATeamLead(TeamLeadAgent):
    """
    QA Team Lead Agent specializing in:
    - Test strategy and planning
    - Automated and manual testing
    - Quality standards enforcement
    - Bug detection and reporting
    - Performance testing
    - Security testing
    - Accessibility validation
    """
    
    def __init__(self, agent_id: str, config, project_state):
        """Initialize QA Team Lead."""
        super().__init__(
            agent_id=agent_id,
            team_type=TeamType.QA,
            config=config,
            project_state=project_state,
            model_preference="claude"  # Claude excels at edge case detection
        )
        
        # QA-specific configuration for timeout management
        self.testing_timeout = 180  # 3 minutes max per test task
        self.max_test_attempts = 2  # Limit test retries
    
    async def _should_delegate_to_worker(self, task: Task) -> bool:
        """
        Determine if QA task should be delegated to specialized worker.
        
        QA tasks are good for worker delegation when they are:
        - Focused validation tasks (HTML, CSS, JS, Performance)
        - Atomic testing scenarios
        - Specific compliance checks
        """
        task_lower = task.description.lower()
        
        # Atomic testing tasks that benefit from specialization
        atomic_test_indicators = [
            'validate', 'check', 'verify', 'test', 'audit',
            'html', 'css', 'javascript', 'performance', 
            'accessibility', 'responsive', 'cross-browser',
            'standards', 'compliance', 'optimization'
        ]
        
        # Complex coordination tasks that Team Lead should handle
        complex_indicators = [
            'comprehensive', 'full testing', 'end-to-end',
            'integration', 'system', 'workflow', 'strategy'
        ]
        
        # Delegate if it's an atomic test task
        if any(indicator in task_lower for indicator in atomic_test_indicators):
            if not any(indicator in task_lower for indicator in complex_indicators):
                self._log(LogLevel.INFO, f"QA task suitable for worker delegation: {task.description}")
                return True
        
        return False
    
    async def _delegate_to_worker(self, task: Task) -> bool:
        """Delegate QA task to appropriate specialist worker."""
        try:
            self._log(LogLevel.INFO, f"QA Team Lead delegating task to worker: {task.description}")
            
            # Create appropriate QA worker using factory
            worker = QAWorkerFactory.create_worker(task, self.project_state, self.config)
            
            # Register worker in project state
            self.project_state.agents[worker.agent_id] = {
                "type": "worker",
                "model": worker.model_preference,
                "tokensUsed": 0,
                "callCount": 0
            }
            
            self._log(LogLevel.INFO, f"Created {worker.specialty.value} worker for task: {task.description}")
            
            # Execute with timeout management
            import asyncio
            try:
                # Execute with stricter timeout for QA tasks
                success = await asyncio.wait_for(
                    worker.execute_task(task), 
                    timeout=self.testing_timeout
                )
                
                if success:
                    # Update worker metrics in project state
                    if worker.agent_id in self.project_state.agents:
                        self.project_state.agents[worker.agent_id]["tokensUsed"] = worker.tokens_used
                        self.project_state.agents[worker.agent_id]["callCount"] = worker.call_count
                    
                    self._log(LogLevel.INFO, f"Worker {worker.agent_id} completed task: {task.description}")
                    return True
                else:
                    self._log(LogLevel.WARNING, f"Worker {worker.agent_id} failed task: {task.description}")
                    return False
                    
            except asyncio.TimeoutError:
                self._log(LogLevel.WARNING, f"QA task timed out after {self.testing_timeout}s: {task.description}")
                task.error = f"Task timed out after {self.testing_timeout} seconds"
                return False
                    
        except Exception as e:
            self._log(LogLevel.ERROR, f"QA worker delegation failed: {e}")
            task.error = str(e)
            return False
    
    def _get_worker_for_task(self, task: Task):
        """Get appropriate QA worker for the given task."""
        return QAWorkerFactory.create_worker(task, self.project_state, self.config)
    
    def _get_expertise_areas(self) -> List[str]:
        """QA expertise areas."""
        return [
            "Test strategy and planning",
            "Automated testing frameworks",
            "Manual testing techniques",
            "Performance testing",
            "Security testing",
            "Accessibility testing",
            "API testing and validation",
            "Cross-browser testing",
            "Mobile testing",
            "Load and stress testing",
            "Bug tracking and reporting",
            "Quality metrics and KPIs"
        ]
    
    def _get_team_best_practices(self) -> List[str]:
        """QA best practices."""
        return [
            "Shift-left testing approach",
            "Risk-based testing prioritization",
            "Comprehensive test coverage (unit, integration, E2E)",
            "Continuous testing in CI/CD pipeline",
            "Clear test documentation and reporting",
            "Defect prevention over defect detection",
            "User-centric testing approach",
            "Performance testing from early stages",
            "Security testing integration",
            "Accessibility compliance validation",
            "Cross-platform compatibility testing",
            "Test data management and cleanup"
        ]
    
    def _get_common_tools(self) -> List[str]:
        """Common QA tools and technologies."""
        return [
            "Selenium", "Playwright", "Cypress",
            "Jest", "PyTest", "JUnit",
            "Postman", "Insomnia", "REST Assured",
            "JMeter", "LoadRunner", "Artillery",
            "OWASP ZAP", "Burp Suite",
            "Jira", "TestRail", "Zephyr",
            "SonarQube", "ESLint",
            "Lighthouse", "axe-core",
            "BrowserStack", "Sauce Labs"
        ]
    
    def _get_quality_standards(self) -> Dict[str, str]:
        """QA quality standards."""
        return {
            "test_coverage": "80% minimum code coverage, 100% critical path coverage",
            "defect_rate": "<1% defect escape rate to production",
            "performance": "95th percentile response time <2s, 99.9% uptime",
            "accessibility": "WCAG 2.1 AA compliance, automated accessibility testing",
            "security": "OWASP compliance, regular security scan integration",
            "browser_support": "Cross-browser testing on latest 2 versions",
            "mobile_support": "Responsive testing on major devices and screen sizes",
            "regression": "Full regression suite execution before releases"
        }
    
    def _load_specialized_prompts(self) -> Dict[str, str]:
        """Load QA-specific prompt templates."""
        return {
            "test_strategy": """
You are a QA Team Lead with expertise in comprehensive testing strategies.

TASK: {task_description}
PROJECT CONTEXT: {project_objective}

Develop a thorough testing approach that ensures quality and reliability:

**Test Planning:**
- Analyze requirements for testability
- Identify critical user journeys and edge cases
- Define test coverage metrics and acceptance criteria
- Plan test data requirements and management
- Schedule testing activities in development lifecycle

**Testing Types to Consider:**
- Unit testing for individual components
- Integration testing for system interactions
- End-to-end testing for user workflows
- Performance testing for scalability
- Security testing for vulnerability assessment
- Accessibility testing for inclusive design
- Cross-browser/cross-platform compatibility

**Risk-Based Approach:**
- Identify high-risk areas requiring thorough testing
- Prioritize testing based on business impact
- Define exit criteria for each testing phase
- Plan contingency testing for failure scenarios

**Quality Metrics:**
- Define measurable quality objectives
- Implement test reporting and tracking
- Monitor defect trends and resolution times
- Track test execution progress and coverage

**Automation Strategy:**
- Identify candidates for test automation
- Select appropriate testing frameworks
- Plan test maintenance and CI/CD integration
- Balance automated and manual testing efforts

Provide detailed test plans with specific test cases, expected outcomes, and quality metrics.
            """,
            
            "bug_analysis": """
You are a QA Team Lead specializing in defect detection and analysis.

TASK: {task_description}
PROJECT CONTEXT: {project_objective}

Conduct thorough testing and analysis to identify potential issues:

**Bug Detection Approach:**
- Systematic exploration of functionality
- Boundary value testing and edge cases
- Negative testing with invalid inputs
- State transition testing
- Concurrency and race condition testing

**Analysis Framework:**
- Root cause analysis for identified issues
- Impact assessment (functional, performance, security)
- Reproduction steps with clear documentation
- Classification by severity and priority
- Regression impact evaluation

**Testing Scenarios:**
- Happy path user workflows
- Error handling and recovery scenarios
- Data validation and input sanitization
- Performance under various load conditions
- Security vulnerabilities and attack vectors

**Quality Assessment:**
- Code review from testing perspective
- Test coverage gap analysis
- Performance bottleneck identification
- Accessibility compliance verification
- Cross-platform compatibility issues

**Documentation Standards:**
- Clear bug reports with reproduction steps
- Screenshots/videos for UI issues
- Environment and configuration details
- Expected vs actual behavior description
- Suggested fixes or workarounds

Provide comprehensive testing results with detailed bug reports and quality recommendations.
            """,
            
            "validation_testing": """
You are a QA Team Lead focused on validation and verification testing.

TASK: {task_description}
PROJECT CONTEXT: {project_objective}

Validate that the implementation meets requirements and quality standards:

**Requirements Validation:**
- Verify implementation matches specifications
- Test all defined acceptance criteria
- Validate business rules and logic
- Confirm user experience meets expectations
- Check integration points and data flow

**Functional Validation:**
- End-to-end workflow testing
- Data integrity verification
- Error handling validation
- Performance requirement verification
- Security control effectiveness

**Non-Functional Testing:**
- Performance testing (load, stress, volume)
- Usability testing and user experience
- Accessibility compliance verification
- Security vulnerability assessment
- Compatibility testing across platforms

**Quality Gates:**
- Code quality metrics verification
- Test coverage threshold validation
- Performance benchmark compliance
- Security scan result review
- Documentation completeness check

**User Acceptance Criteria:**
- Real-world usage scenario testing
- User workflow validation
- Data accuracy verification
- System reliability confirmation
- Performance under normal conditions

**Risk Mitigation:**
- Identify potential failure points
- Test disaster recovery procedures
- Validate backup and restore processes
- Confirm monitoring and alerting systems
- Test rollback procedures

Provide validation results with pass/fail criteria and recommendations for production readiness.
            """
        }
    
    def _build_specialized_prompt(self, task: Task) -> str:
        """Build QA-specific prompt based on task characteristics."""
        task_description = task.description.lower()
        
        # Determine prompt type based on task content
        if any(keyword in task_description for keyword in ["validate", "verify", "acceptance", "production"]):
            prompt_type = "validation_testing"
        elif any(keyword in task_description for keyword in ["bug", "defect", "issue", "problem", "debug"]):
            prompt_type = "bug_analysis"
        else:
            prompt_type = "test_strategy"
        
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
        """Apply QA-specific post-processing."""
        # Add QA-specific context and validation notes
        processed_output = f"""QA Team Lead Analysis:
Task: {task.description}
Team Expertise Applied: {', '.join(self.team_context['expertise_areas'][:3])}

{output}

Quality Assurance Checklist:
- Test Coverage: Verify 80%+ code coverage and 100% critical path testing
- Performance: Confirm <2s response times and scalability requirements
- Security: Validate OWASP compliance and vulnerability assessments
- Accessibility: Ensure WCAG 2.1 AA compliance and inclusive design
- Cross-Platform: Test compatibility across browsers and devices
- User Experience: Validate intuitive workflows and error handling
- Regression: Execute full regression suite before deployment
- Documentation: Maintain clear test documentation and bug reports
"""
        return processed_output
    
    async def _process_deliverable_code(self, filename: str, code: str) -> str:
        """Apply QA-specific processing to deliverable files."""
        file_extension = filename.split('.')[-1].lower()
        
        if file_extension in ['js', 'ts']:
            return self._enhance_test_code(code)
        elif file_extension in ['py']:
            return self._enhance_python_test_code(code)
        elif file_extension in ['html']:
            return self._enhance_html_validation(code)
        
        return code
    
    def _enhance_test_code(self, test_code: str) -> str:
        """Add QA best practices to JavaScript/TypeScript test code."""
        # Add test structure comments if missing
        if 'describe(' in test_code and '// Test Suite:' not in test_code:
            enhanced_code = """// QA Team Lead Enhancement: Test Structure
// Test Suite: Comprehensive validation with edge cases
// Coverage: Unit, integration, and user workflow testing
// Quality Gates: Performance, accessibility, and security validation

""" + test_code
            return enhanced_code
        
        return test_code
    
    def _enhance_python_test_code(self, test_code: str) -> str:
        """Add QA best practices to Python test code."""
        # Add pytest imports and structure if missing
        if 'def test_' in test_code and 'import pytest' not in test_code:
            enhanced_code = """# QA Team Lead Enhancement: Python Testing Structure
import pytest
from unittest.mock import Mock, patch

""" + test_code
            return enhanced_code
        
        return test_code
    
    def _enhance_html_validation(self, html_code: str) -> str:
        """Add QA validation attributes to HTML."""
        # Add test-id attributes for easier testing
        if '<button' in html_code and 'data-testid' not in html_code:
            html_code = html_code.replace('<button', '<button data-testid="button"')
        
        if '<input' in html_code and 'data-testid' not in html_code:
            html_code = html_code.replace('<input', '<input data-testid="input"')
        
        return html_code
    
    def get_capabilities(self) -> List[str]:
        """Get QA-specific capabilities."""
        return [
            "test_strategy_development",
            "automated_testing",
            "manual_testing",
            "performance_testing",
            "security_testing",
            "accessibility_validation",
            "bug_detection_analysis",
            "quality_metrics_tracking",
            "cross_platform_testing",
            "user_acceptance_testing"
        ]