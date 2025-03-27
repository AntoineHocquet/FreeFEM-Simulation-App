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
simulate --run sim     # Run FreeFEM via Docker
simulate --run viz     # Plot static matplotlib visual
simulate --run gif     # Generate animated .gif
```

All outputs go into the data/ directory.


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

FreeFEM++ (via container antoinehocquet/freefem)

matplotlib

pandas