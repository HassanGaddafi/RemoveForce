"""
gui/app.py
Main application window — professional dark GUI with multi-tab layout.
"""

import threading
import os
from tkinter import filedialog, messagebox
import tkinter as tk
import customtkinter as ctk
from datetime import datetime

from core.engine import ForceDeleteEngine
from core.scanner import PathScanner
from utils.logger import AppLogger
from utils.history import HistoryManager, HistoryEntry
from utils.sysinfo import get_system_info, format_bytes


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Color palette ───────────────────────────────────────────────
C_BG       = "#0D0D0F"
C_SURFACE  = "#141418"
C_CARD     = "#1A1A20"
C_BORDER   = "#2A2A35"
C_RED      = "#E8354A"
C_RED_DIM  = "#4A1520"
C_AMBER    = "#F5A623"
C_GREEN    = "#2ECC71"
C_BLUE     = "#3B82F6"
C_TEXT     = "#F0F0F5"
C_MUTED    = "#6B6B80"
C_SUCCESS  = "#1A3A2A"


class RemoveForceApp:
    def __init__(self):
        self.logger  = AppLogger()
        self.history = HistoryManager()
        self.scanner = PathScanner()
        self.engine  = ForceDeleteEngine(logger=self.logger)

        self.selected_path = tk.StringVar()
        self._scan_result  = None
        self._deleting     = False

        self._build_window()
        self._build_ui()
        self.logger.add_callback(self._on_log)

    # ── Window setup ─────────────────────────────────────────────
    def _build_window(self):
        self.root = ctk.CTk()
        self.root.title("RemoveForce v2.0")
        self.root.geometry("900x680")
        self.root.minsize(760, 560)
        self.root.configure(fg_color=C_BG)

    # ── UI layout ─────────────────────────────────────────────────
    def _build_ui(self):
        self._build_header()

        self.tabview = ctk.CTkTabview(
            self.root, fg_color=C_SURFACE,
            segmented_button_fg_color=C_CARD,
            segmented_button_selected_color=C_RED,
            segmented_button_selected_hover_color="#C0273A",
            segmented_button_unselected_color=C_CARD,
            segmented_button_unselected_hover_color=C_BORDER,
            text_color=C_TEXT,
        )
        self.tabview.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.tabview.add("  Delete  ")
        self.tabview.add("  History  ")
        self.tabview.add("  Logs  ")
        self.tabview.add("  System  ")

        self._build_delete_tab(self.tabview.tab("  Delete  "))
        self._build_history_tab(self.tabview.tab("  History  "))
        self._build_logs_tab(self.tabview.tab("  Logs  "))
        self._build_system_tab(self.tabview.tab("  System  "))

    def _build_header(self):
        hdr = ctk.CTkFrame(self.root, fg_color=C_SURFACE, corner_radius=0, height=64)
        hdr.pack(fill="x", padx=0, pady=0)
        hdr.pack_propagate(False)

        left = ctk.CTkFrame(hdr, fg_color="transparent")
        left.pack(side="left", padx=20, fill="y")

        ctk.CTkLabel(
            left, text="RemoveForce",
            font=ctk.CTkFont("Courier", 22, "bold"),
            text_color=C_RED
        ).pack(side="left", pady=16)

        ctk.CTkLabel(
            left, text=" v2.0",
            font=ctk.CTkFont("Courier", 12),
            text_color=C_MUTED
        ).pack(side="left", pady=16)

        ctk.CTkLabel(
            hdr, text="⬡ Administrator Mode",
            font=ctk.CTkFont(size=12),
            text_color=C_GREEN
        ).pack(side="right", padx=24, pady=16)

    # ── DELETE TAB ────────────────────────────────────────────────
    def _build_delete_tab(self, parent):
        parent.configure(fg_color=C_SURFACE)

        # Path selection card
        card = self._card(parent, "Target Path")
        card.pack(fill="x", padx=16, pady=(12, 8))

        path_row = ctk.CTkFrame(card, fg_color="transparent")
        path_row.pack(fill="x", padx=16, pady=(0, 12))

        self.path_entry = ctk.CTkEntry(
            path_row, textvariable=self.selected_path,
            placeholder_text="Paste a path or browse...",
            font=ctk.CTkFont("Courier", 13),
            fg_color=C_BG, border_color=C_BORDER,
            text_color=C_TEXT, height=42
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            path_row, text="Browse File", width=110,
            fg_color=C_CARD, hover_color=C_BORDER,
            border_color=C_BORDER, border_width=1,
            text_color=C_TEXT, height=42,
            command=self._browse_file
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            path_row, text="Browse Folder", width=120,
            fg_color=C_CARD, hover_color=C_BORDER,
            border_color=C_BORDER, border_width=1,
            text_color=C_TEXT, height=42,
            command=self._browse_folder
        ).pack(side="left")

        ctk.CTkButton(
            card, text="Scan Target",
            fg_color=C_BLUE, hover_color="#2563EB",
            text_color="white", height=40, corner_radius=8,
            command=self._scan
        ).pack(padx=16, pady=(0, 16), fill="x")

        # Scan result card
        self.scan_card = self._card(parent, "Scan Result")
        self.scan_card.pack(fill="x", padx=16, pady=8)

        self.scan_text = ctk.CTkTextbox(
            self.scan_card, height=130,
            fg_color=C_BG, text_color=C_TEXT,
            font=ctk.CTkFont("Courier", 12),
            border_color=C_BORDER, border_width=1,
            state="disabled"
        )
        self.scan_text.pack(fill="x", padx=16, pady=(0, 16))

        # Warning checkbox
        self.confirm_var = tk.BooleanVar(value=False)
        self.confirm_check = ctk.CTkCheckBox(
            parent,
            text="I understand this action is permanent and cannot be undone",
            variable=self.confirm_var,
            text_color=C_MUTED, font=ctk.CTkFont(size=12),
            fg_color=C_RED, hover_color="#C0273A",
            checkmark_color="white",
        )
        self.confirm_check.pack(padx=16, pady=8, anchor="w")

        # Delete button
        self.delete_btn = ctk.CTkButton(
            parent, text="⚡  FORCE DELETE",
            fg_color=C_RED, hover_color="#C0273A",
            text_color="white",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=52, corner_radius=10,
            command=self._delete
        )
        self.delete_btn.pack(fill="x", padx=16, pady=8)

        # Progress bar
        self.progress = ctk.CTkProgressBar(
            parent, fg_color=C_CARD, progress_color=C_RED
        )
        self.progress.pack(fill="x", padx=16, pady=(0, 4))
        self.progress.set(0)

        self.status_label = ctk.CTkLabel(
            parent, text="Ready", text_color=C_MUTED,
            font=ctk.CTkFont("Courier", 11)
        )
        self.status_label.pack(anchor="w", padx=16)

    # ── HISTORY TAB ───────────────────────────────────────────────
    def _build_history_tab(self, parent):
        parent.configure(fg_color=C_SURFACE)

        # Stats row
        stats = self.history.get_stats()
        stat_row = ctk.CTkFrame(parent, fg_color="transparent")
        stat_row.pack(fill="x", padx=16, pady=(12, 8))

        self._stat_chip(stat_row, "Total", str(stats["total_operations"]), C_BLUE)
        self._stat_chip(stat_row, "Success", str(stats["successful"]), C_GREEN)
        self._stat_chip(stat_row, "Failed", str(stats["failed"]), C_RED)
        self._stat_chip(stat_row, "Freed", format_bytes(stats["total_size_freed"]), C_AMBER)

        # History list
        card = self._card(parent, "Operation History")
        card.pack(fill="both", expand=True, padx=16, pady=8)

        self.history_box = ctk.CTkTextbox(
            card, fg_color=C_BG, text_color=C_TEXT,
            font=ctk.CTkFont("Courier", 11),
            border_color=C_BORDER, border_width=1
        )
        self.history_box.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        ctk.CTkButton(
            card, text="Refresh", width=100,
            fg_color=C_CARD, hover_color=C_BORDER,
            text_color=C_TEXT, border_color=C_BORDER, border_width=1,
            command=self._refresh_history
        ).pack(side="right", padx=16, pady=(0, 12))

        self._refresh_history()

    # ── LOGS TAB ──────────────────────────────────────────────────
    def _build_logs_tab(self, parent):
        parent.configure(fg_color=C_SURFACE)

        card = self._card(parent, "Live Log")
        card.pack(fill="both", expand=True, padx=16, pady=(12, 16))

        self.log_box = ctk.CTkTextbox(
            card, fg_color=C_BG, text_color=C_TEXT,
            font=ctk.CTkFont("Courier", 11),
            border_color=C_BORDER, border_width=1
        )
        self.log_box.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        # Load recent logs
        for line in self.logger.get_recent_logs(50):
            self._append_log(line)

    # ── SYSTEM TAB ────────────────────────────────────────────────
    def _build_system_tab(self, parent):
        parent.configure(fg_color=C_SURFACE)

        info = get_system_info()
        card = self._card(parent, "System Information")
        card.pack(fill="x", padx=16, pady=(12, 8))

        rows = [
            ("Operating System", f"{info['os']} {info['os_release']}"),
            ("OS Version", info["os_version"][:60]),
            ("Architecture", info["machine"]),
            ("Python Version", info["python_version"]),
            ("Administrator", "Yes ✓" if info["is_admin"] else "No ✗"),
            ("Disk Free (C:)", info["disk_free"]),
            ("RAM Total", info["ram_total"]),
            ("RAM Available", info["ram_available"]),
        ]

        for i, (label, value) in enumerate(rows):
            row = ctk.CTkFrame(card, fg_color=C_BG if i % 2 == 0 else C_CARD, corner_radius=0)
            row.pack(fill="x", padx=16, pady=0)

            ctk.CTkLabel(
                row, text=label, width=200, anchor="w",
                text_color=C_MUTED, font=ctk.CTkFont(size=12)
            ).pack(side="left", padx=12, pady=8)

            ctk.CTkLabel(
                row, text=value, anchor="w",
                text_color=C_TEXT, font=ctk.CTkFont("Courier", 12)
            ).pack(side="left", padx=8, pady=8)

        # Deletion strategies
        strat_card = self._card(parent, "Deletion Strategies (in order)")
        strat_card.pack(fill="x", padx=16, pady=8)

        strategies = [
            ("1", "Unlock & Delete", "Kill locking processes, then delete normally"),
            ("2", "Take Ownership", "Use icacls/takeown to claim full control"),
            ("3", "Remove Read-only", "Strip readonly/hidden attributes recursively"),
            ("4", "CMD Force Delete", "Use cmd.exe /del /f /q as fallback"),
            ("5", "Schedule on Reboot", "MoveFileEx — delete on next Windows restart"),
        ]

        for num, name, desc in strategies:
            row = ctk.CTkFrame(strat_card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=3)

            ctk.CTkLabel(
                row, text=num, width=24,
                fg_color=C_RED, corner_radius=4,
                text_color="white", font=ctk.CTkFont("Courier", 11, "bold")
            ).pack(side="left", padx=(0, 10))

            ctk.CTkLabel(
                row, text=name, width=160, anchor="w",
                text_color=C_TEXT, font=ctk.CTkFont(size=12, weight="bold")
            ).pack(side="left")

            ctk.CTkLabel(
                row, text=desc, anchor="w",
                text_color=C_MUTED, font=ctk.CTkFont(size=11)
            ).pack(side="left", padx=8, pady=6)

    # ── Helpers ───────────────────────────────────────────────────
    def _card(self, parent, title: str) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color=C_CARD, corner_radius=10, border_color=C_BORDER, border_width=1)
        ctk.CTkLabel(
            frame, text=title.upper(),
            font=ctk.CTkFont("Courier", 10, "bold"),
            text_color=C_MUTED
        ).pack(anchor="w", padx=16, pady=(12, 6))
        return frame

    def _stat_chip(self, parent, label: str, value: str, color: str):
        chip = ctk.CTkFrame(parent, fg_color=C_CARD, corner_radius=8, border_color=C_BORDER, border_width=1)
        chip.pack(side="left", padx=(0, 8))
        ctk.CTkLabel(chip, text=value, font=ctk.CTkFont(size=20, weight="bold"), text_color=color).pack(padx=16, pady=(10, 0))
        ctk.CTkLabel(chip, text=label, font=ctk.CTkFont(size=11), text_color=C_MUTED).pack(padx=16, pady=(0, 10))

    def _browse_file(self):
        path = filedialog.askopenfilename(title="Select a file to delete")
        if path:
            self.selected_path.set(path)

    def _browse_folder(self):
        path = filedialog.askdirectory(title="Select a folder to delete")
        if path:
            self.selected_path.set(path)

    def _set_scan_text(self, text: str):
        self.scan_text.configure(state="normal")
        self.scan_text.delete("1.0", "end")
        self.scan_text.insert("1.0", text)
        self.scan_text.configure(state="disabled")

    def _scan(self):
        path = self.selected_path.get().strip()
        if not path:
            messagebox.showwarning("No path", "Please enter or browse a path first.")
            return

        self._status("Scanning...", C_BLUE)
        report = self.scanner.scan(path)
        self._scan_result = report

        lines = [
            f"  Path       : {report.path}",
            f"  Type       : {'File' if report.is_file else 'Directory'}",
            f"  Size       : {report.total_size_readable}",
            f"  Files      : {report.file_count}",
            f"  Subfolders : {report.folder_count}",
            f"  Locked by  : {', '.join(p['name'] for p in report.locked_by) or 'None'}",
        ]

        if report.warnings:
            lines.append("")
            for w in report.warnings:
                lines.append(f"  ⚠  {w}")

        self._set_scan_text("\n".join(lines))

        if report.is_system_path:
            self._status("System path detected — be careful!", C_AMBER)
        elif report.is_locked:
            self._status(f"Locked by {len(report.locked_by)} process(es) — RemoveForce will handle it", C_AMBER)
        else:
            self._status("Target scanned — ready to delete", C_GREEN)

    def _delete(self):
        if self._deleting:
            return

        path = self.selected_path.get().strip()
        if not path:
            messagebox.showwarning("No path", "Please select a target first.")
            return

        if not self.confirm_var.get():
            messagebox.showwarning("Confirm", "Please check the confirmation box before proceeding.")
            return

        if self._scan_result and self._scan_result.is_system_path:
            if not messagebox.askyesno(
                "System Path Warning",
                "This path is inside a protected Windows directory.\n\nAre you ABSOLUTELY sure you want to delete it?"
            ):
                return

        self._deleting = True
        self.delete_btn.configure(state="disabled", text="Deleting...")
        self.progress.set(0.1)
        self._status("Starting deletion...", C_AMBER)

        def _worker():
            result = self.engine.delete(path)

            # Record in history
            scan = self._scan_result
            entry = HistoryEntry(
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                path=result.path,
                success=result.success,
                method_used=result.method_used,
                processes_killed=result.processes_killed,
                duration_ms=result.duration_ms,
                error=result.error,
                size_bytes=scan.total_size_bytes if scan else 0,
                file_count=scan.file_count if scan else 0,
            )
            self.history.record(entry)

            self.root.after(0, lambda: self._on_delete_done(result))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_delete_done(self, result):
        self._deleting = False
        self.delete_btn.configure(state="normal", text="⚡  FORCE DELETE")
        self.progress.set(1.0)
        self._scan_result = None
        self.confirm_var.set(False)

        if result.success:
            self.progress.configure(progress_color=C_GREEN)
            self._status(
                f"Deleted in {result.duration_ms:.0f}ms via {result.method_used}",
                C_GREEN
            )
            msg = f"Successfully deleted:\n{result.path}"
            if result.processes_killed:
                msg += f"\n\nKilled processes: {', '.join(result.processes_killed)}"
            if result.error:
                msg += f"\n\nNote: {result.error}"
            messagebox.showinfo("Success", msg)
            self.selected_path.set("")
            self._set_scan_text("")
        else:
            self.progress.configure(progress_color=C_RED)
            self._status(f"Deletion failed: {result.error}", C_RED)
            messagebox.showerror("Failed", f"Could not delete:\n{result.path}\n\nReason: {result.error}")

        self.root.after(2000, lambda: self.progress.set(0))
        self.root.after(2000, lambda: self.progress.configure(progress_color=C_RED))

    def _status(self, text: str, color: str = C_MUTED):
        self.status_label.configure(text=text, text_color=color)

    def _on_log(self, message: str):
        self.root.after(0, lambda: self._append_log(message))

    def _append_log(self, line: str):
        try:
            self.log_box.configure(state="normal")
            color = C_RED if "[ERROR]" in line else (C_AMBER if "[WARN]" in line else C_TEXT)
            self.log_box.insert("end", line + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        except Exception:
            pass

    def _refresh_history(self):
        self.history_box.configure(state="normal")
        self.history_box.delete("1.0", "end")
        entries = self.history.get_all()
        if not entries:
            self.history_box.insert("1.0", "  No operations recorded yet.")
        else:
            for e in entries[:50]:
                icon = "✓" if e.get("success") else "✗"
                line = (
                    f"  {icon}  {e.get('timestamp', '')}  |  "
                    f"{os.path.basename(e.get('path', ''))}  |  "
                    f"{e.get('method_used', '')}  |  "
                    f"{e.get('duration_ms', 0):.0f}ms\n"
                )
                self.history_box.insert("end", line)
        self.history_box.configure(state="disabled")

    def run(self):
        self.root.mainloop()
