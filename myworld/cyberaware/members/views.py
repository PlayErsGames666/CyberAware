from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
import datetime
import json
import re
from .models import (
    Member,
    Course,
    Lecture,
    LectureQuestion,
    MemberLectureProgress,
    MemberDailyActivity,
    MemberQuizAttempt,
    MemberAchievement,
    UserSettings,
    LoginHistory,
)

ACHIEVEMENT_CATEGORIES = [
    {
        "id": "learning",
        "title": "Learning / Content",
        "icon": "book",
        "items": [
            {
                "code": "first_step",
                "title": "First Step",
                "description": "completed first lecture",
                "profile_icon": "pulse",
            },
            {
                "code": "start_of_journey",
                "title": "Start of Journey",
                "description": "completed first module entirely",
                "profile_icon": "pulse",
            },
            {
                "code": "curious",
                "title": "Curious Learner",
                "description": "completed 5 lectures",
                "profile_icon": "pulse",
            },
            {
                "code": "deep_dive",
                "title": "Deep Dive",
                "description": "completed 10 lectures",
                "profile_icon": "pulse",
            },
            {
                "code": "to_the_end",
                "title": "To the End",
                "description": "finished lecture to 100%",
                "profile_icon": "pulse",
            },
            {
                "code": "no_skips",
                "title": "No Skips",
                "description": "completed module without skipping",
                "profile_icon": "pulse",
            },
        ],
    },
    {
        "id": "tests",
        "title": "Tests & Assignments",
        "icon": "check",
        "items": [
            {
                "code": "first_quiz",
                "title": "Knowledge Check",
                "description": "passed first test",
                "profile_icon": "alert",
            },
            {
                "code": "no_mistakes",
                "title": "First Try Success",
                "description": "test passed without errors",
                "profile_icon": "alert",
            },
            {
                "code": "almost_perfect",
                "title": "Almost Perfect",
                "description": "80%+ score",
                "profile_icon": "alert",
            },
            {
                "code": "excellent",
                "title": "Excellent",
                "description": "100% on test",
                "profile_icon": "alert",
            },
            {
                "code": "dont_give_up",
                "title": "Never Give Up",
                "description": "retook test after failure",
                "profile_icon": "alert",
            },
            {
                "code": "all_quizzes",
                "title": "Material Mastered",
                "description": "passed all module tests",
                "profile_icon": "alert",
            },
        ],
    },
    {
        "id": "cyber",
        "title": "Cybersecurity (Thematic)",
        "icon": "shield",
        "items": [
            {
                "code": "passwords",
                "title": "Password Protected",
                "description": "studied password security",
                "profile_icon": "default",
            },
            {
                "code": "phishing",
                "title": "Phishing? Not Today",
                "description": "completed phishing lecture",
                "profile_icon": "default",
            },
            {
                "code": "social_engineering",
                "title": "Trust but Verify",
                "description": "social engineering topic",
                "profile_icon": "default",
            },
            {
                "code": "hygiene",
                "title": "Digital Hygiene",
                "description": "learned basic security rules",
                "profile_icon": "default",
            },
            {
                "code": "safe_start",
                "title": "Safe Start",
                "description": "completed introductory course",
                "profile_icon": "default",
            },
        ],
    },
    {
        "id": "activity",
        "title": "Activity",
        "icon": "flame",
        "items": [
            {
                "code": "streak_2",
                "title": "Coming Back",
                "description": "logged in 2 days in a row",
                "profile_icon": "default",
            },
            {
                "code": "streak_5",
                "title": "Building Habits",
                "description": "5 days in a row",
                "profile_icon": "default",
            },
            {
                "code": "streak_7",
                "title": "Week with Us",
                "description": "7 days in a row",
                "profile_icon": "default",
            },
            {
                "code": "streak_14",
                "title": "Consistency",
                "description": "14 days in a row",
                "profile_icon": "default",
            },
        ],
    },
    {
        "id": "progress",
        "title": "Progress",
        "icon": "level",
        "items": [
            {
                "code": "level_2",
                "title": "Level Up",
                "description": "reached level 2",
                "profile_icon": "default",
            },
            {
                "code": "level_5",
                "title": "Growing Strong",
                "description": "reached level 5",
                "profile_icon": "default",
            },
            {
                "code": "xp_100",
                "title": "Experience Matters",
                "description": "earned 100 XP",
                "profile_icon": "default",
            },
            {
                "code": "xp_500",
                "title": "Experienced",
                "description": "earned 500 XP",
                "profile_icon": "default",
            },
            {
                "code": "xp_1000",
                "title": "Learning Veteran",
                "description": "earned 1000 XP",
                "profile_icon": "default",
            },
        ],
    },
    {
        "id": "completion",
        "title": "Completion",
        "icon": "flag",
        "items": [
            {
                "code": "finish_course",
                "title": "Course Complete",
                "description": "finished course",
                "profile_icon": "default",
            },
            {
                "code": "all_modules",
                "title": "Informed User",
                "description": "completed all modules",
                "profile_icon": "default",
            },
            {
                "code": "cyberaware",
                "title": "CyberAware",
                "description": "unlocked all basic topics",
                "profile_icon": "default",
            },
        ],
    },
]

