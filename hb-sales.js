// We're going to use this to compare dates.
var nowDate = new Date(Date.now());
var nowTime = nowDate.getTime();

// Here we define functions to display larger data in a "modal" window.
// I can't get the icons to work :-(  Not sure anyone really cares about my code but help would be appreciated! :-D
function getHeight() {
	return $(window).height() - $('h1').outerHeight(true);
}

// JavaScript has no strftime
function saleEndDateFormatter(value, row, index) {
	var dateStr;

	if(row['sale_end'] == null) {
		dateStr = '';
	} else {
		var endDate = new Date(row['sale_end'] * 1000);
		var endTime = endDate.getTime();

		if(endTime <= nowTime) {
			dateStr = '<p class="text-muted" data-toggle="tooltip" data-placement="bottom" title="Item may still available but at full price.">Sale&nbsp;expired</p>';
		} else {
			dateStr = '';

			// Y-m-d
			dateStr += endDate.getFullYear() + '-';

			var month = endDate.getMonth() + 1;
			if(month < 10) {
				dateStr += '0';
			}
			dateStr += month + '-';

			if(endDate.getDate() < 10) {
				dateStr += '0';
			}
			dateStr += endDate.getDate() + 'T';

			if(endDate.getHours() < 10) {
				dateStr += '0';
			}
			dateStr += endDate.getHours() + ':';

			if(endDate.getMinutes() < 10) {
				dateStr += '0';
			}
			dateStr += endDate.getMinutes() + ':';

			if(endDate.getSeconds() < 10) {
				dateStr += '0';
			}
			dateStr += endDate.getSeconds();
		}
	}
	return dateStr;
}

// Here we will make a singular detailed listing of information for the user
// Currently this means system requirements, description, etc
function detailFormatter(index, row, element) {
	var html = '<div align="center"><h1>System requirements</h1></div>\n\n';
	html += row['system_requirements'] + '\n\n';
	html += '<div align="center"><h1>Description</h1></div>\n\n';
	html += '<div id="desc" style="white-space:pre-wrap;">' + row['description'] + '</div>\n\n';

	// Lets get links in here
	if(row['other_links'].length > 0) {
		html += '<ul>\n';
		row['other_links'].forEach((link) => {
			html += '<li><a href="' + link['other-link'] + '" target="_blank">' + link['other-link-title'] + '</li>\n';
		});
		html += '</ul>\n';
	}

	return html;
}

function priceFormatter(value, row, index) {
	var price;

	if(row['sale_end'] == null)
		return row['full_price']['amount'];

	var endDate = new Date(row['sale_end'] * 1000);
	var endTime = endDate.getTime();

	var tdiff = (endTime-nowTime)/1000;

	if(tdiff > 0) {
		percent = Math.trunc(Math.round(100 * (row['full_price']['amount'] - row['current_price']['amount']) / row['full_price']['amount']));
		price = row['current_price']['amount'] + '<br><s>' + row['full_price']['amount'] + '</s><br>(' + percent + '% off)'
	} else {
		price = row['full_price']['amount'];
	}

	return price;
}

