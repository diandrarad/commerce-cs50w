from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create_listing", views.create_listing, name="create_listing"),
    path("listing/<int:listing_id>", views.listing, name="listing"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("bid", views.bid, name="bid"),
    path("close_listing", views.close_listing, name="close_listing"),
    path("add_comment", views.add_comment, name="add_comment"),
    path("categories", views.categories, name="categories"),
    path("category_listings/<int:category_id>", views.category_listings, name="category_listings"),
]