ACHIEVEMENT_BY_CODE = {}
for category in ACHIEVEMENT_CATEGORIES:
    for item in category["items"]:
        ACHIEVEMENT_BY_CODE[item["code"]] = {
            **item,
            "category_id": category["id"],
            "category_title": category["title"],
            "category_icon": category["icon"],
        }


def _recalculate_member_level(member: Member) -> None:
    """
    Update member.level based on current member.xp.
    Level 0 starts at 0 XP.
    1 lvl requires 100 XP, and each next level requires 1.5x more XP than the previous.
    """
    base_required = 100
    total_xp = member.xp
    level = 0
    required_for_next = base_required

    while total_xp >= required_for_next:
        total_xp -= required_for_next
        level += 1
        required_for_next = int(required_for_next * 1.5)

    member.level = level
    member.save(update_fields=["level"])


def _course_progress_percent(member: Member, course: Course) -> int:
    """
    Calculate user's progress in a course based on completed lectures.
    """
    lectures = course.lectures.all()
    total = lectures.count()
    if total == 0:
        return 0

    completed = MemberLectureProgress.objects.filter(
        member=member,
        lecture__in=lectures,
        completed=True,
    ).count()

    return int((completed / total) * 100)


def _track_daily_activity(member: Member) -> None:
    """
    Mark that member was active today (used for streak achievements).
    """
    if not member:
        return
    today = timezone.localdate()
    MemberDailyActivity.objects.get_or_create(member=member, date=today)


def _calculate_login_streak(member: Member) -> int:
    """
    Calculate how many consecutive days (including today, if active)
    the user has visited the platform.
    """
    entries = list(MemberDailyActivity.objects.filter(member=member).order_by("-date"))
    if not entries:
        return 0

    streak = 1
    previous_date = entries[0].date
    for entry in entries[1:]:
        # Skip duplicates for the same day if any
        if entry.date == previous_date:
            continue
        if previous_date - entry.date == datetime.timedelta(days=1):
            streak += 1
            previous_date = entry.date
        else:
            break
    return streak