// Unfortunately this leads to confusion unless we let the user know the full and current price.
// We'll do that in the formatter but we'll sort based off of the current price.  Now the user
// will know how much they could've saved for an expired sale :'-( Sorry ya'll!  My JS isn't
// strong!
function priceSorter(a, b, rowA, rowB) {
	if(a['amount'] > b['amount'])
		return 1;
	if(a['amount'] < b['amount'])
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
				value['steam_percent'] * 100 + '% of ' + value['steam_count'] + ' users gave a ' +
				value['review_text'] + ' rating.' + '">' + Math.trunc(value['steam_percent'] * 100) + '%</p>';

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

function availabilityFormatter(value, row, index) {
	if(value.length == 0)
		return null;

	delivery_methods = row['delivery_methods'];
	platforms = row['platforms'];

	var retVal = '';

	for(i=0; i<row['delivery_methods'].length; i++) {
		var dm = row['delivery_methods'][i];

		retVal += '<div class="availability-section">\n';
		switch(dm) {
			case 'audio-download':
				retVal += '<i class="hb hb-audio" title="Audio download"></i>&nbsp;|&nbsp;';
				break;
			case 'download':
				/* retVal += '\t<div class="platform download">\n' +
					'\t\t<i class="hb hb-drmfree" title="DRM-free download"></i>\n' +
					'\t</div>\n'; */
				retVal += '<i class="hb hb-drmfree" title="DRM-free download"></i>&nbsp;|&nbsp;';
				break;
			case 'other-key':
				retVal += '<i class="hb hb-key" title="Key"></i>&nbsp;|&nbsp;';
				break;
			// Similar to "default" but we end it here.
			case 'android':
				retVal += '<i class="hb hb-' + dm + '" title="' + dm[0].toUpperCase() + dm.slice(1) + '"></i>\n</div><br>\n';
				continue;
				break;
			default:
				retVal += '<i class="hb hb-' + dm + '" title="' + dm[0].toUpperCase() + dm.slice(1) + '"></i>&nbsp;|&nbsp;';
				break;
		}

		// Now we process platforms
		for(j=0; j<row['platforms'].length; j++) {
			var platform = row['platforms'][j];

			// gog doesn't do vive or oculus
			if(dm == 'gog') {
				// We can't do "str" in "array" for some reason but we can do this.
				// Basically if we find this we skip
				if(['vive', 'oculus-rift'].indexOf(platform) > -1) {
					continue;
				}
			}

			// Audio only has specific file types
			if(dm == 'audio-download') {
				// Here if we can't find anything outside of this we skip
				if(['mp3','wav'].indexOf(platform) == -1) {
					continue;
				}
			}

			if(['mp3','wav'].indexOf(platform) > -1) {
				if(['audio-download'].indexOf(dm) == -1) {
					continue;
				}
			}

			// Android only does android
			if(platform == 'android') {
				continue;
			}

			switch(platform) {
				// Weird stuff
				case 'mac':
					retVal += '<i class="hb hb-osx" title="Mac"></i>';
					break;
				case 'oculus-rift':
					retVal += '<i class="hb hb-oculus" title="Oculus Rift"></i>';
					break;
				// file types
				case 'wav':
					retVal += '<i class="hb hb-file-audio-o" title="' + platform.toUpperCase() + '"></i>';
					break;
				case 'mp3':
					retVal += '<i class="hb hb-file-' + platform + '" title="' + platform.toUpperCase() + '"></i>';
					break;
				default:
					retVal += '<i class="hb hb-' + platform + '" title="' + platform[0].toUpperCase() + platform.slice(1) + '"></i>';
					break;
			}
			// retVal += '&nbsp;'
			// retVal += '\t</ul>\n';
		}
		retVal += '</div><br>\n';
	}

	return retVal;
}

function rowStyle(row, index) {
	// If there's no sale then success
	if(row['sale_end'] == null) {
		style = "table-success";
	} else {
		var endDate = new Date(row['sale_end'] * 1000);
		var endTime = endDate.getTime();

		// This can be negative meaning the sale has expired.
		// We divice by 1000 to get seconds.
		var tdiff = (endTime-nowTime)/1000;

		// Let's get get the obvious ones out of the way
		if(tdiff < 0) {
			style = "table-secondary"; // gray
		} else if(tdiff < 3600) {
			style = "table-danger"; // red
		} else if(tdiff <= 86400 ) {
			style = "table-warning"; // yellow
		} else {
			style = "table-success"; // green
		}
	}

	return { classes: style }
}

function onSaleFormatter(value, row, index) {
	return value;
}

$('#table').bootstrapTable({
	url: 'hb-sales.json',
	rowStyle: rowStyle,

	// data: rawJsonData, // Contains total, rows - doesn't seem to work - works when pulled from url though :-/
	classes: "table table-dark",
	// classes: "table table-hover table-dark glyphicon",
	// data: jsonData,
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
			field: 'onsale',
			title: 'On Sale?',
			sortable: true,
			searchable: true,
			filterControl: 'input',
		}, {
			field: 'delivery_methods',
			formatter: availabilityFormatter,
			title: 'Provider/Platforms/Format',
			filterControl: 'input',
		}, {
			field: 'user_rating',
			title: 'User rating',
			sortable: true,
			searchable: true,
			filterControl: 'input',
			formatter: userRatingFormatter,
			sorter: userRatingSorter,
		}, {
			field: 'handheld_friendly',
			title: 'Handheld Friendly',
			sortable: true,
			searchable: true,
			filterControl: 'input',
	}], // Close columns
}); // Close table
