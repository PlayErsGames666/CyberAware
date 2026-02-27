from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Course(models.Model):
    """Course (e.g. Cyber Threat Intelligence, Digital Forensics)."""
    slug = models.SlugField(max_length=32, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["slug"]

    def __str__(self):
        return self.title


class Lecture(models.Model):
    """Single lecture within a course."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lectures")
    order = models.PositiveIntegerField(default=0, help_text="Order in the course")
    title = models.CharField(max_length=255)
    heading = models.CharField(max_length=255)
    content = models.TextField(help_text="Lecture body (plain text or HTML)")

    class Meta:
        ordering = ["course", "order"]
        unique_together = [["course", "order"]]

    def __str__(self):
        return f"{self.course.title} – {self.title}"


class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='member')
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    phone = models.IntegerField(null=True)
    joined_date = models.DateField(null=True)

    # Gamification fields
    xp = models.PositiveIntegerField(default=0, help_text="Total experience points earned by the user.")
    level = models.PositiveIntegerField(default=0, help_text="Current level calculated from XP.")


class LectureQuestion(models.Model):
    """
    Multiple-choice question that belongs to a lecture.
    Several questions can be attached to each lecture.
    """
    OPTION_A = "A"
    OPTION_B = "B"
    OPTION_C = "C"
    OPTION_D = "D"

    OPTION_CHOICES = [
        (OPTION_A, "A"),
        (OPTION_B, "B"),
        (OPTION_C, "C"),
        (OPTION_D, "D"),
    ]

    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=1, choices=OPTION_CHOICES)

    class Meta:
        ordering = ["lecture_id", "id"]

    def __str__(self):
        return f"Q for {self.lecture_id}: {self.text[:50]}..."


class MemberLectureProgress(models.Model):
    """
    Stores per-user progress for each lecture and XP awarded for finishing the quiz.
    """
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="lecture_progress")
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name="member_progress")
    completed = models.BooleanField(default=False)
    answered_correctly = models.BooleanField(default=False)
    xp_awarded = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [["member", "lecture"]]

    def __str__(self):
        return f"{self.member_id} – {self.lecture_id}: {'done' if self.completed else 'pending'}"


class MemberDailyActivity(models.Model):
    """
    Tracks on which days the member was active in the product.
    Used to calculate login/returning streak achievements.
    """
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="daily_activity")
    date = models.DateField()
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["member", "date"]]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.member_id} – {self.date}"


class MemberQuizAttempt(models.Model):
    """
    Stores every quiz attempt for a lecture to power
    achievements like \"80%+\", \"с первого раза\" и т.п.
    """
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="quiz_attempts")
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name="quiz_attempts")
    created_at = models.DateTimeField(auto_now_add=True)
    correct_count = models.PositiveIntegerField()
    total_questions = models.PositiveIntegerField()
    was_success = models.BooleanField(default=False)

    class Meta:
        ordering = ["lecture_id", "created_at"]

    def __str__(self):
        return f"{self.member_id} – {self.lecture_id}: {self.correct_count}/{self.total_questions} ({'ok' if self.was_success else 'fail'})"


class MemberAchievement(models.Model):
    """
    Stores achievements earned by members.
    """
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="achievements")
    code = models.CharField(max_length=50, help_text="Achievement code (e.g., 'first_step', 'level_2')")
    earned_at = models.DateTimeField(auto_now_add=True, help_text="When the achievement was earned")

    class Meta:
        unique_together = [["member", "code"]]
        ordering = ["-earned_at"]

    def __str__(self):
        return f"{self.member_id} – {self.code}"


class UserSettings(models.Model):
    """
    Stores per-user preferences: appearance, notifications, privacy, security flags.
    Created automatically on first access via get_or_create.
    """
    THEME_CHOICES = [("dark", "Dark"), ("light", "Light"), ("system", "System")]
    FONT_CHOICES = [("small", "Small"), ("medium", "Medium"), ("large", "Large")]
    VISIBILITY_CHOICES = [
        ("everyone", "Everyone"),
        ("registered", "Registered users"),
        ("only_me", "Only me"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_settings")

    # Appearance
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default="dark")
    accent_color = models.CharField(max_length=7, default="#38bdf8")
    compact_mode = models.BooleanField(default=False)
    font_size = models.CharField(max_length=10, choices=FONT_CHOICES, default="medium")
    animations_enabled = models.BooleanField(default=True)

    # Notifications
    notify_course_updates = models.BooleanField(default=True)
    notify_new_lectures = models.BooleanField(default=True)
    notify_email = models.BooleanField(default=True)
    notify_in_app = models.BooleanField(default=True)
    notify_telegram = models.BooleanField(default=False)

    # Privacy
    profile_visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default="everyone")
    analytics_tracking = models.BooleanField(default=True)

    # Security
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=64, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings for {self.user}"


class LoginHistory(models.Model):
    """
    Records every login event: IP address, device/browser, rough location,
    session key (to allow targeted logout) and whether the session is still active.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="login_history")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device = models.CharField(max_length=255, blank=True, default="Unknown device")
    location = models.CharField(max_length=255, blank=True, default="Unknown location")
    session_key = models.CharField(max_length=40, blank=True, db_index=True)
    logged_in_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    logged_out_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-logged_in_at"]

    def __str__(self):
        return f"{self.user} – {self.ip_address} – {'active' if self.is_active else 'ended'}"
