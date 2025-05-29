#!/usr/bin/env python3
"""
Compare visual regression baselines between branches.

This script is used in CI/CD to detect visual changes between the main branch
and pull request branches.
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from PIL import Image, ImageChops, ImageDraw, ImageFont
import numpy as np


@dataclass
class ComparisonResult:
    """Result of comparing two baseline images"""
    filename: str
    similarity: float
    pixel_diff_count: int
    max_diff: float
    has_size_change: bool
    old_size: Optional[Tuple[int, int]]
    new_size: Optional[Tuple[int, int]]
    

class BaselineComparator:
    """Compare visual regression baselines between directories"""
    
    def __init__(self, threshold: float = 0.99):
        """
        Initialize comparator.
        
        Args:
            threshold: Similarity threshold (0-1) below which images are considered different
        """
        self.threshold = threshold
        self.results: List[ComparisonResult] = []
        
    def compare_directories(self, old_dir: Path, new_dir: Path) -> Dict[str, Any]:
        """
        Compare all baselines between two directories.
        
        Args:
            old_dir: Directory with original baselines
            new_dir: Directory with new baselines
            
        Returns:
            Dictionary with comparison results
        """
        old_files = set(f.name for f in old_dir.glob("*.png"))
        new_files = set(f.name for f in new_dir.glob("*.png"))
        
        # Find added/removed files
        added_files = new_files - old_files
        removed_files = old_files - new_files
        common_files = old_files & new_files
        
        # Compare common files
        for filename in common_files:
            old_path = old_dir / filename
            new_path = new_dir / filename
            result = self._compare_images(old_path, new_path, filename)
            self.results.append(result)
            
        # Summary statistics
        total_compared = len(self.results)
        changed_files = [r for r in self.results if r.similarity < self.threshold]
        size_changes = [r for r in self.results if r.has_size_change]
        
        return {
            'total_files': len(old_files | new_files),
            'compared_files': total_compared,
            'added_files': list(added_files),
            'removed_files': list(removed_files),
            'changed_files': len(changed_files),
            'size_changes': len(size_changes),
            'threshold': self.threshold,
            'details': self.results,
            'summary': self._generate_summary(changed_files)
        }
        
    def _compare_images(self, old_path: Path, new_path: Path, 
                       filename: str) -> ComparisonResult:
        """Compare two images and return similarity metrics"""
        old_img = Image.open(old_path).convert('RGB')
        new_img = Image.open(new_path).convert('RGB')
        
        # Check size changes
        has_size_change = old_img.size != new_img.size
        old_size = old_img.size
        new_size = new_img.size
        
        # Resize for comparison if needed
        if has_size_change:
            # Resize to larger dimensions for comparison
            max_width = max(old_img.width, new_img.width)
            max_height = max(old_img.height, new_img.height)
            old_img = old_img.resize((max_width, max_height), Image.Resampling.LANCZOS)
            new_img = new_img.resize((max_width, max_height), Image.Resampling.LANCZOS)
            
        # Calculate pixel differences
        diff = ImageChops.difference(old_img, new_img)
        diff_array = np.array(diff)
        
        # Calculate metrics
        pixel_diff_count = np.count_nonzero(diff_array.sum(axis=2) > 0)
        total_pixels = diff_array.shape[0] * diff_array.shape[1]
        similarity = 1.0 - (pixel_diff_count / total_pixels)
        
        # Maximum difference per channel
        max_diff = diff_array.max() / 255.0
        
        return ComparisonResult(
            filename=filename,
            similarity=similarity,
            pixel_diff_count=pixel_diff_count,
            max_diff=max_diff,
            has_size_change=has_size_change,
            old_size=old_size if has_size_change else None,
            new_size=new_size if has_size_change else None
        )
        
    def _generate_summary(self, changed_files: List[ComparisonResult]) -> str:
        """Generate human-readable summary of changes"""
        if not changed_files:
            return "No visual changes detected."
            
        summary_lines = [f"Found {len(changed_files)} visual changes:"]
        
        for result in changed_files:
            change_desc = []
            
            if result.has_size_change:
                change_desc.append(
                    f"size changed from {result.old_size} to {result.new_size}"
                )
                
            change_desc.append(
                f"{(1-result.similarity)*100:.2f}% pixels different"
            )
            
            summary_lines.append(f"  - {result.filename}: {', '.join(change_desc)}")
            
        return "\n".join(summary_lines)
        
    def generate_diff_images(self, old_dir: Path, new_dir: Path, 
                           output_dir: Path) -> None:
        """Generate diff visualization images for changed files"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for result in self.results:
            if result.similarity >= self.threshold:
                continue
                
            old_path = old_dir / result.filename
            new_path = new_dir / result.filename
            diff_path = output_dir / f"{result.filename.replace('.png', '_diff.png')}"
            
            self._create_diff_visualization(old_path, new_path, diff_path, result)
            
    def _create_diff_visualization(self, old_path: Path, new_path: Path,
                                 output_path: Path, result: ComparisonResult) -> None:
        """Create a visual diff showing old, new, and difference"""
        old_img = Image.open(old_path).convert('RGB')
        new_img = Image.open(new_path).convert('RGB')
        
        # Handle size differences
        max_width = max(old_img.width, new_img.width)
        max_height = max(old_img.height, new_img.height)
        
        if old_img.size != (max_width, max_height):
            old_resized = Image.new('RGB', (max_width, max_height), 'white')
            old_resized.paste(old_img, (0, 0))
            old_img = old_resized
            
        if new_img.size != (max_width, max_height):
            new_resized = Image.new('RGB', (max_width, max_height), 'white')
            new_resized.paste(new_img, (0, 0))
            new_img = new_resized
            
        # Create difference image
        diff_img = ImageChops.difference(old_img, new_img)
        
        # Enhance difference visibility
        diff_enhanced = Image.eval(diff_img, lambda x: min(255, x * 10))
        
        # Create composite image
        spacing = 20
        label_height = 40
        total_width = max_width * 3 + spacing * 4
        total_height = max_height + label_height + spacing * 2
        
        composite = Image.new('RGB', (total_width, total_height), 'white')
        draw = ImageDraw.Draw(composite)
        
        # Add images
        y_offset = label_height + spacing
        composite.paste(old_img, (spacing, y_offset))
        composite.paste(new_img, (max_width + spacing * 2, y_offset))
        composite.paste(diff_enhanced, (max_width * 2 + spacing * 3, y_offset))
        
        # Add labels
        try:
            # Try to use a nice font
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            # Fall back to default font
            font = ImageFont.load_default()
            
        labels = ['Original', 'New', f'Difference ({(1-result.similarity)*100:.1f}%)']
        x_positions = [
            spacing + max_width // 2,
            max_width + spacing * 2 + max_width // 2,
            max_width * 2 + spacing * 3 + max_width // 2
        ]
        
        for label, x_pos in zip(labels, x_positions):
            # Get text bounding box for centering
            bbox = draw.textbbox((0, 0), label, font=font)
            text_width = bbox[2] - bbox[0]
            draw.text((x_pos - text_width // 2, 10), label, fill='black', font=font)
            
        # Add metadata
        metadata_text = f"Size: {result.old_size} → {result.new_size}" if result.has_size_change else f"Size: {old_img.size}"
        draw.text((spacing, total_height - 25), metadata_text, fill='gray', font=font)
        
        # Save composite
        composite.save(output_path, 'PNG')
        

def main():
    """Main entry point for CLI usage"""
    parser = argparse.ArgumentParser(
        description='Compare visual regression baselines between directories'
    )
    parser.add_argument(
        'old_dir',
        type=Path,
        help='Directory containing original baselines'
    )
    parser.add_argument(
        'new_dir',
        type=Path,
        help='Directory containing new baselines'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.99,
        help='Similarity threshold (0-1) for detecting changes (default: 0.99)'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('tests/visual_diffs'),
        help='Directory for diff images (default: tests/visual_diffs)'
    )
    parser.add_argument(
        '--generate-diffs',
        action='store_true',
        help='Generate diff visualization images'
    )
    
    args = parser.parse_args()
    
    # Validate directories
    if not args.old_dir.exists():
        print(f"Error: Old directory '{args.old_dir}' does not exist")
        sys.exit(1)
        
    if not args.new_dir.exists():
        print(f"Error: New directory '{args.new_dir}' does not exist")
        sys.exit(1)
        
    # Run comparison
    comparator = BaselineComparator(threshold=args.threshold)
    results = comparator.compare_directories(args.old_dir, args.new_dir)
    
    # Print results
    print(f"Visual Baseline Comparison Report")
    print(f"=================================")
    print(f"Total files: {results['total_files']}")
    print(f"Files compared: {results['compared_files']}")
    print(f"Files added: {len(results['added_files'])}")
    print(f"Files removed: {len(results['removed_files'])}")
    print(f"Files changed: {results['changed_files']}")
    print(f"Files with size changes: {results['size_changes']}")
    print(f"\nThreshold: {results['threshold']*100:.1f}% similarity")
    
    if results['added_files']:
        print(f"\nAdded files:")
        for f in results['added_files']:
            print(f"  + {f}")
            
    if results['removed_files']:
        print(f"\nRemoved files:")
        for f in results['removed_files']:
            print(f"  - {f}")
            
    print(f"\n{results['summary']}")
    
    # Generate diff images if requested
    if args.generate_diffs and results['changed_files'] > 0:
        print(f"\nGenerating diff images in {args.output_dir}...")
        comparator.generate_diff_images(args.old_dir, args.new_dir, args.output_dir)
        print(f"Generated {results['changed_files']} diff images")
        
    # Exit with error code if changes detected
    if results['changed_files'] > 0:
        print(f"\n❌ Visual regression detected!")
        sys.exit(1)
    else:
        print(f"\n✅ No visual regressions detected")
        sys.exit(0)
        

if __name__ == '__main__':
    main()