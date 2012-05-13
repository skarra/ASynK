// 
// Created       : Sat May 05 13:15:20 IST 2012
// Last Modified : Sun May 13 14:09:30 IST 2012
//
// Copyright (C) 2012, Sriram Karra <karra.etc@gmail.com>
// All Rights Reserved
//
// Licensed under the GNU AGPL v3
// 

function hideAllSheetDivs() {
    $("#sheet").children().css({display : "none"})
}

// Register callbacks to handle specific events on our main UI.
function addFormHandlers () {
    console.log('addFormHandlers');

    $("#home").mouseenter(function () {
	hideAllSheetDivs();
	$("#home_text").css({display : "block"});
    })

    $("#announce").mouseenter(function () {
	hideAllSheetDivs()
	$("#announce_text").css({display : "block"})
    })

    $("#downloads").mouseenter(function () {
	hideAllSheetDivs()
	$("#downloads_text").css({display : "block"})
    })

    $("#doc").mouseenter(function () {
	hideAllSheetDivs()
	$("#doc_text").css({display : "block"});
    })

    $("#about").mouseenter(function () {
	hideAllSheetDivs()
	$("#about_text").css({display : "block"})
    })

    $(".announce_download").click(function () {
	$("#downloads").mouseenter();
    })
}

function onLoad () {
    // Initialize the database if available
    addFormHandlers();
}

jQuery(onLoad);
