"""Small English/German interface translations for app navigation and controls."""

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QAbstractButton, QComboBox, QGroupBox, QLabel, QTabWidget, QToolButton, QWidget


DE = {
    "SPP 2433 - Point Cloud Evaluation": "SPP 2433 - Punktwolkenauswertung",
    "Open project": "Projekt öffnen",
    "Recent projects": "Zuletzt verwendete Projekte",
    "No recent projects": "Keine zuletzt verwendeten Projekte",
    "Save": "Speichern",
    "Save as": "Speichern unter",
    "Save project as": "Projekt speichern unter",
    "Pack & Go": "Pack & Go",
    "TXT to CSV": "TXT in CSV",
    "Light theme": "Helles Design",
    "Dark theme": "Dunkles Design",
    "New user guide": "Einführung",
    "Documentation": "Dokumentation",
    "Documentation; open the menu for the new user guide": "Dokumentation; über das Menü den Guide öffnen",
    "About": "Über",
    "GitHub repository": "GitHub-Repository",
    "Help and information": "Hilfe und Informationen",
    "Point Clouds": "Punktwolken",
    "Add point cloud": "Punktwolke hinzufügen",
    "Remove selected point cloud": "Ausgewählte Punktwolke entfernen",
    "Move selected point cloud up": "Ausgewählte Punktwolke nach oben",
    "Move selected point cloud down": "Ausgewählte Punktwolke nach unten",
    "Camera Orientation": "Kameraausrichtung",
    "Top (+Z)": "Oben (+Z)",
    "Bottom (−Z)": "Unten (−Z)",
    "+X": "+X",
    "−X": "−X",
    "+Y": "+Y",
    "−Y": "−Y",
    "Diagonal (−X,+Y,+Z)": "Diagonal (−X,+Y,+Z)",
    "Isometric": "Isometrisch",
    "Apply Camera Angles": "Kamerawinkel anwenden",
    "Elevation:": "Höhenwinkel:",
    "Azimuth:": "Azimut:",
    "Roll:": "Rollen:",
    "Point Viewer": "Punktansicht",
    "View controls": "Ansichtssteuerung",
    "Workspace tools": "Werkzeuge",
    "Scroll tabs left": "Tabs nach links verschieben",
    "Scroll tabs right": "Tabs nach rechts verschieben",
    "Choose a step for the selected point cloud": "Werkzeug für die ausgewählte Punktwolke wählen",
    "Data": "Daten",
    "Preview Plot": "Plot-Vorschau",
    "Performance": "Leistung",
    "Limit points in interactive preview": "Punkte in der interaktiven Vorschau begrenzen",
    "Maximum preview points:": "Maximale Punktzahl in der Vorschau:",
    "This limit only affects the interactive preview. Plot exports always use all points.": "Diese Begrenzung betrifft nur die interaktive Vorschau. Plot-Exporte verwenden immer alle Punkte.",
    "Limits point density in the live plot only. Plot exports always use full resolution.": "Begrenzt nur die Punktdichte in der Live-Ansicht. Plot-Exporte verwenden immer die volle Auflösung.",
    "Colour Mapping": "Farbzuordnung",
    "Axes": "Achsen",
    "Legend": "Legende",
    "Use preview settings": "Vorschau-Einstellungen übernehmen",
    "Choose whether to replace the active export profile or create a new one from the preview.": "Wähle, ob das aktive Exportprofil ersetzt oder aus der Vorschau ein neues erstellt werden soll.",
    "Prepare": "Vorbereiten",
    "Filter": "Filtern",
    "Manual Align": "Manuell ausrichten",
    "Auto Align": "Automatisch ausrichten",
    "Align": "Ausrichten",
    "Evaluate": "Auswerten",
    "Export": "Exportieren",
    "Export Point Cloud": "Punktwolke exportieren",
    "Export options": "Exportoptionen",
    "Export current display": "Aktuelle Ansicht exportieren",
    "Export full resolution": "Volle Auflösung exportieren",
    "Export filtered point cloud": "Gefilterte Punktwolke exportieren",
    "Export centered": "Zentriert exportieren",
    "Preview export settings": "Exporteinstellungen ansehen",
    "Manual transform": "Manuelle Transformation",
    "Global alignment": "Globale Ausrichtung",
    "Color Settings": "Farbeinstellungen",
    "Base Color:": "Grundfarbe:",
    "Mapping Column:": "Farbspalte:",
    "Color Mapping Column (Overrides Base Color):": "Farbzuordnungsspalte (ersetzt Grundfarbe):",
    "Analysis Display": "Analyseanzeige",
    "Show latest pointwise error map": "Letzte punktweise Fehlerkarte anzeigen",
    "Show error map": "Fehlerkarte anzeigen",
    "Error-map colouring:": "Färbung der Fehlerkarte:",
    "Error map:": "Fehlerkarte:",
    "Calculated deviation": "Berechnete Abweichung",
    "Difference from mean deviation": "Abweichung vom Mittelwert",
    "Unsigned nearest-reference distance (existing)": "Vorhandener, ungerichteter Referenzabstand",
    "Signed local normal / plane distance": "Lokaler vorzeichenbehafteter Normalen-/Ebenenabstand",
    "Automatic (signed: symmetric P95 magnitude)": "Automatisch (vorzeichenbehaftet: symmetrischer P95-Betrag)",
    "Symmetric +/- maximum": "Symmetrisches +/- Maximum",
    "Custom minimum / maximum": "Benutzerdefiniertes Minimum / Maximum",
    "Automatic (by error method)": "Automatisch (nach Fehlermethode)",
    "Blue / white at zero / red": "Blau / Weiß bei Null / Rot",
    "Blue / beige at zero / red": "Blau / Beige bei Null / Rot",
    "Voxel Grid Downsampling (Uniform)": "Voxel-Raster (gleichmäßige Reduktion)",
    "Enable Voxel Filter": "Voxel-Filter aktivieren",
    "Voxel filter": "Voxel-Filter",
    "Threshold:": "Schwellwert:",
    "Voxel Size:": "Voxelgröße:",
    "Outlier Filters": "Ausreißerfilter",
    "Std:": "Standardabweichung:",
    "Min:": "Minimum:",
    "Max:": "Maximum:",
    "Current Dataset": "Aktueller Datensatz",
    "Z-Score": "Z-Wert",
    "Z-Bounds": "Z-Grenzen",
    "Save Filtered Data": "Gefilterte Daten speichern",
    "Create Centred Copy": "Zentrierte Kopie erstellen",
    "Centred copy": "Zentrierte Kopie",
    "Derived Point Clouds": "Abgeleitete Punktwolken",
    "Export Filtered Point Cloud": "Gefilterte Punktwolke exportieren",
    "Alignment method": "Ausrichtungsmethode",
    "Bounded fine alignment": "Begrenzte Feinausrichtung",
    "Standard ICP": "Standard-ICP",
    "Robust ICP (Partial Overlap)": "Robustes ICP (teilweise Überlappung)",
    "Global PCA / FPFH": "Globale PCA / FPFH",
    "Manual Transform (Selected Dataset)": "Manuelle Transformation (Auswahl)",
    "Preset:": "Vorlage:",
    "Distance unit:": "Längeneinheit:",
    "Uniform scale:": "Einheitliche Skalierung:",
    "Rotate X (deg):": "Drehung X (Grad):",
    "Rotate Y (deg):": "Drehung Y (Grad):",
    "Rotate Z (deg):": "Drehung Z (Grad):",
    "Invert Axis:": "Achse umkehren:",
    "Invert X": "X umkehren",
    "Invert Y": "Y umkehren",
    "Invert Z": "Z umkehren",
    "Apply Transform": "Transformation anwenden",
    "Apply": "Anwenden",
    "Save As...": "Speichern unter…",
    "Rename...": "Umbenennen…",
    "Rename": "Umbenennen",
    "Delete": "Löschen",
    "Legacy ICP (unbounded)": "Älteres ICP-Verfahren (unbegrenzt)",
    "Previous Global Auto Alignment (PCA / FPFH)": "Vorherige globale automatische Ausrichtung (PCA / FPFH)",
    "Bounded Manual Fine Alignment (Selected -> Reference)": "Begrenzte manuelle Feinausrichtung (Auswahl -> Referenz)",
    "Run Legacy ICP (Selected -> Target)": "ICP ausführen (Auswahl -> Ziel)",
    "Run ICP": "ICP ausführen",
    "Run Previous Global Auto Align": "Vorherige globale automatische Ausrichtung starten",
    "Run global alignment": "Global ausrichten",
    "Optimise Manual Alignment": "Manuelle Ausrichtung optimieren",
    "Optimise alignment": "Ausrichtung optimieren",
    "Target (Reference):": "Ziel (Referenz):",
    "Method:": "Methode:",
    "Max Distance:": "Maximaler Abstand:",
    "Reference:": "Referenz:",
    "Selected cloud:": "Ausgewählte Wolke:",
    "Registration points:": "Registrierungspunkte:",
    "Translation X (+/-):": "Verschiebung X (+/-):",
    "Translation Y (+/-):": "Verschiebung Y (+/-):",
    "Translation Z (+/-):": "Verschiebung Z (+/-):",
    "Rotation X (+/-):": "Drehung X (+/-):",
    "Rotation Y (+/-):": "Drehung Y (+/-):",
    "Rotation Z (+/-):": "Drehung Z (+/-):",
    "Calculate Surface Error": "Oberflächenfehler berechnen",
    "Calculate error": "Fehler berechnen",
    "Surface Error (Source -> Reference)": "Oberflächenfehler (Quelle -> Referenz)",
    "Show pointwise error colour map after calculation": "Punktweise Fehlerkarte nach der Berechnung anzeigen",
    "Highlight errors above the mean in red": "Abweichungen über dem Mittelwert rot hervorheben",
    "Highlight above mean": "Über Mittelwert rot",
    "View results…": "Ergebnisse anzeigen…",
    "No comparison calculated yet.": "Noch kein Vergleich berechnet.",
    "No results — calculate surface error": "Keine Ergebnisse — zuerst Oberflächenfehler berechnen",
    "View Surface Error Results…": "Oberflächenfehler-Ergebnisse anzeigen…",
    "Source:": "Quelle:",
    "Reference edge margin:": "Randabstand der Referenz:",
    "Maximum source points:": "Maximale Quellenpunkte:",
    "Error method:": "Fehlermethode:",
    "Normal radius:": "Normalenradius:",
    "Maximum normal neighbours:": "Maximale Nachbarn für Normalen:",
    "Normal orientation:": "Normalenausrichtung:",
    "Axial measurement range:": "Axialer Messbereich:",
    "Heatmap scale:": "Heatmap-Skalierung:",
    "Heatmap minimum:": "Heatmap-Minimum:",
    "Heatmap maximum:": "Heatmap-Maximum:",
    "Result status:": "Ergebnisstatus:",
    "Last result:": "Letztes Ergebnis:",
    "Export Appearance": "Exportdarstellung",
    "Export Profiles": "Exportprofile",
    "New export profile": "Neues Exportprofil",
    "Rename export profile": "Exportprofil umbenennen",
    "Delete export profile": "Exportprofil löschen",
    "Import profile or export settings": "Profil oder Exporteinstellungen importieren",
    "Import export profile": "Exportprofil importieren",
    "Choose a profile:": "Profil auswählen:",
    "Name in this project:": "Name in diesem Projekt:",
    "Add export profile": "Exportprofil hinzufügen",
    "No export settings": "Keine Exporteinstellungen",
    "This file does not contain any export profiles or legacy export settings.": "Diese Datei enthält weder Exportprofile noch ältere Exporteinstellungen.",
    "A profile with this name already exists.": "Ein Profil mit diesem Namen existiert bereits.",
    "Export settings import error": "Fehler beim Import der Exporteinstellungen",
    "The selected file is not a project or export settings file.": "Die Datei enthält weder ein Projekt noch Exporteinstellungen.",
    "Use active error heatmap": "Aktive Fehler-Heatmap verwenden",
    "Use error heatmap": "Heatmap verwenden",
    "Height map (Z coordinate)": "Höhenkarte (Z-Koordinate)",
    "Height map (Z)": "Höhenkarte (Z)",
    "Show legend": "Legende anzeigen",
    "Heatmap:": "Heatmap:",
    "Height map:": "Höhenkarte:",
    "Heatmap colours:": "Heatmap-Farben:",
    "Height-map colours:": "Höhenkartenfarben:",
    "Colour-bar height:": "Farbleistenhöhe:",
    "Colour-bar decimal places:": "Dezimalstellen der Farbleiste:",
    "Colour-bar label:": "Farbleistenbeschriftung:",
    "Colour-bar label font size:": "Schriftgröße der Farbleistenbeschriftung:",
    "Colour-bar numbers font size:": "Schriftgröße der Farbleistenwerte:",
    "Point size:": "Punktgröße:",
    "X-axis label:": "X-Achsenbeschriftung:",
    "Y-axis label:": "Y-Achsenbeschriftung:",
    "Z-axis label:": "Z-Achsenbeschriftung:",
    "Axis label font size:": "Schriftgröße der Achsenbeschriftungen:",
    "Axis numbers font size:": "Schriftgröße der Achsenwerte:",
    "Z-axis title gap:": "Abstand zum Z-Achsennamen:",
    "Z-axis tick label gap:": "Abstand zu Z-Achsenwerten:",
    "Z-axis tick interval:": "Teilung der Z-Achse:",
    "Number of Z-axis ticks:": "Anzahl der Z-Achsenwerte:",
    "Legend:": "Legende:",
    "Legend point size:": "Punktgröße in der Legende:",
    "Legend placement:": "Position der Legende:",
    "Legend corner:": "Legendenecke:",
    "Legend title:": "Legendentitel:",
    "Legend labels:": "Legendenbeschriftungen:",
    "Inside plot": "Im Diagramm",
    "Outside plot": "Außerhalb des Diagramms",
    "Best position (inside)": "Beste Position (innen)",
    "Upper right": "Oben rechts",
    "Upper left": "Oben links",
    "Lower right": "Unten rechts",
    "Lower left": "Unten links",
    "Export Actions": "Exportaktionen",
    "Preview Export Settings": "Exporteinstellungen ansehen",
    "Preview": "Vorschau",
    "Export full-resolution plot": "Plot in voller Auflösung exportieren",
    "Exports the current plot settings at full point resolution without display voxel downsampling.": "Exportiert den Plot mit den aktuellen Einstellungen und voller Punktauflösung ohne Voxel-Reduktion der Anzeige.",
    "Export filtered": "Gefiltert exportieren",
    "Save export settings…": "Einstellungen speichern…",
    "Load export settings…": "Einstellungen laden…",
    "Save settings": "Setup speichern",
    "Load settings": "Setup laden",
    "Export Current Display": "Aktuelle Ansicht exportieren",
    "Export Full Resolution (No Voxel)": "Volle Auflösung exportieren (ohne Voxel)",
    "Save Export Settings…": "Exporteinstellungen speichern…",
    "Load Export Settings…": "Exporteinstellungen laden…",
}


