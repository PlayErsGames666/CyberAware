from django.contrib import admin

from .models import Member, Course, Lecture


class LectureInline(admin.StackedInline):
    model = Lecture
    extra = 0
    ordering = ("order",)


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


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "phone", "joined_date")
    search_fields = ("first_name", "last_name")
    list_filter = ("joined_date",)
