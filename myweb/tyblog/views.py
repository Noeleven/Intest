from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def tyreport(request):
	return render(request, 'TYreport.html')
def tt(request):
	return render(request, 'test.html')
