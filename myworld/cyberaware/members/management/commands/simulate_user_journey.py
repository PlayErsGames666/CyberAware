from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from members.models import (
    Member, Course, Lecture, LectureQuestion,
    MemberLectureProgress, MemberQuizAttempt, MemberAchievement, MemberDailyActivity
)
from members.views import _evaluate_member_achievements, _track_daily_activity, _recalculate_member_level
import datetime
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = 'Simulate complete user journey to test all achievements'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='journey_test@example.com',
            help='Email for test user'
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset existing user progress'
        )

    def handle(self, *args, **options):
        email = options['email']
        reset = options['reset']

        # Create or get test user
        user, created = User.objects.get_or_create(
            username=email,
            defaults={'email': email}
        )

        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(f"Created test user: {email}")

        # Create or get member
        member, member_created = Member.objects.get_or_create(
            user=user,
            defaults={
                'first_name': 'Journey',
                'last_name': 'Tester',
                'email': email,
                'xp': 0,
                'level': 0
            }
        )

        if reset and not member_created:
            # Reset progress
            MemberLectureProgress.objects.filter(member=member).delete()
            MemberQuizAttempt.objects.filter(member=member).delete()
            MemberAchievement.objects.filter(member=member).delete()
            MemberDailyActivity.objects.filter(member=member).delete()
            member.xp = 0
            member.level = 0
            member.save()
            self.stdout.write(f"Reset progress for: {email}")

        self.stdout.write(f"\n=== Starting User Journey Simulation ===")

        # Simulate multi-day activity for streaks
        base_date = timezone.now().date() - datetime.timedelta(days=20)
        for i in range(15):  # 15 days of activity
            activity_date = base_date + datetime.timedelta(days=i)
            MemberDailyActivity.objects.get_or_create(
                member=member,
                date=activity_date,
                defaults={'last_seen': timezone.now()}
            )

        self.stdout.write("✓ Simulated 15-day activity streak")

        courses = list(Course.objects.all())
        total_xp_awarded = 0

        # Complete all courses and lectures
        for course_idx, course in enumerate(courses):
            self.stdout.write(f"\n--- Processing Course: {course.title} ---")

            lectures = list(course.lectures.all())

            for lecture_idx, lecture in enumerate(lectures):
                # Mark lecture as completed
                progress, created = MemberLectureProgress.objects.get_or_create(
                    member=member,
                    lecture=lecture,
                    defaults={
                        'completed': True,
                        'answered_correctly': True,
                        'xp_awarded': 25
                    }
                )

                if created:
                    total_xp_awarded += 25
                    self.stdout.write(f"  ✓ Completed lecture: {lecture.title}")

                # Simulate quiz attempts
                questions = list(lecture.questions.all())
                if questions:
                    # First attempt - sometimes fail to test "don't give up" achievement
                    if lecture_idx == 1 and course_idx == 0:  # Fail second lecture of first course
                        # Failed attempt first
                        MemberQuizAttempt.objects.get_or_create(
                            member=member,
                            lecture=lecture,
                            created_at=timezone.now() - datetime.timedelta(minutes=10),
                            defaults={
                                'correct_count': len(questions) - 1,  # One wrong answer
                                'total_questions': len(questions),
                                'was_success': False
                            }
                        )
                        self.stdout.write(f"  ⚠ Failed first attempt for: {lecture.title}")

                    # Successful attempt
                    MemberQuizAttempt.objects.get_or_create(
                        member=member,
                        lecture=lecture,
                        defaults={
                            'correct_count': len(questions),
                            'total_questions': len(questions),
                            'was_success': True
                        }
                    )
                    self.stdout.write(f"  ✓ Passed quiz for: {lecture.title}")

        # Update member XP and level
        member.xp += total_xp_awarded
        member.save()
        _recalculate_member_level(member)

        # Evaluate all achievements
        achievements_before = MemberAchievement.objects.filter(member=member).count()
        earned_achievements = _evaluate_member_achievements(member)
        achievements_after = MemberAchievement.objects.filter(member=member).count()

        # Display results
        self.stdout.write(f"\n=== SIMULATION RESULTS ===")
        self.stdout.write(f"User: {email}")
        self.stdout.write(f"Password: testpass123")
        self.stdout.write(f"")

        member.refresh_from_db()
        self.stdout.write(f"Final Stats:")
        self.stdout.write(f"  • Total XP: {member.xp}")
        self.stdout.write(f"  • Level: {member.level}")
        self.stdout.write(f"  • Lectures completed: {MemberLectureProgress.objects.filter(member=member, completed=True).count()}")
        self.stdout.write(f"  • Quiz attempts: {MemberQuizAttempt.objects.filter(member=member).count()}")
        self.stdout.write(f"  • Achievements earned: {achievements_after}")

        # Group achievements by category
        from members.views import ACHIEVEMENT_CATEGORIES

        self.stdout.write(f"\n=== ACHIEVEMENTS BY CATEGORY ===")

        earned_codes = set(MemberAchievement.objects.filter(member=member).values_list('code', flat=True))

        for category in ACHIEVEMENT_CATEGORIES:
            category_achievements = []
            for item in category['items']:
                if item['code'] in earned_codes:
                    category_achievements.append(f"  ✓ {item['title']}: {item['description']}")
                else:
                    category_achievements.append(f"  ○ {item['title']}: {item['description']}")

            self.stdout.write(f"\n{category['title']} ({category['icon']}):")
            for ach_text in category_achievements:
                self.stdout.write(ach_text)

        # Calculate completion percentage
        total_possible = sum(len(cat['items']) for cat in ACHIEVEMENT_CATEGORIES)
        completion_percent = (achievements_after / total_possible) * 100

        self.stdout.write(f"\n=== COMPLETION SUMMARY ===")
        self.stdout.write(f"Achievement completion: {achievements_after}/{total_possible} ({completion_percent:.1f}%)")

        if completion_percent >= 90:
            self.stdout.write(self.style.SUCCESS("🎉 EXCELLENT! Almost all achievements unlocked!"))
        elif completion_percent >= 70:
            self.stdout.write(self.style.SUCCESS("🎯 GREAT! Most achievements unlocked!"))
        elif completion_percent >= 50:
            self.stdout.write(self.style.WARNING("👍 GOOD! Many achievements unlocked!"))
        else:
            self.stdout.write(self.style.WARNING("📈 Keep going! More achievements await!"))

        # Provide login instructions
        self.stdout.write(f"\n=== LOGIN INSTRUCTIONS ===")
        self.stdout.write(f"1. Go to: http://127.0.0.1:8000")
        self.stdout.write(f"2. Login with:")
        self.stdout.write(f"   Email: {email}")
        self.stdout.write(f"   Password: testpass123")
        self.stdout.write(f"3. Visit profile to see achievements!")

        self.stdout.write(self.style.SUCCESS(f'\n✅ User journey simulation completed successfully!'))
