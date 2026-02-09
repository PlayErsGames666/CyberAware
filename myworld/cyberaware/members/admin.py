from django.contrib import admin

from .models import Member, Course, Lecture, LectureQuestion, MemberLectureProgress


class LectureInline(admin.StackedInline):
    model = Lecture
    extra = 0
    ordering = ("order",)


class LectureQuestionInline(admin.TabularInline):
    model = LectureQuestion
    extra = 1


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("slug", "title")
    search_fields = ("title", "description")
    inlines = [LectureInline]


@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order")
    list_filter = ("course",)
    ordering = ("course", "order")
    inlines = [LectureQuestionInline]


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "phone", "joined_date", "xp", "level")
    search_fields = ("first_name", "last_name")
    list_filter = ("joined_date", "level")


@admin.register(LectureQuestion)
class LectureQuestionAdmin(admin.ModelAdmin):
    list_display = ("lecture", "text", "correct_option")
    list_filter = ("lecture__course",)
    search_fields = ("text",)


@admin.register(MemberLectureProgress)
class MemberLectureProgressAdmin(admin.ModelAdmin):
    list_display = ("member", "lecture", "completed", "answered_correctly", "xp_awarded")
    list_filter = ("completed", "answered_correctly", "lecture__course")
