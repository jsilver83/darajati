'use strict';
function handlePaste(e) {
    var clipboardData, pastedData;

    // Stop data actually being pasted into div
    e.stopPropagation();
    e.preventDefault();

    var reKFUPMID = /^\d{9}$/;

    var pasteComments = document.getElementById('pasteComments');
    pasteComments.innerHTML = "<h4>Errors in pasting grades from Excel: </h4><hr>";

    // Get pasted data via clipboard API
    clipboardData = e.clipboardData || window.clipboardData;
    pastedData = clipboardData.getData('Text');

    var allTrs = document.querySelectorAll('.grade');

    var i, emptyGrades = 0;
    for (i = 0; i < allTrs.length; i++) {
        allTrs.item(i).parentElement.parentElement.parentElement.className = "danger";
    }

    var lines = pastedData.split("\n");
    var data, kfupmid, grade, notes, gradeToBeChanged, notesToBeChanged, found, match, errorsFound;

    errorsFound = false;

    for (i = 0; i < lines.length; i++) {
        data = lines[i].split('\t');
        if (data.length === 2 || data.length === 3) {
            kfupmid = data[0];
            match = reKFUPMID.exec(kfupmid);
            if (!match) {
                pasteComments.innerHTML = pasteComments.innerHTML + "[" + kfupmid + "] is NOT a valid KFUPM ID<br>";
                errorsFound = true;
                continue;
            }

            grade = data[1].trim();
            if (isNaN(grade)) {
                pasteComments.innerHTML = pasteComments.innerHTML + "[" + kfupmid + "] does NOT have a valid grade (" + grade + ")<br>";
                errorsFound = true;
                continue;
            }
            if (data.length === 3) {
                notes = data[2].trim();
            } else {
                notes = "";
            }

            found = false;

            var students = document.getElementsByClassName("kfupmid");
            for (var j = 0; j < students.length; j++) {
                if (students.item(j).innerHTML === kfupmid) {
                    gradeToBeChanged = students.item(j).parentElement.parentElement.querySelectorAll('.grade');
                    if (gradeToBeChanged.length === 1) {
                        gradeToBeChanged[0].querySelectorAll('input')[0].value = grade;
                    }
                    notesToBeChanged = students.item(j).parentElement.parentElement.querySelectorAll('.notes');
                    if (notesToBeChanged.length === 1) {
                        notesToBeChanged[0].querySelectorAll('input')[0].value = notes;
                    }

                    if (grade.length > 0) {
                        students.item(j).parentElement.parentElement.className = "success";
                    }
                    else {
                        emptyGrades++;
                        errorsFound = true;
                        pasteComments.innerHTML = pasteComments.innerHTML + "[" + kfupmid + "] has an empty score pasted in<br>";
                    }
                    found = true;
                    break;
                }
            }

            if (!found) {
                pasteComments.innerHTML = pasteComments.innerHTML + "[" + kfupmid + "] is NOT found in the table of students in this page<br>";
                errorsFound = true;
            }
        }
    }

    calculate_average();

    if (errorsFound) {
        pasteComments.style.display = 'block';
    }
}

document.addEventListener('paste', handlePaste);

$(document).ready(function () {

    (function ($) {

        $.fn.enableCellNavigation = function () {

            var arrow = {
                left: 37,
                up: 38,
                right: 39,
                down: 40,
                enter: 13
            };

            // select all on focus
            this.find('input,select').keydown(function (e) {
                // shortcut for key other than arrow keys
                if ($.inArray(e.which, [arrow.left, arrow.up, arrow.right, arrow.down, arrow.enter]) < 0) {
                    return;
                }

                var input = e.target;
                var td = $(e.target).closest('td');
                var moveTo = null;

                switch (e.which) {

                    case arrow.left: {
                        if (typeof input.selectionStart == 'undefined') {
                            moveTo = td.prev('td:has(input,select)');
                        } else if (input.selectionStart == 0) {
                            moveTo = td.prev('td:has(input,select)');
                        }
                        break;
                    }
                    case arrow.right: {
                        if (typeof input.selectionStart == 'undefined') {
                            moveTo = td.next('td:has(input,select)');
                        } else if (input.selectionEnd == input.value.length) {
                            moveTo = td.next('td:has(input,select)');
                        }
                        break;
                    }
                    case arrow.enter: {

                        var tr = td.closest('tr');
                        var pos = td[0].cellIndex;

                        var moveToRow = null;
                        if (e.which == arrow.down) {
                            moveToRow = tr.next('tr');
                        } else if (e.which == arrow.up) {
                            moveToRow = tr.prev('tr');
                        }

                        if (moveToRow.length) {
                            moveTo = $(moveToRow[0].cells[pos]);
                        }

                        break;
                    }

                    case arrow.up:
                    case arrow.down: {

                        var tr = td.closest('tr');
                        var pos = td[0].cellIndex;

                        var moveToRow = null;
                        if (e.which == arrow.down) {
                            moveToRow = tr.next('tr');
                        } else if (e.which == arrow.up) {
                            moveToRow = tr.prev('tr');
                        }

                        if (moveToRow.length) {
                            moveTo = $(moveToRow[0].cells[pos]);
                        }

                        break;
                    }

                }

                if (moveTo && moveTo.length) {

                    e.preventDefault();

                    moveTo.find('input,select').each(function (i, input) {
                        input.focus();
                        input.select();
                    });

                }

            });

        };

    })(jQuery);
    $(function () {
        $('table').enableCellNavigation();
    });

});

$(document).ready(function () {
    $('.grade_quantity').on('keyup paste', calculate_average);
});

function calculate_average() {
    var entryInPercentages = $("#entryPercent").html(); console.log(entryInPercentages);
    var gradeFragmentWeight = $("#weight").html(); console.log(gradeFragmentWeight);
    var total = 0.0;
    var count = 0;
    var average = 0.0;
    var average_in_percent = 0.0;
    $('.grade_quantity').each(function (index) {
        if ($(this).val() != '') {
            var value = parseFloat($(this).val());
            total += value;
            count += 1;
        }
    });
    if (entryInPercentages === "True") {
        average_in_percent = total / count;
        average = average_in_percent / 100 * gradeFragmentWeight;
    }
    else {
        average = total / count;
        average_in_percent = average / gradeFragmentWeight * 100;
    }

    $('.section_average').html(
        "" + average.toFixed(4) + ",  (" + average_in_percent.toFixed(4) + "%)"
    );
}