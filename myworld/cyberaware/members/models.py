from django.db import models
from django.contrib.auth import get_user_model

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