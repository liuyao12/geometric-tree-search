# 3D Lattice Tiler

Standalone JavaScript port of the Observable notebook:

https://observablehq.com/@liuyao12/3d-lattice-tiler

Run from the repository root with any static server, for example:

```bash
python3 -m http.server 5174
```

Then open:

```text
http://127.0.0.1:5174/apps/3d-lattice-tiler/
```

The port keeps the notebook search engine in `engine.js` and moves the page UI and batched Three.js rendering into `app.js`.
