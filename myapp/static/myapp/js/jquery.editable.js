// Simple jQuery plugin which makes tables editable
// Author: Dmitry A. Paramonov (c) 2014
(function($){
    'use strict'

    $.fn.editable = function(options){
        var settings = $.extend({
            onHandle: function(display, rows, old_text){},
        }, options);

        return this.each(function(){
            if(!$(this).text){
                return $(this);
            }
            
            $(this).on("click", function(e){
                // may be slow...
                // $(".edit").hide();
                // $(".display").show();
                $(this).children(".display").hide();
                
                var edit = $(this).children(".edit");
                
                edit.attr("size", $(this).attr("size"));
                edit.show();
                edit.focus();
            }).on("mousedown", function(e){
                //workaround to prevent blur event before click
                e.preventDefault();
            });

            var txt = $(this).text();
            var span = "<span class='display'></span>";
            var input = "<input type='text' class='edit'>";

            $(this).text("");
            $(this)
            .append(span)
            .append(input);

            var display = $(this).children(".display");
            var edit = $(this).children(".edit");

            display.text(txt);
            display.show();
            edit.val(txt);
            edit.hide();

            $(this).children("input.edit").blur(function(e){
                $(this).hide();
                $(this).siblings(".display").first().show();
            });

            $(this).children("input.edit").keypress(function(e){
                if(e.which == 13){
                    $(span).text($(this).val());

                    var display = $(this).siblings(".display").first();
                    var old_text = display.text();
                    
                    display.text($(this).val());
                    display.show();
                    $(this).hide();

                    settings.onHandle.call(
                        display,
                        $(this), 
                        $(this).parent().parent().children(), 
                        old_text);
                }
            });
        });
    }
}(jQuery));