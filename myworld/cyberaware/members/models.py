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