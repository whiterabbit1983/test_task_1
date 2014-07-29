from django.http import HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import requires_csrf_token
from django.utils.decorators import method_decorator
import json
from .models import MODELS_MAP

class ActionMixin:
    def serialize(self, model, queryset, **kwargs):
        fields_map = [[
        field.name, 
        model._meta.get_field(field.name).verbose_name, 
        field.__class__.__name__[:-5]] 
        for field in model._meta.fields]

        res = {"fields": fields_map, "data": []}

        for obj in queryset:
            obj_data = {}
            for fld in model._meta.fields:
                obj_data.update({fld.name: str(getattr(obj, fld.name, ""))})
            res["data"].append(obj_data)
        res.update(kwargs)
        return json.dumps(res)

    def render_to_json(self, context, **kwargs):
        data = json.dumps(context)
        kwargs["content_type"] = "application/json"
        return HttpResponse(data, **kwargs)

    def render_to_response(self, context):
        queryset = self.get_queryset()
        post_url = reverse("myapp:new_entity", kwargs={"entity": self.kwargs["entity"]})
        self.kwargs["pk"] = 0
        update_url = reverse("myapp:update_entity", kwargs=self.kwargs)
        data = self.serialize(
            self.model, queryset, 
            post_url=post_url,
            update_url=update_url)
        response = HttpResponse(data, content_type="application/json")
        response["Access-Control-Allow-Origin"] = "*"
        return response

    def get_success_url(self):
        return reverse("myapp:show_entity", kwargs={"entity": self.kwargs["entity"]})

    @method_decorator(requires_csrf_token)
    def dispatch(self, *args, **kwargs):
        return super(ActionMixin, self).dispatch(*args, **kwargs)

class QuerysetMixin:
    def get_queryset(self):
        try:
            self.model = model = MODELS_MAP[self.kwargs["entity"]]
            return model.objects.all()
        except KeyError:
            raise Http404

class ValidationMixin:
    def form_valid(self, form):
        super(ValidationMixin, self).form_valid(form)
        return self.render_to_response({})

    def form_invalid(self, form):
        super(ValidationMixin, self).form_invalid(form)
        return self.render_to_json(form.errors, status=400)
