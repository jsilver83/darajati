//Preloader
$(window).load(function () {
    $('.preloader').fadeOut(500);
});


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


	function mob_quick_access(){
		if ($('.footer').isOnScreen() == true) {
	       $('.mob-quick-access').css('position','absolute');
	    }
	    else{
	    	$('.mob-quick-access').css('position','');
	    }
	}
	mob_quick_access();

	$(window).scroll(function() {
	    mob_quick_access();
	});


	$('.mob-quick-access').click(function(){
		$('body').css({'overflow':'hidden'});
		$('.quick-access').addClass('blanket');
	});

	$('.quick-access-close').click(function(){
		$('body').css({'overflow':''});
		$('.quick-access').removeClass('blanket');
	});

	$("#id_search_value").keydown(function(){
		$('.errorlist').hide();
	});

});