from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from members.models import (
    Member, Course, Lecture, LectureQuestion,
    MemberLectureProgress, MemberQuizAttempt, MemberAchievement
)
from members.views import _evaluate_member_achievements, _track_daily_activity
import datetime

User = get_user_model()


class Command(BaseCommand):
    help = 'Test achievements system by creating test user and simulating activity'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='test@example.com',
            help='Email for test user'
        )

    def handle(self, *args, **options):
        email = options['email']

        # Create or get test user
        user, created = User.objects.get_or_create(
            username=email,
            defaults={'email': email, 'password': 'testpass123'}
        )

        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(f"Created test user: {email}")
        else:
            self.stdout.write(f"Using existing user: {email}")

        # Create or get member
        member, created = Member.objects.get_or_create(
            user=user,
            defaults={
                'first_name': 'Test',
                'last_name': 'User',
                'email': email,
                'xp': 0,
                'level': 0
            }
        )

        if created:
            self.stdout.write(f"Created member profile for: {email}")

        # Track daily activity
        _track_daily_activity(member)
        self.stdout.write("Tracked daily activity")

        # Simulate completing first lecture
        first_course = Course.objects.first()
        if first_course:
            first_lecture = first_course.lectures.first()
            if first_lecture:
                # Mark lecture as completed
                progress, created = MemberLectureProgress.objects.get_or_create(
                    member=member,
                    lecture=first_lecture,
                    defaults={
                        'completed': True,
                        'answered_correctly': True,
                        'xp_awarded': 25
                    }
                )

                if created:
                    member.xp += 25
                    member.save()
                    self.stdout.write(f"Completed first lecture: {first_lecture.title}")

                # Simulate quiz attempt
                questions = list(first_lecture.questions.all())
                if questions:
                    MemberQuizAttempt.objects.get_or_create(
                        member=member,
                        lecture=first_lecture,
                        defaults={
                            'correct_count': len(questions),
                            'total_questions': len(questions),
                            'was_success': True
                        }
                    )
                    self.stdout.write(f"Added successful quiz attempt")

        # Evaluate achievements
        achievements_before = MemberAchievement.objects.filter(member=member).count()
        earned_achievements = _evaluate_member_achievements(member)
        achievements_after = MemberAchievement.objects.filter(member=member).count()

        self.stdout.write(f"\nAchievements before: {achievements_before}")
        self.stdout.write(f"Achievements after: {achievements_after}")
        self.stdout.write(f"New achievements earned: {achievements_after - achievements_before}")

        self.stdout.write(f"\nEarned achievements:")
        for achievement in earned_achievements:
            self.stdout.write(f"  - {achievement['title']}: {achievement['subtitle']}")

        # Show member stats
        member.refresh_from_db()
        self.stdout.write(f"\nMember stats:")
        self.stdout.write(f"  XP: {member.xp}")
        self.stdout.write(f"  Level: {member.level}")
        self.stdout.write(f"  Total achievements: {MemberAchievement.objects.filter(member=member).count()}")

        self.stdout.write(self.style.SUCCESS(f'\nTest completed! You can now login with {email} / testpass123'))
