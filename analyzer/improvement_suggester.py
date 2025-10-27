from typing import Dict, Any, List
from .llm_client import LLMClient
import ast
import os

class ImprovementSuggester:
    def __init__(self, llm_backend: str = "ollama"):
        self.llm_client = LLMClient(llm_backend)
    
    def generate_improvements(self, 
                           static_analysis: Dict[str, Any],
                           dynamic_analysis: Dict[str, Any],
                           codebase_path: str) -> Dict[str, Any]:
        """Generate comprehensive improvement suggestions"""
        
        # Categorize issues and generate targeted suggestions
        architectural_suggestions = self._suggest_architectural_improvements(
            static_analysis, dynamic_analysis, codebase_path
        )
        
        performance_suggestions = self._suggest_performance_improvements(
            static_analysis, dynamic_analysis
        )
        
        security_suggestions = self._suggest_security_improvements(
            static_analysis, codebase_path
        )
        
        code_quality_suggestions = self._suggest_code_quality_improvements(
            static_analysis, codebase_path
        )
        
        return {
            "architectural": architectural_suggestions,
            "performance": performance_suggestions,
            "security": security_suggestions,
            "code_quality": code_quality_suggestions,
            "priority_ranking": self._prioritize_improvements(
                architectural_suggestions,
                performance_suggestions,
                security_suggestions,
                code_quality_suggestions
            )
        }
    
    def _suggest_architectural_improvements(self, static: Dict, dynamic: Dict, codebase_path: str) -> List[str]:
        """Suggest architectural refactoring"""
        prompt = f"""
        CODEBASE ARCHITECTURAL ANALYSIS:
        
        Static Analysis: {static.get('summary', {})}
        Dynamic Analysis: {dynamic.get('call_graph', {})}
        Codebase Structure: {self._analyze_codebase_structure(codebase_path)}
        
        Suggest specific architectural improvements focusing on:
        - Modularization and separation of concerns
        - Dependency management and reduction
        - Design pattern applications
        - API design improvements
        - Scalability enhancements
        
        Provide concrete, actionable suggestions:
        """
        
        response = self.llm_client.generate(prompt, max_tokens=1500)
        return self._parse_suggestions_list(response)
    
    def _suggest_performance_improvements(self, static: Dict, dynamic: Dict) -> List[str]:
        """Suggest performance optimizations"""
        prompt = f"""
        PERFORMANCE ANALYSIS:
        
        Static Issues: {static.get('sonarqube', {}).get('issues', [])[:10]}
        Memory Usage: {dynamic.get('memory_profile', {})}
        Execution Complexity: {dynamic.get('call_graph', {}).get('most_complex', [])}
        
        Identify performance bottlenecks and suggest optimizations for:
        - Algorithm improvements
        - Memory usage reduction
        - Execution speed optimization
        - Database/IO performance
        - Caching strategies
        
        Provide specific optimization techniques:
        """
        
        response = self.llm_client.generate(prompt, max_tokens=1200)
        return self._parse_suggestions_list(response)
    
    def _suggest_security_improvements(self, static: Dict, codebase_path: str) -> List[str]:
        """Suggest security hardening"""
        prompt = f"""
        SECURITY ANALYSIS:
        
        Security Issues Found: {[issue for issue in static.get('semgrep', {}).get('results', []) 
                               if 'security' in str(issue).lower()][:10]}
        Code Patterns: {self._analyze_security_patterns(codebase_path)}
        
        Suggest security improvements for:
        - Input validation and sanitization
        - Authentication and authorization
        - Data protection and encryption
        - API security
        - Dependency vulnerabilities
        
        Provide specific security hardening measures:
        """
        
        response = self.llm_client.generate(prompt, max_tokens=1000)
        return self._parse_suggestions_list(response)
    
    def _suggest_code_quality_improvements(self, static: Dict, codebase_path: str) -> List[str]:
        """Suggest code quality enhancements"""
        prompt = f"""
        CODE QUALITY ANALYSIS:
        
        Quality Metrics: {static.get('summary', {}).get('quality_metrics', {})}
        Issues Found: {len(static.get('sonarqube', {}).get('issues', []))}
        Code Structure: {self._analyze_code_quality_metrics(codebase_path)}
        
        Suggest code quality improvements for:
        - Readability and maintainability
        - Testing and test coverage
        - Error handling and robustness
        - Documentation and comments
        - Code duplication reduction
        
        Provide specific refactoring suggestions:
        """
        
        response = self.llm_client.generate(prompt, max_tokens=1000)
        return self._parse_suggestions_list(response)
    
    def _analyze_codebase_structure(self, codebase_path: str) -> Dict[str, Any]:
        """Analyze codebase structure for architectural insights"""
        structure = {
            "module_count": 0,
            "average_file_size": 0,
            "dependency_relationships": 0,
            "entry_points": []
        }
        
        for root, dirs, files in os.walk(codebase_path):
            py_files = [f for f in files if f.endswith('.py')]
            structure["module_count"] += len(py_files)
            
            for file in py_files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        structure["average_file_size"] += len(content)
                        
                        # Simple entry point detection
                        if '__main__' in content or 'if __name__' in content:
                            structure["entry_points"].append(file_path)
                except:
                    pass
        
        if structure["module_count"] > 0:
            structure["average_file_size"] /= structure["module_count"]
        
        return structure
    
    def _analyze_security_patterns(self, codebase_path: str) -> List[str]:
        """Analyze security-related code patterns"""
        security_patterns = []
        
        for root, dirs, files in os.walk(codebase_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read().lower()
                            if any(pattern in content for pattern in 
                                  ['eval(', 'exec(', 'pickle.load', 'yaml.load', 
                                   'subprocess.call', 'os.system', 'input(']):
                                security_patterns.append(f"{file_path}: potential unsafe operation")
                    except:
                        pass
        
        return security_patterns[:10]
    
    def _analyze_code_quality_metrics(self, codebase_path: str) -> Dict[str, Any]:
        """Analyze basic code quality metrics"""
        return {
            "large_files": self._find_large_files(codebase_path),
            "complex_functions": self._find_complex_functions(codebase_path),
            "documentation_coverage": self._estimate_doc_coverage(codebase_path)
        }
    
    def _find_large_files(self, codebase_path: str) -> List[str]:
        """Find unusually large source files"""
        large_files = []
        for root, dirs, files in os.walk(codebase_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    size = os.path.getsize(file_path)
                    if size > 10000:  # 10KB
                        large_files.append(f"{file_path} ({size} bytes)")
        return large_files[:5]
    
    def _find_complex_functions(self, codebase_path: str) -> List[str]:
        """Find potentially complex functions"""
        # Simplified complexity detection
        complex_funcs = []
        for root, dirs, files in os.walk(codebase_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            lines = f.readlines()
                            # Simple heuristic: long functions
                            for i, line in enumerate(lines):
                                if line.strip().startswith('def '):
                                    func_name = line.split('def ')[1].split('(')[0]
                                    # Check function length
                                    j = i + 1
                                    while j < len(lines) and (lines[j].startswith(' ') or lines[j].startswith('\t')):
                                        j += 1
                                    if j - i > 50:  # More than 50 lines
                                        complex_funcs.append(f"{file_path}:{func_name}")
                    except:
                        pass
        return complex_funcs[:10]
    
    def _estimate_doc_coverage(self, codebase_path: str) -> float:
        """Estimate documentation coverage"""
        total_funcs = 0
        documented_funcs = 0
        
        for root, dirs, files in os.walk(codebase_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                            lines = content.split('\n')
                            
                            for i, line in enumerate(lines):
                                if line.strip().startswith('def '):
                                    total_funcs += 1
                                    # Check if previous line is a docstring
                                    if i > 0 and '"""' in lines[i-1]:
                                        documented_funcs += 1
                    except:
                        pass
        
        return documented_funcs / total_funcs if total_funcs > 0 else 0
    
    def _parse_suggestions_list(self, llm_response: str) -> List[str]:
        """Parse LLM response into structured suggestions list"""
        suggestions = []
        lines = llm_response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or 
                        (len(line) > 10 and any(c.isdigit() for c in line[:3]))):
                # Clean up the suggestion
                clean_suggestion = line.lstrip('-• ').lstrip('1234567890. ')
                if len(clean_suggestion) > 20:  # Meaningful suggestion
                    suggestions.append(clean_suggestion)
        
        return suggestions[:15]  # Limit to top 15 suggestions
    
    def _prioritize_improvements(self, *suggestion_categories) -> List[Dict[str, Any]]:
        """Prioritize improvements based on impact and effort"""
        all_suggestions = []
        
        for category, suggestions in zip(
            ['architectural', 'performance', 'security', 'code_quality'],
            suggestion_categories
        ):
            for i, suggestion in enumerate(suggestions):
                # Simple prioritization heuristic
                if 'security' in category:
                    priority = 'HIGH'
                elif 'performance' in category and 'bottleneck' in suggestion.lower():
                    priority = 'HIGH'
                elif 'architectural' in category:
                    priority = 'MEDIUM'
                else:
                    priority = 'LOW'
                
                all_suggestions.append({
                    'suggestion': suggestion,
                    'category': category,
                    'priority': priority,
                    'estimated_effort': self._estimate_effort(suggestion)
                })
        
        # Sort by priority and effort
        return sorted(all_suggestions, 
                     key=lambda x: (x['priority'] != 'HIGH', x['estimated_effort']))
    
    def _estimate_effort(self, suggestion: str) -> str:
        """Estimate implementation effort for a suggestion"""
        suggestion_lower = suggestion.lower()
        
        if any(word in suggestion_lower for word in ['refactor', 'rewrite', 'redesign']):
            return 'HIGH'
        elif any(word in suggestion_lower for word in ['add', 'implement', 'create']):
            return 'MEDIUM'
        elif any(word in suggestion_lower for word in ['update', 'improve', 'enhance']):
            return 'LOW'
        else:
            return 'MEDIUM'