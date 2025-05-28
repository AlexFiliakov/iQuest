"""
Unit tests for peer group comparison functionality.
"""

import pytest
from datetime import datetime, timedelta
import hashlib

from src.analytics.peer_group_comparison import (
    PeerGroupManager, PeerGroup, GroupMember, GroupComparison,
    GroupPrivacyLevel, GroupRole, AnonymousMetricData,
    GroupChallengeManager, GroupChallenge
)


class TestGroupMember:
    """Test group member functionality."""
    
    def test_member_initialization(self):
        """Test member initialization and ID anonymization."""
        member = GroupMember(
            member_id="user123",
            joined_date=datetime.now(),
            role=GroupRole.MEMBER,
            last_active=datetime.now()
        )
        
        # Should hash short IDs
        assert len(member.member_id) == 64  # SHA256 hex length
        assert member.member_id != "user123"
        assert member.is_active
        
    def test_member_with_long_id(self):
        """Test member with already hashed ID."""
        long_id = hashlib.sha256("user123".encode()).hexdigest()
        member = GroupMember(
            member_id=long_id,
            joined_date=datetime.now(),
            role=GroupRole.ADMIN,
            last_active=datetime.now()
        )
        
        # Should not re-hash
        assert member.member_id == long_id


class TestPeerGroup:
    """Test peer group functionality."""
    
    def test_group_initialization(self):
        """Test group initialization."""
        group = PeerGroup(
            group_id="test_group_123",
            name="Morning Runners",
            description="Early morning running group",
            created_date=datetime.now(),
            privacy_level=GroupPrivacyLevel.PRIVATE
        )
        
        assert group.group_id == "test_group_123"
        assert group.name == "Morning Runners"
        assert group.min_members == 5
        assert group.max_members == 100
        assert group.member_count == 0
        assert not group.is_valid_for_comparison
        
    def test_member_count(self):
        """Test active member counting."""
        group = PeerGroup(
            group_id="test_group",
            name="Test Group",
            description="Test",
            created_date=datetime.now(),
            privacy_level=GroupPrivacyLevel.ANONYMOUS
        )
        
        # Add members
        for i in range(7):
            member = GroupMember(
                member_id=f"user{i}",
                joined_date=datetime.now(),
                role=GroupRole.MEMBER,
                last_active=datetime.now()
            )
            group.members.append(member)
            
        assert group.member_count == 7
        assert group.is_valid_for_comparison
        
        # Deactivate some members
        group.members[0].is_active = False
        group.members[1].is_active = False
        
        assert group.member_count == 5
        assert group.is_valid_for_comparison
        
        # One more makes it invalid
        group.members[2].is_active = False
        assert group.member_count == 4
        assert not group.is_valid_for_comparison
        
    def test_invite_code_generation(self):
        """Test invite code generation and validation."""
        group = PeerGroup(
            group_id="test_group",
            name="Test Group",
            description="Test",
            created_date=datetime.now(),
            privacy_level=GroupPrivacyLevel.PRIVATE
        )
        
        # Generate codes
        code1 = group.generate_invite_code()
        code2 = group.generate_invite_code()
        
        assert len(code1) > 10  # Reasonable length
        assert code1 != code2  # Unique codes
        assert group.validate_invite_code(code1)
        assert group.validate_invite_code(code2)
        assert not group.validate_invite_code("invalid_code")


