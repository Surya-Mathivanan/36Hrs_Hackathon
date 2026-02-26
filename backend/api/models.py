from django.db import models


class EmissionFactor(models.Model):
    """Emission conversion factors per source type."""
    source_type = models.CharField(max_length=100, unique=True)
    factor = models.FloatField()
    factor_unit = models.CharField(max_length=50)

    class Meta:
        db_table = 'emission_factors'

    def __str__(self):
        return f"{self.source_type}: {self.factor} {self.factor_unit}"


class ActivityData(models.Model):
    """Daily campus activity consumption records."""
    SOURCE_CHOICES = [
        ('electricity', 'Electricity'),
        ('bus_diesel', 'Bus Diesel'),
        ('canteen_lpg', 'Canteen LPG'),
        ('waste_landfill', 'Waste (Landfill)'),
    ]

    date = models.DateField()
    source_type = models.CharField(max_length=100, choices=SOURCE_CHOICES)
    raw_value = models.FloatField()
    unit = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'activity_data'
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} | {self.source_type}: {self.raw_value} {self.unit}"

    @property
    def emissions_tonnes(self):
        """Calculate CO2e emissions in tonnes."""
        try:
            factor = EmissionFactor.objects.get(source_type=self.source_type)
            return (self.raw_value * factor.factor) / 1000
        except EmissionFactor.DoesNotExist:
            return 0.0


class HumanPopulation(models.Model):
    """Daily campus population counts (students + staff)."""
    date = models.DateField(unique=True)
    student_count = models.IntegerField()
    staff_count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'human_population'
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} | Students: {self.student_count} Staff: {self.staff_count}"

    @property
    def total_count(self):
        return self.student_count + self.staff_count

    @property
    def emissions_tonnes(self):
        """1 kg CO2 per person per day."""
        return self.total_count * 1.0 / 1000


class CollegeProfile(models.Model):
    """Singleton: stores college identity info shown on the public dashboard."""
    college_name = models.CharField(max_length=200, default='KIT Campus')
    tagline = models.CharField(max_length=300, default='Supporting UN SDG 13: Climate Action')
    address = models.TextField(default='')
    contact_email = models.EmailField(default='', blank=True)
    contact_phone = models.CharField(max_length=30, default='', blank=True)
    website = models.URLField(default='', blank=True)
    logo_emoji = models.CharField(max_length=10, default='🏫')
    established_year = models.CharField(max_length=10, default='', blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'college_profile'

    def __str__(self):
        return self.college_name

    @classmethod
    def get_singleton(cls):
        """Always return the single profile row, creating it if missing."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
