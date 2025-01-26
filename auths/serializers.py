from rest_framework import serializers
from .models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    skills = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=[],
        write_only=True
    )
    class Meta:
        model = CustomUser
        fields = [
            'id',
            'email',
            'password',
            'full_name',
            'skills',
            'resume',
            'github',
            'linkedin',
            'role',
            'github_score'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'full_name': {'required': False},
            'skills': {'required': False},
            'resume': {'required': False},
            'github': {'required': False},
            'linkedin': {'required': False},
            'role': {'required': False},
            'github_score': {'read_only': True}
        }

    def validate_email(self, value):
        if self.instance and self.instance.email == value:
            return value
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        user = CustomUser(
            email=validated_data['email'],
            full_name=validated_data.get('full_name', ''),
            skills=validated_data.get('skills', ''),
            resume=validated_data.get('resume', ''),
            github=validated_data.get('github', ''),
            linkedin=validated_data.get('linkedin', ''),
            role=validated_data.get('role', 'participant')
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            instance.set_password(validated_data.pop('password'))

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()
        return instance
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.skills:
            data['skills'] = [skill.strip() for skill in instance.skills.split(',')]
        else:
            data['skills'] = []
        return data

    def to_internal_value(self, data):
        if 'skills' in data and isinstance(data['skills'], list):
            data['skills'] = ','.join([str(skill).strip() for skill in data['skills']])
        return super().to_internal_value(data)