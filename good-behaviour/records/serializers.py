"""
Serializers for Good Behaviour API
"""
from rest_framework import serializers
from .models import Citizen, CriminalRecord


class RecordSerializer(serializers.ModelSerializer):
    """Serializer for a good behaviour record entry."""
    offense_type_display = serializers.CharField(source='get_offense_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = CriminalRecord
        fields = [
            'id', 'offense_type', 'offense_type_display', 'description',
            'offense_date', 'severity', 'severity_display', 'status',
            'status_display', 'sentence', 'fine_amount', 'created_at'
        ]


class CitizenSerializer(serializers.ModelSerializer):
    """Serializer for citizen with good behaviour records."""
    records = RecordSerializer(source='criminal_records', many=True, read_only=True)
    has_record = serializers.BooleanField(source='has_criminal_record', read_only=True)
    record_count = serializers.SerializerMethodField()

    class Meta:
        model = Citizen
        fields = [
            'id', 'citizen_id', 'first_name', 'last_name', 'date_of_birth',
            'email', 'phone', 'address', 'has_record', 'record_count',
            'records', 'created_at'
        ]

    def get_record_count(self, obj):
        return obj.criminal_records.count()


class CitizenListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for citizen list."""
    has_record = serializers.BooleanField(source='has_criminal_record', read_only=True)
    record_count = serializers.SerializerMethodField()

    class Meta:
        model = Citizen
        fields = [
            'id', 'citizen_id', 'first_name', 'last_name',
            'has_record', 'record_count'
        ]

    def get_record_count(self, obj):
        return obj.criminal_records.count()
