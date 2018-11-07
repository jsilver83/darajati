$(document).ready(function(){
	var window_height = '',header_height = '',footer_height = '', window_width = '';

	function size_calcs(){
		window_height = $(window).outerHeight();
		header_height = $('.header').outerHeight();
		footer_height = $('.footer').outerHeight();
		window_width = $(window).outerWidth();
	}

	function dalilcntntheight(){
		$('.fit-window').css('min-height', window_height - header_height - footer_height);

		if(window_width <= 850){
			$('.content-panel').css('min-height', window_height - header_height - footer_height);
		}
		else{
			$('.content-panel').css('min-height', '');
		}

	}


	size_calcs();
	dalilcntntheight();

	$(window).resize(function(){

		size_calcs();
		dalilcntntheight();

	});


	$.fn.isOnScreen = function(){

	    var win = $(window);

	    var viewport = {
	        top : win.scrollTop(),
	        left : win.scrollLeft()
	    };
	    viewport.right = viewport.left + win.width();
	    viewport.bottom = viewport.top + win.height();

	    var bounds = this.offset();
	    bounds.right = bounds.left + this.outerWidth();
	    bounds.bottom = bounds.top + this.outerHeight();

	    return (!(viewport.right < bounds.left || viewport.left > bounds.right || viewport.bottom < bounds.top || viewport.top > bounds.bottom));

	};


    $('.info-icon').click(function () {
        $('.info-cntnt').hide();
        $(this).next('.info-cntnt').show();
    });

    $(window).click(function () {
        if ($(this).hasClass('info-icon')) {
            $('.info-cntnt').hide();
        }
    });

    $(document).mouseup(function (e) {
        var container = $(".info-cntnt");

        // if the target of the click isn't the container nor a descendant of the container
        if (!container.is(e.target) && container.has(e.target).length === 0) {
            container.hide();
        }
    });

});