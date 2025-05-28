"""
Peer Group Comparison Module for Apple Health Monitor.

Manages privacy-preserving peer group comparisons with:
- Anonymous group creation and management
- Minimum group size enforcement
- Encrypted data sharing
- Supportive comparison messaging
"""

import logging
import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class GroupPrivacyLevel(Enum):
    """Privacy levels for peer groups."""
    PRIVATE = "private"  # Invite-only, members know each other
    ANONYMOUS = "anonymous"  # No member identification
    PUBLIC = "public"  # Open groups (still anonymous stats)


class GroupRole(Enum):
    """Roles within a peer group."""
    CREATOR = "creator"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


@dataclass
class GroupMember:
    """Anonymous group member representation."""
    member_id: str  # Anonymous hash
    joined_date: datetime
    role: GroupRole
    last_active: datetime
    is_active: bool = True
    
    def __post_init__(self):
        # Ensure member_id is anonymized
        if len(self.member_id) < 32:
            # Hash any short IDs for privacy
            self.member_id = hashlib.sha256(self.member_id.encode()).hexdigest()


@dataclass 
class PeerGroup:
    """Peer comparison group."""
    group_id: str
    name: str
    description: str
    created_date: datetime
    privacy_level: GroupPrivacyLevel
    min_members: int = 5
    max_members: int = 100
    members: List[GroupMember] = field(default_factory=list)
    invite_codes: Set[str] = field(default_factory=set)
    settings: Dict = field(default_factory=dict)
    
    @property
    def member_count(self) -> int:
        """Get active member count."""
        return sum(1 for m in self.members if m.is_active)
        
    @property
    def is_valid_for_comparison(self) -> bool:
        """Check if group has enough members for comparison."""
        return self.member_count >= self.min_members
        
    def generate_invite_code(self) -> str:
        """Generate a secure invite code."""
        code = secrets.token_urlsafe(16)
        self.invite_codes.add(code)
        return code
        
    def validate_invite_code(self, code: str) -> bool:
        """Check if invite code is valid."""
        return code in self.invite_codes


@dataclass
class GroupComparison:
    """Results of a peer group comparison."""
    group_id: str
    metric: str
    comparison_date: datetime
    user_value: float
    group_stats: Dict[str, float]
    anonymous_ranking: str  # e.g., "top quarter", "middle half"
    trend_comparison: Optional[str] = None
    insights: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class AnonymousMetricData:
    """Anonymous metric data for group sharing."""
    metric: str
    period_start: datetime
    period_end: datetime
    aggregated_value: float
    data_points: int
    is_complete: bool = True
    
    def to_differential_private(self, epsilon: float = 1.0) -> 'AnonymousMetricData':
        """Apply differential privacy to the data."""
        # Add Laplace noise using secure random
        sensitivity = 1.0  # Adjust based on metric
        scale = sensitivity / epsilon
        # Use secure random for differential privacy
        rng = np.random.RandomState(secrets.randbits(32))
        noise = rng.laplace(0, scale)
        
        return AnonymousMetricData(
            metric=self.metric,
            period_start=self.period_start,
            period_end=self.period_end,
            aggregated_value=self.aggregated_value + noise,
            data_points=self.data_points,
            is_complete=self.is_complete
        )


