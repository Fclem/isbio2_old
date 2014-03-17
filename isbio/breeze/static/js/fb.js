//$(document).ready(function(){
  $("form").delegate(".component", "mousedown", function(md){
    $(".popover").remove();

    md.preventDefault();
    var tops = [];
    var mouseX = md.pageX;
    var mouseY = md.pageY;
    var $temp;
    var timeout;
    var $this = $(this);
    var delays = {
      main: 0,
      form: 120
    }
    var type;

    if($this.parent().parent().parent().parent().attr("id") === "components"){
      type = "main";
    } else {
      type = "form";
    }

    var delayed = setTimeout(function(){
      if(type === "main"){
        $temp = $("<form class='form-horizontal span6' id='temp'></form>").append($this.clone());
      } else {
        if($this.attr("id") !== "legend"){
          $temp = $("<form class='form-horizontal span6' id='temp'></form>").append($this);
        }
      }

      $("body").append($temp);

      $temp.css({"position" : "absolute",
                 "top"      : mouseY - ($temp.height()/2) + "px",
                 "left"     : mouseX - ($temp.width()/2) + "px",
                 "opacity"  : "0.8"}).show()

      var half_box_height = ($temp.height()/2);
      var half_box_width = ($temp.width()/2);
      var $target = $("#target");
      var tar_pos = $target.position();
      var $target_component = $("#target .component");

      $(document).delegate("body", "mousemove", function(mm){

        var mm_mouseX = mm.pageX;
        var mm_mouseY = mm.pageY;

        $temp.css({"top"      : mm_mouseY - half_box_height + "px",
          "left"      : mm_mouseX - half_box_width  + "px"});

        if ( mm_mouseX > tar_pos.left &&
          mm_mouseX < tar_pos.left + $target.width() + $temp.width()/2 &&
          mm_mouseY > tar_pos.top &&
          mm_mouseY < tar_pos.top + $target.height() + $temp.height()/2
          ){
            $("#target").css("background-color", "#ffffff");
            $target_component.css({"border-top" : "1px solid white", "border-bottom" : "none"});
            tops = $.grep($target_component, function(e){
              return ($(e).position().top -  mm_mouseY + half_box_height > 0 && $(e).attr("id") !== "legend");
            });
            if (tops.length > 0){
              $(tops[0]).css("border-top", "1px solid #22aaff");
            } else{
              if($target_component.length > 0){
                $($target_component[$target_component.length - 1]).css("border-bottom", "1px solid #22aaff");
              }
            }
          } else{
            $("#target").css("background-color", "#fff");
            $target_component.css({"border-top" : "1px solid white", "border-bottom" : "none"});
            $target.css("background-color", "#fff");
          }
      });

      $("body").delegate("#temp", "mouseup", function(mu){
        mu.preventDefault();

        var mu_mouseX = mu.pageX;
        var mu_mouseY = mu.pageY;
        var tar_pos = $target.position();

        $("#target .component").css({"border-top" : "1px solid white", "border-bottom" : "none"});

        // acting only if mouse is in right place
        if (mu_mouseX + half_box_width > tar_pos.left &&
          mu_mouseX - half_box_width < tar_pos.left + $target.width() &&
          mu_mouseY + half_box_height > tar_pos.top &&
          mu_mouseY - half_box_height < tar_pos.top + $target.height()
          ){
            $temp.attr("style", null);
            // where to add
            if(tops.length > 0){
              $($temp.html()).insertBefore(tops[0]);
            } else {
              $("#target fieldset").append($temp.append("\n\n\ ").html());
            }
          } else {
            // no add
            $("#target .component").css({"border-top" : "1px solid white", "border-bottom" : "none"});
            tops = [];
          }

        //clean up & add popover
        $target.css("background-color", "#fff");
        $(document).undelegate("body", "mousemove");
        $("body").undelegate("#temp","mouseup");
        $("#target .component").popover({trigger: "manual", html: true, placement: "right"});
        $temp.remove();
        genSource();
      });
    }, delays[type]);

    $(document).mouseup(function () {
      clearInterval(delayed);
      return false;
    });
    $(this).mouseout(function () {
      clearInterval(delayed);
      return false;
    });
  });

  var genSource = function(){
    var $temptxt = $("<div>").html($("#build").html());
    //scrubbbbbbb
    $($temptxt).find(".component").attr({
      "title": null,
      "data-original-title":null,
      "data-type": null,
      "data-content": null,
      "rel": null,
      "trigger":null,
      "style": null});
    $($temptxt).find(".valtype").attr("data-valtype", null).removeClass("valtype");
    $($temptxt).find(".component").removeClass("component");
    $($temptxt).find("form").attr({"id":  null, "style": null});
    $("#source").val( constructXML() );
    //$("#source").val($temptxt.html().replace(/\n\ \ \ \ \ \ \ \ \ \ \ \ /g,"\n"));
  }

  var constructXML = function(){
    // create root element; script ID should better be obtained here
    var docxml = "<rScript name=\"undefined\">\n<inputArray>\n";
    // create input array
    $("#target").find(".component").each(function(){
      var tmp = '';
      var fieldLabel = $(this).find('[data-valtype="label"]').text();
      var fieldVar = $(this).find('[data-valtype="r_inline"]').val();

      switch ($(this).attr("breeze-control")){
        case "numeric_input":
          docxml += '<inputItem comment=\"' + fieldLabel + '\" default=\"\" rvarname=\"' + fieldVar + '\" type=\"NUM\" ';
          docxml += 'val=\"' + $(this).find('[data-valtype="numeric_limits"]').attr('def') + '\" ';
          docxml += 'max=\"' + $(this).find('[data-valtype="numeric_limits"]').attr('max') + '\" min=\"' + $(this).find('[data-valtype="numeric_limits"]').attr('min') + '\" ';
          docxml += 'help=\"' + $(this).find('[data-valtype="help_text"]').val() + '\" ';
          docxml += 'optional=\"' + $(this).find('[data-valtype="flag_optional"]').val() + '\"/> \n';
          break;
        case "text_input":
          docxml += '<inputItem comment=\"' + fieldLabel + '\" default=\"\" rvarname=\"' + fieldVar + '\" type=\"TEX\" val=\"' + $(this).find('[data-valtype="text_default"]').val() + '\" ';
          docxml += 'help=\"' + $(this).find('[data-valtype="help_text"]').val() + '\" ';
          docxml += 'optional=\"' + $(this).find('[data-valtype="flag_optional"]').val() + '\"/> \n';
          break;
        case "text_area":
          docxml += '<inputItem comment=\"' + fieldLabel + '\" default=\"\" rvarname=\"' + fieldVar + '\" type=\"TAR\" val=\"\" ';
          docxml += 'help=\"' + $(this).find('[data-valtype="help_text"]').val() + '\" ';
          docxml += 'optional=\"' + $(this).find('[data-valtype="flag_optional"]').val() + '\"/> \n';
          break;
        case "check_box":
          docxml += '<inputItem comment=\"' + fieldLabel + '\" default=\"\" rvarname=\"' + fieldVar + '\" type=\"CHB\" val=\"' + $(this).find('[data-valtype="checkbox_def"]').prop('checked') + '\" ';
          docxml += 'help=\"' + $(this).find('[data-valtype="help_text"]').val() + '\" /> \n';
          break;
        case "file_upload":
          docxml += '<inputItem comment=\"' + fieldLabel + '\" default=\"\" rvarname=\"' + fieldVar + '\" type=\"FIL\" val=\"\" ';
          docxml += 'help=\"' + $(this).find('[data-valtype="help_text"]').val() + '\" ';
          docxml += 'optional=\"' + $(this).find('[data-valtype="flag_optional"]').val() + '\"/> \n';
          break;
        case "template_upload":
          docxml += '<inputItem comment=\"' + fieldLabel + '\" default=\"' + $(this).find('[data-valtype="tmpl_list"]').val() + '\" rvarname=\"' + fieldVar + '\" type=\"TPL\" val=\"\" ';
          docxml += 'help=\"' + $(this).find('[data-valtype="help_text"]').val() + '\" ';
          docxml += 'optional=\"' + $(this).find('[data-valtype="flag_optional"]').val() + '\"/> \n';
          break;
        case "dataset_selector":
          tmp = '';
          docxml += '<inputItem comment=\"' + fieldLabel + '\" default=\"\" rvarname=\"' + fieldVar + '\" type=\"DTS\" val=\"\" ';
          docxml += 'help=\"' + $(this).find('[data-valtype="help_text"]').val() + '\" > \n';
          docxml += '<altArray>' + '\n';
          tmp = $.map($(this).find("option"), function(e,i){return $(e).text()}).join("\n");
          docxml += "<altItem>" + tmp.split("\n").join("</altItem>\n<altItem>") + "</altItem>\n";
          docxml += '</altArray>\n</inputItem>\n';
          break;
        case "dtm_samples_selector":
          docxml += '<inputItem comment=\"' + fieldLabel + '\" default=\"\" rvarname=\"' + fieldVar + '\" type=\"DTM_SAMPLES\" val=\"\" ';
          docxml += 'help=\"' + $(this).find('[data-valtype="help_text"]').val() + '\" /> \n';
          break;
        case "drop_down":
          tmp = '';
          docxml += '<inputItem comment=\"' + fieldLabel + '\" default=\"\" rvarname=\"' + fieldVar + '\" type=\"DRP\" val=\"\" ';
          docxml += 'help=\"' + $(this).find('[data-valtype="help_text"]').val() + '\" > \n';
          docxml += '<altArray>' + '\n';
          tmp = $.map($(this).find("option"), function(e,i){return $(e).text()}).join("\n");
          docxml += "<altItem>" + tmp.split("\n").join("</altItem>\n<altItem>") + "</altItem>\n";
          docxml += '</altArray>\n</inputItem>\n';
          break;
        case "mult_select":
          docxml += '<inputItem comment=\"' + fieldLabel + '\" default=\"\" rvarname=\"' + fieldVar + '\" type=\"MLT\" val=\"\" ';
          docxml += 'help=\"' + $(this).find('[data-valtype="help_text"]').val() + '\" > \n';
          docxml += '<altArray>' + '\n';
          tmp = $.map($(this).find("option"), function(e,i){return $(e).text()}).join("\n");
          docxml += "<altItem>" + tmp.split("\n").join("</altItem>\n<altItem>") + "</altItem>\n";
          docxml += '</altArray>\n</inputItem>\n';
          break;
      }
    });

    docxml += "</inputArray>\n"
    // escape builder form html and incorporate it into xml; (xml parsing fails if not escaped!)
    var builder_form = $("#target").html().replace(/</g, '&lt;').replace(/>/g, '&gt;');
    docxml += '<builder representation=\"\">' + builder_form + '</builder>' + '\n';
    docxml += "</rScript>";
    return docxml;
  }

  //activate legend popover
  $("#target .component").popover({trigger: "manual", html: true, placement: "right"});
  //popover on click event
  $("#target").delegate(".component", "click", function(e){
    e.preventDefault();
    $(".popover").hide();
    // $active_component is .valtype - content of .component div tag
    var $active_component = $(this);
    $active_component.popover("show");

    var valtypes = $active_component.find(".valtype");
    // iterate over all the elements of the component
    $.each(valtypes, function(i,e){
      // fill out the form on popover
      // by extracting data tha is stored on the form
      // valID - input ID on the popover form
      var valID ="#" + $(e).attr("data-valtype");
      var val;
      if(valID ==="#placeholder"){
          val = $(e).attr("placeholder");
          $(".popover " + valID).val(val);
      } else if(valID==="#checkbox"){
          val = $(e).attr("checked");
          $(".popover " + valID).attr("checked",val);
      } else if(valID==="#option"){
          val = $.map($(e).find("option"), function(e,i){return $(e).text()});
          val = val.join("\n")
          $(".popover "+valID).text(val);
      } else if(valID==="#checkboxes"){
          val = $.map($(e).find("label"), function(e,i){return $(e).text().trim()});
          val = val.join("\n")
          $(".popover "+valID).text(val);
      } else if(valID==="#radios"){
          val = $.map($(e).find("label"), function(e,i){return $(e).text().trim()});
          val = val.join("\n");
          $(".popover "+valID).text(val);
          $(".popover #name").val($(e).find("input").attr("name"));
      } else if(valID==="#inline-checkboxes"){
          val = $.map($(e).find("label"), function(e,i){return $(e).text().trim()});
          val = val.join("\n")
          $(".popover "+valID).text(val);
      } else if(valID==="#inline-radios"){
          val = $.map($(e).find("label"), function(e,i){return $(e).text().trim()});
          val = val.join("\n")
          $(".popover "+valID).text(val);
          $(".popover #name").val($(e).find("input").attr("name"));
      } else if(valID==="#button") {
          val = $(e).text();
          var type = $(e).find("button").attr("class").split(" ").filter(function(e){return e.match(/btn-.*/)});
          $(".popover #color option").attr("selected", null);
          if(type.length === 0){
            $(".popover #color #default").attr("selected", "selected");
          } else {
            $(".popover #color #"+type[0]).attr("selected", "selected");
          }
          val = $(e).find(".btn").text();
          $(".popover #button").val(val);
      } else if (valID==="#r_inline"){
          val = $(e).val();
          $(".popover " + valID).val(val);
      } else if (valID==="#help_text"){
          val = $(e).val();
          $(".popover " + valID).val(val);
      } else if (valID==="#text_default"){
          val = $(e).val();
          $(".popover " + valID).val(val);
      } else if (valID==="#flag_optional"){
          tmp = $(e).val();
          if (tmp == '1') val = true;
          else val = false;
          $(".popover " + valID).prop('checked', val);
      } else if (valID==="#numeric_limits"){
          $(".popover #max_limit").val($(e).attr('max'));
          $(".popover #min_limit").val($(e).attr('min'));
          $(".popover #def_val").val($(e).attr('def'));
      } else if (valID==="#checkbox_def"){
          if ($(e).prop("checked")) $(".popover " + valID).prop('checked', true);
          else $(".popover " + valID).prop('checked', false);
      } else if (valID==="#db_list"){
          var existing = $(e).find("option");
          $.getJSON('/resources/scripts/script-editor/get-content/datasets', function(data) {
            var options = [];
            $.each(data, function(key, val) { options.push('<option>' + key + '</option>'); });
            $(valID).append(options);
            // mark previously selected
            $.each(existing, function(i,e){
              $(valID).find("option:contains(" + $(e).text() + ")").prop('selected', true);
            });
          });
      } else if (valID==="#tmpl_list"){
          var existing = $(e).val();
          $.getJSON('/resources/scripts/script-editor/get-content/templates', function(data) {
            var options = [];
            $.each(data, function(key, val) { options.push('<option>' + key + '</option>'); });
            $(valID).append(options);
            // mark previously selected
            $(valID).find("option:contains(" + existing + ")").prop('selected', true);
          });
      } else { // apparently 'label' goes to ELSE
        val = $(e).text();
        $(".popover " + valID).val(val);
      }
    });

    // fired when click CANCE button on field popover
    $(".popover").delegate(".btn-danger", "click", function(e){
      e.preventDefault();
      $active_component.popover("hide");
    });

    // fired when click SAVE button on field popover
    $(".popover").delegate(".btn-primary", "click", function(e){
      e.preventDefault();
      var inputs = $(".popover input,.popover select");
      // why textarea is pushed here?
      // inputs.push($(".popover textarea")[0]);

      // Now we iterate over each textarea on the form
      // I have no idea why the author used to pick only
      // [0] element before (see comment above).
      $.each($(".popover textarea"), function(i,e){ inputs.push(e); });

      // for each input on the popover
      $.each(inputs, function(i,e){
        var vartype = $(e).attr("id");
        var value = $active_component.find('[data-valtype="'+vartype+'"]')
        // console.log(vartype); // this is for debugging
        if(vartype==="placeholder"){
          $(value).attr("placeholder", $(e).val());
        } else if (vartype==="option"){
          var options = $(e).val().split("\n");
          $(value).html("");
          $.each(options, function(i,e){
            $(value).append("\n      ");
            $(value).append($("<option>").text(e));
          });
        } else if (vartype==="checkboxes"){
          var checkboxes = $(e).val().split("\n");
          $(value).html("\n      <!-- Multiple Checkboxes -->");
          $.each(checkboxes, function(i,e){
            if(e.length > 0){
              $(value).append('\n      <label class="checkbox">\n        <input type="checkbox" value="'+e+'">\n        '+e+'\n      </label>');
            }
          });
          $(value).append("\n  ")
        } else if (vartype==="radios"){
          var group_name = $(".popover #name").val();
          var radios = $(e).val().split("\n");
          $(value).html("\n      <!-- Multiple Radios -->");
          $.each(radios, function(i,e){
            if(e.length > 0){
              $(value).append('\n      <label class="radio">\n        <input type="radio" value="'+e+'" name="'+group_name+'">\n        '+e+'\n      </label>');
            }
          });
          $(value).append("\n  ")
          $($(value).find("input")[0]).attr("checked", true)
        } else if (vartype==="inline-checkboxes"){
          var checkboxes = $(e).val().split("\n");
          $(value).html("\n      <!-- Inline Checkboxes -->");
          $.each(checkboxes, function(i,e){
            if(e.length > 0){
              $(value).append('\n      <label class="checkbox inline">\n        <input type="checkbox" value="'+e+'">\n        '+e+'\n      </label>');
            }
          });
          $(value).append("\n  ")
        } else if (vartype==="inline-radios"){
          var radios = $(e).val().split("\n");
          var group_name = $(".popover #name").val();
          $(value).html("\n      <!-- Inline Radios -->");
          $.each(radios, function(i,e){
            if(e.length > 0){
              $(value).append('\n      <label class="radio inline">\n        <input type="radio" value="'+e+'" name="'+group_name+'">\n        '+e+'\n      </label>');
            }
          });
          $(value).append("\n  ")
          $($(value).find("input")[0]).attr("checked", true)
        } else if (vartype === "button"){
          var type =  $(".popover #color option:selected").attr("id");
          $(value).find("button").text($(e).val()).attr("class", "btn "+type);
        } else if (vartype === "r_inline"){
          $(value).val($(e).val());
        } else if (vartype === "help_text"){
          $(value).val($(e).val());
        } else if (vartype === "text_default"){
          $(value).val($(e).val());
        } else if (vartype === "flag_optional"){
          if ( $(e).prop("checked") ) $(value).val(1);
          else $(value).val(0);
        } else if (vartype === "max_limit"){
          $active_component.find('[data-valtype="numeric_limits"]').attr('max', $(e).val());
        } else if (vartype === "min_limit"){
          $active_component.find('[data-valtype="numeric_limits"]').attr('min', $(e).val());
        } else if (vartype === "def_val"){
          $active_component.find('[data-valtype="numeric_limits"]').attr('def', $(e).val());
        } else if (vartype === "checkbox_def"){
          $(value).prop("checked", $(e).prop("checked"));
        } else if (vartype === "db_list"){
          $(value).find("option").remove();
          $(e).find("option:selected").clone().appendTo(value);
        } else if (vartype === "tmpl_list"){
          $(value).val($(e).find("option:selected").text());
        } else {
          $(value).text($(e).val());
        }
      $active_component.popover("hide");
      genSource();
    });
    });
  });
  $("#navtab").delegate("#sourcetab", "click", function(e){
    genSource();
  });
//});
