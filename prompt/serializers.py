# prompt/serializers.py

from rest_framework import serializers
from .models import Tag, PromptCategory, WritingPrompt

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

class PromptCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptCategory
        fields = ['id', 'name', 'description', 'slug']

class WritingPromptSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    tags = TagSerializer(many=True, read_only=True)
    
    class Meta:
        model = WritingPrompt
        fields = ['id', 'text', 'category', 'category_name', 'difficulty', 
                  'prompt_type', 'created_at', 'tags']
        