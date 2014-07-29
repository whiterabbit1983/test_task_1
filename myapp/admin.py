import os
from django.contrib import admin
from .models import MODELS_MAP

for _, model in MODELS_MAP.items():
    admin.site.register(model)
