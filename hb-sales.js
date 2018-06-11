// We're going to use this to compare dates.
var nowDate = new Date(Date.now());

// Here we define functions to display larger data in a "modal" window.
// I can't get the icons to work :-(  Not sure anyone really cares about my code but help would be appreciated! :-D
function getHeight() {
	return $(window).height() - $('h1').outerHeight(true);
}

// JavaScript has no strftime
function saleEndDateFormatter(value, row, index) {
	var date = new Date(value * 1000);
	if(date <= nowDate) {
		dateStr = '<p class="text-muted" data-toggle="tooltip" data-placement="bottom" title="Item is still available but at full price.">Sale&nbsp;expired';
	} else {
		var dateStr
		if((date.getTime() - nowDate.getTime()) < 86400000)
			dateStr = '<p class="text-danger" data-toggle="tooltip" data-placement="bottom" title="Less than 24 hours!">';
		else
			dateStr = '<p class="text-success">';

		// Y-m-d
		dateStr += date.getFullYear() + '-';

		if(date.getMonth() < 10)
			dateStr += '0';
		dateStr += date.getMonth() + '-';

		if(date.getDate() < 10)
			dateStr += '0';
		dateStr += date.getDate() + 'T';

		if(date.getHours() < 10)
			dateStr += '0';
		dateStr += date.getHours() + ':';

		if(date.getMinutes() < 10)
			dateStr += '0';
		dateStr += date.getMinutes() + ':';

		if(date.getSeconds() < 10)
			dateStr += '0';
		dateStr += date.getSeconds();
	}

	dateStr += '</p>';

	return dateStr;
}


// Here we will make a singular detailed listing of information for the user
// Currently this means system requirements, description, etc
function detailFormatter(index, row, element) {
	var html = '<div align="center"><h1>System requirements</h1></div>\n\n';
	html += row['system_requirements'] + '\n\n';
	html += '<div align="center"><h1>Description</h1></div>\n\n';
	html += row['description'] + '\n\n';

	html += 'current_price: ' + row['current_price'][0] + '<br>\n\n';
	html += 'full_price: ' + row['full_price'][0] + '<br>\n\n';

	return html;
}

function priceFormatter(value, row, index) {
	var price;
	var saleDate = new Date(row['sale_end'] * 1000);

	if(saleDate.getTime() <= nowDate.getTime()) {
		// price = row['full_price'].join('&nbsp')
		price = row['full_price'][0]
	} else {
		// price = row['current_price'].join('&nbsp;');
		price = row['current_price'][0];
	}

	return price;
}

function userRatingFormatter(value, row, index) {
	var html = '-';

	if(value)
		html = value['steam_percent'] + '%&nbsp;|&nbsp;' + value['review_text'].replace(' ','&nbsp;');

	return html;
}

function humanNameFormatter(value, row, index) {
	var url = '<a href="https://www.humblebundle.com/store/' + row['human_url'] + '" target="_blank">' + row['human_name'] + '</a>';

	return  url;
}

function deliveryMethodsFormatter(value, row, index) {
	for(var i=0; i< value.length; i++) {
		switch(value[i]) {
			case 'android':
				value[i] = '<i class="fab fa-google-play" title="Android"></i>';
				break;
			// This icon has DRM-free on it but alas that is not marked free so using this icon
			case 'download':
				value[i] = '<i class="fas fa-download" title="Download"></i>';
				break;
			case 'steam':
				value[i] = '<i class="fab fa-steam-symbol" title="Steam"></i>';
				break;
			// Not the best representation
			case 'other-key':
				value[i] = '<i class="fas fa-key" title="Other key"></i>';
				break;
			// audio-download
			case 'audio-download':
				value[i] = '<i class="fas fa-music" title="audio-download"></i>';
				break;
			// No reasonable icons in fa
			case 'uplay':
			case 'blizzard':
			default:
				break;
		}
	}

	return value.join('&nbsp;');
}

function platformFormatter(value, row, index) {
	for(var i=0; i < value.length; i++) {
		switch(value[i]) {
			case 'mac':
				value[i] = '<i class="fab fa-apple" title="Mac"></i>';
				break;
			case 'windows':
				value[i] = '<i class="fab fa-windows" title="Windows"></i>';
				break;
			case 'linux':
				value[i] = '<i class="fab fa-linux" title="Linux"></i>';
				break;
			case 'android':
				value[i] = '<i class="fab fa-android" title="Android"></i>';
				break;
			default:
				break;
		}
	}

	return value.join('&nbsp;');
}


$('#table').bootstrapTable({
	// url: 'hb-sales.json',
	// data: rawJsonData, // Contains total, rows - doesn't seem to work - works when pulled from url though :-/
	classes: "table table-hover table-dark glyphicon",
	data: jsonData,
	search: false,
	// height: 700,
	// height: getHeight(),
	// I can't find a way to do a logical and across truth values return by the filter-control extension :'-(
	iconsPrefix: 'fas',
	icons: {
		paginationSwitchDown: 'glyphicon-collapse-down icon-chevron-down fa-chevron-down',
		paginationSwitchUp: 'glyphicon-collapse-up icon-chevron-up fa-chevron-up',
		refresh: 'glyphicon-refresh icon-refresh fa-sync',
		toggle: 'glyphicon-list-alt icon-list-alt fa-list',
		columns: 'glyphicon-th icon-th fa-columns',
		detailOpen: 'glyphicon-plus icon-plus fa-plus',
		detailClose: 'glyphicon-minus icon-minus fa-minus'
	},
	// toolbar: '#toolbar',
	idField: 'id',
	uniqueId: 'id',
	filterControl: true,
	filterShowClear: false, // I want to show the icon and if I can't nay!
	filterStrictSearch: true,
/*
	dataField: 'rows',
	totalField: 'total',
	contentType: 'application/json',
	dataType: 'json',
*/
	showColumns: true,
	// showRefresh: false,
	detailView: true,
	detailFormatter: detailFormatter,
	clear: 'glyphicon-trash icon-clear fa-trash',
	columns: [{
			title: 'Sale end',
			field: 'sale_end',
			formatter: saleEndDateFormatter,
			sortable: true,
		}, {
			field: 'human_name',
			title: 'Name',
			searchable: true,
			formatter: humanNameFormatter,
			sortable: true,
			filterControl: 'input',
		}, {
			field: 'current_price',
			title: 'Price',
			formatter: priceFormatter,
			sortable: true,
			filterControl: 'input',
		}, {
			field: 'delivery_methods',
			formatter: deliveryMethodsFormatter,
			title: 'Delivery method',
			searchable: true,
			filterControl: 'input',
		}, {
			field: 'platforms',
			title: 'Platforms',
			searchable: true,
			formatter: platformFormatter,
			filterControl: 'input',
		}, {
			field: 'user_rating',
			title: 'User rating',
			formatter: userRatingFormatter,
			sortable: true,
			searchable: true,
			filterControl: 'input',
	}], // Close columns
/*
			field: 'other_links',
			title: 'Other links',
			visible: false,
		}, {
			field: 'developers',
			title: 'Developers',
			visible: false,
		}, {
			field: 'system_requirements',
			title: 'System requirements',
			visible: false,
		}, {
			field: 'description',
			title: 'Description',
			// visible: false,
			formatter: operateFormatter,
			events: showMeDaModal,
	}],
*/ // We don't care to show these here - they will be in the detail view.
}); // Close table
