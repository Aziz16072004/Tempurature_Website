from django.shortcuts import render
from django.http import HttpResponse
# from .forms import PostForm

# Create your views here.

def homePage(request):
    return HttpResponse("<h1>Hello, this is the home page:</h1>")
# def post_new(request):
#     form = PostForm()
#     return render(request, 'blog/post_edit.html', {'form': form})