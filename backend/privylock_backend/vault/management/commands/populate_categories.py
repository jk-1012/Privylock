from django.core.management.base import BaseCommand
from vault.models import DocumentCategory

class Command(BaseCommand):
    help = 'Populates document categories'

    def handle(self, *args, **options):
        categories = [
            {'name': 'Identity Documents', 'icon': '🆔', 'order': 1},
            {'name': 'Vehicle Documents', 'icon': '🚗', 'order': 2},
            {'name': 'Education Documents', 'icon': '🎓', 'order': 3},
            {'name': 'Property Documents', 'icon': '🏠', 'order': 4},
            {'name': 'Financial Documents', 'icon': '💰', 'order': 5},
            {'name': 'Medical Documents', 'icon': '🏥', 'order': 6},
            {'name': 'Credentials', 'icon': '🔐', 'order': 7},
            {'name': 'Other', 'icon': '📄', 'order': 8},
        ]

        for cat in categories:
            DocumentCategory.objects.get_or_create(
                name=cat['name'],
                defaults={
                    'icon': cat['icon'],
                    'display_order': cat['order']
                }
            )

        self.stdout.write(self.style.SUCCESS('Categories populated!'))