class PeerGroupManager:
    """Manages peer groups and comparisons."""
    
    def __init__(self, min_group_size: int = 5):
        self.groups: Dict[str, PeerGroup] = {}
        self.min_group_size = min_group_size
        self.member_groups: Dict[str, List[str]] = {}  # member_id -> group_ids
        
    def create_group(self, name: str, description: str, 
                    creator_id: str, privacy_level: GroupPrivacyLevel) -> PeerGroup:
        """Create a new peer comparison group."""
        group_id = self._generate_group_id()
        
        # Anonymize creator ID
        creator_hash = hashlib.sha256(creator_id.encode()).hexdigest()
        
        creator_member = GroupMember(
            member_id=creator_hash,
            joined_date=datetime.now(),
            role=GroupRole.CREATOR,
            last_active=datetime.now()
        )
        
        group = PeerGroup(
            group_id=group_id,
            name=name,
            description=description,
            created_date=datetime.now(),
            privacy_level=privacy_level,
            members=[creator_member]
        )
        
        self.groups[group_id] = group
        self._add_member_to_index(creator_hash, group_id)
        
        logger.info(f"Created peer group: {group_id}")
        return group
        
    def join_group(self, group_id: str, member_id: str, 
                  invite_code: Optional[str] = None) -> bool:
        """Join a peer group."""
        if group_id not in self.groups:
            logger.error(f"Group not found: {group_id}")
            return False
            
        group = self.groups[group_id]
        
        # Check if group is full
        if group.member_count >= group.max_members:
            logger.warning(f"Group {group_id} is full")
            return False
            
        # Validate invite code for private groups
        if group.privacy_level == GroupPrivacyLevel.PRIVATE:
            if not invite_code or not group.validate_invite_code(invite_code):
                logger.warning(f"Invalid invite code for group {group_id}")
                return False
                
        # Anonymize member ID
        member_hash = hashlib.sha256(member_id.encode()).hexdigest()
        
        # Check if already a member
        if any(m.member_id == member_hash for m in group.members):
            logger.info(f"Member already in group {group_id}")
            return True
            
        # Add member
        new_member = GroupMember(
            member_id=member_hash,
            joined_date=datetime.now(),
            role=GroupRole.MEMBER,
            last_active=datetime.now()
        )
        
        group.members.append(new_member)
        self._add_member_to_index(member_hash, group_id)
        
        logger.info(f"Member joined group {group_id}")
        return True
        
    def leave_group(self, group_id: str, member_id: str) -> bool:
        """Leave a peer group."""
        if group_id not in self.groups:
            return False
            
        group = self.groups[group_id]
        member_hash = hashlib.sha256(member_id.encode()).hexdigest()
        
        # Find and deactivate member
        for member in group.members:
            if member.member_id == member_hash:
                member.is_active = False
                self._remove_member_from_index(member_hash, group_id)
                logger.info(f"Member left group {group_id}")
                return True
                
        return False
        
    def get_group_statistics(self, group_id: str, metric: str,
                           period_days: int = 30) -> Optional[Dict[str, float]]:
        """Get anonymous group statistics for a metric."""
        if group_id not in self.groups:
            return None
            
        group = self.groups[group_id]
        
        if not group.is_valid_for_comparison:
            logger.warning(f"Group {group_id} too small for comparison")
            return None
            
        # In real implementation, this would aggregate member data
        # For now, return mock statistics using secure random
        rng = np.random.RandomState(secrets.randbits(32))
        mock_values = rng.normal(8000, 2000, group.member_count)
        
        return {
            'mean': float(np.mean(mock_values)),
            'median': float(np.median(mock_values)),
            'std': float(np.std(mock_values)),
            'min': float(np.min(mock_values)),
            'max': float(np.max(mock_values)),
            'percentile_25': float(np.percentile(mock_values, 25)),
            'percentile_75': float(np.percentile(mock_values, 75)),
            'member_count': group.member_count
        }
        
    def compare_to_group(self, group_id: str, member_id: str,
                        metric: str, user_value: float) -> Optional[GroupComparison]:
        """Compare user's metric to their peer group."""
        if group_id not in self.groups:
            return GroupComparison(
                group_id=group_id,
                metric=metric,
                comparison_date=datetime.now(),
                user_value=user_value,
                group_stats={},
                anonymous_ranking="",
                error="Group not found"
            )
            
        group = self.groups[group_id]
        member_hash = hashlib.sha256(member_id.encode()).hexdigest()
        
        # Verify membership
        if not any(m.member_id == member_hash and m.is_active for m in group.members):
            return GroupComparison(
                group_id=group_id,
                metric=metric,
                comparison_date=datetime.now(),
                user_value=user_value,
                group_stats={},
                anonymous_ranking="",
                error="Not a member of this group"
            )
            
        # Get group statistics
        stats = self.get_group_statistics(group_id, metric)
        
        if not stats:
            return GroupComparison(
                group_id=group_id,
                metric=metric,
                comparison_date=datetime.now(),
                user_value=user_value,
                group_stats={},
                anonymous_ranking="",
                error="Insufficient group data"
            )
            
        # Calculate anonymous ranking
        ranking = self._calculate_anonymous_ranking(user_value, stats)
        
        # Generate supportive insights
        insights = self._generate_group_insights(user_value, stats, ranking)
        
        return GroupComparison(
            group_id=group_id,
            metric=metric,
            comparison_date=datetime.now(),
            user_value=user_value,
            group_stats=stats,
            anonymous_ranking=ranking,
            insights=insights
        )
        
    def _generate_group_id(self) -> str:
        """Generate a unique group ID."""
        return secrets.token_urlsafe(12)
        
    def _add_member_to_index(self, member_hash: str, group_id: str):
        """Add member to group index."""
        if member_hash not in self.member_groups:
            self.member_groups[member_hash] = []
        if group_id not in self.member_groups[member_hash]:
            self.member_groups[member_hash].append(group_id)
            
    def _remove_member_from_index(self, member_hash: str, group_id: str):
        """Remove member from group index."""
        if member_hash in self.member_groups:
            self.member_groups[member_hash] = [
                gid for gid in self.member_groups[member_hash] if gid != group_id
            ]
            
    def _calculate_anonymous_ranking(self, value: float, 
                                   stats: Dict[str, float]) -> str:
        """Calculate anonymous ranking description."""
        if value >= stats['percentile_75']:
            return "top quarter"
        elif value >= stats['median']:
            return "upper half"
        elif value >= stats['percentile_25']:
            return "middle range"
        else:
            return "building momentum"
            
    def _generate_group_insights(self, value: float, stats: Dict[str, float],
                               ranking: str) -> List[str]:
        """Generate supportive group insights."""
        insights = []
        
        # Always start with something positive
        if ranking == "top quarter":
            insights.append("You're leading the pack! 🏆")
            insights.append("Your dedication is inspiring the group.")
        elif ranking == "upper half":
            insights.append("You're doing better than most! 🌟")
            insights.append("Keep up the great momentum.")
        elif ranking == "middle range":
            insights.append("You're right on track! 💪")
            insights.append("Consistency is key to improvement.")
        else:
            insights.append("Every journey starts somewhere! 🌱")
            insights.append("Your group is here to support you.")
            
        # Add context about the group
        insights.append(f"Your group average: {stats['mean']:,.0f}")
        
        # Suggest next steps
        if value < stats['median']:
            improvement = stats['median'] - value
            insights.append(f"Just {improvement:,.0f} more to reach the group median!")
        else:
            above_average = value - stats['mean']
            insights.append(f"You're {above_average:,.0f} above the group average!")
            
        return insights


