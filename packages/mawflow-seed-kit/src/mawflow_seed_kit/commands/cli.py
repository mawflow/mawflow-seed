from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable
from importlib.metadata import version

from mawflow_seed_kit import export_agent_context, inspect_agent_readiness, render_agent_context
from .project_init import ProjectInitConfig, ProjectInitError
from .project_contract import project_doctor, project_migration
from .project_components import (
    component_apply,
    component_init,
    component_inspect,
    component_remove,
    component_source_bind,
    component_source_unbind,
    component_state,
)
from .project_seedization import init_or_seed_project
from .project_topology import (
    apply_saved_topology_plan,
    finish_topology_plan,
    hydrate_project,
    inspect_project_sources,
    plan_code_source_binding,
    plan_code_source_remove,
    plan_code_source_unbind,
    plan_code_source_upsert,
    plan_source_registry_consolidation,
    plan_subproject_remove,
    plan_subproject_upsert,
    save_topology_plan,
)
from .template_sources import DEFAULT_PACKAGE_INDEX_URL, DEFAULT_TEMPLATE_PACKAGE
from .template_drift import TemplateDriftConfig, TemplateDriftError, plan_template_drift


def _json_print(payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mawflow", description="Seed project tools. Daily commands work offline without an account.")
    parser.add_argument("--version", action="version", version=version("mawflow-seed-kit"))
    parser.add_argument("-C", "--workdir", default="")
    sub = parser.add_subparsers(dest="area", required=True)
    project = sub.add_parser(
        "project",
        help="Initialize MAWflow projects with 'mawflow project init'.",
        description="Initialize and inspect MAWflow projects.",
    )
    project_sub = project.add_subparsers(dest="command")
    project_init = project_sub.add_parser(
        "init",
        help="Initialize a new directory or Seed-enable the current Git repository.",
    )
    project_init.add_argument(
        "name",
        nargs="?",
        default="",
        help="Optional project name. Omit it to initialize the current directory.",
    )
    project_init.add_argument(
        "--root",
        default="",
        help="Project root. Defaults to the current directory when name is omitted.",
    )
    project_init.add_argument(
        "--profile",
        choices=["blank", "minimal", "service", "web-api"],
        default="",
        help="Defaults to blank. Legacy profiles remain aliases and no longer create components.",
    )
    project_init.add_argument("--source", choices=["package", "github", "gitee", "git", "local"], default="package")
    project_init.add_argument("--index-url", default=DEFAULT_PACKAGE_INDEX_URL)
    project_init.add_argument("--template", default=DEFAULT_TEMPLATE_PACKAGE)
    project_init.add_argument("--template-version", default="")
    project_init.add_argument("--repo", default="")
    project_init.add_argument("--ref", default="")
    project_init.add_argument("--path", default="")
    project_init.add_argument("--target-dir", default="")
    project_init.add_argument("--plan", action="store_true", help="Resolve and verify the source without writing files.")
    project_init.add_argument("--execute", action="store_true", help="Apply a persisted existing-repository preview.")
    project_init.add_argument("--confirm", default="", help="Exact confirmation from the existing-repository preview.")
    project_init.add_argument("--plan-file", default="", help="Optional private migration plan path.")
    project_init.add_argument("--git-init", dest="git_init", action="store_true", default=True)
    project_init.add_argument("--no-git-init", dest="git_init", action="store_false")
    project_drift = project_sub.add_parser("drift", help="Plan an incremental Seed template upgrade.")
    project_drift.add_argument("--root", default=".", help="Existing project root. Defaults to the current directory.")
    project_drift.add_argument("--applied-version", default="", help="Override the recorded applied commit.")
    project_drift.add_argument("--target-version", default="", help="Override the configured target ref.")
    project_drift.add_argument("--git-url", default="", help="Override the configured Seed Git URL.")
    project_drift.add_argument("--max-commits", type=int, default=20, help="Maximum commit summaries to include.")
    project_doctor_parser = project_sub.add_parser("doctor", help="Compile and validate Seed Contract v2.")
    project_doctor_parser.add_argument("--root", default=".")
    adopt = project_sub.add_parser(
        "adopt",
        help="Compatibility alias for 'mawflow project init --root ...'.",
    )
    adopt.add_argument("--root", default=".")
    adopt.add_argument("--profile", choices=["blank", "minimal", "service", "web-api"], default="")
    adopt.add_argument("--execute", action="store_true")
    adopt.add_argument("--confirm", default="")
    adopt.add_argument("--plan-file", default="")
    agent_doctor = project_sub.add_parser("agents", help="Check portable Agent entry readiness without running an Agent.")
    agent_doctor.add_argument("--root", default=".")
    agent_context = project_sub.add_parser("context", help="Export bounded shared project context for local or web Agents.")
    agent_context.add_argument("--root", default=".")
    agent_context.add_argument("--agent", default="")
    agent_context.add_argument("--module", default="")
    agent_context.add_argument("--task-kind", choices=["development", "review", "delivery", "governance"], default="development")
    agent_context.add_argument("--max-chars", type=int, default=12000)
    agent_context.add_argument("--format", choices=["json", "markdown"], default="json")
    upgrade_project = project_sub.add_parser(
        "upgrade", help="Preview or apply a one-time Seed Contract v2 migration."
    )
    upgrade_project.add_argument("--root", default=".")
    upgrade_project.add_argument("--profile", choices=["blank", "minimal", "service", "web-api"], default="blank")
    upgrade_project.add_argument("--execute", action="store_true")
    upgrade_project.add_argument("--confirm", default="")
    upgrade_project.add_argument("--plan-file", default="")
    upgrade_project.add_argument("--template", action="store_true", help="Update package-managed Seed files using a three-way comparison.")
    upgrade_project.add_argument("--rollback", default="", metavar="RECOVERY_KEY", help="Restore a Seed template update offline.")

    hydrate_project_parser = project_sub.add_parser(
        "hydrate", help="Clone and bind missing external code sources on this device."
    )
    hydrate_project_parser.add_argument("--root", default=".")
    hydrate_project_parser.add_argument("--source", action="append", default=[])
    hydrate_project_parser.add_argument("--git-access-profile", default="")
    hydrate_project_parser.add_argument("--execute", action="store_true")

    project_sources = project_sub.add_parser(
        "sources", help="Inspect or consolidate external source declarations."
    )
    project_sources_sub = project_sources.add_subparsers(dest="source_command", required=True)
    project_sources_inspect = project_sources_sub.add_parser("inspect")
    project_sources_inspect.add_argument("--root", default=".")
    project_sources_consolidate = project_sources_sub.add_parser(
        "consolidate", help="Consolidate compatible v2.4 component source declarations."
    )
    project_sources_consolidate.add_argument("--root", default=".")
    project_sources_consolidate.add_argument("--execute", action="store_true")
    project_sources_consolidate.add_argument("--confirm", default="")
    project_sources_consolidate.add_argument("--plan-file", default="")

    subproject = sub.add_parser("subproject", help="Manage independent subprojects inside one MAWflow project.")
    subproject_sub = subproject.add_subparsers(dest="command", required=True)
    subproject_add = subproject_sub.add_parser("add")
    subproject_add.add_argument("key")
    subproject_add.add_argument("--name", required=True)
    subproject_add.add_argument("--description", default="")
    subproject_add.add_argument("--status", choices=["active", "archived"], default="active")
    subproject_add.add_argument("--grouping-basis", choices=["standalone", "same_customer", "same_deployment", "same_product", "other"], default="standalone")
    subproject_add.add_argument("--customer-ref", default="")
    subproject_add.add_argument("--deployment-group-ref", default="")
    subproject_add.add_argument("--root", default=".")
    subproject_add.add_argument("--plan", action="store_true")
    subproject_add.add_argument("--plan-file", default="")
    subproject_remove = subproject_sub.add_parser("remove")
    subproject_remove.add_argument("key")
    subproject_remove.add_argument("--root", default=".")
    subproject_remove.add_argument("--plan", action="store_true")
    subproject_remove.add_argument("--plan-file", default="")
    subproject_list = subproject_sub.add_parser("list")
    subproject_list.add_argument("--root", default=".")
    subproject_apply = subproject_sub.add_parser("apply")
    subproject_apply.add_argument("--root", default=".")
    subproject_apply.add_argument("--plan-file", default="")
    subproject_apply.add_argument("--confirm", required=True)

    code_source = sub.add_parser("code-source", help="Manage Git repositories shared by multiple components.")
    code_source_sub = code_source.add_subparsers(dest="command", required=True)
    code_source_add = code_source_sub.add_parser("add")
    code_source_add.add_argument("key")
    code_source_add.add_argument("--repository-url", required=True)
    code_source_add.add_argument("--name", default="")
    code_source_add.add_argument("--default-branch", default="")
    code_source_add.add_argument("--visibility", choices=["private", "internal", "public"], default="private")
    code_source_add.add_argument("--credential-requirement-ref", default="")
    code_source_add.add_argument("--root", default=".")
    code_source_add.add_argument("--plan", action="store_true")
    code_source_add.add_argument("--plan-file", default="")
    code_source_bind = code_source_sub.add_parser("bind")
    code_source_bind.add_argument("key")
    code_source_bind.add_argument("directory")
    code_source_bind.add_argument("--origin", choices=["existing_directory", "managed_clone"], default="existing_directory")
    code_source_bind.add_argument("--git-access-profile", default="")
    code_source_bind.add_argument("--root", default=".")
    code_source_bind.add_argument("--plan", action="store_true")
    code_source_bind.add_argument("--plan-file", default="")
    for code_source_command in ("unbind", "remove"):
        command_parser = code_source_sub.add_parser(code_source_command)
        command_parser.add_argument("key")
        command_parser.add_argument("--root", default=".")
        command_parser.add_argument("--plan", action="store_true")
        command_parser.add_argument("--plan-file", default="")
    code_source_list = code_source_sub.add_parser("list")
    code_source_list.add_argument("--root", default=".")
    code_source_apply = code_source_sub.add_parser("apply")
    code_source_apply.add_argument("--root", default=".")
    code_source_apply.add_argument("--plan-file", default="")
    code_source_apply.add_argument("--confirm", required=True)

    component = sub.add_parser(
        "component",
        help="Create, adopt, inspect, enable, and disable project components.",
    )
    component_sub = component.add_subparsers(dest="command")

    def add_component_write_args(command_parser: argparse.ArgumentParser) -> None:
        command_parser.add_argument("--root", default=".")
        command_parser.add_argument("--plan", action="store_true", help="Save and print the exact plan without applying it.")
        command_parser.add_argument("--plan-file", default="", help="Private plan path; defaults to .local/.maw/component-plan.json.")

    def add_component_init_args(command_parser: argparse.ArgumentParser) -> None:
        command_parser.add_argument("key")
        command_parser.add_argument("--type", dest="component_type", default="custom")
        command_parser.add_argument("--name", default="")
        command_parser.add_argument("--path", default="")
        command_parser.add_argument("--subproject", default="default")
        command_parser.add_argument("--source-root", default="")
        command_parser.add_argument(
            "--source-mode",
            choices=["embedded", "external_git", "external-git"],
            default="embedded",
        )
        command_parser.add_argument("--repository-url", default="")
        command_parser.add_argument("--repository-ref", default="")
        command_parser.add_argument("--repository-subpath", default="")
        command_parser.add_argument("--default-branch", default="")
        command_parser.add_argument("--source-directory", default="")
        command_parser.add_argument(
            "--source-origin",
            choices=["existing_directory", "managed_clone"],
            default="existing_directory",
        )
        command_parser.add_argument("--git-access-profile", default="")
        command_parser.add_argument("--enable", action="store_true")
        add_component_write_args(command_parser)

    component_init_parser = component_sub.add_parser("init", help="Create a component boundary; default disabled.")
    add_component_init_args(component_init_parser)
    component_add_parser = component_sub.add_parser(
        "add",
        help="Guided-compatible component entry with embedded or external Git source parameters.",
    )
    add_component_init_args(component_add_parser)

    component_adopt_parser = component_sub.add_parser("adopt", help="Adopt an existing directory without overwriting source files.")
    component_adopt_parser.add_argument("path")
    component_adopt_parser.add_argument("--key", required=True)
    component_adopt_parser.add_argument("--type", dest="component_type", default="custom")
    component_adopt_parser.add_argument("--name", default="")
    component_adopt_parser.add_argument("--enable", action="store_true")
    add_component_write_args(component_adopt_parser)

    for action in ("enable", "disable"):
        action_parser = component_sub.add_parser(action, help=f"{action.title()} a component without deleting its directory.")
        action_parser.add_argument("key")
        add_component_write_args(action_parser)

    component_source_parser = component_sub.add_parser(
        "source", help="Bind or unbind this device's external Git source directory."
    )
    component_source_sub = component_source_parser.add_subparsers(dest="source_command", required=True)
    component_source_bind_parser = component_source_sub.add_parser("bind", help="Bind an existing external Git root.")
    component_source_bind_parser.add_argument("key")
    component_source_bind_parser.add_argument("directory")
    component_source_bind_parser.add_argument("--git-access-profile", default="")
    component_source_bind_parser.add_argument(
        "--origin", choices=["existing_directory", "managed_clone"], default="existing_directory"
    )
    add_component_write_args(component_source_bind_parser)
    component_source_unbind_parser = component_source_sub.add_parser(
        "unbind", help="Remove only this device's binding; retain the source directory."
    )
    component_source_unbind_parser.add_argument("key")
    add_component_write_args(component_source_unbind_parser)

    component_remove_parser = component_sub.add_parser(
        "remove", help="Unregister a component and clean safe references; retain source directories."
    )
    component_remove_parser.add_argument("key")
    add_component_write_args(component_remove_parser)

    component_apply_parser = component_sub.add_parser("apply", help="Apply a previously saved component plan.")
    component_apply_parser.add_argument("--root", default=".")
    component_apply_parser.add_argument("--execute", action="store_true", required=True)
    component_apply_parser.add_argument("--plan-file", default="")
    component_apply_parser.add_argument("--confirm", required=True)

    component_list_parser = component_sub.add_parser("list", help="List registered components and health status.")
    component_list_parser.add_argument("--root", default=".")
    component_show_parser = component_sub.add_parser("show", help="Show one registered component.")
    component_show_parser.add_argument("key")
    component_show_parser.add_argument("--root", default=".")
    component_doctor_parser = component_sub.add_parser("doctor", help="Check component directory and descriptor consistency.")
    component_doctor_parser.add_argument("key", nargs="?", default="")
    component_doctor_parser.add_argument("--root", default=".")

    sub.add_parser(
        "capabilities",
        help="Print Seed Kit version and machine-readable project capabilities.",
    )

    verify = project_sub.add_parser("verify", help="Preview registered verification commands, then confirm the exact plan.")
    verify.add_argument("--root", default=".")
    verify.add_argument("--component", action="append", default=[])
    verify.add_argument("--suite", choices=["all", "test", "lint", "typecheck", "build"], default="all")
    verify.add_argument("--execute", action="store_true")
    verify.add_argument("--confirm", default="")
    verify.add_argument("--task-key", default="")
    verify.add_argument("--task-version", default="")
    return parser


def main(argv: list[str] | None = None, *, authorize_upgrade: Callable[[], object] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.workdir:
        os.chdir(Path(args.workdir).expanduser())
    if args.area == "capabilities":
        _json_print({"schema": "mawflow.seed_cli.capabilities.v1", "version": version("mawflow-seed-kit"), "profile": "seed-cli", "host_required": False, "daily_login_required": False, "capabilities": ["project.init.current_directory", "project.init.existing_git", "project.init.idempotent", "component.lifecycle", "project.agent_context", "project.upgrade.online_account_required"]})
        return 0
    if args.area == "project" and args.command == "upgrade" and args.execute and not args.rollback:
        try:
            if authorize_upgrade is None:
                raise ValueError("upgrade_online_login_required: use the official mawflow CLI")
            authorize_upgrade()
        except (OSError, ValueError) as exc:
            _json_print({"status": "blocked", "error": str(exc), "daily_commands_available": True})
            return 1
    if args.area in {"subproject", "code-source"}:
        try:
            root = Path(args.root)
            plan_file = Path(args.plan_file) if getattr(args, "plan_file", "") else None
            if args.command == "apply":
                result = apply_saved_topology_plan(
                    root, confirmation=args.confirm, plan_file=plan_file
                )
            elif args.area == "subproject" and args.command == "list":
                inspection = inspect_project_sources(root)
                result = {
                    "schema": "mawflow.subproject_inspection.v1",
                    "status": inspection["status"],
                    "items": inspection["subprojects"],
                }
            elif args.area == "subproject" and args.command == "add":
                public, private = plan_subproject_upsert(
                    root,
                    key=args.key,
                    name=args.name,
                    description=args.description,
                    status=args.status,
                    grouping_basis=args.grouping_basis,
                    customer_ref=args.customer_ref,
                    deployment_group_ref=args.deployment_group_ref,
                )
                result = finish_topology_plan(
                    root, public, private, preview_only=args.plan, plan_file=plan_file
                )
            elif args.area == "subproject" and args.command == "remove":
                public, private = plan_subproject_remove(root, key=args.key)
                result = finish_topology_plan(
                    root, public, private, preview_only=args.plan, plan_file=plan_file
                )
            elif args.area == "code-source" and args.command == "list":
                result = inspect_project_sources(root)
            elif args.area == "code-source" and args.command == "add":
                public, private = plan_code_source_upsert(
                    root,
                    key=args.key,
                    repository_url=args.repository_url,
                    name=args.name,
                    default_branch=args.default_branch,
                    visibility=args.visibility,
                    credential_requirement_ref=args.credential_requirement_ref,
                )
                result = finish_topology_plan(
                    root, public, private, preview_only=args.plan, plan_file=plan_file
                )
            elif args.area == "code-source" and args.command == "bind":
                public, private = plan_code_source_binding(
                    root,
                    key=args.key,
                    directory_path=Path(args.directory),
                    git_access_profile_ref=args.git_access_profile,
                    origin=args.origin,
                )
                result = finish_topology_plan(
                    root, public, private, preview_only=args.plan, plan_file=plan_file
                )
            elif args.area == "code-source" and args.command == "unbind":
                public, private = plan_code_source_unbind(root, key=args.key)
                result = finish_topology_plan(
                    root, public, private, preview_only=args.plan, plan_file=plan_file
                )
            elif args.area == "code-source" and args.command == "remove":
                public, private = plan_code_source_remove(root, key=args.key)
                result = finish_topology_plan(
                    root, public, private, preview_only=args.plan, plan_file=plan_file
                )
            else:
                parser.print_help()
                return 2
            _json_print(result)
            return 0 if result.get("status") not in {"failed", "blocked", "needs_attention"} else 1
        except (OSError, ValueError) as exc:
            _json_print(
                {
                    "schema": "mawflow.project_topology_result.v1",
                    "status": "failed",
                    "error": str(exc),
                }
            )
            return 1
    if args.area == "component":
        try:
            if args.command in {"init", "add"}:
                result = component_init(
                    Path(args.root),
                    key=args.key,
                    component_type=args.component_type,
                    name=args.name,
                    path=args.path,
                    subproject_ref=args.subproject,
                    source_root=args.source_root,
                    source_mode=args.source_mode.replace("-", "_"),
                    repository_url=args.repository_url,
                    repository_ref=args.repository_ref,
                    repository_subpath=args.repository_subpath,
                    default_branch=args.default_branch,
                    source_directory=Path(args.source_directory) if args.source_directory else None,
                    source_origin=args.source_origin,
                    git_access_profile_ref=args.git_access_profile,
                    enabled=args.enable,
                    preview_only=args.plan,
                    plan_file=Path(args.plan_file) if args.plan_file else None,
                )
            elif args.command == "adopt":
                result = component_init(
                    Path(args.root),
                    key=args.key,
                    component_type=args.component_type,
                    name=args.name,
                    path=args.path,
                    enabled=args.enable,
                    adopt=True,
                    preview_only=args.plan,
                    plan_file=Path(args.plan_file) if args.plan_file else None,
                )
            elif args.command in {"enable", "disable"}:
                result = component_state(
                    Path(args.root),
                    key=args.key,
                    enabled=args.command == "enable",
                    preview_only=args.plan,
                    plan_file=Path(args.plan_file) if args.plan_file else None,
                )
            elif args.command == "source" and args.source_command == "bind":
                result = component_source_bind(
                    Path(args.root),
                    key=args.key,
                    directory_path=Path(args.directory),
                    git_access_profile_ref=args.git_access_profile,
                    origin=args.origin,
                    preview_only=args.plan,
                    plan_file=Path(args.plan_file) if args.plan_file else None,
                )
            elif args.command == "source" and args.source_command == "unbind":
                result = component_source_unbind(
                    Path(args.root),
                    key=args.key,
                    preview_only=args.plan,
                    plan_file=Path(args.plan_file) if args.plan_file else None,
                )
            elif args.command == "remove":
                result = component_remove(
                    Path(args.root),
                    key=args.key,
                    preview_only=args.plan,
                    plan_file=Path(args.plan_file) if args.plan_file else None,
                )
            elif args.command == "apply":
                result = component_apply(
                    Path(args.root),
                    confirmation=args.confirm,
                    plan_file=Path(args.plan_file) if args.plan_file else None,
                )
            elif args.command == "list":
                result = component_inspect(Path(args.root))
            elif args.command in {"show", "doctor"}:
                result = component_inspect(Path(args.root), args.key or None)
            else:
                parser.print_help()
                return 2
            _json_print(result)
            if args.command == "doctor" and result.get("status") != "ready":
                return 1
            return 0
        except (OSError, ValueError) as exc:
            _json_print(
                {
                    "schema": "mawflow.host_component_result.v1",
                    "status": "failed",
                    "error": str(exc),
                }
            )
            return 1
    if args.area == "project":
        if args.command == "verify":
            from .verification import verify_project
            try:
                result = verify_project(args.root, execute=args.execute, confirmation=args.confirm,
                    component=args.component, suite=args.suite, task_key=args.task_key, task_version=args.task_version)
                _json_print(result)
                return 0 if result["status"] in {"planned", "success"} else 1
            except (OSError, ValueError) as exc:
                _json_print({"status": "blocked", "error": str(exc)})
                return 1
        if args.command == "hydrate":
            try:
                result = hydrate_project(
                    Path(args.root),
                    execute=args.execute,
                    source_keys=list(args.source or []),
                    git_access_profile_ref=args.git_access_profile,
                )
                _json_print(result)
                return 0 if result.get("status") not in {"failed", "blocked", "needs_attention"} else 1
            except (OSError, ValueError) as exc:
                _json_print(
                    {
                        "schema": "mawflow.project_hydration_result.v1",
                        "status": "failed",
                        "error": str(exc),
                    }
                )
                return 1
        if args.command == "sources":
            try:
                root = Path(args.root)
                if args.source_command == "inspect":
                    result = inspect_project_sources(root)
                elif args.source_command == "consolidate" and args.execute:
                    result = apply_saved_topology_plan(
                        root,
                        confirmation=args.confirm,
                        plan_file=Path(args.plan_file) if args.plan_file else None,
                    )
                elif args.source_command == "consolidate":
                    public, private = plan_source_registry_consolidation(root)
                    path = save_topology_plan(
                        root,
                        private,
                        Path(args.plan_file) if args.plan_file else None,
                    )
                    result = {**public, "status": "planned", "plan_file": str(path)}
                else:
                    parser.print_help()
                    return 2
                _json_print(result)
                return 0 if result.get("status") not in {"failed", "blocked"} else 1
            except (OSError, ValueError) as exc:
                _json_print(
                    {
                        "schema": "mawflow.project_source_registry_result.v1",
                        "status": "failed",
                        "error": str(exc),
                    }
                )
                return 1
        if args.command == "init":
            try:
                config = ProjectInitConfig(
                    name=args.name,
                    profile=args.profile,
                    source=args.source,
                    index_url=args.index_url,
                    template=args.template,
                    template_version=args.template_version,
                    repo=args.repo,
                    ref=args.ref,
                    path=args.path,
                    target_dir=args.target_dir,
                    git_init=args.git_init,
                    plan_only=args.plan,
                )
                result = init_or_seed_project(
                    config,
                    root=args.root,
                    execute=args.execute,
                    confirmation=args.confirm,
                    plan_file=Path(args.plan_file) if args.plan_file else None,
                )
                if (
                    result.get("status") == "previewed"
                    and not args.plan
                    and not args.execute
                    and sys.stdin.isatty()
                    and sys.stdout.isatty()
                ):
                    required = str(result.get("confirmation_required") or "")
                    writes = len(result.get("writes") or [])
                    deletes = len(result.get("deletes") or [])
                    print(
                        f"Existing Git repository: {writes} writes, {deletes} deletes.",
                        file=sys.stderr,
                    )
                    entered = input(f"Type {required} to apply, or press Enter to keep the preview: ")
                    if entered == required:
                        result = init_or_seed_project(
                            config,
                            root=args.root,
                            execute=True,
                            confirmation=entered,
                            plan_file=Path(args.plan_file) if args.plan_file else None,
                        )
                _json_print(result)
                return 0 if result.get("status") not in {"blocked", "needs_attention"} else 1
            except (OSError, ValueError, ProjectInitError) as exc:
                _json_print(
                    {
                        "schema": "mawflow.project_init.result.v3",
                        "status": "failed",
                        "error": str(exc),
                        "recovery": [
                            "Run git status --short and commit or stash existing changes.",
                            "Use a Git repository root for any directory that already contains project files.",
                            "Run mawflow capabilities to verify the installed CLI supports current-directory initialization.",
                        ],
                    }
                )
                return 1
        if args.command in {"agents", "context"}:
            try:
                if args.command == "agents":
                    result = inspect_agent_readiness(args.root)
                    _json_print(result)
                    return 0 if result["status"] == "ready" else 1
                result = export_agent_context(args.root, module_key=args.module, agent_name=args.agent, task_kind=args.task_kind, max_chars=args.max_chars)
                if args.format == "markdown":
                    print(render_agent_context(result))
                else:
                    _json_print(result)
                return 0
            except (OSError, ValueError) as exc:
                _json_print({"status": "failed", "error": str(exc), "message": "无法读取共享 Agent 上下文，请核对路径、模块与 Seed 版本。"})
                return 1
        if args.command == "doctor":
            try:
                result = project_doctor(Path(args.root))
                _json_print(result)
                return 0 if result.get("status") == "ready" else 1
            except (OSError, ValueError) as exc:
                _json_print({"schema": "mawflow.seed_project_definition.v2", "status": "failed", "error": str(exc)})
                return 1
        if args.command == "adopt":
            try:
                result = init_or_seed_project(
                    ProjectInitConfig(name="", profile=args.profile),
                    root=args.root,
                    execute=args.execute,
                    confirmation=args.confirm,
                    plan_file=Path(args.plan_file) if args.plan_file else None,
                )
                _json_print(result)
                return 0 if result.get("status") not in {"blocked", "needs_attention"} else 1
            except (OSError, ValueError, ProjectInitError) as exc:
                _json_print({"schema": "mawflow.project_init.result.v3", "status": "failed", "error": str(exc)})
                return 1
        if args.command == "upgrade":
            try:
                if args.template or args.rollback:
                    from .template_update import update_template
                    result = update_template(Path(args.root), execute=args.execute, confirmation=args.confirm, rollback=args.rollback)
                    _json_print(result)
                    return 1 if result["status"] == "blocked" else 0
                result = project_migration(
                    Path(args.root),
                    profile=args.profile,
                    execute=args.execute,
                    confirmation=args.confirm,
                    plan_file=Path(args.plan_file) if args.plan_file else None,
                )
                _json_print(result)
                return 0
            except (OSError, ValueError) as exc:
                _json_print({"schema": "mawflow.seed_migration_result.v2", "status": "failed", "error": str(exc)})
                return 1
        if args.command == "drift":
            try:
                result = plan_template_drift(
                    TemplateDriftConfig(
                        root=Path(args.root),
                        applied_version=args.applied_version,
                        target_version=args.target_version,
                        git_url=args.git_url,
                        max_commits=args.max_commits,
                    )
                )
                _json_print(result)
                return 1 if result["status"] in {"source_channel_unconfirmed", "baseline_invalid", "diverged"} else 0
            except TemplateDriftError as exc:
                _json_print({"schema": "mawflow.template_drift.plan.v2", "status": "failed", "error": str(exc)})
                return 1
    parser.error("unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
