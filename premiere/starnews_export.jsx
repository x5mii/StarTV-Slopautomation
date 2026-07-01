/** StarNews batch export for Adobe Premiere Pro
 *
 * Run from Premiere: File → Scripts → starnews_export.jsx
 *
 * Exports three outputs from the open dated project:
 *   TV: SN_<date>_1   — sequence "SN_Täglich" (720p, 50fps)
 *   SM: SN_<date>_SM  — sequence "SN_Social"
 *   YT: SN_<date>_YT  — sequence "SN_Täglich" via StarNews YT.epr preset
 *
 * Prerequisite: Save the project first so app.project.path is set.
 */

(function () {
    var TV_SEQUENCE = "SN_Täglich";
    var SM_SEQUENCE = "SN_Social";
    var YT_SEQUENCE = "SN_Täglich";
    var YT_PRESET = "/Users/samuel/Documents/Adobe/Adobe Media Encoder/26.0/Presets/StarNews YT.epr";

    if (!app.project) {
        alert("Kein Projekt geöffnet.");
        return;
    }

    if (!app.project.path) {
        alert("Bitte zuerst das Projekt speichern (Datei → Speichern).");
        return;
    }

    if (app.project.sequences.numSequences === 0) {
        alert("Keine Sequenzen im Projekt gefunden.");
        return;
    }

    var projectPath = app.project.path;
    var projectFolder = projectPath.substring(0, projectPath.lastIndexOf("/"));
    var projectName = app.project.name.replace(/\.prproj$/i, "");

    var dateStr = extractDate(projectName);
    if (!dateStr) {
        dateStr = prompt("Datum eingeben (DD.MM):", "01.07");
        if (!dateStr) {
            return;
        }
    }

    var tvSeq = findSequence(TV_SEQUENCE);
    var smSeq = findSequence(SM_SEQUENCE);
    var ytSeq = findSequence(YT_SEQUENCE);

    var missing = [];
    if (!tvSeq) missing.push(TV_SEQUENCE);
    if (!smSeq) missing.push(SM_SEQUENCE);
    if (!ytSeq) missing.push(YT_SEQUENCE);
    if (missing.length > 0) {
        alert("Sequenzen nicht gefunden:\n" + missing.join("\n"));
        return;
    }

    var tvOut = projectFolder + "/SN_" + dateStr + "_1.mp4";
    var smOut = projectFolder + "/SN_" + dateStr + "_SM.mp4";
    var ytOut = projectFolder + "/SN_" + dateStr + "_YT.mp4";

    var proceed = confirm(
        "StarNews Export für " + dateStr + "\n\n" +
        "TV: " + tvOut + "\n" +
        "SM: " + smOut + "\n" +
        "YT: " + ytOut + "\n\n" +
        "Export starten?"
    );
    if (!proceed) {
        return;
    }

    app.encoder.launchEncoder();

    var workArea = 0; // entire sequence
    var removeOnComplete = 0; // keep in AME queue
    var reports = [];

    try {
        app.encoder.encodeSequence(tvSeq, tvOut, "", workArea, removeOnComplete);
        reports.push("TV queued: " + tvOut);
    } catch (e) {
        reports.push("TV failed: " + e.toString());
    }

    try {
        app.encoder.encodeSequence(smSeq, smOut, "", workArea, removeOnComplete);
        reports.push("SM queued: " + smOut);
    } catch (e) {
        reports.push("SM failed: " + e.toString());
    }

    try {
        app.encoder.encodeSequence(ytSeq, ytOut, YT_PRESET, workArea, removeOnComplete);
        reports.push("YT queued: " + ytOut);
    } catch (e) {
        reports.push("YT failed: " + e.toString());
    }

    alert(
        "StarNews Export gestartet.\n\n" +
        reports.join("\n") +
        "\n\nAdobe Media Encoder wurde geöffnet — dort den Export starten."
    );

    function extractDate(name) {
        var match = name.match(/SN_(\d{2}\.\d{2})/);
        if (match) {
            return match[1];
        }
        match = name.match(/(\d{2}\.\d{2})/);
        return match ? match[1] : null;
    }

    function findSequence(name) {
        for (var i = 0; i < app.project.sequences.numSequences; i++) {
            if (app.project.sequences[i].name === name) {
                return app.project.sequences[i];
            }
        }
        return null;
    }
})();
