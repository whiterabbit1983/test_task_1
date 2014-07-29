from django.test import TestCase
from django.test.client import Client
from django.db import models
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.core.management import call_command
from django.template.loader import render_to_string
import json
import datetime
from .models import ModelsLoader, clean
from .views import EntityView, NewEntityView, UpdateEntityView, MainView


class ModelsLoaderTest(TestCase):
    def setUp(self):
        self.models_json = """
        {
        "anymodel": {
            "title": "Rooms title",
            "fields": [
            {"id": "department", "title": "Dept title", "type": "char"},
            {"id": "spots", "title": "Spots title", "type": "integer"},
            {"id": "any_date", "title": "Any date title", "type": "date"}
            ]}
        }
        """
        # ideally I should generate all possible 
        # symbols that do not match the pattern
        # but for now I use only some of them
        self.dirty_json = """
        {
        "anymo del": {
            "ti tle": "Rooms title",
            "fi elds": [
            {"id": "departm ent", "title": "Dept title", "type": "char"},
            {"id": "spo ts", "title": "Spots title", "type": "inte ger"},
            {"id": "any_da te", "title": "Any date title", "type": "date"}
            ]}
        }
        """
        self.json_with_skips = """
        {
            "anymodel": {
                "title": "Rooms title",
                "fields": [
                {"id": "department", "title": "Dept title", "type": "char"},
                {"id": "spots", "title": "Spots title", "type": "integer"},
                {"id": "int_fld_1", "title": "Int fld title"},
                {"id": "int_fld_1", "type": "integer"},
                {"title": "Int fld 3 title", "type": "integer"},
                {"id": "none_fld", "title": "None fld title", "type": "none"},
                {"id": "any_date", "title": "Any date title", "type": "date"}
                ]},
            "windows": {
                "fields": [
                {"id": "department", "title": "Dept title", "type": "char"},
                {"id": "spots", "title": "Spots title", "type": "integer"},
                {"id": "any_date", "title": "Any date title", "type": "date"}
                ]}
        }
        """
        self.invalid_json = """
        {
        ""anymodel": {
            "title": "Rooms",
            "fields": [
            {"id": "department", "title": "Dept", "type": "char"}
            ]}
        }
        """
        self.models_dict = json.loads(self.models_json)

    def test_clean(self):
        s = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_"
        self.assertEqual(s, clean(s))

    def test_get_content_valid(self):
        l = ModelsLoader(self.models_json)
        self.assertEqual(l._get_content(self.models_json), self.models_dict)

    def test_get_content_invalid(self):
        l = ModelsLoader(self.invalid_json)
        self.assertEqual(l._get_content(self.invalid_json), {})

    def test_check_keys_ok_1(self):
        l = ModelsLoader(self.models_json)
        self.assertTrue(l._check_keys({"key1": 1, "key2": 2}, ["key1", "key2"]))

    def test_check_keys_ok_2(self):
        l = ModelsLoader(self.models_json)
        self.assertTrue(l._check_keys({"key1": 1, "key2": 2, "key3": 3}, ["key1", "key2"]))

    def test_check_keys_false(self):
        l = ModelsLoader(self.models_json)
        self.assertFalse(l._check_keys({"key1": 1}, ["key1", "key2"]))

    def test_unload_model(self):
        l = ModelsLoader(self.models_json)
        l.load()
        created = False
        try:
            from .models import Anymodel
            created = True
        except ImportError:
            pass
        self.assertTrue(created)
        l.unload("Anymodel")
        created = False
        try:
            from .models import Anymodel
            created = True
        except ImportError:
            pass
        self.assertFalse(created)

    def test_load_in_globals_class_created(self):
        l = ModelsLoader(self.models_json)
        created = False
        try:
            from .models import Anymodel
            created = True
        except ImportError:
            pass
        self.assertFalse(created)
        l.load()
        created = False
        try:
            from .models import Anymodel
            created = True
        except ImportError:
            pass
        self.assertTrue(created)
        l.unload("Anymodel")

    def test_load_in_globals_class_is_model(self):
        l = ModelsLoader(self.models_json)
        l.load()
        from .models import Anymodel
        self.assertIsInstance(Anymodel, models.base.ModelBase)
        l.unload("Anymodel")

    def test_load_in_globals_has_str(self):
        l = ModelsLoader(self.models_json)
        l.load()
        from .models import Anymodel
        self.assertTrue(hasattr(Anymodel, "__str__"))
        l.unload("Anymodel")

    def test_load_in_globals_has_meta(self):
        l = ModelsLoader(self.models_json)
        l.load()
        from .models import Anymodel
        self.assertTrue(hasattr(Anymodel, "_meta"))
        l.unload("Anymodel")

    def test_load_in_globals_meta_is_class(self):
        l = ModelsLoader(self.models_json)
        l.load()
        from .models import Anymodel
        self.assertIsInstance(Anymodel._meta, models.options.Options)
        l.unload("Anymodel")

    def test_load_in_globals_meta_title(self):
        l = ModelsLoader(self.models_json)
        l.load()
        from .models import Anymodel
        self.assertTrue(hasattr(Anymodel._meta, "verbose_name_plural"))
        self.assertEqual(Anymodel._meta.verbose_name_plural, "Rooms title")
        l.unload("Anymodel")

    def test_load_in_globals_fields_count(self):
        l = ModelsLoader(self.models_json)
        l.load()
        from .models import Anymodel
        self.assertEqual(len(Anymodel._meta.fields), 4)
        l.unload("Anymodel")

    def test_load_in_globals_fields_names(self):
        l = ModelsLoader(self.models_json)
        l.load()
        from .models import Anymodel
        fn = [f.name for f in Anymodel._meta.fields]
        self.assertIn("id", fn)
        self.assertIn("department", fn)
        self.assertIn("spots", fn)
        self.assertIn("any_date", fn)
        l.unload("Anymodel")

    def test_load_in_globals_field_types(self):
        l = ModelsLoader(self.models_json)
        l.load()
        from .models import Anymodel
        self.assertIsInstance(Anymodel._meta.fields[0], models.AutoField)
        self.assertIsInstance(Anymodel._meta.fields[1], models.CharField)
        self.assertIsInstance(Anymodel._meta.fields[2], models.IntegerField)
        self.assertIsInstance(Anymodel._meta.fields[3], models.DateField)
        l.unload("Anymodel")

    def test_load_dirty_in_globals_class_created(self):
        l = ModelsLoader(self.dirty_json)
        l.unload('Anymodel')
        created = False
        try:
            from .models import Anymodel
            created = True
        except ImportError:
            pass
        self.assertFalse(created)
        l.load()
        created = False
        try:
            from .models import Anymodel
            created = True
        except ImportError:
            pass
        self.assertTrue(created)
        l.unload("Anymodel")

    def test_load_dirty_in_globals_class_is_model(self):
        l = ModelsLoader(self.dirty_json)
        l.load()
        from .models import Anymodel
        self.assertIsInstance(Anymodel, models.base.ModelBase)
        l.unload("Anymodel")

    def test_load_dirty_in_globals_has_str(self):
        l = ModelsLoader(self.dirty_json)
        l.load()
        from .models import Anymodel
        self.assertTrue(hasattr(Anymodel, "__str__"))
        l.unload("Anymodel")

    def test_load_dirty_in_globals_has_meta(self):
        l = ModelsLoader(self.dirty_json)
        l.load()
        from .models import Anymodel
        self.assertTrue(hasattr(Anymodel, "_meta"))
        l.unload("Anymodel")

    def test_load_dirty_in_globals_meta_is_class(self):
        l = ModelsLoader(self.dirty_json)
        l.load()
        from .models import Anymodel
        self.assertIsInstance(Anymodel._meta, models.options.Options)
        l.unload("Anymodel")

    def test_load_dirty_in_globals_meta_title(self):
        l = ModelsLoader(self.dirty_json)
        l.load()
        from .models import Anymodel
        self.assertTrue(hasattr(Anymodel._meta, "verbose_name_plural"))
        self.assertEqual(Anymodel._meta.verbose_name_plural, "Rooms title")
        l.unload("Anymodel")

    def test_load_dirty_in_globals_fields_count(self):
        l = ModelsLoader(self.dirty_json)
        l.load()
        from .models import Anymodel
        self.assertEqual(len(Anymodel._meta.fields), 4)
        l.unload("Anymodel")

    def test_load_dirty_in_globals_fields_names(self):
        l = ModelsLoader(self.dirty_json)
        l.load()
        from .models import Anymodel
        fn = [f.name for f in Anymodel._meta.fields]
        self.assertIn("id", fn)
        self.assertIn("department", fn)
        self.assertIn("spots", fn)
        self.assertIn("any_date", fn)
        l.unload("Anymodel")

    def test_load_dirty_in_globals_field_types(self):
        l = ModelsLoader(self.dirty_json)
        l.load()
        from .models import Anymodel
        self.assertIsInstance(Anymodel._meta.fields[0], models.AutoField)
        self.assertIsInstance(Anymodel._meta.fields[1], models.CharField)
        self.assertIsInstance(Anymodel._meta.fields[2], models.IntegerField)
        self.assertIsInstance(Anymodel._meta.fields[3], models.DateField)
        l.unload("Anymodel")

    def test_load_with_skips_in_globals_models(self):
        l = ModelsLoader(self.json_with_skips)
        l.load()
        created = False
        try:
            from .models import Anymodel
            created = True
        except ImportError:
            pass
        self.assertTrue(created)
        created = False
        try:
            from .models import Windows
            created = True
        except ImportError:
            pass
        self.assertFalse(created)
        l.unload("Anymodel")

    def test_load_with_skips_in_globals_fields_count(self):
        l = ModelsLoader(self.json_with_skips)
        l.load()
        from .models import Anymodel
        self.assertEqual(len(Anymodel._meta.fields), 4)
        l.unload("Anymodel")

    def test_load_with_skips_in_globals_fields_names(self):
        l = ModelsLoader(self.json_with_skips)
        l.load()
        from .models import Anymodel
        fn = [f.name for f in Anymodel._meta.fields]
        self.assertIn("id", fn)
        self.assertIn("department", fn)
        self.assertIn("spots", fn)
        self.assertIn("any_date", fn)
        l.unload("Anymodel")

    def test_load_with_skips_in_globals_fields_types(self):
        l = ModelsLoader(self.json_with_skips)
        l.load()
        from .models import Anymodel
        self.assertIsInstance(Anymodel._meta.fields[0], models.AutoField)
        self.assertIsInstance(Anymodel._meta.fields[1], models.CharField)
        self.assertIsInstance(Anymodel._meta.fields[2], models.IntegerField)
        self.assertIsInstance(Anymodel._meta.fields[3], models.DateField)
        l.unload("Anymodel")

