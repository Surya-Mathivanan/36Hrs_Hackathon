from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ActivityData, HumanPopulation, EmissionFactor, CollegeProfile


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class EmissionFactorSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionFactor
        fields = ['id', 'source_type', 'factor', 'factor_unit']


class ActivityDataSerializer(serializers.ModelSerializer):
    emissions_tonnes = serializers.ReadOnlyField()

    class Meta:
        model = ActivityData
        fields = ['id', 'date', 'source_type', 'raw_value', 'unit', 'emissions_tonnes', 'created_at']

    def validate_source_type(self, value):
        allowed = ['electricity', 'bus_diesel', 'canteen_lpg', 'waste_landfill']
        if value not in allowed:
            raise serializers.ValidationError(
                f"Invalid source_type. Must be one of: {', '.join(allowed)}"
            )
        return value

    def validate_raw_value(self, value):
        if value <= 0:
            raise serializers.ValidationError("raw_value must be positive.")
        return value


class ActivityDataBulkSerializer(serializers.Serializer):
    """For bulk CSV upload."""
    records = serializers.ListField(
        child=serializers.DictField(),
        min_length=1
    )


class HumanPopulationSerializer(serializers.ModelSerializer):
    total_count = serializers.ReadOnlyField()
    emissions_tonnes = serializers.ReadOnlyField()

    class Meta:
        model = HumanPopulation
        fields = ['id', 'date', 'student_count', 'staff_count', 'total_count', 'emissions_tonnes', 'created_at']

    def validate_student_count(self, value):
        if value < 0:
            raise serializers.ValidationError("student_count must be non-negative.")
        return value

    def validate_staff_count(self, value):
        if value < 0:
            raise serializers.ValidationError("staff_count must be non-negative.")
        return value


class CollegeProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollegeProfile
        fields = [
            'id', 'college_name', 'tagline', 'address',
            'contact_email', 'contact_phone', 'website',
            'logo_emoji', 'established_year', 'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']
