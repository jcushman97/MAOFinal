"""
Backend Team Lead Agent for MAOS

Specialized agent for backend development, system architecture, and server-side logic.
Focuses on scalability, security, performance, and robust API design.
"""

from typing import Dict, Any, List
from agents.team_lead_agent import TeamLeadAgent, TeamType
from core.state import Task
from core.logger import get_logger

logger = get_logger("backend_lead")


class BackendTeamLead(TeamLeadAgent):
    """
    Backend Team Lead Agent specializing in:
    - Server-side development and architecture
    - API design and implementation
    - Database design and optimization
    - Security and authentication
    - Performance and scalability
    - DevOps and deployment
    """
    
    def __init__(self, agent_id: str, config, project_state):
        """Initialize Backend Team Lead."""
        super().__init__(
            agent_id=agent_id,
            team_type=TeamType.BACKEND,
            config=config,
            project_state=project_state,
            model_preference="claude"  # Claude excels at system architecture
        )
    
    def _get_expertise_areas(self) -> List[str]:
        """Backend expertise areas."""
        return [
            "System architecture design",
            "RESTful API development",
            "Database design and optimization",
            "Authentication and authorization",
            "Security best practices",
            "Performance optimization",
            "Scalability patterns",
            "Microservices architecture",
            "DevOps and CI/CD",
            "Cloud infrastructure",
            "Error handling and logging",
            "Data modeling and migrations"
        ]
    
    def _get_team_best_practices(self) -> List[str]:
        """Backend development best practices."""
        return [
            "API-first design approach",
            "Comprehensive input validation",
            "Secure authentication (OAuth2/JWT)",
            "Database transaction management",
            "Proper error handling and logging",
            "Performance monitoring and metrics",
            "Automated testing (unit/integration)",
            "Code documentation and API specs",
            "Security by design principles",
            "Scalable architecture patterns",
            "Infrastructure as Code",
            "Continuous deployment practices"
        ]
    
    def _get_common_tools(self) -> List[str]:
        """Common backend tools and technologies."""
        return [
            "Python", "Node.js", "Java", "Go",
            "FastAPI", "Express.js", "Spring Boot",
            "PostgreSQL", "MySQL", "MongoDB", "Redis",
            "Docker", "Kubernetes",
            "AWS", "Google Cloud", "Azure",
            "Nginx", "Apache",
            "Git", "Jenkins", "GitHub Actions",
            "Prometheus", "Grafana",
            "Elasticsearch", "RabbitMQ"
        ]
    
    def _get_quality_standards(self) -> Dict[str, str]:
        """Backend quality standards."""
        return {
            "reliability": "99.9% uptime target with graceful degradation",
            "security": "OWASP Top 10 compliance, secure by default",
            "performance": "<200ms API response time, efficient database queries",
            "scalability": "Horizontal scaling support, stateless design",
            "maintainability": "Clean architecture, comprehensive documentation",
            "testing": "80%+ test coverage, automated testing pipeline",
            "monitoring": "Comprehensive logging, metrics, and alerting",
            "data_integrity": "ACID compliance, backup and recovery procedures"
        }
    
    def _load_specialized_prompts(self) -> Dict[str, str]:
        """Load backend-specific prompt templates."""
        return {
            "api_development": """
You are a Backend Team Lead with expertise in system architecture and API development.

TASK: {task_description}
PROJECT CONTEXT: {project_objective}

Design and implement a robust backend solution following these principles:

**Architecture Requirements:**
- Follow RESTful API design principles
- Implement proper HTTP status codes and methods
- Use consistent naming conventions
- Apply separation of concerns pattern
- Design for scalability and maintainability

**Security Standards:**
- Implement input validation and sanitization
- Use secure authentication mechanisms
- Apply proper authorization controls
- Prevent common vulnerabilities (OWASP Top 10)
- Implement rate limiting and request throttling

**Data Management:**
- Design efficient database schema
- Use proper indexing strategies
- Implement transaction management
- Apply data validation at multiple layers
- Plan for data migration and versioning

**Performance Considerations:**
- Optimize database queries
- Implement caching strategies
- Use connection pooling
- Apply pagination for large datasets
- Monitor and log performance metrics

**Error Handling:**
- Implement comprehensive error handling
- Provide meaningful error messages
- Log errors with proper context
- Design graceful degradation patterns

Provide clean, well-documented code with proper error handling and security considerations.
            """,
            
            "database_design": """
You are a Backend Team Lead specializing in database architecture.

TASK: {task_description}
PROJECT CONTEXT: {project_objective}

Create an efficient and scalable database solution:

**Database Design Principles:**
- Normalize data structure to reduce redundancy
- Design appropriate relationships (1:1, 1:N, N:N)
- Choose suitable data types for optimal storage
- Plan for future schema evolution
- Consider read/write access patterns

**Performance Optimization:**
- Create strategic indexes for query performance
- Avoid N+1 query problems
- Implement query optimization techniques
- Use appropriate database constraints
- Plan for data archival and cleanup

**Data Integrity:**
- Implement proper foreign key constraints
- Use database transactions appropriately
- Apply data validation rules
- Plan backup and recovery strategies
- Implement audit trails where needed

**Scalability Planning:**
- Design for horizontal scaling potential
- Consider read replicas for heavy read workloads
- Plan data partitioning strategies
- Implement connection pooling
- Monitor database performance metrics

Provide complete database schema with migration scripts and performance considerations.
            """,
            
            "security_focus": """
You are a Backend Team Lead with security expertise.

TASK: {task_description}
PROJECT CONTEXT: {project_objective}

Implement a secure backend solution addressing all security concerns:

**Authentication & Authorization:**
- Implement secure user authentication (OAuth2/JWT)
- Design role-based access control (RBAC)
- Use strong password policies and hashing
- Implement session management
- Apply principle of least privilege

**Input Security:**
- Validate and sanitize all inputs
- Prevent SQL injection attacks
- Protect against XSS vulnerabilities
- Implement CSRF protection
- Use parameterized queries

**Data Protection:**
- Encrypt sensitive data at rest and in transit
- Implement proper key management
- Use secure communication protocols (HTTPS)
- Apply data anonymization where appropriate
- Implement secure backup procedures

**System Security:**
- Keep dependencies updated and secure
- Implement proper logging for security events
- Use secure configuration management
- Apply rate limiting and DDoS protection
- Regular security testing and audits

**Compliance Considerations:**
- Follow GDPR/privacy regulations
- Implement data retention policies
- Provide user data access and deletion
- Maintain audit trails
- Document security procedures

Provide secure code with detailed security explanations and compliance considerations.
            """
        }
    
    def _build_specialized_prompt(self, task: Task) -> str:
        """Build backend-specific prompt based on task characteristics."""
        task_description = task.description.lower()
        
        # Determine prompt type based on task content
        if any(keyword in task_description for keyword in ["database", "schema", "sql", "migration", "model"]):
            prompt_type = "database_design"
        elif any(keyword in task_description for keyword in ["security", "auth", "login", "permission", "encrypt"]):
            prompt_type = "security_focus"
        else:
            prompt_type = "api_development"
        
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
        """Apply backend-specific post-processing."""
        # Add backend-specific context and validation notes
        processed_output = f"""Backend Team Lead Analysis:
Task: {task.description}
Team Expertise Applied: {', '.join(self.team_context['expertise_areas'][:3])}

{output}

Architecture Review Notes:
- Security: Verify input validation, authentication, and authorization
- Performance: Optimize queries, implement caching, monitor response times
- Scalability: Design for horizontal scaling and load distribution
- Reliability: Implement error handling, logging, and graceful degradation
- Maintainability: Follow clean architecture and documentation standards
- Data Integrity: Ensure ACID compliance and backup procedures
"""
        return processed_output
    
    async def _process_deliverable_code(self, filename: str, code: str) -> str:
        """Apply backend-specific processing to deliverable files."""
        file_extension = filename.split('.')[-1].lower()
        
        if file_extension == 'py':
            return self._enhance_python_code(code)
        elif file_extension == 'js':
            return self._enhance_nodejs_code(code)
        elif file_extension == 'sql':
            return self._enhance_sql_code(code)
        
        return code
    
    def _enhance_python_code(self, python_code: str) -> str:
        """Add backend best practices to Python code."""
        # Add docstring if missing
        if '"""' not in python_code and "'''" not in python_code:
            if 'def ' in python_code or 'class ' in python_code:
                # Add module docstring
                module_docstring = '"""\nBackend module generated by MAOS Backend Team Lead.\n"""\n\n'
                python_code = module_docstring + python_code
        
        # Add logging import if functions are present
        if 'def ' in python_code and 'import logging' not in python_code:
            logging_import = 'import logging\n\n'
            python_code = logging_import + python_code
        
        return python_code
    
    def _enhance_nodejs_code(self, js_code: str) -> str:
        """Add backend best practices to Node.js code."""
        # Add use strict if not present
        if "'use strict'" not in js_code and '"use strict"' not in js_code:
            js_code = "'use strict';\n\n" + js_code
        
        return js_code
    
    def _enhance_sql_code(self, sql_code: str) -> str:
        """Add backend best practices to SQL code."""
        # Add transaction wrapper if not present
        if 'BEGIN' not in sql_code.upper() and 'CREATE' in sql_code.upper():
            sql_code = "-- Backend Team Lead Enhancement: Transaction wrapper\nBEGIN;\n\n" + sql_code + "\n\nCOMMIT;"
        
        return sql_code
    
    def get_capabilities(self) -> List[str]:
        """Get backend-specific capabilities."""
        return [
            "api_development",
            "database_design",
            "system_architecture",
            "security_implementation",
            "performance_optimization",
            "scalability_planning",
            "devops_integration",
            "microservices_design",
            "authentication_systems",
            "data_modeling"
        ]