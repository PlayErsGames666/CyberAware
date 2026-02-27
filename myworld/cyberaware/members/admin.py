from django.contrib import admin

from .models import Member, Course, Lecture, LectureQuestion, MemberLectureProgress, MemberAchievement, MemberQuizAttempt, MemberDailyActivity


class LectureInline(admin.StackedInline):
    model = Lecture
    extra = 0
    ordering = ("order",)
    verbose_name = "Lecture"
    verbose_name_plural = "Lectures"


class LectureQuestionInline(admin.TabularInline):
    model = LectureQuestion
    extra = 1
    verbose_name = "Question"
    verbose_name_plural = "Questions"


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("slug", "title")
    search_fields = ("title", "description")
    inlines = [LectureInline]
    verbose_name = "Course"
    verbose_name_plural = "Courses"


@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order")
    list_filter = ("course",)
    ordering = ("course", "order")
    inlines = [LectureQuestionInline]
    verbose_name = "Lecture"
    verbose_name_plural = "Lectures"


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "phone", "joined_date", "xp", "level")
    search_fields = ("first_name", "last_name", "email")
    list_filter = ("joined_date", "level")
    verbose_name = "Member"
    verbose_name_plural = "Members"


@admin.register(LectureQuestion)
class LectureQuestionAdmin(admin.ModelAdmin):
    list_display = ("lecture", "text", "correct_option")
    list_filter = ("lecture__course",)
    search_fields = ("text",)
    verbose_name = "Quiz Question"
    verbose_name_plural = "Quiz Questions"


@admin.register(MemberLectureProgress)
class MemberLectureProgressAdmin(admin.ModelAdmin):
    list_display = ("member", "lecture", "completed", "answered_correctly", "xp_awarded")
    list_filter = ("completed", "answered_correctly", "lecture__course")
    verbose_name = "Lecture Progress"
    verbose_name_plural = "Lecture Progress"


@admin.register(MemberAchievement)
class MemberAchievementAdmin(admin.ModelAdmin):
    list_display = ("member", "code", "get_achievement_title", "earned_at")
    list_filter = ("code", "earned_at")
    search_fields = ("member__first_name", "member__last_name", "code")
    readonly_fields = ("earned_at",)
    verbose_name = "Achievement"
    verbose_name_plural = "Achievements"

    def get_achievement_title(self, obj):
        from .views import ACHIEVEMENT_BY_CODE
        achievement_data = ACHIEVEMENT_BY_CODE.get(obj.code, {})
        return achievement_data.get('title', obj.code)
    get_achievement_title.short_description = 'Achievement Title'


@admin.register(MemberQuizAttempt)
class MemberQuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("member", "lecture", "correct_count", "total_questions", "get_percentage", "was_success", "created_at")
    list_filter = ("was_success", "lecture__course", "created_at")
    readonly_fields = ("created_at",)
    verbose_name = "Quiz Attempt"
    verbose_name_plural = "Quiz Attempts"

    def get_percentage(self, obj):
        if obj.total_questions > 0:
            return f"{(obj.correct_count / obj.total_questions) * 100:.0f}%"
        return "0%"
    get_percentage.short_description = 'Score %'


@admin.register(MemberDailyActivity)
class MemberDailyActivityAdmin(admin.ModelAdmin):
    list_display = ("member", "date", "last_seen")
    list_filter = ("date",)
    readonly_fields = ("last_seen",)
    verbose_name = "Daily Activity"
    verbose_name_plural = "Daily Activities"