def _evaluate_member_achievements(member: Member):
    """
    Evaluate all achievements for the given member based on:
    - lecture progress
    - quiz attempts / results
    - XP / level
    - daily activity streak

    This function also saves new achievements to the database.
    """
    if not member:
        return []

    # Get existing achievements for this member
    existing_achievements = set(
        MemberAchievement.objects.filter(member=member).values_list('code', flat=True)
    )

    earned_codes = set()

    # Progress / XP basics
    total_xp = member.xp
    level = member.level

    lecture_progress_qs = MemberLectureProgress.objects.filter(member=member)
    total_completed_lectures = lecture_progress_qs.filter(completed=True).count()

    courses = list(Course.objects.all())
    any_course_50 = False
    any_course_100 = False
    all_courses_100 = bool(courses)
    any_course_all_quizzes = False

    for course in courses:
        progress = _course_progress_percent(member, course)
        if progress >= 50:
            any_course_50 = True
        if progress == 100:
            any_course_100 = True
        else:
            all_courses_100 = False

        lectures = list(course.lectures.all())
        if lectures:
            completed_in_course = lecture_progress_qs.filter(
                lecture__in=lectures, answered_correctly=True
            ).count()
            if completed_in_course == len(lectures):
                any_course_all_quizzes = True

    # Quiz attempts
    quiz_attempts = MemberQuizAttempt.objects.filter(member=member).order_by(
        "lecture_id", "created_at"
    )

    any_success_attempt = False
    any_100_attempt = False
    any_80_attempt = False
    has_first_try_perfect = False
    passed_after_fail = False

    attempts_by_lecture = {}
    for attempt in quiz_attempts:
        attempts_by_lecture.setdefault(attempt.lecture_id, []).append(attempt)

    for lecture_id, attempts in attempts_by_lecture.items():
        attempts_sorted = sorted(attempts, key=lambda a: a.created_at)
        seen_fail = False
        for att in attempts_sorted:
            # Common stats for both success and fail
            if att.total_questions:
                percent = (att.correct_count / att.total_questions) * 100
                if percent >= 80:
                    any_80_attempt = True
            if att.was_success:
                any_success_attempt = True
                if att.total_questions and att.correct_count == att.total_questions:
                    any_100_attempt = True
                if not seen_fail and att.total_questions and att.correct_count == att.total_questions:
                    has_first_try_perfect = True
                if seen_fail:
                    passed_after_fail = True
                break
            else:
                seen_fail = True

    # Daily activity / streaks
    streak_days = _calculate_login_streak(member)

    # --- Map conditions to achievement codes ---
    # Learning / content
    if total_completed_lectures >= 1:
        earned_codes.add("first_step")
        earned_codes.add("to_the_end")
    if any_course_50:
        earned_codes.add("start_of_journey")
    if total_completed_lectures >= 5:
        earned_codes.add("curious")
    if total_completed_lectures >= 10:
        earned_codes.add("deep_dive")
    if any_course_100:
        earned_codes.add("no_skips")

    # Tests & quizzes
    if any_success_attempt:
        earned_codes.add("first_quiz")
    if has_first_try_perfect:
        earned_codes.add("no_mistakes")
    if any_80_attempt:
        earned_codes.add("almost_perfect")
    if any_100_attempt:
        earned_codes.add("excellent")
    if passed_after_fail:
        earned_codes.add("dont_give_up")
    if any_course_all_quizzes:
        earned_codes.add("all_quizzes")

    # Thematic cyber achievements – based on lecture topics
    # These rely on naming conventions in lecture titles/headings.
    password_lectures = Lecture.objects.filter(
        Q(title__icontains="password") | Q(heading__icontains="password") | Q(title__icontains="парол")
    )
    if password_lectures.exists():
        if lecture_progress_qs.filter(lecture__in=password_lectures, completed=True).exists():
            earned_codes.add("passwords")

    phishing_lectures = Lecture.objects.filter(
        Q(title__icontains="phishing")
        | Q(heading__icontains="phishing")
        | Q(title__icontains="фишинг")
        | Q(heading__icontains="фишинг")
    )
    if phishing_lectures.exists():
        if lecture_progress_qs.filter(lecture__in=phishing_lectures, completed=True).exists():
            earned_codes.add("phishing")

    social_lectures = Lecture.objects.filter(
        Q(title__icontains="social engineering")
        | Q(heading__icontains="social engineering")
        | Q(title__icontains="соц. инженер")
        | Q(title__icontains="социальная инженер")
    )
    if social_lectures.exists():
        if lecture_progress_qs.filter(lecture__in=social_lectures, completed=True).exists():
            earned_codes.add("social_engineering")

    hygiene_lectures = Lecture.objects.filter(
        Q(title__icontains="digital hygiene")
        | Q(heading__icontains="digital hygiene")
        | Q(title__icontains="цифровая гигиена")
        | Q(heading__icontains="цифровая гигиена")
    )
    if hygiene_lectures.exists():
        if lecture_progress_qs.filter(lecture__in=hygiene_lectures, completed=True).exists():
            earned_codes.add("hygiene")

    intro_course = Course.objects.filter(
        Q(slug__in=["intro", "start", "basics"])
        | Q(title__icontains="intro")
        | Q(title__icontains="basic")
        | Q(title__icontains="вводн")
        | Q(title__icontains="основы")
    ).first()
    if intro_course and _course_progress_percent(member, intro_course) == 100:
        earned_codes.add("safe_start")

    # Activity / streak
    if streak_days >= 2:
        earned_codes.add("streak_2")
    if streak_days >= 5:
        earned_codes.add("streak_5")
    if streak_days >= 7:
        earned_codes.add("streak_7")
    if streak_days >= 14:
        earned_codes.add("streak_14")

    # Progress: levels & XP
    if level >= 2:
        earned_codes.add("level_2")
    if level >= 5:
        earned_codes.add("level_5")
    if total_xp >= 100:
        earned_codes.add("xp_100")
    if total_xp >= 500:
        earned_codes.add("xp_500")
    if total_xp >= 1000:
        earned_codes.add("xp_1000")

    # Completion
    if any_course_100:
        earned_codes.add("finish_course")
    if all_courses_100 and courses:
        earned_codes.add("all_modules")
        earned_codes.add("cyberaware")

    # Save new achievements to database
    new_achievements = earned_codes - existing_achievements
    for code in new_achievements:
        MemberAchievement.objects.create(member=member, code=code)

    # Convert codes to rich objects for templates
    earned = []
    for code in sorted(earned_codes):
        meta = ACHIEVEMENT_BY_CODE.get(code)
        if not meta:
            continue
        earned.append(
            {
                "code": code,
                "title": meta["title"],
                "subtitle": meta["description"],
                "icon": meta.get("profile_icon", "default"),
                "category_id": meta["category_id"],
                "category_title": meta["category_title"],
            }
        )
    return earned


def members(request):
    mymembers = Member.objects.all().values()
    template = loader.get_template('mainpage.html')
    context = {
        'mymembers': mymembers,
        'user': request.user,
    }
    return HttpResponse(template.render(context, request))


# ─── Helpers for login tracking ──────────────────────────────────────────────

