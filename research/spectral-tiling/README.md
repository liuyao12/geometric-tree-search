# Spectral geometry and planar tiling

This study asks how tile Laplacian spectra, billiard data, Fourier spectrality,
diffraction and dynamical spectra relate to tiling and forced aperiodicity.
The canonical report is [the web article](../../docs/projects/spectral-tiling-study.html).
A printable version is [the PDF](../../output/pdf/spectral-tiling-study.pdf).

The computation estimates the first twelve Dirichlet modes of ten members of
the Hat–Turtle family. Tiling labels come from the cited published family
theorem. They are never inferred from finite growth or a spectral classifier.

Install `requirements.txt` into a temporary environment, then run:

```sh
python compute.py
python verify.py
python build_report.py
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=../../output/pdf report.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=../../output/pdf report.tex
```

The compiler writes `report.pdf`; copy it to the stable delivery filename
`../../output/pdf/spectral-tiling-study.pdf`. The figure PDFs are local assets
used by the LaTeX source. The web report uses the corresponding PNGs.

`results.json` contains all eigenvalues, meshes, geometry, residuals, square
controls, versions and the SHA-256 hash of the executed computation.
`verification.json` records independent checks and exact rational calculations
in the quadratic field for the heat-invariant counterexample.

The continuum mesh model uses floating arithmetic. Its eigenvalues are
numerical estimates, without certified continuum error bounds. The exact
heat-coefficient equality uses rational arithmetic with the square root of
three. It does not establish full isospectrality.

No tiling/search engine is created or modified. This is a specialized
continuum spectral experiment, not the GCTS point-value reference baseline.
The report discusses the requirements for any later sound integration.
