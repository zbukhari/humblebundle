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
		dateStr = '<p class="text-muted" data-toggle="tooltip" data-placement="bottom" title="Item may still available but at full price.">Sale&nbsp;expired';
	} else {
		var dateStr
		if((date.getTime() - nowDate.getTime()) < (86400 * 1000))
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

	return html;
}

function priceFormatter(value, row, index) {
	var price;
	var saleDate = new Date(row['sale_end'] * 1000);

	if(saleDate.getTime() <= nowDate.getTime()) {
		// price = '<s>' + row['current_price'][0] + '</s>&nbsp;' + row['full_price'][0]; // current_price full_price
		price = row['full_price'][0] + '&nbsp;<s>' + row['current_price'][0] + '</s>'; // full_price current_price
	} else {
		price = row['current_price'][0];
	}

	// return price;
	return parseFloat(Math.round(price * 100) / 100).toFixed(2);
}

// Unfortunately this leads to confusion unless we let the user know the full and current price.
// We'll do that in the formatter but we'll sort based off of the current price.  Now the user
// will know how much they could've saved for an expired sale :'-( Sorry ya'll!  My JS isn't
// strong!
function priceSorter(a, b, rowA, rowB) {
	if(a > b)
		return 1;
	if(a < b)
		return -1;

	return 0;
}

function userRatingFormatter(value, row, index) {
	var html;

	if(value == null)
		html = '-';
	else
		// We really should not get here.  value is not defined.  console.log shows it as such, JSON shows it as such, JS shows it as such but it ends up here and then fails on review_text.  hamlet_storefront - 2018-06-11.
		if(typeof(value['review_text']) == 'undefined')
			return '-';
		else
			// html = '<p value['steam_percent'] + '%&nbsp;|&nbsp;' + value['review_text'].replace(' ','&nbsp;');
			html = '<p data-toggle="tooltip" data-placement="bottom" title="' +
				value['steam_percent'] + '% of ' + value['steam_count'] + ' users gave a ' +
				value['review_text'] + ' rating.' + '">' + value['steam_percent'] + '%</p>';

	return html;
}

function userRatingSorter(a, b, rowA, rowB) {
	var tmpA;
	var tmpB;
	if(rowA['user_rating'] == null)
		tmpA = 0;
	else
		tmpA = a['steam_percent'];

	if(rowB['user_rating'] == null)
		tmpB = 0;
	else
		tmpB = b['steam_percent'];

	if(tmpA > tmpB)
		return 1;
	if(tmpA < tmpB)
		return -1;

	return 0;
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
				value[i] = '<i class="fas fa-music" title="' + value[i] + '"></i>';
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
			// Poopy icons
			case 'oculus-rift':
			case 'vive':
				value[i] = '<i class="fas fa-glasses" title="' + value[i] + '"></i>';
				break;
			// Also poopy icons
			case 'mp3':
			case 'wav':
				value[i] = '<i class="fas fa-music" title="' + value[i] + '"></i>';
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
	sortStable: true,
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
	sortName: 'sale_end',
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
			sorter: priceSorter,
			searchable: true,
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
			sortable: true,
			searchable: true,
			filterControl: 'input',
			formatter: userRatingFormatter,
			sorter: userRatingSorter,
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
