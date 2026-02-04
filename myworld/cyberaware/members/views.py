from django.contrib.auth import authenticate, login, get_user_model
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.template import loader
from .models import Member


def members(request):
    mymembers = Member.objects.all().values()
    template = loader.get_template('mainpage.html')
    context = {
        'mymembers': mymembers,
    }
    return HttpResponse(template.render(context, request))


def login_view(request):
    message = ""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            message = "Please enter both login and password."
        else:
            # 1. Попытаться аутентифицировать как существующего пользователя
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect("profile")

            # 2. Если пользователя нет — попробовать создать «регистрацию»
            User = get_user_model()
            try:
                existing = User.objects.filter(username=username).first()
            except Exception:
                existing = None

            if existing is not None:
                # Пользователь существует, но пароль не подходит
                message = "Invalid login or password."
            else:
                # Создаём нового пользователя и базовую запись в Member
                user = User.objects.create_user(username=username, password=password)
                Member.objects.create(
                    first_name=username,
                    last_name="",
                    phone=None,
                    joined_date=None,
                )
                login(request, user)
                return redirect("profile")

    return render(request, "login.html", {"message": message})


def courses_view(request):
    courses = [
        {
            "id": "cti",
            "title": "Cyber Threat Intelligence",
            "description": (
                "Learn how to collect, analyze, and use threat intelligence to predict attacks, "
                "prioritize risks, and make better security decisions."
            ),
        },
        {
            "id": "df",
            "title": "Digital Forensics",
            "description": (
                "Understand how to preserve evidence, investigate incidents, and reconstruct what "
                "happened using logs, disk artifacts, and memory analysis."
            ),
        },
        {
            "id": "wh",
            "title": "White Hacker",
            "description": (
                "Practice ethical hacking foundations: reconnaissance, common vulnerabilities, "
                "and safe exploitation methods to improve defenses."
            ),
        },
        {
            "id": "aics",
            "title": "AI Cyber Security",
            "description": (
                "Explore how AI is used in security: anomaly detection, phishing detection, "
                "SOC automation, and the risks of adversarial ML."
            ),
        },
    ]
    return render(request, "courses.html", {"courses": courses})


def course_lectures_view(request, course_id: str):
    course_titles = {
        "cti": "Cyber Threat Intelligence",
        "df": "Digital Forensics",
        "wh": "White Hacker",
        "aics": "AI Cyber Security",
    }

    if course_id != "cti":
        return render(
            request,
            "lectures.html",
            {
                "course_id": course_id,
                "course_title": course_titles.get(course_id, "Course"),
                "lectures": [],
                "active_lecture": None,
                "message": "Lectures for this course are coming soon.",
                "progress_percent": 0,
            },
        )

    lectures = [
        {
            "id": "l1",
            "title": "Lecture 1",
            "heading": "Lecture Number 1",
            "content": "Threat intelligence basics: sources, types (strategic/operational/tactical), and the intel lifecycle.",
        },
        {
            "id": "l2",
            "title": "Lecture 2",
            "heading": "Lecture Number 2",
            "content": "IOC vs IOA, ATT&CK mapping, and how to turn raw indicators into actionable detections.",
        },
        {
            "id": "l3",
            "title": "Lecture 3",
            "heading": "Lecture Number 3",
            "content": "Threat actor profiling, TTPs, reporting structure, and communicating risk to stakeholders.",
        },
        {
            "id": "l4",
            "title": "Lecture 4",
            "heading": "Lecture Number 4",
            "content": "Collection & automation: feeds, enrichment, scoring, and basic TI workflows for a SOC.",
        },
    ]

    active_id = request.GET.get("lecture") or lectures[0]["id"]
    active_lecture = next((l for l in lectures if l["id"] == active_id), lectures[0])

    completed_count = 0
    progress_percent = int((completed_count / max(len(lectures), 1)) * 100)

    return render(
        request,
        "lectures.html",
        {
            "course_id": course_id,
            "course_title": course_titles[course_id],
            "lectures": lectures,
            "active_lecture": active_lecture,
            "message": "",
            "progress_percent": progress_percent,
        },
    )


def profile_view(request):
    """
    Simple user profile page that mirrors the layout from the mockup
    but with a cleaner, more modern visual style.
    """

    user = request.user
    if user.is_authenticated:
        display_name = user.get_full_name() or user.get_username() or "User"
        user_id = f"id:{user.id:06d}"
    else:
        display_name = "Guest"
        user_id = "id:000000"

    # Placeholder data – can later be replaced with real progress
    xp_percent = 62
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
            "achievements": achievements,
        },
    )


def settings_view(request):
    """
    Simple settings page that uses the standalone settings.html
    template. Behaviour is a static prototype for now.
    """
    return render(request, "settings.html")
