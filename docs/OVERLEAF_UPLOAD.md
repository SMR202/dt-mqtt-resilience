# Complete LaTeX report: upload and compile

`paper/overleaf_upload.zip` is the complete upload package. It contains `main.tex`, `references.bib`, and a `figures/` folder with architecture and the three measured-results charts. `main.tex` contains the entire report, metric equations, policy algorithm, measured tables and all 16 inline bibliography entries. The separate BibTeX file is supplied for migration into an official template; this source does not require BibTeX to compile.

## New Overleaf project

1. Download `overleaf_upload.zip` from the GitHub research branch or use the delivered local ZIP.
2. In the Overleaf project dashboard, choose **New project → Existing project (.zip)** and select the ZIP. Preserve `main.tex` at the root and the `figures/` subfolder.
3. Select `main.tex` as the main document. Use **pdfLaTeX** and a recent TeX Live version. Click **Recompile**.
4. Check all four figures and result tables. The source deliberately shows a missing-image notice if a figure was omitted, rather than inventing an image.
5. Confirm names, affiliations, student IDs and contributions. Replace the article layout with the supplied official course/journal template if required. The official template was not provided.
6. Share the project with the instructor and teammate as required; this package does not create Overleaf sharing permissions.

## Existing Overleaf project

Upload `main.tex` and the files in `figures/` using Overleaf's file-upload button. Create the `figures` folder if needed. Set this `main.tex` as the main document, or copy its body into the official template while retaining the image paths and required packages. Do not overwrite a teammate's work without keeping a project-history copy.

The image code is already written, for example:

```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=.95\linewidth]{figures/live_comparison.png}
  \caption{Actual MQTT comparison under local application-shaped conditions.}
\end{figure}
```

No video or audio is required for this paper. Upload PNG/PDF figures as project files; do not paste screenshots of results tables into the manuscript. Tables are editable LaTeX.

## Compilation status

The Codex built-in compiler was attempted on 7 October 2026 and returned `Unable to find standard directories for platform`. This is a compiler-platform failure, not a successful compile or a document-specific diagnostic. The source remains open/editable. Overleaf compilation still needs verification; send its actual error text if it reports a source error.

Official instructions verified 7 October 2026: [uploading a project](https://docs.overleaf.com/managing-projects-and-files/uploading-a-project), [inserting images](https://docs.overleaf.com/writing-and-editing/inserting-images).
