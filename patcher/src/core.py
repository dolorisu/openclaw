"""
Core patch engine for OpenClaw patcher system
"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Set, Callable


class PatchStatus(Enum):
    """Status of a patch"""
    NOT_APPLIED = "not_applied"
    APPLIED = "applied"
    PARTIALLY_APPLIED = "partially_applied"
    FAILED = "failed"
    CONFLICT = "conflict"


@dataclass
class PatchResult:
    """Result of applying a patch"""
    status: PatchStatus
    files_modified: List[Path] = field(default_factory=list)
    files_failed: List[Path] = field(default_factory=list)
    message: str = ""
    details: Dict[str, any] = field(default_factory=dict)


class Patch(ABC):
    """
    Base class for all patches
    
    Subclasses must implement:
    - name: Unique identifier
    - description: Human-readable description
    - dependencies: List of patch names this depends on
    - check(): Check if patch is already applied
    - apply(): Apply the patch
    - rollback(): Rollback the patch (optional)
    """
    
    name: str = ""
    description: str = ""
    dependencies: List[str] = []
    
    def __init__(self, engine: 'PatchEngine'):
        self.engine = engine
        self.dist_dir = engine.dist_dir
    
    @abstractmethod
    def check(self) -> PatchStatus:
        """Check if patch is already applied"""
        pass
    
    @abstractmethod
    def apply(self) -> PatchResult:
        """Apply the patch"""
        pass
    
    def rollback(self) -> PatchResult:
        """Rollback the patch (optional, default: not implemented)"""
        return PatchResult(
            status=PatchStatus.FAILED,
            message=f"Rollback not implemented for {self.name}"
        )
    
    def find_files(self, pattern: str) -> List[Path]:
        """Find files in dist directory matching pattern (glob)"""
        return sorted(self.dist_dir.glob(pattern))
    
    def find_files_containing(self, pattern: str, glob_pattern: str = "*.js") -> List[Path]:
        """Find files containing a regex pattern"""
        regex = re.compile(pattern)
        matches = []
        for f in self.dist_dir.glob(glob_pattern):
            if not f.is_file():
                continue
            try:
                content = f.read_text(encoding='utf-8', errors='ignore')
                if regex.search(content):
                    matches.append(f)
            except Exception:
                continue
        return sorted(matches)
    
    def backup_file(self, file_path: Path) -> Path:
        """Create backup of file before modification"""
        backup_dir = self.engine.backup_dir / self.name
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create backup with hash to avoid collisions
        file_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:8]
        backup_path = backup_dir / f"{file_path.name}.{file_hash}.bak"
        
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def replace_in_file(
        self,
        file_path: Path,
        old_text: str,
        new_text: str,
        backup: bool = True,
        count: int = -1
    ) -> bool:
        """
        Replace text in file
        
        Args:
            file_path: Path to file
            old_text: Text to find (can be regex if regex=True)
            new_text: Replacement text
            backup: Create backup before modifying
            count: Max replacements (-1 = all)
        
        Returns:
            True if replaced, False if not found
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            
            if old_text not in content:
                return False
            
            if backup:
                self.backup_file(file_path)
            
            new_content = content.replace(old_text, new_text, count)
            file_path.write_text(new_content, encoding='utf-8')
            return True
            
        except Exception as e:
            print(f"Error replacing in {file_path}: {e}")
            return False
    
    def regex_replace_in_file(
        self,
        file_path: Path,
        pattern: str,
        replacement: str,
        backup: bool = True,
        flags: int = 0
    ) -> int:
        """
        Replace using regex in file
        
        Returns:
            Number of replacements made
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            
            if backup:
                self.backup_file(file_path)
            
            new_content, count = re.subn(pattern, replacement, content, flags=flags)
            
            if count > 0:
                file_path.write_text(new_content, encoding='utf-8')
            
            return count
            
        except Exception as e:
            print(f"Error regex replacing in {file_path}: {e}")
            return 0


class PatchEngine:
    """
    Core patch engine that manages patch lifecycle
    """
    
    def __init__(
        self,
        openclaw_dir: Optional[Path] = None,
        backup_dir: Optional[Path] = None
    ):
        self.openclaw_dir = openclaw_dir or self._find_openclaw_dir()
        self.dist_dir = self.openclaw_dir / "dist"
        self.backup_dir = backup_dir or (Path.home() / ".openclaw" / "patcher" / "backups")
        
        if not self.dist_dir.exists():
            raise FileNotFoundError(f"OpenClaw dist directory not found: {self.dist_dir}")
        
        self.patches: Dict[str, Patch] = {}
        self._dependency_graph: Dict[str, Set[str]] = {}
    
    def _find_openclaw_dir(self) -> Path:
        """Find OpenClaw installation directory"""
        # Try common locations
        locations = [
            Path("/opt/homebrew/lib/node_modules/openclaw"),
            Path("/usr/local/lib/node_modules/openclaw"),
            Path.home() / ".npm-global" / "lib" / "node_modules" / "openclaw",
        ]
        
        # Try using `which openclaw`
        try:
            result = subprocess.run(
                ["which", "openclaw"],
                capture_output=True,
                text=True,
                check=True
            )
            openclaw_bin = Path(result.stdout.strip())
            # Resolve symlink and go up to find node_modules
            openclaw_real = openclaw_bin.resolve()
            # Typically: /usr/local/bin/openclaw -> ../lib/node_modules/openclaw/dist/cli.js
            node_modules_path = openclaw_real.parent.parent
            if (node_modules_path / "dist").exists():
                return node_modules_path
        except Exception:
            pass
        
        # Fallback to common locations
        for loc in locations:
            if loc.exists() and (loc / "dist").exists():
                return loc
        
        raise FileNotFoundError("Could not find OpenClaw installation")
    
    def register_patch(self, patch_class: type[Patch]) -> None:
        """Register a patch class"""
        patch = patch_class(self)
        self.patches[patch.name] = patch
        self._dependency_graph[patch.name] = set(patch.dependencies)
    
    def get_patch(self, name: str) -> Optional[Patch]:
        """Get a registered patch by name"""
        return self.patches.get(name)
    
    def check_patch(self, name: str) -> PatchStatus:
        """Check status of a patch"""
        patch = self.get_patch(name)
        if not patch:
            raise ValueError(f"Unknown patch: {name}")
        return patch.check()
    
    def check_all(self) -> Dict[str, PatchStatus]:
        """Check status of all patches"""
        return {name: patch.check() for name, patch in self.patches.items()}
    
    def resolve_dependencies(self, patch_names: List[str]) -> List[str]:
        """
        Resolve patch dependencies in correct order
        
        Returns list of patch names in application order (dependencies first)
        """
        visited = set()
        order = []
        
        def visit(name: str):
            if name in visited:
                return
            visited.add(name)
            
            # Visit dependencies first
            for dep in self._dependency_graph.get(name, []):
                visit(dep)
            
            order.append(name)
        
        for name in patch_names:
            visit(name)
        
        return order
    
    def apply_patch(self, name: str, force: bool = False) -> PatchResult:
        """
        Apply a single patch
        
        Args:
            name: Patch name
            force: Apply even if already applied
        """
        patch = self.get_patch(name)
        if not patch:
            return PatchResult(
                status=PatchStatus.FAILED,
                message=f"Unknown patch: {name}"
            )
        
        # Check if already applied
        if not force:
            status = patch.check()
            if status == PatchStatus.APPLIED:
                return PatchResult(
                    status=PatchStatus.APPLIED,
                    message=f"Patch {name} already applied (use --force to reapply)"
                )
        
        # Check dependencies
        for dep in patch.dependencies:
            dep_status = self.check_patch(dep)
            if dep_status != PatchStatus.APPLIED:
                return PatchResult(
                    status=PatchStatus.FAILED,
                    message=f"Dependency not met: {dep} is {dep_status.value}"
                )
        
        # Apply patch
        return patch.apply()
    
    def apply_all(self, force: bool = False) -> Dict[str, PatchResult]:
        """
        Apply all patches in dependency order
        
        Args:
            force: Apply even if already applied
        """
        patch_names = list(self.patches.keys())
        ordered = self.resolve_dependencies(patch_names)
        
        results = {}
        for name in ordered:
            results[name] = self.apply_patch(name, force=force)
            
            # Stop if critical patch failed
            if results[name].status == PatchStatus.FAILED:
                print(f"⚠️  Patch {name} failed, stopping.")
                break
        
        return results
    
    def rollback_patch(self, name: str) -> PatchResult:
        """Rollback a single patch"""
        patch = self.get_patch(name)
        if not patch:
            return PatchResult(
                status=PatchStatus.FAILED,
                message=f"Unknown patch: {name}"
            )
        
        return patch.rollback()
    
    def restart_gateway(self) -> bool:
        """Restart OpenClaw gateway"""
        try:
            # Try systemd (Linux VPS)
            result = subprocess.run(
                ["systemctl", "--user", "restart", "openclaw-gateway"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return True
            
            # Try openclaw CLI
            result = subprocess.run(
                ["openclaw", "gateway", "restart"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
            
        except Exception as e:
            print(f"Failed to restart gateway: {e}")
            return False