class TestPeerGroupManager:
    """Test peer group manager functionality."""
    
    @pytest.fixture
    def manager(self):
        """Create a peer group manager."""
        return PeerGroupManager()
        
    def test_manager_initialization(self, manager):
        """Test manager initialization."""
        assert manager.min_group_size == 5
        assert len(manager.groups) == 0
        assert len(manager.member_groups) == 0
        
    def test_create_group(self, manager):
        """Test group creation."""
        group = manager.create_group(
            name="Fitness Friends",
            description="Stay fit together",
            creator_id="creator123",
            privacy_level=GroupPrivacyLevel.PRIVATE
        )
        
        assert group.name == "Fitness Friends"
        assert group.member_count == 1  # Creator
        assert len(manager.groups) == 1
        assert group.group_id in manager.groups
        
        # Check creator is anonymized
        creator_hash = hashlib.sha256("creator123".encode()).hexdigest()
        assert group.members[0].member_id == creator_hash
        assert group.members[0].role == GroupRole.CREATOR
        
    def test_join_group_public(self, manager):
        """Test joining a public group."""
        # Create public group
        group = manager.create_group(
            name="Public Fitness",
            description="Open to all",
            creator_id="creator123",
            privacy_level=GroupPrivacyLevel.PUBLIC
        )
        
        # Join without invite code
        success = manager.join_group(group.group_id, "member456")
        assert success
        assert group.member_count == 2
        
    def test_join_group_private(self, manager):
        """Test joining a private group."""
        # Create private group
        group = manager.create_group(
            name="Private Club",
            description="Invite only",
            creator_id="creator123",
            privacy_level=GroupPrivacyLevel.PRIVATE
        )
        
        # Generate invite code
        invite_code = group.generate_invite_code()
        
        # Try without invite code - should fail
        success = manager.join_group(group.group_id, "member456")
        assert not success
        assert group.member_count == 1
        
        # Try with valid invite code - should succeed
        success = manager.join_group(group.group_id, "member456", invite_code)
        assert success
        assert group.member_count == 2
        
        # Try with invalid invite code - should fail
        success = manager.join_group(group.group_id, "member789", "bad_code")
        assert not success
        assert group.member_count == 2
        
    def test_join_group_already_member(self, manager):
        """Test joining a group when already a member."""
        group = manager.create_group(
            name="Test Group",
            description="Test",
            creator_id="creator123",
            privacy_level=GroupPrivacyLevel.PUBLIC
        )
        
        # Join once
        success = manager.join_group(group.group_id, "member456")
        assert success
        assert group.member_count == 2
        
        # Try to join again
        success = manager.join_group(group.group_id, "member456")
        assert success  # Should return True but not add duplicate
        assert group.member_count == 2  # Still 2
        
    def test_leave_group(self, manager):
        """Test leaving a group."""
        group = manager.create_group(
            name="Test Group",
            description="Test",
            creator_id="creator123",
            privacy_level=GroupPrivacyLevel.PUBLIC
        )
        
        # Add member
        manager.join_group(group.group_id, "member456")
        assert group.member_count == 2
        
        # Leave group
        success = manager.leave_group(group.group_id, "member456")
        assert success
        assert group.member_count == 1  # Only creator remains
        
        # Try to leave non-existent group
        success = manager.leave_group("bad_group_id", "member456")
        assert not success
        
    def test_group_statistics(self, manager):
        """Test getting group statistics."""
        group = manager.create_group(
            name="Stats Group",
            description="Test statistics",
            creator_id="creator123",
            privacy_level=GroupPrivacyLevel.PUBLIC
        )
        
        # Add enough members
        for i in range(5):
            manager.join_group(group.group_id, f"member{i}")
            
        # Get statistics
        stats = manager.get_group_statistics(group.group_id, "steps")
        
        assert stats is not None
        assert 'mean' in stats
        assert 'median' in stats
        assert 'std' in stats
        assert 'min' in stats
        assert 'max' in stats
        assert stats['member_count'] == 6  # creator + 5 members
        
    def test_group_statistics_too_small(self, manager):
        """Test statistics for group that's too small."""
        group = manager.create_group(
            name="Small Group",
            description="Too small",
            creator_id="creator123",
            privacy_level=GroupPrivacyLevel.PUBLIC
        )
        
        # Only has creator
        stats = manager.get_group_statistics(group.group_id, "steps")
        assert stats is None
        
    def test_compare_to_group(self, manager):
        """Test comparing to group."""
        group = manager.create_group(
            name="Comparison Group",
            description="Test comparison",
            creator_id="creator123",
            privacy_level=GroupPrivacyLevel.PUBLIC
        )
        
        # Add members
        for i in range(5):
            manager.join_group(group.group_id, f"member{i}")
            
        # Compare as creator
        comparison = manager.compare_to_group(
            group.group_id, "creator123", "steps", 8500
        )
        
        assert comparison is not None
        assert comparison.error is None
        assert comparison.user_value == 8500
        assert comparison.anonymous_ranking in [
            "top quarter", "upper half", "middle range", "building momentum"
        ]
        assert len(comparison.insights) > 0
        
    def test_compare_to_group_not_member(self, manager):
        """Test comparing when not a member."""
        group = manager.create_group(
            name="Exclusive Group",
            description="Members only",
            creator_id="creator123",
            privacy_level=GroupPrivacyLevel.PRIVATE
        )
        
        # Try to compare without being member
        comparison = manager.compare_to_group(
            group.group_id, "outsider", "steps", 8000
        )
        
        assert comparison.error == "Not a member of this group"
        
    def test_member_index(self, manager):
        """Test member group index tracking."""
        # Create multiple groups
        group1 = manager.create_group(
            "Group 1", "First group", "user123", GroupPrivacyLevel.PUBLIC
        )
        group2 = manager.create_group(
            "Group 2", "Second group", "user456", GroupPrivacyLevel.PUBLIC
        )
        
        # Join both groups as same user
        manager.join_group(group1.group_id, "member789")
        manager.join_group(group2.group_id, "member789")
        
        # Check index
        member_hash = hashlib.sha256("member789".encode()).hexdigest()
        assert member_hash in manager.member_groups
        assert len(manager.member_groups[member_hash]) == 2
        assert group1.group_id in manager.member_groups[member_hash]
        assert group2.group_id in manager.member_groups[member_hash]


