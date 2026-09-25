"""Read-only discovery of the installed game's reflected SHiFT interface."""
def probe():
    import unrealsdk
    results = []
    for cls in unrealsdk.find_all("Class"):
        name = str(cls.Name)
        if not any(word in name.lower() for word in ("shift", "social", "friend", "online", "cohtml", "coherent", "uisystem", "uiview", "inputrouter", "inputmanager", "viewportclient")):
            continue
        fields = []
        for field in cls._fields():
            label = str(field.Name)
            if True:
                fields.append({"name": label, "type": str(field.Class.Name),
                               "args": [str(p.Name) for p in field._properties()] if hasattr(field, "_properties") else []})
        if True:
            try:
                live = [obj for obj in unrealsdk.find_all(cls, exact=False) if "Default__" not in obj._path_name()][:8]
                instances = [obj._path_name() for obj in live]
                properties = []
                for prop in cls._properties():
                    key = str(prop.Name)
                    values = []
                    if not any(word in key.lower() for word in ("token", "password", "credential", "ticket", "secret")):
                        for obj in live[:2]:
                            try:
                                values.append(str(getattr(obj, key))[:180])
                            except Exception as exc:
                                values.append(type(exc).__name__)
                    properties.append({"name": key, "type": str(prop.Class.Name), "values": values})
            except Exception as exc:
                instances = [repr(exc)]
                properties = []
            results.append({"class": cls._path_name(), "fields": fields, "instances": instances, "properties": properties})
    return {"ok": True, "classes": results}
