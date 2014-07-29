from django.views.generic import ListView, TemplateView
from django.views.generic.edit import CreateView, UpdateView
from .mixins import ActionMixin, QuerysetMixin, ValidationMixin
from .models import MODELS_MAP

class EntityView(QuerysetMixin, ActionMixin, ListView):
    pass

class NewEntityView(QuerysetMixin, ValidationMixin, ActionMixin, CreateView):
    pass

class UpdateEntityView(QuerysetMixin, ValidationMixin, ActionMixin, UpdateView):
    pass

class MainView(TemplateView):
    template_name = "myapp/main.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        m = {k: v._meta.verbose_name_plural for k, v in MODELS_MAP.items()}
        ctx["models_map"] = m
        return ctx
