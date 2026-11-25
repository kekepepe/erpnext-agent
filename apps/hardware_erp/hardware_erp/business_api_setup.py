"""Schema setup for the W6 Business API v1 adapter inside hardware_erp."""

BUSINESS_DOCTYPES = ("Purchase Receipt", "Delivery Note")
IDEMPOTENCY_TABLE = "hardware_erp_business_idempotency"
AUDIT_TABLE = "hardware_erp_business_audit"


def ensure_tables():
    import frappe

    frappe.db.sql_ddl(
        f"""
        CREATE TABLE IF NOT EXISTS `{IDEMPOTENCY_TABLE}` (
            `operator` VARCHAR(140) NOT NULL,
            `operation` VARCHAR(32) NOT NULL,
            `target_id` VARCHAR(140) NOT NULL,
            `idempotency_key` VARCHAR(128) NOT NULL,
            `request_digest` CHAR(64) NOT NULL,
            `response_status` INT NOT NULL,
            `response_json` LONGTEXT NOT NULL,
            `created_at` DATETIME(6) NOT NULL,
            PRIMARY KEY (`operator`, `operation`, `target_id`, `idempotency_key`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )
    frappe.db.sql_ddl(
        f"""
        CREATE TABLE IF NOT EXISTS `{AUDIT_TABLE}` (
            `id` BIGINT NOT NULL AUTO_INCREMENT,
            `operator` VARCHAR(140) NOT NULL,
            `created_at` DATETIME(6) NOT NULL,
            `operation` VARCHAR(32) NOT NULL,
            `doctype` VARCHAR(64) NOT NULL,
            `doc_id` VARCHAR(140) NOT NULL,
            `http_status` INT NOT NULL,
            `result_code` VARCHAR(64) NOT NULL,
            PRIMARY KEY (`id`),
            KEY `idx_business_audit_operator_time` (`operator`, `created_at`),
            KEY `idx_business_audit_doc` (`doctype`, `doc_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )


def ensure_custom_fields():
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

    revision_field = {
        "fieldname": "custom_w6_revision",
        "label": "W6草稿版本",
        "fieldtype": "Int",
        "default": "0",
        "hidden": 1,
        "read_only": 1,
        "no_copy": 1,
        "insert_after": "naming_series",
    }
    create_custom_fields({
        doctype: [dict(revision_field)] for doctype in BUSINESS_DOCTYPES
    })


def configure():
    from hardware_erp.view_presets import ensure_preset_table, seed_default_presets

    ensure_custom_fields()
    ensure_tables()
    ensure_preset_table()
    seed_default_presets()
