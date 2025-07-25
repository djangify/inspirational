from django.shortcuts import render


def tools_home(request):
    return render(request, "tools/index.html")


def calming_game(request):
    return render(request, "tools/calming_game.html")


def tap_to_calm(request):
    return render(request, "tools/tap_to_calm.html")
