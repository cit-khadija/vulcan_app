from . import __version__ as app_version

app_name = "vulcan_app"
app_title = "Vulcan App"
app_publisher = "Crafrt"
app_description = "Vulcan"
app_email = "craftinteractive.com"
app_license = "MIT"


fixtures = [
    {
        "dt":"Custom Field",
        "filters":[
            ['name','in',[
                #TODO: Get all other fields
                'Quotation Item-item_details',
                'Sales Order Item-item_details',
                'Quotation Item-door_no',
                'Sales Order Item-door_no',
                'Quotation-add_hardware_set',
                'Quotation-assign_item_details',
                'Quotation-section_break_waeqk',
                'Stock Entry-custom_work_order',
                'Stock Entry Detail-cwo_item'
            ]]
        ]
    }
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/vulcan_app/css/vulcan_app.css"
# app_include_js = "/assets/vulcan_app/js/vulcan_app.js"

# include js, css files in header of web template
# web_include_css = "/assets/vulcan_app/css/vulcan_app.css"
# web_include_js = "/assets/vulcan_app/js/vulcan_app.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "vulcan_app/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Sales Order" : "public/js/sales_order.js",
    "Quotation": "public/js/quotation.js",
    "Stock Entry": "public/js/stock_entry.js"
    }
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "vulcan_app.utils.jinja_methods",
#	"filters": "vulcan_app.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "vulcan_app.install.before_install"
# after_install = "vulcan_app.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "vulcan_app.uninstall.before_uninstall"
# after_uninstall = "vulcan_app.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "vulcan_app.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Stock Entry": {
        "on_submit":"vulcan_app.events.stock_entry.on_submit",
        "before_submit": "vulcan_app.events.stock_entry.before_submit",
        "on_cancel":"vulcan_app.events.stock_entry.on_cancel",
    }
}

# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
#	"all": [
#		"vulcan_app.tasks.all"
#	],
#	"daily": [
#		"vulcan_app.tasks.daily"
#	],
#	"hourly": [
#		"vulcan_app.tasks.hourly"
#	],
#	"weekly": [
#		"vulcan_app.tasks.weekly"
#	],
#	"monthly": [
#		"vulcan_app.tasks.monthly"
#	],
# }

# Testing
# -------

# before_tests = "vulcan_app.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "vulcan_app.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "vulcan_app.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["vulcan_app.utils.before_request"]
# after_request = ["vulcan_app.utils.after_request"]

# Job Events
# ----------
# before_job = ["vulcan_app.utils.before_job"]
# after_job = ["vulcan_app.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"vulcan_app.auth.validate"
# ]
