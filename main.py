#!/usr/bin/env python3
import argparse
import json
import sys
from analyzer.multi_codebase import MultiCodebaseAnalyzer

def main():
    parser = argparse.ArgumentParser(description="Hybrid Code Analysis Tool")
    parser.add_argument("--codebase", help="Path to single codebase")
    parser.add_argument("--codebase-a", help="Path to first codebase for comparison")
    parser.add_argument("--codebase-b", help="Path to second codebase for comparison") 
    parser.add_argument("--question", help="Question about the codebase", default="Analyze this codebase")
    parser.add_argument("--backend", choices=["ollama", "vllm"], default="ollama", help="LLM backend to use")
    parser.add_argument("--output", help="Output file (JSON)")
    parser.add_argument("--merge-analysis", action="store_true", help="Analyze merging two codebases")
    
    args = parser.parse_args()
    
    analyzer = MultiCodebaseAnalyzer(llm_backend=args.backend)
    
    try:
        if args.merge_analysis and args.codebase_a and args.codebase_b:
            result = analyzer.analyze_merge(args.codebase_a, args.codebase_b)
        elif args.codebase_a and args.codebase_b:
            result = analyzer.compare_codebases(args.codebase_a, args.codebase_b, args.question)
        elif args.codebase:
            result = analyzer.analyze_single(args.codebase, args.question)
        else:
            print("Error: Must specify --codebase or both --codebase-a and --codebase-b")
            sys.exit(1)
        
        # Output results
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
            print("="*80)
            
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()