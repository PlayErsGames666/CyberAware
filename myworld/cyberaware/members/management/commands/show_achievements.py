from django.core.management.base import BaseCommand
from members.views import ACHIEVEMENT_CATEGORIES


class Command(BaseCommand):
    help = 'Show all available achievements in the system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--category',
            type=str,
            help='Show only specific category (learning, tests, cyber, activity, progress, completion)'
        )

    def handle(self, *args, **options):
        category_filter = options.get('category')

        self.stdout.write(self.style.SUCCESS('\n=== CYBERAWARE ACHIEVEMENTS SYSTEM ===\n'))

        total_achievements = 0

        for category in ACHIEVEMENT_CATEGORIES:
            if category_filter and category['id'] != category_filter:
                continue

            self.stdout.write(f"📂 {category['title']} ({category['icon']})")
            self.stdout.write(f"   Category ID: {category['id']}")
            self.stdout.write("")

            for idx, item in enumerate(category['items'], 1):
                self.stdout.write(f"   {idx}. 🏆 {item['title']}")
                self.stdout.write(f"      Code: {item['code']}")
                self.stdout.write(f"      Description: {item['description']}")
                if 'profile_icon' in item:
                    self.stdout.write(f"      Icon: {item['profile_icon']}")
                self.stdout.write("")

            total_achievements += len(category['items'])
            self.stdout.write(f"   Subtotal: {len(category['items'])} achievements")
            self.stdout.write("-" * 50)
            self.stdout.write("")

        if not category_filter:
            self.stdout.write(f"🎯 TOTAL ACHIEVEMENTS: {total_achievements}")
            self.stdout.write("")

            # Show category summary
            self.stdout.write("📊 CATEGORIES SUMMARY:")
            for category in ACHIEVEMENT_CATEGORIES:
                count = len(category['items'])
                self.stdout.write(f"   • {category['title']}: {count} achievements")

            self.stdout.write(f"\n💡 TIP: Use --category flag to filter by category")
            self.stdout.write(f"   Available categories: {', '.join([cat['id'] for cat in ACHIEVEMENT_CATEGORIES])}")

        self.stdout.write(self.style.SUCCESS('\n✅ Achievement system overview complete!'))