def _get_client_ip(request):
    """Return the best-guess real IP for the request."""
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _parse_device(request):
    """Return a short human-readable device / browser string from User-Agent."""
    ua = request.META.get("HTTP_USER_AGENT", "")
    if not ua:
        return "Unknown device"

    # OS detection
    if "Windows NT 10" in ua:
        os_name = "Windows 10"
    elif "Windows NT 11" in ua or "Windows NT 10.0; Win64" in ua:
        os_name = "Windows"
    elif "Macintosh" in ua or "Mac OS X" in ua:
        os_name = "macOS"
    elif "iPhone" in ua:
        os_name = "iPhone"
    elif "iPad" in ua:
        os_name = "iPad"
    elif "Android" in ua:
        os_name = "Android"
    elif "Linux" in ua:
        os_name = "Linux"
    else:
        os_name = "Unknown OS"

    # Browser detection
    if "Edg/" in ua or "Edge/" in ua:
        browser = "Edge"
    elif "OPR/" in ua or "Opera" in ua:
        browser = "Opera"
    elif "Chrome/" in ua:
        browser = "Chrome"
    elif "Firefox/" in ua:
        browser = "Firefox"
    elif "Safari/" in ua:
        browser = "Safari"
    else:
        browser = "Browser"

    return f"{browser} on {os_name}"


def _record_login(request, user):
    """Create a LoginHistory entry for this login event."""
    # Mark previous active sessions as inactive first (optional – keep them as-is so
    # the user can see them; we only set is_active=False when they explicitly log out)
    LoginHistory.objects.create(
        user=user,
        ip_address=_get_client_ip(request),
        device=_parse_device(request),
        location="Unknown location",
        session_key=request.session.session_key or "",
    )


def login_view(request):
    # If the user is already logged in, redirect them to profile immediately
    if request.user.is_authenticated:
        next_url = request.GET.get("next") or "profile"
        return redirect(next_url)

    message = ""
    next_url = request.GET.get("next") or request.POST.get("next") or "profile"
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        if not email or not password:
            message = "Please enter both email and password."
        else:
            try:
                validate_email(email)
            except ValidationError:
                message = "Please enter a valid email address."
            else:
                # 1. Try to authenticate as existing user (username = email)
                user = authenticate(request, username=email, password=password)

                if user is not None:
                    login(request, user)
                    # Track daily activity for existing users
                    try:
                        member = Member.objects.get(user=user)
                        _track_daily_activity(member)
                    except Member.DoesNotExist:
                        pass
                    _record_login(request, user)
                    return redirect(next_url)

                # 2. If user does not exist — create new account (registration)
                UserModel = get_user_model()
                existing = UserModel.objects.filter(username=email).first()

                if existing is not None:
                    message = "Invalid email or password."
                else:
                    user = UserModel.objects.create_user(username=email, email=email, password=password)
                    member = Member.objects.create(
                        user=user,
                        first_name=email.split("@")[0],
                        last_name="",
                        phone=None,
                        joined_date=None,
                    )
                    login(request, user)
                    # Track daily activity for new users
                    _track_daily_activity(member)
                    _record_login(request, user)
                    return redirect(next_url)

    return render(request, "login.html", {"message": message, "next": next_url})


def courses_view(request):
    courses = [
        {"id": c.slug, "title": c.title, "description": c.description}
        for c in Course.objects.all()
    ]
    return render(request, "courses.html", {"courses": courses})


def course_lectures_view(request, course_id: str):
    try:
        course = Course.objects.get(slug=course_id)
    except Course.DoesNotExist:
        return render(
            request,
            "lectures.html",
            {
                "course_id": course_id,
                "course_title": "Course",
                "lectures": [],
                "active_lecture": None,
                "message": "Course not found.",
                "progress_percent": 0,
            },
        )

    lectures = list(course.lectures.all())
    if not lectures:
        return render(
            request,
            "lectures.html",
            {
                "course_id": course_id,
                "course_title": course.title,
                "lectures": [],
                "active_lecture": None,
                "message": "Lectures for this course are coming soon.",
                "progress_percent": 0,
            },
        )

    active_id = request.GET.get("lecture")
    if active_id:
        try:
            active_lecture = course.lectures.get(pk=active_id)
        except (Lecture.DoesNotExist, ValueError):
            active_lecture = lectures[0]
    else:
        active_lecture = lectures[0]

    # Calculate per-user course progress, quiz state and XP/level summary
    member = None
    progress_percent = 0
    quiz_completed = False
    member_total_xp = 0
    member_level = 0

    if request.user.is_authenticated:
        try:
            member = Member.objects.get(user=request.user)
        except Member.DoesNotExist:
            member = None

    if member:
        # Keep level in sync with current XP so lecture page and profile
        # always show the same values.
        _recalculate_member_level(member)
        member_total_xp = member.xp
        member_level = member.level

        progress_percent = _course_progress_percent(member, course)
        try:
            lecture_progress = MemberLectureProgress.objects.get(member=member, lecture=active_lecture)
            quiz_completed = lecture_progress.answered_correctly
        except MemberLectureProgress.DoesNotExist:
            quiz_completed = False

    questions = active_lecture.questions.all()

    return render(
        request,
        "lectures.html",
        {
            "course_id": course_id,
            "course_title": course.title,
            "lectures": lectures,
            "active_lecture": active_lecture,
            "message": "",
            "progress_percent": progress_percent,
            "questions": questions,
            "quiz_completed": quiz_completed,
            "member_total_xp": member_total_xp,
            "member_level": member_level,
        },
    )


