frappe.listview_settings['Custom Work Order'] = {
	add_fields: ["status"],
	get_indicator: function(doc) {
		let colors = {
			'Draft':'red',
			'Submitted':'blue',
			'Not Started':'blue',
			'In Process':'blue',
			'Completed':'green',
			'Stopped':'orange',
			'Closed':'green'
		};
		let status = doc.status;
		return [__(status), colors[status], 'status,=,'+status];
	},
};
