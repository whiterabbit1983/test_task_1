from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
import json
import os
import re

MODELS_MAP = {}

file_name = getattr(settings, "JSON_FILE_NAME", "models.json")
JSON_FULL_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), file_name))

def clean(s, regex="[^a-zA-Z0-9_]"):
    pattern = re.compile(regex)
    return pattern.sub("", s).strip()

def escape(s):
    # ugly
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "&#39;").replace("\"", "&quot;")

# save method for a model
# escaping goes here
def model_save(self, *args, **kwargs):
    self.full_clean()
    model = self.__class__
    fields = model._meta.fields
    for field in fields:
        val = getattr(self, field.name)
        if isinstance(val, str):
            val = escape(val)
        setattr(self, field.name, val)
    super(model, self).save(*args, **kwargs)

class ModelsLoader:
    # just simple structure
    field_map = {
        "char": [models.CharField, {"max_length": 200}],
        "integer": [
            models.IntegerField, 
            {"validators": 
                [MaxValueValidator(2147483647), 
                MinValueValidator(-2147483648)]}],
        "date": [models.DateField, {}]
    }

    required_model_keys = ["title", "fields"]
    required_attr_keys = ["id", "title", "type"]

    def __init__(self, json_str):
        self._content = self._get_content(json_str)

    def _get_content(self, json_str):
        try:
            return json.loads(json_str)
        except ValueError:
            return {}

    def _clean_keys(self, d):
        old_keys = d.keys()
        return dict([(clean(k), d[k]) for k in old_keys])

    def _check_keys(self, dct, req_keys):
        return set(req_keys).issubset(set(dct))

    def unload(self, model_name_str):
        if model_name_str in globals():
            del globals()[model_name_str]

    def load(self):
        # TODO: add logging (to all methods)
        for model_name, model_attrs in self._content.items():
            model_name = clean(model_name).capitalize()
            model_attrs = self._clean_keys(model_attrs)
            attr_dict = dict()
            if not self._check_keys(model_attrs, self.required_model_keys):
                # if model does not have any of required keys
                # consider it as invalid and skip
                continue
            first_fld_name = None
            for field in model_attrs["fields"]:
                if (not self._check_keys(field, self.required_attr_keys) or 
                    not clean(field["type"]) in self.field_map):
                    # the same skipping logic as for models
                    continue
                fld_type = clean(field["type"])
                fld_name = clean(field["id"])
                if not first_fld_name:
                    first_fld_name = fld_name
                    # define __str__ function
                    attr_dict["cap_field"] = fld_name
                    attr_dict["__str__"] = lambda s: getattr(s, s.cap_field)
                
                fld_class = self.field_map[fld_type][0]
                fld_args = self.field_map[fld_type][1]
                attr_dict[fld_name] = fld_class(field["title"], **fld_args)

            attr_dict.update({
                "Meta": type(
                    "Meta", (), {
                    "verbose_name_plural": model_attrs["title"], 
                    "ordering": ("id",)}),
                "save": model_save,
                "__module__": __name__
                })

            globals().update({
                model_name: type(model_name, (models.Model,), attr_dict)})
            MODELS_MAP[model_name.lower()] = globals()[model_name]

if os.path.exists(JSON_FULL_PATH):
    ModelsLoader(
        open(JSON_FULL_PATH).read()).load()
