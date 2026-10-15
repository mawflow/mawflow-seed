"""Project-only read policy; Host/account operations remain with their owner."""


def readonly_allowed(args):
    if getattr(args, "execute", False):
        return False
    if args.area in {"version", "profile"}:
        return True
    area, command = args.area, getattr(args, "command", "")
    if area == "capabilities":
        return True
    if area == "project":
        return command in {"doctor", "agents", "context", "verify", "hydrate"} or (
            command == "sources" and args.source_command == "inspect")
    return (area == "component" and command in {"list", "show", "doctor"}) or (
        area in {"subproject", "code-source"} and command == "list")
