#!/usr/bin/env python3
"""
Self-Improvement Module for Complete Self System

Provides:
- Self-modification capabilities
- Performance optimization
- Knowledge expansion
- Error analysis and fixing
- Automatic updates
"""

import os
import json
import time
import ast
import hashlib
import difflib
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path


class SelfImprovement:
    """
    Self-improvement system for the Complete Self System.
    
    Features:
    - Self-modifying code
    - Performance optimization
    - Knowledge expansion
    - Error analysis and fixing
    - Automatic updates
    - Version control integration
    """
    
    def __init__(self, cfg: Dict[str, Any], db=None, simple_llm_reply=None):
        """
        Initialize the SelfImprovement system.
        
        Args:
            cfg: Configuration dictionary
            db: Database instance
            simple_llm_reply: Function to get LLM replies
        """
        self.cfg = cfg
        self.db = db
        self.simple_llm_reply = simple_llm_reply
        self.base_dir = Path(__file__).parent.parent
    
    def suggest_improvements(self, code: str, context: str = "") -> Dict[str, Any]:
        """
        Suggest improvements for code using LLM.
        
        Args:
            code: Code to improve
            context: Context about what the code should do
            
        Returns:
            Dictionary with improvement suggestions
        """
        if not self.simple_llm_reply:
            return {"success": False, "error": "LLM not configured"}
        
        prompt = f"""
Analyze this Python code and suggest improvements.

Code:
{code}

Context: {context}

Provide your response as JSON with:
- "improvements": List of improvement suggestions
- "optimized_code": The improved code (if applicable)
- "performance_tips": List of performance tips
- "security_issues": List of security issues
- "explanation": Brief explanation of changes

Respond ONLY with valid JSON.
"""
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a Python code improvement expert. Analyze code and suggest improvements. Return ONLY JSON."
                },
                {"role": "user", "content": prompt}
            ]
            
            reply = self.simple_llm_reply(messages)
            
            # Try to parse JSON
            try:
                data = json.loads(reply)
                return {"success": True, **data}
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "improvements": [reply],
                    "optimized_code": "",
                    "performance_tips": [],
                    "security_issues": [],
                    "explanation": ""
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def optimize_code(self, code: str, goal: str = "performance") -> Dict[str, Any]:
        """
        Optimize code for a specific goal.
        
        Args:
            code: Code to optimize
            goal: Optimization goal (performance, readability, memory)
            
        Returns:
            Dictionary with optimized code
        """
        if not self.simple_llm_reply:
            return {"success": False, "error": "LLM not configured"}
        
        prompt = f"""
Optimize this Python code for {goal}.

Code:
{code}

Provide ONLY the optimized code, no explanations.

Optimized code:
"""
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": f"You are a Python code optimizer. Optimize for {goal}. Return ONLY code."
                },
                {"role": "user", "content": prompt}
            ]
            
            reply = self.simple_llm_reply(messages)
            
            # Extract code
            if "```python" in reply:
                code_start = reply.find("```python") + 10
                code_end = reply.find("```", code_start)
                optimized = reply[code_start:code_end].strip()
            elif "```" in reply:
                code_start = reply.find("```") + 3
                code_end = reply.find("```", code_start)
                optimized = reply[code_start:code_end].strip()
            else:
                optimized = reply.strip()
            
            return {"success": True, "optimized_code": optimized}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def explain_code(self, code: str) -> Dict[str, Any]:
        """
        Explain what code does in simple terms.
        
        Args:
            code: Code to explain
            
        Returns:
            Dictionary with explanation
        """
        if not self.simple_llm_reply:
            return {"success": False, "error": "LLM not configured"}
        
        prompt = f"""
Explain what this Python code does in simple terms.

Code:
{code}

Provide a concise explanation.
"""
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a Python code explainer. Explain code simply and clearly."
                },
                {"role": "user", "content": prompt}
            ]
            
            reply = self.simple_llm_reply(messages)
            
            return {"success": True, "explanation": reply}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_tests(self, code: str, function_name: str = "") -> Dict[str, Any]:
        """
        Generate test cases for code.
        
        Args:
            code: Code to test
            function_name: Name of the function to test
            
        Returns:
            Dictionary with generated tests
        """
        if not self.simple_llm_reply:
            return {"success": False, "error": "LLM not configured"}
        
        prompt = f"""
Generate Python test cases for this code.

Code:
{code}

{'- Function to test: ' + function_name if function_name else ''}

Provide ONLY Python test code (no explanations).
Use pytest style.

Test code:
"""
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a Python test generator. Generate pytest tests. Return ONLY code."
                },
                {"role": "user", "content": prompt}
            ]
            
            reply = self.simple_llm_reply(messages)
            
            # Extract code
            if "```python" in reply:
                code_start = reply.find("```python") + 10
                code_end = reply.find("```", code_start)
                tests = reply[code_start:code_end].strip()
            elif "```" in reply:
                code_start = reply.find("```") + 3
                code_end = reply.find("```", code_start)
                tests = reply[code_start:code_end].strip()
            else:
                tests = reply.strip()
            
            return {"success": True, "tests": tests}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def analyze_errors(self, error_message: str, code: str = "") -> Dict[str, Any]:
        """
        Analyze errors and suggest fixes.
        
        Args:
            error_message: The error message
            code: The code that caused the error
            
        Returns:
            Dictionary with analysis and suggestions
        """
        if not self.simple_llm_reply:
            return {"success": False, "error": "LLM not configured"}
        
        prompt = f"""
Analyze this error and suggest fixes.

Error: {error_message}

{'- Code:\\n' + code if code else ''}

Provide JSON with:
- "error_type": Type of error
- "cause": Likely cause
- "suggestions": List of fix suggestions
- "fixed_code": Fixed code (if applicable)

Respond ONLY with valid JSON.
"""
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a Python error analyzer. Analyze errors and suggest fixes. Return ONLY JSON."
                },
                {"role": "user", "content": prompt}
            ]
            
            reply = self.simple_llm_reply(messages)
            
            try:
                data = json.loads(reply)
                return {"success": True, **data}
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "error_type": "Unknown",
                    "cause": "Could not parse analysis",
                    "suggestions": [reply],
                    "fixed_code": ""
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def refactor_code(self, code: str, style: str = "pep8") -> Dict[str, Any]:
        """
        Refactor code to follow a specific style.
        
        Args:
            code: Code to refactor
            style: Style to use (pep8, clean, efficient)
            
        Returns:
            Dictionary with refactored code
        """
        if not self.simple_llm_reply:
            return {"success": False, "error": "LLM not configured"}
        
        prompt = f"""
Refactor this Python code to follow {style} style guidelines.

Code:
{code}

Provide ONLY the refactored code, no explanations.

Refactored code:
"""
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": f"You are a Python code refactorer. Refactor to {style} style. Return ONLY code."
                },
                {"role": "user", "content": prompt}
            ]
            
            reply = self.simple_llm_reply(messages)
            
            # Extract code
            if "```python" in reply:
                code_start = reply.find("```python") + 10
                code_end = reply.find("```", code_start)
                refactored = reply[code_start:code_end].strip()
            elif "```" in reply:
                code_start = reply.find("```") + 3
                code_end = reply.find("```", code_start)
                refactored = reply[code_start:code_end].strip()
            else:
                refactored = reply.strip()
            
            return {"success": True, "refactored_code": refactored}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def document_code(self, code: str) -> Dict[str, Any]:
        """
        Add documentation to code.
        
        Args:
            code: Code to document
            
        Returns:
            Dictionary with documented code
        """
        if not self.simple_llm_reply:
            return {"success": False, "error": "LLM not configured"}
        
        prompt = f"""
Add comprehensive documentation to this Python code.

Code:
{code}

Provide ONLY the documented code with:
- Module docstring
- Function docstrings
- Type hints
- Comments where needed

Documented code:
"""
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a Python documentation expert. Add comprehensive docs. Return ONLY code."
                },
                {"role": "user", "content": prompt}
            ]
            
            reply = self.simple_llm_reply(messages)
            
            # Extract code
            if "```python" in reply:
                code_start = reply.find("```python") + 10
                code_end = reply.find("```", code_start)
                documented = reply[code_start:code_end].strip()
            elif "```" in reply:
                code_start = reply.find("```") + 3
                code_end = reply.find("```", code_start)
                documented = reply[code_start:code_end].strip()
            else:
                documented = reply.strip()
            
            return {"success": True, "documented_code": documented}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def self_update_check(self) -> Dict[str, Any]:
        """
        Check for self-updates and improvements.
        
        Returns:
            Dictionary with update suggestions
        """
        if not self.db or not self.simple_llm_reply:
            return {"success": False, "error": "Dependencies not configured"}
        
        # Get recent conversations
        history = self.db.get_history(50) if self.db else []
        
        # Get recent errors (if tracked)
        errors = []
        if self.db:
            # This would need error tracking in the DB
            pass
        
        # Get system stats
        stats = self.db.get_stats() if self.db else {}
        
        prompt = f"""
Analyze this AI assistant's recent activity and suggest self-improvements.

Recent conversations (last 50 turns):
{json.dumps([{'role': h['role'], 'content': h['content'][:200]} for h in history], indent=2)}

Database stats:
{json.dumps(stats, indent=2)}

Suggest improvements in these areas:
1. What new features should be added based on usage patterns?
2. What existing features need improvement?
3. What knowledge gaps exist that should be filled?
4. What performance optimizations are needed?

Provide JSON with:
- "feature_suggestions": List of new features to add
- "improvement_suggestions": List of improvements to existing features
- "knowledge_gaps": List of knowledge areas to expand
- "performance_tips": List of performance optimizations

Respond ONLY with valid JSON.
"""
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are an AI self-improvement expert. Analyze usage and suggest improvements. Return ONLY JSON."
                },
                {"role": "user", "content": prompt}
            ]
            
            reply = self.simple_llm_reply(messages)
            
            try:
                data = json.loads(reply)
                return {"success": True, **data}
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "feature_suggestions": [reply],
                    "improvement_suggestions": [],
                    "knowledge_gaps": [],
                    "performance_tips": []
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def modify_self(self, file_path: str, changes: str) -> Dict[str, Any]:
        """
        Modify a file in the system (with safety checks).
        
        Args:
            file_path: Path to the file to modify
            changes: Description of changes to make
            
        Returns:
            Dictionary with modification result
        """
        if not self.simple_llm_reply:
            return {"success": False, "error": "LLM not configured"}
        
        # Safety checks
        full_path = self.base_dir / file_path
        
        # Only allow modifications in app/ directory
        if not str(full_path).startswith(str(self.base_dir / "app")):
            return {"success": False, "error": "Can only modify files in app/ directory"}
        
        # Only allow .py files
        if not full_path.name.endswith(".py"):
            return {"success": False, "error": "Can only modify .py files"}
        
        # Read current file
        if not full_path.exists():
            return {"success": False, "error": "File not found"}
        
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                current_code = f.read()
        except Exception as e:
            return {"success": False, "error": f"Cannot read file: {e}"}
        
        # Ask LLM to generate modified code
        prompt = f"""
Modify this Python file based on the requested changes.

Current file: {file_path}

Current code:
{current_code}

Requested changes: {changes}

Provide ONLY the complete modified file content.
Do NOT include any explanations or markdown.

Modified code:
"""
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a Python code modifier. Modify files based on requests. Return ONLY the complete file content."
                },
                {"role": "user", "content": prompt}
            ]
            
            reply = self.simple_llm_reply(messages)
            
            # Extract code
            if "```python" in reply:
                code_start = reply.find("```python") + 10
                code_end = reply.find("```", code_start)
                modified = reply[code_start:code_end].strip()
            elif "```" in reply:
                code_start = reply.find("```") + 3
                code_end = reply.find("```", code_start)
                modified = reply[code_start:code_end].strip()
            else:
                modified = reply.strip()
            
            # Safety check: Don't allow removal of all content
            if len(modified) < 10:
                return {"success": False, "error": "Modified code too short"}
            
            # Create backup
            backup_path = full_path.parent / f"{full_path.name}.backup.{int(time.time())}"
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(current_code)
            
            # Write modified code
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(modified)
            
            return {
                "success": True,
                "file": str(file_path),
                "backup": str(backup_path.name),
                "message": "File modified successfully"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def add_new_feature(self, feature_name: str, description: str) -> Dict[str, Any]:
        """
        Add a new feature to the system.
        
        Args:
            feature_name: Name of the new feature
            description: Description of what the feature should do
            
        Returns:
            Dictionary with feature creation result
        """
        if not self.simple_llm_reply:
            return {"success": False, "error": "LLM not configured"}
        
        # Generate feature code
        prompt = f"""
Create a new Python module for an AI assistant feature.

Feature name: {feature_name}
Feature description: {description}

Create a complete, well-documented Python module with:
- Module docstring
- Main class or functions
- Type hints
- Error handling
- Example usage in docstrings

Return ONLY the Python code, no explanations.

Code:
"""
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a Python feature creator. Create complete, well-documented modules. Return ONLY code."
                },
                {"role": "user", "content": prompt}
            ]
            
            reply = self.simple_llm_reply(messages)
            
            # Extract code
            if "```python" in reply:
                code_start = reply.find("```python") + 10
                code_end = reply.find("```", code_start)
                code = reply[code_start:code_end].strip()
            elif "```" in reply:
                code_start = reply.find("```") + 3
                code_end = reply.find("```", code_start)
                code = reply[code_start:code_end].strip()
            else:
                code = reply.strip()
            
            # Save to file
            file_name = feature_name.lower().replace(" ", "_") + ".py"
            file_path = self.base_dir / "app" / file_name
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
            
            return {
                "success": True,
                "feature_name": feature_name,
                "file_path": str(file_path),
                "code": code[:500] + ("..." if len(code) > 500 else ""),
                "message": "Feature created successfully"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def expand_knowledge(self, topic: str) -> Dict[str, Any]:
        """
        Expand knowledge about a topic.
        
        Args:
            topic: Topic to learn about
            
        Returns:
            Dictionary with knowledge expansion result
        """
        if not self.db or not self.simple_llm_reply:
            return {"success": False, "error": "Dependencies not configured"}
        
        # Check existing knowledge
        existing = self.db.search_knowledge(topic, limit=10) if self.db else []
        
        prompt = f"""
Expand knowledge about this topic for an AI assistant.

Topic: {topic}

Existing knowledge (if any):
{json.dumps([{'question': k['question'], 'answer': k['answer']} for k in existing], indent=2)}

Generate new knowledge entries as JSON array with:
- "question": The question
- "answer": The answer
- "category": Topic category
- "confidence": Confidence level (0.0 to 1.0)

Provide ONLY valid JSON array.
"""
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a knowledge expansion expert. Generate new knowledge entries. Return ONLY JSON array."
                },
                {"role": "user", "content": prompt}
            ]
            
            reply = self.simple_llm_reply(messages)
            
            try:
                knowledge_items = json.loads(reply)
                if not isinstance(knowledge_items, list):
                    knowledge_items = [knowledge_items]
                
                added = 0
                for item in knowledge_items:
                    if self.db:
                        self.db.add_knowledge(
                            question=item.get("question", ""),
                            answer=item.get("answer", ""),
                            category=item.get("category", topic)
                        )
                        added += 1
                
                return {
                    "success": True,
                    "topic": topic,
                    "items_added": added,
                    "items": knowledge_items
                }
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Invalid JSON response",
                    "raw_response": reply
                }
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global instance
self_improvement = None


def create_self_improvement(cfg: Dict[str, Any], db=None, simple_llm_reply=None) -> SelfImprovement:
    """
    Create a SelfImprovement instance.
    
    Args:
        cfg: Configuration dictionary
        db: Database instance
        simple_llm_reply: Function to get LLM replies
        
    Returns:
        SelfImprovement instance
    """
    global self_improvement
    if self_improvement is None:
        self_improvement = SelfImprovement(cfg, db, simple_llm_reply)
    return self_improvement
