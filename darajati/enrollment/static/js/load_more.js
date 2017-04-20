/**
 * Created by malnajdi on 2/16/17.
 */

$(document).ready(function () {
    var size_li = $(".result-list a").size();
    var x = 20;
    if (size_li < 20) {
        $('.load-more').hide();
    }
    $('.result-list a:lt(' + x + ')').show();
    $('.load-more').click(function () {

        x = (x + 20 <= size_li) ? x + 20 : size_li;
        $('.result-list a:lt(' + x + ')').show();
        if (x >= size_li) {
            $('.load-more').hide();
        }
    });
});
