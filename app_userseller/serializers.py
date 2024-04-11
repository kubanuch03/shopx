from rest_framework import serializers
from .models import SellerProfile
from product.serializers import Product
from Category.serializers import CategorySerializer, PodCategorySerializer


    
    
class SellerRegisterSerializer(serializers.ModelSerializer):
    email_or_phone = serializers.EmailField(required=True)
    password = serializers.CharField(required=True,write_only=True)
    password_confirm = serializers.CharField(required=True,write_only=True)
    shop_name= serializers.CharField(required=False)

    class Meta:
        model = SellerProfile
        fields = ['email_or_phone','password','password_confirm','shop_name','location_latitude',
                  'location_longitude',]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Пароли не совпадают")
        return attrs
    

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = SellerProfile.objects.create_user(**validated_data)
        user.is_seller = True
        user.save()
        return user
    

class BecomeSellerSerializer(serializers.Serializer):


    def create(self, validated_data):
        return SellerProfile.objects.create(**validated_data)
    
class VerifyCodeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = SellerProfile
        fields = ['code']


class LoginSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=True)
    email_or_phone = serializers.CharField(required=True)
    
    class Meta:
        ref_name = "SellerLogin"
        model = SellerProfile
        fields = ['email_or_phone','password']
    
    def validate(self, attrs):
        email_or_phone = attrs.get('email_or_phone')
        password = attrs.get('password')

        if not email_or_phone or not password:
            raise serializers.ValidationError("Both email/phone and password are required")

        return attrs


# class ChangePasswordSerializer(serializers.Serializer):
#     old_password = serializers.CharField(write_only=True)
#     new_password = serializers.CharField(write_only=True)
#     confirm_new_password = serializers.CharField(write_only=True)
    
#     class Meta:
#         fields = ['old_password',
#                   'new_password',
#                   'confirm_new_password',]

class SendCodeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = SellerProfile
        fields = ['email_or_phone']


# class ForgetPasswordSerializer(serializers.Serializer):
#     code = serializers.CharField(max_length=6,write_only=True)
#     password = serializers.CharField(max_length=20,write_only=True)
#     confirm_password = serializers.CharField(max_length=20,write_only=True)

#     class Meta:
#         fields = ['password','confirm_password','code']



# class UserProfileSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = CustomUser
#         fields = ['username',
#                   'surname',
#                   'email_or_phone',
#                   'number',
#                   'gender',
#                   ]
        
# class SellerProfileSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = SellerProfile
#         fields = [
#                 #   'number',
#                   'shop_name',
#                   'address',
#                   'location_latitude',
#                   'location_longitude',
#                   'email_or_phone',
#                   'category_sc',

#                   'instagram_link',
#                   'whatsapp_link',
#                   'tiktok_link',
#                   'facebook_link',
#                   ]
        








# class ProductSerializerForMarket(serializers.ModelSerializer):
#     category = CategorySerializer()
#     podcategory = PodCategorySerializer()

#     class Meta:
#         model = Product
#         fields = ['name','category','podcategory']
        

        
# class MarketSerializer(serializers.ModelSerializer):
#     products = ProductSerializerForMarket(many=True, read_only=True)
    
#     class Meta:
#         model = SellerProfile
#         fields = ('shop_name','products', 'location_latitude',
#                   'location_longitude', 'number', 'email_or_phone', 'is_verified','whatsapp_link','instagram_link','facebook_link','tiktok_link')



# class LogoutSerializer(serializers.Serializer):
#     refresh_token = serializers.CharField()

#     class Meta:
#         fields = ['refresh_token',]