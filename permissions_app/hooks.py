from . import __version__ as app_version

app_name = "permissions_app"
app_title = "Permissions App"
app_publisher = "Jesus T."
app_description = "App dedicada a la heredacion de permisos"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "jesus22torrealba@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/permissions_app/css/permissions_app.css"
# app_include_js = "/assets/permissions_app/js/permissions_app.js"

# include js, css files in header of web template
# web_include_css = "/assets/permissions_app/css/permissions_app.css"
# web_include_js = "/assets/permissions_app/js/permissions_app.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "permissions_app/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {"Role" : "public/js/role_form.js"}
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

# Installation
# ------------

# before_install = "permissions_app.install.before_install"
# after_install = "permissions_app.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "permissions_app.uninstall.before_uninstall"
# after_uninstall = "permissions_app.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "permissions_app.notifications.get_notification_config"

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
	"Role": {
		"after_insert": "permissions_app.permissions.heredar_al_insertar"
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
#	"all": [
#		"permissions_app.tasks.all"
#	],
#	"daily": [
#		"permissions_app.tasks.daily"
#	],
#	"hourly": [
#		"permissions_app.tasks.hourly"
#	],
#	"weekly": [
#		"permissions_app.tasks.weekly"
#	]
#	"monthly": [
#		"permissions_app.tasks.monthly"
#	]
# }

# Testing
# -------

# before_tests = "permissions_app.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "permissions_app.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "permissions_app.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Request Events
# ----------------
# before_request = ["permissions_app.utils.before_request"]
# after_request = ["permissions_app.utils.after_request"]

# Job Events
# ----------
# before_job = ["permissions_app.utils.before_job"]
# after_job = ["permissions_app.utils.after_job"]

# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"permissions_app.auth.validate"
# ]