class TestAnonymousMetricData:
    """Test anonymous metric data handling."""
    
    def test_metric_data_initialization(self):
        """Test metric data initialization."""
        data = AnonymousMetricData(
            metric="steps",
            period_start=datetime.now() - timedelta(days=7),
            period_end=datetime.now(),
            aggregated_value=56000,  # Weekly total
            data_points=7
        )
        
        assert data.metric == "steps"
        assert data.aggregated_value == 56000
        assert data.data_points == 7
        assert data.is_complete
        
    def test_differential_privacy(self):
        """Test differential privacy application."""
        data = AnonymousMetricData(
            metric="steps",
            period_start=datetime.now() - timedelta(days=1),
            period_end=datetime.now(),
            aggregated_value=8000,
            data_points=1
        )
        
        # Apply differential privacy
        private_data = data.to_differential_private(epsilon=1.0)
        
        # Should be different due to noise
        assert private_data.aggregated_value != data.aggregated_value
        assert private_data.metric == data.metric
        assert private_data.data_points == data.data_points
        
        # Multiple applications should give different results
        results = [data.to_differential_private().aggregated_value 
                  for _ in range(10)]
        assert len(set(results)) > 1


class TestGroupChallenge:
    """Test group challenge functionality."""
    
    def test_challenge_initialization(self):
        """Test challenge initialization."""
        start = datetime.now()
        end = start + timedelta(days=30)
        
        challenge = GroupChallenge(
            challenge_id="challenge123",
            group_id="group456",
            name="30-Day Step Challenge",
            metric="steps",
            start_date=start,
            end_date=end,
            target_type="improvement"
        )
        
        assert challenge.challenge_id == "challenge123"
        assert challenge.name == "30-Day Step Challenge"
        assert challenge.metric == "steps"
        assert challenge.target_type == "improvement"
        
    def test_challenge_active_status(self):
        """Test challenge active status checking."""
        # Future challenge
        future_challenge = GroupChallenge(
            challenge_id="future",
            group_id="group1",
            name="Future Challenge",
            metric="steps",
            start_date=datetime.now() + timedelta(days=7),
            end_date=datetime.now() + timedelta(days=37),
            target_type="absolute"
        )
        
        assert not future_challenge.is_active
        assert future_challenge.days_remaining == 0
        
        # Active challenge
        active_challenge = GroupChallenge(
            challenge_id="active",
            group_id="group1",
            name="Active Challenge",
            metric="steps",
            start_date=datetime.now() - timedelta(days=5),
            end_date=datetime.now() + timedelta(days=25),
            target_type="consistency"
        )
        
        assert active_challenge.is_active
        assert active_challenge.days_remaining == 25
        
        # Past challenge
        past_challenge = GroupChallenge(
            challenge_id="past",
            group_id="group1",
            name="Past Challenge",
            metric="steps",
            start_date=datetime.now() - timedelta(days=35),
            end_date=datetime.now() - timedelta(days=5),
            target_type="improvement"
        )
        
        assert not past_challenge.is_active
        assert past_challenge.days_remaining == 0


class TestGroupChallengeManager:
    """Test group challenge manager."""
    
    @pytest.fixture
    def managers(self):
        """Create group and challenge managers."""
        group_manager = PeerGroupManager()
        challenge_manager = GroupChallengeManager(group_manager)
        return group_manager, challenge_manager
        
    def test_create_challenge(self, managers):
        """Test creating a group challenge."""
        group_manager, challenge_manager = managers
        
        # Create group
        group = group_manager.create_group(
            "Challenge Group",
            "Group for challenges",
            "creator123",
            GroupPrivacyLevel.PUBLIC
        )
        
        # Create challenge
        challenge = challenge_manager.create_challenge(
            group.group_id,
            "Summer Steps",
            "steps",
            30,
            "improvement"
        )
        
        assert challenge is not None
        assert challenge.name == "Summer Steps"
        assert challenge.metric == "steps"
        assert challenge.group_id == group.group_id
        assert len(challenge.challenge_id) > 0
        
        # Verify it's tracked
        assert challenge.challenge_id in challenge_manager.active_challenges
        
    def test_create_challenge_invalid_group(self, managers):
        """Test creating challenge for non-existent group."""
        _, challenge_manager = managers
        
        challenge = challenge_manager.create_challenge(
            "bad_group_id",
            "Invalid Challenge",
            "steps",
            30,
            "absolute"
        )
        
        assert challenge is None