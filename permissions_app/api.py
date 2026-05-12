import frappe

# El decorador whitelist hace que esta función sea visible desde el Javascript (navegador)
@frappe.whitelist()
def heredar_permisos_rol(role_name, role_parent):
    """
    Recibe el nombre del rol hijo y el nombre del rol padre para copiar permisos manualmente.
    """
    # Validación de seguridad
    if not role_name or not role_parent:
        return "Faltan parámetros"

    # Definición de campos a copiar (igual que en permissions.py)
    fields = ["parent", "permlevel", "read", "write", "create", "delete", 
              "submit", "cancel", "amend", "report", "export", "import", 
              "print", "email", "share"]
              
    # Buscamos permisos del padre (priorizando Custom)
    custom_perms = frappe.get_all("Custom DocPerm", filters={"role": role_parent}, fields=fields)
    
    if not custom_perms:
        custom_perms = frappe.get_all("DocPerm", filters={"role": role_parent}, fields=fields)

    count = 0 # Contador para informar al usuario cuántos permisos se crearon
    for perm in custom_perms:
        doctype_nombre = perm.get("parent")
        
        # Validación de duplicidad
        if not frappe.db.exists("Custom DocPerm", {"parent": doctype_nombre, "role": role_name, "permlevel": perm.get("permlevel", 0)}):
            # Creación e inserción del permiso
            new_perm = frappe.get_doc({
                "doctype": "Custom DocPerm",
                "parent": doctype_nombre,
                "parenttype": "DocType",
                "parentfield": "permissions",
                "role": role_name,
                **{k: v for k, v in perm.items() if k not in ['parent', 'name']}
            })
            new_perm.insert(ignore_permissions=True)
            count += 1
    
    # Forzar el guardado en la base de datos para que los cambios sean inmediatos
    frappe.db.commit()
    
    # Enviar un mensaje de éxito que el JS mostrará en pantalla
    return f"Heredados: {count} permisos de '{role_parent}'"