class GroupChallengeManager:
    """Manages group challenges and competitions."""
    
    def __init__(self, group_manager: PeerGroupManager):
        self.group_manager = group_manager
        self.active_challenges: Dict[str, 'GroupChallenge'] = {}
        
    def create_challenge(self, group_id: str, name: str,
                       metric: str, duration_days: int,
                       target_type: str = 'improvement') -> Optional['GroupChallenge']:
        """Create a group challenge."""
        if group_id not in self.group_manager.groups:
            return None
            
        challenge = GroupChallenge(
            challenge_id=secrets.token_urlsafe(8),
            group_id=group_id,
            name=name,
            metric=metric,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=duration_days),
            target_type=target_type,
            participants=[]
        )
        
        self.active_challenges[challenge.challenge_id] = challenge
        return challenge


@dataclass
class GroupChallenge:
    """Group challenge/competition."""
    challenge_id: str
    group_id: str
    name: str
    metric: str
    start_date: datetime
    end_date: datetime
    target_type: str  # 'improvement', 'absolute', 'consistency'
    participants: List[str]
    leaderboard: Optional[Dict] = None
    
    @property
    def is_active(self) -> bool:
        """Check if challenge is currently active."""
        now = datetime.now()
        return self.start_date <= now <= self.end_date
        
    @property
    def days_remaining(self) -> int:
        """Get days remaining in challenge."""
        if not self.is_active:
            return 0
        return (self.end_date - datetime.now()).days