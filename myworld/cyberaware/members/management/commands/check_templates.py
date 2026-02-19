from django.core.management.base import BaseCommand
from django.template import Template, Context, TemplateSyntaxError
import os
import re


class Command(BaseCommand):
    help = 'Check Django templates for common syntax issues and multiline problems'

    def add_arguments(self, parser):
        parser.add_argument(
            '--template',
            type=str,
            help='Check specific template file'
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Automatically fix detected issues'
        )

    def handle(self, *args, **options):
        template_file = options.get('template')
        auto_fix = options.get('fix', False)

        self.stdout.write(self.style.SUCCESS('\n=== DJANGO TEMPLATE CHECKER ===\n'))

        if template_file:
            # Check specific template
            template_path = f"members/templates/{template_file}"
            self.check_template(template_path, auto_fix)
        else:
            # Check all templates in members/templates/
            templates_dir = "members/templates"
            if os.path.exists(templates_dir):
                for filename in os.listdir(templates_dir):
                    if filename.endswith('.html'):
                        template_path = os.path.join(templates_dir, filename)
                        self.check_template(template_path, auto_fix)
            else:
                self.stdout.write(self.style.ERROR(f"Templates directory not found: {templates_dir}"))

        self.stdout.write(self.style.SUCCESS('\n✅ Template check completed!\n'))

    def check_template(self, template_path, auto_fix=False):
        """Check a single template file for issues"""

        if not os.path.exists(template_path):
            self.stdout.write(self.style.ERROR(f"❌ Template not found: {template_path}"))
            return

        self.stdout.write(f"\n📄 Checking: {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.splitlines()

        issues_found = []
        fixes_applied = []

        # Check for multiline Django template tags
        multiline_issues = self.find_multiline_issues(lines)
        if multiline_issues:
            issues_found.extend(multiline_issues)
            if auto_fix:
                content, fixed_lines = self.fix_multiline_issues(content, multiline_issues)
                fixes_applied.extend(fixed_lines)

        # Check for template syntax errors
        try:
            Template(content)
            self.stdout.write("  ✅ Template syntax is valid")
        except TemplateSyntaxError as e:
            issues_found.append(f"Template syntax error: {e}")

        # Check for common issues
        common_issues = self.find_common_issues(lines)
        if common_issues:
            issues_found.extend(common_issues)

        # Report results
        if issues_found:
            self.stdout.write(f"  ⚠️  Found {len(issues_found)} issues:")
            for issue in issues_found:
                self.stdout.write(f"    - {issue}")
        else:
            self.stdout.write("  ✅ No issues found")

        # Apply fixes if requested
        if auto_fix and fixes_applied:
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.stdout.write(f"  🔧 Applied {len(fixes_applied)} fixes:")
            for fix in fixes_applied:
                self.stdout.write(f"    - {fix}")

    def find_multiline_issues(self, lines):
        """Find Django template tags that span multiple lines"""
        issues = []

        for i, line in enumerate(lines):
            line_num = i + 1

            # Check for {% tags that don't close on same line
            if '{%' in line and not '%}' in line:
                issues.append(f"Line {line_num}: Unclosed template tag: {line.strip()}")

            # Check for {{ variables that don't close on same line
            if '{{' in line and not '}}' in line:
                issues.append(f"Line {line_num}: Unclosed variable: {line.strip()}")

            # Check for tags that start on previous line
            if '%}' in line and not '{%' in line:
                if i > 0 and '{%' in lines[i-1] and not '%}' in lines[i-1]:
                    issues.append(f"Lines {line_num-1}-{line_num}: Multiline template tag")

            if '}}' in line and not '{{' in line:
                if i > 0 and '{{' in lines[i-1] and not '}}' in lines[i-1]:
                    issues.append(f"Lines {line_num-1}-{line_num}: Multiline variable")

        return issues

    def find_common_issues(self, lines):
        """Find common template issues"""
        issues = []

        for i, line in enumerate(lines):
            line_num = i + 1

            # Check for mixed quotes in template tags
            if re.search(r'{%.*".*\'.*%}', line) or re.search(r'{%.*\'.*".*%}', line):
                issues.append(f"Line {line_num}: Mixed quotes in template tag")

            # Check for extra spaces in template tags
            if re.search(r'{%\s{2,}', line) or re.search(r'\s{2,}%}', line):
                issues.append(f"Line {line_num}: Extra spaces in template tag")

            # Check for missing spaces around template tags
            if re.search(r'\S{%', line) or re.search(r'%}\S', line):
                issues.append(f"Line {line_num}: Missing spaces around template tag")

        return issues

    def fix_multiline_issues(self, content, issues):
        """Attempt to fix multiline template issues"""
        fixes_applied = []

        # Fix common multiline patterns
        patterns = [
            # Fix avatar display issue
            (
                r'{%\s*if\s+display_name\s*%}\s*{{\s*display_name\|first\|upper\s*}}\s*{%\s*else\s*%}\s*U\s*{%\s*endif\s*%}',
                '{% if display_name %}{{ display_name|first|upper }}{% else %}U{% endif %}',
                'Fixed multiline if-else statement'
            ),
            # Fix general multiline tags
            (
                r'{%([^%]*)%}\s*\n\s*([^{]*){%',
                r'{% \1 \2 %}',
                'Fixed multiline template tag'
            ),
            # Fix multiline variables
            (
                r'{{([^}]*)}}\s*\n\s*([^{]*)\|([^}]*)}',
                r'{{ \1|\3 }}',
                'Fixed multiline variable'
            )
        ]

        for pattern, replacement, description in patterns:
            old_content = content
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
            if content != old_content:
                fixes_applied.append(description)

        return content, fixes_applied