@login_required
@require_http_methods(["POST"])
def submit_lecture_quiz_view(request, course_id: str, lecture_id: int):
    """
    Handle quiz submission for a lecture.
    Awards XP if all answers are correct and the quiz for this lecture
    was not already passed before.
    """
    try:
        course = Course.objects.get(slug=course_id)
        lecture = course.lectures.get(pk=lecture_id)
    except (Course.DoesNotExist, Lecture.DoesNotExist):
        return JsonResponse({"success": False, "error": "Lecture not found."}, status=404)

    try:
        member = Member.objects.get(user=request.user)
    except Member.DoesNotExist:
        return JsonResponse({"success": False, "error": "Profile not found."}, status=400)

    questions = list(lecture.questions.all())
    if not questions:
        return JsonResponse({"success": False, "error": "No questions for this lecture."}, status=400)

    data = request.POST or request.body
    # Support both regular form POST (request.POST) and JSON
    if not request.POST and request.body:
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (ValueError, AttributeError):
            payload = {}
    else:
        payload = request.POST

    all_correct = True
    incorrect_questions = []
    correct_count = 0

    for q in questions:
        submitted = str(payload.get(f"q_{q.id}", "")).strip().upper()
        if submitted == q.correct_option:
            correct_count += 1
        else:
            all_correct = False
            incorrect_questions.append(q.id)

    # Track this quiz attempt
    MemberQuizAttempt.objects.create(
        member=member,
        lecture=lecture,
        correct_count=correct_count,
        total_questions=len(questions),
        was_success=all_correct
    )

    if not all_correct:
        return JsonResponse(
            {
                "success": False,
                "error": "Some answers are incorrect. Please try again.",
                "incorrect_questions": incorrect_questions,
            },
            status=200,
        )

    # All answers correct – award XP once per lecture for this member
    progress, created = MemberLectureProgress.objects.get_or_create(
        member=member,
        lecture=lecture,
        defaults={"completed": False, "answered_correctly": False},
    )

    gained_xp = 0
    # Give XP the first time the user successfully passes this lecture quiz
    if created or not progress.answered_correctly:
        gained_xp = 25  # XP per lecture quiz
        member.xp += gained_xp
        member.save(update_fields=["xp"])
        _recalculate_member_level(member)

        progress.completed = True
        progress.answered_correctly = True
        progress.xp_awarded += gained_xp
        progress.save(update_fields=["completed", "answered_correctly", "xp_awarded"])

    # Track daily activity
    _track_daily_activity(member)

    # Update achievements after successful quiz completion
    _evaluate_member_achievements(member)

    course_progress = _course_progress_percent(member, course)

    return JsonResponse(
        {
            "success": True,
            "gained_xp": gained_xp,
            "total_xp": member.xp,
            "level": member.level,
            "course_progress": course_progress,
        }
    )


def profile_view(request):
    """
    Simple user profile page that mirrors the layout from the mockup
    but with a cleaner, more modern visual style.
    Requires authentication: redirects to login if user came from main/courses without registering.
    """
    if not request.user.is_authenticated:
        return redirect(f"{reverse('login')}?next={reverse('profile')}")

    user = request.user
    member = None
    if user.is_authenticated:
        try:
            member = Member.objects.get(user=user)
        except Member.DoesNotExist:
            member = None

        if member:
            display_name = f"{member.first_name} {member.last_name}".strip() or user.get_username() or "User"
        else:
            display_name = user.get_full_name() or user.get_username() or "User"
        user_id = f"id:{user.id:06d}"
    else:
        display_name = "Guest"
        user_id = "id:000000"

    # Real XP/level data
    current_xp = 0
    current_level = 0
    xp_to_next = 100
    xp_in_current_level = 0
    xp_required_current_level = 100
    xp_percent = 0

    # Get user achievements
    user_achievements = []
    if member:
        # Ensure level is in sync with XP
        _recalculate_member_level(member)
        current_xp = member.xp
        current_level = member.level

        # Calculate how much XP is needed for current and next level
        base_required = 100
        level = 0
        total_xp_remaining = current_xp
        required_for_next = base_required

        while total_xp_remaining >= required_for_next:
            total_xp_remaining -= required_for_next
            level += 1
            required_for_next = int(required_for_next * 1.5)

        xp_in_current_level = total_xp_remaining
        xp_required_current_level = required_for_next
        xp_to_next = max(required_for_next - total_xp_remaining, 0)
        xp_percent = int((xp_in_current_level / max(xp_required_current_level, 1)) * 100)

        # Evaluate and get user achievements
        user_achievements = _evaluate_member_achievements(member)

        # Create formatted XP progress text
        xp_progress_text = f"Level {current_level} · {xp_in_current_level}/{xp_required_current_level} XP to next level"
    else:
        xp_progress_text = "Level 0 · 0/100 XP to next level"

    return render(
        request,
        "profile.html",
        {
            "display_name": display_name,
            "user_id": user_id,
            "xp_percent": xp_percent,
            "current_xp": current_xp,
            "current_level": current_level,
            "xp_to_next": xp_to_next,
            "xp_required_current_level": xp_required_current_level,
            "xp_in_current_level": xp_in_current_level,
            "xp_progress_text": xp_progress_text,
            "member": member,
            "user": user,
            "achievements": user_achievements,
        },
    )


