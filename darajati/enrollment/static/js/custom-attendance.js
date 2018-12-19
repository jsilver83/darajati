$(function () {
    var counter = 1;

    //http://stackoverflow.com/questions/7650063/how-can-i-prevent-window-onbeforeunload-from-being-triggered-by-javascript-href
    //store onbeforeunload for later use
    $(window).data('beforeunload', window.onbeforeunload);


    var confirmOnPageExit = function (e) {
        // If we haven't been passed the event get the window.event
        e = e || window.event;

        var message = 'You changed the attendance of some students but the changes are not saved yet!';

        // For IE6-8 and Firefox prior to version 4
        if (e) {
            e.returnValue = message;
        }

        // For Chrome, Safari, IE8+ and Opera 12+
        return message;
    };


    $("button[type=submit]").mousedown(function () {
        window.onbeforeunload = null;
        window.onbeforeunload = $(window).data('beforeunload');
    });

    $("select").change(function () {
        window.onbeforeunload = confirmOnPageExit;

        var val = $(this).val();
        if (val == "abs") {
            $(this).parent("div").parent("div").parent("td").removeClass("warning");
            $(this).parent("div").parent("div").parent("td").removeClass("success");
            $(this).parent("div").parent("div").parent("td").addClass("error");
        }
        else if (val == "lat") {
            $(this).parent("div").parent("div").parent("td").removeClass("error");
            $(this).parent("div").parent("div").parent("td").removeClass("success");
            $(this).parent("div").parent("div").parent("td").addClass("warning");
        }
        else if (val == "exc") {
            $(this).parent("div").parent("div").parent("td").removeClass("error");
            $(this).parent("div").parent("div").parent("td").removeClass("warning");
            $(this).parent("div").parent("div").parent("td").addClass("success");
        }
        else {
            $(this).parent("div").parent("div").parent("td").removeClass("warning");
            $(this).parent("div").parent("div").parent("td").removeClass("success");
            $(this).parent("div").parent("div").parent("td").removeClass("error");
        }
    });

    $(".alert-warning").delay(4000).slideUp(500, function () {
        $(this).alert('close');
    });
});