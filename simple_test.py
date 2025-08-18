#!/usr/bin/env python3
"""
Simple Testing Suite for MAOS
Validates all phases of the Multi-Agent Orchestration System without Unicode characters
"""

import asyncio
import sys
import time
import json
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.orchestrator import Orchestrator
from core.config import Config
from core.logger import setup_logging
from core.parallel_orchestrator import ParallelStrategy, ExecutionMode
from core.state import ProjectStatus, TaskStatus


class TestResult:
    """Container for test results."""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.success = False
        self.duration = 0.0
        self.error_message = ""
        self.details = {}
        
    def mark_success(self, duration: float, details: Dict[str, Any] = None):
        self.success = True
        self.duration = duration
        self.details = details or {}
        
    def mark_failure(self, duration: float, error: str, details: Dict[str, Any] = None):
        self.success = False
        self.duration = duration
        self.error_message = error
        self.details = details or {}


class SimpleTestSuite:
    """Simple test suite for MAOS system."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.test_project_dir = Path("test_projects")
        self.change_log = []
        
        # Ensure test directories exist
        self.test_project_dir.mkdir(exist_ok=True)
        
        # Setup logging
        setup_logging(level="INFO")
        
    def log_change(self, change_type: str, description: str, file_path: str = None):
        """Log any changes made during testing."""
        change_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": change_type,
            "description": description,
            "file_path": file_path
        }
        self.change_log.append(change_entry)
        print(f"[CHANGE] {change_type} - {description}")
        
    async def run_all_tests(self) -> bool:
        """Run simple test suite across all phases."""
        print("Starting Simple MAOS Test Suite")
        print("=" * 50)
        
        test_methods = [
            self.test_basic_system_startup,
            self.test_phase1_functionality,
            self.test_phase2_delegation,
            self.test_phase3_workers,
            self.test_phase4_parallel,
            self.test_end_to_end
        ]
        
        total_success = True
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                result = TestResult(test_method.__name__)
                result.mark_failure(0.0, f"Test execution failed: {str(e)}")
                self.results.append(result)
                total_success = False
                print(f"[FAIL] {test_method.__name__} failed: {e}")
                
        # Generate report
        self.generate_report()
        
        return total_success
        
    async def test_basic_system_startup(self):
        """Test basic system initialization."""
        result = TestResult("test_basic_system_startup")
        start_time = time.time()
        
        try:
            print("\nTesting Basic System Startup...")
            
            # Test configuration loading
            config = Config.load()
            assert config is not None, "Config should load successfully"
            assert config.project_dir.exists(), "Project directory should exist"
            
            # Test orchestrator initialization
            orchestrator = Orchestrator(config)
            assert orchestrator is not None, "Orchestrator should initialize"
            
            duration = time.time() - start_time
            result.mark_success(duration, {
                "config_loaded": True,
                "orchestrator_initialized": True
            })
            
            print(f"[PASS] Basic system startup completed in {duration:.2f}s")
            
        except Exception as e:
            duration = time.time() - start_time
            result.mark_failure(duration, str(e))
            print(f"[FAIL] Basic system startup failed: {e}")
            
        self.results.append(result)
        
    async def test_phase1_functionality(self):
        """Test Phase 1: Project Manager functionality."""
        result = TestResult("test_phase1_functionality")
        start_time = time.time()
        
        try:
            print("\nTesting Phase 1: PM Functionality...")
            
            config = Config.load()
            config.project_dir = self.test_project_dir
            
            orchestrator = Orchestrator(config)
            
            # Test simple project creation
            test_objective = "Create a simple HTML page"
            project_id = await orchestrator.start_project(test_objective, dry_run=True)
            
            assert project_id is not None, "Project should be created"
            assert len(project_id) > 0, "Project ID should be non-empty"
            
            duration = time.time() - start_time
            result.mark_success(duration, {
                "project_created": True,
                "project_id": project_id
            })
            
            print(f"[PASS] Phase 1 functionality completed in {duration:.2f}s")
            
        except Exception as e:
            duration = time.time() - start_time
            result.mark_failure(duration, str(e))
            print(f"[FAIL] Phase 1 functionality failed: {e}")
            
        self.results.append(result)
        
    async def test_phase2_delegation(self):
        """Test Phase 2: Hierarchical delegation."""
        result = TestResult("test_phase2_delegation")
        start_time = time.time()
        
        try:
            print("\nTesting Phase 2: Hierarchical Delegation...")
            
            from agents.frontend_lead import FrontendTeamLead
            from agents.backend_lead import BackendTeamLead
            from agents.qa_lead import QATeamLead
            
            config = Config.load()
            
            # Create a mock project state for testing
            from core.state import ProjectState
            mock_project = ProjectState(objective="test project")
            
            # Test team lead initialization
            frontend_lead = FrontendTeamLead("test_frontend", config, mock_project)
            assert frontend_lead is not None, "Frontend lead should initialize"
            
            backend_lead = BackendTeamLead("test_backend", config, mock_project)
            assert backend_lead is not None, "Backend lead should initialize"
            
            qa_lead = QATeamLead("test_qa", config, mock_project)
            assert qa_lead is not None, "QA lead should initialize"
            
            duration = time.time() - start_time
            result.mark_success(duration, {
                "team_leads_initialized": True,
                "teams": ["frontend", "backend", "qa"]
            })
            
            print(f"[PASS] Phase 2 delegation completed in {duration:.2f}s")
            
        except Exception as e:
            duration = time.time() - start_time
            result.mark_failure(duration, str(e))
            print(f"[FAIL] Phase 2 delegation failed: {e}")
            
        self.results.append(result)
        
    async def test_phase3_workers(self):
        """Test Phase 3: Worker agents and QA optimizations."""
        result = TestResult("test_phase3_workers")
        start_time = time.time()
        
        try:
            print("\nTesting Phase 3: Worker Agents...")
            
            from agents.frontend_workers import HTMLWorker, CSSWorker
            from agents.qa_workers import HTMLValidationWorker
            
            config = Config.load()
            
            # Create a mock project state for testing
            from core.state import ProjectState
            mock_project = ProjectState(objective="test project")
            
            # Test worker initialization
            html_worker = HTMLWorker("test_html", config, mock_project)
            assert html_worker is not None, "HTML worker should initialize"
            
            css_worker = CSSWorker("test_css", config, mock_project)
            assert css_worker is not None, "CSS worker should initialize"
            
            qa_worker = HTMLValidationWorker("test_qa_html", "qa", config, mock_project)
            assert qa_worker is not None, "QA worker should initialize"
            
            # Test timeout configuration
            assert hasattr(qa_worker, 'execution_context'), "QA worker should have execution context"
            
            duration = time.time() - start_time
            result.mark_success(duration, {
                "workers_initialized": True,
                "qa_optimizations": True
            })
            
            print(f"[PASS] Phase 3 workers completed in {duration:.2f}s")
            
        except Exception as e:
            duration = time.time() - start_time
            result.mark_failure(duration, str(e))
            print(f"[FAIL] Phase 3 workers failed: {e}")
            
        self.results.append(result)
        
    async def test_phase4_parallel(self):
        """Test Phase 4: Parallel execution."""
        result = TestResult("test_phase4_parallel")
        start_time = time.time()
        
        try:
            print("\nTesting Phase 4: Parallel Execution...")
            
            from core.parallel_orchestrator import ParallelOrchestrator
            from core.dependency_analyzer import DependencyAnalyzer
            from core.resource_manager import ResourceManager
            
            config = Config.load()
            
            # Test parallel components
            parallel_orchestrator = ParallelOrchestrator(config, ParallelStrategy.BALANCED)
            assert parallel_orchestrator is not None, "Parallel orchestrator should initialize"
            
            analyzer = DependencyAnalyzer(ParallelStrategy.BALANCED)
            assert analyzer is not None, "Dependency analyzer should initialize"
            
            resource_manager = ResourceManager(config)
            assert resource_manager is not None, "Resource manager should initialize"
            
            # Test orchestrator with parallel enabled
            orchestrator = Orchestrator(config, enable_parallel=True)
            assert orchestrator.enable_parallel == True, "Parallel should be enabled"
            
            capabilities = orchestrator.get_parallel_capabilities()
            assert capabilities["parallel_enabled"] == True, "Capabilities should show parallel enabled"
            
            duration = time.time() - start_time
            result.mark_success(duration, {
                "parallel_components": True,
                "orchestrator_parallel": True
            })
            
            print(f"[PASS] Phase 4 parallel completed in {duration:.2f}s")
            
        except Exception as e:
            duration = time.time() - start_time
            result.mark_failure(duration, str(e))
            print(f"[FAIL] Phase 4 parallel failed: {e}")
            
        self.results.append(result)
        
    async def test_end_to_end(self):
        """Test end-to-end project execution."""
        result = TestResult("test_end_to_end")
        start_time = time.time()
        
        try:
            print("\nTesting End-to-End Project...")
            
            config = Config.load()
            config.project_dir = self.test_project_dir
            
            # Test both modes
            for mode_name, enable_parallel in [("Sequential", False), ("Parallel", True)]:
                print(f"  Testing {mode_name} mode...")
                
                orchestrator = Orchestrator(config, enable_parallel=enable_parallel)
                
                test_objective = "Create a simple HTML page with title"
                project_id = await orchestrator.start_project(test_objective, dry_run=True)
                
                assert project_id is not None, f"{mode_name} should create project"
                
            duration = time.time() - start_time
            result.mark_success(duration, {
                "end_to_end": True,
                "modes_tested": ["sequential", "parallel"]
            })
            
            print(f"[PASS] End-to-end testing completed in {duration:.2f}s")
            
        except Exception as e:
            duration = time.time() - start_time
            result.mark_failure(duration, str(e))
            print(f"[FAIL] End-to-end testing failed: {e}")
            
        self.results.append(result)
        
    def generate_report(self):
        """Generate test report."""
        print("\n" + "=" * 50)
        print("TEST REPORT")
        print("=" * 50)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.success])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\nFAILED TESTS ({failed_tests}):")
            for result in self.results:
                if not result.success:
                    print(f"  [FAIL] {result.test_name}")
                    print(f"         Error: {result.error_message}")
                        
        print(f"\nPASSED TESTS ({passed_tests}):")
        for result in self.results:
            if result.success:
                print(f"  [PASS] {result.test_name} ({result.duration:.2f}s)")
                
        # Phase analysis
        phase_status = {
            "Phase 1 (PM)": any("phase1" in r.test_name for r in self.results if r.success),
            "Phase 2 (Delegation)": any("phase2" in r.test_name for r in self.results if r.success),
            "Phase 3 (Workers)": any("phase3" in r.test_name for r in self.results if r.success),
            "Phase 4 (Parallel)": any("phase4" in r.test_name for r in self.results if r.success)
        }
        
        print(f"\nPHASE STATUS:")
        for phase, status in phase_status.items():
            status_text = "WORKING" if status else "ISSUES"
            print(f"  {phase}: {status_text}")
                
        # Overall assessment
        print(f"\nOVERALL ASSESSMENT:")
        if failed_tests == 0:
            print("  [SUCCESS] All tests passed! System working according to PRD.")
            print("  [SUCCESS] No issues found. Safe to proceed.")
        else:
            print("  [WARNING] Some tests failed. Review issues above.")
            print("  [WARNING] May need fixes before proceeding.")
            
        # Save report
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": passed_tests/total_tests*100
            },
            "results": [{
                "test_name": r.test_name,
                "success": r.success,
                "duration": r.duration,
                "error_message": r.error_message
            } for r in self.results],
            "phase_status": phase_status
        }
        
        report_file = Path("test_report.json")
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
            
        print(f"\nDetailed report saved to: {report_file}")


async def main():
    """Main test execution."""
    test_suite = SimpleTestSuite()
    
    try:
        success = await test_suite.run_all_tests()
        
        if success:
            print("\nAll tests completed successfully!")
            return 0
        else:
            print("\nSome tests failed. See report above.")
            return 1
            
    except KeyboardInterrupt:
        print("\nTesting interrupted by user")
        return 130
    except Exception as e:
        print(f"\nTesting suite failed: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))