class ModelTest(TestCase):
    def setUp(self):
        self.models_json = """
        {
        "anymodel": {
            "title": "Rooms title",
            "fields": [
            {"id": "department", "title": "Dept title", "type": "char"},
            {"id": "spots", "title": "Spots title", "type": "integer"},
            {"id": "any_date", "title": "Any date title", "type": "date"}
            ]}
        }
        """
        ModelsLoader(self.models_json).load()
        call_command("syncdb")

    def test_model_create_object(self):
        from .models import Anymodel
        Anymodel.objects.create(department="d", spots=1, any_date="2011-11-11")
        obj = Anymodel.objects.get(pk=1)
        self.assertEqual(obj.department, "d")
        self.assertEqual(obj.spots, 1)
        self.assertEqual(obj.any_date, datetime.date(2011,11,11))

    def test_model_ordering(self):
        from .models import Anymodel
        Anymodel.objects.create(id=2, department="d2", spots=2, any_date="2012-11-11")
        Anymodel.objects.create(id=1, department="d1", spots=1, any_date="2011-11-11")
        obj1, obj2 = Anymodel.objects.all()
        self.assertEqual(obj1.id, 1)
        self.assertEqual(obj2.id, 2)

    def test_model_to_str(self):
        from .models import Anymodel
        Anymodel.objects.create(department="d2", spots=2, any_date="2012-11-11")
        self.assertEqual(Anymodel._meta.fields[1].name, "department")
        obj = Anymodel.objects.get(pk=1)
        self.assertEqual(str(obj), "d2")

    def test_model_save_escape(self):
        from .models import Anymodel
        Anymodel.objects.create(department="<>&'\"", spots=2, any_date="2012-11-11")
        obj = Anymodel.objects.get(pk=1)
        self.assertEqual(obj.department, "&lt;&gt;&amp;&#39;&quot;")

    def test_model_num_overflow(self):
        from .models import Anymodel
        valid = False
        try:
            Anymodel.objects.create(department="d", spots=2147483647, any_date="2012-11-11")
            valid = True
        except ValidationError:
            pass
        self.assertTrue(valid)

        try:
            Anymodel.objects.create(department="d", spots=-2147483648, any_date="2012-11-11")
            valid = True
        except ValidationError:
            pass
        self.assertTrue(valid)

        valid = False
        try:
            Anymodel.objects.create(department="d", spots=(2147483647 + 1), any_date="2012-11-11")
            valid = True
        except ValidationError:
            pass
        self.assertFalse(valid)

        valid = False
        try:
            Anymodel.objects.create(department="d", spots=(-2147483648 - 1), any_date="2012-11-11")
            valid = True
        except ValidationError:
            pass
        self.assertFalse(valid)

