from rest_framework import serializers
from .models import ConsumedData


class ConsumedDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsumedData
        fields = ['id', 'producer_id', 'value', 'producer_timestamp', 'consumed_at', 'producer_name']
        read_only_fields = ['id', 'consumed_at']
