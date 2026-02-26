"""
Management command: python manage.py seed_data
Seeds emission factors, creates the default admin user, and inserts sample activity data.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import EmissionFactor, ActivityData, HumanPopulation


class Command(BaseCommand):
    help = 'Seed the database with emission factors, admin user, and sample data.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\n🌿 Seeding database...\n'))

        # 1. Emission factors
        EMISSION_FACTORS = [
            ('electricity',   0.708, 'kg_co2e_per_kwh'),
            ('bus_diesel',    2.68,  'kg_co2e_per_liter'),
            ('canteen_lpg',   2.93,  'kg_co2e_per_kg'),
            ('waste_landfill',1.25,  'kg_co2e_per_kg'),
            ('human_daily',   1.0,   'kg_co2e_per_person_per_day'),
        ]
        for source_type, factor, unit in EMISSION_FACTORS:
            obj, created = EmissionFactor.objects.update_or_create(
                source_type=source_type,
                defaults={'factor': factor, 'factor_unit': unit}
            )
            status = 'created' if created else 'updated'
            self.stdout.write(f"  ✅ Emission factor [{source_type}] {status}")

        # 2. Admin user
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@campus.edu',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS('\n  ✅ Admin user created (admin / admin123)'))
        else:
            self.stdout.write('\n  ℹ️  Admin user already exists.')

        # 3. Sample activity data
        if ActivityData.objects.count() == 0:
            sample_data = [
                ('2025-01-15', 'electricity',   120000, 'kWh'),
                ('2025-02-15', 'electricity',   115000, 'kWh'),
                ('2025-03-15', 'electricity',   118000, 'kWh'),
                ('2025-04-15', 'electricity',   122000, 'kWh'),
                ('2025-05-15', 'electricity',   125000, 'kWh'),
                ('2025-06-15', 'electricity',   130000, 'kWh'),
                ('2025-07-15', 'electricity',   128000, 'kWh'),
                ('2025-08-15', 'electricity',   132000, 'kWh'),
                ('2025-09-15', 'electricity',   126000, 'kWh'),
                ('2025-10-15', 'electricity',   124000, 'kWh'),
                ('2025-11-15', 'electricity',   119000, 'kWh'),
                ('2025-12-15', 'electricity',   117000, 'kWh'),
                ('2025-01-15', 'bus_diesel',    5000,   'Liters'),
                ('2025-02-15', 'bus_diesel',    4800,   'Liters'),
                ('2025-03-15', 'bus_diesel',    5200,   'Liters'),
                ('2025-04-15', 'bus_diesel',    5100,   'Liters'),
                ('2025-05-15', 'bus_diesel',    5300,   'Liters'),
                ('2025-06-15', 'bus_diesel',    5500,   'Liters'),
                ('2025-01-15', 'canteen_lpg',   800,    'kg'),
                ('2025-02-15', 'canteen_lpg',   750,    'kg'),
                ('2025-03-15', 'canteen_lpg',   820,    'kg'),
                ('2025-04-15', 'canteen_lpg',   810,    'kg'),
                ('2025-05-15', 'canteen_lpg',   830,    'kg'),
                ('2025-06-15', 'canteen_lpg',   850,    'kg'),
                ('2025-01-15', 'waste_landfill',2000,   'kg'),
                ('2025-02-15', 'waste_landfill',1900,   'kg'),
                ('2025-03-15', 'waste_landfill',2100,   'kg'),
                ('2025-04-15', 'waste_landfill',2050,   'kg'),
                ('2025-05-15', 'waste_landfill',2200,   'kg'),
                ('2025-06-15', 'waste_landfill',2300,   'kg'),
                # 2024 data for year-over-year comparison
                ('2024-01-15', 'electricity',   110000, 'kWh'),
                ('2024-02-15', 'electricity',   108000, 'kWh'),
                ('2024-03-15', 'electricity',   112000, 'kWh'),
                ('2024-04-15', 'electricity',   115000, 'kWh'),
                ('2024-05-15', 'electricity',   118000, 'kWh'),
                ('2024-06-15', 'electricity',   120000, 'kWh'),
                ('2024-01-15', 'bus_diesel',    4700,   'Liters'),
                ('2024-02-15', 'bus_diesel',    4500,   'Liters'),
                ('2024-03-15', 'bus_diesel',    4900,   'Liters'),
                ('2024-04-15', 'bus_diesel',    4800,   'Liters'),
                ('2024-05-15', 'bus_diesel',    5000,   'Liters'),
                ('2024-06-15', 'bus_diesel',    5200,   'Liters'),
                ('2024-01-15', 'canteen_lpg',   730,    'kg'),
                ('2024-02-15', 'canteen_lpg',   700,    'kg'),
                ('2024-03-15', 'canteen_lpg',   760,    'kg'),
                ('2024-04-15', 'canteen_lpg',   750,    'kg'),
                ('2024-05-15', 'canteen_lpg',   780,    'kg'),
                ('2024-06-15', 'canteen_lpg',   800,    'kg'),
                ('2024-01-15', 'waste_landfill',1800,   'kg'),
                ('2024-02-15', 'waste_landfill',1750,   'kg'),
                ('2024-03-15', 'waste_landfill',1900,   'kg'),
                ('2024-04-15', 'waste_landfill',1850,   'kg'),
                ('2024-05-15', 'waste_landfill',2000,   'kg'),
                ('2024-06-15', 'waste_landfill',2100,   'kg'),
            ]
            from datetime import date as date_cls
            objs = [
                ActivityData(
                    date=date_cls.fromisoformat(d),
                    source_type=st,
                    raw_value=rv,
                    unit=u
                )
                for d, st, rv, u in sample_data
            ]
            ActivityData.objects.bulk_create(objs)
            self.stdout.write(self.style.SUCCESS(f'\n  ✅ Inserted {len(objs)} sample activity records'))
        else:
            self.stdout.write('\n  ℹ️  Activity data already exists, skipping sample insert.')

        # 4. Sample human population data
        if HumanPopulation.objects.count() == 0:
            from datetime import date as date_cls
            human_samples = [
                ('2025-01-15', 4800, 520),
                ('2025-02-15', 4900, 530),
                ('2025-03-15', 5000, 540),
                ('2025-04-15', 5100, 550),
                ('2025-05-15', 4950, 510),
                ('2025-06-15', 4700, 500),
                ('2025-07-15', 3200, 480),
                ('2025-08-15', 3400, 490),
                ('2025-09-15', 5200, 560),
                ('2025-10-15', 5300, 570),
                ('2025-11-15', 5100, 555),
                ('2025-12-15', 4600, 510),
            ]
            objs = [
                HumanPopulation(date=date_cls.fromisoformat(d), student_count=sc, staff_count=sf)
                for d, sc, sf in human_samples
            ]
            HumanPopulation.objects.bulk_create(objs)
            self.stdout.write(self.style.SUCCESS(f'\n  ✅ Inserted {len(objs)} sample human population records'))
        else:
            self.stdout.write('\n  ℹ️  Human population data already exists, skipping.')

        self.stdout.write(self.style.SUCCESS('\n🎯 Database seeding completed successfully!\n'))
