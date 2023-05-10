from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.contrib import messages
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from decimal import Decimal

from .models import User, Listing, Category, Bid, Comment


def index(request):
    active_listings = Listing.objects.filter(active=True)
    return render(request, "auctions/index.html", {"listings": active_listings})


def listing(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    comments = Comment.objects.filter(listing=listing)
    current_price = listing.current_price()
    highest_bid = listing.bids.aggregate(Max('amount'))['amount__max']
    if highest_bid is None:
        highest_bid = listing.starting_bid
    winning_bid = None
    if not listing.active:
        winning_bid = listing.bids.order_by('-amount').first()
    if request.method == "POST":
        if "add-watchlist" in request.POST:
            user = request.user
            if user not in listing.watchers.all():
                listing.watchers.add(user)
                messages.success(request, "Added to watchlist.")
            else:
                listing.watchers.remove(user)
                messages.success(request, "Removed from watchlist.")
            return redirect("listing", listing_id=listing_id)
        elif "bid" in request.POST:
            try:
                bid_amount = float(request.POST["bid-amount"])
            except ValueError:
                messages.error(request, "Please enter a valid bid amount.")
                return redirect("listing", listing_id=listing_id)
            if bid_amount < listing.starting_bid:
                messages.error(request, "Bid amount must be at least the starting bid.")
                return redirect("listing", listing_id=listing_id)
            elif bid_amount <= highest_bid:
                messages.error(request, "Bid amount must be greater than the current highest bid.")
                return redirect("listing", listing_id=listing_id)
            else:
                bid = Bid(amount=bid_amount, listing=listing, bidder=request.user)
                bid.save()
                messages.success(request, "Bid placed.")
                return redirect("listing", listing_id=listing_id)
        elif "close-auction" in request.POST:
            if request.user == listing.created_by:
                listing.active = False
                listing.save()
                messages.success(request, "Auction closed.")
                return redirect("listing", listing_id=listing_id)
    return render(request, "auctions/listing.html", {
            "listing": listing,
            "comments": comments,
            "current_price": current_price,
            "highest_bid": highest_bid,
            "winning_bid": winning_bid
        })


@login_required
def watchlist(request):
    if request.method == 'POST':
        listing_id = request.POST['listing_id']
        listing = Listing.objects.get(pk=listing_id)
        user = request.user
        if user in listing.watchers.all():
            listing.watchers.remove(user)
        else:
            listing.watchers.add(user)
        return redirect(reverse('listing', args=[listing_id]))

    user = request.user
    watchlist = user.watchlist.all()
    context = {'listings': watchlist}
    return render(request, 'auctions/watchlist.html', context)

def bid(request):
    if request.method == "POST":
        # Get listing and bid amount from form submission
        listing_id = request.POST.get("listing_id")
        bid_amount = Decimal(request.POST.get("bid_amount"))
        
        # Retrieve listing and current highest bid (if any)
        listing = Listing.objects.get(pk=listing_id)
        current_bid = listing.bids.order_by("-amount").first()
        
        # Ensure bid is valid (greater than starting bid and higher than any previous bids)
        if bid_amount <= listing.starting_bid:
            messages.error(request, "Bid must be higher than the starting bid.")
            return redirect("listing", listing_id=listing_id)
        if current_bid and bid_amount <= current_bid.amount:
            messages.error(request, "Bid must be higher than the current highest bid.")
            return redirect("listing", listing_id=listing_id)
        
        # Place bid and redirect back to listing page
        Bid.objects.create(amount=bid_amount, listing=listing, bidder=request.user)
        messages.success(request, "Bid placed successfully!")
        return redirect("listing", listing_id=listing_id)

@login_required
def close_listing(request):
    if request.method == "POST":
        listing_id = request.POST.get("listing_id")
        listing = get_object_or_404(Listing, pk=listing_id)

        if listing.created_by != request.user:
            raise Http404("You are not authorized to perform this action.")

        if not listing.active:
            raise Http404("This listing is already closed.")

        highest_bid = listing.bids.order_by('-amount').first()
        if highest_bid:
            listing.winner = highest_bid.bidder
            listing.current_price = highest_bid.amount
        else:
            listing.current_price = listing.starting_bid

        listing.active = False
        listing.save()
        messages.success(request, "Listing closed successfully!")
        return redirect("index")
    else:
        raise Http404("Invalid request method.")

@login_required
def add_comment(request):
    if request.method == "POST":
        listing_id = request.POST.get("listing_id")
        comment_text = request.POST.get("comment_text")
        listing = Listing.objects.get(pk=listing_id)
        commenter = request.user

        if listing.active:
            Comment.objects.create(listing=listing, commenter=commenter, text=comment_text)
            messages.success(request, "Comment added successfully!")
        else:
            messages.warning(request, "This listing is no longer active.")

        return redirect("listing", listing_id=listing_id)


def categories(request):
    active_listings = Listing.objects.filter(active=True)
    categories = Category.objects.filter
    return render(request, "auctions/categories.html", {"categories": categories, "listings": active_listings})


def category_listings(request, category_id):
    try:
        category = Category.objects.get(pk=category_id)
    except Category.DoesNotExist:
        raise Http404("Category does not exist")
    listings = Listing.objects.filter(category=category, active=True)
    return render(request, 'auctions/category_listings.html', {
        'category': category,
        'listings': listings,
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required
def create_listing(request):
    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST['description']
        starting_bid = request.POST['starting_bid']
        image_url = request.POST['image_url']
        category_id = request.POST['category']
        category = Category.objects.get(id=category_id)
        user = request.user
        listing = Listing(title=title, description=description, starting_bid=starting_bid, image_url=image_url, category=category, created_by=user)
        listing.save()
        return HttpResponseRedirect(reverse("index"))
    else:
        categories = Category.objects.all()
        return render(request, 'auctions/create_listing.html', {'categories': categories})