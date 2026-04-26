"""Listening stats dialog — shows top artists, genre distribution, totals."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QLabel, QScrollArea,
    QVBoxLayout, QWidget,
)


def _fmt_stats() -> str:
    from .. import stats as s

    totals = s.total_stats()
    if not totals or totals["total_plays"] == 0:
        return "No play history yet.\nStart listening and come back!"

    lines: list[str] = []
    lines.append("Overall")
    lines.append(f"  Plays:    {totals['total_plays']}")
    lines.append(f"  Hours:    {totals['total_hours']:.1f} h")
    lines.append(f"  Artists:  {totals['unique_artists']}")
    lines.append(f"  Genres:   {totals['unique_genres']}")

    artists = s.top_artists(10)
    if artists:
        lines.append("")
        lines.append("Top Artists")
        for artist, cnt, hrs in artists:
            lines.append(f"  {artist:<28} {cnt:>4} plays  {hrs:.1f} h")

    genres = s.genre_distribution()
    if genres:
        lines.append("")
        lines.append("Genre Distribution")
        total_plays = totals["total_plays"]
        for genre, cnt in genres:
            pct = cnt / total_plays * 100
            lines.append(f"  {genre:<28} {cnt:>4} plays  {pct:.0f}%")

    return "\n".join(lines)


class StatsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Lyra — Listening Stats")
        self.setMinimumWidth(440)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        text = _fmt_stats()

        label = QLabel(text)
        label.setFont(QFont("Menlo", 12))
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        label.setContentsMargins(12, 12, 12, 12)

        scroll = QScrollArea()
        scroll.setWidget(label)
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(320)
        scroll.setFrameShape(scroll.Shape.NoFrame)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(scroll)
        layout.addWidget(buttons)
