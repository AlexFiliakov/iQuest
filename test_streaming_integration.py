#!/usr/bin/env python3
"""
Integration test for XML Streaming Processor

Tests the streaming processor with a real Apple Health XML file.
"""

import sys
import os
import tempfile
import time
from pathlib import Path

# Add src to path to import modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from xml_streaming_processor import XMLStreamingProcessor


def test_streaming_processor():
    """Test the streaming processor with a real XML file."""
    
    # Path to the sample XML file
    xml_path = "raw data/apple_health_export_2024-11-3/export.xml"
    
    if not Path(xml_path).exists():
        print(f"❌ Sample XML file not found: {xml_path}")
        return False
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        db_path = temp_db.name
    
    try:
        print(f"🔍 Testing XML streaming processor with {xml_path}")
        print(f"📊 File size: {Path(xml_path).stat().st_size / (1024*1024):.1f} MB")
        
        # Initialize processor
        processor = XMLStreamingProcessor(memory_limit_mb=200)
        
        # Progress tracking
        progress_updates = []
        def progress_callback(percent, records):
            progress_updates.append((percent, records))
            if len(progress_updates) % 10 == 0:  # Print every 10th update
                print(f"📈 Progress: {percent:.1f}% - {records:,} records processed")
        
        # Process the file
        print("🚀 Starting XML processing...")
        start_time = time.time()
        
        record_count = processor.process_xml_file(
            xml_path, 
            db_path, 
            progress_callback
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"✅ Processing complete!")
        print(f"📈 Records processed: {record_count:,}")
        print(f"⏱️  Processing time: {processing_time:.2f} seconds")
        print(f"🔢 Progress updates: {len(progress_updates)}")
        
        # Verify database
        import sqlite3
        conn = sqlite3.connect(db_path)
        
        # Check record count
        cursor = conn.execute("SELECT COUNT(*) FROM health_records")
        db_count = cursor.fetchone()[0]
        
        # Check data types
        cursor = conn.execute("SELECT DISTINCT type FROM health_records LIMIT 10")
        types = [row[0] for row in cursor.fetchall()]
        
        # Check memory usage
        final_memory = processor.memory_monitor.get_current_usage_mb()
        
        conn.close()
        
        print(f"🗄️  Database records: {db_count:,}")
        print(f"🏷️  Sample record types: {', '.join(types[:5])}")
        print(f"💾 Final memory usage: {final_memory:.1f} MB")
        
        # Validation
        if db_count == record_count and record_count > 0:
            print("🎉 Test PASSED! Streaming processor working correctly.")
            return True
        else:
            print(f"❌ Test FAILED! Record count mismatch: {record_count} vs {db_count}")
            return False
            
    except Exception as e:
        print(f"❌ Test FAILED with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up temporary database
        if Path(db_path).exists():
            os.unlink(db_path)


def test_memory_monitoring():
    """Test memory monitoring functionality."""
    print("\n🧪 Testing memory monitoring...")
    
    from xml_streaming_processor import MemoryMonitor
    
    monitor = MemoryMonitor(limit_mb=100)
    current_usage = monitor.get_current_usage_mb()
    percentage = monitor.get_usage_percentage()
    
    print(f"💾 Current memory usage: {current_usage:.1f} MB")
    print(f"📊 Usage percentage: {percentage:.1f}%")
    print(f"⚠️  Over limit: {monitor.is_over_limit()}")
    
    return True


def test_chunk_size_calculation():
    """Test chunk size calculation logic."""
    print("\n🧪 Testing chunk size calculation...")
    
    processor = XMLStreamingProcessor()
    
    # Test different file sizes
    test_sizes = [
        (30 * 1024 * 1024, "30MB"),    # Small
        (100 * 1024 * 1024, "100MB"),  # Medium  
        (500 * 1024 * 1024, "500MB")   # Large
    ]
    
    for size_bytes, size_label in test_sizes:
        chunk_size = processor.calculate_chunk_size(size_bytes)
        should_stream = processor.should_use_streaming("dummy_path")
        print(f"📄 {size_label:>6}: chunk_size={chunk_size:>5}, stream={should_stream}")
    
    return True


if __name__ == "__main__":
    print("🔬 XML Streaming Processor Integration Test\n")
    
    # Run tests
    tests = [
        ("Memory Monitoring", test_memory_monitoring),
        ("Chunk Size Calculation", test_chunk_size_calculation),
        ("Streaming Processor", test_streaming_processor),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} tests passed")
    print('='*50)
    
    if passed == total:
        print("🎉 All tests passed! XML Streaming Processor is working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the implementation.")
        sys.exit(1)