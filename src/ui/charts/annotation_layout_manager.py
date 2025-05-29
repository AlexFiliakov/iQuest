"""Layout manager for positioning health annotations without overlap"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from PyQt6.QtCore import QPointF, QRectF, QSizeF

from ...analytics.annotation_models import HealthAnnotation, AnnotationPriority


@dataclass
class AnnotationBounds:
    """Bounds information for an annotation"""
    annotation: HealthAnnotation
    data_pos: QPointF
    display_pos: QPointF
    bounds: QRectF
    needs_leader: bool = False
    leader_path: Optional[List[QPointF]] = None


class AnnotationLayoutManager:
    """Manages annotation positioning to prevent overlaps and optimize readability"""
    
    def __init__(self):
        # Layout configuration
        self.margin = 10  # Minimum margin between annotations
        self.leader_line_enabled = True
        self.max_leader_length = 100
        self.annotation_size = QSizeF(250, 120)  # Default expanded size
        self.marker_size = 12
        
        # Positioning strategies
        self.position_strategies = [
            self._position_right,
            self._position_left,
            self._position_above,
            self._position_below,
            self._position_diagonal
        ]
    
    def optimize_layout(self, 
                       annotations: List[HealthAnnotation],
                       data_to_scene_transform,
                       scene_bounds: QRectF) -> Dict[str, AnnotationBounds]:
        """Optimize annotation positions to prevent overlaps
        
        Args:
            annotations: List of annotations to position
            data_to_scene_transform: Function to convert data coordinates to scene
            scene_bounds: Bounds of the scene/chart area
            
        Returns:
            Dictionary mapping annotation ID to bounds information
        """
        # Sort annotations by priority and position
        sorted_annotations = sorted(
            annotations,
            key=lambda a: (a.priority.value, a.data_point),
            reverse=True
        )
        
        # Track positioned annotations
        positioned: Dict[str, AnnotationBounds] = {}
        occupied_areas: List[QRectF] = []
        
        for annotation in sorted_annotations:
            # Convert data position to scene coordinates
            scene_pos = data_to_scene_transform(annotation.data_point, annotation.value)
            
            # Find optimal position
            bounds_info = self._find_optimal_position(
                annotation, scene_pos, occupied_areas, scene_bounds
            )
            
            # Add to positioned annotations
            positioned[annotation.id] = bounds_info
            occupied_areas.append(bounds_info.bounds)
        
        return positioned
    
    def _find_optimal_position(self,
                              annotation: HealthAnnotation,
                              data_pos: QPointF,
                              occupied_areas: List[QRectF],
                              scene_bounds: QRectF) -> AnnotationBounds:
        """Find optimal position for an annotation"""
        # Try each positioning strategy
        for strategy in self.position_strategies:
            display_pos, bounds = strategy(data_pos, self.annotation_size, scene_bounds)
            
            # Check if position is valid and doesn't overlap
            if self._is_valid_position(bounds, occupied_areas, scene_bounds):
                return AnnotationBounds(
                    annotation=annotation,
                    data_pos=data_pos,
                    display_pos=display_pos,
                    bounds=bounds,
                    needs_leader=self._needs_leader_line(data_pos, display_pos)
                )
        
        # If no non-overlapping position found, use leader line
        display_pos, bounds = self._position_with_leader(
            data_pos, occupied_areas, scene_bounds
        )
        
        # Create leader path
        leader_path = self._create_leader_path(data_pos, display_pos)
        
        return AnnotationBounds(
            annotation=annotation,
            data_pos=data_pos,
            display_pos=display_pos,
            bounds=bounds,
            needs_leader=True,
            leader_path=leader_path
        )
    
    def _position_right(self, data_pos: QPointF, size: QSizeF, 
                       scene_bounds: QRectF) -> Tuple[QPointF, QRectF]:
        """Position annotation to the right of data point"""
        display_pos = QPointF(
            data_pos.x() + self.marker_size + self.margin,
            data_pos.y() - size.height() / 2
        )
        bounds = QRectF(display_pos, size)
        return display_pos, bounds
    
    def _position_left(self, data_pos: QPointF, size: QSizeF,
                      scene_bounds: QRectF) -> Tuple[QPointF, QRectF]:
        """Position annotation to the left of data point"""
        display_pos = QPointF(
            data_pos.x() - size.width() - self.marker_size - self.margin,
            data_pos.y() - size.height() / 2
        )
        bounds = QRectF(display_pos, size)
        return display_pos, bounds
    
    def _position_above(self, data_pos: QPointF, size: QSizeF,
                       scene_bounds: QRectF) -> Tuple[QPointF, QRectF]:
        """Position annotation above data point"""
        display_pos = QPointF(
            data_pos.x() - size.width() / 2,
            data_pos.y() - size.height() - self.marker_size - self.margin
        )
        bounds = QRectF(display_pos, size)
        return display_pos, bounds
    
    def _position_below(self, data_pos: QPointF, size: QSizeF,
                       scene_bounds: QRectF) -> Tuple[QPointF, QRectF]:
        """Position annotation below data point"""
        display_pos = QPointF(
            data_pos.x() - size.width() / 2,
            data_pos.y() + self.marker_size + self.margin
        )
        bounds = QRectF(display_pos, size)
        return display_pos, bounds
    
    def _position_diagonal(self, data_pos: QPointF, size: QSizeF,
                          scene_bounds: QRectF) -> Tuple[QPointF, QRectF]:
        """Position annotation diagonally from data point"""
        # Try upper-right diagonal
        if data_pos.x() < scene_bounds.center().x():
            display_pos = QPointF(
                data_pos.x() + self.marker_size + self.margin,
                data_pos.y() - size.height() - self.margin
            )
        else:
            # Upper-left diagonal
            display_pos = QPointF(
                data_pos.x() - size.width() - self.marker_size - self.margin,
                data_pos.y() - size.height() - self.margin
            )
        
        bounds = QRectF(display_pos, size)
        return display_pos, bounds
    
    def _position_with_leader(self, data_pos: QPointF, 
                             occupied_areas: List[QRectF],
                             scene_bounds: QRectF) -> Tuple[QPointF, QRectF]:
        """Position annotation with a leader line to avoid overlaps"""
        # Find the nearest free edge position
        edge_positions = self._get_edge_positions(scene_bounds)
        
        best_pos = None
        min_distance = float('inf')
        
        for edge_pos in edge_positions:
            # Check if this edge position is free
            test_bounds = QRectF(edge_pos, self.annotation_size)
            
            if self._is_valid_position(test_bounds, occupied_areas, scene_bounds):
                # Calculate distance
                distance = self._point_distance(data_pos, edge_pos)
                
                if distance < min_distance and distance <= self.max_leader_length:
                    min_distance = distance
                    best_pos = edge_pos
        
        if best_pos is None:
            # Fallback: stack on right edge
            best_pos = self._find_stacking_position(occupied_areas, scene_bounds)
        
        return best_pos, QRectF(best_pos, self.annotation_size)
    
    def _get_edge_positions(self, scene_bounds: QRectF) -> List[QPointF]:
        """Get candidate positions along scene edges"""
        positions = []
        
        # Sample positions along edges
        num_samples = 10
        
        # Right edge
        for i in range(num_samples):
            y = scene_bounds.top() + (i + 1) * scene_bounds.height() / (num_samples + 1)
            positions.append(QPointF(
                scene_bounds.right() - self.annotation_size.width() - self.margin,
                y - self.annotation_size.height() / 2
            ))
        
        # Left edge
        for i in range(num_samples):
            y = scene_bounds.top() + (i + 1) * scene_bounds.height() / (num_samples + 1)
            positions.append(QPointF(
                scene_bounds.left() + self.margin,
                y - self.annotation_size.height() / 2
            ))
        
        return positions
    
    def _find_stacking_position(self, occupied_areas: List[QRectF],
                               scene_bounds: QRectF) -> QPointF:
        """Find position by stacking annotations vertically"""
        # Start from top-right
        x = scene_bounds.right() - self.annotation_size.width() - self.margin
        y = scene_bounds.top() + self.margin
        
        # Find the lowest unoccupied position
        test_pos = QPointF(x, y)
        test_bounds = QRectF(test_pos, self.annotation_size)
        
        while any(test_bounds.intersects(area) for area in occupied_areas):
            y += self.annotation_size.height() + self.margin
            test_pos = QPointF(x, y)
            test_bounds = QRectF(test_pos, self.annotation_size)
            
            # Wrap to left side if needed
            if y + self.annotation_size.height() > scene_bounds.bottom():
                x = scene_bounds.left() + self.margin
                y = scene_bounds.top() + self.margin
        
        return test_pos
    
    def _create_leader_path(self, start: QPointF, end: QPointF) -> List[QPointF]:
        """Create a leader line path between two points"""
        # Simple two-segment leader line
        mid_x = (start.x() + end.x()) / 2
        
        return [
            start,
            QPointF(mid_x, start.y()),
            QPointF(mid_x, end.y() + self.annotation_size.height() / 2),
            QPointF(end.x(), end.y() + self.annotation_size.height() / 2)
        ]
    
    def _is_valid_position(self, bounds: QRectF, occupied_areas: List[QRectF],
                          scene_bounds: QRectF) -> bool:
        """Check if a position is valid (within bounds and no overlaps)"""
        # Check if within scene bounds
        if not scene_bounds.contains(bounds):
            return False
        
        # Check for overlaps with occupied areas
        for area in occupied_areas:
            if bounds.intersects(area):
                return False
        
        return True
    
    def _needs_leader_line(self, data_pos: QPointF, display_pos: QPointF) -> bool:
        """Determine if a leader line is needed"""
        distance = self._point_distance(data_pos, display_pos)
        return distance > self.marker_size * 3
    
    def _point_distance(self, p1: QPointF, p2: QPointF) -> float:
        """Calculate distance between two points"""
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        return np.sqrt(dx * dx + dy * dy)


class AnnotationGrouper:
    """Groups nearby annotations for better layout"""
    
    def __init__(self, grouping_threshold: float = 50):
        self.grouping_threshold = grouping_threshold
    
    def group_annotations(self, annotations: List[HealthAnnotation],
                         data_to_scene_transform) -> List[List[HealthAnnotation]]:
        """Group annotations that are close together in screen space"""
        groups = []
        remaining = list(annotations)
        
        while remaining:
            # Start a new group with the highest priority annotation
            current_group = [remaining.pop(0)]
            group_center = data_to_scene_transform(
                current_group[0].data_point, 
                current_group[0].value
            )
            
            # Find all annotations close to this group
            i = 0
            while i < len(remaining):
                ann_pos = data_to_scene_transform(
                    remaining[i].data_point,
                    remaining[i].value
                )
                
                # Check distance to group center
                distance = self._point_distance(group_center, ann_pos)
                
                if distance < self.grouping_threshold:
                    current_group.append(remaining.pop(i))
                    # Update group center
                    group_center = self._calculate_group_center(
                        current_group, data_to_scene_transform
                    )
                else:
                    i += 1
            
            groups.append(current_group)
        
        return groups
    
    def _calculate_group_center(self, group: List[HealthAnnotation],
                               data_to_scene_transform) -> QPointF:
        """Calculate the center point of a group of annotations"""
        center = QPointF(0, 0)
        
        for ann in group:
            pos = data_to_scene_transform(ann.data_point, ann.value)
            center += pos
        
        center /= len(group)
        return center
    
    def _point_distance(self, p1: QPointF, p2: QPointF) -> float:
        """Calculate distance between two points"""
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        return np.sqrt(dx * dx + dy * dy)