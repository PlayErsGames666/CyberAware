# Generated manually – populate Course and Lecture data

from django.db import migrations


def create_courses_and_lectures(apps, schema_editor):
    Course = apps.get_model("members", "Course")
    Lecture = apps.get_model("members", "Lecture")

    courses_data = [
        {
            "slug": "cti",
            "title": "Cyber Threat Intelligence",
            "description": "Learn how to collect, analyze, and use threat intelligence to predict attacks, prioritize risks, and make better security decisions.",
            "lectures": [
                ("Lecture 1", "Threat Intelligence Basics", "Threat intelligence basics: sources, types (strategic/operational/tactical), and the intel lifecycle. Understanding how TI supports decision-making and how to integrate it into security operations."),
                ("Lecture 2", "IOC, IOA and ATT&CK", "IOC vs IOA, ATT&CK mapping, and how to turn raw indicators into actionable detections. Building detection rules and aligning them with adversary behavior."),
                ("Lecture 3", "Threat Actor Profiling", "Threat actor profiling, TTPs, reporting structure, and communicating risk to stakeholders. Writing clear TI reports and briefing non-technical audiences."),
                ("Lecture 4", "Collection and Automation", "Collection & automation: feeds, enrichment, scoring, and basic TI workflows for a SOC. Integrating open-source and commercial feeds into your pipeline."),
            ],
        },
        {
            "slug": "df",
            "title": "Digital Forensics",
            "description": "Understand how to preserve evidence, investigate incidents, and reconstruct what happened using logs, disk artifacts, and memory analysis.",
            "lectures": [
                ("Lecture 1", "Introduction to Digital Forensics", "Introduction to digital forensics: principles of evidence, chain of custody, and legal considerations. Role of forensics in incident response and criminal investigations."),
                ("Lecture 2", "Disk and File System Analysis", "Disk and file system analysis: imaging, recovery of deleted files, timeline analysis. Using common tools to extract artifacts from Windows and Linux systems."),
                ("Lecture 3", "Memory Forensics", "Memory forensics: capturing RAM, analyzing processes and network connections, detecting malware and rootkits. Volatility and modern memory analysis techniques."),
                ("Lecture 4", "Log Analysis and Reporting", "Log analysis and correlation: event logs, network logs, and building a timeline. Writing forensic reports and presenting findings in court or to management."),
            ],
        },
        {
            "slug": "wh",
            "title": "White Hacker",
            "description": "Practice ethical hacking foundations: reconnaissance, common vulnerabilities, and safe exploitation methods to improve defenses.",
            "lectures": [
                ("Lecture 1", "Ethics and Reconnaissance", "Ethical hacking overview: scope, authorization, and legal boundaries. Passive and active reconnaissance, OSINT, and footprinting without crossing legal lines."),
                ("Lecture 2", "Common Vulnerabilities", "Common vulnerabilities: OWASP Top 10, misconfigurations, and weak authentication. Identifying and documenting findings in a structured way."),
                ("Lecture 3", "Exploitation Basics", "Safe exploitation basics: proof-of-concept without causing damage, using labs and CTF environments. Understanding exploit development and mitigation."),
                ("Lecture 4", "Reporting and Remediation", "Reporting and remediation: writing clear findings, risk ratings, and working with developers to fix issues. Building a sustainable offensive security program."),
            ],
        },
        {
            "slug": "aics",
            "title": "AI Cyber Security",
            "description": "Explore how AI is used in security: anomaly detection, phishing detection, SOC automation, and the risks of adversarial ML.",
            "lectures": [
                ("Lecture 1", "AI in Security Overview", "AI in security: overview of ML applications—anomaly detection, classification, and automation. Where AI helps and where it can mislead in SOC and threat detection."),
                ("Lecture 2", "Phishing and Malware Detection", "Phishing and malware detection with ML: feature extraction, model types, and real-world deployment. Handling false positives and keeping models up to date."),
                ("Lecture 3", "SOC Automation and SOAR", "SOC automation and SOAR: using AI to triage alerts, automate playbooks, and reduce analyst fatigue. Integration with SIEM and ticketing systems."),
                ("Lecture 4", "Adversarial ML and Risks", "Adversarial ML and AI risks: evasion, poisoning, and model theft. Defending ML systems and understanding the limits of AI in security."),
            ],
        },
    ]

    for c in courses_data:
        course = Course.objects.create(
            slug=c["slug"],
            title=c["title"],
            description=c["description"],
        )
        for order, (title, heading, content) in enumerate(c["lectures"], start=1):
            Lecture.objects.create(
                course=course,
                order=order,
                title=title,
                heading=heading,
                content=content,
            )


def reverse_populate(apps, schema_editor):
    Course = apps.get_model("members", "Course")
    Course.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0004_add_course_lecture"),
    ]

    operations = [
        migrations.RunPython(create_courses_and_lectures, reverse_populate),
    ]
