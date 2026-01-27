#!/usr/bin/env python3
"""
Target Project Verification Script
Verifies existence, accessibility, and basic structure of target projects
"""

import os
import json
from datetime import datetime

def verify_project(project_path):
    """Verify a single project's existence, permissions, and structure"""
    result = {
        'path': project_path,
        'exists': False,
        'readable': False,
        'writable': False,
        'structure': [],
        'error': None
    }
    
    try:
        # Check if project exists
        if os.path.exists(project_path):
            result['exists'] = True
            
            # Check read permissions
            if os.access(project_path, os.R_OK):
                result['readable'] = True
                
                # Check write permissions
                if os.access(project_path, os.W_OK):
                    result['writable'] = True
                
                # List basic structure
                try:
                    items = os.listdir(project_path)
                    result['structure'] = sorted(items)
                except PermissionError as e:
                    result['error'] = f"Permission denied listing contents: {str(e)}"
                    
            else:
                result['error'] = "Read permission denied"
        else:
            result['error'] = "Project path does not exist"
            
    except Exception as e:
        result['error'] = f"Unexpected error: {str(e)}"
        
    return result

def generate_verification_report():
    """Generate verification report for target projects"""
    
    # Define target projects
    target_projects = [
        r'C:\Users\vsharma.A123SYSTEMSEU\Documents\Python_Scripts\AI\Codebase_Indexer',
        r'C:\Users\vsharma.A123SYSTEMSEU\Documents\Python_Scripts\AI\chatroom\src\core'
    ]
    
    # Current project for reference
    current_project = r'c:\Users\vsharma.A123SYSTEMSEU\Documents\Python_Scripts\AI\hybrid_code_analyser'
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'current_project': current_project,
        'target_projects': {},
        'summary': {}
    }
    
    # Verify each target project
    for project_path in target_projects:
        project_name = os.path.basename(project_path.rstrip('\/'))
        report['target_projects'][project_name] = verify_project(project_path)
    
    # Generate summary
    accessible_projects = [
        name for name, data in report['target_projects'].items() 
        if data['exists'] and data['readable']
    ]
    
    report['summary'] = {
        'total_projects': len(target_projects),
        'accessible_projects': len(accessible_projects),
        'accessible_project_names': accessible_projects,
        'verification_status': 'SUCCESS' if accessible_projects else 'PARTIAL'
    }
    
    return report

def save_report(report, filename='target_projects_verification_report.json'):
    """Save verification report to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    return filename

def print_report_summary(report):
    """Print human-readable summary of verification report"""
    print("=" * 60)
    print("TARGET PROJECTS VERIFICATION REPORT")
    print("=" * 60)
    print(f"Generated: {report['timestamp']}")
    print(f"Current Project: {report['current_project']}")
    print()
    
    print("SUMMARY:")
    print(f"  Total Target Projects: {report['summary']['total_projects']}")
    print(f"  Accessible Projects: {report['summary']['accessible_projects']}")
    print(f"  Verification Status: {report['summary']['verification_status']}")
    print()
    
    for project_name, project_data in report['target_projects'].items():
        print(f"PROJECT: {project_name}")
        print(f"  Path: {project_data['path']}")
        print(f"  Exists: {project_data['exists']}")
        print(f"  Readable: {project_data['readable']}")
        print(f"  Writable: {project_data['writable']}")
        
        if project_data['error']:
            print(f"  Error: {project_data['error']}")
        else:
            print(f"  Structure: {len(project_data['structure'])} items")
            if project_data['structure']:
                print(f"    - {', '.join(project_data['structure'][:10])}")
                if len(project_data['structure']) > 10:
                    print(f"    - ... and {len(project_data['structure']) - 10} more items")
        print()

if __name__ == "__main__":
    # Generate and save report
    report = generate_verification_report()
    report_file = save_report(report)
    
    # Print summary
    print_report_summary(report)
    print(f"Full report saved to: {report_file}")