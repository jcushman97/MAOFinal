"""
Intelligent Model Router for MAOS Phase 5

Advanced routing system that selects optimal LLM models based on:
- Task type and complexity
- Model strengths and capabilities
- Fallback mechanisms for reliability
- Load balancing across providers
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from pathlib import Path

from core.config import Config
from core.state import Task, TaskStatus

logger = logging.getLogger(__name__)


class ModelCapability(Enum):
    """Model capability categories."""
    CODING = "coding"
    REASONING = "reasoning"
    RESEARCH = "research"
    CREATIVE = "creative"
    ANALYSIS = "analysis"
    DOCUMENTATION = "documentation"


@dataclass
class ModelProfile:
    """Profile describing a model's strengths and characteristics."""
    name: str
    capabilities: Dict[ModelCapability, float]  # 0.0-1.0 strength ratings
    cost_factor: float  # Relative cost (1.0 = baseline)
    speed_factor: float  # Relative speed (1.0 = baseline)
    reliability: float  # Success rate (0.0-1.0)
    max_context: int  # Maximum context window
    available: bool = True


class IntelligentModelRouter:
    """
    Advanced model routing system for MAOS Phase 5.
    
    Implements intelligent model selection based on task characteristics,
    model capabilities, and system performance metrics.
    """
    
    def __init__(self, config: Config):
        """Initialize the model router."""
        self.config = config
        self.model_profiles = self._initialize_model_profiles()
        self.usage_stats = {}  # Track model usage and performance
        self.fallback_chains = self._create_fallback_chains()
        
    def _initialize_model_profiles(self) -> Dict[str, ModelProfile]:
        """Initialize model capability profiles."""
        return {
            "claude": ModelProfile(
                name="claude",
                capabilities={
                    ModelCapability.CODING: 0.95,
                    ModelCapability.REASONING: 0.90,
                    ModelCapability.RESEARCH: 0.85,
                    ModelCapability.CREATIVE: 0.80,
                    ModelCapability.ANALYSIS: 0.90,
                    ModelCapability.DOCUMENTATION: 0.85
                },
                cost_factor=1.0,
                speed_factor=1.0,
                reliability=0.95,
                max_context=200000,
                available=True
            ),
            "gpt": ModelProfile(
                name="gpt",
                capabilities={
                    ModelCapability.CODING: 0.85,
                    ModelCapability.REASONING: 0.85,
                    ModelCapability.RESEARCH: 0.80,
                    ModelCapability.CREATIVE: 0.90,
                    ModelCapability.ANALYSIS: 0.80,
                    ModelCapability.DOCUMENTATION: 0.90
                },
                cost_factor=1.2,
                speed_factor=0.9,
                reliability=0.90,
                max_context=128000,
                available=self._check_model_availability("gpt")
            ),
            "gemini": ModelProfile(
                name="gemini",
                capabilities={
                    ModelCapability.CODING: 0.80,
                    ModelCapability.REASONING: 0.85,
                    ModelCapability.RESEARCH: 0.95,
                    ModelCapability.CREATIVE: 0.85,
                    ModelCapability.ANALYSIS: 0.90,
                    ModelCapability.DOCUMENTATION: 0.80
                },
                cost_factor=0.8,
                speed_factor=1.1,
                reliability=0.88,
                max_context=1000000,
                available=self._check_model_availability("gemini")
            )
        }
    
    def _check_model_availability(self, model_name: str) -> bool:
        """Check if a model is available and configured."""
        provider_config = self.config.get_provider_config(model_name)
        return provider_config is not None
    
    def _create_fallback_chains(self) -> Dict[str, List[str]]:
        """Create fallback chains for each model."""
        return {
            "claude": ["gpt", "gemini"],
            "gpt": ["claude", "gemini"], 
            "gemini": ["claude", "gpt"]
        }
    
    def select_model_for_task(
        self, 
        task: Task, 
        preferred_model: Optional[str] = None,
        exclude_models: Optional[List[str]] = None
    ) -> Tuple[str, float]:
        """
        Select the optimal model for a given task.
        
        Args:
            task: Task to execute
            preferred_model: User's preferred model (if any)
            exclude_models: Models to exclude from selection
            
        Returns:
            Tuple of (model_name, confidence_score)
        """
        if exclude_models is None:
            exclude_models = []
            
        # Use preferred model if specified and available
        if preferred_model and preferred_model not in exclude_models:
            if self._is_model_available(preferred_model):
                confidence = self._calculate_model_fitness(preferred_model, task)
                return preferred_model, confidence
        
        # Get task requirements
        task_capabilities = self._analyze_task_requirements(task)
        
        # Score all available models
        model_scores = {}
        for model_name, profile in self.model_profiles.items():
            if model_name in exclude_models or not profile.available:
                continue
                
            score = self._score_model_for_task(profile, task, task_capabilities)
            model_scores[model_name] = score
        
        # Select best model
        if not model_scores:
            # Fallback to default routing if no models available
            default_model = self.config.get_provider_for_task(task.team or "general")
            return default_model, 0.5
            
        best_model = max(model_scores.items(), key=lambda x: x[1])
        return best_model[0], best_model[1]
    
    def _analyze_task_requirements(self, task: Task) -> Dict[ModelCapability, float]:
        """Analyze task requirements to determine needed capabilities."""
        requirements = {cap: 0.0 for cap in ModelCapability}
        
        description = (task.description or "").lower()
        team = (task.team or "").lower()
        
        # Analyze based on team assignment
        if team in ["frontend", "backend", "python"]:
            requirements[ModelCapability.CODING] = 0.9
            requirements[ModelCapability.ANALYSIS] = 0.7
        elif team == "qa":
            requirements[ModelCapability.ANALYSIS] = 0.9
            requirements[ModelCapability.REASONING] = 0.8
        elif team == "research":
            requirements[ModelCapability.RESEARCH] = 0.9
            requirements[ModelCapability.ANALYSIS] = 0.7
        
        # Analyze based on description keywords
        coding_keywords = ["code", "implement", "function", "class", "api", "debug"]
        research_keywords = ["research", "analyze", "investigate", "study", "explore"]
        creative_keywords = ["design", "create", "generate", "brainstorm", "innovative"]
        docs_keywords = ["document", "write", "explain", "describe", "manual"]
        
        for keyword in coding_keywords:
            if keyword in description:
                requirements[ModelCapability.CODING] = max(
                    requirements[ModelCapability.CODING], 0.8
                )
        
        for keyword in research_keywords:
            if keyword in description:
                requirements[ModelCapability.RESEARCH] = max(
                    requirements[ModelCapability.RESEARCH], 0.8
                )
        
        for keyword in creative_keywords:
            if keyword in description:
                requirements[ModelCapability.CREATIVE] = max(
                    requirements[ModelCapability.CREATIVE], 0.8
                )
                
        for keyword in docs_keywords:
            if keyword in description:
                requirements[ModelCapability.DOCUMENTATION] = max(
                    requirements[ModelCapability.DOCUMENTATION], 0.8
                )
        
        # Default reasoning requirement
        if max(requirements.values()) < 0.5:
            requirements[ModelCapability.REASONING] = 0.7
            
        return requirements
    
    def _score_model_for_task(
        self, 
        profile: ModelProfile, 
        task: Task,
        requirements: Dict[ModelCapability, float]
    ) -> float:
        """Score a model's fitness for a specific task."""
        
        # Base capability score
        capability_score = 0.0
        total_weight = 0.0
        
        for capability, requirement in requirements.items():
            if requirement > 0:
                model_strength = profile.capabilities.get(capability, 0.0)
                weighted_score = model_strength * requirement
                capability_score += weighted_score
                total_weight += requirement
        
        if total_weight > 0:
            capability_score = capability_score / total_weight
        
        # Apply modifiers
        reliability_modifier = profile.reliability
        speed_modifier = min(profile.speed_factor, 2.0) / 2.0  # Normalize to 0-1
        cost_modifier = max(2.0 - profile.cost_factor, 0.0) / 2.0  # Lower cost = higher score
        
        # Historical performance modifier
        history_modifier = self._get_historical_performance(profile.name, task.team)
        
        # Combine scores with weights
        final_score = (
            capability_score * 0.6 +
            reliability_modifier * 0.2 +
            speed_modifier * 0.1 +
            cost_modifier * 0.05 +
            history_modifier * 0.05
        )
        
        return min(final_score, 1.0)
    
    def _get_historical_performance(self, model_name: str, team: str) -> float:
        """Get historical performance score for a model on specific team tasks."""
        key = f"{model_name}_{team}"
        if key in self.usage_stats:
            stats = self.usage_stats[key]
            success_rate = stats.get("success_rate", 0.9)
            return success_rate
        return 0.9  # Default to good performance for new combinations
    
    def _calculate_model_fitness(self, model_name: str, task: Task) -> float:
        """Calculate fitness score for a specific model and task."""
        profile = self.model_profiles.get(model_name)
        if not profile:
            return 0.0
            
        requirements = self._analyze_task_requirements(task)
        return self._score_model_for_task(profile, task, requirements)
    
    def _is_model_available(self, model_name: str) -> bool:
        """Check if a model is currently available."""
        profile = self.model_profiles.get(model_name)
        return profile is not None and profile.available
    
    def get_fallback_model(self, failed_model: str, task: Task) -> Optional[str]:
        """Get fallback model when primary model fails."""
        fallback_chain = self.fallback_chains.get(failed_model, [])
        
        for fallback_model in fallback_chain:
            if self._is_model_available(fallback_model):
                return fallback_model
                
        return None
    
    def update_model_performance(
        self, 
        model_name: str, 
        task: Task, 
        success: bool,
        response_time: float = 0.0
    ):
        """Update model performance statistics."""
        key = f"{model_name}_{task.team}"
        
        if key not in self.usage_stats:
            self.usage_stats[key] = {
                "total_calls": 0,
                "successful_calls": 0,
                "avg_response_time": 0.0,
                "success_rate": 0.9
            }
        
        stats = self.usage_stats[key]
        stats["total_calls"] += 1
        
        if success:
            stats["successful_calls"] += 1
            
        stats["success_rate"] = stats["successful_calls"] / stats["total_calls"]
        
        # Update response time with exponential moving average
        if response_time > 0:
            if stats["avg_response_time"] == 0:
                stats["avg_response_time"] = response_time
            else:
                alpha = 0.1  # Smoothing factor
                stats["avg_response_time"] = (
                    alpha * response_time + 
                    (1 - alpha) * stats["avg_response_time"]
                )
    
    def get_model_recommendations(self, task_type: str) -> List[Tuple[str, float]]:
        """Get ranked model recommendations for a task type."""
        # Create a dummy task for analysis
        dummy_task = Task(
            id="dummy",
            description=f"Task of type {task_type}",
            team=task_type,
            status=TaskStatus.QUEUED,
            dependencies=[],
            subtasks=[],
            artifacts=[],
            attempts=0
        )
        
        recommendations = []
        for model_name in self.model_profiles.keys():
            if self._is_model_available(model_name):
                score = self._calculate_model_fitness(model_name, dummy_task)
                recommendations.append((model_name, score))
        
        # Sort by score descending
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations
    
    def save_stats(self, filepath: Path):
        """Save usage statistics to file."""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.usage_stats, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save model router stats: {e}")
    
    def load_stats(self, filepath: Path):
        """Load usage statistics from file."""
        try:
            if filepath.exists():
                with open(filepath, 'r') as f:
                    self.usage_stats = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load model router stats: {e}")
            self.usage_stats = {}