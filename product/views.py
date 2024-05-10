from rest_framework.response import Response
from rest_framework import generics, response
from rest_framework.viewsets import GenericViewSet
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.filters import SearchFilter, OrderingFilter

from django.db.models import Avg, Count, Q
from django_filters.rest_framework import DjangoFilterBackend

from .serializers import *
from .models import Product, Recall, RecallImages ,Like, Size
from .filters import CustomFilter
from datetime import datetime
from rest_framework import permissions
from .tasks import send_push_notification_recall
# from Shopx.settings import REDIS_TIMEOUT
from django.core.cache import cache
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny



class ProductCreateApiView(CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny, ]  #!!!!! сделать что бы создавать мог только админ и продавец
                       
    # def perform_create(self, serializer):
    #     serializer.save(user=self.request.user)


class ProductListApiView(ListAPIView):
    queryset = Product.objects.all().annotate(rating=Avg("recall__rating"), likes=Count('like'))
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CustomFilter
    search_fields = ["name", "description"]
    ordering_fields = ["name", "price"]

    def HistorySearch(self):
        pass

    def get_queryset(self):
        # Пытаемся получить результат из кеша
        cached_queryset = cache.get('cached_product_queryset')
        if cached_queryset is not None:
            return cached_queryset

        # Если результат не найден в кеше, выполняем запрос к базе данных
        queryset = self._get_queryset_from_database()

        # Кешируем результат на 1 час
        cache.set('cached_product_queryset', queryset, timeout=3600)

        return queryset

    def _get_queryset_from_database(self):
        # Получаем список товаров с аннотацией средней оценки и количества отзывов
        queryset = Product.objects.annotate(
            average_rating=Avg('recall__rating'),
            num_reviews=Count('recall')
        )
        queryset = queryset.order_by('-average_rating')

        # Дополнительно сортируем товары по количеству отзывов (от большего к меньшему)
        queryset = queryset.order_by('-num_reviews')

        return queryset
   



# Представление для получения деталей, обновления и удаления продукта
class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all().annotate(rating=Avg("recall__rating"), likes=Count('like'))
    serializer_class = ProductSerializer
    # permission_classes = [IsSeller, ]

    def perform_update(self, serializer):
        instance = serializer.instance
        instance.price = serializer.apply_discount_to_price(instance.price, serializer.validated_data.get('discount', 0))
        instance.save()


# Представление для получения деталей, обновления и удаления продукта
#====== Recall   ===========================================================

class RecallListApiView(ListAPIView):
    serializer_class = RecallSerializer

    def get_queryset(self):
        pk = self.kwargs.get('pk')
        if pk is not None:
            queryset = Recall.objects.filter(product=pk)
            return queryset
        else:
            
            return Recall.objects.none()


class RecallViewSet(GenericViewSet):
    queryset = Recall.objects.all()
    serializer_class = RecallSerializer
    # permission_classes = [IsBuyer, ]

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        
        product = serializer.validated_data['product']
        rating = serializer.validated_data['rating']
        text = serializer.validated_data['text']    
        print(request.user)
        
        product.rating = product.recall_set.aggregate(Avg('rating'))['rating__avg']
        product.num_reviews = product.recall_set.count()
        product.save()


        title = f"Отзыв от {request.user.username} {datetime.utcnow()}\n{rating}\n{text}"
        
        whom = product.user.device_token
        
        # send_push_notification_recall.delay(title, whom)
        
        return Response({'success':'Отзыв был отправлен продавцу'})
    
    
    def retrieve(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, pk=None):
        instance = self.get_object()
        if instance.user == self.request.user:
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    def partial_update(self, request, pk=None):
        return self.update(request, pk=None)

    def destroy(self, request, pk=None):
        instance = self.get_object()
        if instance.user == self.request.user:
            instance.delete()
            return Response({'success':'Recall is deleted'})


class ReccallImageCreateApiView(generics.CreateAPIView):
    queryset = RecallImages.objects.all()
    serializer_class = RecallImageSerializer
    permission_classes = [permissions.IsAuthenticated]
#====== Like   ===========================================================

class LikeView(generics.RetrieveDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    # permission_classes = [IsBuyer, ]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        like = Like.objects.filter(user=self.request.user, product=instance)
        if like:
            return Response({"success":"Like was already created"})
        else:
            Like.objects.create(user=self.request.user, product=instance)
            return Response("Like created")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        like = Like.objects.filter(user=self.request.user, product=instance)
        if like:
            like.delete()
            return Response({"succes":"Like is deleted"})
        else:
            return Response({"success":"No Like"})
        

#====== Size   ===========================================================

class SizeListApiView(generics.ListAPIView):
    queryset = Size.objects.all()
    serializer_class = SizeSerializer


class SizeDetailApiView(generics.RetrieveAPIView):
    queryset = Size.objects.all()
    serializer_class = SizeSerializer


class SizeCreateApiView(generics.ListCreateAPIView):
    queryset = Size.objects.all()
    serializer_class = SizeSerializer
    permission_classes = [permissions.IsAdminUser]

    def create(self, request, *args, **kwargs):
        sizes = request.data.get('sizes') 
        
        sizes_exists = Size.objects.filter(sizes=sizes).exists()
        if sizes_exists:
            return response.Response({"error": "this size already exists"})
        
        sizes_serializer = self.get_serializer(data=request.data)
        sizes_serializer.is_valid(raise_exception=True)
        sizes_serializer.save()
        return response.Response({"success": f"size created successfully"})


class SizeRUDApiView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Size.objects.all()
    serializer_class = SizeSerializer
    permission_classes = [permissions.IsAdminUser]




