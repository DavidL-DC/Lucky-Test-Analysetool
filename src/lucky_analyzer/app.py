from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from .database import Database
from .models import DashboardMetrics
from .service import AnalyticsService


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "data" / "lucky_analyzer.sqlite3"


class LuckyAnalyzerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Lucky Test Analysetool")
        self.geometry("980x620")
        self.minsize(820, 520)

        self.database = Database(DATABASE_PATH)
        self.service = AnalyticsService(PROJECT_ROOT, self.database)
        self.metric_values: dict[str, tk.StringVar] = {}
        self.data_status = tk.StringVar(value="Noch keine Daten vorhanden")
        self.last_status_message = "Bereit"

        self._build_ui()
        self._show_metrics(self.database.dashboard_metrics())
        self.after(250, self.refresh_data)

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"))
        style.configure("Metric.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("Muted.TLabel", foreground="#59636e")

        main = ttk.Frame(self, padding=24)
        main.pack(fill="both", expand=True)

        header = ttk.Frame(main)
        header.pack(fill="x", pady=(0, 20))
        ttk.Label(header, text="Lucky Test Dashboard", style="Title.TLabel").pack(
            side="left"
        )
        self.refresh_button = ttk.Button(
            header, text="Jetzt aktualisieren", command=self.refresh_data
        )
        self.refresh_button.pack(side="right")

        ttk.Label(main, textvariable=self.data_status, style="Muted.TLabel").pack(
            anchor="w", pady=(0, 18)
        )

        cards = ttk.Frame(main)
        cards.pack(fill="x")
        for column in range(3):
            cards.columnconfigure(column, weight=1)

        definitions = [
            ("first_downloads", "Erstdownloads"),
            ("redownloads", "Erneute Downloads"),
            ("total_downloads", "Gesamtdownloads"),
            ("updates", "Updates"),
            ("installations", "Installationen*"),
            ("deletions", "Deinstallationen*"),
            ("average_rating", "Bewertung"),
            ("rating_count", "Bewertungsanzahl"),
        ]
        for index, (key, label) in enumerate(definitions):
            self._create_card(cards, index // 3, index % 3, key, label)

        ttk.Label(
            main,
            text=(
                "* Installationen und Deinstallationen beruhen auf freigegebenen "
                "Analytics-Daten und können verzögert oder unvollständig sein."
            ),
            style="Muted.TLabel",
            wraplength=850,
        ).pack(anchor="w", pady=(20, 0))

        status_frame = ttk.Frame(main)
        status_frame.pack(fill="x", side="bottom", pady=(20, 0))
        ttk.Separator(status_frame).pack(fill="x", pady=(0, 10))
        status_header = ttk.Frame(status_frame)
        status_header.pack(fill="x")
        ttk.Label(status_header, text="Status", style="Muted.TLabel").pack(side="left")
        ttk.Button(
            status_header, text="Status kopieren", command=self._copy_status
        ).pack(side="right")
        self.status_text = tk.Text(
            status_frame,
            height=4,
            wrap="word",
            relief="flat",
            background=self.cget("background"),
            font=("Segoe UI", 9),
        )
        self.status_text.pack(fill="x", pady=(4, 0))
        self._set_status("Bereit")

    def _create_card(
        self, parent: ttk.Frame, row: int, column: int, key: str, label: str
    ) -> None:
        frame = ttk.LabelFrame(parent, text=label, padding=16)
        frame.grid(row=row, column=column, sticky="nsew", padx=6, pady=6)
        value = tk.StringVar(value="–")
        self.metric_values[key] = value
        ttk.Label(frame, textvariable=value, style="Metric.TLabel").pack(anchor="w")

    def refresh_data(self) -> None:
        self.refresh_button.configure(state="disabled")
        self._set_status("App-Store-Daten werden aktualisiert …")
        threading.Thread(target=self._refresh_worker, daemon=True).start()

    def _refresh_worker(self) -> None:
        try:
            metrics = self.service.refresh()
        except Exception as exc:
            self.after(0, self._refresh_failed, str(exc))
            return
        self.after(0, self._refresh_succeeded, metrics)

    def _refresh_succeeded(self, metrics: DashboardMetrics) -> None:
        self._show_metrics(metrics)
        self._set_status("App-Store-Daten erfolgreich aktualisiert")
        self.refresh_button.configure(state="normal")

    def _refresh_failed(self, message: str) -> None:
        self._show_metrics(self.database.dashboard_metrics())
        self._set_status(f"Aktualisierung fehlgeschlagen:\n{message}")
        self.refresh_button.configure(state="normal")

    def _set_status(self, message: str) -> None:
        self.last_status_message = message
        self.status_text.configure(state="normal")
        self.status_text.delete("1.0", "end")
        self.status_text.insert("1.0", message)
        self.status_text.configure(state="disabled")

    def _copy_status(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self.last_status_message)
        self.update_idletasks()

    def _show_metrics(self, metrics: DashboardMetrics) -> None:
        integer_fields = (
            "first_downloads",
            "redownloads",
            "total_downloads",
            "updates",
            "installations",
            "deletions",
        )
        for name in integer_fields:
            self.metric_values[name].set(f"{getattr(metrics, name):,}".replace(",", "."))
        self.metric_values["average_rating"].set(
            "–" if metrics.average_rating is None else f"{metrics.average_rating:.2f}"
        )
        self.metric_values["rating_count"].set(
            "–"
            if metrics.rating_count is None
            else f"{metrics.rating_count:,}".replace(",", ".")
        )

        if metrics.last_success_at:
            local_time = metrics.last_success_at.astimezone()
            data_date = (
                metrics.data_through.strftime("%d.%m.%Y")
                if metrics.data_through
                else "unbekannt"
            )
            self.data_status.set(
                "Letzter erfolgreicher Abruf: "
                f"{local_time.strftime('%d.%m.%Y %H:%M')} Uhr · Datenstand: {data_date}"
            )
        else:
            self.data_status.set("Noch kein erfolgreicher Abruf")


def main() -> None:
    app = LuckyAnalyzerApp()
    app.mainloop()
