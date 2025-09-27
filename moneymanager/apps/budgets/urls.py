from django.urls import path
from . import views

app_name = 'budgets'

urlpatterns = [
    # Budget URLs
    path('', views.BudgetListView.as_view(), name='list'),
    path('create/', views.BudgetCreateView.as_view(), name='create'),
    path('<uuid:pk>/', views.budget_detail, name='detail'),
    path('<uuid:pk>/edit/', views.BudgetUpdateView.as_view(), name='update'),

    # Budget Goals
    path('goals/', views.BudgetGoalListView.as_view(), name='goals'),
    path('goals/create/', views.BudgetGoalCreateView.as_view(), name='goal_create'),
    path('goals/<uuid:pk>/progress/', views.goal_update_progress, name='goal_progress'),

    # Analytics
    path('analytics/', views.budget_analytics, name='analytics'),
]