#!/usr/bin/env python3
import argparse
import json
import sys
import warnings
import os
from typing import Dict, Any
from analyzer.multi_codebase import MultiCodebaseAnalyzer
from analyzer.analysis_storage import AnalysisStorage
from analyzer.improvement_suggester import ImprovementSuggester

# Suppress warnings at the very beginning
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import logging
logging.getLogger('faiss').setLevel(logging.ERROR)
logging.getLogger('faiss.loader').setLevel(logging.ERROR)

def process_discovery_artifacts(result: Dict[str, Any], args):
    """Process and output discovery artifacts"""
    
    # Check if discovery artifacts are present
    if "discovery_artifacts" in result:
        artifacts = result["discovery_artifacts"]
        
        # Print console summary if requested
        if args.discovery_summary:
            print("\n" + "="*80)
            print("DISCOVERY SUMMARY")
            print("="*80)
            
            # Print static discovery summary
            if artifacts.get("static"):
                print("\nStatic Analysis Discovery:")
                from analyzer.discovery_artifact import DiscoveryArtifactGenerator
                generator = DiscoveryArtifactGenerator()
                summary = generator.generate_console_summary(artifacts["static"])
                print(summary)
            
            # Print dynamic discovery summary
            if artifacts.get("dynamic"):
                print("\nDynamic Analysis Discovery:")
                from analyzer.discovery_artifact import DiscoveryArtifactGenerator
                generator = DiscoveryArtifactGenerator()
                summary = generator.generate_console_summary(artifacts["dynamic"])
                print(summary)
        
        # Save discovery artifact to file if requested
        if args.discovery_output:
            try:
                import json
                with open(args.discovery_output, 'w') as f:
                    json.dump(artifacts, f, indent=2)
                print(f"\nDiscovery artifacts saved to {args.discovery_output}")
            except Exception as e:
                print(f"Warning: Failed to save discovery artifacts: {str(e)}")

def process_result(result: Dict[str, Any], args):
    """Process and output analysis results"""
    
    # Process discovery artifacts first
    process_discovery_artifacts(result, args)
    
    # Output main results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print("\n" + "="*80)
        if "llm_analysis" in result:
            print("ANALYSIS RESULT:")
            print(result["llm_analysis"])
        elif "comparison_analysis" in result:
            print("COMPARISON RESULT:")  
            print(result["comparison_analysis"])
        elif "multi_path_analysis" in result:
            print("MULTI-PATH ANALYSIS RESULT:")
            print(f"Analyzed {result['path_count']} codebase paths")
            for i, path in enumerate(result['paths_analyzed']):
                print(f"  Path {i+1}: {path}")
        print("="*80)

    # Save analysis to storage after ensuring all analysis results are in proper format
    if not isinstance(result, dict):
        print("Warning: Analysis result is not a dictionary. Cannot save to database.")
        return
    
    # Proceed with saving if the result is a dictionary
    storage = AnalysisStorage()
    storage.save_full_analysis(result)
    print("Analysis saved to database.")

    # Suggest improvements if single codebase analysis
    if "static_analysis" in result and "dynamic_analysis" in result:
        user_input = input("Do you want to suggest improvements based on the analysis? (yes/no): ").lower()
        if user_input == 'yes':
            suggester = ImprovementSuggester(llm_backend=args.backend)
            improvements = suggester.suggest_improvements(result)
            if improvements and improvements.strip():
                print("\nSuggested Improvements:\n", improvements)
            else:
                print("No improvements suggested.")
    
    print("\nAnalysis complete.")

def main():
    parser = argparse.ArgumentParser(description="Hybrid Code Analysis Tool")
    
    # Add support for multiple root paths
    parser.add_argument("--root-paths", nargs='+', 
                       help="Multiple root paths for analysis (space-separated)")
    
    # Keep existing single codebase argument for backward compatibility
    parser.add_argument("--codebase", help="Path to single codebase")
    
    # Add discovery reporting options
    parser.add_argument("--discovery-output", 
                       help="Output file for discovery artifact (JSON)")
    parser.add_argument("--discovery-summary", 
                       action="store_true", 
                       help="Print discovery summary to console")
    
    # Rest of existing arguments remain unchanged
    parser.add_argument("--codebase-a", help="Path to first codebase for comparison")
    parser.add_argument("--codebase-b", help="Path to second codebase for comparison") 
    parser.add_argument("--question", help="Question about the codebase", 
                       default="Analyze this codebase")
    parser.add_argument("--backend", choices=["ollama", "vllm"], default="ollama", 
                       help="LLM backend to use")
    parser.add_argument("--output", help="Output file (JSON)")
    parser.add_argument("--merge-analysis", action="store_true", 
                       help="Analyze merging two codebases")

    args = parser.parse_args()

    analyzer = MultiCodebaseAnalyzer(llm_backend=args.backend)

    try:
        # Handle multiple root paths vs single codebase
        if args.root_paths:
            # Use multiple root paths
            codebase_paths = args.root_paths
        elif args.codebase:
            # Use single codebase (backward compatibility)
            codebase_paths = [args.codebase]
        else:
            # Check for comparison/merge scenarios
            if args.merge_analysis and args.codebase_a and args.codebase_b:
                result = analyzer.analyze_merge(args.codebase_a, args.codebase_b)
            elif args.codebase_a and args.codebase_b:
                result = analyzer.compare_codebases(args.codebase_a, args.codebase_b, args.question)
            else:
                print("Error: Must specify --codebase, --root-paths, or both --codebase-a and --codebase-b")
                sys.exit(1)
            
            # Skip the rest of single codebase processing
            return process_result(result, args)
        
        # For single codebase analysis with potential multiple root paths
        if len(codebase_paths) == 1:
            # Single codebase path
            result = analyzer.analyze_single(codebase_paths[0], args.question)
        else:
            # Multiple root paths - we need to handle this case
            # For now, we'll analyze each path separately and aggregate results
            # This is a simplified approach; a more sophisticated multi-path analyzer could be implemented
            results = []
            for codebase_path in codebase_paths:
                results.append(analyzer.analyze_single(codebase_path, args.question))
            
            # Aggregate results (simple approach)
            result = {
                "multi_path_analysis": True,
                "individual_results": results,
                "path_count": len(codebase_paths),
                "paths_analyzed": codebase_paths
            }
        
        process_result(result, args)
        
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
