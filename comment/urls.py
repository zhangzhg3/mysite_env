from django.urls import path
from . import views

### start with blog
urlpatterns = [
    ### http://localhost:8000/blog/1
    path('update_comment',views.update_comment,name='update_comment'),
]