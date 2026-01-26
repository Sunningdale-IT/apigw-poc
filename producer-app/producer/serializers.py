from rest_framework import serializers
from .models import ProducedData


class ProducedDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProducedData
        fields = ['id', 'value', 'timestamp', 'producer']
        read_only_fields = ['id', 'timestamp']
