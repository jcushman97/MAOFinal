# MAOS DEVELOPMENT GUARDRAILS

**Version:** 1.0  
**Effective:** January 18, 2025  
**Last Updated:** January 18, 2025

## CODE STYLE AND FORMATTING

### Python Standards
- **PEP 8 Compliance:** All Python code must follow PEP 8 style guidelines
- **Line Length:** Maximum 88 characters (Black formatter standard)
- **Indentation:** 4 spaces, no tabs
- **Imports:** Grouped and sorted (stdlib, third-party, local)
- **Docstrings:** Google-style docstrings for all public functions and classes
- **Type Hints:** Required for all function signatures and class attributes

### Naming Conventions
- **Classes:** PascalCase (e.g., `ProjectManager`, `TaskRouter`)
- **Functions/Methods:** snake_case (e.g., `execute_task`, `get_agent_state`)
- **Variables:** snake_case (e.g., `task_id`, `project_state`)
- **Constants:** UPPER_SNAKE_CASE (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Files:** snake_case with descriptive names (e.g., `state_manager.py`, `cli_wrapper.py`)

### Forbidden Characters and Patterns
- **No Emojis:** No emoji characters in code, comments, or strings
- **No Unicode Art:** No decorative Unicode characters
- **No Special Characters:** Avoid non-ASCII characters except in documentation
- **No Magic Numbers:** Use named constants instead of hardcoded values
- **No Global Variables:** Use configuration classes or dependency injection

## SECURITY GUARDRAILS

### File System Access
- **Path Validation:** All file paths must be validated and sanitized
- **No Directory Traversal:** Prevent `../` or absolute path exploits
- **Restricted Write Access:** Only write to designated project directories
- **No Executable Creation:** Do not create or modify executable files
- **Safe Temp Files:** Use secure temporary file creation methods

### CLI Integration
- **Command Injection Prevention:** All CLI inputs must be sanitized
- **Timeout Enforcement:** All subprocess calls must have timeout limits
- **Error Handling:** Capture and sanitize all CLI error outputs
- **No Shell=True:** Use subprocess with explicit command arrays
- **Resource Limits:** Implement memory and CPU usage constraints

### Data Handling
- **No Credential Storage:** Never store API keys or passwords in code
- **Input Validation:** Validate all user inputs and external data
- **Safe JSON Parsing:** Use safe JSON parsing with schema validation
- **No Code Execution:** Never execute dynamically generated code
- **Logging Safety:** No sensitive data in logs

## ARCHITECTURE CONSTRAINTS

### Agent Communication
- **JSON Only:** All inter-agent communication must use structured JSON
- **Schema Validation:** All JSON must conform to predefined schemas
- **No Direct Access:** Agents cannot directly access other agents' state
- **Immutable Messages:** Agent messages should be immutable after creation
- **Error Propagation:** All errors must be properly caught and logged

### State Management
- **Atomic Operations:** All state changes must be atomic
- **Version Control:** State files should include version information
- **Backup Strategy:** Implement automatic state backup before modifications
- **Consistency Checks:** Validate state integrity on load and save
- **No Shared State:** Each agent maintains isolated state

### Resource Management
- **Memory Limits:** Implement memory usage monitoring and limits
- **Token Tracking:** Track and limit token usage per agent and project
- **Timeout Enforcement:** All operations must have reasonable timeouts
- **Cleanup Procedures:** Implement proper resource cleanup on errors
- **Graceful Degradation:** System must handle resource exhaustion gracefully

## TESTING REQUIREMENTS

### Test Coverage
- **Minimum Coverage:** 80% code coverage for all modules
- **Unit Tests:** All functions and methods must have unit tests
- **Integration Tests:** Critical workflows must have integration tests
- **Error Path Testing:** All error conditions must be tested
- **Mock External Dependencies:** CLI tools and file systems must be mocked

### Test Standards
- **Descriptive Names:** Test names must clearly describe what is being tested
- **Single Assertion:** Each test should verify one specific behavior
- **Test Data:** Use fixtures for test data, no hardcoded values
- **Cleanup:** All tests must clean up after themselves
- **Deterministic:** Tests must not depend on external state or timing

## ERROR HANDLING STANDARDS

### Exception Management
- **Specific Exceptions:** Use specific exception types, not generic Exception
- **Error Context:** Include relevant context in exception messages
- **No Silent Failures:** All errors must be logged or propagated
- **Graceful Recovery:** Implement recovery strategies where possible
- **User-Friendly Messages:** Error messages should be actionable for users

### Logging Requirements
- **Structured Logging:** Use structured logging with consistent formats
- **Log Levels:** Use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **No Sensitive Data:** Never log passwords, tokens, or user data
- **Contextual Information:** Include relevant context (task_id, agent_id, etc.)
- **Performance Logging:** Log performance metrics for monitoring

## DEPENDENCY MANAGEMENT

### Library Restrictions
- **Minimal Dependencies:** Only add dependencies that are absolutely necessary
- **Security Scanning:** All dependencies must be scanned for vulnerabilities
- **Version Pinning:** Pin exact versions in requirements.txt
- **License Compatibility:** Ensure all dependencies have compatible licenses
- **No Deprecated Libraries:** Avoid libraries that are deprecated or unmaintained

### Import Guidelines
- **Standard Library First:** Prefer standard library over third-party when possible
- **Explicit Imports:** Use explicit imports, avoid wildcard imports
- **Import Order:** Follow PEP 8 import ordering
- **No Circular Imports:** Design modules to avoid circular dependencies
- **Lazy Loading:** Use lazy loading for expensive imports when appropriate

## DOCUMENTATION STANDARDS

### Code Documentation
- **Public API Documentation:** All public classes and functions must be documented
- **Parameter Documentation:** Document all parameters and return values
- **Example Usage:** Include usage examples for complex functions
- **Error Documentation:** Document possible exceptions and error conditions
- **Version Information:** Include version info for significant changes

### Comment Guidelines
- **Why, Not What:** Comments should explain why, not what the code does
- **Keep Updated:** Comments must be updated when code changes
- **No Obvious Comments:** Avoid comments that state the obvious
- **TODO Format:** Use standardized TODO format with assignee and date
- **License Headers:** Include appropriate license headers in source files

## PERFORMANCE GUIDELINES

### Efficiency Requirements
- **Time Complexity:** Document time complexity for algorithms
- **Memory Usage:** Monitor and optimize memory usage
- **Caching Strategy:** Implement appropriate caching for expensive operations
- **Lazy Evaluation:** Use lazy evaluation where appropriate
- **Profiling:** Profile performance-critical code paths

### Scalability Considerations
- **Linear Scaling:** Design for linear scaling with project size
- **Resource Pooling:** Use resource pooling for expensive objects
- **Async Operations:** Use async/await for I/O-bound operations
- **Batch Processing:** Implement batch processing for bulk operations
- **Memory Management:** Implement proper memory cleanup and garbage collection

## CONFIGURATION MANAGEMENT

### Settings Organization
- **Environment-Based:** Support multiple environment configurations
- **Type Safety:** Use typed configuration classes
- **Validation:** Validate all configuration values on startup
- **Default Values:** Provide sensible defaults for all settings
- **Documentation:** Document all configuration options

### Secrets Management
- **Environment Variables:** Use environment variables for sensitive data
- **No Hardcoded Secrets:** Never hardcode secrets in source code
- **Secure Storage:** Use secure storage mechanisms for local secrets
- **Access Control:** Implement proper access controls for configuration
- **Audit Trail:** Log configuration changes and access

## QUALITY GATES

### Pre-Commit Checks
- **Linting:** Code must pass all linting checks
- **Type Checking:** All type annotations must be valid
- **Tests:** All tests must pass before commit
- **Security Scan:** Basic security scanning must pass
- **Documentation:** Public APIs must be documented

### Review Requirements
- **Code Review:** All changes require code review
- **Security Review:** Security-sensitive changes require security review
- **Architecture Review:** Architectural changes require architecture review
- **Documentation Review:** Documentation changes require review
- **Testing Review:** Test changes require testing specialist review

## VIOLATION HANDLING

### Enforcement
- **Automated Checks:** Use automated tools to enforce guardrails
- **Build Failures:** Violations should cause build failures
- **Review Blocking:** Violations should block code reviews
- **Documentation:** All violations must be documented
- **Remediation:** Provide clear guidance for fixing violations

### Exceptions
- **Justification Required:** All exceptions must be justified
- **Approval Process:** Exceptions require explicit approval
- **Time-Bound:** Exceptions should be time-bound with expiration
- **Documentation:** All exceptions must be documented
- **Review:** Regular review of granted exceptions

---

## GUARDRAIL UPDATES

This document will be updated as the project evolves. All changes must be:
- Reviewed by the development team
- Documented with rationale
- Communicated to all developers
- Implemented with appropriate tooling
- Verified through testing

**Next Review Date:** February 18, 2025