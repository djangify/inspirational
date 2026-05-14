# bots/views.py
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
from shop.models import OrderItem, Product
from .models import BotProduct, BotAccess

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


def user_has_purchased(user, product):
    """Check if a user has a completed order containing this product."""
    if user.is_superuser:
        return True
    return OrderItem.objects.filter(
        order__user=user,
        product=product,
        order__status='completed'
    ).exists()


def get_or_create_bot_access(user, bot_product):
    """Get existing access record or create a new one."""
    access, created = BotAccess.objects.get_or_create(
        user=user,
        bot_product=bot_product,
        defaults={
            'access_expires': timezone.now() + timezone.timedelta(
                days=bot_product.access_days
            )
        }
    )
    return access, created


@login_required
def bot_chat(request, product_slug):
    """
    Main chat view. Checks purchase, checks access, renders the chat interface.
    """
    product = get_object_or_404(Product, slug=product_slug, is_active=True)

    # Check product has a bot
    try:
        bot_product = product.bot
    except BotProduct.DoesNotExist:
        return render(request, 'bots/no_bot.html', {'product': product})

    if not bot_product.is_active:
        return render(request, 'bots/no_bot.html', {'product': product})

    # Check user has purchased this product
    if not user_has_purchased(request.user, product):
        return render(request, 'bots/access_denied.html', {
            'product': product,
            'reason': 'purchase'
        })

    # Get or create access record
    access, _ = get_or_create_bot_access(request.user, bot_product)

    # Check access is still valid
    if access.is_expired:
        return render(request, 'bots/access_denied.html', {
            'product': product,
            'access': access,
            'reason': 'expired'
        })

    if access.messages_remaining <= 0:
        return render(request, 'bots/access_denied.html', {
            'product': product,
            'access': access,
            'reason': 'limit'
        })

    return render(request, 'bots/chat.html', {
        'product': product,
        'bot_product': bot_product,
        'access': access,
        'welcome_message': bot_product.welcome_message,
    })


@login_required
@require_POST
def bot_message(request, product_slug):
    """
    API endpoint. Receives message history, returns AI response.
    Increments message counter on each call.
    """
    product = get_object_or_404(Product, slug=product_slug, is_active=True)

    try:
        bot_product = product.bot
    except BotProduct.DoesNotExist:
        return JsonResponse({'error': 'No bot found for this product.'}, status=404)

    # Verify purchase
    if not user_has_purchased(request.user, product):
        return JsonResponse({'error': 'Access denied.'}, status=403)

    # Get access record
    try:
        access = BotAccess.objects.get(user=request.user, bot_product=bot_product)
    except BotAccess.DoesNotExist:
        return JsonResponse({'error': 'No access record found.'}, status=403)

    # Check limits
    if access.is_expired:
        return JsonResponse({
            'error': 'Your access has expired.',
            'expired': True
        }, status=403)

    if access.messages_remaining <= 0:
        return JsonResponse({
            'error': 'You have reached your message limit.',
            'limit_reached': True
        }, status=403)

    # Parse request body
    try:
        data = json.loads(request.body)
        messages = data.get('messages', [])
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request.'}, status=400)

    if not messages:
        return JsonResponse({'error': 'No messages provided.'}, status=400)

    # Call Anthropic API
    if not ANTHROPIC_AVAILABLE:
        return JsonResponse({'error': 'AI service not available.'}, status=500)

    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1000,
            system=bot_product.system_prompt,
            messages=messages
        )

        reply = response.content[0].text

        # Increment message count
        access.message_count += 1
        access.save()

        return JsonResponse({
            'reply': reply,
            'messages_remaining': access.messages_remaining,
            'days_remaining': access.days_remaining,
        })

    except anthropic.AuthenticationError:
        return JsonResponse({'error': 'API authentication failed.'}, status=500)
    except anthropic.RateLimitError:
        return JsonResponse({'error': 'Rate limit reached. Please try again in a moment.'}, status=429)
    except Exception as e:
      import traceback
      traceback.print_exc()
      return JsonResponse({'error': str(e)}, status=500)