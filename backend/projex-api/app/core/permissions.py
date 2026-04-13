"""Permission constants and default role definitions for RBAC."""


# ── Permission strings ──────────────────────────────────────
class Permissions:
    # Spaces
    SPACE_CREATE = "space:create"
    SPACE_EDIT = "space:edit"
    SPACE_DELETE = "space:delete"
    SPACE_ARCHIVE = "space:archive"

    # Work Items
    ITEM_CREATE = "item:create"
    ITEM_EDIT = "item:edit"
    ITEM_DELETE = "item:delete"
    ITEM_ASSIGN = "item:assign"
    ITEM_TRANSITION = "item:transition"
    ITEM_COMMENT = "item:comment"

    # Sprints
    SPRINT_CREATE = "sprint:create"
    SPRINT_START = "sprint:start"
    SPRINT_CLOSE = "sprint:close"

    # Timesheets
    TIMESHEET_LOG = "timesheet:log"
    TIMESHEET_APPROVE = "timesheet:approve"
    TIMESHEET_EXPORT = "timesheet:export"

    # Admin
    ADMIN_USERS = "admin:users"
    ADMIN_ROLES = "admin:roles"
    ADMIN_SETTINGS = "admin:settings"

    # Budget
    BUDGET_CREATE = "budget:create"
    BUDGET_EDIT = "budget:edit"
    BUDGET_VIEW = "budget:view"

    # Wiki
    WIKI_CREATE = "wiki:create"
    WIKI_EDIT = "wiki:edit"


# ── All permissions (for admin role) ────────────────────────
ALL_PERMISSIONS = [
    v for k, v in vars(Permissions).items()
    if not k.startswith("_") and isinstance(v, str)
]


# ── Default role definitions ────────────────────────────────
DEFAULT_ROLES = {
    "admin": {
        "name": "admin",
        "description": "Full access to all features",
        "permissions": ALL_PERMISSIONS,
        "field_security": {},
        "is_system": True,
    },
    "member": {
        "name": "member",
        "description": "Standard team member with create/edit permissions",
        "permissions": [
            Permissions.SPACE_EDIT,
            Permissions.ITEM_CREATE,
            Permissions.ITEM_EDIT,
            Permissions.ITEM_ASSIGN,
            Permissions.ITEM_TRANSITION,
            Permissions.ITEM_COMMENT,
            Permissions.SPRINT_CREATE,
            Permissions.TIMESHEET_LOG,
            Permissions.BUDGET_VIEW,
            Permissions.WIKI_CREATE,
            Permissions.WIKI_EDIT,
        ],
        "field_security": {},
        "is_system": True,
    },
    "viewer": {
        "name": "viewer",
        "description": "Read-only access to spaces and items",
        "permissions": [
            Permissions.ITEM_COMMENT,
            Permissions.BUDGET_VIEW,
        ],
        "field_security": {
            "budget_amount": "hidden",
        },
        "is_system": True,
    },
    "guest": {
        "name": "guest",
        "description": "Limited access — can only view assigned items",
        "permissions": [
            Permissions.ITEM_COMMENT,
        ],
        "field_security": {
            "budget_amount": "hidden",
            "timesheet_rate": "hidden",
        },
        "is_system": True,
    },
}
