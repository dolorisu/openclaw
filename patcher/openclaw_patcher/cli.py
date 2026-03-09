"""
CLI interface for OpenClaw patcher
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import PatchEngine, PatchStatus
from .patches import ALL_PATCHES


def print_status(engine: PatchEngine, verbose: bool = False):
    """Print status of all patches"""
    print("\n📊 Patch Status:\n")
    
    statuses = engine.check_all()
    
    status_emoji = {
        PatchStatus.APPLIED: "✅",
        PatchStatus.NOT_APPLIED: "❌",
        PatchStatus.PARTIALLY_APPLIED: "⚠️ ",
        PatchStatus.FAILED: "💥",
        PatchStatus.CONFLICT: "🔥",
    }
    
    for name, status in statuses.items():
        patch = engine.get_patch(name)
        emoji = status_emoji.get(status, "❓")
        print(f"  {emoji} {name:20s} {status.value:20s}")
        
        if verbose and patch:
            print(f"      {patch.description}")
            if patch.dependencies:
                print(f"      Dependencies: {', '.join(patch.dependencies)}")
    
    print()


def cmd_status(args, engine: PatchEngine):
    """Show patch status"""
    print_status(engine, verbose=args.verbose)


def cmd_apply(args, engine: PatchEngine):
    """Apply patches"""
    
    if args.all:
        print("🚀 Applying all patches...\n")
        results = engine.apply_all(force=args.force)
        
        for name, result in results.items():
            status_emoji = "✅" if result.status == PatchStatus.APPLIED else "❌"
            print(f"{status_emoji} {name}: {result.message}")
        
        print()
        
        # Restart gateway if requested
        if args.restart:
            print("🔄 Restarting OpenClaw gateway...")
            if engine.restart_gateway():
                print("✅ Gateway restarted successfully")
            else:
                print("⚠️  Failed to restart gateway (you may need to restart manually)")
        
    else:
        # Apply specific patches
        patches_to_apply = args.patches or []
        
        if not patches_to_apply:
            print("❌ No patches specified. Use --all or specify patch names.")
            print(f"   Available patches: {', '.join(engine.patches.keys())}")
            return 1
        
        print(f"🚀 Applying patches: {', '.join(patches_to_apply)}\n")
        
        for name in patches_to_apply:
            if name not in engine.patches:
                print(f"❌ Unknown patch: {name}")
                continue
            
            result = engine.apply_patch(name, force=args.force)
            status_emoji = "✅" if result.status == PatchStatus.APPLIED else "❌"
            print(f"{status_emoji} {name}: {result.message}")
        
        print()
        
        # Restart gateway if requested
        if args.restart:
            print("🔄 Restarting OpenClaw gateway...")
            if engine.restart_gateway():
                print("✅ Gateway restarted successfully")
            else:
                print("⚠️  Failed to restart gateway")


def cmd_check(args, engine: PatchEngine):
    """Check specific patch"""
    name = args.patch
    
    if name not in engine.patches:
        print(f"❌ Unknown patch: {name}")
        return 1
    
    patch = engine.get_patch(name)
    status = engine.check_patch(name)
    
    print(f"\n📋 Patch: {name}")
    print(f"   Description: {patch.description}")
    print(f"   Status: {status.value}")
    
    if patch.dependencies:
        print(f"   Dependencies: {', '.join(patch.dependencies)}")
        print()
        print("   Dependency status:")
        for dep in patch.dependencies:
            dep_status = engine.check_patch(dep)
            emoji = "✅" if dep_status == PatchStatus.APPLIED else "❌"
            print(f"     {emoji} {dep}: {dep_status.value}")
    
    print()


def cmd_rollback(args, engine: PatchEngine):
    """Rollback a patch"""
    name = args.patch
    
    if name not in engine.patches:
        print(f"❌ Unknown patch: {name}")
        return 1
    
    print(f"🔄 Rolling back patch: {name}\n")
    
    result = engine.rollback_patch(name)
    status_emoji = "✅" if result.status == PatchStatus.APPLIED else "❌"
    print(f"{status_emoji} {result.message}\n")
    
    if args.restart:
        print("🔄 Restarting OpenClaw gateway...")
        if engine.restart_gateway():
            print("✅ Gateway restarted successfully")
        else:
            print("⚠️  Failed to restart gateway")


def main():
    """Main CLI entry point"""
    
    parser = argparse.ArgumentParser(
        description="OpenClaw Patcher - Unified patch management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--openclaw-dir",
        type=Path,
        help="OpenClaw installation directory (auto-detected if not specified)"
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show patch status")
    status_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed information"
    )
    
    # Apply command
    apply_parser = subparsers.add_parser("apply", help="Apply patches")
    apply_parser.add_argument(
        "patches",
        nargs="*",
        help="Patch names to apply (or use --all)"
    )
    apply_parser.add_argument(
        "--all",
        action="store_true",
        help="Apply all patches"
    )
    apply_parser.add_argument(
        "--force",
        action="store_true",
        help="Force apply even if already applied"
    )
    apply_parser.add_argument(
        "--restart",
        action="store_true",
        default=True,
        help="Restart gateway after applying (default: true)"
    )
    apply_parser.add_argument(
        "--no-restart",
        action="store_false",
        dest="restart",
        help="Skip gateway restart"
    )
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check specific patch")
    check_parser.add_argument("patch", help="Patch name to check")
    
    # Rollback command
    rollback_parser = subparsers.add_parser("rollback", help="Rollback a patch")
    rollback_parser.add_argument("patch", help="Patch name to rollback")
    rollback_parser.add_argument(
        "--restart",
        action="store_true",
        help="Restart gateway after rollback"
    )
    
    args = parser.parse_args()
    
    # Initialize engine
    try:
        engine = PatchEngine(openclaw_dir=args.openclaw_dir)
        
        # Register all patches
        for patch_class in ALL_PATCHES:
            engine.register_patch(patch_class)
        
    except Exception as e:
        print(f"❌ Failed to initialize patcher: {e}")
        return 1
    
    # Route to command handler
    commands = {
        "status": cmd_status,
        "apply": cmd_apply,
        "check": cmd_check,
        "rollback": cmd_rollback,
    }
    
    handler = commands.get(args.command)
    if handler:
        return handler(args, engine) or 0
    else:
        print(f"❌ Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