class ViewsTest(TestCase):
    def setUp(self):
        self.models_json = """
        {
        "anymodel": {
            "title": "Rooms title",
            "fields": [
            {"id": "department", "title": "Dept title", "type": "char"},
            {"id": "spots", "title": "Spots title", "type": "integer"},
            {"id": "any_date", "title": "Any date title", "type": "date"}
            ]}
        }
        """
        ModelsLoader(self.models_json).load()
        call_command("syncdb")

    def test_list_view_status(self):
        resp = self.client.get("/myapp/anymodel")
        self.assertEqual(resp.status_code, 200)

    def test_list_view_is_valid_json(self):
        resp = self.client.get("/myapp/anymodel")
        valid = False
        try:
            json.loads(resp.content.decode("utf-8"))
            valid = True
        except Exception as e:
            pass
        self.assertTrue(valid)

    def test_list_view_objects_len(self):
        from .models import Anymodel
        Anymodel.objects.create(
            department="d",
            spots=1,
            any_date="2011-11-11")
        
        resp = self.client.get("/myapp/anymodel")
        d = json.loads(resp.content.decode("utf-8"))
        self.assertEqual(len(d["data"]), 1)

    def test_list_view_objects_fields_len(self):
        from .models import Anymodel
        Anymodel.objects.create(
            department="d",
            spots=1,
            any_date="2011-11-11")
        
        resp = self.client.get("/myapp/anymodel")
        d = json.loads(resp.content.decode("utf-8"))
        self.assertEqual(len(d["fields"]), 4)

    def test_list_view_objects_fields_is_list(self):
        from .models import Anymodel
        Anymodel.objects.create(
            department="d",
            spots=1,
            any_date="2011-11-11")
        
        resp = self.client.get("/myapp/anymodel")
        d = json.loads(resp.content.decode("utf-8"))
        self.assertIsInstance(d["fields"][0], list)
        self.assertIsInstance(d["fields"][1], list)
        self.assertIsInstance(d["fields"][2], list)
        self.assertIsInstance(d["fields"][3], list)

    def test_list_view_objects_fields_names(self):
        from .models import Anymodel
        Anymodel.objects.create(
            department="d",
            spots=1,
            any_date="2011-11-11")
        
        resp = self.client.get("/myapp/anymodel")
        d = json.loads(resp.content.decode("utf-8"))
        self.assertEqual(d["fields"][0][0], Anymodel._meta.fields[0].name)
        self.assertEqual(d["fields"][1][0], Anymodel._meta.fields[1].name)
        self.assertEqual(d["fields"][2][0], Anymodel._meta.fields[2].name)
        self.assertEqual(d["fields"][3][0], Anymodel._meta.fields[3].name)

    def test_list_view_objects_fields_verbose_names(self):
        from .models import Anymodel
        Anymodel.objects.create(
            department="d",
            spots=1,
            any_date="2011-11-11")
        
        resp = self.client.get("/myapp/anymodel")
        d = json.loads(resp.content.decode("utf-8"))
        self.assertEqual(d["fields"][0][1], Anymodel._meta.fields[0].verbose_name)
        self.assertEqual(d["fields"][1][1], Anymodel._meta.fields[1].verbose_name)
        self.assertEqual(d["fields"][2][1], Anymodel._meta.fields[2].verbose_name)
        self.assertEqual(d["fields"][3][1], Anymodel._meta.fields[3].verbose_name)

    def test_list_view_objects_fields_types(self):
        from .models import Anymodel
        Anymodel.objects.create(
            department="d",
            spots=1,
            any_date="2011-11-11")
        
        resp = self.client.get("/myapp/anymodel")
        d = json.loads(resp.content.decode("utf-8"))
        self.assertEqual(d["fields"][0][2], models.AutoField.__name__[:-5])
        self.assertEqual(d["fields"][1][2], models.CharField.__name__[:-5])
        self.assertEqual(d["fields"][2][2], models.IntegerField.__name__[:-5])
        self.assertEqual(d["fields"][3][2], models.DateField.__name__[:-5])

    def test_list_view_objects_attrs(self):
        from .models import Anymodel
        Anymodel.objects.create(
            department="d",
            spots=2,
            any_date="2011-11-11")
        
        resp = self.client.get("/myapp/anymodel")
        d = json.loads(resp.content.decode("utf-8"))
        jo = d["data"][0]
        self.assertEqual(jo["id"], "1")
        self.assertEqual(jo["department"], "d")
        self.assertEqual(jo["spots"], "2")
        self.assertEqual(jo["any_date"], "2011-11-11")

    def test_list_view_post_url(self):
        from .models import Anymodel
        Anymodel.objects.create(
            department="d",
            spots=2,
            any_date="2011-11-11")
        
        resp = self.client.get("/myapp/anymodel")
        d = json.loads(resp.content.decode("utf-8"))
        self.assertEqual(d["post_url"], "/myapp/anymodel/add")

    def test_list_view_update_url(self):
        from .models import Anymodel
        Anymodel.objects.create(
            department="d",
            spots=2,
            any_date="2011-11-11")
        
        resp = self.client.get("/myapp/anymodel")
        d = json.loads(resp.content.decode("utf-8"))
        self.assertEqual(d["update_url"], "/myapp/anymodel/update/0")

    def test_add_view_status_ok(self):
        resp = self.client.post(
            "/myapp/anymodel/add", 
            {"department": "dept",
            "spots": "2",
            "any_date": "2010-10-10"})
        self.assertEqual(resp.status_code, 200)

    def test_add_view_got_objects(self):
        resp = self.client.post(
            "/myapp/anymodel/add", 
            {"department": "dept",
            "spots": "2",
            "any_date": "2010-10-10"})
        valid = False
        try:
            d = json.loads(resp.content.decode("utf-8"))
            valid = True
        except Exception:
            pass
        self.assertTrue(valid)
        self.assertIn("post_url", d)
        self.assertIn("update_url", d)
        self.assertIn("data", d)
        self.assertIn("fields", d)
        self.assertEqual(len(d["data"]), 1)
        self.assertEqual(d["data"][0], {"id": "1", "department": "dept", "spots": "2", "any_date": "2010-10-10"})

    def test_update_view_status_ok(self):
        # add one record
        self.client.post(
            "/myapp/anymodel/add", 
            {"department": "dept",
            "spots": "2",
            "any_date": "2010-10-10"})

        resp = self.client.post(
            "/myapp/anymodel/update/1", 
            {"department": "dept1",
            "spots": "23",
            "any_date": "2012-10-10"})
        self.assertEqual(resp.status_code, 200)

    def test_update_view_object_updated(self):
        # add one record
        self.client.post(
            "/myapp/anymodel/add", 
            {"department": "dept",
            "spots": "2",
            "any_date": "2010-10-10"})

        resp = self.client.post(
            "/myapp/anymodel/update/1", 
            {"department": "dept1",
            "spots": "23",
            "any_date": "2012-10-10"})

        valid = False
        try:
            d = json.loads(resp.content.decode("utf-8"))
            valid = True
        except Exception:
            pass
        self.assertTrue(valid)
        self.assertIn("post_url", d)
        self.assertIn("update_url", d)
        self.assertIn("data", d)
        self.assertIn("fields", d)
        self.assertEqual(len(d["data"]), 1)
        self.assertEqual(d["data"][0], {"id": "1", "department": "dept1", "spots": "23", "any_date": "2012-10-10"})

    def test_update_view_not_found(self):
        # add one record
        self.client.post(
            "/myapp/anymodel/add", 
            {"department": "dept",
            "spots": "2",
            "any_date": "2010-10-10"})

        resp = self.client.post(
            "/myapp/anymodel/update/111", 
            {"department": "dept1",
            "spots": "23",
            "any_date": "2012-10-10"})
        self.assertEqual(resp.status_code, 404)

    def test_update_view_fields_required(self):
        self.client.post(
            "/myapp/anymodel/add", 
            {"department": "dept",
            "spots": "2",
            "any_date": "2010-10-10"})

        resp = self.client.post(
            "/myapp/anymodel/update/1",
            {"department": "",
            "spots": "",
            "any_date": ""})
        valid = False
        try:
            d = json.loads(resp.content.decode("utf-8"))
            valid = True
        except Exception:
            pass
        self.assertTrue(valid)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("department", d)
        self.assertIn("spots", d)
        self.assertIn("any_date", d)

    def test_update_view_error_int_json(self):
        self.client.post(
            "/myapp/anymodel/add", 
            {"department": "dept",
            "spots": "2",
            "any_date": "2010-10-10"})

        resp = self.client.post(
            "/myapp/anymodel/update/1",
            {"department": "dept",
            "spots": "3c",
            "any_date": "2010-10-10"})
        valid = False
        try:
            d = json.loads(resp.content.decode("utf-8"))
            valid = True
        except Exception:
            pass
        self.assertTrue(valid)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("spots", d)
        self.assertNotIn("department", d)
        self.assertNotIn("any_date", d)

    def test_update_view_error_date_json(self):
        self.client.post(
            "/myapp/anymodel/add", 
            {"department": "dept",
            "spots": "2",
            "any_date": "2010-10-10"})

        resp = self.client.post(
            "/myapp/anymodel/update/1",
            {"department": "dept",
            "spots": "3",
            "any_date": "2010-10-10z"})
        valid = False
        try:
            d = json.loads(resp.content.decode("utf-8"))
            valid = True
        except Exception:
            pass
        self.assertTrue(valid)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("any_date", d)
        self.assertNotIn("department", d)
        self.assertNotIn("spots", d)

    def test_list_view_show_escaped(self):
        from .models import Anymodel
        Anymodel.objects.create(department="<>'\"&", spots=2, any_date="2010-10-10")

        resp = self.client.get("/myapp/anymodel")
        d = json.loads(resp.content.decode("utf-8"))
        j_obj = d["data"][0]
        self.assertEqual(j_obj["id"], "1")
        self.assertEqual(j_obj["department"], "&lt;&gt;&#39;&quot;&amp;")
        self.assertEqual(j_obj["spots"], "2")
        self.assertEqual(j_obj["any_date"], "2010-10-10")

    def test_add_view_add_escaped(self):
        from .models import Anymodel
        self.client.post(
            "/myapp/anymodel/add",
            {"department": "<>'\"&",
            "spots": "3",
            "any_date": "2010-10-10"})
        
        obj = Anymodel.objects.get(pk=1)

        self.assertEqual(obj.id, 1)
        self.assertEqual(obj.department, "&lt;&gt;&#39;&quot;&amp;")
        self.assertEqual(obj.spots, 3)
        self.assertEqual(obj.any_date, datetime.date(2010, 10, 10))

    def test_update_view_update_escaped(self):
        from .models import Anymodel
        self.client.post(
            "/myapp/anymodel/add",
            {"department": "dept",
            "spots": "3",
            "any_date": "2010-10-10"})

        self.client.post(
            "/myapp/anymodel/update/1",
            {"department": "<>'\"&",
            "spots": "4",
            "any_date": "2011-10-10"})
        
        obj = Anymodel.objects.get(pk=1)

        self.assertEqual(obj.id, 1)
        self.assertEqual(obj.department, "&lt;&gt;&#39;&quot;&amp;")
        self.assertEqual(obj.spots, 4)
        self.assertEqual(obj.any_date, datetime.date(2011, 10, 10))

    def test_add_view_error_int_json(self):
        resp = self.client.post(
            "/myapp/anymodel/add",
            {"department": "dept",
            "spots": "a",
            "any_date": "2010-10-10"})
        valid = False
        try:
            d = json.loads(resp.content.decode("utf-8"))
            valid = True
        except Exception:
            pass
        self.assertEqual(resp.status_code, 400)
        self.assertTrue(valid)
        self.assertIn("spots", d)
        self.assertNotIn("department", d)
        self.assertNotIn("any_date", d)

    def test_add_view_error_date_json(self):
        resp = self.client.post(
            "/myapp/anymodel/add",
            {"department": "dept",
            "spots": "3",
            "any_date": "2010-10-10z"})
        valid = False
        try:
            d = json.loads(resp.content.decode("utf-8"))
            valid = True
        except Exception:
            pass
        self.assertEqual(resp.status_code, 400)
        self.assertTrue(valid)
        self.assertIn("any_date", d)
        self.assertNotIn("department", d)
        self.assertNotIn("spots", d)

    def test_add_view_fields_required(self):
        resp = self.client.post(
            "/myapp/anymodel/add",
            {"department": "",
            "spots": "",
            "any_date": ""})
        valid = False
        try:
            d = json.loads(resp.content.decode("utf-8"))
            valid = True
        except Exception:
            pass
        self.assertTrue(valid)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("department", d)
        self.assertIn("spots", d)
        self.assertIn("any_date", d)

    def test_main_view_links_is_correct(self):
        resp = self.client.get("/myapp/")
        self.assertContains(resp, "var links = {")
        self.assertContains(resp, "\"anymodel\": [\"Rooms title\",")
        self.assertContains(resp, "/myapp/anymodel\"],")

    def test_main_view_escaped_from_models_json(self):
        html1 = render_to_string(
            "myapp/main.html", 
            {"models_map": {"anymodel<>'&\"": "Anymodel title<>'&\""}})
        self.assertIn("anymodel&lt;&gt;&#39;&amp;&quot", html1)
        self.assertIn("Anymodel title&lt;&gt;&#39;&amp;&quot", html1)