def apply_language(root: QWidget, language: str) -> None:
    """Translate known interface labels while retaining English source strings."""
    translations = DE if language == "de" else {}

    def translated(original: str) -> str:
        return translations.get(original, original)

    for action in root.findChildren(QAction):
        original = action.property("englishText")
        if original is None:
            original = action.text()
            action.setProperty("englishText", original)
        action.setText(translated(original))
        tooltip = action.property("englishToolTip")
        if tooltip is None:
            tooltip = action.toolTip()
            action.setProperty("englishToolTip", tooltip)
        action.setToolTip(translated(tooltip))

    for widget in root.findChildren(QWidget):
        if isinstance(widget, QGroupBox):
            original = widget.property("englishTitle")
            if original is None:
                original = widget.title()
                widget.setProperty("englishTitle", original)
            widget.setTitle(translated(original))
        elif isinstance(widget, QTabWidget):
            original_tabs = widget.property("englishTabs")
            if original_tabs is None:
                original_tabs = [widget.tabText(i) for i in range(widget.count())]
                widget.setProperty("englishTabs", original_tabs)
            for index, text in enumerate(original_tabs):
                widget.setTabText(index, translated(text))
        elif isinstance(widget, QComboBox):
            original_items = widget.property("englishItems")
            if original_items is None:
                original_items = [widget.itemText(i) for i in range(widget.count())]
                widget.setProperty("englishItems", original_items)
            for index, text in enumerate(original_items):
                if index < widget.count() and widget.itemData(index) is not None:
                    widget.setItemText(index, translated(text))
        elif isinstance(widget, QLabel) or isinstance(widget, QAbstractButton):
            if not (isinstance(widget, QToolButton) and widget.defaultAction() is not None):
                original = widget.property("englishText")
                if original is None:
                    original = widget.text()
                    widget.setProperty("englishText", original)
                widget.setText(translated(original))

        tooltip = widget.property("englishToolTip")
        if tooltip is None:
            tooltip = widget.toolTip()
            widget.setProperty("englishToolTip", tooltip)
        widget.setToolTip(translated(tooltip))