@require_http_methods(["POST"])
@ensure_csrf_cookie
def update_profile_view(request):
    """
    Update user profile (first_name, last_name, email)
    """
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Not authenticated"}, status=401)

    try:
        data = json.loads(request.body)
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()
        email = data.get("email", "").strip()

        # Get or create Member for this user
        member, created = Member.objects.get_or_create(
            user=request.user,
            defaults={
                "first_name": first_name or request.user.username,
                "last_name": last_name,
                "email": email or request.user.email,
            }
        )

        # Update fields
        if first_name:
            member.first_name = first_name
        if last_name:
            member.last_name = last_name
        if email:
            member.email = email
            # Also update User email if needed
            request.user.email = email
            request.user.save()

        member.save()

        return JsonResponse({
            "success": True,
            "message": "Profile updated successfully",
            "data": {
                "first_name": member.first_name,
                "last_name": member.last_name,
                "email": member.email or request.user.email,
            }
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


def settings_view(request):
    """
    Full settings page: loads UserSettings, LoginHistory, and renders settings.html.
    """
    if not request.user.is_authenticated:
        return redirect("login")

    user_settings, _ = UserSettings.objects.get_or_create(user=request.user)
    login_history = LoginHistory.objects.filter(user=request.user).order_by("-logged_in_at")[:20]
    active_sessions = LoginHistory.objects.filter(user=request.user, is_active=True).order_by("-logged_in_at")

    context = {
        "user_settings": user_settings,
        "login_history": login_history,
        "active_sessions": active_sessions,
        "current_session_key": request.session.session_key or "",
    }
    return render(request, "settings.html", context)


@require_http_methods(["POST"])
def change_password_view(request):
    """AJAX endpoint: change the logged-in user's password."""
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Not authenticated"}, status=401)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        data = request.POST

    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")
    confirm_password = data.get("confirm_password", "")

    if not current_password or not new_password or not confirm_password:
        return JsonResponse({"success": False, "error": "All fields are required."}, status=400)

    if new_password != confirm_password:
        return JsonResponse({"success": False, "error": "New passwords do not match."}, status=400)

    if len(new_password) < 8:
        return JsonResponse({"success": False, "error": "Password must be at least 8 characters."}, status=400)

    from django.contrib.auth import update_session_auth_hash
    user = request.user
    if not user.check_password(current_password):
        return JsonResponse({"success": False, "error": "Current password is incorrect."}, status=400)

    user.set_password(new_password)
    user.save()
    update_session_auth_hash(request, user)
    return JsonResponse({"success": True, "message": "Password changed successfully."})


@require_http_methods(["POST"])
def logout_all_devices_view(request):
    """Invalidate every session except the current one, mark LoginHistory inactive."""
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Not authenticated"}, status=401)

    current_key = request.session.session_key

    # Flush all stored sessions for this user via the session engine
    from django.contrib.sessions.models import Session
    from django.utils import timezone as tz
    all_sessions = Session.objects.filter(expire_date__gte=tz.now())
    for session in all_sessions:
        try:
            data = session.get_decoded()
            uid = data.get("_auth_user_id")
            if uid and int(uid) == request.user.pk and session.session_key != current_key:
                session.delete()
        except Exception:
            pass

    # Mark all other LoginHistory entries as inactive
    LoginHistory.objects.filter(
        user=request.user, is_active=True
    ).exclude(session_key=current_key).update(
        is_active=False,
        logged_out_at=timezone.now()
    )

    return JsonResponse({"success": True, "message": "Logged out from all other devices."})


@require_http_methods(["POST"])
def logout_session_view(request):
    """Log out a single session by session_key."""
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Not authenticated"}, status=401)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        data = request.POST

    session_key = data.get("session_key", "")
    if not session_key:
        return JsonResponse({"success": False, "error": "session_key required"}, status=400)

    if session_key == request.session.session_key:
        return JsonResponse({"success": False, "error": "Cannot log out current session here."}, status=400)

    from django.contrib.sessions.models import Session
    Session.objects.filter(session_key=session_key).delete()
    LoginHistory.objects.filter(
        user=request.user, session_key=session_key
    ).update(is_active=False, logged_out_at=timezone.now())

    return JsonResponse({"success": True, "message": "Session terminated."})


@require_http_methods(["POST"])
def toggle_2fa_view(request):
    """Toggle two-factor authentication for the user."""
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Not authenticated"}, status=401)

    user_settings, _ = UserSettings.objects.get_or_create(user=request.user)
    user_settings.two_factor_enabled = not user_settings.two_factor_enabled
    user_settings.save()

    state = "enabled" if user_settings.two_factor_enabled else "disabled"
    return JsonResponse({
        "success": True,
        "enabled": user_settings.two_factor_enabled,
        "message": f"Two-factor authentication {state}."
    })


@require_http_methods(["POST"])
def save_notifications_view(request):
    """Save notification preferences."""
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Not authenticated"}, status=401)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        data = request.POST

    user_settings, _ = UserSettings.objects.get_or_create(user=request.user)
    user_settings.notify_course_updates = bool(data.get("notify_course_updates", False))
    user_settings.notify_new_lectures = bool(data.get("notify_new_lectures", False))
    user_settings.notify_email = bool(data.get("notify_email", False))
    user_settings.notify_in_app = bool(data.get("notify_in_app", False))
    user_settings.notify_telegram = bool(data.get("notify_telegram", False))
    user_settings.save()

    return JsonResponse({"success": True, "message": "Notification preferences saved."})


@require_http_methods(["POST"])
def save_appearance_view(request):
    """Save appearance / UI preferences."""
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Not authenticated"}, status=401)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        data = request.POST

    user_settings, _ = UserSettings.objects.get_or_create(user=request.user)

    theme = data.get("theme", "dark")
    if theme in ("dark", "light", "system"):
        user_settings.theme = theme

    accent = data.get("accent_color", "#38bdf8")
    if re.match(r"^#[0-9a-fA-F]{6}$", accent):
        user_settings.accent_color = accent

    font_size = data.get("font_size", "medium")
    if font_size in ("small", "medium", "large"):
        user_settings.font_size = font_size

    user_settings.compact_mode = bool(data.get("compact_mode", False))
    user_settings.animations_enabled = bool(data.get("animations_enabled", True))
    user_settings.save()

    return JsonResponse({"success": True, "message": "Appearance settings saved.", "settings": {
        "theme": user_settings.theme,
        "accent_color": user_settings.accent_color,
        "font_size": user_settings.font_size,
        "compact_mode": user_settings.compact_mode,
        "animations_enabled": user_settings.animations_enabled,
    }})


@require_http_methods(["POST"])
def save_privacy_view(request):
    """Save privacy preferences."""
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Not authenticated"}, status=401)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        data = request.POST

    user_settings, _ = UserSettings.objects.get_or_create(user=request.user)

    visibility = data.get("profile_visibility", "everyone")
    if visibility in ("everyone", "registered", "only_me"):
        user_settings.profile_visibility = visibility

    user_settings.analytics_tracking = bool(data.get("analytics_tracking", True))
    user_settings.save()

    return JsonResponse({"success": True, "message": "Privacy settings saved."})


@require_http_methods(["GET"])
def export_data_view(request):
    """Export all user data as a JSON download."""
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Not authenticated"}, status=401)

    import json as json_lib

    user = request.user
    try:
        member = Member.objects.get(user=user)
    except Member.DoesNotExist:
        member = None

    user_settings, _ = UserSettings.objects.get_or_create(user=user)

    data = {
        "account": {
            "username": user.username,
            "email": user.email,
            "date_joined": str(user.date_joined),
        },
        "profile": {
            "first_name": member.first_name if member else "",
            "last_name": member.last_name if member else "",
            "xp": member.xp if member else 0,
            "level": member.level if member else 0,
        } if member else {},
        "settings": {
            "theme": user_settings.theme,
            "accent_color": user_settings.accent_color,
            "compact_mode": user_settings.compact_mode,
            "font_size": user_settings.font_size,
            "animations_enabled": user_settings.animations_enabled,
            "notify_course_updates": user_settings.notify_course_updates,
            "notify_new_lectures": user_settings.notify_new_lectures,
            "notify_email": user_settings.notify_email,
            "notify_in_app": user_settings.notify_in_app,
            "notify_telegram": user_settings.notify_telegram,
            "profile_visibility": user_settings.profile_visibility,
            "analytics_tracking": user_settings.analytics_tracking,
        },
        "login_history": [
            {
                "ip": str(lh.ip_address),
                "device": lh.device,
                "location": lh.location,
                "logged_in_at": str(lh.logged_in_at),
                "is_active": lh.is_active,
            }
            for lh in LoginHistory.objects.filter(user=user).order_by("-logged_in_at")[:50]
        ],
        "achievements": [
            {"code": a.code, "earned_at": str(a.earned_at)}
            for a in MemberAchievement.objects.filter(member=member)
        ] if member else [],
    }

    response = HttpResponse(
        json_lib.dumps(data, indent=2, ensure_ascii=False),
        content_type="application/json",
    )
    response["Content-Disposition"] = f'attachment; filename="cyberaware_data_{user.username}.json"'
    return response


@require_http_methods(["POST"])
def delete_account_view(request):
    """Permanently delete the user account after password confirmation."""
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Not authenticated"}, status=401)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        data = request.POST

    password = data.get("password", "")
    if not password:
        return JsonResponse({"success": False, "error": "Password is required to delete your account."}, status=400)

    if not request.user.check_password(password):
        return JsonResponse({"success": False, "error": "Incorrect password."}, status=400)

    from django.contrib.auth import logout as auth_logout
    user = request.user
    auth_logout(request)
    user.delete()

    return JsonResponse({"success": True, "message": "Account deleted. Goodbye.", "redirect": "/"})


def logout_view(request):
    """Log out the current user and redirect to the main page."""
    if request.user.is_authenticated:
        # Mark current session as inactive in login history
        session_key = request.session.session_key
        if session_key:
            LoginHistory.objects.filter(
                user=request.user,
                session_key=session_key,
                is_active=True,
            ).update(is_active=False, logged_out_at=timezone.now())
        logout(request)
    return redirect("members")


def achievements_view(request):
    """
    Static Achievements page that groups all badges into categories.
    This is a catalogue of what can be earned in CyberAware.
    """
    categories = [
        {
            "id": "learning",
            "title": "Обучение / Контент",
            "icon": "book",
            "items": [
                {"code": "first_step", "title": "Первый шаг", "description": "прочитал первую лекцию"},
                {"code": "start_of_journey", "title": "Начало пути", "description": "прошёл первый модуль целиком"},
                {"code": "curious", "title": "Любознательный", "description": "прочитал 5 лекций"},
                {"code": "deep_dive", "title": "Погружение", "description": "прочитал 10 лекций"},
                {"code": "to_the_end", "title": "До конца", "description": "дочитал лекцию до 100%"},
                {"code": "no_skips", "title": "Без пропусков", "description": "прошёл модуль без скипов"},
            ],
        },
        {
            "id": "tests",
            "title": "Тесты и задания",
            "icon": "check",
            "items": [
                {"code": "first_quiz", "title": "Проверка знаний", "description": "прошёл первый тест"},
                {"code": "no_mistakes", "title": "Сдал с первого раза", "description": "тест пройден без ошибок"},
                {"code": "almost_perfect", "title": "Почти идеально", "description": "результат 80%+"},
                {"code": "excellent", "title": "Отличник", "description": "100% за тест"},
                {"code": "dont_give_up", "title": "Не сдаюсь", "description": "перепрошёл тест после ошибки"},
                {"code": "all_quizzes", "title": "Закрепил материал", "description": "прошёл все тесты модуля"},
            ],
        },
        {
            "id": "cyber",
            "title": "Кибербезопасность (тематические)",
            "icon": "shield",
            "items": [
                {"code": "passwords", "title": "Пароль под замком", "description": "изучил тему паролей"},
                {"code": "phishing", "title": "Фишинг? Не сегодня", "description": "прошёл лекцию про фишинг"},
                {"code": "social_engineering", "title": "Доверяй, но проверяй", "description": "тема соц. инженерии"},
                {"code": "hygiene", "title": "Цифровая гигиена", "description": "изучил базовые правила безопасности"},
                {"code": "safe_start", "title": "Безопасный старт", "description": "завершил вводный курс"},
            ],
        },
        {
            "id": "activity",
            "title": "Активность",
            "icon": "flame",
            "items": [
                {"code": "streak_2", "title": "Возвращаюсь", "description": "зашёл 2 дня подряд"},
                {"code": "streak_5", "title": "Привычка", "description": "5 дней подряд"},
                {"code": "streak_7", "title": "Неделя с нами", "description": "7 дней подряд"},
                {"code": "streak_14", "title": "Постоянство", "description": "14 дней подряд"},
            ],
        },
        {
            "id": "progress",
            "title": "Прогресс",
            "icon": "level",
            "items": [
                {"code": "level_2", "title": "Первый уровень", "description": "достиг уровня 2"},
                {"code": "level_5", "title": "Расту", "description": "достиг уровня 5"},
                {"code": "xp_100", "title": "Опыт имеет значение", "description": "100 XP"},
                {"code": "xp_500", "title": "На опыте", "description": "500 XP"},
                {"code": "xp_1000", "title": "Ветеран обучения", "description": "1000 XP"},
            ],
        },
        {
            "id": "completion",
            "title": "Завершение",
            "icon": "flag",
            "items": [
                {"code": "finish_course", "title": "Финиш", "description": "завершил курс"},
                {"code": "all_modules", "title": "Осознанный пользователь", "description": "прошёл все модули"},
                {"code": "cyberaware", "title": "CyberAware", "description": "открыл все базовые темы"},
            ],
        },
    ]

    return render(request, "achievements.html", {"categories": categories})
