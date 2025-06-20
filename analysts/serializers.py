from rest_framework import serializers

from .models import Analyst


class AnalystSerializer(serializers.ModelSerializer):

    class Meta:
        model = Analyst
        fields = ['id', 'first_name','last_name', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}  #We will not return the password when we created user successfully


    def create(self, validated_data):
        password = validated_data.pop('password',None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
           instance.set_password(password) #set_password hash the pwd py default
        instance.save()
        return instance