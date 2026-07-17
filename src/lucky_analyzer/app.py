from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path

import customtkinter as ctk

from .database import Database
from .models import CustomerReview, DashboardMetrics
from .service import AnalyticsService


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "data" / "lucky_analyzer.sqlite3"

FONT = "Quicksand"
BACKGROUND = ("#F3F4F6", "#0C0D0F")
SIDEBAR = ("#FFFFFF", "#121416")
GLASS = ("#FFFFFF", "#191B1E")
GLASS_HOVER = ("#ECEFF2", "#25282C")
GLASS_BORDER = ("#DDE1E5", "#30343A")
INNER_SURFACE = ("#F6F7F9", "#111315")
SCROLL = ("#CDD3DA", "#353A41")
SCROLL_HOVER = ("#B8C0C9", "#474E57")
TEXT = ("#17191C", "#F4F5F6")
MUTED = ("#69727D", "#AAB0B8")
SUBTLE = ("#87919C", "#737B85")
INACTIVE = ("#A9B0B8", "#555C65")
ACCENT = "#78A9FF"
ACCENT_STRONG = "#4B83F5"
SUCCESS = "#55D6A4"
WARNING = "#FFBF69"


class LuckyAnalyzerApp(ctk.CTk):
    def __init__(self) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        super().__init__(fg_color=BACKGROUND)
        self.title("Lucky Test Analysetool")
        self.geometry("1240x840")
        self.minsize(1040, 720)

        self.database = Database(DATABASE_PATH)
        self.service = AnalyticsService(PROJECT_ROOT, self.database)
        self.metric_values: dict[str, tk.StringVar] = {}
        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        self.reviews_by_id: dict[str, CustomerReview] = {}
        self.review_buttons: dict[str, ctk.CTkButton] = {}
        self.current_review_text = ""
        self.data_status = tk.StringVar(value="Noch keine Daten vorhanden")
        self.review_distribution = tk.StringVar(value="Noch keine Rezensionen")
        self.source_status = tk.StringVar(value="Wartet auf Aktualisierung")
        self.dark_mode = tk.BooleanVar(value=True)
        self.last_status_message = "Bereit"

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_content()
        self._show_metrics(self.database.dashboard_metrics())
        self.after(300, self.refresh_data)

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=SIDEBAR)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(8, weight=1)

        logo = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo.grid(row=0, column=0, padx=22, pady=(28, 36), sticky="ew")
        badge = ctk.CTkLabel(
            logo,
            text="LT",
            width=44,
            height=44,
            corner_radius=14,
            fg_color=ACCENT_STRONG,
            text_color="white",
            font=ctk.CTkFont(FONT, 18, "bold"),
        )
        badge.pack(side="left")
        ctk.CTkLabel(
            logo,
            text="Lucky Test\nAnalytics",
            justify="left",
            text_color=TEXT,
            font=ctk.CTkFont(FONT, 17, "bold"),
        ).pack(side="left", padx=(12, 0))

        ctk.CTkLabel(
            sidebar,
            text="ÜBERSICHT",
            text_color=MUTED,
            font=ctk.CTkFont(FONT, 12, "bold"),
        ).grid(row=1, column=0, padx=24, pady=(0, 8), sticky="w")
        self._nav_item(
            sidebar,
            2,
            "dashboard",
            "⌂",
            "Dashboard",
            lambda: self._navigate("dashboard", None),
            active=True,
        )
        self._nav_item(
            sidebar,
            3,
            "ratings",
            "★",
            "Bewertungen",
            lambda: self._navigate("ratings", "rating_section"),
        )

        ctk.CTkLabel(
            sidebar,
            text="QUELLEN",
            text_color=MUTED,
            font=ctk.CTkFont(FONT, 12, "bold"),
        ).grid(row=4, column=0, padx=24, pady=(28, 8), sticky="w")
        self._source_item(sidebar, 5, "Apple App Store", SUCCESS)
        self._source_item(sidebar, 6, "YouTube", INACTIVE, "Demnächst")
        self._source_item(sidebar, 7, "TikTok & Instagram", INACTIVE, "Demnächst")

        ctk.CTkSwitch(
            sidebar,
            text="Dark Mode",
            variable=self.dark_mode,
            command=self._toggle_appearance,
            onvalue=True,
            offvalue=False,
            progress_color=ACCENT_STRONG,
            button_color="#FFFFFF",
            button_hover_color="#E3E8EF",
            text_color=MUTED,
            font=ctk.CTkFont(FONT, 15, "bold"),
        ).grid(row=8, column=0, padx=24, pady=(12, 4), sticky="sw")

        source_card = ctk.CTkFrame(
            sidebar,
            corner_radius=18,
            fg_color=GLASS,
            border_width=1,
            border_color=GLASS_BORDER,
        )
        source_card.grid(row=9, column=0, padx=18, pady=(16, 12), sticky="sew")
        ctk.CTkLabel(
            source_card,
            text="APPLE STATUS",
            text_color=MUTED,
            font=ctk.CTkFont(FONT, 11, "bold"),
        ).pack(anchor="w", padx=14, pady=(14, 5))
        ctk.CTkLabel(
            source_card,
            textvariable=self.source_status,
            text_color=TEXT,
            justify="left",
            wraplength=155,
            font=ctk.CTkFont(FONT, 13),
        ).pack(anchor="w", padx=14, pady=(0, 14))
        ctk.CTkLabel(
            sidebar,
            text="Lokal · Privat · Version 0.1",
            text_color=SUBTLE,
            font=ctk.CTkFont(FONT, 11),
        ).grid(row=10, column=0, padx=22, pady=(0, 20), sticky="w")

    def _nav_item(
        self,
        parent: ctk.CTkFrame,
        row: int,
        key: str,
        icon: str,
        label: str,
        command,
        active: bool = False,
    ) -> None:
        button = ctk.CTkButton(
            parent,
            text=f"{icon}   {label}",
            command=command,
            height=42,
            corner_radius=13,
            anchor="w",
            fg_color=GLASS_HOVER if active else "transparent",
            hover_color=GLASS_HOVER,
            text_color=TEXT if active else MUTED,
            font=ctk.CTkFont(FONT, 14, "bold" if active else "normal"),
        )
        button.grid(row=row, column=0, padx=16, pady=3, sticky="ew")
        self.nav_buttons[key] = button

    def _source_item(
        self,
        parent: ctk.CTkFrame,
        row: int,
        label: str,
        color: str | tuple[str, str],
        suffix: str = "Verbunden",
    ) -> None:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=0, padx=24, pady=7, sticky="ew")
        ctk.CTkLabel(frame, text="●", text_color=color, width=14).pack(side="left")
        ctk.CTkLabel(
            frame, text=label, text_color=MUTED, font=ctk.CTkFont(FONT, 13)
        ).pack(side="left", padx=(7, 0))
        ctk.CTkLabel(
            frame, text=suffix, text_color=SUBTLE, font=ctk.CTkFont(FONT, 12)
        ).pack(side="right")

    def _build_content(self) -> None:
        self.content = ctk.CTkScrollableFrame(
            self,
            corner_radius=0,
            fg_color=BACKGROUND,
            scrollbar_button_color=SCROLL,
            scrollbar_button_hover_color=SCROLL_HOVER,
        )
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.grid(row=0, column=0, padx=34, pady=(30, 8), sticky="ew")
        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(
            title_box,
            text="Guten Überblick.",
            text_color=TEXT,
            font=ctk.CTkFont(FONT, 31, "bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text="Alle wichtigen App-Store-Signale an einem Ort.",
            text_color=MUTED,
            font=ctk.CTkFont(FONT, 14),
        ).pack(anchor="w", pady=(3, 0))
        self.refresh_button = ctk.CTkButton(
            header,
            text="↻  Jetzt aktualisieren",
            command=self.refresh_data,
            width=174,
            height=44,
            corner_radius=15,
            fg_color=ACCENT_STRONG,
            hover_color="#6498FF",
            font=ctk.CTkFont(FONT, 14, "bold"),
        )
        self.refresh_button.pack(side="right", pady=5)

        ctk.CTkLabel(
            self.content,
            textvariable=self.data_status,
            text_color=MUTED,
            font=ctk.CTkFont(FONT, 13),
        ).grid(row=1, column=0, padx=36, pady=(0, 20), sticky="w")

        self._build_metric_cards(row=2)
        self._build_rating_overview(row=3)
        self._build_review_browser(row=4)
        self._build_status_panel(row=5)

    def _build_metric_cards(self, row: int) -> None:
        section = ctk.CTkFrame(self.content, fg_color="transparent")
        self.metric_section = section
        section.grid(row=row, column=0, padx=28, sticky="ew")
        for column in range(3):
            section.grid_columnconfigure(column, weight=1, uniform="metrics")
        definitions = [
            ("total_downloads", "Gesamtdownloads", "↓", ACCENT),
            ("first_downloads", "Erstdownloads", "＋", SUCCESS),
            ("redownloads", "Erneute Downloads", "↻", "#B69CFF"),
            ("updates", "Updates", "↑", "#78D7FF"),
            ("installations", "Installationen*", "◇", SUCCESS),
            ("deletions", "Deinstallationen*", "−", WARNING),
        ]
        for index, definition in enumerate(definitions):
            self._metric_card(section, index // 3, index % 3, *definition)

    def _metric_card(
        self,
        parent: ctk.CTkFrame,
        row: int,
        column: int,
        key: str,
        label: str,
        icon: str,
        accent: str,
    ) -> None:
        card = ctk.CTkFrame(
            parent,
            height=122,
            corner_radius=22,
            fg_color=GLASS,
            border_width=1,
            border_color=GLASS_BORDER,
        )
        card.grid(row=row, column=column, padx=7, pady=7, sticky="nsew")
        card.grid_propagate(False)
        ctk.CTkLabel(
            card,
            text=icon,
            width=34,
            height=34,
            corner_radius=11,
            fg_color=GLASS_HOVER,
            text_color=accent,
            font=ctk.CTkFont(FONT, 18, "bold"),
        ).place(x=18, y=17)
        value = tk.StringVar(value="–")
        self.metric_values[key] = value
        ctk.CTkLabel(
            card,
            textvariable=value,
            text_color=TEXT,
            font=ctk.CTkFont(FONT, 26, "bold"),
        ).place(x=18, y=58)
        ctk.CTkLabel(
            card,
            text=label,
            text_color=MUTED,
            font=ctk.CTkFont(FONT, 12),
        ).place(x=18, y=91)

    def _build_rating_overview(self, row: int) -> None:
        section = ctk.CTkFrame(self.content, fg_color="transparent")
        self.rating_section = section
        section.grid(row=row, column=0, padx=35, pady=(18, 0), sticky="ew")
        section.grid_columnconfigure(0, weight=2)
        section.grid_columnconfigure(1, weight=3)

        summary = self._glass_panel(section)
        summary.grid(row=0, column=0, padx=(0, 7), sticky="nsew")
        ctk.CTkLabel(
            summary,
            text="DACH-Gesamtbewertung",
            text_color=MUTED,
            font=ctk.CTkFont(FONT, 13, "bold"),
        ).pack(anchor="w", padx=22, pady=(20, 4))
        rating_row = ctk.CTkFrame(summary, fg_color="transparent")
        rating_row.pack(fill="x", padx=22)
        for key in ("dach_average_rating", "dach_rating_count"):
            self.metric_values[key] = tk.StringVar(value="–")
        ctk.CTkLabel(
            rating_row,
            textvariable=self.metric_values["dach_average_rating"],
            text_color=TEXT,
            font=ctk.CTkFont(FONT, 34, "bold"),
        ).pack(side="left")
        ctk.CTkLabel(
            summary,
            textvariable=self.metric_values["dach_rating_count"],
            text_color=MUTED,
            font=ctk.CTkFont(FONT, 13),
        ).pack(anchor="w", padx=22, pady=(2, 18))
        ctk.CTkLabel(
            summary,
            text="Gewichtet aus Deutschland, Österreich und der Schweiz",
            text_color=SUBTLE,
            wraplength=280,
            justify="left",
            font=ctk.CTkFont(FONT, 11),
        ).pack(anchor="w", padx=22, pady=(0, 20))

        distribution = self._glass_panel(section)
        distribution.grid(row=0, column=1, padx=(7, 0), sticky="nsew")
        top = ctk.CTkFrame(distribution, fg_color="transparent")
        top.pack(fill="x", padx=22, pady=(18, 8))
        ctk.CTkLabel(
            top,
            text="Schriftliche Rezensionen",
            text_color=TEXT,
            font=ctk.CTkFont(FONT, 16, "bold"),
        ).pack(side="left")
        for key in ("written_review_average", "written_review_count"):
            self.metric_values[key] = tk.StringVar(value="–")
        ctk.CTkLabel(
            top,
            textvariable=self.metric_values["written_review_average"],
            text_color=WARNING,
            font=ctk.CTkFont(FONT, 15, "bold"),
        ).pack(side="right")
        self.rating_bars: dict[int, ctk.CTkProgressBar] = {}
        self.rating_counts: dict[int, tk.StringVar] = {}
        for stars in range(5, 0, -1):
            line = ctk.CTkFrame(distribution, fg_color="transparent")
            line.pack(fill="x", padx=22, pady=3)
            ctk.CTkLabel(
                line,
                text=f"{stars} ★",
                width=34,
                text_color=MUTED,
                font=ctk.CTkFont(FONT, 11),
            ).pack(side="left")
            bar = ctk.CTkProgressBar(
                line,
                height=7,
                corner_radius=4,
                fg_color=INNER_SURFACE,
                progress_color=WARNING,
            )
            bar.pack(side="left", fill="x", expand=True, padx=10)
            bar.set(0)
            self.rating_bars[stars] = bar
            count = tk.StringVar(value="0")
            self.rating_counts[stars] = count
            ctk.CTkLabel(
                line, textvariable=count, width=26, text_color=MUTED
            ).pack(side="right")
        ctk.CTkLabel(
            distribution,
            textvariable=self.metric_values["written_review_count"],
            text_color=SUBTLE,
            font=ctk.CTkFont(FONT, 11),
        ).pack(anchor="e", padx=22, pady=(5, 15))

    def _build_review_browser(self, row: int) -> None:
        panel = self._glass_panel(self.content)
        panel.grid(row=row, column=0, padx=35, pady=(16, 0), sticky="ew")
        panel.grid_columnconfigure(0, weight=2)
        panel.grid_columnconfigure(1, weight=3)
        ctk.CTkLabel(
            panel,
            text="Neueste Rezensionen",
            text_color=TEXT,
            font=ctk.CTkFont(FONT, 17, "bold"),
        ).grid(row=0, column=0, padx=22, pady=(18, 10), sticky="w")
        ctk.CTkButton(
            panel,
            text="Text kopieren",
            command=self._copy_review,
            width=108,
            height=30,
            corner_radius=10,
            fg_color=GLASS_HOVER,
            hover_color=GLASS_HOVER,
            text_color=MUTED,
        ).grid(row=0, column=1, padx=22, pady=(18, 10), sticky="e")

        self.review_list = ctk.CTkScrollableFrame(
            panel,
            height=245,
            corner_radius=14,
            fg_color=INNER_SURFACE,
            scrollbar_button_color=SCROLL,
        )
        self.review_list.grid(row=1, column=0, padx=(18, 8), pady=(0, 18), sticky="nsew")
        self.review_list.bind("<MouseWheel>", self._scroll_review_list)
        self.review_list._parent_canvas.bind("<MouseWheel>", self._scroll_review_list)
        self.review_text = ctk.CTkTextbox(
            panel,
            height=245,
            corner_radius=14,
            fg_color=INNER_SURFACE,
            border_width=1,
            border_color=GLASS_BORDER,
            text_color=TEXT,
            font=ctk.CTkFont(FONT, 14),
            wrap="word",
        )
        self.review_text.grid(row=1, column=1, padx=(8, 18), pady=(0, 18), sticky="nsew")
        self.review_text.configure(state="disabled")
        self.review_text._textbox.bind("<MouseWheel>", self._scroll_review_text)

    def _build_status_panel(self, row: int) -> None:
        panel = self._glass_panel(self.content)
        panel.grid(row=row, column=0, padx=35, pady=(16, 32), sticky="ew")
        header = ctk.CTkFrame(panel, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(13, 4))
        ctk.CTkLabel(
            header,
            text="Systemstatus",
            text_color=MUTED,
            font=ctk.CTkFont(FONT, 12, "bold"),
        ).pack(side="left")
        ctk.CTkButton(
            header,
            text="Kopieren",
            command=self._copy_status,
            width=74,
            height=26,
            corner_radius=9,
            fg_color="transparent",
            hover_color=GLASS_HOVER,
            text_color=MUTED,
        ).pack(side="right")
        self.status_text = ctk.CTkTextbox(
            panel,
            height=70,
            corner_radius=12,
            fg_color=INNER_SURFACE,
            text_color=MUTED,
            font=ctk.CTkFont(FONT, 12),
            wrap="word",
        )
        self.status_text.pack(fill="x", padx=18, pady=(0, 16))
        self.status_text._textbox.bind("<MouseWheel>", self._scroll_status_text)
        self._set_status("Bereit")

    def _glass_panel(self, parent: ctk.CTkBaseClass) -> ctk.CTkFrame:
        return ctk.CTkFrame(
            parent,
            corner_radius=22,
            fg_color=GLASS,
            border_width=1,
            border_color=GLASS_BORDER,
        )

    def _toggle_appearance(self) -> None:
        ctk.set_appearance_mode("dark" if self.dark_mode.get() else "light")

    def _navigate(self, key: str, target_attribute: str | None) -> None:
        self.update_idletasks()
        canvas = self.content._parent_canvas
        scroll_region = canvas.bbox("all")
        total_height = scroll_region[3] if scroll_region else 1
        target_y = 0 if target_attribute is None else getattr(self, target_attribute).winfo_y()
        canvas.yview_moveto(max(0.0, min(1.0, target_y / total_height)))
        for button_key, button in self.nav_buttons.items():
            active = button_key == key
            button.configure(
                fg_color=GLASS_HOVER if active else "transparent",
                text_color=TEXT if active else MUTED,
            )

    def _scroll_review_list(self, event) -> str:
        self.review_list._parent_canvas.yview_scroll(
            self._wheel_units(event, speed=6), "units"
        )
        return "break"

    def _scroll_review_text(self, event) -> str:
        self.review_text._textbox.yview_scroll(
            self._wheel_units(event, speed=4), "units"
        )
        return "break"

    def _scroll_status_text(self, event) -> str:
        self.status_text._textbox.yview_scroll(
            self._wheel_units(event, speed=4), "units"
        )
        return "break"

    @staticmethod
    def _wheel_units(event, speed: int) -> int:
        delta = getattr(event, "delta", 0)
        if delta == 0:
            return 0
        notches = max(1, round(abs(delta) / 120))
        return (-1 if delta > 0 else 1) * speed * notches

    def refresh_data(self) -> None:
        self.refresh_button.configure(state="disabled", text="Aktualisiere …")
        self.source_status.set("Daten werden synchronisiert …")
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
        self.source_status.set("Alle Apple-Daten aktuell")
        self._set_status("App-Store-Daten erfolgreich aktualisiert")
        self.refresh_button.configure(state="normal", text="↻  Jetzt aktualisieren")

    def _refresh_failed(self, message: str) -> None:
        self._show_metrics(self.database.dashboard_metrics())
        self.source_status.set("Teilweise aktuell · Details unten")
        self._set_status(f"Aktualisierung mit Hinweis:\n{message}")
        self.refresh_button.configure(state="normal", text="↻  Erneut versuchen")

    def _set_status(self, message: str) -> None:
        self.last_status_message = message
        self.status_text.configure(state="normal")
        self.status_text.delete("1.0", "end")
        self.status_text.insert("1.0", message)
        self.status_text.configure(state="disabled")

    def _copy_status(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self.last_status_message)

    def _show_metrics(self, metrics: DashboardMetrics) -> None:
        for name in (
            "first_downloads",
            "redownloads",
            "total_downloads",
            "updates",
            "installations",
            "deletions",
        ):
            self.metric_values[name].set(self._format_number(getattr(metrics, name)))
        self.metric_values["dach_average_rating"].set(
            "–" if metrics.dach_average_rating is None else f"{metrics.dach_average_rating:.2f} ★"
        )
        self.metric_values["dach_rating_count"].set(
            f"{self._format_number(metrics.dach_rating_count)} Bewertungen"
        )
        self.metric_values["written_review_average"].set(
            "–" if metrics.written_review_average is None else f"{metrics.written_review_average:.2f} ★"
        )
        self.metric_values["written_review_count"].set(
            f"{self._format_number(metrics.written_review_count)} schriftliche Rezensionen"
        )
        distribution = metrics.written_review_distribution
        maximum = max(distribution, default=0)
        for stars in range(1, 6):
            count = distribution[stars - 1]
            self.rating_counts[stars].set(str(count))
            self.rating_bars[stars].set(count / maximum if maximum else 0)
        self._show_reviews()

        if metrics.last_success_at:
            local_time = metrics.last_success_at.astimezone()
            data_date = metrics.data_through.strftime("%d.%m.%Y") if metrics.data_through else "–"
            self.data_status.set(
                f"Zuletzt synchronisiert {local_time.strftime('%d.%m.%Y um %H:%M')} Uhr  ·  Datenstand {data_date}"
            )
        else:
            self.data_status.set("Apple-Verbindung aktiv · Analytics-Berichte werden vorbereitet")

    def _show_reviews(self) -> None:
        reviews = self.database.latest_customer_reviews()
        self.reviews_by_id = {review.review_id: review for review in reviews}
        self.review_buttons.clear()
        for widget in self.review_list.winfo_children():
            widget.destroy()
        for review in reviews:
            button = ctk.CTkButton(
                self.review_list,
                text=self._review_button_text(review),
                command=lambda item=review: self._display_review(item),
                height=58,
                corner_radius=13,
                anchor="w",
                fg_color="transparent",
                hover_color=GLASS_HOVER,
                text_color=MUTED,
                font=ctk.CTkFont(FONT, 12),
            )
            button.pack(fill="x", pady=3)
            button.bind("<MouseWheel>", self._scroll_review_list)
            if button._text_label is not None:
                button._text_label.configure(justify="left", anchor="w")
                button._text_label.bind("<MouseWheel>", self._scroll_review_list)
            self.review_buttons[review.review_id] = button
        if reviews:
            self._display_review(reviews[0])
        else:
            self._set_review_text("Noch keine schriftlichen Rezensionen vorhanden.")

    def _review_button_text(self, review: CustomerReview) -> str:
        title = review.title.strip() or "Ohne Titel"
        return (
            f"{review.rating} ★   {title[:34]}\n"
            f"{review.created_at.astimezone().strftime('%d.%m.%Y')}  ·  {review.territory or '–'}"
        )

    def _display_review(self, review: CustomerReview) -> None:
        for review_id, button in self.review_buttons.items():
            button.configure(
                fg_color=GLASS_HOVER if review_id == review.review_id else "transparent",
                text_color=TEXT if review_id == review.review_id else MUTED,
            )
        nickname = review.reviewer_nickname.strip() or "Unbekannt"
        header = f"{review.rating} ★   {nickname}"
        if review.territory:
            header += f"   ·   {review.territory}"
        title = review.title.strip() or "Ohne Titel"
        self._set_review_text(f"{header}\n\n{title}\n\n{review.body.strip()}")

    def _set_review_text(self, text: str) -> None:
        self.current_review_text = text
        self.review_text.configure(state="normal")
        self.review_text.delete("1.0", "end")
        self.review_text.insert("1.0", text)
        self.review_text.configure(state="disabled")

    def _copy_review(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self.current_review_text)

    @staticmethod
    def _format_number(value: int) -> str:
        return f"{value:,}".replace(",", ".")


def main() -> None:
    app = LuckyAnalyzerApp()
    app.mainloop()
