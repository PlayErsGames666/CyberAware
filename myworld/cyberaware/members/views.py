from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
import json
from .models import Member, Course, Lecture, LectureQuestion, MemberLectureProgress


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


def members(request):
    mymembers = Member.objects.all().values()
    template = loader.get_template('mainpage.html')
    context = {
        'mymembers': mymembers,
    }
    return HttpResponse(template.render(context, request))


def login_view(request):
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
                    return redirect(next_url)

                # 2. If user does not exist — create new account (registration)
                User = get_user_model()
                existing = User.objects.filter(username=email).first()

                if existing is not None:
                    message = "Invalid email or password."
                else:
                    user = User.objects.create_user(username=email, email=email, password=password)
                    Member.objects.create(
                        user=user,
                        first_name=email.split("@")[0],
                        last_name="",
                        phone=None,
                        joined_date=None,
                    )
                    login(request, user)
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

    for q in questions:
        submitted = str(payload.get(f"q_{q.id}", "")).strip().upper()
        if submitted != q.correct_option:
            all_correct = False
            incorrect_questions.append(q.id)

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
    achievements = [
        {
            "title": "First Steps",
            "subtitle": "Completed your first lecture",
            "icon": "pulse",
        },
        {
            "title": "Risk Watcher",
            "subtitle": "Reviewed basic cyber risks",
            "icon": "alert",
        },
    ]

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
            "achievements": achievements,
            "member": member,
            "user": user,
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
    Simple settings page that uses the standalone settings.html
    template. Behaviour is a static prototype for now.
    """
    return render(request, "settings.html")
