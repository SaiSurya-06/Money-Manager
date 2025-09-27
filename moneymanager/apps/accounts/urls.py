from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.SignUpView.as_view(), name='signup'),

    # Profile management
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),

    # Family groups
    path('family-groups/', views.family_groups_list, name='family_groups'),
    path('family-groups/create/', views.family_group_create, name='family_group_create'),
    path('family-groups/<uuid:group_id>/', views.family_group_detail, name='family_group_detail'),
    path('family-groups/<uuid:group_id>/invite/', views.invite_member, name='invite_member'),
    path('family-groups/<uuid:group_id>/remove/<uuid:user_id>/', views.remove_member, name='remove_member'),

    # AJAX endpoints
    path('api/switch-family-group/', views.switch_family_group, name='switch_family_group'),
]