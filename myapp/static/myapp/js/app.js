(function($){
    App = function (options){
        var defaultOptions = {
            "links-var": {},
            "links-div": "list",
            "links-class": "menu",
            "table-div": "info",
            "errors-div": "errors",
            "form-div": "form",
            "csrf-input": "csrfmiddlewaretoken",
            "csrf-cookie": "csrftoken",
            "form-name": "addform",
            "td-class": "editable",
        };

        function csrfSafeMethod(method) {
            return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
        }

        function getCfrsCookie(options){
            var cookiename = options["csrf-cookie"];
            var csrfinput = options["csrf-input"];

            if($.cookie(cookiename) == undefined){
                $.cookie(
                    cookiename, 
                    $("input[name="+ csrfinput +"]").val());
            }

            return $.cookie(cookiename);
        }
        
        function showErrors(err_dict, options){
            var err_div = options["errors-div"];

            for(var err_field in err_dict){
                var err_desc = err_dict[err_field];
                $("#" + err_div).append(
                    "<div><b><font color=red>"+ 
                    err_field +": "+ err_desc +
                    "</font></b></div>");
            }
        }

        function renderTable(options, data){
            function drawHeader(fields){
                return "<tr>" + fields.reduce(function(acc, field){
                    return acc + "<th>"+ field[1] +"</th>";
                }, "") + "</tr>";
            };

            function drawBody(fields, objs){
                return objs.reduce(function(acc, obj){
                    return acc + "<tr>"+ fields.reduce(function(acc, field){
                        return acc +"<td field_type='"+ 
                        field[2] +"' field_id='"+ field[0] + 
                        "' class='"+ options["td-class"] +"'>"+ 
                        obj[field[0]] +"</td>";
                    }, "") +"</tr>";
                }, "");
            }

            return "<table border=1 id='grid'>"+ 
            drawHeader(data["fields"]) + 
            drawBody(data["fields"], data["data"]) +"</table>";
        }

        function renderForm(options, data){
            function drawInputs(fields){
                return fields.reduce(function(acc, field){
                    if(field[2] !== "Auto"){
                        return acc + "<tr><td>"+
                        "<label for='"+ field[0] +"'>"+ field[1] +"</label>"+
                        "<input type='text' class='form-control "+ field[2] +"' id='"+ field[0] +"'>"+
                        "</td></tr>";
                    }else{
                        return acc;
                    }
                }, "");
            }

            return "<form action='' id='"+ options["form-name"] +"' method='POST'><fieldset>"+
            "<table>"+ drawInputs(data["fields"]) +"</table>"+
            "<tr><td><input type='submit' value='Add'></td></tr>"+
            "</fieldset></form>";
        }

        function renderLinks(options){
            return Object.keys(options["links-var"]).reduce(function(acc, key){
                return acc + "<a class='"+ options["links-class"] +
                "' href='' id='"+ key +"'>"+ options["links-var"][key][0] +"</a><br>";
            }, "");
        }
        
        function postRequest(options, url, inputs){
            var post_data = {};
            
            inputs.each(function(idx, input){
                post_data[$(input).attr("id")] = $(input).val();
            });

            $.post(url, post_data)
            .success(function(data){
                refreshPage(options, data);
            });
        }

        function updateRequest(edit, options, url, cells, old_text){
            var disp = this;
            var post_data = {};
            var uid = "";

            [].forEach.call(cells, function(cell){
                if($(cell).attr("field_id") === "id"){
                    uid = $(cell).children(".display").first().text();
                }
                post_data[$(cell).attr("field_id")] = $(cell).children(".edit").first().val();
            });
            url = url.substring(0, url.lastIndexOf("/")) + "/" + uid;
            $.post(url, post_data)
            .success(function(data){
                refreshPage(options, data);
            })
            .error(function(xhr, data, err){
                $(disp).text(old_text);
                $(edit).val(old_text);
            });
        }

        function handleTable(options, data){
            $("#"+ options["table-div"]).html(renderTable(options, data));
            $("td."+ options["td-class"]).editable({
                onHandle: function(edit, cells, old_text){
                    updateRequest.call(this, edit, options, 
                        data["update_url"], cells, old_text);
                },
            });
        }

        function handleForm(options, data){
            $("#"+ options["form-div"]).html(renderForm(options, data));
            //setup form submit handler
            $("#" + options["form-name"]).submit(function(e){
                e.preventDefault();
                postRequest(
                    options, 
                    data["post_url"],
                    $(".form-control"));
            });
        }

        function refreshPage(options, data){
            //draw table and set its event handlers
            handleTable(options, data);

            //draw form and set its handlers
            handleForm(options, data);

            var dateFormat = {
                dateFormat: "yy-mm-dd"
            };
            
            //setup datepicker 
            $("input.Date").datepicker(dateFormat);
            $("td[field_type=Date] > .edit").datepicker($.extend({
                onClose: function(date){
                    var e = $.Event("keypress");
                    e.which = 13;
                    e.keyCode = 13;
                    $(this).trigger(e);
                    this.blur();
                }
            }, dateFormat));
        }

        function handleLinks(options){
            //draw links
            $("#"+ options["links-div"]).html(renderLinks(options));
            //setup handlers
            $("."+ options["links-class"]).click(function(e){
                var url = options["links-var"][$(this).attr("id")][1];

                $.getJSON(url, function(data){
                    refreshPage(options, data);
                });
                e.preventDefault();
            });
        }

        function ctor(options){
            this.options = $.extend(defaultOptions, options);
        };

        ctor.prototype.run = function(){
            var options = this.options;
            
            //setup ajax parameters
            $.ajaxSetup({
                beforeSend: function(xhr, settings) {
                    var csrftoken = getCfrsCookie(options);

                    $("#"+ options["errors-div"]).html("");
                    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", csrftoken);
                    }
                },
                error: function(xhr, data, err){
                    showErrors(xhr.responseJSON, options);
                }
            });
            //draw links and setup handlers
            handleLinks(options);
        };

        return new ctor(options);
    }    
}(jQuery));