# FreeFEM Simulation App

This project is a **Dockerized scientific simulation pipeline** using FreeFEM++, orchestrated entirely through Python.

It allows you to:

- 📊 Solve the heat equation on a 2D disk via FreeFEM++
- 🐳 Run simulations inside Docker for portability
- ⚙️ Configure all parameters from a simple `params.json` file
- 📈 Visualize results (static plots + animated GIF)
- ✅ Run end-to-end tests using `pytest`
- 📦 Install and use as a CLI tool via `simulate`

---

## 📦 Installation

Clone the repo and set up a virtual environment:

```bash
git clone https://github.com/YOUR_USERNAME/FreeFEM-Simulation-App.git
cd FreeFEM-Simulation-App
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

---

## 🚀 Usage

Run the full simulation + visualization pipeline:

```bash
simulate --run all
```

Individual steps:

```bash
simulate --run sim       # Run the PDE selected in params.json (or by --pde)
simulate --run viz       # Plot static matplotlib visual
simulate --run gif       # Generate animated .gif
simulate --run list      # List the PDE catalogue
simulate --run llg       # Run LLG (Landau-Lifshitz-Gilbert) FreeFEM sim
simulate --run llg-gif   # Generate the LLG magnetization .gif
```

### Industrial-PDE catalogue

The `edp/catalogue/` directory ships templates for the canonical industrial
PDEs of the report appendix (Linear Elasticity, Stokes creeping flow, Heat
diffusion, Steady heat / Poisson, **Advection-Diffusion** with SUPG, and the
scalar Laplacian eigenvalue problem). Pick one with:

```bash
simulate --run sim --pde advection_diffusion
simulate --run sim --pde stokes
simulate --run sim --pde elasticity
# ...
```

See `edp/catalogue/README.md` for the full list and parameter conventions.

All outputs go into the `data/` directory (heat CSV/PNG/GIF), with LLG
per-step CSVs under `data/data_llg/` and the LLG GIF at `data/llg_magnetization.gif`.

Inside the container, the project root is mounted at `/workspace`, so the
`.edp` scripts read from `/workspace/edp/` and write outputs to
`/workspace/data/...`. This avoids the earlier path mismatch where outputs
were landing in `edp/` instead of `data/`.


---

## ⚙️ Configuration

All parameters are defined in params.json:

```
{
  "T": 1.0,
  "dt": 0.05,
  "mesh_resolution": 50
}
```

Edit these to modify simulation behavior.


---

## 🌍 Dependencies

Python 3.8+

Docker

FreeFEM++ 
(via container antoinehocquet/freefem; release: https://github.com/FreeFem/FreeFem-docker/releases/download/v4.12/freefem.tar.gz)

matplotlib

pandas
