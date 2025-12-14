from django.urls import path
from .views import CreatePostView, ViewPostsView, BuyProductView, MarketPricesListView, CreateMarketPriceView, AISuggestionsView, AutoRefreshPricesView, WelcomeView, SendMessageView, CreateOrderView, MyOrdersView, MyDashboardStatsView

urlpatterns = [
    path('', ViewPostsView.as_view(), name='view_posts'),
    path('new/', CreatePostView.as_view(), name='create_post'),
    path('buy/<int:pk>/', BuyProductView.as_view(), name='buy_product'),
    path('order/', CreateOrderView.as_view(), name='create_order'),
    path('my-orders/', MyOrdersView.as_view(), name='my_orders'),
    path('dashboard-stats/', MyDashboardStatsView.as_view(), name='dashboard_stats'),
    path('market-prices/', MarketPricesListView.as_view(), name='market_prices'),
    path('market-prices/create/', CreateMarketPriceView.as_view(), name='create_market_price'),
    path('market-prices/ai-suggestions/', AISuggestionsView.as_view(), name='ai_suggestions'),
    path('market-prices/auto-refresh/', AutoRefreshPricesView.as_view(), name='auto_refresh_prices'),
    path('welcome/', WelcomeView.as_view(), name='welcome'),
    path('send-message/<int:pk>/', SendMessageView.as_view(), name='send_message'),
]
