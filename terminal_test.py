#!/usr/bin/env python3
"""
Terminal-based test of the Ultimate Log Analyzer
Shows false positive elimination and root cause analysis
"""

import os
import sys
import importlib.util
from datetime import datetime

# Import the analyzer
spec = importlib.util.spec_from_file_location("analyzer", "desktop-analyzer-ultimate.py")
analyzer_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyzer_module)

def analyze_log_file(file_path):
    """Analyze a single log file and display results"""
    print(f"\n{'='*80}")
    print(f"ANALYZING: {os.path.basename(file_path)}")
    print(f"{'='*80}")
    
    try:
        # Create analyzer instance
        analyzer = analyzer_module.UltimateLogAnalyzer()
        
        # Read log file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📁 File size: {len(content):,} characters")
        
        # Parse entries
        entries = analyzer.parse_log_entries(content)
        print(f"📊 Total log entries: {len(entries):,}")
        
        # Analyze patterns
        errors, patterns = analyzer.analyze_patterns(entries)
        print(f"🔍 Error patterns detected: {len(errors)}")
        
        # Check for false positives
        false_positives = []
        actual_errors = []
        
        for error in errors:
            if 'completed successfully' in error.get('message', '').lower():
                false_positives.append(error)
            else:
                actual_errors.append(error)
        
        print(f"❌ Actual errors: {len(actual_errors)}")
        print(f"✅ False positives eliminated: {len(false_positives)}")
        
        # Severity distribution
        severity_counts = {'Low (≤3)': 0, 'Medium (4-5)': 0, 'High (6-7)': 0, 'Critical (8-10)': 0}
        for entry in entries:
            severity = entry.get('severity', 0)
            if severity <= 3:
                severity_counts['Low (≤3)'] += 1
            elif severity <= 5:
                severity_counts['Medium (4-5)'] += 1
            elif severity <= 7:
                severity_counts['High (6-7)'] += 1
            else:
                severity_counts['Critical (8-10)'] += 1
        
        print(f"\n📈 SEVERITY DISTRIBUTION:")
        for level, count in severity_counts.items():
            percentage = (count / len(entries)) * 100 if entries else 0
            print(f"   {level}: {count:,} ({percentage:.1f}%)")
        
        # Show sample successful operations (should have low severity)
        successful_operations = [e for e in entries if 'completed successfully' in e.get('message', '').lower()]
        if successful_operations:
            print(f"\n✅ SUCCESSFUL OPERATIONS (first 5):")
            for i, op in enumerate(successful_operations[:5]):
                severity = op.get('severity', 0)
                timestamp = op.get('timestamp', 'Unknown')
                message = op.get('message', '')[:60] + '...' if len(op.get('message', '')) > 60 else op.get('message', '')
                print(f"   {i+1}. Severity: {severity:.1f}/10 - {message}")
        
        # Show actual errors
        if actual_errors:
            print(f"\n🚨 ACTUAL ERRORS (first 5):")
            for i, error in enumerate(actual_errors[:5]):
                severity = error.get('severity', 0)
                error_type = error.get('type', 'Unknown')
                message = error.get('message', '')[:60] + '...' if len(error.get('message', '')) > 60 else error.get('message', '')
                print(f"   {i+1}. [{error_type}] Severity: {severity:.1f}/10 - {message}")
        
        # Root cause analysis
        root_causes = analyzer.identify_root_causes(entries, actual_errors, patterns)
        print(f"\n🔍 ROOT CAUSE ANALYSIS:")
        print(f"   Total root causes identified: {len(root_causes)}")
        
        if root_causes:
            print(f"\n📋 TOP ROOT CAUSES:")
            for i, cause in enumerate(root_causes[:3]):
                title = cause.get('title', 'Unknown Cause')
                description = cause.get('description', 'No description')
                confidence = cause.get('confidence', 0) * 100
                severity = cause.get('severity', 'Unknown')
                print(f"   {i+1}. {title}")
                print(f"      Confidence: {confidence:.1f}% | Severity: {severity}")
                print(f"      {description}")
                print()
        
        # Pattern analysis
        if patterns:
            print(f"🏷️  ERROR PATTERN BREAKDOWN:")
            sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)
            for pattern_type, count in sorted_patterns:
                print(f"   {pattern_type}: {count} occurrences")
        
        return {
            'success': True,
            'total_entries': len(entries),
            'actual_errors': len(actual_errors),
            'false_positives': len(false_positives),
            'root_causes': len(root_causes),
            'patterns': len(patterns)
        }
        
    except Exception as e:
        print(f"❌ Error analyzing {file_path}: {str(e)}")
        return {'success': False, 'error': str(e)}

def main():
    """Main test function"""
    print("🚀 ENTERPRISE LOG ANALYZER - TERMINAL TEST")
    print("Testing false positive elimination and root cause analysis")
    
    # Test files (you can modify this list)
    test_files = [
        'attached_assets/logbank_mixed_faults_large_1749729416155.log',
        'attached_assets/logbank_mixed_faults_small_1749729416156.log',
        'attached_assets/logbank_thermal_critical_1749729416156.log'
    ]
    
    # If user provides a specific file as argument
    if len(sys.argv) > 1:
        test_files = [sys.argv[1]]
    
    results = []
    
    for file_path in test_files:
        if os.path.exists(file_path):
            result = analyze_log_file(file_path)
            if result['success']:
                results.append(result)
        else:
            print(f"❌ File not found: {file_path}")
    
    # Summary
    if results:
        print(f"\n{'='*80}")
        print("📊 SUMMARY RESULTS")
        print(f"{'='*80}")
        
        total_entries = sum(r['total_entries'] for r in results)
        total_errors = sum(r['actual_errors'] for r in results)
        total_false_positives = sum(r['false_positives'] for r in results)
        total_root_causes = sum(r['root_causes'] for r in results)
        
        print(f"Files analyzed: {len(results)}")
        print(f"Total log entries: {total_entries:,}")
        print(f"Actual errors detected: {total_errors:,}")
        print(f"False positives eliminated: {total_false_positives}")
        print(f"Root causes identified: {total_root_causes}")
        
        if total_false_positives == 0:
            print("\n✅ SUCCESS: No false positives detected!")
        else:
            print(f"\n⚠️  {total_false_positives} false positives detected")
        
        if total_root_causes > 0:
            print("✅ Root cause analysis working properly!")
        else:
            print("⚠️  No root causes identified")

if __name__ == "__main__":
    main()